import 'dart:io';
import 'package:flutter_test/flutter_test.dart';
import 'package:vol_dashboard/model.dart';
import 'package:vol_dashboard/recompute.dart';

void main() {
  final raw = File('assets/dashboard.json').readAsStringSync();
  final d = Dash.parse(raw);

  test('dashboard.json 结构与字段完整', () {
    expect(d.family.length, 8);
    expect(d.term.length, 4);
    expect(d.ladder.rows.length, 6);
    expect(d.signals.length, 6);
    expect(d.indices.length, 6);
    expect(d.meta.vixSamples, greaterThan(9000));
    expect(d.fam('VIX').value, greaterThan(0));
    for (final f in d.family) {
      expect(f.spark.length, greaterThan(100), reason: f.ticker);
      expect(f.pct10y, isNotNull, reason: f.ticker);
    }
    expect(d.term.map((e) => e.key).toSet(), {'short', 'mid', 'long', 'total'});
  });

  test('打包了运行时重算所需的历史序列', () {
    for (final k in ['VIX', 'VIX9D', 'VIX3M', 'VIX6M', 'VVIX', 'SKEW']) {
      expect(d.history.containsKey(k), isTrue, reason: k);
      expect(d.history[k]!.dates.length, greaterThan(1000), reason: k);
    }
    for (final k in ['SPX', 'DJI', 'IXIC', 'NDX', 'RUT', 'SOX']) {
      expect(d.history.containsKey(k), isTrue, reason: k);
    }
    // 日期必须严格递增
    for (final e in d.history.entries) {
      final ds = e.value.dates;
      for (var i = 1; i < ds.length; i++) {
        expect(ds[i] > ds[i - 1], isTrue, reason: e.key);
      }
    }
  });

  test('重算在无新数据时必须复现原值（恒等性）', () {
    final hist = <String, Map<int, double>>{};
    for (final e in d.history.entries) {
      hist[e.key] = e.value.map;
    }
    final r = rebuild(d, hist);
    // 关键指标不能漂移
    expect((r.verdict.vix - d.verdict.vix).abs() < 0.01, isTrue,
        reason: 'VIX ${r.verdict.vix} vs ${d.verdict.vix}');
    expect(r.verdict.band, d.verdict.band);
    expect(r.verdict.suggestPos, d.verdict.suggestPos);
    expect(r.verdict.mode, d.verdict.mode);
    for (var i = 0; i < d.family.length; i++) {
      expect((r.family[i].value - d.family[i].value).abs() < 0.01, isTrue,
          reason: d.family[i].ticker);
    }
    // 分位允许小误差（客户端窗口与原脚本口径一致）
    for (var i = 0; i < d.family.length; i++) {
      final a = r.family[i].pct10y, b = d.family[i].pct10y;
      if (a != null && b != null) {
        expect((a - b).abs() < 1.0, isTrue,
            reason: '${d.family[i].ticker} 分位 ${a} vs ${b}');
      }
    }
  });

  test('追加一天新数据后指标按预期方向变化', () {
    final hist = <String, Map<int, double>>{};
    for (final e in d.history.entries) {
      hist[e.key] = Map<int, double>.from(e.value.map);
    }
    final lastDay = hist['VIX']!.keys.reduce((a, b) => a > b ? a : b);
    final newDay = lastDay + 1;
    // 人为把 VIX 推到 45，应触发买点①并进入恐慌模式
    hist['VIX']![newDay] = 45.0;
    hist['VIX9D']![newDay] = 48.0;
    hist['VIX3M']![newDay] = 38.0;
    final r = rebuild(d, hist);
    expect(r.verdict.vix, 45.0);
    expect(r.verdict.band, 'VIX > 40');
    expect(r.verdict.mode, '恐慌');
    expect(r.signals.firstWhere((s) => s.id == 'buy1').state, isTrue);
    expect(r.verdict.suggestPos, 100);
  });

  test('数据稀疏时重算不崩溃', () {
    final hist = <String, Map<int, double>>{
      'VIX': {20260101: 20.0},
      'SPX': {20260101: 5000.0},
    };
    final r = rebuild(d, hist);
    expect(r.verdict.vix, 20.0);
    expect(r.meta.lastTradeDate, '2026-01-01');
  });
}