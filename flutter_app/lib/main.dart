import 'package:flutter/material.dart';
import 'model.dart';
import 'theme.dart';
import 'graphics.dart';
import 'live_data.dart';
import 'recompute.dart';
import 'dialogs.dart';

void main() => runApp(const VolApp());

class VolApp extends StatelessWidget {
  const VolApp({super.key});
  @override
  Widget build(BuildContext context) => MaterialApp(
        title: '波动率看盘',
        debugShowCheckedModeBanner: false,
        theme: ThemeData(
          scaffoldBackgroundColor: C.bg,
          colorScheme: ColorScheme.fromSeed(
              seedColor: C.accent, brightness: Brightness.dark),
          useMaterial3: true,
        ),
        home: const Home(),
      );
}

class Home extends StatefulWidget {
  const Home({super.key});
  @override
  State<Home> createState() => _HomeState();
}

class _HomeState extends State<Home> {
  Dash? _dash;
  RefreshResult? _last;
  String? _fatal;
  bool _busy = false;
  bool _autoRan = false;

  @override
  void initState() {
    super.initState();
    _boot();
  }

  /// 启动流程：先载入打包快照（保证立刻有画面），再后台尝试自动补当日数据。
  Future<void> _boot() async {
    try {
      final base = await Dash.load();
      if (!mounted) return;
      setState(() => _dash = base);
      if (!_autoRan) {
        _autoRan = true;
        await _refresh(base, showDialogOnError: true, silent: true);
      }
    } catch (e) {
      if (!mounted) return;
      setState(() => _fatal = e.toString());
    }
  }

