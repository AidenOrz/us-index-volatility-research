# -*- coding: utf-8 -*-
"""VIX 专题图表（6 张），输出 E:\\workspace\\new\\output\\figures\\"""
import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

BASE = r"E:\workspace\new"
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
C1, C2, C3 = "#1f4e79", "#c0504d", "#4f81bd"

panel = pd.read_csv(os.path.join(BASE, "data", "processed", "timing_panel.csv"), index_col=0, parse_dates=True)
panel = panel.loc["1994-05-05":].copy()
px = panel["SPX"].astype(float)
vix = panel["VIX"].astype(float)
ret = px.pct_change()

# ---------- 图 1：VIX 水平分层 -> 未来 12 个月收益与胜率 ----------
lv = pd.read_csv(os.path.join(OUT, "vix_level_bins.csv"))
lab = lv["分组"].astype(str).tolist()
x = np.arange(len(lab))
fig, ax1 = plt.subplots(figsize=(10, 4.8))
vals = lv["12M均值%"].tolist()
cmap = plt.get_cmap("Blues")
norm = [(v - min(vals)) / (max(vals) - min(vals)) * 0.55 + 0.35 for v in vals]
b = ax1.bar(x, vals, color=[cmap(n) for n in norm], edgecolor="#1f4e79", lw=0.6, width=0.62)
ax1.set_ylabel("未来 12 个月平均收益（%）", color=C1)
ax1.tick_params(axis="y", labelcolor=C1)
ax1.axhline(10.49, color="gray", ls="--", lw=1)
ax1.text(-0.45, 11.1, "全样本基准 10.49%", va="bottom", ha="left", fontsize=8.5, color="gray")
ax1.set_ylim(0, max(vals) * 1.22)
for xi, v in zip(x, vals):
    ax1.text(xi, v + 0.6, "%.1f" % v, ha="center", fontsize=9.5, color="#1f4e79")
ax2 = ax1.twinx()
ax2.plot(x, lv["12M胜率%"], "o-", color="#e46c0a", lw=2, ms=6)
ax2.set_ylabel("12 个月胜率（%）", color="#e46c0a")
ax2.tick_params(axis="y", labelcolor="#e46c0a")
ax2.set_ylim(55, 100)
ax2.grid(False)
ax1.set_xticks(x); ax1.set_xticklabels(lab, rotation=30, ha="right")
ax1.set_xlabel("VIX 收盘水平")
ax1.set_title("图 1  VIX 水平分层：越恐慌，未来一年越好（1994-05~2026-11，SPX）", fontsize=11.5, pad=10)
fig.tight_layout()
fig.savefig(os.path.join(FIG, "15_VIX水平分层.png"), bbox_inches="tight")
plt.close(fig)

# ---------- 图 2：U 型曲线（含趋势状态） ----------
us = pd.read_csv(os.path.join(OUT, "vix_ushape.csv"))
order = ["<13", "13-20", "20-25", "25-30", "30-40", ">40"]
piv = us.pivot(index="VIX区间", columns="趋势", values="12M均值%").reindex(order)
fig, ax = plt.subplots(figsize=(9.5, 4.8))
x = np.arange(len(order))
ax.plot(x, piv["站上200日线"], "o-", color=C1, lw=2.2, ms=7, label="SPX 站上 200 日线")
ax.plot(x, piv["跌破200日线"], "s-", color=C2, lw=2.2, ms=7, label="SPX 跌破 200 日线")
for xi in x:
    up_v = piv["站上200日线"].iloc[xi]
    dn_v = piv["跌破200日线"].iloc[xi]
    up_off = (0, 13) if up_v >= dn_v else (0, -18)
    dn_off = (0, -18) if up_v >= dn_v else (0, 13)
    ax.annotate("%.1f" % up_v, (xi, up_v), textcoords="offset points",
                xytext=up_off, ha="center", fontsize=8.5, color=C1,
                bbox=dict(boxstyle="round,pad=0.12", fc="white", ec="none", alpha=0.75))
    ax.annotate("%.1f" % dn_v, (xi, dn_v), textcoords="offset points",
                xytext=dn_off, ha="center", fontsize=8.5, color=C2,
                bbox=dict(boxstyle="round,pad=0.12", fc="white", ec="none", alpha=0.75))
