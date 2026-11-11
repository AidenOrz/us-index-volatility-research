# -*- coding: utf-8 -*-
"""VIX 类指数用于买卖点判断的实证检验。
产出（均在 data/output/）：
  vix_level_bins.csv        VIX 绝对水平分层 -> 未来收益/胜率/未来实现波动
  vix_pct_bins.csv          VIX 滚动 10 年分位分层
  vix_ts_bins.csv           VIX 期限结构(VIX/VIX3M-1) 分层
  vix_events.csv            离散信号事件检验
  vix_by_index.csv          同一信号在六个指数上的效果
  vix_strategy.csv          VIX 择时策略回测（全样本）
  vix_strategy_oos.csv      样本外(2011 起)回测
  vix_interaction.csv       VIX 分位 × CAPE 分位 交互
  vix_now.csv               当前逐项读数
"""
import os
import numpy as np
import pandas as pd

BASE = r"E:\workspace\new"
PROC = os.path.join(BASE, "data", "processed")
OUT = os.path.join(BASE, "data", "output")
COST = 0.0005
IDX = ["SPX", "DJI", "IXIC", "NDX", "RUT", "SOX"]

panel = pd.read_csv(os.path.join(PROC, "timing_panel.csv"), index_col=0, parse_dates=True)
panel = panel.loc["1994-05-05":].copy()
px = panel["SPX"].astype(float)
ret = px.pct_change()
rf = panel["rf_d"].fillna(0.0)
vix = panel["VIX"].astype(float)
vix3m = panel["VIX3M"].astype(float)
vts = panel["vix_ts"].astype(float)
vp = panel["vix_p"].astype(float)          # 0~1 小数
cape_p = panel["cape_p"].astype(float)     # 0~1 小数

HOR = {"1M": 21, "3M": 63, "6M": 126, "12M": 252}
F = {k: (px.shift(-h) / px - 1.0) * 100.0 for k, h in HOR.items()}
fwdrv = np.log(px).diff().rolling(21).std().shift(-21) * np.sqrt(252) * 100.0

# 未来 252 日内的最高/最低相对今天（衡量盈亏比）
rev = px[::-1]
fmin = rev.rolling(252, min_periods=21).min()[::-1]
fmax = rev.rolling(252, min_periods=21).max()[::-1]
fwd_dn = (fmin / px - 1.0) * 100.0
fwd_up = (fmax / px - 1.0) * 100.0


def stat_block(mask, label, note=""):
    mask = mask.reindex(px.index).fillna(False).astype(bool)
    row = {"分组": label, "天数": int(mask.sum()), "占比%": mask.mean() * 100.0,
           "VIX中位": vix[mask].median()}
    for k in HOR:
        s = F[k][mask].dropna()
        row[k + "均值%"] = s.mean() if len(s) else np.nan
        row[k + "胜率%"] = (s > 0).mean() * 100.0 if len(s) else np.nan
    s21 = F["1M"][mask].dropna()
    row["1M中位%"] = s21.median() if len(s) else np.nan
    row["未来21日实现波动%"] = fwdrv[mask].median()
    row["未来1年最大上行%"] = fwd_up[mask].median()
    row["未来1年最大下行%"] = fwd_dn[mask].median()
    u, d = row["未来1年最大上行%"], row["未来1年最大下行%"]
    row["盈亏比"] = (u / abs(d)) if (d and not np.isnan(d) and d != 0) else np.nan
    row["说明"] = note
    return row


# ========== 1) VIX 绝对水平分层 ==========
edges = [(0, 11), (11, 13), (13, 15), (15, 17.5), (17.5, 20), (20, 25), (25, 30), (30, 40), (40, 999)]
rows = []
for lo, hi in edges:
    m = (vix >= lo) & (vix < hi)
    note = "极低波动·自满区" if hi <= 13 else ("常态区" if hi <= 20 else ("警觉区" if hi <= 25 else ("恐慌区" if hi <= 40 else "极端恐慌")))
    rows.append(stat_block(m, ("%g-%g" % (lo, hi)) if hi < 999 else ">40", note))
