# -*- coding: utf-8 -*-
"""Subset CJK + mono fonts to the glyphs actually used by the app."""
import os, sys, json, glob
from fontTools import subset
from fontTools.ttLib import TTFont, TTCollection
sys.stdout.reconfigure(encoding="utf-8")

ROOT = r"E:\workspace\new\flutter_app"
OUT = os.path.join(ROOT, "assets", "fonts")
os.makedirs(OUT, exist_ok=True)

# 1) 收集所有会出现的字符：源码 + dashboard.json
chars = set()
for p in glob.glob(os.path.join(ROOT, "lib", "*.dart")) + [os.path.join(ROOT, "assets", "dashboard.json")]:
    if os.path.exists(p):
        with open(p, encoding="utf-8") as f:
            chars |= set(f.read())

# ASCII 全量 + 常用标点 + 数字符号
for c in range(0x20, 0x7F):
    chars.add(chr(c))
chars |= set("，。、；：「」『』（）—…·《》〈〉【】〔〕％–~±×÷≤≥≠≈√∞°′″‰↑↓←→▲▼■□●○◆◇★☆✓✗⚠① ②③④⑤⑥⑦⑧⑨⑩")
chars |= set("αβγδεζηθικλμνξοπρστυφχψωΑΒΓΔΕΖΗΘΙΚΛΜΝΞΟΠΡΣΤΥΦΧΨΩ")
chars.discard("\n"); chars.discard("\r"); chars.discard("\t")
text = "".join(sorted(chars))
print("unique chars:", len(text))

def ttc_extract(path, idx=0):
    coll = TTCollection(path)
    return coll.fonts[idx]

def build(src, dst, is_ttc=False, idx=0, wght=None):
    if is_ttc:
        font = ttc_extract(src, idx)
        tmp = dst + ".tmp.ttf"
        font.save(tmp)
        src2 = tmp
    else:
        src2 = src
    if wght is not None:
        from fontTools.varLib import instancer
        f = TTFont(src2)
        if "fvar" in f:
            axes = {a.axisTag: float(a.defaultValue) for a in f["fvar"].axes}
            if "wght" in axes:
                axes["wght"] = float(wght)
                inst = instancer.instantiateVariableFont(f, axes, updateFontNames=True)
                tmpw = dst + ".w.ttf"
                inst.save(tmpw)
                f.close()
                src2 = tmpw
        else:
            f.close()
    opts = subset.Options()
    opts.layout_features = ["*"]
    opts.name_IDs = ["*"]
    opts.name_legacy = True
    opts.notdef_outline = True
    opts.recalc_bounds = True
    opts.drop_tables += ["DSIG"]
    font = subset.load_font(src2, opts)
    sub = subset.Subsetter(options=opts)
    sub.populate(text=text)
    sub.subset(font)
    subset.save_font(font, dst, opts)
    font.close()
    for p in (src2,):
        if p != src and p.endswith(".ttf") and ".w.ttf" in p and os.path.exists(p):
            os.remove(p)
    if is_ttc and os.path.exists(src2):
        os.remove(src2)
    print("  ->", os.path.basename(dst), round(os.path.getsize(dst)/1024, 1), "KB")

W = r"C:\Windows\Fonts"
print("NotoSansSC ...")
build(os.path.join(W, "NotoSansSC-VF.ttf"), os.path.join(OUT, "NotoSC.otf"), wght=400)
build(os.path.join(W, "NotoSansSC-VF.ttf"), os.path.join(OUT, "NotoSC-Bold.otf"), wght=700)
print("mono ...")
build(os.path.join(W, "CascadiaMono.ttf"), os.path.join(OUT, "Mono.ttf"), wght=400)
build(os.path.join(W, "CascadiaMono.ttf"), os.path.join(OUT, "Mono-Bold.otf"), wght=700)
print("done")