  /// 尝试补齐。silent=true 时成功不打扰，失败才弹窗。
  Future<void> _refresh(Dash base,
      {bool showDialogOnError = true, bool silent = false}) async {
    if (_busy) return;
    setState(() => _busy = true);
    try {
      final res = await LiveData.refresh(base);
      if (!mounted) return;
      setState(() {
        _dash = res.dash;
        _last = res.report;
        _busy = false;
      });
      if (!res.report.ok && showDialogOnError) {
        await showDataErrorDialog(context, res.report, canRetry: true, onRetry: () {
          final d = _dash;
          if (d != null) _refresh(d, showDialogOnError: true);
        });
      } else if (res.report.ok && !silent && res.report.failures.isNotEmpty) {
        await showPartialDialog(context, res.report);
      }
    } catch (e) {
      if (!mounted) return;
      setState(() => _busy = false);
      if (showDialogOnError) {
        await showFatalDialog(context, e.toString(), onRetry: () {
          final d = _dash;
          if (d != null) _refresh(d, showDialogOnError: true);
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_fatal != null) {
      return Scaffold(
        body: Center(
            child: Text('数据载入失败：' + _fatal!, style: sans(13, color: C.up))),
      );
    }
    final d = _dash;
    if (d == null) {
      return const Scaffold(
          body: Center(
              child: SizedBox(
                  width: 22,
                  height: 22,
                  child: CircularProgressIndicator(strokeWidth: 2))));
    }
    return Scaffold(
      body: _Board(
        d: d,
        busy: _busy,
        last: _last,
        onRefresh: () {
          final cur = _dash;
          if (cur != null) _refresh(cur, showDialogOnError: true);
        },
      ),
    );
  }
}
class _Board extends StatelessWidget {
  final Dash d;
  final bool busy;
  final RefreshResult? last;
  final VoidCallback? onRefresh;
  const _Board(
      {required this.d, this.busy = false, this.last, this.onRefresh});
  @override
  Widget build(BuildContext context) => LayoutBuilder(builder: (ctx, c) {
        final w = c.maxWidth;
        final three = w >= 1030;
        final two = w >= 740;
        return Padding(
          padding: const EdgeInsets.fromLTRB(14, 10, 14, 10),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              HeaderBar(d: d, busy: busy, last: last, onRefresh: onRefresh),
              const SizedBox(height: 6),
              IndexStrip(d: d),
              const SizedBox(height: 8),
              VerdictBar(d: d),
              const SizedBox(height: 8),
              if (three) ...[
                Expanded(
                  flex: 12,
                  child: Row(
                    crossAxisAlignment: CrossAxisAlignment.stretch,
                    children: [
                      Expanded(flex: 32, child: FamilyPanel(d: d)),
                      const SizedBox(width: 8),
                      Expanded(flex: 30, child: TermPanel(d: d)),
                      const SizedBox(width: 8),
                      Expanded(flex: 30, child: SignalPanel(d: d)),
                    ],
                  ),
                ),
                const SizedBox(height: 8),
                Expanded(
                  flex: 9,
                  child: Row(
                    crossAxisAlignment: CrossAxisAlignment.stretch,
                    children: [
                      Expanded(flex: 36, child: LadderPanel(d: d)),
                      const SizedBox(width: 8),
                      Expanded(flex: 30, child: VvixPanel(d: d)),
                      const SizedBox(width: 8),
                      Expanded(flex: 34, child: WatchPanel(d: d)),
                    ],
                  ),
                ),
              ] else if (two)
                Expanded(
                  child: SingleChildScrollView(
                    child: Column(
                      children: [
                        SizedBox(
                          height: 460,
                          child: Row(
                            crossAxisAlignment: CrossAxisAlignment.stretch,
                            children: [
                              Expanded(flex: 1, child: FamilyPanel(d: d)),
                              const SizedBox(width: 8),
                              Expanded(flex: 1, child: TermPanel(d: d)),
                            ],
                          ),
                        ),
                        const SizedBox(height: 8),
                        SizedBox(
                          height: 420,
                          child: Row(
                            crossAxisAlignment: CrossAxisAlignment.stretch,
                            children: [
                              Expanded(flex: 1, child: SignalPanel(d: d)),
                              const SizedBox(width: 8),
                              Expanded(flex: 1, child: LadderPanel(d: d)),
                            ],
                          ),
                        ),
                        const SizedBox(height: 8),
                        SizedBox(
                          height: 340,
                          child: Row(
                            crossAxisAlignment: CrossAxisAlignment.stretch,
                            children: [
                              Expanded(flex: 1, child: VvixPanel(d: d)),
                              const SizedBox(width: 8),
                              Expanded(flex: 1, child: WatchPanel(d: d)),
                            ],
                          ),
                        ),
                      ],
                    ),
                  ),
                )
              else
                Expanded(
                  child: SingleChildScrollView(
                    child: Column(
                      children: [
                        SizedBox(height: 470, child: FamilyPanel(d: d)),
                        const SizedBox(height: 8),
                        SizedBox(height: 430, child: TermPanel(d: d)),
                        const SizedBox(height: 8),
                        SizedBox(height: 430, child: SignalPanel(d: d)),
                        const SizedBox(height: 8),
                        SizedBox(height: 330, child: LadderPanel(d: d)),
                        const SizedBox(height: 8),
                        SizedBox(height: 330, child: VvixPanel(d: d)),
                        const SizedBox(height: 8),
                        SizedBox(height: 330, child: WatchPanel(d: d)),
                      ],
                    ),
                  ),
                ),
            ],
          ),
        );
      });
}

/// ───────── 面板容器 ─────────
class Panel extends StatelessWidget {
  final String title;
  final String? hint;
  final Widget child;
  final Widget? trailing;
  const Panel(
      {super.key,
      required this.title,
      required this.child,
      this.hint,
      this.trailing});
  @override
  Widget build(BuildContext context) => Container(
        decoration: BoxDecoration(
          color: C.panel,
          borderRadius: BorderRadius.circular(10),
          border: Border.all(color: C.line, width: 1),
        ),
        padding: const EdgeInsets.fromLTRB(12, 10, 12, 10),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Row(
              children: [
                Container(
                  width: 2.5,
                  height: 11,
                  decoration: BoxDecoration(
                      color: C.accent, borderRadius: BorderRadius.circular(2)),
                ),
                const SizedBox(width: 6),
                Text(title, style: sans(12.5, w: FontWeight.w700)),
                if (hint != null) ...[
                  const SizedBox(width: 6),
                  Flexible(
                      child: Text(hint!,
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                          style: sans(10.5, color: C.text3))),
                ],
                const Spacer(),
                ?trailing,
              ],
            ),
            const SizedBox(height: 8),
            Expanded(child: child),
          ],
        ),
      );
}

/// ───────── 顶部标题 ─────────
class HeaderBar extends StatelessWidget {
  final Dash d;
  final bool busy;
  final RefreshResult? last;
  final VoidCallback? onRefresh;
  const HeaderBar(
      {super.key, required this.d, this.busy = false, this.last, this.onRefresh});

  @override
  Widget build(BuildContext context) {
    final m = d.meta;
    return SizedBox(
      height: 34,
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.center,
        children: [
          Text('波动率看盘', style: sans(17, w: FontWeight.w700, ls: 0.4)),
          const SizedBox(width: 10),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
            decoration: BoxDecoration(
                color: C.panel2,
                borderRadius: BorderRadius.circular(4),
                border: Border.all(color: C.line)),
            child: Text('VIX 择时', style: sans(10, color: C.text2)),
          ),
          const SizedBox(width: 8),
          _DataStatusChip(d: d, last: last, busy: busy),
          const Spacer(),
          Text('数据 ' + m.lastTradeDate, style: mono(11, color: C.text2)),
          const SizedBox(width: 12),
          Text('快照 ' + m.generatedAt, style: mono(10.5, color: C.text3)),
          const SizedBox(width: 10),
          _RefreshButton(busy: busy, onTap: onRefresh),
        ],
      ),
    );
  }
}

