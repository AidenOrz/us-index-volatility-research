import 'dart:math' as math;
import 'package:flutter/material.dart';
import 'theme.dart';

/// 迷你走势线
class Spark extends StatelessWidget {
  final List<double> data;
  final Color color;
  final double width;
  final double height;
  final bool fill;
  final double stroke;
  const Spark(this.data,
      {super.key,
      this.color = C.accent,
      this.width = 90,
      this.height = 28,
      this.fill = true,
      this.stroke = 1.4});
  @override
  Widget build(BuildContext context) =>
      CustomPaint(size: Size(width, height), painter: _SparkPainter(data, color, fill, stroke));
}

class _SparkPainter extends CustomPainter {
  final List<double> d;
  final Color color;
  final bool fill;
  final double stroke;
  _SparkPainter(this.d, this.color, this.fill, this.stroke);

  @override
  void paint(Canvas canvas, Size size) {
    if (d.length < 2) return;
    var lo = d.reduce(math.min), hi = d.reduce(math.max);
    if (hi - lo < 1e-9) {
      hi += 1;
      lo -= 1;
    }
    final dx = size.width / (d.length - 1);
    double yy(double v) => size.height - (v - lo) / (hi - lo) * size.height;
    final path = Path();
    for (var i = 0; i < d.length; i++) {
      final x = i * dx, y = yy(d[i]);
      i == 0 ? path.moveTo(x, y) : path.lineTo(x, y);
    }
    if (fill) {
      final fp = Path.from(path)
        ..lineTo(size.width, size.height)
        ..lineTo(0, size.height)
        ..close();
      canvas.drawPath(
          fp,
          Paint()
            ..shader = LinearGradient(
              begin: Alignment.topCenter,
              end: Alignment.bottomCenter,
              colors: [color.withValues(alpha: 0.30), color.withValues(alpha: 0.0)],
            ).createShader(Rect.fromLTWH(0, 0, size.width, size.height)));
    }
    canvas.drawPath(
        path,
        Paint()
          ..color = color
          ..style = PaintingStyle.stroke
          ..strokeWidth = stroke
          ..strokeJoin = StrokeJoin.round
          ..strokeCap = StrokeCap.round);
    // 末点
    canvas.drawCircle(
        Offset(size.width, yy(d.last)), stroke * 1.5, Paint()..color = color);
  }

  @override
  bool shouldRepaint(covariant _SparkPainter o) => o.d != d || o.color != color;
}

/// 期限结构曲线（真实到期天数对数轴）
class TermCurve extends StatelessWidget {
  final List<MapEntry<String, double>> pts;
  final List<double> days;
  final double width;
  final double height;
  final Color color;
  const TermCurve(this.pts,
      {super.key,
      required this.days,
      this.width = 300,
      this.height = 110,
      this.color = C.accent});
  @override
  Widget build(BuildContext context) => CustomPaint(
      size: Size(width, height), painter: _CurvePainter(pts, days, color));
}

class _CurvePainter extends CustomPainter {
  final List<MapEntry<String, double>> pts;
  final List<double> days;
  final Color color;
  _CurvePainter(this.pts, this.days, this.color);

  @override
  void paint(Canvas canvas, Size size) {
    if (pts.length < 2) return;
    const padL = 0.0, padT = 22.0, padB = 20.0;
    final vals = pts.map((e) => e.value).toList();
    var lo = vals.reduce(math.min), hi = vals.reduce(math.max);
    if (hi - lo < 1e-6) {
      hi += 1;
      lo -= 1;
    }
    final span = hi - lo;
    lo -= span * 0.28;
    hi += span * 0.28;
    final w = size.width - padL;
    final h = size.height - padT - padB;
    final n = pts.length;
    // 真实到期天数对数轴：9 → 30 → 90 → 180
    final ldays = days.map((e) => math.log(e)).toList();
    final loD = ldays.reduce(math.min), hiD = ldays.reduce(math.max);
    final spanD = (hiD - loD).abs() < 1e-9 ? 1.0 : (hiD - loD);
    Offset pos(int i) => Offset(
        padL + 14 + (w - 28) * (ldays[i] - loD) / spanD,
        padT + h - (pts[i].value - lo) / (hi - lo) * h);

    // 网格
    final gp = Paint()
      ..color = C.lineSoft
      ..strokeWidth = 1;
    canvas.drawLine(Offset(0, padT + h), Offset(size.width, padT + h), gp);

    final path = Path();
    for (var i = 0; i < n; i++) {
      final p = pos(i);
      i == 0 ? path.moveTo(p.dx, p.dy) : path.lineTo(p.dx, p.dy);
    }
    final fp = Path.from(path)
      ..lineTo(pos(n - 1).dx, padT + h)
      ..lineTo(pos(0).dx, padT + h)
      ..close();
    canvas.drawPath(
        fp,
        Paint()
          ..shader = LinearGradient(
            begin: Alignment.topCenter,
            end: Alignment.bottomCenter,
            colors: [color.withValues(alpha: 0.26), color.withValues(alpha: 0.0)],
          ).createShader(Rect.fromLTWH(0, padT, size.width, h)));
    canvas.drawPath(
        path,
        Paint()
          ..color = color
          ..style = PaintingStyle.stroke
          ..strokeWidth = 2.0
          ..strokeJoin = StrokeJoin.round);

    for (var i = 0; i < n; i++) {
      final p = pos(i);
      canvas.drawCircle(p, 3.4, Paint()..color = C.panel);
      canvas.drawCircle(
          p,
          3.4,
          Paint()
            ..color = color
            ..style = PaintingStyle.stroke
            ..strokeWidth = 1.6);
      final tp = TextPainter(
        textDirection: TextDirection.ltr,
        text: TextSpan(text: fx(pts[i].value, 1), style: mono(10, color: C.text2)),
      )..layout();
      tp.paint(canvas, Offset(p.dx - tp.width / 2, p.dy - 18));
      final lp = TextPainter(
        textDirection: TextDirection.ltr,
        text: TextSpan(text: pts[i].key, style: sans(10, color: C.text3)),
      )..layout();
      lp.paint(canvas, Offset(p.dx - lp.width / 2, padT + h + 6));
    }
  }