lv = pd.DataFrame(rows)
lv.to_csv(os.path.join(OUT, "vix_level_bins.csv"), index=False, encoding="utf-8-sig")
print("=== 1. VIX 绝对水平分层（1994-05-05~2026-11-06, SPX）===")
print(lv.round(2).to_string(index=False))

# ========== 2) VIX 滚动 10 年分位分层 ==========
edges2 = [(0, 0.10), (0.10, 0.25), (0.25, 0.50), (0.50, 0.75), (0.75, 0.90), (0.90, 1.0001)]
rows = []
for lo, hi in edges2:
    m = (vp >= lo) & (vp < hi)
    rows.append(stat_block(m, "分位 %g-%g%%" % (round(lo * 100), round(min(hi, 1) * 100)), ""))
pv_ = pd.DataFrame(rows)
pv_.to_csv(os.path.join(OUT, "vix_pct_bins.csv"), index=False, encoding="utf-8-sig")
print("\n=== 2. VIX 滚动 10 年分位分层 ===")
print(pv_.round(2).to_string(index=False))

# ========== 3) 期限结构分层 ==========
edges3 = [(-9, -0.20), (-0.20, -0.10), (-0.10, -0.03), (-0.03, 0.03), (0.03, 0.10), (0.10, 9)]
rows = []
for lo, hi in edges3:
    m = (vts >= lo) & (vts < hi)
    note = "深度 contango·极度自满" if hi <= -0.20 else ("倒挂·恐慌" if lo >= 0.10 else "")
    lab = ("<%.0f%%" % (hi * 100)) if lo <= -1 else ("%g%%~%g%%" % (round(lo * 100), round(hi * 100)))
    rows.append(stat_block(m, lab, note))
ts_ = pd.DataFrame(rows)
ts_.to_csv(os.path.join(OUT, "vix_ts_bins.csv"), index=False, encoding="utf-8-sig")
print("\n=== 3. VIX 期限结构 (VIX/VIX3M-1) 分层 ===")
print(ts_.round(2).to_string(index=False))

# ========== 4) 离散事件信号 ==========
ma20v = vix.rolling(20).mean()
vix_chg1 = vix.pct_change()
spx_chg5 = px / px.shift(5) - 1

sigs = {
    "VIX 上穿 20": (vix > 20) & (vix.shift(1) <= 20),
    "VIX 上穿 25": (vix > 25) & (vix.shift(1) <= 25),
    "VIX 上穿 30": (vix > 30) & (vix.shift(1) <= 30),
    "VIX 上穿 40": (vix > 40) & (vix.shift(1) <= 40),
    "VIX 单日涨>20%": vix_chg1 > 0.20,
    "VIX>20MA×1.5 急冲": vix > ma20v * 1.5,
    "VIX>20MA×2.0 暴冲": vix > ma20v * 2.0,
    "VIX/VIX3M 倒挂>5%": vts > 0.05,
    "VIX/VIX3M 倒挂>10%": vts > 0.10,
    "VIX 分位>95%": vp > 0.95,
    "VIX 分位>90%": vp > 0.90,
    "VIX 分位<10%": vp < 0.10,
    "VIX<13 自满": vix < 13,
    "VIX<15 且跌破20MA": (vix < 15) & (vix < ma20v),
    "VIX 下穿 12": (vix < 12) & (vix.shift(1) >= 12),
    "VIX 深度contango<-20%": vts < -0.20,
    "VIX 创1年新低": vix <= vix.rolling(252).min(),
    "VIX与SPX同涨(5日)": (vix / vix.shift(5) > 1) & (spx_chg5 > 0),
}
BUY = {"VIX 上穿 20", "VIX 上穿 25", "VIX 上穿 30", "VIX 上穿 40", "VIX 单日涨>20%",
       "VIX>20MA×1.5 急冲", "VIX>20MA×2.0 暴冲", "VIX/VIX3M 倒挂>5%", "VIX/VIX3M 倒挂>10%",
       "VIX 分位>95%", "VIX 分位>90%", "VIX<15 且跌破20MA"}

