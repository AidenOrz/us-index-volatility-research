# -*- coding: utf-8 -*-
"""新下载的 VIX9D / VIX6M 带来的新指标：完整期限结构斜率。
之前只用了 VIX/VIX3M，现在有 9 天 / 30 天 / 3 个月 / 6 个月四档，可以构造两条斜率：
  短端斜率 = VIX/VIX9D - 1   （9 天到 30 天，最敏感）
  长端斜率 = VIX6M/VIX3M - 1 （3 个月到 6 个月）
  总斜率   = VIX/VIX6M - 1
产出 data/output/vix_term_slopes.csv
"""
import os
import numpy as np
import pandas as pd

BASE = r"E:\workspace\new"
CB = os.path.join(BASE, "data", "raw", "cboe_vol")
PROC = os.path.join(BASE, "data", "processed")
OUT = os.path.join(BASE, "data", "output")


def load(t):
    d = pd.read_csv(os.path.join(CB, t + "_History.csv"))
    d["DATE"] = pd.to_datetime(d["DATE"], format="%m/%d/%Y")
    col = "CLOSE" if "CLOSE" in d.columns else d.columns[-1]
    return d.set_index("DATE")[col].astype(float).sort_index()


p = pd.concat([load(t).rename(t) for t in ["VIX9D", "VIX", "VIX3M", "VIX6M"]],
              axis=1, sort=True).loc["2011-01-04":]
px = pd.read_csv(os.path.join(PROC, "prices_close.csv"), index_col=0, parse_dates=True)["SPX"].astype(float)
p["SPX"] = px.reindex(p.index)
p = p.dropna(subset=["SPX"])
print("期限结构面板:", p.shape, p.index.min().date(), "~", p.index.max().date())

p["slope_short"] = p["VIX"] / p["VIX9D"] - 1      # 9D -> 30D
p["slope_mid"] = p["VIX3M"] / p["VIX"] - 1        # 30D -> 3M
p["slope_long"] = p["VIX6M"] / p["VIX3M"] - 1     # 3M -> 6M
p["slope_total"] = p["VIX6M"] / p["VIX9D"] - 1    # 9D -> 6M

f21 = (p["SPX"].shift(-21) / p["SPX"] - 1) * 100
f63 = (p["SPX"].shift(-63) / p["SPX"] - 1) * 100
f252 = (p["SPX"].shift(-252) / p["SPX"] - 1) * 100


def rp(s, win=2520, minp=756):
    return s.rolling(win, min_periods=minp).apply(lambda a: (a[-1] > a[:-1]).mean(), raw=True)


rows = []
for nm in ["slope_short", "slope_mid", "slope_long", "slope_total"]:
    s = p[nm].dropna()
    q = rp(p[nm])
    for lo, hi, lab in [(0, .10, "0-10%"), (.10, .50, "10-50%"), (.50, .90, "50-90%"), (.90, 1.001, "90-100%")]:
        m = (q >= lo) & (q < hi)
        rows.append({"斜率": nm, "分位": lab, "天数": int(m.sum()),
                     "中位斜率%": s[m].median() * 100,
                     "1M均值%": f21[m].dropna().mean(), "1M胜率%": (f21[m].dropna() > 0).mean() * 100,
                     "3M均值%": f63[m].dropna().mean(),
                     "12M均值%": f252[m].dropna().mean(), "12M胜率%": (f252[m].dropna() > 0).mean() * 100})
d = pd.DataFrame(rows)
d.to_csv(os.path.join(OUT, "vix_term_slopes.csv"), index=False, encoding="utf-8-sig")
print("\n=== 四档期限结构斜率（2011 起）===")
print(d.round(2).to_string(index=False))

print("\n=== 当前读数 ===")
last = p.index[-1]
print("日期:", last.date())
for nm, lab in [("VIX9D", "9天"), ("VIX", "30天"), ("VIX3M", "3个月"), ("VIX6M", "6个月")]:
    print("  %-6s %s = %.2f" % (nm, lab, p[nm].loc[last]))
for nm in ["slope_short", "slope_mid", "slope_long", "slope_total"]:
    print("  %-12s = %+.2f%%  (10年分位 %.1f%%)" % (nm, p[nm].loc[last] * 100, rp(p[nm]).loc[last] * 100))

print("\n=== 相关系数：斜率 vs 未来收益 ===")
for nm in ["slope_short", "slope_mid", "slope_long", "slope_total"]:
    print("  %-12s vs 1M: %+.4f  vs 3M: %+.4f  vs 12M: %+.4f" % (
        nm, p[nm].corr(f21), p[nm].corr(f63), p[nm].corr(f252)))
