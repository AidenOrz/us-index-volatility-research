# -*- coding: utf-8 -*-
"""择时策略回测：趋势 / 回撤 / 估值 / 波动 / 合成，对比买入持有。

规则全部只用当日及之前的信息（信号在 t 日收盘生成，t+1 日起生效），避免前视。
现金收益用 ^IRX 日化；换手按单边 5bp 计成本。
"""
import os
import numpy as np
import pandas as pd

BASE = r"E:\workspace\new"
PROC = os.path.join(BASE, "data", "processed")
OUT = os.path.join(BASE, "data", "output")

df = pd.read_csv(os.path.join(PROC, "timing_panel.csv"), index_col=0, parse_dates=True)
df = df.loc["1994-05-05":].copy()
px = df["SPX"].astype(float)
ret = px.pct_change().fillna(0.0)
rf = df["rf_d"].fillna(0.0)

# 信号统一：w = 目标仓位（0~1），在 t 日收盘决定，t+1 日生效
n = len(df)
W = pd.DataFrame(index=df.index)

# ---------- 基准 ----------
W["买入持有"] = 1.0

# ---------- 趋势类 ----------
ma200 = px.rolling(200).mean()
ma50 = px.rolling(50).mean()
W["趋势 MA200"] = (px > ma200).astype(float)
W["趋势 MA200+2%缓冲"] = np.where(px > ma200*1.02, 1.0, np.where(px < ma200*0.98, 0.0, np.nan))
W["趋势 MA200+2%缓冲"] = pd.Series(W["趋势 MA200+2%缓冲"], index=df.index).ffill().fillna(0.0)
W["双均线 50/200"] = (ma50 > ma200).astype(float)
# 12 个月绝对动量
mom12 = px / px.shift(252) - 1
W["绝对动量 12M"] = (mom12 > 0).astype(float)
# 12M 动量 + 200 日线双重确认
W["动量+趋势双确认"] = ((mom12 > 0) & (px > ma200)).astype(float)

# ---------- 回撤 / 逆向类 ----------
dd = px / px.cummax() - 1                      # ≤0
ath = px.cummax()
# 深度回撤买入：回撤 >15% 满仓，回撤 <3%（接近新高）减半
w = pd.Series(np.nan, index=df.index)
w[dd <= -0.15] = 1.0
w[(dd > -0.15) & (dd <= -0.05)] = 0.8
w[dd > -0.05] = 0.6
W["回撤加仓"] = w.ffill().fillna(0.6)

# VIX 逆向：恐慌加仓
vix = df["VIX"].astype(float)
w = pd.Series(0.6, index=df.index)
w[vix >= 30] = 1.0
w[(vix >= 20) & (vix < 30)] = 0.85
w[vix < 15] = 0.5
W["VIX 逆向"] = w

# ---------- 估值类 ----------
cape = df["cape"].astype(float)
cape_p = cape.expanding(min_periods=750).apply(lambda a: (a[-1] > a[:-1]).mean(), raw=True)
w = pd.Series(np.nan, index=df.index)
w[cape_p >= 0.90] = 0.4
w[(cape_p >= 0.75) & (cape_p < 0.90)] = 0.6
w[(cape_p >= 0.25) & (cape_p < 0.75)] = 0.85
w[(cape_p >= 0.10) & (cape_p < 0.25)] = 1.0
w[cape_p < 0.10] = 1.0
W["估值分位 CAPE"] = w.ffill().fillna(0.85)

# 股息率
dy = df["dy"].astype(float)
dy_p = dy.expanding(min_periods=750).apply(lambda a: (a[-1] < a[:-1]).mean(), raw=True)  # 低分位=贵
w = pd.Series(np.nan, index=df.index)
w[dy_p >= 0.90] = 0.4
w[(dy_p >= 0.75) & (dy_p < 0.90)] = 0.6
w[(dy_p >= 0.25) & (dy_p < 0.75)] = 0.85
w[dy_p < 0.25] = 1.0
W["估值分位 股息率"] = w.ffill().fillna(0.85)

# ---------- 合成打分 ----------
# 每个子信号给 0/0.5/1 分，取平均作为仓位
def s_trend():
    return ((px > ma200).astype(float) + (ma50 > ma200).astype(float) + (mom12 > 0).astype(float)) / 3.0

def s_val():
    z = pd.Series(np.nan, index=df.index)
    z[cape_p >= 0.85] = 0.0
    z[(cape_p >= 0.5) & (cape_p < 0.85)] = 0.5
    z[(cape_p >= 0.3) & (cape_p < 0.5)] = 0.8
    z[cape_p < 0.3] = 1.0
    return z.ffill().fillna(0.5)

def s_fear():
    z = pd.Series(0.5, index=df.index)
    z[vix >= 30] = 1.0
    z[vix < 14] = 0.2
    return z

W["合成 三因子等权"] = (0.5*s_trend() + 0.3*s_val() + 0.2*s_fear()).clip(0, 1)
# 只做趋势确认后再看情绪（避免半仓长期拖累）
base_trend = ((px > ma200) & (ma50 > ma200)).astype(float)
W["合成 趋势闸门+估值"] = np.where(base_trend > 0,
                                (0.6 + 0.4*(1-cape_p.fillna(0.5))).clip(0, 1),
                                (0.3*(1-cape_p.fillna(0.5))).clip(0, 1))
W["合成 趋势闸门+估值"] = pd.Series(W["合成 趋势闸门+估值"], index=df.index).ffill().fillna(0.5)

W = W.shift(1).fillna(0.0)          # 次日生效

# ---------- 回测引擎 ----------
COST = 0.0005
rows, curves = [], {}
for name in W.columns:
    w = W[name].clip(0, 1)
    dr = w*ret + (1-w)*rf
    turn = w.diff().abs().fillna(w.abs())
    dr = dr - turn*COST
    eq = (1+dr).cumprod()
    curves[name] = eq
    yrs = len(dr)/252
    ann = eq.iloc[-1]**(1/yrs)-1
    vol = dr.std(ddof=1)*np.sqrt(252)
    sharpe = (dr.mean()*252)/(dr.std(ddof=1)*np.sqrt(252))
    ex = dr - rf
    sortino = (ex.mean()*252)/(dr[dr<0].std(ddof=1)*np.sqrt(252))
    mdd = (eq/eq.cummax()-1).min()
    rows.append({
        "策略": name, "累计收益%": (eq.iloc[-1]-1)*100, "年化%": ann*100, "年化波动%": vol*100,
        "夏普": sharpe, "索提诺": sortino, "最大回撤%": mdd*100,
        "卡玛": (ann*100)/abs(mdd*100) if mdd != 0 else np.nan,
        "平均仓位%": w.mean()*100, "年换手(次)": turn.sum()/yrs,
        "正收益年占比%": np.nan,
    })

res = pd.DataFrame(rows)
# 年度胜率
yr = pd.DataFrame({k: (1+v).groupby(v.index.year).prod()-1 for k, v in curves.items()})
res["正收益年占比%"] = [ (yr[c] > 0).mean()*100 for c in res["策略"] ]

res = res.sort_values("夏普", ascending=False)
res.to_csv(os.path.join(OUT, "timing_strategy.csv"), index=False, encoding="utf-8")
pd.DataFrame(curves).to_csv(os.path.join(PROC, "timing_equity.csv"), encoding="utf-8")
yr.to_csv(os.path.join(OUT, "timing_strategy_annual.csv"), encoding="utf-8")

pd.set_option("display.width", 250)
print("=== 择时策略对比（1994-05-05 ~ 2026-11-06，含 5bp 单边成本）===")
print(res.round(2).to_string(index=False))
