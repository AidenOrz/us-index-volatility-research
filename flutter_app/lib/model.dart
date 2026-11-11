import 'dart:convert';
import 'package:flutter/services.dart';

double? _d(dynamic v) => v == null ? null : (v as num).toDouble();
double _dd(dynamic v) => v == null ? 0.0 : (v as num).toDouble();
String _s(dynamic v) => v == null ? '' : v.toString();
int _i(dynamic v) => v == null ? 0 : (v as num).toInt();
bool _b(dynamic v) => v == true;
List<double> _ld(dynamic v) =>
    v == null ? <double>[] : (v as List).map((e) => (e as num).toDouble()).toList();

/// 一条历史序列（打包进 assets 的最近若干年，供日增量更新用）
class OHLC {
  final List<int> dates;   // yyyymmdd
  final List<double> values;
  OHLC(this.dates, this.values);
  factory OHLC.from(dynamic j) => OHLC(
        ((j['dates'] as List?) ?? const []).map((e) => (e as num).toInt()).toList(),
        ((j['values'] as List?) ?? const []).map((e) => (e as num).toDouble()).toList(),
      );
  Map<int, double> get map {
    final out = <int, double>{};
    for (var i = 0; i < dates.length && i < values.length; i++) {
      out[dates[i]] = values[i];
    }
    return out;
  }
}

class Meta {
  final String generatedAt, lastTradeDate, vixStart, cotStart;
  final int vixSamples;
  final String? termStart;
  Meta(this.generatedAt, this.lastTradeDate, this.vixStart, this.cotStart,
      this.vixSamples, this.termStart);
  factory Meta.from(dynamic j) => Meta(
        _s(j['generatedAt']),
        _s(j['lastTradeDate']),
        _s(j['vixStart']),
        _s(j['cotStart']),
        _i(j['vixSamples']),
        j['termStart'] == null ? null : _s(j['termStart']),
      );
}

class FamItem {
  final String ticker, name, desc, kind, date;
  final double value;
  final double? pct10y, ma20, vsMa20, hi63, fromHi63, chg1d;
  final List<double> spark;
  FamItem(this.ticker, this.name, this.desc, this.kind, this.date, this.value,
      this.pct10y, this.ma20, this.vsMa20, this.hi63, this.fromHi63, this.chg1d,
      this.spark);
  factory FamItem.from(dynamic j) => FamItem(
        _s(j['ticker']), _s(j['name']), _s(j['desc']), _s(j['kind']),
        _s(j['date']), _dd(j['value']), _d(j['pct10y']), _d(j['ma20']),
        _d(j['vsMa20']), _d(j['hi63']), _d(j['fromHi63']), _d(j['chg1d']),
        _ld(j['spark']),
      );
}

class TermItem {
  final String key, label, date;
  final double value;
  final double? pct10y;
  final List<double> spark;
  TermItem(this.key, this.label, this.date, this.value, this.pct10y, this.spark);
  factory TermItem.from(dynamic j) => TermItem(_s(j['key']), _s(j['label']),
      _s(j['date']), _dd(j['value']), _d(j['pct10y']), _ld(j['spark']));
}

class Tenor {
  final String tenor;
  final double value;
  final double days;
  Tenor(this.tenor, this.value, this.days);
  factory Tenor.from(dynamic j) =>
      Tenor(_s(j['tenor']), _dd(j['value']), _dd(j['days']));
}

class LadderRow {
  final String band, note;
  final int days;
  final double? share, r1m, w1m, r12m, w12m, rr, pos;
  LadderRow(this.band, this.note, this.days, this.share, this.r1m, this.w1m,
      this.r12m, this.w12m, this.rr, this.pos);
  factory LadderRow.from(dynamic j) => LadderRow(
        _s(j['band']), _s(j['note']), _i(j['days']), _d(j['share']),
        _d(j['r1m']), _d(j['w1m']), _d(j['r12m']), _d(j['w12m']), _d(j['rr']),
        _d(j['pos']),
      );
}

class Ladder {
  final List<LadderRow> rows;
  final String? current;
  final double vix;
  Ladder(this.rows, this.current, this.vix);
  LadderRow? get cur {
    for (final r in rows) {
      if (r.band == current) return r;
    }
    return null;
  }

  factory Ladder.from(dynamic j) => Ladder(
        (j['rows'] as List).map(LadderRow.from).toList(),
        j['current'] == null ? null : _s(j['current']),
        _dd(j['vix']),
      );
}

class SlopeRow {
  final String key, pct;
  final int days;
  final double? median, r1m, w1m, r3m, r12m, w12m;
  SlopeRow(this.key, this.pct, this.days, this.median, this.r1m, this.w1m,
      this.r3m, this.r12m, this.w12m);
  factory SlopeRow.from(dynamic j) => SlopeRow(
        _s(j['key']), _s(j['pct']), _i(j['days']), _d(j['median']), _d(j['r1m']),
        _d(j['w1m']), _d(j['r3m']), _d(j['r12m']), _d(j['w12m']),
      );
}

class BucketRow {
  final String group;
  final int days;
  final double? r1m, w1m, r3m, r12m, w12m, d21vix;
  BucketRow(this.group, this.days, this.r1m, this.w1m, this.r3m, this.r12m,
      this.w12m, this.d21vix);
  factory BucketRow.from(dynamic j) => BucketRow(
        _s(j['group']), _i(j['days']), _d(j['r1m']), _d(j['w1m']), _d(j['r3m']),
        _d(j['r12m']), _d(j['w12m']), _d(j['d21vix']),
      );
}

