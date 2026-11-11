# -*- coding: utf-8 -*-
"""结构特征：市值覆盖、行业集中度、成长/价值风格、流动性。"""
import os, csv
import numpy as np, pandas as pd

RAW = r"E:\workspace\new\data\raw"; PROC = r"E:\workspace\new\data\processed"; OUT = r"E:\workspace\new\data\output"
os.makedirs(OUT, exist_ok=True)

def load_ishares(name):
    lines = open(os.path.join(RAW, name + "_holdings.txt"), encoding="utf-8", errors="ignore").read().splitlines()
    hi = next(i for i, l in enumerate(lines) if l.startswith("Ticker,Name,"))
    rows = list(csv.reader(lines[hi:]))
    hdr = rows[0]
    body = [r for r in rows[1:] if len(r) >= len(hdr)]
    df = pd.DataFrame([r[:len(hdr)] for r in body], columns=hdr)
    for c in ["Weight (%)", "Market Value", "Price"]:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c].str.replace(",", ""), errors="coerce")
    df["Sector"] = df["Sector"].str.strip()
    if "Weight (%)" not in df.columns and "Market Weight" in df.columns:
        df["Weight (%)"] = pd.to_numeric(df["Market Weight"], errors="coerce")
    return df

data = {n: load_ishares(n) for n in ["IWM", "SOXX", "IVV", "IWF", "IWD"]}
for n, d in data.items():
    print(n, len(d), "权重合计 %.2f" % d["Weight (%)"].sum(), "权益合计 %.2f" %
          d.loc[d["Asset Class"].str.contains("Equity"), "Weight (%)"].sum())

# ---------- 行业权重 ----------
sector_tbl = {}
for n, label in [("IWM", "罗素2000"), ("SOXX", "费城半导体"), ("IVV", "标普500"),
                 ("IWF", "罗素1000成长"), ("IWD", "罗素1000价值")]:
    d = data[n]
    eq = d[d["Asset Class"].str.contains("Equity", na=False)]
    sector_tbl[label] = eq.groupby("Sector")["Weight (%)"].sum().sort_values(ascending=False)
S = pd.DataFrame(sector_tbl).fillna(0)
S.loc["合计"] = S.sum()
S.to_csv(os.path.join(OUT, "sector_weights.csv"), encoding="utf-8-sig")
print("\n=== GICS 行业权重 (%) ===")
print(S.round(2).to_string())

# ---------- 集中度 ----------
print("\n=== 权重集中度 ===")
conc = {}
for nm in ["SP500", "NDX", "DJI"]:
    w = pd.read_csv(os.path.join(PROC, "weights_%s.csv" % nm))["Weight"] / 100
    conc[nm] = dict(成分数=len(w), 前十=w.nlargest(10).sum()*100, 第一大=w.max()*100,
                    HHI=(w**2).sum()*10000, 有效家数=1/(w**2).sum())
for n, label in [("IVV", "标普500(IVV)"), ("IWM", "罗素2000(IWM)"), ("SOXX", "费城半导体(SOXX)")]:
    d = data[n]; d = d[d["Asset Class"].str.contains("Equity", na=False)]
    w = d["Weight (%)"] / 100
    conc[label] = dict(成分数=len(w), 前十=w.nlargest(10).sum()*100, 第一大=w.max()*100,
                       HHI=(w**2).sum()*10000, 有效家数=1/(w**2).sum())
cdf = pd.DataFrame(conc).T.round(2)
cdf.to_csv(os.path.join(OUT, "concentration.csv"), encoding="utf-8-sig")
print(cdf.to_string())

# 罗素2000 覆盖率（IWM 1971 只 vs 罗素2000 名义 2000 只）
print("\n罗素2000: IWM 持仓 %d 只，权重最大 %.2f%%，中位数权重 %.3f%%" % (
    len(data["IWM"]), data["IWM"]["Weight (%)"].max(), data["IWM"]["Weight (%)"].median()))
print("标普500: 最大 %.2f%%, 中位数 %.3f%%" % (data["IVV"]["Weight (%)"].max(), data["IVV"]["Weight (%)"].median()))

# ---------- 成长 vs 价值 ----------
def tr(t):
    return pd.read_csv(os.path.join(RAW, "yahoo_%s.csv" % t), parse_dates=["date"]).set_index("date")["adjclose"]
G, V, SG, SV = tr("IWF"), tr("IWD"), tr("IWO"), tr("IWN")
gv = (G / V).dropna()
gv.to_csv(os.path.join(OUT, "growth_value_ratio.csv"), encoding="utf-8-sig")
print("\n=== 成长/价值 相对强弱 ===")
for a, b, lab in [("2000-05-26","2002-10-09","科网破裂"),("2002-10-09","2007-10-09","信贷繁荣"),
                  ("2007-10-09","2009-03-09","金融危机"),("2009-03-09","2020-02-19","后危机长牛"),
                  ("2020-03-23","2022-01-03","流动性牛市"),("2022-01-03","2022-10-12","加息熊市"),
                  ("2022-10-12","2025-02-19","AI 牛市"),("2025-02-19","2026-11-06","近期")]:
    seg = gv.loc[a:b]
    if len(seg) < 20: continue
    print("%-9s 成长/价值比值 %+7.1f%% | 大盘成长 IWF %+7.1f%%  大盘价值 IWD %+7.1f%%" % (
        lab, (seg.iloc[-1]/seg.iloc[0]-1)*100,
        (G.loc[a:b].iloc[-1]/G.loc[a:b].iloc[0]-1)*100,
        (V.loc[a:b].iloc[-1]/V.loc[a:b].iloc[0]-1)*100))

# ---------- 流动性 ----------
print("\n=== 代表 ETF 近一年日均成交额 ===")
for t in ["SPY","QQQ","DIA","IWM","SOXX","SMH"]:
    d = pd.read_csv(os.path.join(RAW, "yahoo_%s.csv" % t), parse_dates=["date"]).set_index("date").loc["2025-11-06":]
    dv = (d["close"] * d["volume"]).mean()
    print("%-5s 日均 %6.2f 亿美元   年化波动 %.1f%%" % (t, dv/1e8, d["close"].pct_change().std()*np.sqrt(252)*100))
