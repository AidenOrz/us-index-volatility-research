# -*- coding: utf-8 -*-
"""VIX 买卖点：U 型结构验证、条件细分、U 型仓位策略、当前状态历史类比。
产出：
  vix_ushape.csv        VIX 区间 × 趋势状态 交叉细分
  vix_ushape_strat.csv  按 U 型曲线设计的仓位策略
  vix_analog.csv        当前状态的历史类比（VIX 区间+倒挂+距高点）
  vix_rulebook.csv      可执行规则手册（含当前读数与动作）
"""
import os
import numpy as np
import pandas as pd

BASE = r"E:\workspace\new"
PROC = os.path.join(BASE, "data", "processed")
OUT = os.path.join(BASE, "data", "output")
COST = 0.0005

panel = pd.read_csv(os.path.join(PROC, "timing_panel.csv"), index_col=0, parse_dates=True)
panel = panel.loc["1994-05-05":].copy()
px = panel["SPX"].astype(float)
ret = px.pct_change()
rf = panel["rf_d"].fillna(0.0)
vix = panel["VIX"].astype(float)
vts = panel["vix_ts"].astype(float)
vp = panel["vix_p"].astype(float)
ma200 = px.rolling(200).mean()
above = (px > ma200)
f21 = (px.shift(-21) / px - 1.0) * 100.0
f252 = (px.shift(-252) / px - 1.0) * 100.0

# ---------- 1) VIX 区间 × 趋势状态 ----------
bands = [("<13", vix < 13), ("13-20", (vix >= 13) & (vix < 20)),
         ("20-25", (vix >= 20) & (vix < 25)), ("25-30", (vix >= 25) & (vix < 30)),
         ("30-40", (vix >= 30) & (vix < 40)), (">40", vix >= 40)]
rows = []
for lab, m in bands:
    for tl, tm in [("站上200日线", m & above), ("跌破200日线", m & ~above)]:
        s = f252[tm].dropna()
        rows.append({"VIX区间": lab, "趋势": tl, "天数": int(tm.sum()),
                     "12M均值%": s.mean() if len(s) else np.nan,
                     "12M胜率%": (s > 0).mean() * 100 if len(s) else np.nan,
                     "12M最差%": s.min() if len(s) else np.nan})
us = pd.DataFrame(rows)
us.to_csv(os.path.join(OUT, "vix_ushape.csv"), index=False, encoding="utf-8-sig")
print("=== 1. VIX 区间 × 趋势状态（未来 12 个月）===")
print(us.round(2).to_string(index=False))
piv = us.pivot(index="VIX区间", columns="趋势", values="12M均值%").reindex([b[0] for b in bands])
print("\n透视：")
print(piv.round(2).to_string())
print("\n（天数）")
print(us.pivot(index="VIX区间", columns="趋势", values="天数").reindex([b[0] for b in bands]).to_string())

# ---------- 2) U 型仓位策略 ----------
def bt(sig, name):
    w = sig.reindex(px.index).ffill().shift(1).fillna(0.0).clip(0, 1)
    dr = w * ret + (1 - w) * rf - w.diff().abs().fillna(0) * COST
    eq = (1 + dr).cumprod()
    yrs = len(dr) / 252.0
    ann = eq.iloc[-1] ** (1 / yrs) - 1
    mdd = (eq / eq.cummax() - 1).min()
    return {"策略": name, "累计%": (eq.iloc[-1] - 1) * 100, "年化%": ann * 100,
            "波动%": dr.std(ddof=1) * np.sqrt(252) * 100,
            "夏普": (dr.mean() * 252) / (dr.std(ddof=1) * np.sqrt(252)),
            "最大回撤%": mdd * 100, "卡玛": ann * 100 / abs(mdd * 100) if mdd else np.nan,
            "平均仓位%": w.mean() * 100, "年换手": w.diff().abs().fillna(0).sum() / yrs}

def u_shape(v):
    # 按实测 U 型：两端重、20-25 轻
    if v >= 40: return 1.00
    if v >= 30: return 0.95
    if v >= 25: return 0.80
    if v >= 20: return 0.45      # 最差区间，仓位最低
    if v >= 15: return 0.80
    return 0.95                  # 极平静，反而重仓

one = pd.Series(1.0, index=px.index)
w_u = vix.apply(u_shape)
# U 型 + 趋势否决（跌破年线时 20-25 区更危险）
w_ut = w_u.where(above, np.minimum(w_u, 0.50))
# 只减不增的温和版：底仓 70% + 30% U 型
w_mid = 0.7 + 0.3 * w_u
rows = [bt(one, "买入持有"), bt(w_u, "U型仓位（VIX 20-25 减到 45%）"),
        bt(w_ut, "U型+跌破年线再砍半"), bt(w_mid, "70%底仓 + 30% U型")]
ust = pd.DataFrame(rows).sort_values("夏普", ascending=False)
ust.to_csv(os.path.join(OUT, "vix_ushape_strat.csv"), index=False, encoding="utf-8-sig")
print("\n=== 2. U 型仓位策略回测 ===")
print(ust.round(2).to_string(index=False))

# ---------- 3) 当前状态历史类比 ----------
last = px.index[-1]
v_now, ts_now, vp_now = vix.iloc[-1], vts.iloc[-1], vp.iloc[-1]
dd_now = px.iloc[-1] / px.cummax().iloc[-1] - 1.0
print("\n当前：VIX=%.2f 分位=%.1f%% 期限差=%.2f%% 距高点=%.2f%%" % (v_now, vp_now * 100, ts_now * 100, dd_now * 100))

