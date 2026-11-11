# -*- coding: utf-8 -*-
"""趋势与风险图表。"""
import os
import numpy as np, pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm

RAW = r"E:\workspace\new\data\raw"; PROC = r"E:\workspace\new\data\processed"
FIG = r"E:\workspace\new\output\figures"
os.makedirs(FIG, exist_ok=True)

# 中文字体
for cand in ["Microsoft YaHei", "SimHei", "Noto Sans CJK SC"]:
    try:
        fm.findfont(cand, fallback_to_default=False)
        plt.rcParams["font.sans-serif"] = [cand]; break
    except Exception:
        continue
plt.rcParams["axes.unicode_minus"] = False
print("font:", plt.rcParams["font.sans-serif"])

C = pd.read_csv(os.path.join(PROC, "prices_close.csv"), index_col=0, parse_dates=True)
ORDER = ["SPX","DJI","IXIC","NDX","RUT","SOX"]
CN = {"SPX":"标普500","DJI":"道琼斯工业","IXIC":"纳斯达克综合","NDX":"纳斯达克100","RUT":"罗素2000","SOX":"费城半导体"}
COL = dict(zip(ORDER, ["#1f4e79","#c00000","#2e7d32","#7030a0","#bf8f00","#0f8b8d"]))
D = C.loc["1994-05-05":]

# 1 累计净值（对数）
fig, ax = plt.subplots(figsize=(11,6.2))
for k in ORDER:
    s = D[k].dropna(); ax.plot(s.index, s/s.iloc[0], label=CN[k], color=COL[k], lw=1.4)
ax.set_yscale("log"); ax.set_title("六大美股指数累计净值（1994-05-05 = 1，对数坐标，价格指数）")
ax.set_ylabel("累计净值（倍，对数）"); ax.grid(alpha=.3); ax.legend(ncol=3, fontsize=9)
ax.axhline(1, color="gray", lw=.6)
plt.tight_layout(); plt.savefig(os.path.join(FIG,"01_累计净值.png"), dpi=160); plt.close()

# 2 回撤曲线
fig, ax = plt.subplots(figsize=(11,5))
for k in ORDER:
    s = D[k].dropna(); c = s/s.iloc[0]; dd = c/c.cummax()-1
    ax.plot(dd.index, dd*100, label=CN[k], color=COL[k], lw=1.0, alpha=.85)
ax.set_title("六大指数历史回撤（自 1994-05-05 起）"); ax.set_ylabel("回撤（%）")
ax.grid(alpha=.3); ax.legend(ncol=3, fontsize=9)
plt.tight_layout(); plt.savefig(os.path.join(FIG,"02_回撤曲线.png"), dpi=160); plt.close()

# 3 滚动 1 年波动率
fig, ax = plt.subplots(figsize=(11,5))
for k in ORDER:
    r = D[k].dropna().pct_change().rolling(252).std()*np.sqrt(252)*100
    ax.plot(r.index, r, label=CN[k], color=COL[k], lw=1.0)
ax.set_title("滚动 252 日年化波动率"); ax.set_ylabel("%"); ax.grid(alpha=.3); ax.legend(ncol=3, fontsize=9)
plt.tight_layout(); plt.savefig(os.path.join(FIG,"03_滚动波动率.png"), dpi=160); plt.close()

# 4 风险-收益散点（全样本 & 近十年）
fig, axes = plt.subplots(1,2, figsize=(12,5))
for ax, (a, ttl) in zip(axes, [("1994-05-05","1994-05 起全样本"), ("2016-11-01","近 10 年")]):
    sub = C.loc[a:]
    for k in ORDER:
        s = sub[k].dropna(); r = s.pct_change().dropna()
        yrs = (s.index[-1]-s.index[0]).days/365.25
        x = r.std()*np.sqrt(252)*100; y = ((s.iloc[-1]/s.iloc[0])**(1/yrs)-1)*100
        ax.scatter(x, y, s=70, color=COL[k]); ax.annotate(CN[k], (x,y), fontsize=8, xytext=(4,4), textcoords="offset points")
    ax.set_xlabel("年化波动率 %"); ax.set_ylabel("年化收益 %"); ax.set_title(ttl); ax.grid(alpha=.3)
