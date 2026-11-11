# -*- coding: utf-8 -*-
"""补充表格：年度收益、各指数最大回撤事件、市值覆盖。"""
import os, csv
import numpy as np, pandas as pd
RAW = r"E:\workspace\new\data\raw"; PROC = r"E:\workspace\new\data\processed"; OUT = r"E:\workspace\new\data\output"
os.makedirs(OUT, exist_ok=True)
C = pd.read_csv(os.path.join(PROC, "prices_close.csv"), index_col=0, parse_dates=True)
ORDER = ["SPX","DJI","IXIC","NDX","RUT","SOX"]

# ---------- 年度收益 ----------
yr = C.loc["1994-05-05":].resample("YE").last().pct_change()
yr.loc[yr.index[0]] = C.loc["1994-05-05":].resample("YE").last().iloc[0] / C.loc["1994-05-05":"1994-12-31"].iloc[0] - 1
yr.index = yr.index.year
yr = (yr*100).round(1)
yr.to_csv(os.path.join(OUT, "annual_returns.csv"), encoding="utf-8-sig")
print("=== 年度收益 % ===")
print(yr.to_string())
print("\n正收益年份占比:", {k: round((yr[k].dropna()>0).mean()*100,1) for k in ORDER})
print("最好年份:", {k: (int(yr[k].idxmax()), yr[k].max()) for k in ORDER})
print("最差年份:", {k: (int(yr[k].idxmin()), yr[k].min()) for k in ORDER})

# ---------- 各指数最大回撤 Top5 ----------
print("\n=== 各指数前 5 大回撤（1994-05 起） ===")
epi = []
for k in ORDER:
    s = C[k].loc["1994-05-05":].dropna()
    cum = s/s.iloc[0]; peak = cum.cummax(); dd = cum/peak-1
    ev, in_dd, start = [], False, None
    for dt, v in dd.items():
        if not in_dd and v < 0:
            in_dd, start = True, dt
        elif in_dd and v >= -1e-9:
            in_dd = False
            seg = dd[start:dt]
            ev.append((dd[start:dt].idxmin(), seg.min(), len(s.loc[start:dt])))
    if in_dd:
        seg = dd[start:]
        ev.append((seg.idxmin(), seg.min(), len(s.loc[start:])))
    ev = sorted(ev, key=lambda x: x[1])[:5]
    for tid, dep, dur in ev:
        run = dd[:tid]
        flat = run[run >= -1e-12]
        pk = flat.index[-1] if len(flat) else run.index[0]
        epi.append(dict(指数=k, 峰值日=pk.date(), 谷底日=tid.date(), 回撤幅度=round(dep*100,2),
                        下跌交易日=len(s.loc[pk:tid]), 收复日=str(dd[tid:][dd[tid:] >= -1e-12].index[0].date()) if (dd[tid:] >= -1e-12).any() else "未收复"))
    print(k, [(str(e[0].date()), round(e[1]*100,1)) for e in ev])
pd.DataFrame(epi).to_csv(os.path.join(OUT, "drawdown_episodes.csv"), index=False, encoding="utf-8-sig")

# ---------- 市值覆盖 ----------
def load_ishares(name):
    lines = open(os.path.join(RAW, name+"_holdings.txt"), encoding="utf-8", errors="ignore").read().splitlines()
    hi = next(i for i,l in enumerate(lines) if l.startswith("Ticker,Name,"))
    rows = list(csv.reader(lines[hi:]))
    df = pd.DataFrame([r[:len(rows[0])] for r in rows[1:] if len(r) >= len(rows[0])], columns=rows[0])
    df["Market Value"] = pd.to_numeric(df["Market Value"].str.replace(",",""), errors="coerce")
    df["Weight"] = pd.to_numeric(df.get("Weight (%)", df.get("Market Weight")).astype(str).str.replace(",",""), errors="coerce")
    return df

mcap = {}
for n, label in [("IVV","标普500"), ("IWM","罗素2000"), ("SOXX","费城半导体"), ("IWF","罗素1000成长"), ("IWD","罗素1000价值")]:
    d = load_ishares(n)
    eq = d[d["Asset Class"].str.contains("Equity", na=False)]
    tot = eq["Market Value"].sum()
    w = eq["Weight"]/100
    mcap[label] = dict(成分数=len(eq), ETF持股市值十亿美元=round(tot/1e9,1),
                       最大权重=round(w.max()*100,2), 中位权重=round(w.median()*100,3),
                       前十大权重=round(w.nlargest(10).sum()*100,2),
                       有效家数=round(1/(w**2).sum(),1))
mdf = pd.DataFrame(mcap).T
mdf.to_csv(os.path.join(OUT, "market_cap.csv"), encoding="utf-8-sig")
print("\n=== 覆盖与权重结构 ===")
print(mdf.to_string())

# ---------- 风格：各指数与成长/价值相关性 ----------
G = pd.read_csv(os.path.join(RAW,"yahoo_IWF.csv"), parse_dates=["date"]).set_index("date")["adjclose"]
V = pd.read_csv(os.path.join(RAW,"yahoo_IWD.csv"), parse_dates=["date"]).set_index("date")["adjclose"]
SG = pd.read_csv(os.path.join(RAW,"yahoo_IWO.csv"), parse_dates=["date"]).set_index("date")["adjclose"]
SV = pd.read_csv(os.path.join(RAW,"yahoo_IWN.csv"), parse_dates=["date"]).set_index("date")["adjclose"]
R = C[ORDER].loc["2000-07-28":].pct_change()
rg = pd.concat([G.pct_change(), V.pct_change(), SG.pct_change(), SV.pct_change()], axis=1)
rg.columns = ["IWF","IWD","IWO","IWN"]
rr = pd.concat([R, rg], axis=1).dropna()
print("\n=== 各指数与大盘成长/价值 ETF 的日收益相关性 ===")
print(rr.corr().loc[ORDER, ["IWF","IWD","IWO","IWN"]].round(3).to_string())
rr.corr().loc[ORDER, ["IWF","IWD","IWO","IWN"]].to_csv(os.path.join(OUT,"style_corr.csv"), encoding="utf-8-sig")
