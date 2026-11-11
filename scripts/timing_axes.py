# -*- coding: utf-8 -*-
"""双轴 v3：只用在 1994 起就完整的成分，样本覆盖全区间。"""
import os
import numpy as np
import pandas as pd

BASE = r"E:\workspace\new"
PROC = os.path.join(BASE, "data", "processed"); OUT = os.path.join(BASE, "data", "output")

def roll_pct(s, win=2520, minp=1000):
    return s.rolling(win, min_periods=minp).apply(lambda a: (a[-1] > a[:-1]).mean(), raw=True)

p = pd.read_csv(os.path.join(PROC, "timing_panel.csv"), index_col=0, parse_dates=True)
p["q_cape"]  = roll_pct(p["cape"].astype(float))
p["q_pe"]    = roll_pct(p["pe"].astype(float))
p["q_ma200"] = roll_pct(p["ma200_dev"].astype(float))
p["q_rsi"]   = roll_pct(p["rsi14"].astype(float))
p["q_mom"]   = roll_pct(p["mom12m"].astype(float))
p["q_vol"]   = roll_pct(p["vol20"].astype(float))

V = (0.6*p["q_cape"] + 0.4*p["q_pe"])
T = (0.45*p["q_ma200"] + 0.30*p["q_rsi"] + 0.25*p["q_mom"])
px = p["SPX"].astype(float)

d = pd.DataFrame({"V": V, "T": T}).loc["1994-05-05":].dropna()
print("双轴样本 %d 日：%s ~ %s" % (len(d), d.index[0].date(), d.index[-1].date()))

def sp(a,b): return float(pd.Series(np.asarray(a,float)).rank().corr(pd.Series(np.asarray(b,float)).rank()))

rows = []
for lab, n in [("1年",252),("3年",756),("5年",1260)]:
    f = px.shift(-n)/px - 1
    sub = pd.DataFrame({"V": d["V"], "T": d["T"], "f": f.reindex(d.index)}).dropna()
    sub["VH"] = sub["V"] >= 0.5; sub["TH"] = sub["T"] >= 0.5
    for (vh, th), g in sub.groupby(["VH","TH"]):
        a = ("估值高" if vh else "估值低") + " × " + ("趋势强" if th else "趋势弱")
        rows.append({"期限": lab, "象限": a, "样本日": len(g), "占比%": len(g)/len(sub)*100,
                     "均值%": g["f"].mean()*100, "中位%": g["f"].median()*100, "胜率%": (g["f"]>0).mean()*100})
    idx = np.arange(0, len(sub), n)
    print("%s：估值轴 IC=%+.3f  趋势轴 IC=%+.3f  (独立观测 %d)" % (
        lab, sp(sub["V"].values[idx], sub["f"].values[idx]),
        sp(sub["T"].values[idx], sub["f"].values[idx]), len(idx)))

qd = pd.DataFrame(rows).sort_values(["期限","象限"])
qd.to_csv(os.path.join(OUT, "timing_quadrant.csv"), index=False, encoding="utf-8")
pd.set_option("display.width", 220)
print("\n=== 四象限 ===")
print(qd.round(2).to_string(index=False))
cur = d.iloc[-1]
print("\n当前：估值轴 %.3f（1994 以来分位 %.1f%%）、趋势轴 %.3f（分位 %.1f%%）" % (
    cur["V"], (d["V"] < cur["V"]).mean()*100, cur["T"], (d["T"] < cur["T"]).mean()*100))
d.to_csv(os.path.join(PROC, "timing_axes.csv"), encoding="utf-8")