base = stat_block(pd.Series(True, index=px.index), "全样本基准", "")
rows = [base]
for name, m in sigs.items():
    m = m.reindex(px.index).fillna(False)
    r = stat_block(m, name, "买入/加仓" if name in BUY else "减仓/警惕")
    r["1M相对基准pp"] = r["1M均值%"] - base["1M均值%"]
    r["12M相对基准pp"] = r["12M均值%"] - base["12M均值%"]
    # 最近一次触发
    trig = px.index[m.values]
    r["最近触发日"] = str(trig[-1].date()) if len(trig) else ""
    rows.append(r)
ev = pd.DataFrame(rows)
ev.to_csv(os.path.join(OUT, "vix_events.csv"), index=False, encoding="utf-8-sig")
print("\n=== 4. 离散信号事件检验 ===")
print(ev[["分组", "天数", "VIX中位", "1M均值%", "1M胜率%", "12M均值%", "12M胜率%",
          "1M相对基准pp", "12M相对基准pp", "未来1年最大上行%", "未来1年最大下行%", "盈亏比",
          "最近触发日", "说明"]].round(2).to_string(index=False))

# ========== 5) 同一信号在六个指数上的效果 ==========
rows = []
for name, m in sigs.items():
    m = m.reindex(px.index).fillna(False)
    if m.sum() < 30:
        continue
    r = {"信号": name, "信号日数": int(m.sum()), "方向": "买入/加仓" if name in BUY else "减仓/警惕"}
    for t in IDX:
        p2 = panel[t].astype(float)
        fr = (p2.shift(-252) / p2 - 1.0) * 100.0
        a = fr[m].dropna()
        b = fr.dropna()
        r[t + "_12M%"] = a.mean()
        r[t + "_超额pp"] = a.mean() - b.mean()
        r[t + "_胜率%"] = (a > 0).mean() * 100.0
    r["六指数超额均值pp"] = np.mean([r[t + "_超额pp"] for t in IDX])
    r["六指数同向数"] = int(sum(1 for t in IDX if r[t + "_超额pp"] > 0))
    rows.append(r)
eff = pd.DataFrame(rows).sort_values("六指数超额均值pp", ascending=False)
eff.to_csv(os.path.join(OUT, "vix_by_index.csv"), index=False, encoding="utf-8-sig")
print("\n=== 5. 信号在六指数上的 12 个月超额（pp）===")
print(eff[["信号", "方向", "信号日数"] + [t + "_超额pp" for t in IDX] +
          ["六指数超额均值pp", "六指数同向数"]].round(2).to_string(index=False))

# ========== 6) 策略回测 ==========
def bt(sig, name):
    w = sig.reindex(px.index).ffill().shift(1).fillna(0.0).clip(0, 1)
    dr = w * ret + (1 - w) * rf - w.diff().abs().fillna(0) * COST
    eq = (1 + dr).cumprod()
    yrs = len(dr) / 252.0
    ann = eq.iloc[-1] ** (1 / yrs) - 1
    mdd = (eq / eq.cummax() - 1).min()
    vol = dr.std(ddof=1) * np.sqrt(252)
    ex = dr - rf
    dn = dr[dr < 0].std(ddof=1) * np.sqrt(252)
    return {"策略": name, "累计%": (eq.iloc[-1] - 1) * 100, "年化%": ann * 100, "波动%": vol * 100,
            "夏普": (dr.mean() * 252) / (dr.std(ddof=1) * np.sqrt(252)),
            "索提诺": (ex.mean() * 252) / dn if dn else np.nan,
            "最大回撤%": mdd * 100, "卡玛": ann * 100 / abs(mdd * 100) if mdd else np.nan,
            "平均仓位%": w.mean() * 100, "年换手": w.diff().abs().fillna(0).sum() / yrs,
            "持有期占比%": (w > 0.01).mean() * 100}

