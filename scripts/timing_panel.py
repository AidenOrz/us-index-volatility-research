# -*- coding: utf-8 -*-
"""构建"位置指标"日频面板（timing panel）。

输入：data/processed/prices_close.csv（六指数）、data/raw/yahoo_IDX_VIX.csv、
      yahoo_IDX_VIX3M.csv、yahoo_IDX_TNX.csv、yahoo_IDX_IRX.csv、yahoo_HYG.csv、
      yahoo_IEF.csv、yahoo_RSP.csv、yahoo_SPY.csv、val_cape.csv / val_pe.csv / val_dy.csv
输出：data/processed/timing_panel.csv
"""
import os
import numpy as np
import pandas as pd

BASE = r"E:\workspace\new"
RAW = os.path.join(BASE, "data", "raw")
PROC = os.path.join(BASE, "data", "processed")

def load_yahoo(name, col="close"):
    p = os.path.join(RAW, "yahoo_%s.csv" % name)
    if not os.path.exists(p):
        return None
    df = pd.read_csv(p, parse_dates=["date"]).set_index("date")[col]
    return df[~df.index.duplicated(keep="last")].sort_index()

px = pd.read_csv(os.path.join(PROC, "prices_close.csv"), index_col=0, parse_dates=True)
spx = px["SPX"].dropna()

df = pd.DataFrame(index=spx.index)
df["SPX"] = spx
for c in ["DJI", "IXIC", "NDX", "RUT", "SOX"]:
    df[c] = px[c].reindex(df.index)

# ---- 趋势 / 位置 ----
df["MA50"] = df["SPX"].rolling(50).mean()
df["MA200"] = df["SPX"].rolling(200).mean()
df["ma200_dev"] = df["SPX"] / df["MA200"] - 1          # 相对 200 日均线偏离
df["ma50_dev"] = df["SPX"] / df["MA50"] - 1
df["golden"] = (df["MA50"] > df["MA200"]).astype(float)
df["ath"] = df["SPX"].cummax()
df["dd"] = df["SPX"] / df["ath"] - 1                    # 距历史高点回撤（≤0）
df["dd_abs"] = -df["dd"]                                # 正值=回撤幅度
df["high252"] = df["SPX"].rolling(252, min_periods=60).max()
df["dist_high252"] = df["SPX"] / df["high252"] - 1

# ---- 动量 ----
for n, lab in [(21, "mom1m"), (63, "mom3m"), (126, "mom6m"), (252, "mom12m")]:
    df[lab] = df["SPX"].pct_change(n)

# ---- 波动 / 情绪 ----
ret = df["SPX"].pct_change()
df["vol20"] = ret.rolling(20).std() * np.sqrt(252)
df["vol60"] = ret.rolling(60).std() * np.sqrt(252)
df["vol_ratio"] = df["vol20"] / df["vol60"]

# RSI(14)
delta = df["SPX"].diff()
up = delta.clip(lower=0).ewm(alpha=1/14, adjust=False).mean()
dn = (-delta.clip(upper=0)).ewm(alpha=1/14, adjust=False).mean()
df["rsi14"] = 100 - 100 / (1 + up / dn.replace(0, np.nan))

# ---- VIX 系列 ----
vix = load_yahoo("IDX_VIX")
if vix is not None:
    df["VIX"] = vix.reindex(df.index)
    df["vix_pct10y"] = df["VIX"].rolling(2520, min_periods=500).rank(pct=True)
    df["vixma10"] = df["VIX"].rolling(10).mean()
vix3m = load_yahoo("IDX_VIX3M")
if vix3m is not None:
    df["VIX3M"] = vix3m.reindex(df.index)
    df["vix_ts"] = df["VIX"] / df["VIX3M"] - 1     # >0 倒挂 = 短期恐慌

# ---- 利率 / 信用 ----
tnx = load_yahoo("IDX_TNX")
irx = load_yahoo("IDX_IRX")
if tnx is not None:
    df["TNX"] = tnx.reindex(df.index)
    df["TNX_chg3m"] = df["TNX"].diff(63)
if irx is not None:
    df["IRX"] = irx.reindex(df.index)
    df["curve"] = df["TNX"] - df["IRX"]            # 10Y - 3M 期限利差

hyg = load_yahoo("HYG")
ief = load_yahoo("IEF")
if hyg is not None and ief is not None:
    h = hyg.reindex(df.index).ffill()
    i = ief.reindex(df.index).ffill()
    ratio = (h / i)
    df["credit_mom63"] = ratio.pct_change(63)      # 信用资产相对国债的动量

rsp = load_yahoo("RSP")
spy = load_yahoo("SPY")
if rsp is not None and spy is not None:
    r = rsp.reindex(df.index).ffill()
    s = spy.reindex(df.index).ffill()
    rr = r / s
    df["breadth_mom63"] = rr.pct_change(63)        # 等权/市值权：宽度改善
    df["breadth_dev200"] = rr / rr.rolling(200).mean() - 1

# ---- 估值（月度，向前填充到日频，只用已公布数据）----
for key, col in [("val_cape", "cape"), ("val_pe", "pe"), ("val_dy", "dy")]:
    p = os.path.join(PROC, key + ".csv")
    if not os.path.exists(p):
        continue
    v = pd.read_csv(p, parse_dates=["date"]).set_index("date")["value"]
    v = v[~v.index.duplicated(keep="last")].sort_index()
    # 月末值 -> 次月首个交易日才可用（避免前视）
    s = v.resample("ME").last().dropna()
    s.index = s.index + pd.offsets.MonthBegin(1)
    df[col] = s.reindex(df.index).ffill()
    df[col + "_pct10y"] = df[col].rolling(2520, min_periods=500).rank(pct=True)

# ---- 无风险日收益（用于策略现金收益）----
if irx is not None:
    rf_ann = df["IRX"] / 100.0
    df["rf_d"] = (1 + rf_ann) ** (1/252) - 1

df = df.drop(columns=["MA50", "MA200", "ath", "high252"], errors="ignore")
df.to_csv(os.path.join(PROC, "timing_panel.csv"), encoding="utf-8")

print("panel", df.shape, df.index.min().date(), "->", df.index.max().date())
cols = [c for c in df.columns]
print("cols:", cols)
sub = df.loc["1994-05-05":]
print("since 1994 rows", len(sub))
print(sub[["ma200_dev", "dd_abs", "cape", "cape_pct10y", "VIX", "vix_ts", "credit_mom63", "breadth_mom63", "curve"]].tail(3).round(4).to_string())
print("non-null counts (since 1994):")
print(sub[["ma200_dev","dd_abs","mom12m","rsi14","vol20","VIX","vix_pct10y","vix_ts","credit_mom63","breadth_mom63","curve","cape","cape_pct10y","pe","dy"]].notna().sum().to_string())
