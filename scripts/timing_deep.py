# -*- coding: utf-8 -*-
"""关键检验：位置指标到底"反着用"还是"顺着用"？+ 估值/趋势分歧组合 + 参数敏感性 + 样本外。"""
import os
import numpy as np
import pandas as pd

BASE = r"E:\workspace\new"
PROC = os.path.join(BASE, "data", "processed")
OUT = os.path.join(BASE, "data", "output")
COST = 0.0005

panel = pd.read_csv(os.path.join(PROC, "timing_panel.csv"), index_col=0, parse_dates=True)
panel = panel.loc["1994-05-05":].copy()
px = panel["SPX"].astype(float)
rf = panel["rf_d"].fillna(0.0)
ret = px.pct_change().fillna(0.0)

def fwd(n):
    return px.shift(-n)/px - 1

def stat(mask, n=252, label=""):
    f = fwd(n)[mask].dropna()
    return {"情景": label, "样本日": int(mask.sum()), "占比%": mask.sum()/len(mask)*100,
            "未来1年均值%": f.mean()*100 if len(f) else np.nan,
            "未来1年中位%": f.median()*100 if len(f) else np.nan,
            "未来1年胜率%": (f>0).mean()*100 if len(f) else np.nan}

# ---- 1. 位置高/低的直觉检验（事件式）----
rows = []
rsi = panel["rsi14"]; dev = panel["ma200_dev"]; dda = panel["dd_abs"]; vix = panel["VIX"]
high252 = px/px.rolling(252, min_periods=60).max()-1

rows.append(stat(rsi > 70, 252, "RSI>70（超买）"))
rows.append(stat(rsi < 30, 252, "RSI<30（超卖）"))
rows.append(stat(dev > 0.10, 252, "高于200日线 10% 以上"))
rows.append(stat(dev < -0.10, 252, "低于200日线 10% 以上"))
rows.append(stat(high252 > -0.01, 252, "距52周高点<1%（创新高区）"))
rows.append(stat(high252 < -0.20, 252, "距52周高点>20%"))
rows.append(stat(dda > 0.20, 252, "自高点回撤>20%"))
rows.append(stat(dda < 0.03, 252, "自高点回撤<3%"))
rows.append(stat(vix > 30, 252, "VIX>30"))
rows.append(stat(vix < 13, 252, "VIX<13"))
rows.append(stat(px > px.rolling(200).mean(), 252, "价格>200日线"))
rows.append(stat(px < px.rolling(200).mean(), 252, "价格<200日线"))
ev = pd.DataFrame(rows)
ev.to_csv(os.path.join(OUT, "timing_events.csv"), index=False, encoding="utf-8")
pd.set_option("display.width", 220)
print('=== 事件式检验：这些「位置」状态出现后，未来 1 年表现 ===')
print(ev.round(2).to_string(index=False))

# ---- 2. 估值极高 + 趋势转弱（分歧组合）----
cape_p = panel["cape_p"]
weak = px < px.rolling(200).mean()
strong = px > px.rolling(200).mean()
rows2 = []
rows2.append(stat((cape_p>0.85) & weak, 252, "估值>85%分位 且 跌破200日线"))
rows2.append(stat((cape_p>0.85) & strong, 252, "估值>85%分位 且 站上200日线"))
rows2.append(stat((cape_p<0.40) & weak, 252, "估值<40%分位 且 跌破200日线"))
rows2.append(stat((cape_p<0.40) & strong, 252, "估值<40%分位 且 站上200日线"))
rows2.append(stat((cape_p>=0.5) & (cape_p<=0.85) & weak, 252, "估值中性 且 跌破200日线"))
rows2.append(stat((cape_p>=0.5) & (cape_p<=0.85) & strong, 252, "估值中性 且 站上200日线"))
dv = pd.DataFrame(rows2)
dv.to_csv(os.path.join(OUT, "timing_divergence.csv"), index=False, encoding="utf-8")
print("\n=== 估值 × 趋势 四象限（未来 1 年）===")
print(dv.round(2).to_string(index=False))

# ---- 3. 参数敏感性：均线长度 / 动量窗口 ----
rows3 = []
def bt(sig):
    w = sig.shift(1).fillna(0.0).clip(0,1)
    dr = w*ret + (1-w)*rf - w.diff().abs().fillna(0)*COST
    eq = (1+dr).cumprod(); yrs = len(dr)/252
    ann = eq.iloc[-1]**(1/yrs)-1
    mdd = (eq/eq.cummax()-1).min()
    return dict(年化=ann*100, 波动=dr.std(ddof=1)*np.sqrt(252)*100,
                夏普=(dr.mean()*252)/(dr.std(ddof=1)*np.sqrt(252)),
                回撤=mdd*100, 卡玛=ann*100/abs(mdd*100), 仓位=w.mean()*100,
                换手=w.diff().abs().fillna(0).sum()/yrs)

for m in [50, 100, 150, 200, 250, 300]:
    r = bt((px > px.rolling(m).mean()).astype(float)); r["参数"] = "MA%d" % m; rows3.append(r)
for m in [100, 150, 200, 250]:
    r = bt((px.rolling(m//2).mean() > px.rolling(m).mean()).astype(float)); r["参数"] = "MA%d/%d" % (m//2, m); rows3.append(r)
for m in [126, 189, 252, 315]:
    r = bt((px/px.shift(m)-1 > 0).astype(float)); r["参数"] = "动量%d日" % m; rows3.append(r)
sens = pd.DataFrame(rows3)[["参数","年化","波动","夏普","回撤","卡玛","仓位","换手"]]
sens.to_csv(os.path.join(OUT, "timing_sensitivity.csv"), index=False, encoding="utf-8")
print("\n=== 参数敏感性（MA200 家族 / 动量窗口）===")
print(sens.round(2).to_string(index=False))

# ---- 4. 样本外：1994-2010 训练选参，2011-2026 检验 ----
print("\n=== 样本外检验（2011-01-01 起）===")
oos = []
for nm, sig in [("买入持有", pd.Series(1.0, index=px.index)),
                ("MA200", (px > px.rolling(200).mean()).astype(float)),
                ("双均线50/200", (px.rolling(50).mean() > px.rolling(200).mean()).astype(float)),
                ("12M动量", (px/px.shift(252)-1 > 0).astype(float))]:
    w = sig.shift(1).fillna(0.0).clip(0,1).loc["2011-01-01":]
    r = ret.loc["2011-01-01":]; f = rf.loc["2011-01-01":]
    dr = w*r + (1-w)*f - w.diff().abs().fillna(0)*COST
    eq = (1+dr).cumprod(); yrs = len(dr)/252
    oos.append({"策略": nm, "年化%": (eq.iloc[-1]**(1/yrs)-1)*100,
                "波动%": dr.std(ddof=1)*np.sqrt(252)*100,
                "夏普": (dr.mean()*252)/(dr.std(ddof=1)*np.sqrt(252)),
                "最大回撤%": (eq/eq.cummax()-1).min()*100,
                "卡玛": (eq.iloc[-1]**(1/yrs)-1)*100/abs((eq/eq.cummax()-1).min()*100)})
o = pd.DataFrame(oos)
o.to_csv(os.path.join(OUT, "timing_oos.csv"), index=False, encoding="utf-8")
print(o.round(2).to_string(index=False))
