# -*- coding: utf-8 -*-
"""VIX 买卖点的细化：事件后收益路径、关键区间的稳健性、恐慌见顶确认规则、分位×期限结构四象限。
产出（data/output/）：
  vix_path.csv            事件日之后 5/10/21/63/126/252 日累计收益路径
  vix_robust.csv          VIX 关键区间在各子区间是否稳健
  vix_peak.csv            恐慌见顶（VIX 回落）规则检验
  vix_quad2.csv           VIX 分位 × 期限结构 四象限
  vix_extreme.csv         VIX>40 / 分位>95% 的日期聚集与唯一事件数
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
ma20v = vix.rolling(20).mean()
vix_chg1 = vix.pct_change()

# ---------- 1) 事件后收益路径 ----------
HOR = [5, 10, 21, 63, 126, 252, 378, 504]
def path_stats(mask, label):
    mask = mask.reindex(px.index).fillna(False).astype(bool)
    r = {"事件": label, "样本数": int(mask.sum())}
    for h in HOR:
        s = ((px.shift(-h) / px - 1.0) * 100.0)[mask].dropna()
        r["%d日均值%%" % h] = s.mean() if len(s) else np.nan
        r["%d日胜率%%" % h] = (s > 0).mean() * 100.0 if len(s) else np.nan
    return r

evs = {
    "VIX 上穿 25": (vix > 25) & (vix.shift(1) <= 25),
    "VIX 上穿 30": (vix > 30) & (vix.shift(1) <= 30),
    "VIX 上穿 40": (vix > 40) & (vix.shift(1) <= 40),
    "VIX>20MA×1.5 急冲": vix > ma20v * 1.5,
    "VIX/VIX3M 倒挂>10%": vts > 0.10,
    "VIX 分位>95%": vp > 0.95,
}
rows = [path_stats(pd.Series(True, index=px.index), "全样本基准")]
for k, m in evs.items():
    rows.append(path_stats(m, k))
# 恐慌见顶确认
hi63 = vix.rolling(63).max()
drop_from_hi = vix / hi63 - 1.0
peak = (drop_from_hi < -0.25) & (drop_from_hi.shift(1) >= -0.25) & (vix > 20)
rows.append(path_stats(peak, "VIX 自63日高点回落25%+且仍>20（恐慌见顶确认）"))
peak2 = (drop_from_hi < -0.40) & (drop_from_hi.shift(1) >= -0.40) & (vix > 25)
rows.append(path_stats(peak2, "VIX 自63日高点回落40%+且仍>25（强确认）"))
pth = pd.DataFrame(rows)
pth.to_csv(os.path.join(OUT, "vix_path.csv"), index=False, encoding="utf-8-sig")
print("=== 1. 事件后收益路径（SPX，%）===")
print(pth.round(2).to_string(index=False))

# ---------- 2) 关键区间稳健性 ----------
bands = [("VIX<13", vix < 13), ("13-20", (vix >= 13) & (vix < 20)),
         ("20-25", (vix >= 20) & (vix < 25)), ("25-30", (vix >= 25) & (vix < 30)),
         ("30-40", (vix >= 30) & (vix < 40)), ("VIX>40", vix >= 40)]
subs = [("1994-2003", "1994-01-01", "2003-12-31"), ("2004-2013", "2004-01-01", "2013-12-31"),
        ("2014-2019", "2014-01-01", "2019-12-31"), ("2020-2026", "2020-01-01", "2026-12-31")]
rows = []
for lab, m in bands:
    for sl, s0, s1 in subs:
        mm = m & (px.index >= s0) & (px.index <= s1)
        s = ((px.shift(-252) / px - 1.0) * 100.0)[mm].dropna()
        rows.append({"区间": lab, "子样本": sl, "天数": int(mm.sum()),
                     "12M均值%": s.mean() if len(s) else np.nan,
                     "12M胜率%": (s > 0).mean() * 100.0 if len(s) else np.nan})
rb = pd.DataFrame(rows)
rb.to_csv(os.path.join(OUT, "vix_robust.csv"), index=False, encoding="utf-8-sig")
piv = rb.pivot(index="区间", columns="子样本", values="12M均值%").reindex([b[0] for b in bands])
print("\n=== 2. 各区间 未来12个月均值 的分年代稳健性（%）===")
print(piv.round(2).to_string())
piv2 = rb.pivot(index="区间", columns="子样本", values="天数").reindex([b[0] for b in bands])
print("\n（天数）")
print(piv2.fillna(0).astype(int).to_string())

# ---------- 3) 恐慌见顶确认作为策略 ----------
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
            "平均仓位%": w.mean() * 100, "信号次数": int((sig.reindex(px.index).fillna(0).diff() > 0).sum())}

one = pd.Series(1.0, index=px.index)
w1 = pd.Series(0.0, index=px.index); w1[peak.values] = 1.0
w1 = w1.replace(0.0, np.nan).ffill(limit=252).fillna(0.0)
w2 = pd.Series(0.0, index=px.index); w2[peak2.values] = 1.0
w2 = w2.replace(0.0, np.nan).ffill(limit=252).fillna(0.0)
# 恐慌见顶 + 趋势确认
ma200 = px.rolling(200).mean()
w3 = w1.where(px > ma200, 0.0)
rows = [bt(one, "买入持有"), bt(w1, "仅恐慌见顶买入(持12月)"), bt(w2, "强确认买入(持12月)"),
        bt(w3, "恐慌见顶+站上200日线") ]
pk = pd.DataFrame(rows)
pk.to_csv(os.path.join(OUT, "vix_peak.csv"), index=False, encoding="utf-8-sig")
print("\n=== 3. 恐慌见顶规则作为策略 ===")
print(pk.round(2).to_string(index=False))

# 列出所有恐慌见顶确认日
trig = px.index[peak.reindex(px.index).fillna(False).values]
print("\n恐慌见顶确认信号出现日（共 %d 次）：" % len(trig))
print(", ".join(str(d.date()) for d in trig))

# ---------- 4) VIX 分位 × 期限结构 四象限 ----------
vq = np.where(vp > 0.75, "VIX高", "VIX低")
tq = np.where(vts > 0.0, "倒挂", "正常")
quad = pd.Series([a + "×" + b for a, b in zip(vq, tq)], index=px.index)
quad[vp.isna() | vts.isna()] = None
rows = []
for q in ["VIX高×倒挂", "VIX高×正常", "VIX低×倒挂", "VIX低×正常"]:
    m = (quad == q)
    s = ((px.shift(-252) / px - 1.0) * 100.0)[m].dropna()
    s21 = ((px.shift(-21) / px - 1.0) * 100.0)[m].dropna()
    rows.append({"象限": q, "天数": int(m.sum()), "占比%": m.mean() * 100,
                 "1M均值%": s21.mean(), "1M胜率%": (s21 > 0).mean() * 100,
                 "12M均值%": s.mean(), "12M胜率%": (s > 0).mean() * 100,
                 "12M最差%": s.min()})
qd = pd.DataFrame(rows)
qd.to_csv(os.path.join(OUT, "vix_quad2.csv"), index=False, encoding="utf-8-sig")
print("\n=== 4. VIX 分位 × 期限结构 四象限 ===")
print(qd.round(2).to_string(index=False))

# ---------- 5) 极端读数的日期聚集 ----------
def clusters(mask, label):
    m = mask.reindex(px.index).fillna(False)
    idx = px.index[m.values]
    if len(idx) == 0:
        return {"信号": label, "天数": 0, "独立事件数(间隔>60日)": 0, "首次": "", "末次": "", "日期清单": ""}
    groups = 1
    for i in range(1, len(idx)):
        if (idx[i] - idx[i - 1]).days > 60:
            groups += 1
    txt = "; ".join(str(d.date()) for d in idx[:6]) + (" ..." if len(idx) > 6 else "")
    return {"信号": label, "天数": len(idx), "独立事件数(间隔>60日)": groups,
            "首次": str(idx[0].date()), "末次": str(idx[-1].date()), "日期清单": txt}

rows = [clusters(vix >= 40, "VIX>=40"), clusters(vix >= 50, "VIX>=50"),
        clusters(vp > 0.95, "VIX 分位>95%"), clusters(vts > 0.10, "期限倒挂>10%"),
        clusters(vix < 12, "VIX<12"), clusters(vix < 10, "VIX<10"),
        clusters(peak, "恐慌见顶确认")]
ex = pd.DataFrame(rows)
ex.to_csv(os.path.join(OUT, "vix_extreme.csv"), index=False, encoding="utf-8-sig")
print("\n=== 5. 极端读数的日期聚集（独立事件数）===")
print(ex.to_string(index=False))
print("\nsaved: vix_path / vix_robust / vix_peak / vix_quad2 / vix_extreme")
