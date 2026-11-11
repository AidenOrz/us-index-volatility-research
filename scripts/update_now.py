# -*- coding: utf-8 -*-
"""用最新交易日（2026-11-09）刷新当前读数，并对比 11-06。"""
import os
import numpy as np
import pandas as pd

BASE = r"E:\workspace\new"
PROC = os.path.join(BASE, "data", "processed")
RAW = os.path.join(BASE, "data", "raw")
CB = os.path.join(RAW, "cboe_vol")
OUT = os.path.join(BASE, "data", "output")


def load_cboe(t):
    p = os.path.join(CB, t + "_History.csv")
    d = pd.read_csv(p)
    d["DATE"] = pd.to_datetime(d["DATE"], format="%m/%d/%Y")
    col = "CLOSE" if "CLOSE" in d.columns else d.columns[-1]
    return d.set_index("DATE")[col].astype(float).sort_index()


vix = load_cboe("VIX")
vix3m = load_cboe("VIX3M")
vix9d = load_cboe("VIX9D")
vix6m = load_cboe("VIX6M")
vvix = load_cboe("VVIX")
skew = load_cboe("SKEW")

px = pd.read_csv(os.path.join(PROC, "prices_close.csv"), index_col=0, parse_dates=True)["SPX"].astype(float)

last = min(vix.index[-1], px.index[-1])
print("最新交易日:", last.date())

ma200 = px.rolling(200).mean()
hi252 = px.rolling(252, min_periods=1).max()


def rp(s, win=2520, minp=1260):
    return s.rolling(win, min_periods=minp).apply(lambda a: (a[-1] > a[:-1]).mean(), raw=True)


rows = []
def add(k, v, u, note, prev=None):
    rows.append({"项目": k, "2026-11-09": v, "2026-11-06": prev, "单位": u, "说明": note})

v = vix.loc[last]; vp6 = vix.loc["2026-11-06"]
v3 = vix3m.reindex([last]).iloc[0]; v36 = vix3m.loc["2026-11-06"]
ts_last = v / v3 - 1; ts_prev = vp6 / v36 - 1
p = rp(vix).loc[last]; p_prev = rp(vix).loc["2026-11-06"]

add("VIX", round(v, 2), "点", "20-25 警觉区" if v >= 20 else "13-20 常态区", round(vp6, 2))
add("VIX 滚动10年分位", round(p * 100, 1), "%", "偏高" if p > .75 else "中性", round(p_prev * 100, 1))
add("VIX3M", round(v3, 2), "点", "", round(v36, 2))
add("VIX/VIX3M-1", round(ts_last * 100, 2), "%",
    "倒挂" if ts_last > 0.03 else ("平坦" if ts_last > -0.03 else "正常 contango"), round(ts_prev * 100, 2))
add("VIX9D", round(vix9d.loc[last], 2), "点", "短期", round(vix9d.loc["2026-11-06"], 2))
add("VIX6M", round(vix6m.loc[last], 2), "点", "长期", round(vix6m.loc["2026-11-06"], 2))
add("VVIX（波动率的波动率）", round(vvix.loc[last], 2), "点", "", round(vvix.loc["2026-11-06"], 2))
add("SKEW（尾部风险偏度）", round(skew.loc[last], 2), "点", "高=左尾贵", round(skew.loc["2026-11-06"], 2))
add("VIX / 20日均线", round(v / vix.rolling(20).mean().loc[last], 2), "倍", "", None)
hi63 = vix.rolling(63).max().loc[last]
add("VIX 自63日高点回落", round((v / hi63 - 1) * 100, 2), "%", f"63日高点 {hi63:.2f}", None)
add("SPX 距 200 日线", round((px.loc[last] / ma200.loc[last] - 1) * 100, 2), "%",
    "线上" if px.loc[last] > ma200.loc[last] else "线下", round((px.loc["2026-11-06"] / ma200.loc["2026-11-06"] - 1) * 100, 2))
add("SPX 距 52 周高点", round((px.loc[last] / hi252.loc[last] - 1) * 100, 2), "%", "", round((px.loc["2026-11-06"] / hi252.loc["2026-11-06"] - 1) * 100, 2))
add("SPX 收盘", round(px.loc[last], 2), "点", "", round(px.loc["2026-11-06"], 2))

d = pd.DataFrame(rows)
d.to_csv(os.path.join(OUT, "vix_now_20261109.csv"), index=False, encoding="utf-8-sig")
print(d.to_string(index=False))

print("\n=== 与 11-06 相比发生了什么 ===")
print("SPX: %.2f -> %.2f (%+.2f%%)" % (px.loc["2026-11-06"], px.loc[last], (px.loc[last] / px.loc["2026-11-06"] - 1) * 100))
print("VIX: %.2f -> %.2f (%+.1f%%)" % (vp6, v, (v / vp6 - 1) * 100))
print("VIX/VIX3M: %+.2f%% -> %+.2f%%  => 从倒挂回到 %s" % (
    ts_prev * 100, ts_last * 100, "正常 contango" if ts_last < -0.03 else "平坦"))
print("\n按 U 型刻度：VIX %.2f 落在 %s 档 -> 建议仓位 %s" % (
    v, "13-20" if v < 20 else ("20-25" if v < 25 else "25-30"),
    "80%" if v < 25 else "80%"))
