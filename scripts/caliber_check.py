# -*- coding: utf-8 -*-
"""口径校验：无风险利率代理差异、股息影响、Sortino 修正。"""
import os
import numpy as np, pandas as pd
RAW = r"E:\workspace\new\data\raw"; PROC = r"E:\workspace\new\data\processed"

irx = pd.read_csv(os.path.join(RAW,"yahoo_IDX_IRX.csv"), parse_dates=["date"]).set_index("date")["close"]
tb  = pd.read_csv(os.path.join(RAW,"treasury_13w.csv"), parse_dates=["date"]).set_index("date")["yield_pct"]
both = irx.index.intersection(tb.index)
d = (tb.loc[both] - irx.loc[both])
print("13周国库券: 财政部券等价收益率 vs ^IRX 贴现率")
print("  重叠样本 %d 天 (%s ~ %s)" % (len(both), both[0].date(), both[-1].date()))
print("  平均差 %.3f 个百分点, 中位 %.3f, 最大 %.3f" % (d.mean(), d.median(), d.max()))
print("  ^IRX 均值 %.3f, 券等价 均值 %.3f" % (irx.loc[both].mean(), tb.loc[both].mean()))

# 股息影响：SP500 价格 vs 全收益
P = pd.read_csv(os.path.join(RAW,"yahoo_IDX_GSPC.csv"), parse_dates=["date"]).set_index("date")["adjclose"]
T = pd.read_csv(os.path.join(RAW,"yahoo_IDX_SP500TR.csv"), parse_dates=["date"]).set_index("date")["adjclose"]
idx = P.index.intersection(T.index)
p, t = P.loc[idx], T.loc[idx]
yrs = (idx[-1]-idx[0]).days/365.25
cagr_p = (p.iloc[-1]/p.iloc[0])**(1/yrs)-1
cagr_t = (t.iloc[-1]/t.iloc[0])**(1/yrs)-1
print("\n标普500 价格指数 vs 全收益指数 (%s ~ %s, %.2f 年)" % (idx[0].date(), idx[-1].date(), yrs))
print("  价格指数 CAGR %.2f%%   全收益 CAGR %.2f%%   股息贡献 %.2f 个百分点/年" % (cagr_p*100, cagr_t*100, (cagr_t-cagr_p)*100))

# 各指数在 1994-05 至 2026-11 的股息率估计（用 ETF 全收益 vs 指数价格）
def etf(tk):
    x = pd.read_csv(os.path.join(RAW,"yahoo_%s.csv"%tk), parse_dates=["date"]).set_index("date")["adjclose"]
    return x
for tk, nm in [("SPY","标普500"),("QQQ","纳指100"),("DIA","道指"),("IWM","罗素2000")]:
    e = etf(tk); e = e.loc["1994-05-05":]
    y2 = (e.index[-1]-e.index[0]).days/365.25
    print("  %-6s %s 全收益 CAGR %.2f%%（该 ETF 覆盖 %s 起）" % (tk, nm, ((e.iloc[-1]/e.iloc[0])**(1/y2)-1)*100, e.index[0].date()))
