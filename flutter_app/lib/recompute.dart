import 'dart:math' as math;

import 'model.dart';

/// 用补齐后的历史序列重算全部派生指标。
///
/// 之所以在客户端重算而不是只更新一个「最新值」，是因为面板上大部分数字
/// 是相对量（分位、斜率、距高点、建议仓位），只换最新价会得到自相矛盾的界面。
/// 这里完整复刻 build_dashboard_json.py 的口径。
Dash rebuild(Dash base, Map<String, Map<int, double>> history) {
  List<MapEntry<int, double>> ser(String k) {
    final m = history[k] ?? const <int, double>{};
    final e = m.entries.where((x) => x.value > 0).toList()
      ..sort((a, b) => a.key.compareTo(b.key));
    return e;
  }

  double? pct10y(List<MapEntry<int, double>> s) {
    if (s.length < 300) return null;
    final win = math.min(2520, s.length);
    final tail = s.sublist(s.length - win);
    final last = tail.last.value;
    var le = 0;
    for (final e in tail) {
      if (e.value <= last) le++;
    }
    return le / tail.length * 100.0;
  }

  /// 把 yyyymmdd 转成显示用字符串
  String dstr(int d) {
    final y = d ~/ 10000, m = (d ~/ 100) % 100, dd = d % 100;
    return y.toString().padLeft(4, '0') +
        '-' +
        m.toString().padLeft(2, '0') +
        '-' +
        dd.toString().padLeft(2, '0');
  }

  double? ma(List<MapEntry<int, double>> s, int n) {
    if (s.length < n) return null;
    var sum = 0.0;
    for (final e in s.sublist(s.length - n)) {
      sum += e.value;
    }
    return sum / n;
  }

  double? hiN(List<MapEntry<int, double>> s, int n) {
    if (s.isEmpty) return null;
    final t = s.length > n ? s.sublist(s.length - n) : s;
    var h = t.first.value;
    for (final e in t) {
      if (e.value > h) h = e.value;
    }
    return h;
  }

  // ── 波动率族 ──
  final family = <FamItem>[];
  for (final f in base.family) {
    final s = ser(f.ticker);
    if (s.isEmpty) {
      family.add(f);
      continue;
    }
    final v = s.last.value;
    final p = pct10y(s);
    final m20 = ma(s, 20);
    final h63 = hiN(s, 63);
    final prev = s.length >= 2 ? s[s.length - 2].value : null;
    final spark = s.length > 120 ? s.sublist(s.length - 120) : s;
    family.add(FamItem(
      f.ticker,
      f.name,
      f.desc,
      f.kind,
      dstr(s.last.key),
      v,
      p,
      m20,
      m20 == null ? null : v / m20 - 1.0,
      h63,
      h63 == null ? null : (v / h63 - 1.0) * 100.0,
      prev == null ? null : (v / prev - 1.0) * 100.0,
      spark.map((e) => e.value).toList(),
    ));
  }

  // ── 期限结构（四条斜率）──
  Map<int, double>? slopeOf(Map<int, double> a, Map<int, double> b, bool inverse) {
    final keys = a.keys.where(b.containsKey).toList()..sort();
    if (keys.length < 300) return null;
    final out = <int, double>{};
    for (final k in keys) {
      final x = a[k]!, y = b[k]!;
      if (x <= 0 || y <= 0) continue;
      out[k] = inverse ? (x / y - 1.0) * 100.0 : (y / x - 1.0) * 100.0;
    }
    return out;
  }

  final hVix = ser('VIX'), h9 = ser('VIX9D'), h3 = ser('VIX3M'), h6 = ser('VIX6M');
  final mVix = {for (final e in hVix) e.key: e.value};
  final m9 = {for (final e in h9) e.key: e.value};
  final m3 = {for (final e in h3) e.key: e.value};
  final m6 = {for (final e in h6) e.key: e.value};

  final slopes = <String, Map<int, double>>{};
  final sShort = slopeOf(mVix, m9, true);
  final sMid = slopeOf(mVix, m3, false);
  final sLong = slopeOf(m3, m6, false);
  final sTotal = slopeOf(m9, m6, false);
  if (sShort != null) slopes['short'] = sShort;
  if (sMid != null) slopes['mid'] = sMid;
  if (sLong != null) slopes['long'] = sLong;
  if (sTotal != null) slopes['total'] = sTotal;

  List<MapEntry<int, double>> ent(Map<int, double> m) =>
      m.entries.toList()..sort((a, b) => a.key.compareTo(b.key));

  final term = <TermItem>[];
  for (final t in base.term) {
    final m = slopes[t.key];
    if (m == null || m.length < 300) {
      term.add(t);
      continue;
    }
    final e = ent(m);
    final p = pct10y(e);
    final spark = e.length > 120 ? e.sublist(e.length - 120) : e;
    term.add(TermItem(t.key, t.label, dstr(e.last.key), e.last.value, p,
        spark.map((x) => x.value).toList()));
  }

  // ── 曲线快照 ──
  double lastOf(List<MapEntry<int, double>> s, double fallback) =>
      s.isEmpty ? fallback : s.last.value;
  final curve = <Tenor>[];
  for (final t in base.curve) {
    final key = t.tenor == '9天'
        ? 'VIX9D'
        : t.tenor == '30天'
            ? 'VIX'
            : t.tenor == '3个月'
                ? 'VIX3M'
                : 'VIX6M';
    curve.add(Tenor(t.tenor, lastOf(ser(key), t.value), t.days));
  }

  // ── 指数 ──
  final indices = <IdxItem>[];
  for (final ix in base.indices) {
    final s = ser(ix.ticker);
    if (s.isEmpty) {
      indices.add(ix);
      continue;
    }
    final v = s.last.value;
    final m200 = ma(s, 200);
    final h52 = hiN(s, 252);
    final prev = s.length >= 2 ? s[s.length - 2].value : null;
    final spark = s.length > 120 ? s.sublist(s.length - 120) : s;
    indices.add(IdxItem(
      ix.ticker,
      ix.name,
      v,
      prev == null ? null : (v / prev - 1.0) * 100.0,
      m200 == null ? null : (v / m200 - 1.0) * 100.0,
      h52 == null ? null : (v / h52 - 1.0) * 100.0,
      ix.ytd,
      spark.map((e) => e.value).toList(),
    ));
  }

  // ── 结论与买卖点 ──
  final vixSer = ser('VIX');
  final spxSer = ser('SPX');
  if (vixSer.isEmpty || spxSer.isEmpty) {
    return base;
  }
  final vix = vixSer.last.value;
  final vixPct = pct10y(vixSer);
  final vixMa20 = ma(vixSer, 20);
  final vixHi63 = hiN(vixSer, 63);
  final spxV = spxSer.last.value;
  final spxMa200 = ma(spxSer, 200);
  final spxAbove = spxMa200 != null && spxV > spxMa200;
  final midSlope = term.where((e) => e.key == 'mid').map((e) => e.value).firstOrNull;

  // 分档
  String? band;
  if (vix < 13) band = 'VIX < 13';
  else if (vix < 20) band = '13 ~ 20';
  else if (vix < 25) band = '20 ~ 25';
  else if (vix < 30) band = '25 ~ 30';
  else if (vix < 40) band = '30 ~ 40';
  else band = 'VIX > 40';

  LadderRow? curRow;
  for (final r in base.ladder.rows) {
    if (r.band == band) curRow = r;
  }
  final ladder = Ladder(base.ladder.rows, band, vix);

  // 六条规则
  final buy1 = vix >= 40 || (vixPct != null && vixPct >= 95) ||
      (vixMa20 != null && vix > vixMa20 * 1.5);
  final buy2 = vixHi63 != null && (vix / vixHi63 - 1.0) <= -0.40 && vix > 25;
  final buy3 = midSlope != null && midSlope > 10;
  final sell1 = vix >= 20 && vix < 25 && !spxAbove;
  final sell2 = vix < 13;
  final sell3 = midSlope != null && midSlope < -20;

  final signals = <Signal>[];
  for (final s in base.signals) {
    var st = s.state;
    var detail = s.detail;
    switch (s.id) {
      case 'buy1':
        st = buy1;
        detail = 'VIX ' +
            vix.toStringAsFixed(2) +
            '，分位 ' +
            (vixPct ?? 0).toStringAsFixed(1) +
            '%，/20MA = ' +
            (vixMa20 == null ? '-' : (vix / vixMa20).toStringAsFixed(2));
        break;
      case 'buy2':
        st = buy2;
        detail = '63日高点 ' +
            (vixHi63 ?? 0).toStringAsFixed(2) +
            '，当前回落 ' +
            (vixHi63 == null ? '-' : ((vix / vixHi63 - 1) * 100).toStringAsFixed(1)) +
            '%';
        break;
      case 'buy3':
        st = buy3;
        detail = '当前 ' + (midSlope ?? 0).toStringAsFixed(2) + '%';
        break;
      case 'sell1':
        st = sell1;
        detail = 'VIX ' +
            vix.toStringAsFixed(2) +
            '，SPX ' +
            (spxAbove ? '在' : '跌破') +
            ' 200 日线' +
            (spxMa200 == null
                ? ''
                : '上方 ' + ((spxV / spxMa200 - 1) * 100).abs().toStringAsFixed(2) + '%');
        break;
      case 'sell2':
        st = sell2;
        detail = 'VIX ' + vix.toStringAsFixed(2) + '（<13 后 12M 仍有 +12.00%）';
        break;
      case 'sell3':
        st = sell3;
        detail = '当前 ' + (midSlope ?? 0).toStringAsFixed(2) + '%';
        break;
    }
    signals.add(Signal(s.id, s.type, s.name, s.cond, detail, s.action, st));
  }

  // 模式
  String mode = '常态';
  if (buy1 || buy2) {
    mode = '恐慌';
  } else if (sell3 || (midSlope != null && midSlope < -15)) {
    mode = '自满';
  }
  const regimeDesc = {
    '恐慌': '波动率处于极端区，历史统计上未来一年收益最好。这是加仓窗口，不是逃跑窗口。',
    '自满': '期限结构深度陡峭，隐含波动率被压得过低。历史上这个位置未来一年收益最差。',
    '常态': '波动率处于中间地带，没有触发任何极端信号。按 VIX 分档持有基准仓位即可。',
  };
  final suggest = curRow?.pos?.round() ?? base.verdict.suggestPos;

  final verdict = Verdict(
    mode,
    regimeDesc[mode]!,
    band,
    suggest,
    vix,
    vixPct,
    midSlope,
    spxMa200 == null ? null : (spxV / spxMa200 - 1.0) * 100.0,
    spxAbove,
  );

  // 数据日期：取所有序列中的最新日
  var newest = 0;
  for (final e in history.entries) {
    for (final k in e.value.keys) {
      if (k > newest) newest = k;
    }
  }
  final meta = Meta(
    base.meta.generatedAt,
    newest > 0 ? dstr(newest) : base.meta.lastTradeDate,
    base.meta.vixStart,
    base.meta.cotStart,
    vixSer.length,
    base.meta.termStart,
  );

  final rebuiltHistory = <String, OHLC>{};
  for (final e in history.entries) {
    final ks = e.value.keys.toList()..sort();
    rebuiltHistory[e.key] = OHLC(
      ks,
      ks.map((k) => e.value[k]!).toList(),
    );
  }

  return Dash(
    meta,
    family,
    term,
    curve,
    ladder,
    base.slopes,
    base.vvixRows,
    base.skewRows,
    base.rules,
    base.cot,
    indices,
    signals,
    base.watch,
    verdict,
    rebuiltHistory,
  );
}
