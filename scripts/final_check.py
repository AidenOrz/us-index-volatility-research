# -*- coding: utf-8 -*-
import re, os
p = r"E:\workspace\new\output\美股主要指数系统性回测与对比分析.html"
s = open(p, encoding="utf-8").read()
print("size KB", round(os.path.getsize(p)/1024, 1))
print("pct2", s.count("%%"), "pctS", s.count("%s"), "nan", s.count(">nan<"))
print("sections", s.count("<section"), "tables", s.count("<table"), "imgs", s.count("<img "))
print("doctype", s.startswith("<!DOCTYPE html>"), "closed", s.rstrip().endswith("</html>"))
# 只检查 body 内，跳过 base64
i = s.find("<main>"); j = s.find("</main>")
body = re.sub(r'base64,[A-Za-z0-9+/=]+', "base64,X", s[i:j])
VOID = {"br","img","hr","meta","link","input"}
stack, errs = [], []
for m in re.finditer(r"<(/?)([a-zA-Z][a-zA-Z0-9]*)[^>]*?(/?)>", body):
    closing, tag, selfc = m.group(1), m.group(2).lower(), m.group(3)
    if tag in VOID or selfc: continue
    if not closing: stack.append(tag)
    else:
        if stack and stack[-1] == tag: stack.pop()
        else: errs.append((tag, stack[-1] if stack else None))
print("body 未闭合:", stack[:8], "错配:", errs[:8])
