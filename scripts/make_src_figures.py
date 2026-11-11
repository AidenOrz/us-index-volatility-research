# -*- coding: utf-8 -*-
"""数据源尽调专题的 4 张图。"""
import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

BASE = r"E:\workspace\new"
CB = os.path.join(BASE, "data", "raw", "cboe_vol")
PROC = os.path.join(BASE, "data", "processed")
OUT = os.path.join(BASE, "data", "output")
FIG = os.path.join(BASE, "output", "figures")
os.makedirs(FIG, exist_ok=True)

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False
plt.rcParams["figure.dpi"] = 130
plt.rcParams["savefig.dpi"] = 130
plt.rcParams["axes.grid"] = True
plt.rcParams["grid.alpha"] = 0.25
plt.rcParams["grid.linestyle"] = "--"
C1, C2, C3, C4 = "#1f4e79", "#c0504d", "#4f81bd", "#e46c0a"


def load(t):
    d = pd.read_csv(os.path.join(CB, t + "_History.csv"))
    d["DATE"] = pd.to_datetime(d["DATE"], format="%m/%d/%Y")
    col = "CLOSE" if "CLOSE" in d.columns else d.columns[-1]
    return d.set_index("DATE")[col].astype(float).sort_index()


# ---------- 图 1：完整期限结构四条曲线（当前 vs 两个历史极端）----------
fig, ax = plt.subplots(figsize=(9.4, 4.8))
labels = ["9天", "30天", "3个月", "6个月"]
cur = [load("VIX9D").iloc[-1], load("VIX").iloc[-1], load("VIX3M").iloc[-1], load("VIX6M").iloc[-1]]
stress = [27.18, 25.64, 24.60, 24.70]      # 2026-11-06
crisis = [None, None, None, None]
# 2020-03-16 取历史
d1 = load("VIX9D"); d2 = load("VIX"); d3 = load("VIX3M"); d4 = load("VIX6M")
def at(s, ds):
    idx = s.index[s.index <= ds]
    return s.loc[idx[-1]] if len(idx) else None
crisis = [at(d1, "2020-03-16"), at(d2, "2020-03-16"), at(d3, "2020-03-16"), at(d4, "2020-03-16")]
calm = [at(d1, "2017-07-11"), at(d2, "2017-07-11"), at(d3, "2017-07-11"), at(d4, "2017-07-11")]
x = np.arange(4)
ax.plot(x, crisis, "s-", color=C2, lw=2.2, ms=8, label="2020-03-16 危机（深度倒挂）")
ax.plot(x, stress, "o-", color=C4, lw=2.0, ms=7, label="2026-11-06 冲击后（轻度倒挂）")
ax.plot(x, cur, "o-", color=C1, lw=2.6, ms=9, label="2026-11-09 当前（正常 contango）")
ax.plot(x, calm, "^--", color="#7f9db9", lw=1.6, ms=6, label="2017-07-11 极静（陡 contango）")
for xx, v in zip(x, cur):
    ax.annotate("%.1f" % v, (xx, v), textcoords="offset points", xytext=(0, -16),
                ha="center", fontsize=8.5, color=C1)
ax.set_yscale("log")
ax.set_yticks([8, 10, 12, 15, 20, 30, 40, 60, 80])
ax.get_yaxis().set_major_formatter(plt.FuncFormatter(lambda v, p: "%g" % v))
ax.set_ylim(7, 110)
ax.set_xticks(x); ax.set_xticklabels(labels)
ax.set_xlabel("合约期限"); ax.set_ylabel("隐含波动率（年化 %，对数轴）")
ax.legend(fontsize=8.8, loc="upper left", framealpha=0.92)
ax.set_title("图 1  VIX 期限结构四档曲线：形态比单点读数信息量大得多", fontsize=11.5, pad=10)
fig.tight_layout(); fig.savefig(os.path.join(FIG, "21_期限结构曲线.png"), bbox_inches="tight"); plt.close(fig)

# ---------- 图 2：四条斜率分位与未来 12 个月收益 ----------
sl = pd.read_csv(os.path.join(OUT, "vix_term_slopes.csv"))
order = ["0-10%", "10-50%", "50-90%", "90-100%"]
names = {"slope_short": "短端 VIX/VIX9D", "slope_mid": "中端 VIX3M/VIX",
         "slope_long": "长端 VIX6M/VIX3M", "slope_total": "全曲线 VIX6M/VIX9D"}
