# -*- coding: utf-8 -*-
"""择时章节图表 v2（位置温度计新定义 + 双轴图）。"""
import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm

BASE = r"E:\workspace\new"
PROC = os.path.join(BASE, "data", "processed"); OUT = os.path.join(BASE, "data", "output")
FIG = os.path.join(BASE, "output", "figures")
os.makedirs(FIG, exist_ok=True)
for cand in ["Microsoft YaHei", "SimHei"]:
    try:
        fm.findfont(cand, fallback_to_default=False); plt.rcParams["font.sans-serif"] = [cand]; break
    except Exception: continue
plt.rcParams["axes.unicode_minus"] = False

panel = pd.read_csv(os.path.join(PROC, "timing_panel.csv"), index_col=0, parse_dates=True)
comp = pd.read_csv(os.path.join(PROC, "timing_composite.csv"), index_col=0, parse_dates=True)
eq = pd.read_csv(os.path.join(PROC, "timing_equity.csv"), index_col=0, parse_dates=True)
axesd = pd.read_csv(os.path.join(PROC, "timing_axes.csv"), index_col=0, parse_dates=True)
px = panel["SPX"].astype(float)

# --- 图 09：位置温度计 ---
d = comp.dropna(subset=["综合"])
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(11.5, 7.4), sharex=True,
                               gridspec_kw={"height_ratios": [1.3, 1]})
ax1.semilogy(px.index, px, color="#1f4e79", lw=1.1)
ax1.set_title("标普500 与「位置温度计」（1994-05 起；0=极冷/极便宜，100=极热/极贵）", fontsize=12)
ax1.set_ylabel("标普500（对数）"); ax1.grid(alpha=.25)
ax2.plot(d.index, d["综合"], color="#c00000", lw=.8)
ax2.fill_between(d.index, 0, d["综合"], color="#c00000", alpha=.10)
ax2.axhline(75, color="#8b0000", ls="--", lw=.8)
ax2.axhline(25, color="#0f8b8d", ls="--", lw=.8)
ax2.text(d.index[30], 78, "75 过热", fontsize=8, color="#8b0000")
ax2.text(d.index[30], 17, "25 过冷", fontsize=8, color="#0f8b8d")
ax2.set_ylim(0, 100); ax2.set_ylabel("综合温度"); ax2.grid(alpha=.25)
plt.tight_layout(); plt.savefig(os.path.join(FIG, "09_位置温度计.png"), dpi=160); plt.close()

# --- 图 10：温度分层 vs 未来收益 ---
fq = pd.read_csv(os.path.join(OUT, "timing_composite_quintile.csv"))
fig, axes = plt.subplots(1, 3, figsize=(12.5, 4.4))
for ax, lab in zip(axes, ["1年", "3年", "5年"]):
    s = fq[fq["期限"] == lab].reset_index(drop=True); vals = s["均值%"].values
    ax.bar(range(len(s)), vals, color=["#0f8b8d", "#4a9e9f", "#bfbfbf", "#d98e73", "#c00000"])
    ax.set_xticks(range(len(s))); ax.set_xticklabels(["最冷", "Q2", "Q3", "Q4", "最热"], fontsize=9)
    ax.set_title("未来 %s 平均收益（按当前温度分组）" % lab, fontsize=11, pad=10)
    ax.set_ylabel("%"); ax.grid(axis="y", alpha=.3)
    span = max(vals) - min(vals) if max(vals) > min(vals) else 1
    ax.set_ylim(min(0, vals.min()) - span*0.12, vals.max() + span*0.22)
    for i, v in enumerate(vals):
        ax.text(i, v + span*0.05, "%.1f" % v, ha="center", fontsize=8.5)
plt.tight_layout(); plt.savefig(os.path.join(FIG, "10_位置与未来收益.png"), dpi=160); plt.close()

# --- 图 11：择时净值（保留原图，重绘）---
fig, ax = plt.subplots(figsize=(11.5, 5.6))
cmap = {"买入持有": "#7f7f7f", "双均线 50/200": "#1f4e79", "合成策略": "#c00000", "70%底仓+30%择时": "#0f8b8d"}
for c in eq.columns:
    ax.semilogy(eq.index, eq[c], label=c, lw=1.3, color=cmap.get(c))
