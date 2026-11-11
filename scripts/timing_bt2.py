# -*- coding: utf-8 -*-
"""择时策略 v2：单指数 + 分年代 + 回撤规避率 + 参数敏感性。"""
import os
import numpy as np
import pandas as pd

BASE = r"E:\workspace\new"
PROC = os.path.join(BASE, "data", "processed")
OUT = os.path.join(BASE, "data", "output")
COST = 0.0005

panel = pd.read_csv(os.path.join(PROC, "timing_panel.csv"), index_col=0, parse_dates=True)
panel = panel.loc["1994-05-05":]
rf = panel["rf_d"].fillna(0.0)

def perf(dr, w, yrs=None):
    eq = (1+dr).cumprod()
    n = len(dr); yrs = n/252
    ann = eq.iloc[-1]**(1/yrs)-1
    vol = dr.std(ddof=1)*np.sqrt(252)
    sh = (dr.mean()*252)/(dr.std(ddof=1)*np.sqrt(252))
    mdd = (eq/eq.cummax()-1).min()
    ex = dr - rf.reindex(dr.index).fillna(0)
    dn = dr[dr < 0].std(ddof=1)*np.sqrt(252)
    return dict(累计=(eq.iloc[-1]-1)*100, 年化=ann*100, 波动=vol*100, 夏普=sh,
                索提诺=(ex.mean()*252)/dn if dn > 0 else np.nan,
                回撤=mdd*100, 卡玛=(ann*100)/abs(mdd*100) if mdd else np.nan,
                仓位=w.mean()*100, 换手=(w.diff().abs().fillna(0)).sum()/yrs)

def run(px, signal, name):
    ret = px.pct_change().fillna(0.0)
    w = signal.shift(1).fillna(0.0).clip(0, 1)
    dr = w*ret + (1-w)*rf - w.diff().abs().fillna(0)*COST
    return perf(dr, w)

rows = []
for c in ["SPX", "NDX", "SOX", "RUT"]:
    px = panel[c].dropna()
    if len(px) < 2000: continue
    ma200 = px.rolling(200).mean(); ma50 = px.rolling(50).mean()
    mom12 = px/px.shift(252)-1
    dd = px/px.cummax()-1

    sigs = {
        "买入持有": pd.Series(1.0, index=px.index),
        "MA200": (px > ma200).astype(float),
        "双均线50/200": (ma50 > ma200).astype(float),
        "12M动量": (mom12 > 0).astype(float),
        "MA200+回撤过滤": ((px > ma200) & (dd > -0.20)).astype(float),
        "MA200 且 波动<中位": ((px > ma200) & (px.pct_change().rolling(20).std() < px.pct_change().rolling(20).std().rolling(1260, min_periods=500).median())).astype(float),
    }
    for nm, sg in sigs.items():
        r = run(px, sg, nm)
        r.update({"指数": c, "策略": nm})
        rows.append(r)

res = pd.DataFrame(rows)[["指数","策略","累计","年化","波动","夏普","索提诺","回撤","卡玛","仓位","换手"]]
res.to_csv(os.path.join(OUT, "timing_multi.csv"), index=False, encoding="utf-8")
pd.set_option("display.width", 250)
print("=== 各指数 × 各择时规则 ===")
print(res.round(2).to_string(index=False))

# ---- 分年代（SPX）----
px = panel["SPX"].dropna()
ma200 = px.rolling(200).mean(); ma50 = px.rolling(50).mean()
mom12 = px/px.shift(252)-1
sigs = {"买入持有": pd.Series(1.0, index=px.index),
        "MA200": (px > ma200).astype(float),
        "双均线50/200": (ma50 > ma200).astype(float),
        "12M动量": (mom12 > 0).astype(float)}
dec_rows = []
for nm, sg in sigs.items():
    w = sg.shift(1).fillna(0.0).clip(0,1)
    ret = px.pct_change().fillna(0.0)
    dr = w*ret + (1-w)*rf - w.diff().abs().fillna(0)*COST
    for dec in ["1994-1999","2000-2009","2010-2019","2020-2026"]:
        a, b = dec.split("-")
        sub = dr.loc[a:b+"-12-31"]
        eq = (1+sub).cumprod()
        yrs = len(sub)/252
        dec_rows.append({"策略": nm, "年代": dec, "年化%": (eq.iloc[-1]**(1/yrs)-1)*100,
                         "波动%": sub.std(ddof=1)*np.sqrt(252)*100,
                         "夏普": (sub.mean()*252)/(sub.std(ddof=1)*np.sqrt(252)),
                         "最大回撤%": (eq/eq.cummax()-1).min()*100})
dec = pd.DataFrame(dec_rows)
dec.to_csv(os.path.join(OUT, "timing_by_decade.csv"), index=False, encoding="utf-8")
print("\n=== SPX 分年代 ===")
print(dec.pivot(index="策略", columns="年代", values="年化%").round(2).to_string())
print("\n（夏普）")
print(dec.pivot(index="策略", columns="年代", values="夏普").round(2).to_string())