  @override
  bool shouldRepaint(covariant _CurvePainter o) => true;
}

/// 仓位刻度盘（半圆）
class PosGauge extends StatelessWidget {
  final int pos;
  final double width;
  final double height;
  const PosGauge(this.pos,
      {super.key, this.width = 168, this.height = 92});
  @override
  Widget build(BuildContext context) =>
      CustomPaint(size: Size(width, height), painter: _GaugePainter(pos));
}

class _GaugePainter extends CustomPainter {
  final int pos;
  _GaugePainter(this.pos);
  @override
  void paint(Canvas canvas, Size size) {
    final c = Offset(size.width / 2, size.height - 6);
    final r = math.min(size.width / 2 - 6, size.height - 16);
    final rect = Rect.fromCircle(center: c, radius: r);
    canvas.drawArc(
        rect,
        math.pi,
        math.pi,
        false,
        Paint()
          ..color = C.line
          ..style = PaintingStyle.stroke
          ..strokeWidth = 9
          ..strokeCap = StrokeCap.round);
    final frac = (pos.clamp(0, 100)) / 100.0;
    if (frac > 0.001) {
      final col = pos >= 80
          ? C.down
          : pos >= 45
              ? C.warn
              : C.up;
      canvas.drawArc(
          rect,
          math.pi,
          math.pi * frac,
          false,
          Paint()
            ..color = col
            ..style = PaintingStyle.stroke
            ..strokeWidth = 9
            ..strokeCap = StrokeCap.round);
    }
    final tp = TextPainter(
      textDirection: TextDirection.ltr,
      text: TextSpan(
          text: '$pos%', style: mono(21, w: FontWeight.w700, color: C.text)),
    )..layout();
    tp.paint(canvas, Offset(c.dx - tp.width / 2, c.dy - tp.height - 4));
  }

  @override
  bool shouldRepaint(covariant _GaugePainter o) => o.pos != pos;
}

/// 水平条形（用于 12M 收益对比），支持负值
class HBar extends StatelessWidget {
  final double value;
  final double maxAbs;
  final double width;
  final double height;
  final Color color;
  const HBar(this.value, this.maxAbs,
      {super.key,
      this.width = 100,
      this.height = 6,
      this.color = C.accent});
  @override
  Widget build(BuildContext context) =>
      CustomPaint(size: Size(width, height), painter: _HBarPainter(value, maxAbs, color));
}

class _HBarPainter extends CustomPainter {
  final double value, maxAbs;
  final Color color;
  _HBarPainter(this.value, this.maxAbs, this.color);
  @override
  void paint(Canvas canvas, Size size) {
    // 以 0 为基准从左起画正数，负数从右端向左
    final rr = Rect.fromLTWH(0, 0, size.width, size.height);
    canvas.drawRRect(
        RRect.fromRectAndRadius(rr, Radius.circular(size.height / 2)),
        Paint()..color = C.lineSoft);
    final frac = (value.abs() / (maxAbs <= 0 ? 1 : maxAbs)).clamp(0.0, 1.0);
    final barW = size.width * frac;
    final left = value >= 0 ? 0.0 : size.width - barW;
    if (barW > 0.5) {
      canvas.drawRRect(
          RRect.fromRectAndRadius(
              Rect.fromLTWH(left, 0, barW, size.height),
              Radius.circular(size.height / 2)),
          Paint()..color = color);
    }
  }

  @override
  bool shouldRepaint(covariant _HBarPainter o) => o.value != value;
}