ax.set_title("择时策略累计净值对比（对数坐标，含 5bp 单边成本）", fontsize=12)
ax.set_ylabel("累计净值（对数）"); ax.grid(alpha=.25); ax.legend(fontsize=9)
plt.tight_layout(); plt.savefig(os.path.join(FIG, "11_择时净值.png"), dpi=160); plt.close()

# --- 图 12：分项雷达 ---
cols = ["估值热", "趋势热", "情绪热", "信用热", "宏观热"]
last = comp[cols].iloc[-1]; avg = comp[cols].mean()
labels = cols
ang = np.linspace(0, 2*np.pi, len(labels), endpoint=False).tolist(); ang += ang[:1]
fig, ax = plt.subplots(figsize=(6.4, 6.4), subplot_kw=dict(polar=True))
for vals, nm, col in [(last.values.tolist()+[last.values[0]], "当前（2026-11-06）", "#c00000"),
                      (avg.values.tolist()+[avg.values[0]], "1994 年以来均值", "#7f7f7f")]:
    ax.plot(ang, vals, lw=1.8, label=nm, color=col); ax.fill(ang, vals, alpha=.12, color=col)
ax.set_xticks(ang[:-1]); ax.set_xticklabels(labels, fontsize=10)
ax.set_ylim(0, 100); ax.set_title("位置分项温度（0=冷/便宜，100=热/贵）", pad=20, fontsize=12)
ax.legend(loc="lower right", bbox_to_anchor=(1.15, -.05), fontsize=9)
plt.tight_layout(); plt.savefig(os.path.join(FIG, "12_分项温度雷达.png"), dpi=160); plt.close()

# --- 图 13：事件式 ---
ev = pd.read_csv(os.path.join(OUT, "timing_events.csv")).sort_values("未来1年均值%")
fig, ax = plt.subplots(figsize=(11.5, 5.2))
ax.barh(range(len(ev)), ev["未来1年均值%"], color="#1f4e79", alpha=.85)
ax.set_yticks(range(len(ev))); ax.set_yticklabels(ev["情景"], fontsize=9)
ax.axvline(ev["未来1年均值%"].mean(), color="gray", ls="--", lw=.8)
for i, (v, w) in enumerate(zip(ev["未来1年均值%"], ev["未来1年胜率%"])):
    ax.text(v + 0.35, i, "%.1f%%  (胜率 %.0f%%)" % (v, w), va="center", fontsize=8)
ax.set_xlabel("该状态出现后未来 1 年平均收益（%）")
ax.set_title("「位置」状态与未来 1 年收益", fontsize=12)
ax.set_xlim(0, ev["未来1年均值%"].max()*1.28); ax.grid(axis="x", alpha=.25)
plt.tight_layout(); plt.savefig(os.path.join(FIG, "13_位置事件检验.png"), dpi=160); plt.close()

# --- 图 14：双轴散点（估值轴 vs 趋势轴，颜色=未来1年收益）---
f1 = (px.shift(-252)/px).reindex(axesd.index)
fig, ax = plt.subplots(figsize=(8.4, 6.6))
s = ax.scatter(axesd["V"], axesd["T"], c=f1*100, cmap="RdYlGn", vmin=-40, vmax=60, s=6, alpha=.75)
cb = plt.colorbar(s, ax=ax); cb.set_label("未来 1 年收益（%）")
ax.axvline(0.5, color="gray", ls="--", lw=.8); ax.axhline(0.5, color="gray", ls="--", lw=.8)
ax.set_xlabel("估值轴（0=便宜，1=贵）"); ax.set_ylabel("趋势轴（0=弱，1=强）")
ax.set_title("双轴坐标下的标普500 历史路径（1994-05 起）", fontsize=12)
ax.scatter([axesd["V"].iloc[-1]], [axesd["T"].iloc[-1]], marker="*", s=380,
           color="#c00000", edgecolor="k", zorder=5, label="当前（2026-11-06）")
ax.legend(loc="upper left", fontsize=9); ax.grid(alpha=.25)
plt.tight_layout(); plt.savefig(os.path.join(FIG, "14_双轴坐标.png"), dpi=160); plt.close()

print("figures 09-14 regenerated")
