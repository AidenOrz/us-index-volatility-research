import 'package:flutter/material.dart';

import 'live_data.dart';
import 'theme.dart';

/// 统一的弹窗骨架：深色、无圆角阴影、标题带色条。
Widget _shell({
  required String title,
  required Color accent,
  required Widget body,
  required List<Widget> actions,
}) =>
    Dialog(
      backgroundColor: C.panel,
      shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(12),
          side: const BorderSide(color: C.line)),
      child: ConstrainedBox(
        constraints: const BoxConstraints(maxWidth: 520, minWidth: 380),
        child: Padding(
          padding: const EdgeInsets.fromLTRB(20, 18, 20, 14),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(children: [
                Container(
                    width: 3,
                    height: 16,
                    decoration: BoxDecoration(
                        color: accent,
                        borderRadius: BorderRadius.circular(2))),
                const SizedBox(width: 9),
                Expanded(
                    child: Text(title,
                        style: sans(15, w: FontWeight.w700))),
              ]),
              const SizedBox(height: 12),
              body,
              const SizedBox(height: 16),
              Row(mainAxisAlignment: MainAxisAlignment.end, children: actions),
            ],
          ),
        ),
      ),
    );

Widget _btn(String label, {bool primary = false, VoidCallback? onTap}) =>
    TextButton(
      onPressed: onTap,
      style: TextButton.styleFrom(
        backgroundColor: primary ? C.accent.withValues(alpha: 0.16) : Colors.transparent,
        side: BorderSide(color: primary ? C.accent.withValues(alpha: 0.5) : C.line),
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(6)),
      ),
      child: Text(label,
          style: sans(12,
              w: primary ? FontWeight.w700 : FontWeight.w400,
              color: primary ? C.accent : C.text2)),
    );

/// 一条数据源状态行
Widget _sourceRow(SourceStatus s) => Padding(
      padding: const EdgeInsets.symmetric(vertical: 3),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(s.ok ? Icons.check_circle_outline : Icons.error_outline,
              size: 13, color: s.ok ? C.down : C.up),
          const SizedBox(width: 6),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  s.name + (s.items > 0 ? ' · ' + s.items.toString() + ' 项' : ''),
                  style: sans(11.5, color: s.ok ? C.text2 : C.text),
                ),
                if (s.detail != null)
                  Padding(
                    padding: const EdgeInsets.only(top: 1),
                    child: Text(s.detail!,
                        style: sans(10.5, color: C.text3, h: 1.4)),
                  ),
              ],
            ),
          ),
        ],
      ),
    );

/// 完全失败：所有源都不可达，此时必须让用户知道「看到的是旧数据」
Future<void> showDataErrorDialog(
  BuildContext context,
  RefreshResult r, {
  bool canRetry = true,
  VoidCallback? onRetry,
}) =>
    showDialog(
      context: context,
      barrierDismissible: false,
      builder: (ctx) => _shell(
        title: '无法获取最新数据',
        accent: C.up,
        body: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              '界面显示的是打包时（' +
                  (r.sources.isEmpty ? '未知' : '最近一次成功') +
                  '）的快照，可能不是最新交易日。',
              style: sans(12, color: C.text2, h: 1.5),
            ),
            const SizedBox(height: 10),
            if (r.failures.isNotEmpty)
              Container(
                width: double.infinity,
                padding: const EdgeInsets.all(9),
                decoration: BoxDecoration(
                    color: C.up.withValues(alpha: 0.07),
                    borderRadius: BorderRadius.circular(6),
                    border: Border.all(color: C.up.withValues(alpha: 0.25))),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    for (final f in r.failures.take(5))
                      Padding(
                        padding: const EdgeInsets.symmetric(vertical: 1.5),
                        child: Text('· ' + f,
                            style: sans(11, color: C.text2, h: 1.45)),
                      ),
                  ],
                ),
              ),
            if (r.sources.isNotEmpty) ...[
              const SizedBox(height: 10),
              for (final s in r.sources) _sourceRow(s),
            ],
            const SizedBox(height: 10),
            Text(
              '检查项：网络连接 / 代理端口 7897 / 目标站点是否可访问。',
              style: sans(10.5, color: C.text3, h: 1.45),
            ),
          ],
        ),
        actions: [
          _btn('知道了', onTap: () => Navigator.of(ctx).pop()),
          if (canRetry) ...[
            const SizedBox(width: 8),
            _btn('重试', primary: true, onTap: () {
              Navigator.of(ctx).pop();
              onRetry?.call();
            }),
          ],
        ],
      ),
    );

/// 部分成功：有源失败但界面仍可用，提示哪里没补上
Future<void> showPartialDialog(BuildContext context, RefreshResult r) =>
    showDialog(
      context: context,
      builder: (ctx) => _shell(
        title: '部分数据未能更新',
        accent: C.warn,
        body: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              '已补齐 ' +
                  r.filledPoints.toString() +
                  ' 个数据点，但下面这些源没成功，对应指标沿用快照值。',
              style: sans(12, color: C.text2, h: 1.5),
            ),
            const SizedBox(height: 10),
            for (final s in r.sources.where((e) => !e.ok)) _sourceRow(s),
          ],
        ),
        actions: [_btn('知道了', primary: true, onTap: () => Navigator.of(ctx).pop())],
      ),
    );

/// 意外异常
Future<void> showFatalDialog(BuildContext context, String err,
        {VoidCallback? onRetry}) =>
    showDialog(
      context: context,
      barrierDismissible: false,
      builder: (ctx) => _shell(
        title: '数据刷新出错',
        accent: C.up,
        body: Text(err,
            style: sans(11.5, color: C.text2, h: 1.5),
            maxLines: 8,
            overflow: TextOverflow.ellipsis),
        actions: [
          _btn('关闭', onTap: () => Navigator.of(ctx).pop()),
          const SizedBox(width: 8),
          _btn('重试', primary: true, onTap: () {
            Navigator.of(ctx).pop();
            onRetry?.call();
          }),
        ],
      ),
    );