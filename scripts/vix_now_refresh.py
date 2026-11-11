# -*- coding: utf-8 -*-
"""把 vix_now.csv 刷新到最新交易日（2026-11-09），列结构与原文件保持一致。"""
import os
import pandas as pd

BASE = r"E:\workspace\new"
CB = os.path.join(BASE, "data", "raw", "cboe_vol")
PROC = os.path.join(BASE, "data", "processed")
OUT = os.path.join(BASE, "data", "output")


def load(t):
    d = pd.read_csv(os.path.join(CB, t + "_History.csv"))
    d["DATE"] = pd.to_datetime(d["DATE"], format="%m/%d/%Y")
    col = "CLOSE" if "CLOSE" in d.columns else d.columns[-1]
    return d.set_index("DATE")[col].astype(float).sort_index()


vix, vix3m = load("VIX"), load("VIX3M")
px = pd.read_csv(os.path.join(PROC, "prices_close.csv"), index_col=0, parse_dates=True)["SPX"].astype(float)
last = min(vix.index[-1], px.index[-1])
ma200 = px.rolling(200).mean()
hi252 = px.rolling(252, min_periods=1).max()
vp = vix.rolling(2520, min_periods=1260).apply(lambda a: (a[-1] > a[:-1]).mean(), raw=True)
cape_p = 0.981   # 沿用上一版 CAPE 10 年分位（月度数据，10 月未更新）

v = vix.loc[last]; v3 = vix3m.loc[last]
ts = v / v3 - 1
rows = []
def add(k, val, u, st):
    rows.append({"项目": k, "读数": val, "单位": u, "状态": st})

add("VIX 收盘", round(v, 2), "点", "极恐" if v > 40 else ("恐慌" if v > 30 else ("警觉" if v > 20 else ("常态" if v > 13 else "自满"))))
add("VIX 滚动10年分位", round(vp.loc[last] * 100, 1), "%", "极高分位" if vp.loc[last] > .90 else ("偏高" if vp.loc[last] > .75 else ("中性" if vp.loc[last] > .25 else "偏低")))
add("VIX3M", round(v3, 2), "点", "")
add("VIX/VIX3M-1", round(ts * 100, 2), "%", "倒挂(恐慌)" if ts > 0.03 else ("平坦" if ts > -0.03 else "正常 contango"))
add("VIX 20日均线", round(vix.rolling(20).mean().loc[last], 2), "点", "")
add("VIX / 20日均线", round(v / vix.rolling(20).mean().loc[last], 2), "倍", "急冲" if v > vix.rolling(20).mean().loc[last] * 1.5 else "常态")
add("VIX 5日变化", round((v / vix.iloc[-6] - 1) * 100, 2), "%", "")
add("SPX 距 200 日线", round((px.loc[last] / ma200.loc[last] - 1) * 100, 2), "%", "线上" if px.loc[last] > ma200.loc[last] else "线下")
add("SPX 距 52 周高点", round((px.loc[last] / hi252.loc[last] - 1) * 100, 2), "%", "")
add("CAPE 分位(10年)", round(cape_p * 100, 1), "%", "极贵" if cape_p > .90 else "偏高")

d = pd.DataFrame(rows)
d.to_csv(os.path.join(OUT, "vix_now.csv"), index=False, encoding="utf-8-sig")
print("最新交易日:", last.date())
print(d.to_string(index=False))