ax.set_ylim(min(piv.min()) - 6, max(piv.max()) + 7)
ax.axvspan(1.6, 2.4, color="#e46c0a", alpha=0.12)
ax.text(2.0, ax.get_ylim()[1] - 4.0, "最差洼地\nVIX 20-25", ha="center", va="top", fontsize=9, color="#a05000",
        bbox=dict(boxstyle="round,pad=0.25", fc="white", ec="#e46c0a", alpha=0.85))
ax.axhline(0, color="black", lw=0.8)
ax.set_xticks(x); ax.set_xticklabels(order)
ax.set_xlabel("VIX 水平"); ax.set_ylabel("未来 12 个月平均收益（%）")
ax.legend(loc="upper left", fontsize=9, framealpha=0.9)
ax.set_title("图 2  VIX 与未来收益不是单调关系：两端高、中间（20-25）最低", fontsize=11.5, pad=10)
fig.tight_layout()
fig.savefig(os.path.join(FIG, "16_VIX_U型曲线.png"), bbox_inches="tight")
plt.close(fig)

# ---------- 图 3：事件后收益路径 ----------
pth = pd.read_csv(os.path.join(OUT, "vix_path.csv"))
hs = [5, 10, 21, 63, 126, 252, 378, 504]
keys = ["全样本基准", "VIX 上穿 25", "VIX 上穿 30", "VIX 上穿 40", "VIX 分位>95%"]
cols = {"全样本基准": "gray", "VIX 上穿 25": "#9dc3e6", "VIX 上穿 30": C3,
        "VIX 上穿 40": C2, "VIX 分位>95%": "#8064a2"}
fig, ax = plt.subplots(figsize=(9.5, 4.8))
for k in keys:
    row = pth[pth["事件"] == k]
    if row.empty:
        continue
    ys = [row["%d日均值%%" % h].iloc[0] for h in hs]
    ax.plot(hs, ys, "o-", color=cols[k], lw=2.0 if k != "全样本基准" else 1.6,
            ls="--" if k == "全样本基准" else "-", ms=5, label=k)
ax.set_xscale("log")
ax.set_xticks(hs)
ax.set_xticklabels(["5日", "10日", "1月", "3月", "6月", "1年", "1.5年", "2年"], fontsize=9)
ax.axhline(0, color="black", lw=0.8)
ax.set_ylabel("事件后累计收益（%）")
ax.legend(fontsize=9, loc="upper left", framealpha=0.9)
ax.set_title("图 3  恐慌信号触发后的收益路径：VIX>40 从第 1 个月起就领先", fontsize=11.5, pad=10)
fig.tight_layout()
fig.savefig(os.path.join(FIG, "17_VIX事件后路径.png"), bbox_inches="tight")
plt.close(fig)

# ---------- 图 4：VIX 与未来实现波动（VRP） ----------
vr = pd.read_csv(os.path.join(OUT, "vix_vrp.csv"))
vr = vr[vr["VIX档"] != "全样本"]
fig, ax1 = plt.subplots(figsize=(9.8, 4.8))
x = np.arange(len(vr))
w = 0.36
ax1.bar(x - w / 2, vr["未来21日实现波动中位数"], w, color=C3, alpha=0.85, label="未来 21 日已实现波动（中位）")
ax1.bar(x + w / 2, vr["VRP中位数"], w, color="#e46c0a", alpha=0.85, label="VRP = VIX − 未来实现波动（中位）")
for xi, a, b_ in zip(x, vr["未来21日实现波动中位数"], vr["VRP中位数"]):
    ax1.text(xi - w / 2, a + 0.6, "%.1f" % a, ha="center", fontsize=8)
    ax1.text(xi + w / 2, b_ + 0.6, "%.1f" % b_, ha="center", fontsize=8)
ax1.set_xticks(x); ax1.set_xticklabels(vr["VIX档"], rotation=20, ha="right")
ax1.set_xlabel("VIX 水平档"); ax1.set_ylabel("波动率（年化 %）")
ax1.set_ylim(0, vr["未来21日实现波动中位数"].max() * 1.30)
h1, l1 = ax1.get_legend_handles_labels()
ax2 = ax1.twinx()
l2 = ax2.plot(x, vr["VRP占VIX比"], "o-", color=C2, lw=2, ms=6, label="VRP 占 VIX 比例（右轴）")
ax2.set_ylabel("VRP 占 VIX 比例（%）", color=C2)
ax2.tick_params(axis="y", labelcolor=C2)
ax2.set_ylim(12, 34)
ax2.grid(False)
ax1.legend(h1 + l2, l1 + ["VRP 占 VIX 比例（右轴）"], fontsize=8.5,
           loc="upper left", bbox_to_anchor=(0.0, -0.20), ncol=3, frameon=False)