/// 数据新鲜度：绿色=最新，黄色=滞后几天，红色=滞后或刷新失败
class _DataStatusChip extends StatelessWidget {
  final Dash d;
  final RefreshResult? last;
  final bool busy;
  const _DataStatusChip({required this.d, this.last, this.busy = false});

  int get _lagDays {
    try {
      final t = DateTime.parse(d.meta.lastTradeDate);
      final now = DateTime.now();
      return DateTime(now.year, now.month, now.day)
          .difference(DateTime(t.year, t.month, t.day))
          .inDays;
    } catch (_) {
      return 999;
    }
  }

  @override
  Widget build(BuildContext context) {
    final failed = last != null && !last!.ok;
    final Color col;
    final String label;
    if (busy) {
      col = C.text3;
      label = '同步中';
    } else if (failed) {
      col = C.up;
      label = '更新失败';
    } else if (_lagDays <= 1) {
      col = C.down;
      label = '最新';
    } else if (_lagDays <= 4) {
      col = C.warn;
      label = '滞后 ${_lagDays} 天';
    } else {
      col = C.up;
      label = '滞后 ${_lagDays} 天';
    }
    final tip = last == null
        ? '尚未尝试联网更新'
        : last!.sources
            .map((s) =>
                s.name + (s.ok ? ' 正常' : ' 失败') + (s.detail != null ? '：' + s.detail! : ''))
            .join('\n');
    return Tooltip(
      message: tip,
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
        decoration: BoxDecoration(
            color: col.withValues(alpha: 0.12),
            borderRadius: BorderRadius.circular(4),
            border: Border.all(color: col.withValues(alpha: 0.4))),
        child: Row(mainAxisSize: MainAxisSize.min, children: [
          Container(
              width: 5,
              height: 5,
              decoration: BoxDecoration(color: col, shape: BoxShape.circle)),
          const SizedBox(width: 4),
          Text(label, style: sans(9.5, w: FontWeight.w700, color: col)),
        ]),
      ),
    );
  }
}

class _RefreshButton extends StatefulWidget {
  final bool busy;
  final VoidCallback? onTap;
  const _RefreshButton({this.busy = false, this.onTap});
  @override
  State<_RefreshButton> createState() => _RefreshButtonState();
}

class _RefreshButtonState extends State<_RefreshButton> {
  bool _hover = false;
  @override
  Widget build(BuildContext context) => MouseRegion(
        cursor: SystemMouseCursors.click,
        onEnter: (_) => setState(() => _hover = true),
        onExit: (_) => setState(() => _hover = false),
        child: GestureDetector(
          onTap: widget.busy ? null : widget.onTap,
          child: Container(
            padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
            decoration: BoxDecoration(
                color: _hover ? C.panel2 : Colors.transparent,
                borderRadius: BorderRadius.circular(4),
                border: Border.all(color: _hover ? C.line : C.lineSoft)),
            child: Row(mainAxisSize: MainAxisSize.min, children: [
              widget.busy
                  ? const SizedBox(
                      width: 9,
                      height: 9,
                      child: CircularProgressIndicator(strokeWidth: 1.4))
                  : Icon(Icons.refresh_rounded,
                      size: 11, color: _hover ? C.text : C.text3),
              const SizedBox(width: 4),
              Text('刷新', style: sans(10, color: _hover ? C.text : C.text2)),
            ]),
          ),
        ),
      );
}

/// ───────── 指数条 ─────────
class IndexStrip extends StatelessWidget {
  final Dash d;
  const IndexStrip({super.key, required this.d});
  @override
  Widget build(BuildContext context) => SizedBox(
        height: 30,
        child: LayoutBuilder(builder: (ctx, c) {
          final compact = c.maxWidth < 900;
          final items = <Widget>[
            for (var i = 0; i < d.indices.length; i++) ...[
              if (i > 0)
                Container(
                    width: 1,
                    height: 14,
                    color: C.lineSoft,
                    margin: const EdgeInsets.symmetric(horizontal: 12)),
              Text(d.indices[i].name,
                  style: sans(11, color: C.text2), maxLines: 1),
              const SizedBox(width: 5),
              Text(fx(d.indices[i].value),
                  style: mono(12.5, color: C.text), maxLines: 1),
              const SizedBox(width: 5),
              Text(fsign(d.indices[i].chg1d),
                  style: mono(11, color: chgColor(d.indices[i].chg1d)),
                  maxLines: 1),
            ],
          ];
          return Row(
            children: [
              Expanded(
                child: compact
                    ? SingleChildScrollView(
                        scrollDirection: Axis.horizontal, child: Row(children: items))
                    : Row(children: [...items, const Spacer(),
                        Text('涨红跌绿', style: sans(10, color: C.text3))]),
              ),
            ],
          );
        }),
      );
}

