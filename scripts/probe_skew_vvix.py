# -*- coding: utf-8 -*-
"""新数据源带来的新指标：SKEW（尾部风险偏度）与 VVIX（波动率的波动率）。
这两条此前未纳入择时面板，是 CBOE 官方新下载文件里独有的。
产出 data/output/skew_vvix_stat.csv
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


skew = load("SKEW")
vvix = load("VVIX")
vix = load("VIX")
px = pd.read_csv(os.path.join(PROC, "prices_close.csv"), index_col=0, parse_dates=True)["SPX"].astype(float)

df = pd.concat([skew.rename("SKEW"), vvix.rename("VVIX"), vix.rename("VIX"), px.rename("SPX")], axis=1)
df = df.loc["1994-05-05":]
print("合并面板:", df.shape, df.index.min().date(), "~", df.index.max().date())
print("各列有效数:", df.notna().sum().to_dict())

f21 = (df["SPX"].shift(-21) / df["SPX"] - 1) * 100
f63 = (df["SPX"].shift(-63) / df["SPX"] - 1) * 100
f126 = (df["SPX"].shift(-126) / df["SPX"] - 1) * 100
f252 = (df["SPX"].shift(-252) / df["SPX"] - 1) * 100
fvix21 = (df["VIX"].shift(-21) - df["VIX"])


def rp(s, win=2520, minp=1260):
    return s.rolling(win, min_periods=minp).apply(lambda a: (a[-1] > a[:-1]).mean(), raw=True)


rows = []
# SKEW 分层
sk = df["SKEW"].dropna()
print("\nSKEW 分布:", "min=%.1f p10=%.1f med=%.1f p90=%.1f max=%.1f" % (
    sk.min(), sk.quantile(.1), sk.median(), sk.quantile(.9), sk.max()))
for lo, hi, lab in [(100, 115, "100-115 低偏度"), (115, 125, "115-125"), (125, 135, "125-135"),
                    (135, 145, "135-145"), (145, 200, "145+ 高偏度")]:
    m = (df["SKEW"] >= lo) & (df["SKEW"] < hi)
    rows.append({"指标": "SKEW", "分组": lab, "天数": int(m.sum()),
                 "1M均值%": f21[m].dropna().mean(), "1M胜率%": (f21[m].dropna() > 0).mean() * 100,
                 "3M均值%": f63[m].dropna().mean(),
                 "12M均值%": f252[m].dropna().mean(), "12M胜率%": (f252[m].dropna() > 0).mean() * 100,
                 "未来21日VIX变化": fvix21[m].dropna().mean()})

# VVIX 分档
print("VVIX 分布:", "min=%.1f p10=%.1f med=%.1f p90=%.1f max=%.1f" % (
    df["VVIX"].min(), df["VVIX"].quantile(.1), df["VVIX"].median(),
    df["VVIX"].quantile(.9), df["VVIX"].max()))
for lo, hi, lab in [(0, 80, "VVIX<80 极静"), (80, 95, "80-95"), (95, 110, "95-110"),
                    (110, 130, "110-130"), (130, 999, "VVIX>130 极动")]:
    m = (df["VVIX"] >= lo) & (df["VVIX"] < hi)
    rows.append({"指标": "VVIX", "分组": lab, "天数": int(m.sum()),
                 "1M均值%": f21[m].dropna().mean(), "1M胜率%": (f21[m].dropna() > 0).mean() * 100,
                 "3M均值%": f63[m].dropna().mean(),
                 "12M均值%": f252[m].dropna().mean(), "12M胜率%": (f252[m].dropna() > 0).mean() * 100,
                 "未来21日VIX变化": fvix21[m].dropna().mean()})

# 分位版本（滚动10年）
for nm in ["SKEW", "VVIX"]:
    p = rp(df[nm])
    for lo, hi in [(0, .10), (.10, .50), (.50, .90), (.90, 1.001)]:
        m = (p >= lo) & (p < hi)
        rows.append({"指标": nm + "(10年分位)", "分组": "%g-%g%%" % (round(lo * 100), round(min(hi, 1) * 100)),
                     "天数": int(m.sum()),
                     "1M均值%": f21[m].dropna().mean(), "1M胜率%": (f21[m].dropna() > 0).mean() * 100,
                     "3M均值%": f63[m].dropna().mean(),
                     "12M均值%": f252[m].dropna().mean(), "12M胜率%": (f252[m].dropna() > 0).mean() * 100,
                     "未来21日VIX变化": fvix21[m].dropna().mean()})

res = pd.DataFrame(rows)
res.to_csv(os.path.join(OUT, "skew_vvix_stat.csv"), index=False, encoding="utf-8-sig")
print("\n=== SKEW / VVIX 分层 ===")
print(res.round(2).to_string(index=False))

# SKEW 与 VIX 的背离：VIX 低但 SKEW 高 = 便宜的保护
print("\n=== VIX 低 × SKEW 高（便宜的保护）===")
vp = rp(df["VIX"]); sp = rp(df["SKEW"])
for lab, m in [
    ("VIX分位<50 且 SKEW分位>75", (vp < .5) & (sp > .75)),
    ("VIX分位<50 且 SKEW分位<50", (vp < .5) & (sp < .5)),
    ("VIX分位>75 且 SKEW分位>75", (vp > .75) & (sp > .75)),
]:
    s = f252[m].dropna()
    s21 = f21[m].dropna()
    print("  %-26s 天数=%-5d 1M=%+6.2f%% 胜率=%.1f%%  12M=%+6.2f%% 胜率=%.1f%%  未来21日VIX变化=%+.2f" % (
        lab, int(m.sum()), s21.mean(), (s21 > 0).mean() * 100, s.mean(), (s > 0).mean() * 100, fvix21[m].dropna().mean()))

# 相关系数
print("\n=== 相关 ===")
print("SKEW vs VIX 水平:", round(skew.corr(df["VIX"]), 4))
print("VVIX vs VIX 水平:", round(df["VVIX"].corr(df["VIX"]), 4))
print("SKEW vs 未来21日SPX:", round(df["SKEW"].corr(f21), 4))
print("VVIX vs 未来21日SPX:", round(df["VVIX"].corr(f21), 4))
print("SKEW vs 未来21日VIX变化:", round(df["SKEW"].corr(fvix21), 4))
print("VVIX vs 未来21日VIX变化:", round(df["VVIX"].corr(fvix21), 4))