plt.tight_layout(); plt.savefig(os.path.join(FIG,"04_风险收益散点.png"), dpi=160); plt.close()

# 5 分阶段热力图
ph = pd.read_csv(r"E:\workspace\new\data\output\phases.csv")
p = ph.pivot_table(index="阶段", columns="指数", values="cumret", sort=False)[ORDER]*100
order = list(dict.fromkeys(ph["阶段"]))
p = p.loc[order]
fig, ax = plt.subplots(figsize=(9.5,5.6))
im = ax.imshow(p.values, cmap="RdYlGn", aspect="auto", vmin=-100, vmax=250)
ax.set_xticks(range(len(ORDER))); ax.set_xticklabels([CN[k] for k in ORDER], fontsize=9)
ax.set_yticks(range(len(p.index))); ax.set_yticklabels(p.index, fontsize=9)
for i in range(p.shape[0]):
    for j in range(p.shape[1]):
        v = p.values[i,j]
        ax.text(j, i, f"{v:.0f}", ha="center", va="center", fontsize=8,
                color="white" if v < -40 or v > 180 else "black")
ax.set_title("分阶段累计收益（%，价格指数）")
plt.colorbar(im, ax=ax, shrink=.8, label="累计收益 %")
plt.tight_layout(); plt.savefig(os.path.join(FIG,"05_分阶段热力图.png"), dpi=160); plt.close()

# 6 年度收益柱状（标普500 vs 纳指100 vs 罗素2000）
yr = C.loc["1994-05-05":].resample("YE").last().pct_change()[ORDER]*100
yr.index = yr.index.year
fig, ax = plt.subplots(figsize=(12,4.6))
x = np.arange(len(yr)); w = .27
for i, k in enumerate(["SPX","NDX","RUT"]):
    ax.bar(x + (i-1)*w, yr[k], w, label=CN[k], color=COL[k])
ax.set_xticks(x); ax.set_xticklabels(yr.index, rotation=90, fontsize=8)
ax.axhline(0, color="black", lw=.8); ax.set_ylabel("年度收益 %"); ax.legend()
ax.set_title("年度收益率对比（1994–2026）"); ax.grid(alpha=.25, axis="y")
plt.tight_layout(); plt.savefig(os.path.join(FIG,"06_年度收益.png"), dpi=160); plt.close()

# 7 行业权重堆积
S = pd.read_csv(r"E:\workspace\new\data\output\sector_weights.csv", index_col=0)
S = S.drop(index=[i for i in S.index if i in ("合计","Other")], errors="ignore")
cols = ["标普500","罗素2000","罗素1000成长","罗素1000价值","费城半导体"]
fig, ax = plt.subplots(figsize=(10,4.8))
bottom = np.zeros(len(cols))
for sec in S.index:
    v = S.loc[sec, cols].values
    ax.bar(cols, v, bottom=bottom, label=sec)
    bottom += v
ax.set_ylabel("权重 %"); ax.set_title("GICS 一级行业权重分布（2026-11-05 持仓）")
ax.legend(fontsize=7, ncol=2, loc="upper right", framealpha=.9)
ax.set_ylim(0, 108)
plt.tight_layout(); plt.savefig(os.path.join(FIG,"07_行业权重.png"), dpi=160); plt.close()

# 8 成长/价值相对强弱
gv = pd.read_csv(r"E:\workspace\new\data\output\growth_value_ratio.csv", index_col=0, parse_dates=True).iloc[:,0]
fig, ax = plt.subplots(figsize=(11,4.2))
ax.plot(gv.index, gv.values, color="#7030a0", lw=1.2)
ax.set_yscale("log"); ax.set_title("大盘成长 / 大盘价值 相对强弱（IWF/IWD，2000-05 起，对数）")
ax.grid(alpha=.3); ax.set_ylabel("比值（对数）")
plt.tight_layout(); plt.savefig(os.path.join(FIG,"08_成长价值.png"), dpi=160); plt.close()
print("figures done:", sorted(os.listdir(FIG)))