one = pd.Series(1.0, index=px.index)
ma200 = px.rolling(200).mean()
trend = ((px > ma200) & (px.rolling(50).mean() > ma200)).astype(float)

def lvl_up(v):   # 恐慌加仓式（逆向）
    return 1.0 if v >= 35 else (0.90 if v >= 25 else (0.70 if v >= 18 else (0.50 if v >= 14 else 0.30)))
def lvl_dn(v):   # 自满加仓式（顺势）
    return 0.30 if v >= 35 else (0.50 if v >= 25 else (0.70 if v >= 18 else (0.90 if v >= 14 else 1.0)))

w_c = one.copy()
w_c = w_c.where(~(vix < 12), 0.40)
w_c = w_c.where(~(vix > 30), 1.00)

w_d = one.copy()
w_d = w_d.where(~(vts < -0.20).fillna(False), 0.50)
w_d = w_d.where(~(vts > 0.05).fillna(False), 1.00)

# 恐慌消退确认：VIX 63 日内曾破 30，且当前回落到 20 日均线下方才买入，持有 12 个月
fear = vix.rolling(63).max() > 30
trig = (fear & (vix < ma20v)).fillna(False)
w_e = pd.Series(0.0, index=px.index)
w_e[trig.values] = 1.0
w_e = w_e.replace(0.0, np.nan).ffill(limit=252).fillna(0.0)

w_f = trend.copy()
w_f = w_f.where(~(vix > 30).fillna(False), 1.0)
w_f = w_f.where(~((vix < 12) & (cape_p > 0.90)).fillna(False), 0.0)

w_g = one.copy()
w_g = w_g.where(~((vp > 0.90) & (vix > 25)).fillna(False), 1.0)
w_g = w_g.where(~((vp < 0.15) & (vix < 15)).fillna(False), 0.50)

strat = {
    "买入持有": one,
    "A 纯VIX分档·逆向(越恐慌越重)": vix.apply(lvl_up),
    "B 纯VIX分档·顺势(越平静越重)": vix.apply(lvl_dn),
    "C VIX阈值(<12减到4成/>30满仓)": w_c,
    "D 期限结构(倒挂满仓/深contango减半)": w_d,
    "E 恐慌消退确认后才买(持12月)": w_e,
    "F 趋势 + VIX>30加分 + VIX<12且估值高减仓": w_f,
    "G VIX分位极端才动作": w_g,
    "H 50%底仓 + 50% VIX阈值": 0.5 + 0.5 * w_c,
}
res = pd.DataFrame([bt(s, n) for n, s in strat.items()]).sort_values("夏普", ascending=False)
res.to_csv(os.path.join(OUT, "vix_strategy.csv"), index=False, encoding="utf-8-sig")
print("\n=== 6. VIX 择时策略回测（1994-05-05~2026-11-06, 单边5bp）===")
print(res.round(2).to_string(index=False))

# ========== 6b) 样本外 2011 起 ==========
m_oos = px.index >= "2011-01-01"
rows = []
for n, s in strat.items():
    w = s.reindex(px.index).ffill()[m_oos].shift(1).fillna(0.0).clip(0, 1)
    r_o, f_o = ret[m_oos], rf[m_oos]
    dr = w * r_o + (1 - w) * f_o - w.diff().abs().fillna(0) * COST
    eq = (1 + dr).cumprod()
    yrs = len(dr) / 252.0
    rows.append({"策略": n, "年化%": (eq.iloc[-1] ** (1 / yrs) - 1) * 100,
                 "波动%": dr.std(ddof=1) * np.sqrt(252) * 100,
                 "夏普": (dr.mean() * 252) / (dr.std(ddof=1) * np.sqrt(252)),
                 "最大回撤%": (eq / eq.cummax() - 1).min() * 100, "平均仓位%": w.mean() * 100})
oos = pd.DataFrame(rows).sort_values("夏普", ascending=False)
oos.to_csv(os.path.join(OUT, "vix_strategy_oos.csv"), index=False, encoding="utf-8-sig")
print("\n=== 6b. 样本外 2011-01-01 起 ===")
print(oos.round(2).to_string(index=False))

