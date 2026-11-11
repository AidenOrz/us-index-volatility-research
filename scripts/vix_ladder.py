# -*- coding: utf-8 -*-
"""仓位刻度表：按 11.2 节使用的 6 个档位精确计算盈亏比与未来收益。
产出 data/output/vix_ladder.csv
"""
import os
import numpy as np
import pandas as pd

BASE = r"E:\workspace\new"
PROC = os.path.join(BASE, "data", "processed")
OUT = os.path.join(BASE, "data", "output")

panel = pd.read_csv(os.path.join(PROC, "timing_panel.csv"), index_col=0, parse_dates=True)
panel = panel.loc["1994-05-05":].copy()
px = panel["SPX"].astype(float)
vix = panel["VIX"].astype(float)

rev = px[::-1]
fmin = rev.rolling(252, min_periods=21).min()[::-1]
fmax = rev.rolling(252, min_periods=21).max()[::-1]
fwd_dn = (fmin / px - 1.0) * 100.0
fwd_up = (fmax / px - 1.0) * 100.0
f252 = (px.shift(-252) / px - 1.0) * 100.0
f21 = (px.shift(-21) / px - 1.0) * 100.0

LADDER = [
    ("VIX < 13", vix < 13, "0.95", "自满区：赔率好，别减仓"),
    ("13 ~ 20", (vix >= 13) & (vix < 20), "0.80", "常态区：标准仓位"),
    ("20 ~ 25", (vix >= 20) & (vix < 25), "0.45", "洼地：全表最差，最低仓位"),
    ("25 ~ 30", (vix >= 25) & (vix < 30), "0.80", "恐慌初期：开始加"),
    ("30 ~ 40", (vix >= 30) & (vix < 40), "0.95", "恐慌区：接近满仓"),
    ("VIX > 40", vix >= 40, "1.00", "极端恐慌：满仓"),
]

rows = []
for lab, m, pos, note in LADDER:
    m = m.reindex(px.index).fillna(False).astype(bool)
    u = fwd_up[m].median()
    d = fwd_dn[m].median()
    s = f252[m].dropna()
    s21 = f21[m].dropna()
    rows.append({
        "档位": lab, "天数": int(m.sum()), "占比%": m.mean() * 100,
        "1M均值%": s21.mean(), "1M胜率%": (s21 > 0).mean() * 100,
        "12M均值%": s.mean(), "12M胜率%": (s > 0).mean() * 100,
        "未来1年最大上行%(中位)": u, "未来1年最大下行%(中位)": d,
        "盈亏比": u / abs(d) if d else np.nan,
        "建议仓位%": float(pos) * 100, "说明": note,
    })
d = pd.DataFrame(rows)
d.to_csv(os.path.join(OUT, "vix_ladder.csv"), index=False, encoding="utf-8-sig")
pd.set_option("display.width", 220)
print(d.round(2).to_string(index=False))
print("\nsaved vix_ladder.csv")