# 相似历史日：VIX 分位 80-95%，期限倒挂 >0，距高点 -3%~-10%
sim = (vp >= 0.80) & (vp <= 0.95) & (vts > 0.0) & (px / px.cummax() - 1 >= -0.10) & (px / px.cummax() - 1 <= -0.03)
rows = []
for h, lab in [(21, "1个月"), (63, "3个月"), (126, "6个月"), (252, "1年"), (504, "2年")]:
    s = ((px.shift(-h) / px - 1.0) * 100.0)[sim].dropna()
    rows.append({"期限": lab, "样本天数": len(s), "均值%": s.mean(),
                 "中位%": s.median(), "胜率%": (s > 0).mean() * 100,
                 "最差%": s.min(), "最好%": s.max()})
an = pd.DataFrame(rows)
an.to_csv(os.path.join(OUT, "vix_analog.csv"), index=False, encoding="utf-8-sig")
print("\n=== 3. 相似状态（VIX分位80-95%% + 期限倒挂 + 距高点-3%%~-10%%，共 %d 天）===" % int(sim.sum()))
print(an.round(2).to_string(index=False))
# 去重成独立事件
idx = px.index[sim.fillna(False).values]
ev = []
prev = None
for d in idx:
    if prev is None or (d - prev).days > 20:
        ev.append(d)
    prev = d
print("\n独立事件起始日（间隔>20日，共 %d 次）：" % len(ev))
print(", ".join(str(d.date()) for d in ev))

# ---------- 4) 规则手册 ----------
rows = []

def rule(条件, 动作, 依据, 当前):
    rows.append({"层级": "", "条件": 条件, "动作": 动作, "依据": 依据, "当前是否触发": 当前})

vp_now_pct = vp_now * 100
rows = [
    {"层级": "买点①极端恐慌", "条件": "VIX ≥ 40 或 VIX 分位 ≥ 95% 或 VIX > 20日均线×1.5",
     "动作": "把仓位加到满格（分批 2-3 日内完成）",
     "依据": "VIX≥40 后 12M +25.03%/胜率 87.9%/超额 +14.5pp；分位>95% 后 +19.70%/75.4%/超额 +9.2pp",
     "当前是否触发": "否（VIX 25.64，分位 86.8%，/20MA=1.36）"},
    {"层级": "买点②恐慌见顶确认", "条件": "VIX 自 63 日高点回落 ≥40% 且仍 >25",
     "动作": "确认后买入并持有 12 个月（不做其他判断）",
     "依据": "31 次样本，12M +23.58%/胜率 96.8%，126 日 +15.75%/93.6%",
     "当前是否触发": "否（VIX 63日高点 %.2f，仅回落 %.1f%%）" % (vix.rolling(63).max().iloc[-1], (vix.iloc[-1] / vix.rolling(63).max().iloc[-1] - 1) * 100)},
    {"层级": "买点③期限倒挂", "条件": "VIX/VIX3M-1 > +10%",
     "动作": "只加不追：先建 1/3 仓，1 个月后视是否止跌再补",
     "依据": "1M −1.48%（胜率仅 58.7%，短期更痛），但 12M +15.03%/胜率 74.4%/超额 +4.5pp",
     "当前是否触发": "是（+4.23%，未达 +10% 阈值 → 观察级）"},
    {"层级": "卖点①中间地带", "条件": "VIX 处于 20-25 且跌破 200 日线",
     "动作": "把仓位降到 50% 以下——这是全样本最差的组合",
     "依据": "20-25 区 12M 仅 +4.38%/胜率 64.4%/盈亏比 1.87；是 U 型曲线的最低点",
     "当前是否触发": "部分是（VIX 25.64 刚出 20-25 区；但 SPX 仍在 200 日线上 +0.71%）"},
    {"层级": "卖点②自满不等于卖点", "条件": "VIX < 13 或创 1 年新低",
     "动作": "不加仓，但也不清仓；只收紧止损",
     "依据": "VIX<13 后 12M +12.00%/胜率 89.6%（比全样本 79.5% 还高），只是超额仅 +1.5pp",
     "当前是否触发": "否"},
    {"层级": "卖点③深 contango", "条件": "VIX/VIX3M-1 < −20%",
     "动作": "减到半仓（防守，不是清仓）",
     "依据": "12M +8.73%（低于基准 10.49%），超额 −1.76pp；但胜率仍有 76.8%",
     "当前是否触发": "否"},
    {"层级": "仓位刻度", "条件": "不预测方向，只调仓位",
     "动作": "VIX<13→0.95；13-20→0.80；20-25→0.45；25-30→0.80；30-40→0.95；>40→1.00",
     "依据": "按实测 U 型设计的阶梯，策略回测见 vix_ushape_strat.csv",
     "当前是否触发": "VIX 25.64 → 建议仓位 0.80"},
]
rb = pd.DataFrame(rows)
rb.to_csv(os.path.join(OUT, "vix_rulebook.csv"), index=False, encoding="utf-8-sig")
print("\n=== 4. 规则手册 ===")
for _, r in rb.iterrows():
    print("[%s] %s" % (r["层级"], r["条件"]))
    print("    动作: %s" % r["动作"])
    print("    依据: %s" % r["依据"])
    print("    当前: %s" % r["当前是否触发"])
    print()
print("saved: vix_ushape / vix_ushape_strat / vix_analog / vix_rulebook")