ax1.set_title("图 4  VIX 是未来波动的先行读数（相关 0.72），但溢价率随恐慌加深而收窄", fontsize=11.5, pad=10)
fig.tight_layout()
fig.savefig(os.path.join(FIG, "18_VIX与实现波动.png"), bbox_inches="tight")
plt.close(fig)

# ---------- 图 5：VIX 时间序列 + 分层阈值 ----------
fig, ax = plt.subplots(figsize=(11, 4.6))
ax.plot(vix.index, vix.values, color=C1, lw=0.8)
ax.axhline(40, color=C2, ls="--", lw=1.2)
ax.axhline(30, color="#e46c0a", ls="--", lw=1.0)
ax.axhline(20, color="gray", ls=":", lw=0.9)
ax.axhline(13, color="#4f81bd", ls="--", lw=1.0)
ax.fill_between(vix.index, 40, vix.values, where=(vix.values >= 40), color=C2, alpha=0.35, label="VIX≥40 极端恐慌")
ax.fill_between(vix.index, 0, vix.values, where=(vix.values < 13), color="#9dc3e6", alpha=0.45, label="VIX<13 自满")
ax.set_ylabel("VIX")
ax.text(vix.index[-1], 42, " 40", va="bottom", fontsize=8, color=C2)
ax.text(vix.index[-1], 31, " 30", va="bottom", fontsize=8, color="#e46c0a")
ax.text(vix.index[-1], 14, " 13", va="bottom", fontsize=8, color="#4f81bd")
ax.legend(fontsize=9, loc="upper left", framealpha=0.9)
ax.set_title("图 5  VIX 全历史与买卖点阈值：极端恐慌区极稀薄（VIX≥40 仅 208 天 / 2.5%，10 段事件）", fontsize=11.5, pad=10)
fig.tight_layout()
fig.savefig(os.path.join(FIG, "19_VIX历史与阈值.png"), bbox_inches="tight")
plt.close(fig)

# ---------- 图 6：仓位刻度阶梯 ----------
bands = [("<13", 0.95), ("13-20", 0.80), ("20-25", 0.45), ("25-30", 0.80), ("30-40", 0.95), (">40", 1.00)]
fig, ax = plt.subplots(figsize=(9.2, 4.2))
x = np.arange(len(bands))
vals = [b[1] for b in bands]
cols = [C2 if v < 0.7 else C1 for v in vals]
ax.bar(x, vals, color=cols, alpha=0.88, width=0.6)
ax.bar([3], [0.80], color="#e46c0a", alpha=0.95, width=0.6)   # 当前所在档高亮
for xi, v in zip(x, vals):
    if xi == 3:
        continue
    ax.text(xi, v + 0.02, "%.0f%%" % (v * 100), ha="center", fontsize=10)
ax.text(3, 0.40, "80%", ha="center", va="center", fontsize=11, color="white", fontweight="bold")
ax.annotate("当前 VIX 25.64\n落在这一档", xy=(3, 0.84), xytext=(3, 1.10),
            fontsize=9.5, color="#a05000", ha="center", va="bottom",
            arrowprops=dict(arrowstyle="-|>", color="#a05000", lw=1.5,
                            shrinkA=2, shrinkB=2))
ax.set_xticks(x); ax.set_xticklabels([b[0] for b in bands])
ax.set_xlabel("VIX 水平"); ax.set_ylabel("建议股票仓位")
ax.set_yticks([0, 0.2, 0.4, 0.6, 0.8, 1.0])
ax.set_ylim(0, 1.32); ax.set_xlim(-0.65, len(bands) - 0.35)
ax.yaxis.set_major_formatter(FuncFormatter(lambda v, p: "%.0f%%" % (v * 100)))
ax.set_title("图 6  U 型仓位刻度：不预测方向，只按情绪定价调仓位", fontsize=11.5, pad=10)
fig.tight_layout()
fig.savefig(os.path.join(FIG, "20_VIX仓位刻度.png"), bbox_inches="tight")
plt.close(fig)

print("saved 6 figures to", FIG)
for f in ["15_VIX水平分层.png", "16_VIX_U型曲线.png", "17_VIX事件后路径.png",
          "18_VIX与实现波动.png", "19_VIX历史与阈值.png", "20_VIX仓位刻度.png"]:
    p = os.path.join(FIG, f)
    print(f, os.path.getsize(p) // 1024, "KB")
