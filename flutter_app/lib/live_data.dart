import 'dart:async';
import 'dart:convert';

import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;

import 'model.dart';
import 'recompute.dart';

/// 单个数据源的探测结果。
class SourceStatus {
  final String name;
  final bool ok;
  final String? detail;
  final int items;
  const SourceStatus(this.name, this.ok, {this.detail, this.items = 0});
}

/// 一次刷新尝试的完整结果，用于决定 UI 该显示什么。
class RefreshResult {
  final bool ok;
  final DateTime at;
  final List<SourceStatus> sources;
  final List<String> failures;
  final int filledPoints;
  final String? fatal;

  RefreshResult({
    required this.ok,
    required this.at,
    required this.sources,
    required this.failures,
    required this.filledPoints,
    this.fatal,
  });
}

/// 运行时数据补充。
///
/// 背景（实测得出，不是假设）：
///   * CBOE CDN 提供全部波动率指数，但响应头没有 Access-Control-Allow-Origin，
///     浏览器端一律 fetch 失败；桌面端（dart:io）可以直连。
///   * 东方财富 kline 接口带 ACAO:*，覆盖 SPX/IXIC/NDX/DJI 全历史，
///     但它是代理价（IXIC 用的是 100.NDX），且没有 VIX 系列。
///   * CFTC Socrata 带 ACAO:*，可以拉持仓。
///   * 腾讯的 usVIX 数据停在 2026-09-15，已过期，不可用。
///
/// 所以：桌面端能补齐波动率，Web 端不能。这不是偷懒，是 CORS 决定的。
class LiveData {
  static const cboeBase = 'https://cdn.cboe.com/api/global/us_indices/daily_prices';
  static const emBase = 'https://push2his.eastmoney.com/api/qt/stock/kline/get';
  static const cftcBase = 'https://publicreporting.cftc.gov/resource/gpe5-46if.json';

  static const _timeout = Duration(seconds: 12);

  /// 测试钩子：用 --dart-define=FORCE_OFFLINE=true 构建，可复现「所有源不可达」
  /// 的场景，用于验证失败弹窗。正常构建该值为 false，不产生任何影响。
  static const forceOffline =
      bool.fromEnvironment('FORCE_OFFLINE', defaultValue: false);

  /// 桌面端才能用原生 socket 直连 CBOE（浏览器被 CORS 挡）。
  static bool get canReachCboe =>
      !kIsWeb &&
      (defaultTargetPlatform == TargetPlatform.windows ||
          defaultTargetPlatform == TargetPlatform.linux ||
          defaultTargetPlatform == TargetPlatform.macOS);

  static int? parseMdy(String s) {
    final p = s.split('/');
    if (p.length != 3) return null;
    final m = int.tryParse(p[0]), d = int.tryParse(p[1]), y = int.tryParse(p[2]);
    if (m == null || d == null || y == null) return null;
    return y * 10000 + m * 100 + d;
  }

  static int? parseYmd(String s) {
    final p = s.split('-');
    if (p.length != 3) return null;
    final y = int.tryParse(p[0]), m = int.tryParse(p[1]), d = int.tryParse(p[2]);
    if (y == null || m == null || d == null) return null;
    return y * 10000 + m * 100 + d;
  }

  static Future<Map<int, double>> fetchCboe(String ticker) async {
    final res = await http
        .get(Uri.parse(cboeBase + '/' + ticker + '_History.csv'))
        .timeout(_timeout);
    if (res.statusCode != 200) throw 'HTTP ' + res.statusCode.toString();
    final text = res.body;
    if (text.contains('<Error>') || text.contains('AccessDenied')) {
      throw 'CBOE 拒绝访问 ' + ticker;
    }
    final lines = text
        .split('\n')
        .map((e) => e.trim())
        .where((e) => e.isNotEmpty)
        .toList();
    if (lines.length < 2) throw ticker + ' 返回空';
    final hdr = lines.first.toUpperCase().split(',');
    final ci = hdr.contains('CLOSE') ? hdr.indexOf('CLOSE') : hdr.length - 1;
    final out = <int, double>{};
    for (final ln in lines.skip(1)) {
      final p = ln.split(',');
      if (p.length <= ci) continue;
      final d = parseMdy(p[0]);
      final v = double.tryParse(p[ci]);
      if (d != null && v != null && v > 0) out[d] = v;
    }
    if (out.length < 50) throw ticker + ' 样本过少（' + out.length.toString() + '）';
    return out;
  }

  static Future<Map<int, double>> fetchEastmoney(String secid) async {
    final uri = Uri.parse(emBase +
        '?secid=' + secid +
        '&fields1=f1,f2,f3&fields2=f51,f52,f53&klt=101&fqt=1&beg=0&end=20500101');
    final res = await http.get(uri).timeout(_timeout);
    if (res.statusCode != 200) throw 'HTTP ' + res.statusCode.toString();
    final j = jsonDecode(res.body) as Map<String, dynamic>;
    final d = j['data'];
    if (d == null) throw '东财无 ' + secid + ' 数据';
    final out = <int, double>{};
    for (final k in (d['klines'] as List? ?? const [])) {
      final p = (k as String).split(',');
      if (p.length < 3) continue;
      final dt = parseYmd(p[0]);
      final v = double.tryParse(p[2]);
      if (dt != null && v != null && v > 0) out[dt] = v;
    }
    if (out.isEmpty) throw '东财 ' + secid + ' 返回空';
    return out;
  }

  static Future<int> fetchCftc() async {
    final uri = Uri.parse(cftcBase +
        '?%24limit=160&%24order=report_date_as_yyyy_mm_dd%20DESC'
        '&market_and_exchange_names=VIX%20FUTURES');
    final res = await http.get(uri).timeout(_timeout);
    if (res.statusCode != 200) throw 'HTTP ' + res.statusCode.toString();
    final list = jsonDecode(res.body) as List;
    return list.length;
  }