/// ───────── 结论条 ─────────
class VerdictBar extends StatelessWidget {
  final Dash d;
  const VerdictBar({super.key, required this.d});

  Color get _modeColor {
    switch (d.verdict.mode) {
      case '恐慌':
        return C.up;
      case '自满':
        return C.warn;
      default:
        return C.down;
    }
  }

  @override
  Widget build(BuildContext context) {
    final v = d.verdict;
    return LayoutBuilder(builder: (ctx, c) {
      final compact = c.maxWidth < 900;
      return Container(
      height: compact ? 176 : 104,
      decoration: BoxDecoration(
        gradient: const LinearGradient(
          begin: Alignment.centerLeft,
          end: Alignment.centerRight,
          colors: [C.panel2, C.panel],
        ),
        borderRadius: BorderRadius.circular(10),
        border: Border.all(color: C.line),
      ),
      padding: const EdgeInsets.fromLTRB(14, 10, 14, 10),
      child: compact ? _compactVerdict(v) : Row(
        crossAxisAlignment: CrossAxisAlignment.center,
        children: [
          // VIX 主数值
          Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Row(children: [
                Text('VIX', style: sans(11, color: C.text2, ls: 0.6)),
                const SizedBox(width: 6),
                Container(
                  width: 6,
                  height: 6,
                  decoration: BoxDecoration(
                      color: pctColor(v.vixPct), shape: BoxShape.circle),
                ),
              ]),
              const SizedBox(height: 2),
              Text(fx(v.vix), style: mono(38, w: FontWeight.w700, color: C.text)),
            ],
          ),
          const SizedBox(width: 14),
          _VStat(
              label: '10 年分位',
              value: fx(v.vixPct, 1) + '%',
              color: pctColor(v.vixPct)),
          _VStat(
              label: '当前档位',
              value: v.band.isEmpty ? '—' : v.band,
              color: C.text),
          _VStat(
              label: 'VIX3M/VIX−1',
              value: fsign(v.midSlope),
              color: (v.midSlope ?? 0) > 0 ? C.up : C.down),
          _VStat(
              label: 'SPX 距年线',
              value: fsign(v.spxVsMa200),
              color: v.spxAbove ? C.down : C.up),
          const SizedBox(width: 6),
          Container(width: 1, height: 56, color: C.lineSoft),
          const SizedBox(width: 10),
          PosGauge(v.suggestPos, width: 150, height: 78),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Row(children: [
                  Container(
                    padding:
                        const EdgeInsets.symmetric(horizontal: 7, vertical: 2),
                    decoration: BoxDecoration(
                        color: _modeColor.withValues(alpha: 0.14),
                        borderRadius: BorderRadius.circular(4),
                        border: Border.all(
                            color: _modeColor.withValues(alpha: 0.45))),
                    child: Text('${v.mode}模式',
                        style: sans(11,
                            w: FontWeight.w700, color: _modeColor)),
                  ),
                  const SizedBox(width: 8),
                  Text('建议仓位 ${v.suggestPos}%',
                      style: sans(11.5, color: C.text2)),
                ]),
                const SizedBox(height: 5),
                Text(v.desc,
                    maxLines: 2,
                    overflow: TextOverflow.ellipsis,
                    style: sans(11.5, color: C.text2, h: 1.45)),
              ],
            ),
          ),
        ],
      ),
    );
    });
  }

  Widget _compactVerdict(Verdict v) => Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            crossAxisAlignment: CrossAxisAlignment.center,
            children: [
              Text('VIX', style: sans(11, color: C.text2, ls: 0.6)),
              const SizedBox(width: 8),
              Text(fx(v.vix),
                  style: mono(30, w: FontWeight.w700, color: C.text)),
              const SizedBox(width: 10),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 7, vertical: 2),
                decoration: BoxDecoration(
                    color: _modeColor.withValues(alpha: 0.14),
                    borderRadius: BorderRadius.circular(4),
                    border: Border.all(color: _modeColor.withValues(alpha: 0.45))),
                child: Text('${v.mode}模式',
                    style: sans(11, w: FontWeight.w700, color: _modeColor)),
              ),
            ],
          ),
          const SizedBox(height: 6),
          Row(
            children: [
              _VStat(
                  label: '建议仓位',
                  value: '${v.suggestPos}%',
                  color: v.suggestPos >= 80
                      ? C.down
                      : v.suggestPos >= 45
                          ? C.warn
                          : C.up),
              _VStat(
                  label: '10 年分位',
                  value: '${fx(v.vixPct, 1)}%',
                  color: pctColor(v.vixPct)),
              _VStat(
                  label: '当前档位',
                  value: v.band.isEmpty ? '—' : v.band,
                  color: C.text),
              _VStat(
                  label: 'VIX3M/VIX−1',
                  value: fsign(v.midSlope),
                  color: (v.midSlope ?? 0) > 0 ? C.up : C.down),
            ],
          ),
          const SizedBox(height: 4),
          Text(v.desc,
              maxLines: 2,
              overflow: TextOverflow.ellipsis,
              style: sans(11, color: C.text2, h: 1.45)),
        ],
      );
}

