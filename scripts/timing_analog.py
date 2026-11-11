# -*- coding: utf-8 -*-
"""历史类比 v2：只取具备完整 3 年前瞻数据的日期，且同一季度只保留一个，避免近邻样本重复。"""
import os
import numpy as np
import pandas as pd

BASE = r"E:\workspace\new"
PROC = os.path.join(BASE, "data", "processed")
OUT = os.path.join(BASE, "data", "output")

panel = pd.read_csv(os.path.join(PROC, "timing_panel.csv"), index_col=0, parse_dates=True)
px = panel["SPX"].astype(float)

FEATS = ["cape_p", "pe_p", "dy_p", "ma200dev_p", "rsi_p", "vix_p", "tnx_p", "curve_p", "credit_p", "breadth_p"]
d = panel.loc["1994-05-05":, FEATS].copy()
z = (d - d.rolling(2520, min_periods=1000).mean()) / d.rolling(2520, min_periods=1000).std()
f1 = px.shift(-252)/px - 1
f3 = px.shift(-756)/px - 1

ok = z.dropna()
ok = ok.loc[:f3.dropna().index[-1]]      # 只保留有完整 3 年前瞻的日期
today = z.iloc[-1]
dist = ((ok - today)**2).sum(axis=1)**0.5

# 同季度只保留一例
picked, seen = [], set()
for dt, dv in dist.sort_values().items():
    key = (dt.year, (dt.month-1)//3)
    if key in seen: continue
    seen.add(key); picked.append((dt, dv))
    if len(picked) >= 12: break

recs = []
for dt, dv in picked:
    recs.append({"日期": str(dt.date()), "距离": round(float(dv), 2),
                 "未来1年%": round(float(f1.get(dt, np.nan))*100, 2),
                 "未来3年%": round(float(f3.get(dt, np.nan))*100, 2)})
nr = pd.DataFrame(recs)
nr.to_csv(os.path.join(OUT, "timing_analogues.csv"), index=False, encoding="utf-8")
print("=== 最相似的 12 个历史时点（同季度去重）===")
print(nr.to_string(index=False))
print("\n均值：1年 %.2f%% / 3年 %.2f%%；胜率：1年 %.0f%% / 3年 %.0f%%；中位：1年 %.2f%% / 3年 %.2f%%" % (
    nr["未来1年%"].mean(), nr["未来3年%"].mean(),
    (nr["未来1年%"]>0).mean()*100, (nr["未来3年%"]>0).mean()*100,
    nr["未来1年%"].median(), nr["未来3年%"].median()))