# ========== 7) VIX 分位 × CAPE 分位 交互 ==========
def cell(mask, label):
    mask = mask.reindex(px.index).fillna(False).astype(bool)
    s = F["12M"][mask].dropna()
    r = {"组合": label, "天数": int(mask.sum())}
    r["未来1年收益%"] = s.mean() if len(s) else np.nan
    r["胜率%"] = (s > 0).mean() * 100 if len(s) else np.nan
    r["未来1年最大下行%(中位)"] = fwd_dn[mask].median()
    r["未来1年最大上行%(中位)"] = fwd_up[mask].median()
    return r

rows = []
vbands = [(0.0, 0.10, "VIX<10%分位(极静)"), (0.10, 0.50, "VIX 10-50%"), (0.50, 0.90, "VIX 50-90%"), (0.90, 1.001, "VIX>90%(极恐)")]
cbands = [(0.0, 0.33, "估值<33%"), (0.33, 0.67, "估值33-67%"), (0.67, 1.001, "估值>67%")]
for vl, vh, vlab in vbands:
    for cl, ch, clab in cbands:
        m = (vp >= vl) & (vp < vh) & (cape_p >= cl) & (cape_p < ch)
        rows.append(cell(m, vlab + " × " + clab))
ia = pd.DataFrame(rows)
ia.to_csv(os.path.join(OUT, "vix_interaction.csv"), index=False, encoding="utf-8-sig")
print("\n=== 7. VIX 分位 × CAPE 分位 交互（未来 1 年）===")
print(ia.round(2).to_string(index=False))

# ========== 8) 当前读数 ==========
last = px.index[-1]
row = []
def add(项, 值, 单位, 状态):
    row.append({"项目": 项, "读数": 值, "单位": 单位, "状态": 状态})

v_now = vix.iloc[-1]; v3_now = vix3m.iloc[-1]; vts_now = vts.iloc[-1]
vp_now = vp.iloc[-1]
add("VIX 收盘", round(v_now, 2), "点", "极恐" if v_now > 40 else ("恐慌" if v_now > 30 else ("警觉" if v_now > 20 else ("常态" if v_now > 13 else "自满"))))
add("VIX 滚动10年分位", round(vp_now * 100, 1), "%", "极高分位" if vp_now > 0.90 else ("偏高" if vp_now > 0.75 else ("中性" if vp_now > 0.25 else "偏低")))
add("VIX3M", round(v3_now, 2), "点", "")
add("VIX/VIX3M-1", round(vts_now * 100, 2), "%", "倒挂(恐慌)" if vts_now > 0.03 else ("平坦" if vts_now > -0.03 else "正常 contango"))
add("VIX 20日均线", round(ma20v.iloc[-1], 2), "点", "")
add("VIX / 20日均线", round(v_now / ma20v.iloc[-1], 2), "倍", "急冲" if v_now > ma20v.iloc[-1] * 1.5 else "常态")
add("VIX 5日变化", round((vix.iloc[-1] / vix.iloc[-6] - 1) * 100, 2), "%", "")
add("SPX 距 200 日线", round(panel["ma200_dev"].iloc[-1] * 100, 2), "%", "线上" if panel["ma200_dev"].iloc[-1] > 0 else "线下")
add("SPX 距 52 周高点", round(panel["dist_high252"].iloc[-1] * 100, 2), "%", "")
add("CAPE 分位(10年)", round(cape_p.iloc[-1] * 100, 1), "%", "极贵" if cape_p.iloc[-1] > 0.90 else "偏高")
now = pd.DataFrame(row)
now.to_csv(os.path.join(OUT, "vix_now.csv"), index=False, encoding="utf-8-sig")
print("\n=== 8. 当前读数（%s）===" % last.date())
print(now.to_string(index=False))

print("\nsaved: vix_level_bins / vix_pct_bins / vix_ts_bins / vix_events / vix_by_index / vix_strategy / vix_strategy_oos / vix_interaction / vix_now")
