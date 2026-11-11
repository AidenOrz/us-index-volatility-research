# -*- coding: utf-8 -*-
"""最终策略集：把"位置"信号拆成 减仓(防御) 与 加仓(进攻) 两类，验证各自贡献。"""
import os
import numpy as np
import pandas as pd

BASE = r"E:\workspace\new"
PROC = os.path.join(BASE, "data", "processed")
OUT = os.path.join(BASE, "data", "output")
COST = 0.0005

panel = pd.read_csv(os.path.join(PROC, "timing_panel.csv"), index_col=0, parse_dates=True)
panel = panel.loc["1994-05-05":].copy()
px = panel["SPX"].astype(float); rf = panel["rf_d"].fillna(0.0)
ret = px.pct_change().fillna(0.0)
ma200 = px.rolling(200).mean(); ma50 = px.rolling(50).mean()
mom12 = px/px.shift(252) - 1
vix = panel["VIX"]; cape_p = panel["cape_p"]

def bt(sig, name):
    w = sig.shift(1).fillna(0.0).clip(0, 1)
    dr = w*ret + (1-w)*rf - w.diff().abs().fillna(0)*COST
    eq = (1+dr).cumprod(); yrs = len(dr)/252
    ann = eq.iloc[-1]**(1/yrs)-1
    mdd = (eq/eq.cummax()-1).min()
    vol = dr.std(ddof=1)*np.sqrt(252)
    ex = dr - rf
    dn = dr[dr < 0].std(ddof=1)*np.sqrt(252)
    return {"策略": name, "累计%": (eq.iloc[-1]-1)*100, "年化%": ann*100, "波动%": vol*100,
            "夏普": (dr.mean()*252)/(dr.std(ddof=1)*np.sqrt(252)),
            "索提诺": (ex.mean()*252)/dn if dn else np.nan,
            "最大回撤%": mdd*100, "卡玛": ann*100/abs(mdd*100),
            "平均仓位%": w.mean()*100, "年换手": w.diff().abs().fillna(0).sum()/yrs,
            "持有期占比%": (w > 0.01).mean()*100}

rows = []
rows.append(bt(pd.Series(1.0, index=px.index), "买入持有"))
# 纯趋势
t1 = ((px > ma200) & (ma50 > ma200)).astype(float)
rows.append(bt(t1, "防御：双均线 50/200"))
# 趋势 + 估值封顶（估值极高分位时把仓位上限压到 0.5）
rows.append(bt(t1 * (1 - 0.5*(cape_p > 0.90).astype(float)), "防御+估值封顶(>90%分位打5折)"))
# 趋势 + VIX 恐慌加仓（进攻）
off = t1.copy()
off = off.where(~(vix > 30), 1.0)          # 恐慌时即便跌破均线也满仓
rows.append(bt(off, "进攻：双均线 + VIX>30 逆势满仓"))
# 趋势 + 回撤加仓
off2 = t1.copy()
dd = px/px.cummax() - 1
off2 = off2.where(~((dd < -0.20) & (vix > 30)), 1.0)
rows.append(bt(off2, "进攻：双均线 + 深跌+恐慌 满仓"))
# 用估值封顶 + VIX 加仓 合成
comb = (t1 * (1 - 0.5*(cape_p > 0.90).astype(float)))
comb = comb.where(~(vix > 30), np.maximum(comb, 0.9))
rows.append(bt(comb, "合成：防御 + 估值封顶 + 恐慌加仓"))
# 只做估值封顶（无趋势）
rows.append(bt((1 - 0.6*(cape_p > 0.90).astype(float)), "仅估值封顶（无趋势）"))
# 7 成常驻底仓 + 3 成趋势择时（更贴近实操）
rows.append(bt(0.7 + 0.3*t1, "70% 底仓 + 30% 趋势择时"))
rows.append(bt(0.5 + 0.5*t1, "50% 底仓 + 50% 趋势择时"))

res = pd.DataFrame(rows).sort_values("夏普", ascending=False)
res.to_csv(os.path.join(OUT, "timing_final.csv"), index=False, encoding="utf-8")
pd.set_option("display.width", 250)
print("=== 最终策略对比（1994-05-05~2026-11-06，单边 5bp）===")
print(res.round(2).to_string(index=False))

# 曲线
curves = {}
def curve(sig, name):
    w = sig.shift(1).fillna(0.0).clip(0,1)
    dr = w*ret + (1-w)*rf - w.diff().abs().fillna(0)*COST
    curves[name] = (1+dr).cumprod()
curve(pd.Series(1.0, index=px.index), "买入持有")
curve(t1, "双均线 50/200")
curve(comb, "合成策略")
curve(0.7 + 0.3*t1, "70%底仓+30%择时")
pd.DataFrame(curves).to_csv(os.path.join(PROC, "timing_equity.csv"), encoding="utf-8")
print("\nsaved equity curves:", list(curves.keys()))
