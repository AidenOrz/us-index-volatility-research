# -*- coding: utf-8 -*-
"""VIX 家族：对口波动率指数（VXN 对纳指100、RVX 对罗素2000）与 VIX 的对比。
产出：
  vix_family.csv       VIX/VXN/RVX 描述统计与相关
  vix_family_sig.csv   同一信号用对口波动率 vs 用 VIX 的效果对比
  vix_family_now.csv   三者当前读数与分位
"""
import os
import numpy as np
import pandas as pd

BASE = r"E:\workspace\new"
RAW = os.path.join(BASE, "data", "raw")
PROC = os.path.join(BASE, "data", "processed")
OUT = os.path.join(BASE, "data", "output")


def load_cboe(fn):
    d = pd.read_csv(os.path.join(RAW, fn))
    d["DATE"] = pd.to_datetime(d["DATE"], format="%m/%d/%Y")
    return d.set_index("DATE")["CLOSE"].astype(float).sort_index()


vix = load_cboe("cboe_VIX.csv")
vxn = load_cboe("cboe_VXN.csv")
rvx = load_cboe("cboe_RVX.csv")

panel = pd.read_csv(os.path.join(PROC, "timing_panel.csv"), index_col=0, parse_dates=True)
panel = panel.loc["1994-05-05":].copy()
px = panel[["SPX", "NDX", "RUT"]].astype(float)

# ---------- 1) 描述统计 ----------
rows = []
for nm, s in [("VIX（标普500）", vix), ("VXN（纳指100）", vxn), ("RVX（罗素2000）", rvx)]:
    rows.append({"指数": nm, "起始": str(s.index[0].date()), "末日": str(s.index[-1].date()),
                 "交易日": len(s), "均值": s.mean(), "中位": s.median(),
                 "最小值": s.min(), "最大值": s.max(),
                 "P10": s.quantile(.10), "P90": s.quantile(.90)})
fam = pd.DataFrame(rows)
fam.to_csv(os.path.join(OUT, "vix_family.csv"), index=False, encoding="utf-8-sig")
print("=== 1. VIX 家族描述统计（CBOE 官方）===")
print(fam.round(2).to_string(index=False))

# 相关
common = pd.concat([vix, vxn, rvx], axis=1, keys=["VIX", "VXN", "RVX"]).dropna()
print("\n共同交易日 %d（%s ~ %s）" % (len(common), common.index[0].date(), common.index[-1].date()))
print("相关系数矩阵（水平）：")
print(common.corr().round(3).to_string())
print("\n相关系数矩阵（日变化）：")
print(common.diff().dropna().corr().round(3).to_string())
print("\n均值比：VXN/VIX=%.3f  RVX/VIX=%.3f" % ((common["VXN"] / common["VIX"]).mean(),
                                              (common["RVX"] / common["VIX"]).mean()))

# ---------- 2) 对口波动率 vs 通用 VIX ----------
def sig_effect(vol, target, label):
    v = vol.reindex(target.index).ffill()
    p = target.astype(float)
    f252 = (p.shift(-252) / p - 1.0) * 100.0
    out = []
    for nm, m in [("上穿30", (v > 30) & (v.shift(1) <= 30)),
                  ("≥40", v >= 40),
                  ("分位>95%", vol.rank(pct=True) > 0.95),
                  ("自63日高点回落40%+且>25",
                   ((v / v.rolling(63).max() - 1) < -0.40) & ((v / v.rolling(63).max() - 1).shift(1) >= -0.40) & (v > 25))]:
        m = m.reindex(p.index).fillna(False)
        s = f252[m].dropna()
        base = f252.dropna().mean()
        out.append({"标的": label, "波动率指数": "对口" if vol is not vix else "VIX(通用)",
                    "信号": nm, "次数": int(m.sum()),
                    "12M均值%": s.mean() if len(s) else np.nan,
                    "12M胜率%": (s > 0).mean() * 100 if len(s) else np.nan,
                    "超额pp": (s.mean() - base) if len(s) else np.nan})
    return out

rows = []
rows += sig_effect(vxn, px["NDX"], "纳指100")
rows += sig_effect(vix, px["NDX"], "纳指100")
rows += sig_effect(rvx, px["RUT"], "罗素2000")
rows += sig_effect(vix, px["RUT"], "罗素2000")
fs = pd.DataFrame(rows)
fs.to_csv(os.path.join(OUT, "vix_family_sig.csv"), index=False, encoding="utf-8-sig")
print("\n=== 2. 用对口波动率 vs 用 VIX 的效果对比（未来 12 个月）===")
print(fs.round(2).to_string(index=False))

# ---------- 3) 当前读数 ----------
last = vix.index[-1]
rows = []
for nm, s in [("VIX", vix), ("VXN", vxn), ("RVX", rvx)]:
    p90 = s.rolling(2520, min_periods=1260).apply(lambda a: (a[-1] > a[:-1]).mean(), raw=True)
    rows.append({"指数": nm, "最新收盘": s.iloc[-1], "日期": str(s.index[-1].date()),
                 "滚动10年分位%": p90.iloc[-1] * 100 if pd.notna(p90.iloc[-1]) else np.nan,
                 "20日均线": s.rolling(20).mean().iloc[-1],
                 "距20日均线倍数": s.iloc[-1] / s.rolling(20).mean().iloc[-1],
                 "63日高点": s.rolling(63).max().iloc[-1],
                 "自63日高点回落%": (s.iloc[-1] / s.rolling(63).max().iloc[-1] - 1) * 100})
fn = pd.DataFrame(rows)
fn.to_csv(os.path.join(OUT, "vix_family_now.csv"), index=False, encoding="utf-8-sig")
print("\n=== 3. 三者当前读数 ===")
print(fn.round(2).to_string(index=False))
print("\nsaved: vix_family / vix_family_sig / vix_family_now")