cols = [C1, C3, C4, C2]
fig, ax = plt.subplots(figsize=(9.4, 4.6))
w = 0.2
for i, (k, c) in enumerate(zip(names, cols)):
    sub = sl[sl["斜率"] == k].set_index("分位").reindex(order)
    ax.bar(np.arange(4) + (i - 1.5) * w, sub["12M均值%"], w, color=c, alpha=0.85, label=names[k])
    for j, v in enumerate(sub["12M均值%"]):
        ax.text(j + (i - 1.5) * w, v + 0.25, "%.1f" % v, ha="center", fontsize=7.6)
ax.set_xticks(np.arange(4)); ax.set_xticklabels(order)
ax.set_xlabel("斜率在过去 10 年的分位"); ax.set_ylabel("未来 12 个月 SPX 平均收益（%）")
ax.legend(fontsize=8.8, ncol=2, framealpha=0.92)
ax.set_title("图 2  期限结构越陡（分位越高），未来一年越差——四条斜率方向一致", fontsize=11.5, pad=10)
fig.tight_layout(); fig.savefig(os.path.join(FIG, "22_斜率与未来收益.png"), bbox_inches="tight"); plt.close(fig)

# ---------- 图 3：杠杆基金空头拥挤度（COT TFF）----------
tff = pd.read_csv(os.path.join(OUT, "cot_tff.csv"))
tff["报告日"] = pd.to_datetime(tff["报告日"])
fig, ax1 = plt.subplots(figsize=(10.6, 4.6))
ax1.plot(tff["报告日"], tff["杠杆基金净持仓"] / 1000, color=C1, lw=1.4, label="杠杆基金净持仓（千张，右轴为负=净空）")
ax1.axhline(0, color="black", lw=0.8)
ax1.set_ylabel("净持仓（千张）", color=C1)
ax1.tick_params(axis="y", labelcolor=C1)
ax2 = ax1.twinx()
ax2.fill_between(tff["报告日"], 0, tff["杠杆基金空头拥挤度分位%"], color=C2, alpha=0.18)
ax2.plot(tff["报告日"], tff["杠杆基金空头拥挤度分位%"], color=C2, lw=0.9, alpha=0.75)
ax2.axhline(90, color=C2, ls="--", lw=1.1)
ax2.set_ylabel("空头拥挤度分位（%）", color=C2)
ax2.tick_params(axis="y", labelcolor=C2)
ax2.set_ylim(0, 105)
ax2.grid(False)
ax1.set_title("图 3  VIX 期货杠杆基金净空持仓：82.9% 的周数为净空，空头拥挤度可算分位", fontsize=11.5, pad=10)
fig.tight_layout(); fig.savefig(os.path.join(FIG, "23_COT杠杆基金.png"), bbox_inches="tight"); plt.close(fig)

# ---------- 图 4：数据源覆盖对比 ----------
srcs = ["CBOE VIX", "CBOE VIX3M", "CBOE VIX9D", "CBOE VIX6M",
        "CBOE VVIX", "CBOE SKEW", "Yahoo ^VIX", "CFTC COT Legacy",
        "CFTC COT TFF", "vixcentral 期货曲线", "TradingView 快照"]
starts = [1990, 2009, 2011, 2008, 2006, 1990, 1990, 2004, 2006, 2007, 2026]
colr = [C1] * 6 + [C3] + [C2, C4] + ["#8064a2", "#7f9db9"]
fig, ax = plt.subplots(figsize=(10.2, 4.4))
for i, (s, c) in enumerate(zip(starts, colr)):
    ax.barh(i, 2026 - s + 0.9, left=s - 0.45, height=0.56, color=c, alpha=0.85)
    ax.text(2026.7, i, "起 %d" % s, va="center", fontsize=8.2)
ax.set_yticks(range(len(srcs)))
ax.set_yticklabels(srcs, fontsize=8.6)
ax.invert_yaxis()
ax.set_xlim(1988, 2040)
ax.set_xlabel("数据覆盖区间（年）")
ax.annotate("仅当期\n(2026-11)", xy=(2026, 10), xytext=(2029, 10.35),
            fontsize=8, color="#3a6ea5", va="center",
            arrowprops=dict(arrowstyle="->", color="#3a6ea5", lw=1.1))
ax.set_title("图 4  本轮实际可用的波动率相关数据源：起点覆盖 1990~2026", fontsize=11.5, pad=10)
fig.tight_layout()
fig.savefig(os.path.join(FIG, "24_数据源覆盖.png"), bbox_inches="tight")
plt.close(fig)

print("saved 4 figures")
for f in ["21_期限结构曲线.png", "22_斜率与未来收益.png", "23_COT杠杆基金.png", "24_数据源覆盖.png"]:
    print(" ", f, os.path.getsize(os.path.join(FIG, f)) // 1024, "KB")