class Rule {
  final String level, cond, action, basis, triggered;
  Rule(this.level, this.cond, this.action, this.basis, this.triggered);
  factory Rule.from(dynamic j) => Rule(_s(j['level']), _s(j['cond']),
      _s(j['action']), _s(j['basis']), _s(j['triggered']));
}

class CotHist {
  final String d;
  final double? lev, am, dl;
  CotHist(this.d, this.lev, this.am, this.dl);
  factory CotHist.from(dynamic j) =>
      CotHist(_s(j['d']), _d(j['lev']), _d(j['am']), _d(j['dl']));
}

class Cot {
  final String reportDate, alignDate;
  final int total, levLong, levShort, levNet, amNet, dealerNet;
  final double? levNetPct, crowdPct, amNetPct, dealerNetPct, vixClose, spxClose;
  final List<CotHist> hist;
  Cot(this.reportDate, this.alignDate, this.total, this.levLong, this.levShort,
      this.levNet, this.amNet, this.dealerNet, this.levNetPct, this.crowdPct,
      this.amNetPct, this.dealerNetPct, this.vixClose, this.spxClose, this.hist);
  factory Cot.from(dynamic j) => Cot(
        _s(j['reportDate']), _s(j['alignDate']), _i(j['total']),
        _i(j['levLong']), _i(j['levShort']), _i(j['levNet']), _i(j['amNet']),
        _i(j['dealerNet']), _d(j['levNetPct']), _d(j['crowdPct']),
        _d(j['amNetPct']), _d(j['dealerNetPct']), _d(j['vixClose']),
        _d(j['spxClose']),
        ((j['hist'] as List?) ?? const []).map(CotHist.from).toList(),
      );
}

class IdxItem {
  final String ticker, name;
  final double value;
  final double? chg1d, vsMa200, fromHi52, ytd;
  final List<double> spark;
  IdxItem(this.ticker, this.name, this.value, this.chg1d, this.vsMa200,
      this.fromHi52, this.ytd, this.spark);
  factory IdxItem.from(dynamic j) => IdxItem(
        _s(j['ticker']), _s(j['name']), _dd(j['value']), _d(j['chg1d']),
        _d(j['vsMa200']), _d(j['fromHi52']), _d(j['ytd']), _ld(j['spark']),
      );
}

class Signal {
  final String id, type, name, cond, detail, action;
  final bool state;
  Signal(this.id, this.type, this.name, this.cond, this.detail, this.action,
      this.state);
  factory Signal.from(dynamic j) => Signal(
        _s(j['id']), _s(j['type']), _s(j['name']), _s(j['cond']),
        _s(j['detail']), _s(j['action']), _b(j['state']),
      );
}

class Watch {
  final String sev, tag, text;
  Watch(this.sev, this.tag, this.text);
  factory Watch.from(dynamic j) =>
      Watch(_s(j['sev']), _s(j['tag']), _s(j['text']));
}

class Verdict {
  final String mode, desc, band;
  final int suggestPos;
  final double vix;
  final double? vixPct, midSlope, spxVsMa200;
  final bool spxAbove;
  Verdict(this.mode, this.desc, this.band, this.suggestPos, this.vix,
      this.vixPct, this.midSlope, this.spxVsMa200, this.spxAbove);
  factory Verdict.from(dynamic j) => Verdict(
        _s(j['mode']), _s(j['desc']), _s(j['band']), _i(j['suggestPos']),
        _dd(j['vix']), _d(j['vixPct']), _d(j['midSlope']),
        _d(j['spxVsMa200']), _b(j['spxAbove']),
      );
}

class Dash {
  final Meta meta;
  final List<FamItem> family;
  final List<TermItem> term;
  final List<Tenor> curve;
  final Ladder ladder;
  final List<SlopeRow> slopes;
  final List<BucketRow> vvixRows;
  final List<BucketRow> skewRows;
  final List<Rule> rules;
  final Cot cot;
  final List<IdxItem> indices;
  final List<Signal> signals;
  final List<Watch> watch;
  final Verdict verdict;
  final Map<String, OHLC> history;

  Dash(this.meta, this.family, this.term, this.curve, this.ladder, this.slopes,
      this.vvixRows, this.skewRows, this.rules, this.cot, this.indices,
      this.signals, this.watch, this.verdict,
      [this.history = const {}]);

  FamItem fam(String t) => family.firstWhere((e) => e.ticker == t,
      orElse: () => family.first);

  static Future<Dash> load() async {
    final raw = await rootBundle.loadString('assets/dashboard.json');
    return Dash.parse(raw);
  }

  static Dash parse(String raw) {
    final j = jsonDecode(raw) as Map<String, dynamic>;
    final vs = j['vvixSkew'] as Map;
    final hj = (j['history'] as Map?) ?? const {};
    final hist = <String, OHLC>{};
    for (final e in hj.entries) {
      hist[e.key as String] = OHLC.from(e.value);
    }
    return Dash(
      Meta.from(j['meta']),
      (j['family'] as List).map(FamItem.from).toList(),
      (j['term'] as List).map(TermItem.from).toList(),
      (j['curve'] as List).map(Tenor.from).toList(),
      Ladder.from(j['ladder']),
      (j['slopes'] as List).map(SlopeRow.from).toList(),
      (vs['vvix'] as List).map(BucketRow.from).toList(),
      (vs['skew'] as List).map(BucketRow.from).toList(),
      (j['rules'] as List).map(Rule.from).toList(),
      Cot.from(j['cot']),
      (j['indices'] as List).map(IdxItem.from).toList(),
      (j['signals'] as List).map(Signal.from).toList(),
      (j['watch'] as List).map(Watch.from).toList(),
      Verdict.from(j['verdict']),
      hist,
    );
  }
}