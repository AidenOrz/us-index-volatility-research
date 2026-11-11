# -*- coding: utf-8 -*-
"""分解：位置温度计的 5 个分项，各自对未来收益的方向是否一致？"""
import os
import numpy as np
import pandas as pd

BASE = r"E:\workspace\new"
PROC = os.path.join(BASE, "data", "processed"); OUT = os.path.join(BASE, "data", "output")

def spearman(a, b):
    return float(pd.Series(np.asarray(a,float)).rank().corr(pd.Series(np.asarray(b,float)).rank()))

panel = pd.read_csv(os.path.join(PROC, "timing_panel.csv"), index_col=0, parse_dates=True).loc["1994-05-05":]
comp = pd.read_csv(os.path.join(PROC, "timing_composite.csv"), index_col=0, parse_dates=True).loc["1994-05-05":]
px = panel["SPX"].astype(float)

rows = []
for col in ["估值","趋势","情绪","信用与宽度","宏观","综合"]:
    s = comp[col].dropna()
    for lab, n in [("1年",252),("3年",756),("5年",1260)]:
        f = px.shift(-n)/px - 1
        m = s.notna() & f.notna()
        sub = pd.DataFrame({"s": s[m], "f": f[m]})
        if len(sub) < 400: continue
        sub["q"] = pd.qcut(sub["s"], 5, labels=False, duplicates="drop")
        g = sub.groupby("q")["f"].mean()*100
        idx = np.arange(0, len(sub), n)
        ic = spearman(sub["s"].values[idx], sub["f"].values[idx])
        rows.append({"分项": col, "期限": lab, "IC": ic,
                     "Q1%": g.get(0, np.nan), "Q2%": g.get(1, np.nan), "Q3%": g.get(2, np.nan),
                     "Q4%": g.get(3, np.nan), "Q5%": g.get(4, np.nan),
                     "Q5-Q1(pp)": g.get(4, np.nan) - g.get(0, np.nan)})
r = pd.DataFrame(rows)
r.to_csv(os.path.join(OUT, "timing_subscore.csv"), index=False, encoding="utf-8")
pd.set_option("display.width", 200)
print("=== 分项温度 → 未来收益（Q1=温度最低，Q5=温度最高）===")
print(r.round(2).to_string(index=False))

# CAPE 绝对值分层表 + >40 的日期分布
print("\n=== CAPE 分层 × 未来年化收益 ===")
bins = [0,10,15,20,25,30,40,200]
labels = ["<10","10-15","15-20","20-25","25-30","30-40",">40"]
out = []
for lab, n in [("1年",252),("5年",1260),("10年",2520)]:
    fa = (px.shift(-n)/px)**(252.0/n) - 1
    s = panel["cape"]
    m = s.notna() & fa.notna()
    sub = pd.DataFrame({"c": s[m], "f": fa[m], "d": fa[m].index})
    sub["b"] = pd.cut(sub["c"], bins, labels=labels)
    for b, g in sub.groupby("b", observed=True):
        out.append({"期限": lab, "CAPE区间": str(b), "样本日": len(g),
                    "年化收益%": g["f"].mean()*100, "中位%": g["f"].median()*100,
                    "胜率%": (g["f"]>0).mean()*100,
                    "年份范围": "%s~%s" % (g["d"].min().year, g["d"].max().year)})
cb = pd.DataFrame(out)
cb.to_csv(os.path.join(OUT, "timing_cape_bins.csv"), index=False, encoding="utf-8")
print(cb.round(2).to_string(index=False))
