# -*- coding: utf-8 -*-
"""阶段划分（修正版）：短阶段不年化；补充上/下行捕获率、相关性与滚动统计。"""
import os
import numpy as np, pandas as pd

RAW = r"E:\workspace\new\data\raw"; PROC = r"E:\workspace\new\data\processed"; OUT = r"E:\workspace\new\data\output"
os.makedirs(OUT, exist_ok=True)
C = pd.read_csv(os.path.join(PROC, "prices_close.csv"), index_col=0, parse_dates=True)
irx = pd.read_csv(os.path.join(RAW, "yahoo_IDX_IRX.csv"), parse_dates=["date"]).set_index("date")["close"]
RF_ANN = (irx / 100.0).reindex(C.index).ffill()
RF_D = (1 + RF_ANN) ** (1/252) - 1
ORDER = ["SPX","DJI","IXIC","NDX","RUT","SOX"]
NAMES = {"SPX":"标普500","DJI":"道琼斯工业","IXIC":"纳斯达克综合","NDX":"纳斯达克100","RUT":"罗素2000","SOX":"费城半导体"}

PHASES = [
 ("1994-05-05","2000-03-24","科网泡沫牛市","牛市"),
 ("2000-03-24","2002-10-09","科网泡沫破裂","熊市"),
 ("2002-10-09","2007-10-09","信贷繁荣牛市","牛市"),
 ("2007-10-09","2009-03-09","全球金融危机","熊市"),
 ("2009-03-09","2020-02-19","后危机长牛","牛市"),
 ("2020-02-19","2020-03-23","新冠闪崩","熊市"),
 ("2020-03-23","2022-01-03","流动性牛市","牛市"),
 ("2022-01-03","2022-10-12","加息熊市","熊市"),
 ("2022-10-12","2025-02-19","AI 牛市","牛市"),
 ("2025-02-19","2025-04-08","关税急跌","震荡"),
 ("2025-04-08","2026-11-06","关税后修复","震荡"),
]

def stats(px, a, b):
    s = px.loc[a:b].dropna()
    ret = s.pct_change().dropna()
    yrs = (s.index[-1]-s.index[0]).days/365.25
    cum = (1+ret).cumprod(); dd = cum/cum.cummax()-1
    ex = ret - RF_D.loc[ret.index].fillna(0)
    neg = ret[ret<0]
    ann = (s.iloc[-1]/s.iloc[0])**(1/yrs)-1
    short = yrs < 1.0
    return dict(cumret=s.iloc[-1]/s.iloc[0]-1, years=yrs, ann=np.nan if short else ann,
                vol=ret.std(ddof=1)*np.sqrt(252),
                sharpe=np.nan if short else ex.mean()/ex.std(ddof=1)*np.sqrt(252),
                sortino=np.nan if short or len(neg)<6 else ex.mean()/neg.std(ddof=1)*np.sqrt(252),
                mdd=dd.min(), calmar=np.nan if short or dd.min()>=0 else ann/abs(dd.min()), n=len(s), short=short)

rows=[]
for a,b,name,kind in PHASES:
    for k in ORDER:
        st = stats(C[k], a, b)
        rows.append(dict(阶段=name, 类型=kind, 指数=k, 名称=NAMES[k], 起始=a, 结束=b, **st))
ph = pd.DataFrame(rows)
ph.to_csv(os.path.join(OUT, "phases.csv"), index=False, encoding="utf-8-sig")

pd.set_option("display.width", 250)
print("=== 累计收益 % （阶段内） ===")
p1 = (ph.pivot_table(index=["类型","阶段"], columns="指数", values="cumret", sort=False)*100).round(1)
p1["最强"] = p1[ORDER].idxmax(axis=1); p1["最弱"] = p1[ORDER].idxmin(axis=1)
print(p1.to_string())
print("\n=== 年化收益 % （<1年为 n.a.） ===")
print((ph.pivot_table(index=["类型","阶段"], columns="指数", values="ann", sort=False)*100).round(1).to_string())
print("\n=== 年化波动率 % ===")
print((ph.pivot_table(index=["类型","阶段"], columns="指数", values="vol", sort=False)*100).round(1).to_string())
print("\n=== 夏普（<1年为 n.a.） ===")
print(ph.pivot_table(index=["类型","阶段"], columns="指数", values="sharpe", sort=False).round(2).to_string())
print("\n=== 最大回撤 % ===")
print((ph.pivot_table(index=["类型","阶段"], columns="指数", values="mdd", sort=False)*100).round(1).to_string())
print("\n=== 卡玛（<1年为 n.a.） ===")
print(ph.pivot_table(index=["类型","阶段"], columns="指数", values="calmar", sort=False).round(2).to_string())

# ---------- 上行/下行捕获率（相对 SPX，全样本） ----------
R = C[ORDER].loc["1994-05-05":].pct_change().dropna()
up = R["SPX"] > 0; dn = R["SPX"] < 0
cap = pd.DataFrame({
 "上行捕获": R[up].mean() / R["SPX"][up].mean(),
 "下行捕获": R[dn].mean() / R["SPX"][dn].mean(),
})
cap["捕获比"] = cap["上行捕获"] / cap["下行捕获"]
# Beta / 年化 alpha
alpha, beta = {}, {}
for k in ORDER:
    x = R["SPX"]; y = R[k]
    b = np.cov(y, x)[0,1]/np.var(x, ddof=1)
    beta[k] = b
    ex = y - RF_D.loc[y.index].fillna(0)
    exm = x - RF_D.loc[x.index].fillna(0)
    a_d = ex.mean() - b*exm.mean()
    alpha[k] = (1+a_d)**252 - 1
cap["Beta"] = pd.Series(beta)
cap["年化Alpha"] = pd.Series(alpha)
cap.to_csv(os.path.join(OUT, "capture_beta.csv"), encoding="utf-8-sig")
print("\n=== 相对标普500的捕获率与 Beta（1994-05 起全样本） ===")
print(cap.assign(**{"上行捕获":(cap["上行捕获"]*100).round(1),"下行捕获":(cap["下行捕获"]*100).round(1),
                    "捕获比":cap["捕获比"].round(2),"Beta":cap["Beta"].round(2),
                    "年化Alpha":(cap["年化Alpha"]*100).round(2)}).to_string())

# ---------- 相关性矩阵 ----------
print("\n=== 日收益相关系数（1994-05 起）===")
print(R.corr().round(3).to_string())
R.corr().to_csv(os.path.join(OUT, "corr_daily.csv"), encoding="utf-8-sig")

# 滚动相关性（相对 SPX，252日）
roll = pd.DataFrame({k: R[k].rolling(252).corr(R["SPX"]) for k in ORDER if k!="SPX"})
roll.to_csv(os.path.join(OUT, "rolling_corr.csv"), encoding="utf-8-sig")
print("\n滚动365日相关性 近期值：")
print(roll.tail(3).round(3).to_string())
