# -*- coding: utf-8 -*-
"""位置指标的有效性检验：时点分位分层 + 前瞻收益 + IC（无前视，不依赖 scipy）。"""
import os
import numpy as np
import pandas as pd

BASE = r"E:\workspace\new"
PROC = os.path.join(BASE, "data", "processed")
OUT = os.path.join(BASE, "data", "output")

def spearman(a, b):
    a = pd.Series(np.asarray(a, float)); b = pd.Series(np.asarray(b, float))
    return float(a.rank().corr(b.rank()))

df = pd.read_csv(os.path.join(PROC, "timing_panel.csv"), index_col=0, parse_dates=True)
df = df.loc["1994-05-05":].copy()
spx = df["SPX"]

FWD = [21, 63, 126, 252]
for n in FWD:
    df["fwd%d" % n] = spx.shift(-n) / spx - 1

INDS = {
    "200日线偏离":      ("ma200_dev", +1),
    "距历史高点回撤":    ("dd_abs", +1),
    "12月动量":        ("mom12m", +1),
    "RSI(14)":        ("rsi14", +1),
    "20日年化波动":     ("vol20", +1),
    "VIX 水平":        ("VIX", +1),
    "VIX 期限倒挂":     ("vix_ts", +1),
    "信用资产动量(63日)": ("credit_mom63", -1),
    "等权/市值宽度(63日)": ("breadth_mom63", -1),
    "期限利差(10Y-3M)":  ("curve", -1),
    "CAPE 席勒市盈率":   ("cape", +1),
    "市盈率 PE":       ("pe", +1),
    "股息率":          ("dy", -1),
}

def pit_pct(s, minp=750):
    return s.expanding(min_periods=minp).apply(lambda a: (a[-1] > a[:-1]).mean(), raw=True)

rows_ic, rows_q = [], []
panel_pct = pd.DataFrame(index=df.index)

for name, (col, d) in INDS.items():
    if col not in df.columns:
        print("skip", name); continue
    s = df[col].astype(float)
    p = pit_pct(s)
    panel_pct[name] = p
    score = p if d > 0 else (1 - p)
    panel_pct[name + "_s"] = score

    rec = {"指标": name}
    for n in FWD:
        f = df["fwd%d" % n]
        m = (score.notna() & f.notna()).values
        if m.sum() < 400:
            rec["IC%d" % n] = np.nan; rec["t%d" % n] = np.nan; continue
        idx = np.arange(0, m.sum(), n)
        xs = score[m].values[idx]; ys = f[m].values[idx]
        if len(xs) < 20 or np.std(xs) == 0:
            rec["IC%d" % n] = np.nan; rec["t%d" % n] = np.nan; continue
        ic = spearman(xs, ys)
        k = max(len(xs) - 2, 1)
        rec["IC%d" % n] = ic
        rec["t%d" % n] = ic * np.sqrt(k / max(1 - ic**2, 1e-9))
    rows_ic.append(rec)

    for q_ in range(5):
        lo, hi = q_/5, (q_+1)/5
        m = (score >= lo) & (score < hi) if q_ < 4 else (score >= lo) & (score <= 1.0)
        sub = df.loc[m.fillna(False).astype(bool)]
        r = {"指标": name, "分位区间": "%d-%d%%" % (int(lo*100), int(hi*100)), "样本日": len(sub)}
        for n in FWD:
            f = sub["fwd%d" % n].dropna()
            r["均值%d日%%" % n] = f.mean()*100 if len(f) else np.nan
            r["中位%d日%%" % n] = f.median()*100 if len(f) else np.nan
            r["胜率%d日%%" % n] = (f > 0).mean()*100 if len(f) else np.nan
        rows_q.append(r)

ic = pd.DataFrame(rows_ic)
ic.to_csv(os.path.join(OUT, "timing_ic.csv"), index=False, encoding="utf-8")
q = pd.DataFrame(rows_q)
q.to_csv(os.path.join(OUT, "timing_quintile.csv"), index=False, encoding="utf-8")
panel_pct.to_csv(os.path.join(PROC, "timing_pct.csv"), encoding="utf-8")

pd.set_option("display.width", 200)
print("=== IC（score 越高=位置越高；非重叠抽样 Spearman）===")
print(ic.round(3).to_string(index=False))
print()
print("=== 未来 12 个月：五分层 ===")
t = q[q["分位区间"].isin(["0-20%","20-40%","40-60%","60-80%","80-100%"])][["指标","分位区间","样本日","均值252日%","胜率252日%"]]
print(t.round(2).to_string(index=False))
