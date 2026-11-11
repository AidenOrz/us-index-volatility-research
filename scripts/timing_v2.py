# -*- coding: utf-8 -*-
"""全历史分位改为「滚动 10 年分位」（无前视、可比），并重做分层检验。"""
import os
import numpy as np
import pandas as pd

BASE = r"E:\workspace\new"
PROC = os.path.join(BASE, "data", "processed")
OUT = os.path.join(BASE, "data", "output")

def roll_pct(s, win=2520, minp=1260):
    """滚动窗口内的百分位（不含当日未来信息）。"""
    r = s.rolling(win, min_periods=minp)
    return r.apply(lambda a: (a[-1] > a[:-1]).mean(), raw=True)

panel = pd.read_csv(os.path.join(PROC, "timing_panel.csv"), index_col=0, parse_dates=True)
# 去掉旧的 expanding 分位列，重算
for c in [c for c in panel.columns if c.endswith("_fpct")]:
    panel = panel.drop(columns=[c])

panel["cape_p"] = roll_pct(panel["cape"].astype(float) if "cape" in panel else None, 2520, 1260)
panel["pe_p"] = roll_pct(panel["pe"].astype(float), 2520, 1260)
panel["dy_p"] = 1 - roll_pct(panel["dy"].astype(float), 2520, 1260)   # 股息率越高越便宜 -> 贵度 = 1-分位
panel["vix_p"] = roll_pct(panel["VIX"].astype(float), 2520, 1260)
panel["tnx_p"] = roll_pct(panel["TNX"].astype(float), 2520, 1260)
panel["ma200dev_p"] = roll_pct(panel["ma200_dev"].astype(float), 2520, 1260)
panel["dd_p"] = roll_pct(panel["dd_abs"].astype(float), 2520, 1260)
panel["mom12_p"] = roll_pct(panel["mom12m"].astype(float), 2520, 1260)
panel["vol_p"] = roll_pct(panel["vol20"].astype(float), 2520, 1260)
panel["rsi_p"] = roll_pct(panel["rsi14"].astype(float), 2520, 1260)
panel["vix_ts_p"] = roll_pct(panel["vix_ts"].astype(float), 2520, 1260)
panel["credit_p"] = 1 - roll_pct(panel["credit_mom63"].astype(float), 2520, 1260)
panel["breadth_p"] = 1 - roll_pct(panel["breadth_mom63"].astype(float), 2520, 1260)
panel["curve_p"] = 1 - roll_pct(panel["curve"].astype(float), 2520, 1260)

panel.to_csv(os.path.join(PROC, "timing_panel.csv"), encoding="utf-8")
print("panel", panel.shape)
print(panel.loc["2026-11-01":, ["cape_p","pe_p","dy_p","vix_p","tnx_p","ma200dev_p","dd_p","rsi_p","vix_ts_p","credit_p","breadth_p","curve_p"]].tail(2).round(3).to_string())

df = panel.loc["1994-05-05":].copy()
spx = df["SPX"]
for n in [21, 63, 126, 252]:
    df["fwd%d" % n] = spx.shift(-n)/spx - 1

# 方向：+1 表示数值高=位置高（贵/过热），-1 反之（已预先取反的列用 +1）
INDS = [
    ("CAPE 席勒市盈率",   "cape_p",     +1),
    ("市盈率 PE",         "pe_p",       +1),
    ("股息率(贵度)",       "dy_p",       +1),
    ("10Y 国债利率",       "tnx_p",      +1),
    ("VIX 水平",          "vix_p",      +1),
    ("VIX 期限倒挂",       "vix_ts_p",   +1),
    ("200日线偏离",        "ma200dev_p", +1),
    ("距历史高点回撤深度",   "dd_p",       +1),
    ("12 月动量",          "mom12_p",    +1),
    ("20 日年化波动",       "vol_p",      +1),
    ("RSI(14)",           "rsi_p",      +1),
    ("信用资产动量",        "credit_p",   +1),
    ("等权/市值宽度",       "breadth_p",  +1),
    ("期限利差 10Y-3M",    "curve_p",    +1),
]

def spearman(a, b):
    return float(pd.Series(np.asarray(a,float)).rank().corr(pd.Series(np.asarray(b,float)).rank()))

rows_ic, rows_q = [], []
for name, col, d in INDS:
    s = df[col].astype(float)
    score = s if d > 0 else 1 - s
    rec = {"指标": name}
    for n in [21, 63, 252]:
        f = df["fwd%d" % n]
        m = (score.notna() & f.notna()).values
        if m.sum() < 300:
            rec["IC%d" % n] = np.nan; rec["t%d" % n] = np.nan; continue
        idx = np.arange(0, m.sum(), n)
        xs, ys = score[m].values[idx], f[m].values[idx]
        if len(xs) < 20 or np.std(xs) == 0:
            rec["IC%d" % n] = np.nan; rec["t%d" % n] = np.nan; continue
        ic = spearman(xs, ys); k = max(len(xs)-2, 1)
        rec["IC%d" % n] = ic
        rec["t%d" % n] = ic*np.sqrt(k/max(1-ic**2, 1e-9))
    rows_ic.append(rec)

    for q_ in range(5):
        lo, hi = q_/5, (q_+1)/5
        m = ((score >= lo) & (score < hi)) if q_ < 4 else ((score >= lo) & (score <= 1.0))
        sub = df.loc[m.fillna(False).astype(bool)]
        r = {"指标": name, "分层": "Q%d" % (q_+1), "区间": "%d-%d%%" % (int(lo*100), int(hi*100)), "样本日": len(sub)}
        for n in [21, 63, 252]:
            f = sub["fwd%d" % n].dropna()
            r["均值%d日%%" % n] = f.mean()*100 if len(f) else np.nan
            r["胜率%d日%%" % n] = (f > 0).mean()*100 if len(f) else np.nan
        rows_q.append(r)

ic, q = pd.DataFrame(rows_ic), pd.DataFrame(rows_q)
ic.to_csv(os.path.join(OUT, "timing_ic.csv"), index=False, encoding="utf-8")
q.to_csv(os.path.join(OUT, "timing_quintile.csv"), index=False, encoding="utf-8")

pd.set_option("display.width", 220)
print("\n=== IC（滚动10年分位，非重叠抽样）===")
print(ic.round(3).to_string(index=False))
print("\n=== 未来 12 个月：Q1(位置最低) vs Q5(位置最高) ===")
p = q.pivot_table(index="指标", columns="分层", values=["均值252日%","胜率252日%"])
print(p.round(2).to_string())
