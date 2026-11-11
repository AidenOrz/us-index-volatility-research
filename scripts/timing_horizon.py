# -*- coding: utf-8 -*-
"""长周期检验 v2：估值对 3/5/10 年收益的预测力。样本用全历史（SPX 1962 起 / CAPE 1871 起）。"""
import os
import numpy as np
import pandas as pd

BASE = r"E:\workspace\new"
PROC = os.path.join(BASE, "data", "processed")
OUT = os.path.join(BASE, "data", "output")

def spearman(a, b):
    return float(pd.Series(np.asarray(a,float)).rank().corr(pd.Series(np.asarray(b,float)).rank()))

panel = pd.read_csv(os.path.join(PROC, "timing_panel.csv"), index_col=0, parse_dates=True)
df = panel.copy()
spx = df["SPX"].astype(float)

HOR = {"1年": 252, "3年": 756, "5年": 1260, "10年": 2520}
for lab, n in HOR.items():
    df["f_"+lab] = spx.shift(-n)/spx - 1
    df["fa_"+lab] = (1+df["f_"+lab])**(1/(n/252)) - 1   # 年化

INDS = [
    ("CAPE 席勒市盈率",  "cape"),
    ("市盈率 PE",        "pe"),
    ("股息率",           "dy"),
    ("10Y 国债利率",      "TNX"),
]

rows = []
for name, col in INDS:
    if col not in df: continue
    for lab in HOR:
        f = df["f_"+lab]; s = df[col].astype(float)
        m = (s.notna() & f.notna()).values
        n = HOR[lab]
        if m.sum() < n*6:
            rows.append({"指标": name, "期限": lab, "IC": np.nan, "t": np.nan, "有效日": int(m.sum())}); continue
        idx = np.arange(0, m.sum(), n)
        xs, ys = s[m].values[idx], f[m].values[idx]
        if len(xs) < 6 or np.std(xs) < 1e-9:
            rows.append({"指标": name, "期限": lab, "IC": np.nan, "t": np.nan, "有效日": int(m.sum())}); continue
        ic = spearman(xs, ys); k = max(len(xs)-2,1)
        rows.append({"指标": name, "期限": lab, "IC": ic, "t": ic*np.sqrt(k/max(1-ic**2,1e-9)), "有效日": int(m.sum())})

r = pd.DataFrame(rows)
r.to_csv(os.path.join(OUT, "timing_ic_horizon.csv"), index=False, encoding="utf-8")
piv = r.pivot(index="指标", columns="期限", values="IC")
piv = piv[[c for c in ["1年","3年","5年","10年"] if c in piv.columns]]
print("=== 分期限 Spearman IC（正值=位置越高未来收益越低，已对 CAPE/PE/利率取反前先看原值）===")
print(piv.round(3).to_string())
print("\n（说明：此处 IC 为指标原值与未来收益的相关，CAPE/PE 为负说明估值越高收益越低）")

# CAPE 绝对值分层 -> 未来 10 年年化收益
print("\n=== CAPE 绝对值分层 与 未来年化收益（1962 起，SPX 价格口径）===")
bins = [0, 10, 15, 20, 25, 30, 40, 100]
labels = ["<10","10-15","15-20","20-25","25-30","30-40",">40"]
for lab in ["1年","5年","10年"]:
    s = df["cape"]; f = df["fa_"+lab]
    m = s.notna() & f.notna()
    sub = pd.DataFrame({"c": s[m], "f": f[m]})
    sub["b"] = pd.cut(sub["c"], bins, labels=labels)
    g = sub.groupby("b", observed=True)["f"].agg(["mean","count"])
    g["mean"] = g["mean"]*100
    print("\n-- 年化，%s --" % lab)
    print(g.round(2).to_string())

# 当前 CAPE 所处位置
cur = panel["cape"].dropna().iloc[-1]
hist = panel["cape"].dropna()
print("\n当前 CAPE = %.2f；1871 以来分位 %.1f%%；1962 以来分位 %.1f%%" % (
    cur, (hist < cur).mean()*100, (hist.loc["1962":] < cur).mean()*100))