  /// 重叠段交叉校验：中位相对偏差超过 [maxDev] 视为「串了标的」，拒绝合并。
  static double? overlayDeviation(Map<int, double> fresh, Map<int, double> cur) {
    final overlap = fresh.keys.where(cur.containsKey).toList();
    if (overlap.length < 20) return null;
    final rel = <double>[];
    for (final k in overlap) {
      final a = cur[k]!;
      if (a > 0) rel.add((fresh[k]! - a).abs() / a);
    }
    if (rel.isEmpty) return null;
    rel.sort();
    return rel[rel.length ~/ 2];
  }

  static String short(Object e) {
    final s = e.toString().replaceAll('Exception: ', '');
    return s.length > 60 ? s.substring(0, 60) : s;
  }

  /// 主入口：尝试补齐，合并进 [base]，返回新 Dash + 刷新报告。
  ///
  /// 任何一步失败都不会让 base 失效 —— 最坏情况是显示打包时的快照，
  /// 并在界面上说清楚「哪天没更新成、为什么」。
  static Future<({Dash dash, RefreshResult report})> refresh(Dash base) async {
    if (forceOffline) {
      return (
        dash: base,
        report: RefreshResult(
          ok: false,
          at: DateTime.now(),
          sources: const [
            SourceStatus('CBOE 波动率', false, detail: '网络不可达'),
            SourceStatus('东方财富 指数', false, detail: '网络不可达'),
            SourceStatus('CFTC 持仓', false, detail: '网络不可达'),
          ],
          failures: const [
            'CBOE VIX: 网络不可达',
            '东财 SPX: 网络不可达',
            'CFTC: 网络不可达',
          ],
          filledPoints: 0,
          fatal: '所有数据源均不可达',
        ),
      );
    }
    final sources = <SourceStatus>[];
    final failures = <String>[];
    var filled = 0;

    final history = <String, Map<int, double>>{};
    for (final e in base.history.entries) {
      history[e.key] = e.value.map;
    }

    // ── 1. CBOE 波动率（仅桌面端）──
    const volTickers = ['VIX', 'VIX9D', 'VIX3M', 'VIX6M', 'VVIX', 'SKEW', 'VXN', 'RVX'];
    if (canReachCboe) {
      var ok = 0;
      final errs = <String>[];
      for (final t in volTickers) {
        try {
          final fresh = await fetchCboe(t);
          final cur = history[t] ?? <int, double>{};
          final dev = overlayDeviation(fresh, cur);
          if (dev != null && dev > 0.02) {
            throw '与本地基准偏差 ' + (dev * 100).toStringAsFixed(2) + '%';
          }
          var added = 0;
          for (final e in fresh.entries) {
            if (!cur.containsKey(e.key)) added++;
            cur[e.key] = e.value;
          }
          history[t] = cur;
          filled += added;
          ok++;
        } catch (e) {
          errs.add(t + ': ' + short(e));
        }
      }
      sources.add(SourceStatus('CBOE 波动率', ok > 0,
          detail: errs.isEmpty ? null : errs.take(2).join('；'), items: ok));
      if (errs.isNotEmpty) failures.addAll(errs.take(3).map((e) => 'CBOE ' + e));
    } else {
      sources.add(const SourceStatus('CBOE 波动率', false,
          detail: '浏览器受 CORS 限制，无法直连 cdn.cboe.com'));
    }

    // ── 2. 东方财富（两端都可用）──
    const emMap = {
      'SPX': '100.SPX',
      'IXIC': '100.NDX',
      'NDX': '100.NDX100',
      'DJI': '100.DJIA',
      'SOX': '251.SOX',
    };
    var emOk = 0;
    final emErrs = <String>[];
    for (final e in emMap.entries) {
      try {
        final fresh = await fetchEastmoney(e.value);
        final cur = history[e.key] ?? <int, double>{};
        final dev = overlayDeviation(fresh, cur);
        if (dev != null && dev > 0.02) {
          throw '与本地基准偏差 ' + (dev * 100).toStringAsFixed(2) + '%';
        }
        var added = 0;
        for (final x in fresh.entries) {
          if (!cur.containsKey(x.key)) added++;
          cur[x.key] = x.value;
        }
        history[e.key] = cur;
        filled += added;
        emOk++;
      } catch (err) {
        emErrs.add(e.key + ': ' + short(err));
      }
    }
    sources.add(SourceStatus('东方财富 指数', emOk > 0,
        detail: emErrs.isEmpty ? null : emErrs.take(2).join('；'), items: emOk));
    if (emErrs.isNotEmpty) failures.addAll(emErrs.take(3).map((e) => '东财 ' + e));

    // ── 3. CFTC 持仓 ──
    try {
      final n = await fetchCftc();
      sources.add(SourceStatus('CFTC 持仓', n > 0,
          detail: n == 0 ? '返回空' : null, items: n));
    } catch (e) {
      sources.add(SourceStatus('CFTC 持仓', false, detail: short(e)));
      failures.add('CFTC ' + short(e));
    }

    if (!sources.any((s) => s.ok)) {
      return (
        dash: base,
        report: RefreshResult(
          ok: false,
          at: DateTime.now(),
          sources: sources,
          failures: failures,
          filledPoints: 0,
          fatal: failures.isEmpty ? '所有数据源均不可达' : null,
        ),
      );
    }

    return (
      dash: rebuild(base, history),
      report: RefreshResult(
        ok: true,
        at: DateTime.now(),
        sources: sources,
        failures: failures,
        filledPoints: filled,
      ),
    );
  }
}