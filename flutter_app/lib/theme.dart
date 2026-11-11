import 'package:flutter/material.dart';

/// 配色：涨红跌绿沿用 A 股习惯；风险等级另用语义色并由文字标注兜底。
class C {
  static const bg = Color(0xFF0A0D12);
  static const panel = Color(0xFF11151C);
  static const panel2 = Color(0xFF161C25);
  static const line = Color(0xFF232B37);
  static const lineSoft = Color(0xFF1A212B);
  static const text = Color(0xFFE7EBF1);
  static const text2 = Color(0xFF98A3B3);
  static const text3 = Color(0xFF5F6A79);
  static const up = Color(0xFFE5484D);
  static const down = Color(0xFF2FA36B);
  static const warn = Color(0xFFF0B429);
  static const accent = Color(0xFF4EA8DE);
  static const violet = Color(0xFF9B8CF5);
}

TextStyle sans(double size,
        {FontWeight w = FontWeight.w400,
        Color color = C.text,
        double? h,
        double? ls}) =>
    TextStyle(
        fontFamily: 'AppSans',
        fontSize: size,
        fontWeight: w,
        color: color,
        height: h,
        letterSpacing: ls);

TextStyle mono(double size,
        {FontWeight w = FontWeight.w500,
        Color color = C.text,
        double? ls,
        double? h}) =>
    TextStyle(
        fontFamily: 'AppMono',
        fontSize: size,
        fontWeight: w,
        color: color,
        height: h,
        letterSpacing: ls,
        fontFeatures: const [FontFeature.tabularFigures()]);

String fx(double? v, [int nd = 2]) => v == null ? '—' : v.toStringAsFixed(nd);

String fsign(double? v, [int nd = 2, String suffix = '%']) {
  if (v == null) return '—';
  final s = v >= 0 ? '+' : '';
  return s + v.toStringAsFixed(nd) + suffix;
}

String fint(int v) {
  final s = v.abs().toString();
  final b = StringBuffer();
  for (var i = 0; i < s.length; i++) {
    if (i > 0 && (s.length - i) % 3 == 0) b.write(',');
    b.write(s[i]);
  }
  return (v < 0 ? '-' : '') + b.toString();
}

Color chgColor(double? v) {
  if (v == null) return C.text2;
  if (v > 0.0001) return C.up;
  if (v < -0.0001) return C.down;
  return C.text2;
}

/// 分位数 → 颜色（低=绿更安全，高=红更警戒）
Color pctColor(double? p) {
  if (p == null) return C.text2;
  if (p >= 85) return C.up;
  if (p >= 65) return C.warn;
  if (p >= 35) return C.accent;
  return C.down;
}
