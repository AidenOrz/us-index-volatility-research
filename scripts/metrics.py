# -*- coding: utf-8 -*-
"""核心绩效指标计算 + 牛熊阶段自动划分。"""
import os, json
import numpy as np, pandas as pd

RAW = r"E:\workspace\new\data\raw"
PROC = r"E:\workspace\new\data\processed"
OUT = r"E:\workspace\new\data\output"
os.makedirs(OUT, exist_ok=True)

C = pd.read_csv(os.path.join(PROC, "prices_close.csv"), index_col=0, parse_dates=True)
irx = pd.read_csv(os.path.join(RAW, "yahoo_IDX_IRX.csv"), parse_dates=["date"]).set_index("date")["close"]
rf = (irx / 100.0).reindex(C.index).ffill()   # 13周国库券贴现率, 年化小数
rf_d = (1 + rf) ** (1/252) - 1

NAMES = {"SPX":"标普500","DJI":"道琼斯工业平均","IXIC":"纳斯达克综合",
         "NDX":"纳斯达克100","RUT":"罗素2000","SOX":"费城半导体"}
ORDER = ["SPX","DJI","IXIC","NDX","RUT","SOX"]

def perf(px, rf_d, start=None, end=None, label=""):
    s = px.dropna()
    if start is not None: s = s[s.index >= start]
    if end is not None:   s = s[s.index <= end]
    if len(s) < 30: return None
    ret = s.pct_change().dropna()
    n = len(s)
    years = (s.index[-1] - s.index[0]).days / 365.25
    total = s.iloc[-1] / s.iloc[0] - 1
    cagr = (s.iloc[-1] / s.iloc[0]) ** (1/years) - 1
    vol = ret.std(ddof=1) * np.sqrt(252)
    ex = ret - rf_d.reindex(ret.index).fillna(0)
    sharpe = ex.mean() / ex.std(ddof=1) * np.sqrt(252) if ex.std(ddof=1) > 0 else np.nan
    downside = ret[ret < 0]
    # 索提诺：分子分母同为年化口径
    sortino = (ex.mean() * 252) / (downside.std(ddof=1) * np.sqrt(252)) if len(downside) > 5 else np.nan
    cum = (1 + ret).cumprod()
    dd = cum / cum.cummax() - 1
    mdd = dd.min()
    calmar = cagr / abs(mdd) if mdd < 0 else np.nan
    # 最大回撤持续期
    peak = cum.cummax()
    underwater = (cum < peak).astype(int)
    runs, cur = [], 0
    for v in underwater:
        if v: cur += 1
        elif cur: runs.append(cur); cur = 0
    if cur: runs.append(cur)
    mdd_dur = max(runs) if runs else 0
    # 当前未收复
    cur_dd = dd.iloc[-1]
    var95 = np.percentile(ret, 5)
    cvar95 = ret[ret <= var95].mean()
    # 年度
    yearly = (s.resample("YE").last() / s.resample("YE").first() - 1)
    return dict(label=label, start=str(s.index[0].date()), end=str(s.index[-1].date()), n=n, years=years,
                total=total, cagr=cagr, vol=vol, sharpe=sharpe, sortino=sortino, mdd=mdd,
                calmar=calmar, mdd_dur_days=mdd_dur, cur_dd=cur_dd,
                skew=ret.skew(), kurt=ret.kurtosis(), var95=var95, cvar95=cvar95,
                best_day=ret.max(), worst_day=ret.min(),
                best_month=(1+s).resample("ME").last().pct_change().max(),
                worst_month=(1+s).resample("ME").last().pct_change().min(),
                win_rate=(ret > 0).mean(), rf_avg=rf.reindex(ret.index).mean(),
                ret=ret, s=s, dd=dd)

START = "1994-05-05"
END = C.index[-1]
rows = []
objs = {}
for k in ORDER:
    o = perf(C[k], rf_d, START, END, k)
    objs[k] = o
    rows.append({kk: vv for kk, vv in o.items() if kk not in ("ret","s","dd")})
df = pd.DataFrame(rows).set_index("label")
df.to_csv(os.path.join(OUT, "metrics_main.csv"), encoding="utf-8-sig")

pd.set_option("display.width", 250)
print("=== 主样本 1994-05-05 ~ %s 绩效（价格指数，不含股息） ===" % END.date())
show = df[["start","end","n","years","total","cagr","vol","sharpe","sortino","mdd","calmar","mdd_dur_days","cur_dd","rf_avg"]].copy()
for c in ["total","cagr","vol","sharpe","sortino","mdd","calmar","cur_dd","rf_avg"]:
    show[c] = (show[c]*100).round(2) if c in ("total","cagr","vol","mdd","cur_dd","rf_avg") else show[c].round(3)
print(show.to_string())
print()
print(df[["skew","kurt","best_day","worst_day","best_month","worst_month","win_rate"]].round(4).to_string())

# ---------- 全历史（各指数自起点） ----------
print("\n=== 各指数全历史 ===")
full = []
for k in ORDER:
    o = perf(C[k], rf_d, None, END, k)
    full.append({kk: vv for kk, vv in o.items() if kk not in ("ret","s","dd")})
fullf = pd.DataFrame(full).set_index("label")
fullf.to_csv(os.path.join(OUT, "metrics_full.csv"), encoding="utf-8-sig")
print(fullf[["start","end","years","cagr","vol","sharpe","mdd","calmar"]].assign(
    cagr=lambda d:(d.cagr*100).round(2), vol=lambda d:(d.vol*100).round(2),
    mdd=lambda d:(d.mdd*100).round(2)).round(3).to_string())

# ---------- 牛熊自动划分 ----------
print("\n=== 标普500 回撤事件识别（>=15%） ===")
s = C["SPX"].dropna()
cum = s / s.iloc[0]
peak = cum.cummax()
dd = cum / peak - 1
events = []
in_dd = False
for dt, v in dd.items():
    if not in_dd and v <= -0.15:
        in_dd = True
        pend = dt
    elif in_dd and v >= -0.001:
        in_dd = False
        seg = dd[pend:dt]
        events.append((s.loc[:pend].idxmax() if False else cum[:pend].idxmax(), seg.idxmin(), dt, seg.min()))
for a, b, c_, m in events:
    print("高点 %s -> 低点 %s (%.2f%%) -> 收复 %s  历时 %d 交易日" %
          (a.date(), b.date(), m*100, c_.date(), len(s.loc[a:c_])))