class _VStat extends StatelessWidget {
  final String label, value;
  final Color color;
  const _VStat({required this.label, required this.value, required this.color});
  @override
  Widget build(BuildContext context) => Padding(
        padding: const EdgeInsets.symmetric(horizontal: 11),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(label, style: sans(10, color: C.text3)),
            const SizedBox(height: 3),
            Text(value, style: mono(16, w: FontWeight.w700, color: color)),
          ],
        ),
      );
}

/// ───────── 波动率家族 ─────────
class FamilyPanel extends StatelessWidget {
  final Dash d;
  const FamilyPanel({super.key, required this.d});
  @override
  Widget build(BuildContext context) {
    return Panel(
      title: '波动率族',
      hint: '8 个 CBOE 官方指数 · 分位为滚动 10 年',
      child: Column(
        children: [
          _FamHead(),
          const SizedBox(height: 2),
          Expanded(
            child: Column(
              children: [
                for (final f in d.family)
                  Expanded(child: _FamRow(f: f)),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _FamHead extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    Widget t(String s, {int f = 1, TextAlign a = TextAlign.left}) => Expanded(
          flex: f,
          child: Text(s,
              textAlign: a,
              style: sans(9.5, color: C.text3, ls: 0.3),
              maxLines: 1),
        );
    return SizedBox(
      height: 14,
      child: Row(
        children: [
          t('指数', f: 26),
          t('最新', f: 26, a: TextAlign.right),
          t('分位', f: 16, a: TextAlign.center),
          t('日变化', f: 22, a: TextAlign.right),
          t('近 120 日', f: 30, a: TextAlign.right),
        ],
      ),
    );
  }
}

class _FamRow extends StatelessWidget {
  final FamItem f;
  const _FamRow({required this.f});
  @override
  Widget build(BuildContext context) {
    final pc = pctColor(f.pct10y);
    return Container(
      decoration: const BoxDecoration(
          border: Border(bottom: BorderSide(color: C.lineSoft, width: 1))),
      child: Row(
        children: [
          Expanded(
            flex: 26,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Text(f.ticker,
                    style: mono(11.5, w: FontWeight.w700, color: C.text)),
                Text(f.kind, style: sans(9, color: C.text3)),
              ],
            ),
          ),
          Expanded(
            flex: 26,
            child: Text(fx(f.value),
                textAlign: TextAlign.right,
                style: mono(14, w: FontWeight.w700)),
          ),
          Expanded(
            flex: 16,
            child: Center(
              child: Container(
                padding:
                    const EdgeInsets.symmetric(horizontal: 4, vertical: 1.5),
                decoration: BoxDecoration(
                    color: pc.withValues(alpha: 0.13),
                    borderRadius: BorderRadius.circular(3)),
                child: Text('${fx(f.pct10y, 0)}%',
                    style: mono(10, color: pc, w: FontWeight.w700)),
              ),
            ),
          ),
          Expanded(
            flex: 22,
            child: Text(fsign(f.chg1d),
                textAlign: TextAlign.right,
                style: mono(11, color: chgColor(f.chg1d))),
          ),
          Expanded(
            flex: 30,
            child: LayoutBuilder(builder: (c, cc) {
              final w = cc.maxWidth.isFinite ? cc.maxWidth : 78.0;
              return Align(
                alignment: Alignment.centerRight,
                child: Spark(f.spark,
                    color: pc,
                    width: w,
                    height: 20,
                    fill: true,
                    stroke: 1.2),
              );
            }),
          ),
        ],
      ),
    );
  }
}

/// ───────── 期限结构 ─────────
class TermPanel extends StatelessWidget {
  final Dash d;
  const TermPanel({super.key, required this.d});
  @override
  Widget build(BuildContext context) {
    final pts = d.curve.map((e) => MapEntry(e.tenor, e.value)).toList();
    final days = d.curve.map((e) => e.days <= 0 ? 1.0 : e.days).toList();
    return Panel(
      title: '期限结构',
      hint: '曲线 + 四条斜率',
      trailing: Text('越陡→未来越差',
          style: sans(9.5, color: C.text3)),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          SizedBox(
              height: 118,
              child: LayoutBuilder(
                  builder: (c, cc) => TermCurve(pts,
                      days: days,
                      width: cc.maxWidth,
                      height: 118,
                      color: (d.verdict.midSlope ?? 0) > 0 ? C.up : C.accent))),
          const SizedBox(height: 6),
          Container(height: 1, color: C.lineSoft),
          const SizedBox(height: 4),
          Row(children: [
            Expanded(flex: 34, child: Text('斜率', style: sans(9.5, color: C.text3))),
            Expanded(
                flex: 18,
                child: Text('当前', style: sans(9.5, color: C.text3), textAlign: TextAlign.right)),
            Expanded(
                flex: 16,
                child: Text('分位', style: sans(9.5, color: C.text3), textAlign: TextAlign.center)),
            Expanded(
                flex: 22,
                child: Text('12M', style: sans(9.5, color: C.text3), textAlign: TextAlign.right)),
          ]),
          const SizedBox(height: 2),
          Expanded(
            child: Column(
              children: [
                for (final t in d.term) Expanded(child: _TermRow(t: t)),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _TermRow extends StatelessWidget {
  final TermItem t;
  const _TermRow({required this.t});
  @override
  Widget build(BuildContext context) {
    final pc = pctColor(t.pct10y);
    final sl = _slopeStats(t.key);
    return Container(
      decoration: const BoxDecoration(
          border: Border(bottom: BorderSide(color: C.lineSoft, width: 1))),
      child: Row(
        children: [
          Expanded(
            flex: 34,
            child: Text(t.label.replaceAll(' VIX', ' '),
                style: sans(10.5, color: C.text2),
                maxLines: 1,
                overflow: TextOverflow.ellipsis),
          ),
          Expanded(
            flex: 18,
            child: Text(fsign(t.value),
                textAlign: TextAlign.right,
                style: mono(12, w: FontWeight.w700, color: chgColor(t.value))),
          ),
          Expanded(
            flex: 16,
            child: Center(
              child: Container(
                padding:
                    const EdgeInsets.symmetric(horizontal: 4, vertical: 1.5),
                decoration: BoxDecoration(
                    color: pc.withValues(alpha: 0.13),
                    borderRadius: BorderRadius.circular(3)),
                child: Text(fx(t.pct10y, 0),
                    style: mono(10, color: pc, w: FontWeight.w700)),
              ),
            ),
          ),
          Expanded(
            flex: 22,
            child: Text(sl,
                textAlign: TextAlign.right,
                style: mono(11, color: C.text2)),
          ),
        ],
      ),
    );
  }

  String _slopeStats(String key) {
    if (key == 'short') return '+16.6%';
    if (key == 'mid') return '+18.9%';
    if (key == 'long') return '+18.8%';
    return '+18.5%';
  }
}

/// ───────── 买卖点 ─────────
class SignalPanel extends StatelessWidget {
  final Dash d;
  const SignalPanel({super.key, required this.d});
  @override
  Widget build(BuildContext context) {
    final n = d.signals.where((e) => e.state).length;
    return Panel(
      title: '买卖点判定',
      hint: '规则来自 32 年回测',
      trailing: Container(
        padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 1.5),
        decoration: BoxDecoration(
            color: n > 0
                ? C.warn.withValues(alpha: 0.14)
                : C.down.withValues(alpha: 0.14),
            borderRadius: BorderRadius.circular(4)),
        child: Text('$n / 6 触发',
            style: sans(9.5,
                w: FontWeight.w700, color: n > 0 ? C.warn : C.down)),
      ),
      child: Column(
        children: [
          for (final s in d.signals) Expanded(child: _SigRow(s: s)),
        ],
      ),
    );
  }
}

class _SigRow extends StatelessWidget {
  final Signal s;
  const _SigRow({required this.s});
  @override
  Widget build(BuildContext context) {
    final isBuy = s.type == 'buy';
    final on = s.state;
    final base = isBuy ? C.down : C.warn;
    final col = on ? base : C.text3;
    return Container(
      decoration: const BoxDecoration(
          border: Border(bottom: BorderSide(color: C.lineSoft, width: 1))),
      margin: const EdgeInsets.only(bottom: 1),
      child: Row(
        children: [
          Container(
            width: 5,
            height: 5,
            margin: const EdgeInsets.only(right: 7),
            decoration: BoxDecoration(
              color: on ? base : C.line,
              shape: BoxShape.circle,
              boxShadow: on
                  ? [BoxShadow(color: base.withValues(alpha: 0.6), blurRadius: 5)]
                  : null,
            ),
          ),
          Expanded(
            child: FittedBox(
              fit: BoxFit.scaleDown,
              alignment: Alignment.centerLeft,
              child: SizedBox(
                width: 240,
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Row(children: [
                      Flexible(
                        child: Text(s.name,
                            maxLines: 1,
                            overflow: TextOverflow.ellipsis,
                            style: sans(11,
                                w: on ? FontWeight.w700 : FontWeight.w400,
                                color: on ? C.text : C.text2)),
                      ),
                      const SizedBox(width: 5),
                      Container(
                        padding: const EdgeInsets.symmetric(
                            horizontal: 4, vertical: 0.5),
                        decoration: BoxDecoration(
                            color: col.withValues(alpha: on ? 0.16 : 0.06),
                            borderRadius: BorderRadius.circular(3)),
                        child: Text(on ? '触发' : '未触发',
                            style: sans(8.5, w: FontWeight.w700, color: col)),
                      ),
                    ]),
                    const SizedBox(height: 1),
                    Text(s.detail,
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                        style: mono(9.5, color: C.text3, w: FontWeight.w400)),
                    const SizedBox(height: 2),
                    Text('→ ' + s.action,
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                        style: sans(9.5,
                            color: on ? base.withValues(alpha: 0.9) : C.text3)),
                  ],
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }
}

/// ───────── VIX 分档 ─────────
class LadderPanel extends StatelessWidget {
  final Dash d;
  const LadderPanel({super.key, required this.d});
  @override
  Widget build(BuildContext context) {
    final L = d.ladder;
    Widget h(String s, int f, TextAlign a) => Expanded(
        flex: f,
        child: Text(s,
            textAlign: a, style: sans(9.5, color: C.text3), maxLines: 1));
    return Panel(
      title: 'VIX 分档 · U 型曲线',
      hint: '20-25 是最差档',
      child: Column(
        children: [
          SizedBox(
            height: 14,
            child: Row(children: [
              h('档位', 24, TextAlign.left),
              h('天数', 14, TextAlign.right),
              h('12M 均值', 20, TextAlign.right),
              h('胜率', 15, TextAlign.right),
              h('盈亏比', 15, TextAlign.right),
              h('仓位', 14, TextAlign.right),
            ]),
          ),
          const SizedBox(height: 2),
          Expanded(
            child: Column(
              children: [
                for (final r in L.rows)
                  Expanded(child: _LadderRowW(r: r, on: r.band == L.current)),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _LadderRowW extends StatelessWidget {
  final LadderRow r;
  final bool on;
  const _LadderRowW({required this.r, required this.on});
  @override
  Widget build(BuildContext context) {
    final rc = chgColor(r.r12m);
    Widget c(String s,
            int f,
            TextStyle st,
            {TextAlign a = TextAlign.right}) =>
        Expanded(
            flex: f,
            child: Text(s,
                textAlign: a, style: st, maxLines: 1, overflow: TextOverflow.ellipsis));
    return Container(
      margin: const EdgeInsets.symmetric(vertical: 1),
      padding: const EdgeInsets.symmetric(horizontal: 4),
      decoration: BoxDecoration(
        color: on ? C.accent.withValues(alpha: 0.10) : Colors.transparent,
        borderRadius: BorderRadius.circular(4),
        border: on
            ? Border.all(color: C.accent.withValues(alpha: 0.4), width: 1)
            : null,
      ),
      child: Row(
        children: [
          c(r.band, 24,
              sans(10.5, w: on ? FontWeight.w700 : FontWeight.w400,
                  color: on ? C.accent : C.text2),
              a: TextAlign.left),
          c(r.days.toString(), 14, mono(10, color: C.text3, w: FontWeight.w400)),
          c(fsign(r.r12m, 2), 20, mono(11, color: rc, w: FontWeight.w700)),
          c(fx(r.w12m, 1), 15,
              mono(10, color: C.text2, w: FontWeight.w400)),
          c(fx(r.rr, 2), 15, mono(10, color: C.text2, w: FontWeight.w400)),
          c('${fx(r.pos, 0)}%', 14,
              mono(10, color: C.text, w: FontWeight.w700)),
        ],
      ),
    );
  }
}

/// ───────── VVIX / SKEW ─────────
class VvixPanel extends StatelessWidget {
  final Dash d;
  const VvixPanel({super.key, required this.d});
  @override
  Widget build(BuildContext context) {
    final vv = d.fam('VVIX');
    return Panel(
      title: 'VVIX 二阶 · SKEW 尾部',
      hint: 'VVIX 低才该担心',
      trailing: Text('VVIX ${fx(vv.value)}',
          style: mono(11, color: C.violet, w: FontWeight.w700)),
      child: Column(
        children: [
          Expanded(
            flex: 10,
            child: Column(
              children: [
                for (final b in d.vvixRows)
                  Expanded(
                      child: Container(
                    decoration: const BoxDecoration(
                        border: Border(
                            bottom: BorderSide(color: C.lineSoft, width: 1))),
                    child: Row(
                      children: [
                        Expanded(
                            flex: 30,
                            child: Text(b.group,
                                style: sans(10, color: C.text2),
                                maxLines: 1,
                                overflow: TextOverflow.ellipsis)),
                        Expanded(
                            flex: 16,
                            child: Text(b.days.toString(),
                                textAlign: TextAlign.right,
                                style: mono(9.5,
                                    color: C.text3, w: FontWeight.w400))),
                        Expanded(
                            flex: 24,
                            child: Text(fsign(b.r12m),
                                textAlign: TextAlign.right,
                                style: mono(11,
                                    color: chgColor(b.r12m),
                                    w: FontWeight.w700))),
                        Expanded(
                            flex: 16,
                            child: Text(fx(b.w12m, 0),
                                textAlign: TextAlign.right,
                                style: mono(10,
                                    color: C.text2, w: FontWeight.w400))),
                        Expanded(
                            flex: 22,
                            child: Text(fsign(b.d21vix, 2, ''),
                                textAlign: TextAlign.right,
                                style: mono(10,
                                    color: chgColor(b.d21vix),
                                    w: FontWeight.w400))),
                      ],
                    ),
                  )),
              ],
            ),
          ),
          const SizedBox(height: 3),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 4),
            decoration: BoxDecoration(
                color: C.panel2, borderRadius: BorderRadius.circular(5)),
            child: Row(children: [
              Text('SKEW ', style: sans(9.5, color: C.text3)),
              Text(fx(d.fam('SKEW').value),
                  style: mono(10.5, color: C.text2, w: FontWeight.w700)),
              const SizedBox(width: 8),
              Expanded(
                child: Text('SKEW 与未来收益相关仅 −0.011，基本无用',
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                    style: sans(9.5, color: C.text3)),
              ),
            ]),
          ),
        ],
      ),
    );
  }
}

/// ───────── 今日提醒 ─────────
class WatchPanel extends StatelessWidget {
  final Dash d;
  const WatchPanel({super.key, required this.d});
  @override
  Widget build(BuildContext context) => Panel(
        title: '今日值得注意',
        hint: '按历史统计排序',
        child: Column(
          children: [
            Expanded(
              child: Column(
                children: [
                  for (final w in d.watch) Expanded(child: _WatchRow(w: w)),
                ],
              ),
            ),
            const SizedBox(height: 6),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 4),
              decoration: BoxDecoration(
                  color: C.panel2, borderRadius: BorderRadius.circular(5)),
              child: Row(children: [
                Text('COT ', style: sans(9.5, color: C.text3)),
                Text('杠杆基金净 ${fint(d.cot.levNet)} 张',
                    style: mono(10, color: chgColor(d.cot.levNet.toDouble()), w: FontWeight.w700)),
                const SizedBox(width: 8),
                Text('拥挤度 ${fx(d.cot.crowdPct, 0)}%',
                    style: mono(10, color: C.text2)),
                const Spacer(),
                Text('${d.cot.reportDate} 报告',
                    style: mono(9.5, color: C.text3, w: FontWeight.w400)),
              ]),
            ),
          ],
        ),
      );
}

class _WatchRow extends StatelessWidget {
  final Watch w;
  const _WatchRow({required this.w});
  Color get col {
    switch (w.sev) {
      case 'high':
        return C.up;
      case 'med':
        return C.warn;
      case 'good':
        return C.down;
      default:
        return C.accent;
    }
  }

  @override
  Widget build(BuildContext context) => Container(
        decoration: const BoxDecoration(
            border: Border(bottom: BorderSide(color: C.lineSoft, width: 1))),
        child: Row(
        crossAxisAlignment: CrossAxisAlignment.center,
        children: [
          Container(
            margin: const EdgeInsets.only(top: 3),
            padding: const EdgeInsets.symmetric(horizontal: 5, vertical: 1.5),
            decoration: BoxDecoration(
                color: col.withValues(alpha: 0.14),
                borderRadius: BorderRadius.circular(3),
                border: Border.all(color: col.withValues(alpha: 0.35))),
            child: Text(w.tag,
                style: sans(9.5, w: FontWeight.w700, color: col)),
          ),
          const SizedBox(width: 6),
          Expanded(
            child: Text(w.text,
                style: sans(11.5, color: C.text2, h: 1.55),
                maxLines: 4,
                overflow: TextOverflow.ellipsis),
          ),
        ],
      ));
}