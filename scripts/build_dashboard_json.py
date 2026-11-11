# -*- coding: utf-8 -*-
"""Build dashboard.json for the Flutter volatility dashboard app."""
import json, os, sys
import pandas as pd
import numpy as np

sys.stdout.reconfigure(encoding="utf-8")

ROOT = r"E:\workspace\new"
RAW = os.path.join(ROOT, "data", "raw")
CBOE = os.path.join(RAW, "cboe_vol")
OUTD = os.path.join(ROOT, "data", "output")
PROC = os.path.join(ROOT, "data", "processed")
APP = os.path.join(ROOT, "flutter_app")

def fl(x, nd=2):
    if x is None: return None
    try:
        v = float(x)
    except Exception:
        return None
    if v != v or v in (float("inf"), float("-inf")):
        return None
    return round(v, nd)

def read_cboe(ticker):
    p = os.path.join(CBOE, ticker + "_History.csv")
    d = pd.read_csv(p)
    d.columns = [c.strip().upper() for c in d.columns]
    col = "CLOSE" if "CLOSE" in d.columns else d.columns[-1]
    d["DATE"] = pd.to_datetime(d["DATE"], format="%m/%d/%Y")
    s = d.set_index("DATE")[col].astype(float).sort_index()
    return s

# ---- 1. 波动率族当前值 ----
FAMILY = [
    ("VIX",    "VIX",         "标普500 30日隐含波动率", "主指标"),
    ("VIX9D",  "VIX9D",       "标普500 9日隐含波动率",  "短端"),
    ("VIX3M",  "VIX3M",       "标普500 3月隐含波动率",  "中端"),
    ("VIX6M",  "VIX6M",       "标普500 6月隐含波动率",  "长端"),
    ("VVIX",   "VVIX",        "波动率的波动率",         "二阶"),
    ("SKEW",   "SKEW",        "尾部风险偏度",           "尾部"),
    ("VXN",    "VXN",         "纳斯达克100 波动率",     "分市场"),
    ("RVX",    "RVX",         "罗素2000 波动率",        "分市场"),
]

series = {}
for t, _, _, _ in FAMILY:
    try:
        series[t] = read_cboe(t)
    except Exception as e:
        print("MISS", t, e)

prices = pd.read_csv(os.path.join(PROC, "prices_close.csv"))
prices["date"] = pd.to_datetime(prices.iloc[:, 0])
prices = prices.set_index("date").drop(columns=[prices.columns[0]])

def rolling_pct(s, win=2520, minp=1260):
    return s.rolling(win, min_periods=minp).apply(lambda w: (w <= w[-1]).mean() * 100.0, raw=True)

family_now = []
for t, name, desc, kind in FAMILY:
    if t not in series: continue
    s = series[t]
    last = s.index[-1]
    v = float(s.iloc[-1])
    pct = rolling_pct(s)
    p = pct.iloc[-1]
    ma20 = s.rolling(20).mean().iloc[-1]
    hi63 = s.rolling(63).max().iloc[-1]
    chg1 = (v / s.iloc[-2] - 1.0) * 100.0
    family_now.append({
        "ticker": t, "name": name, "desc": desc, "kind": kind,
        "value": fl(v), "date": last.strftime("%Y-%m-%d"),
        "pct10y": fl(p, 1), "ma20": fl(ma20), "vsMa20": fl(v / ma20 - 1.0, 4) if ma20 else None,
        "hi63": fl(hi63), "fromHi63": fl((v / hi63 - 1.0) * 100.0, 2) if hi63 else None,
        "chg1d": fl(chg1, 2),
        "spark": [fl(x) for x in s.iloc[-120:].tolist()],
    })

print("family:", len(family_now))

# ---- 2. 期限结构 ----
vix = series["VIX"]; v9 = series.get("VIX9D"); v3 = series.get("VIX3M"); v6 = series.get("VIX6M")
term = {}
term_series = {}
if v9 is not None:
    term_series["short"] = (vix / v9 - 1.0) * 100.0
if v3 is not None:
    term_series["mid"] = (v3 / vix - 1.0) * 100.0
if v6 is not None and v3 is not None:
    term_series["long"] = (v6 / v3 - 1.0) * 100.0
if v6 is not None and v9 is not None:
    term_series["total"] = (v6 / v9 - 1.0) * 100.0

term_now = []
LABELS = {"short": "短端 VIX/VIX9D", "mid": "中端 VIX3M/VIX", "long": "长端 VIX6M/VIX3M", "total": "全曲线 VIX6M/VIX9D"}
for k in ["short", "mid", "long", "total"]:
    if k not in term_series: continue
    s = term_series[k].dropna()
    if len(s) < 300: continue
    pct = rolling_pct(s)
    term_now.append({
        "key": k, "label": LABELS[k],
        "value": fl(s.iloc[-1], 2), "pct10y": fl(pct.iloc[-1], 1),
        "date": s.index[-1].strftime("%Y-%m-%d"),
        "spark": [fl(x, 2) for x in s.iloc[-120:].tolist()],
    })

# 曲线快照
curve = []
for t, lbl, nd in [("VIX9D", "9天", 9), ("VIX", "30天", 30), ("VIX3M", "3个月", 91), ("VIX6M", "6个月", 182)]:
    if t in series:
        curve.append({"tenor": lbl, "value": fl(series[t].iloc[-1]), "days": nd})
print("term:", len(term_now), "curve:", len(curve))

# ---- 3. VIX 分档（U 型）----
ladder = pd.read_csv(os.path.join(OUTD, "vix_ladder.csv"))
ladder_rows = []
for _, r in ladder.iterrows():
    ladder_rows.append({
        "band": str(r["档位"]).strip(),
        "days": int(r["天数"]),
        "share": fl(r["占比%"], 1),
        "r1m": fl(r["1M均值%"], 2), "w1m": fl(r["1M胜率%"], 1),
        "r12m": fl(r["12M均值%"], 2), "w12m": fl(r["12M胜率%"], 1),
        "rr": fl(r["盈亏比"], 2),
        "pos": fl(r["建议仓位%"], 0),
        "note": str(r["说明"]).strip(),
    })

cur_vix = float(series["VIX"].iloc[-1])
cur_band = None
for r in ladder_rows:
    b = r["band"]
    if b == "VIX < 13" and cur_vix < 13: cur_band = b
    elif b == "13 ~ 20" and 13 <= cur_vix < 20: cur_band = b
    elif b == "20 ~ 25" and 20 <= cur_vix < 25: cur_band = b
    elif b == "25 ~ 30" and 25 <= cur_vix < 30: cur_band = b
    elif b == "30 ~ 40" and 30 <= cur_vix < 40: cur_band = b
    elif b == "VIX > 40" and cur_vix >= 40: cur_band = b

# ---- 4. 斜率分层 ----
sl = pd.read_csv(os.path.join(OUTD, "vix_term_slopes.csv"))
slope_rows = []
for _, r in sl.iterrows():
    slope_rows.append({
        "key": str(r["斜率"]), "pct": str(r["分位"]), "days": int(r["天数"]),
        "median": fl(r["中位斜率%"], 2),
        "r1m": fl(r["1M均值%"], 2), "w1m": fl(r["1M胜率%"], 1),
        "r3m": fl(r["3M均值%"], 2),
        "r12m": fl(r["12M均值%"], 2), "w12m": fl(r["12M胜率%"], 1),
    })

# ---- 5. VVIX / SKEW 分层 ----
sk = pd.read_csv(os.path.join(OUTD, "skew_vvix_stat.csv"))
vvix_rows, skew_rows = [], []
for _, r in sk.iterrows():
    ind = str(r["指标"])
    row = {
        "group": str(r["分组"]), "days": int(r["天数"]),
        "r1m": fl(r["1M均值%"], 2), "w1m": fl(r["1M胜率%"], 1),
        "r3m": fl(r["3M均值%"], 2),
        "r12m": fl(r["12M均值%"], 2), "w12m": fl(r["12M胜率%"], 1),
        "d21vix": fl(r["未来21日VIX变化"], 2),
    }
    if ind == "VVIX": vvix_rows.append(row)
    elif ind == "SKEW": skew_rows.append(row)

# ---- 6. 规则书 ----
rb = pd.read_csv(os.path.join(OUTD, "vix_rulebook.csv"))
rules = []
for _, r in rb.iterrows():
    rules.append({
        "level": str(r["层级"]).strip(),
        "cond": str(r["条件"]).strip(),
        "action": str(r["动作"]).strip(),
        "basis": str(r["依据"]).strip(),
        "triggered": str(r["当前是否触发"]).strip(),
    })

# ---- 7. COT ----
cot = pd.read_csv(os.path.join(OUTD, "cot_tff.csv"))
cot_last = cot.iloc[-1]
cot_now = {
    "reportDate": str(cot_last["报告日"]),
    "alignDate": str(cot_last["交易对齐日"]),
    "total": int(cot_last["总持仓"]),
    "levLong": int(cot_last["杠杆基金多头"]),
    "levShort": int(cot_last["杠杆基金空头"]),
    "levNet": int(cot_last["杠杆基金净持仓"]),
    "levNetPct": fl(cot_last["杠杆基金净持仓占持仓%"], 2),
    "crowdPct": fl(cot_last["杠杆基金空头拥挤度分位%"], 1),
    "amNet": int(cot_last["资管净持仓"]),
    "amNetPct": fl(cot_last["资管净持仓占持仓%"], 2),
    "dealerNet": int(cot_last["交易商净持仓"]),
    "dealerNetPct": fl(cot_last["交易商净持仓占持仓%"], 2),
    "vixClose": fl(cot_last["VIX收盘"], 2),
    "spxClose": fl(cot_last["SPX收盘"], 2),
    "hist": [{"d": str(r["报告日"]), "lev": fl(r["杠杆基金净持仓占持仓%"], 2),
              "am": fl(r["资管净持仓占持仓%"], 2), "dl": fl(r["交易商净持仓占持仓%"], 2)}
             for _, r in cot.iloc[-156:].iterrows()],
}
print("cot:", cot_now["reportDate"], cot_now["crowdPct"])

# ---- 8. 指数现价 ----
idx_now = []
MKT = [("SPX", "标普500"), ("DJI", "道琼斯"), ("IXIC", "纳斯达克综指"), ("NDX", "纳斯达克100"), ("RUT", "罗素2000"), ("SOX", "费城半导体")]
spx = prices["SPX"].dropna()
for tk, nm in MKT:
    if tk not in prices.columns: continue
    s = prices[tk].dropna()
    v = float(s.iloc[-1])
    ma200 = s.rolling(200).mean().iloc[-1]
    hi52 = s.rolling(252).max().iloc[-1]
    chg = (v / s.iloc[-2] - 1.0) * 100.0
    ytd_base = s[s.index.year < s.index[-1].year]
    ytd = (v / ytd_base.iloc[-1] - 1.0) * 100.0 if len(ytd_base) else None
    idx_now.append({
        "ticker": tk, "name": nm, "value": fl(v),
        "chg1d": fl(chg, 2),
        "vsMa200": fl((v / ma200 - 1.0) * 100.0, 2) if ma200 == ma200 else None,
        "fromHi52": fl((v / hi52 - 1.0) * 100.0, 2) if hi52 == hi52 else None,
        "ytd": fl(ytd, 2),
        "spark": [fl(x) for x in s.iloc[-120:].tolist()],
    })

# ---- 9. 买卖点判定 ----
nowvix = float(series["VIX"].iloc[-1])
nowpct = float(rolling_pct(series["VIX"]).iloc[-1])
ma20v = float(series["VIX"].rolling(20).mean().iloc[-1])
hi63v = float(series["VIX"].rolling(63).max().iloc[-1])
mid_slope = term_series["mid"].iloc[-1] if "mid" in term_series else None
spx_v = float(spx.iloc[-1]); spx_ma200 = float(spx.rolling(200).mean().iloc[-1])
spx_above = bool(spx_v > spx_ma200)

def grade(cond):
    return "触发" if cond else "未触发"

buy1 = bool(nowvix >= 40 or nowpct >= 95 or nowvix > ma20v * 1.5)
buy2 = bool((nowvix / hi63v - 1.0) <= -0.40 and nowvix > 25)
buy3 = bool(mid_slope is not None and mid_slope > 10)
sell1 = bool((20 <= nowvix < 25) and (not spx_above))
sell2 = bool(nowvix < 13)
sell3 = bool(mid_slope is not None and mid_slope < -20)

suggest = 100
for r in ladder_rows:
    if r["band"] == cur_band:
        suggest = int(r["pos"])

signals = [
    {"id": "buy1", "type": "buy", "name": "买点① 极端恐慌",
     "cond": "VIX ≥ 40 或 分位 ≥ 95% 或 VIX > 20日均线×1.5",
     "state": buy1, "detail": f"VIX {nowvix:.2f}，分位 {nowpct:.1f}%，/20MA = {nowvix/ma20v:.2f}",
     "action": "分批 2-3 日内加到满仓"},
    {"id": "buy2", "type": "buy", "name": "买点② 恐慌见顶确认",
     "cond": "VIX 自 63 日高点回落 ≥40% 且仍 >25",
     "state": buy2, "detail": f"63日高点 {hi63v:.2f}，当前回落 {(nowvix/hi63v-1)*100:.1f}%",
     "action": "确认后买入并持有 12 个月"},
    {"id": "buy3", "type": "buy", "name": "买点③ 期限倒挂",
     "cond": "VIX/VIX3M−1 > +10%",
     "state": buy3, "detail": f"当前 {mid_slope:+.2f}%" if mid_slope is not None else "数据缺失",
     "action": "先建 1/3 仓，1 个月后视止跌再补"},
    {"id": "sell1", "type": "sell", "name": "卖点① 中间地带",
     "cond": "VIX 20–25 且跌破 200 日线",
     "state": sell1, "detail": f"VIX {nowvix:.2f}，SPX {'在' if spx_above else '跌破'} 200 日线上方 {abs((spx_v/spx_ma200-1)*100):.2f}%",
     "action": "仓位降到 50% 以下"},
    {"id": "sell2", "type": "sell", "name": "卖点② 自满不是卖点",
     "cond": "VIX < 13 或创 1 年新低",
     "state": sell2, "detail": f"VIX {nowvix:.2f}（<13 后 12M 仍有 +12.00%，只是超额仅 +1.5pp）",
     "action": "不加仓、不清仓，只收紧止损"},
    {"id": "sell3", "type": "sell", "name": "卖点③ 深 contango",
     "cond": "VIX/VIX3M−1 < −20%",
     "state": sell3, "detail": f"当前 {mid_slope:+.2f}%" if mid_slope is not None else "数据缺失",
     "action": "减半仓（曲线过度自满）"},
]

# 阶段模式
from collections import Counter
modes = []
if buy1 or buy2: modes.append("恐慌")
if sell3 or (mid_slope is not None and mid_slope < -15): modes.append("自满")
if not modes: modes.append("常态")
mode = modes[0]

regime_desc = {
    "恐慌": "波动率处于极端区，历史统计上未来一年收益最好。这是加仓窗口，不是逃跑窗口。",
    "自满": "期限结构深度陡峭，隐含波动率被压得过低。历史上这个位置未来一年收益最差。",
    "常态": "波动率处于中间地带，没有触发任何极端信号。按 VIX 分档持有基准仓位即可。",
}[mode]

# ---- 9b. 今日值得注意 ----
watch = []
vv = series.get("VVIX")
if vv is not None:
    vvv = float(vv.iloc[-1])
    if vvv < 80:
        watch.append({"sev": "high", "tag": "VVIX 极静",
                      "text": f"VVIX {vvv:.2f} 处于极静区。历史上 VVIX<80 的 933 天里，未来 12 个月只有 +3.71%、胜率 71.1%，是所有指标里最差的一组。"})
    elif vvv > 130:
        watch.append({"sev": "high", "tag": "VVIX 极动",
                      "text": f"VVIX {vvv:.2f} 处于极动区。历史上 VVIX>130 后未来 21 日 VIX 平均下跌 10.67 点、1 个月 SPX +5.01%（胜率 83.5%）。"})

if cur_band == "20 ~ 25":
    watch.append({"sev": "high", "tag": "最差档位",
                  "text": f"VIX 落在 20-25 中间地带，这是 U 型曲线的最低点：12M 仅 +4.38%、胜率 64.4%、盈亏比 1.87。历史上只有跌破 200 日线时才真正危险。"})

if not spx_above:
    watch.append({"sev": "high", "tag": "跌破年线",
                  "text": f"标普500 跌破 200 日线 {abs((spx_v/spx_ma200-1)*100):.2f}%。若同时 VIX 在 20-25，这是全样本唯一负收益的格子（−6.54%/胜率 40.1%）。"})

if "mid" in term_series:
    mp = float(rolling_pct(term_series["mid"]).iloc[-1])
    if mp > 90:
        watch.append({"sev": "med", "tag": "曲线过陡",
                      "text": f"VIX3M/VIX 斜率处于 {mp:.0f}% 分位（过陡）。历史上这个位置未来 12 个月只有 +8.38%，比最低分位组低 10.6 个百分点。"})
    elif mp < 10:
        watch.append({"sev": "good", "tag": "曲线低位",
                      "text": f"VIX3M/VIX 斜率处于 {mp:.0f}% 分位（偏平）。历史上这个位置未来 12 个月 +18.94%、胜率 91.9%，是四档里最好的一组。"})

if cur_band == "VIX < 13" or nowvix < 13:
    watch.append({"sev": "med", "tag": "自满区",
                  "text": f"VIX {nowvix:.2f} 低于 13。注意：这不是卖点 —— 历史上 VIX<13 后 12 个月仍有 +12.00%、胜率 89.6%。只是超额降到 +1.5pp，不加仓即可。"})

crowd = float(cot_last["杠杆基金空头拥挤度分位%"])
if crowd > 90:
    watch.append({"sev": "info", "tag": "空头拥挤",
                  "text": f"杠杆基金 VIX 期货空头拥挤度 {crowd:.0f}% 分位。但控制当期 VIX 后 t 值仅 0.15，超额来自 VIX 均值回归而非持仓 —— 仅作描述，不作信号。"})

cur_row = None
for r in ladder_rows:
    if r["band"] == cur_band:
        cur_row = r

if cur_row is not None:
    watch.append({"sev": "info", "tag": "当前档统计",
                  "text": f"VIX 落在 {cur_band} 档。历史上这个档位共 {cur_row['days']} 天，未来 12 个月均值 {cur_row['r12m']:+.2f}%、胜率 {cur_row['w12m']:.1f}%、盈亏比 {cur_row['rr']:.2f}。"})

if not watch:
    watch.append({"sev": "good", "tag": "无极端信号",
                  "text": "六条买卖点全部未触发。波动率处于中间地带，按分档仓位持有即可，不需要额外动作。"})

# 触发距离：最接近触发的那条规则，给出还差多少
best = None
for s in signals:
    if s["state"]:
        continue
    cand = None
    if s["id"] == "buy1":
        if nowvix < 40:
            gaps = [(40 - nowvix) / max(nowvix, 1.0) * 100, (95 - nowpct)]
            g = min(gaps)
            cand = (g, f"距离买点①还差：VIX 再涨 {40-nowvix:.1f} 点到 40，或分位升到 95%（当前 {nowpct:.1f}%，差 {95-nowpct:.1f}pp）。")
    elif s["id"] == "buy2":
        need_vix = hi63v * 0.60
        if nowvix > 25 and nowvix > need_vix:
            cand = ((nowvix - need_vix) / nowvix * 100,
                    f"买点②需要 VIX 回落到 {need_vix:.2f} 且仍在 25 以上（当前 {nowvix:.2f}，还差 {nowvix-need_vix:.2f} 点）。")
    elif s["id"] == "sell3":
        if mid_slope is not None and mid_slope > -20:
            cand = (abs(mid_slope + 20),
                    f"卖点③需要 VIX/VIX3M−1 跌到 −20% 以下（当前 {mid_slope:+.2f}%，还差 {abs(mid_slope+20):.2f}pp）。")
    elif s["id"] == "sell1":
        if nowvix >= 20 and nowvix < 25 and spx_above:
            cand = ((spx_v / spx_ma200 - 1.0) * 100,
                    f"卖点①条件已满足一半（VIX {nowvix:.2f} 在 20-25），只差标普500 跌破 200 日线（当前还在上方 {(spx_v/spx_ma200-1)*100:.2f}%）。")
    if cand is not None and (best is None or cand[0] < best[0]):
        best = cand

if best is not None:
    watch.append({"sev": "info", "tag": "触发距离", "text": best[1]})

# 期限结构方向（常驻）
if "mid" in term_series:
    mp_v = float(term_series["mid"].iloc[-1])
    if mp_v > 0:
        watch.append({"sev": "info", "tag": "期限倒挂",
                      "text": f"VIX/VIX3M−1 = {mp_v:+.2f}%，曲线倒挂 —— 市场对眼前的担忧高于三个月后。倒挂本身不构成买点，需超过 +10% 才算买点③。"})
    elif mp_v < -15:
        watch.append({"sev": "med", "tag": "深度 contango",
                      "text": f"VIX/VIX3M−1 = {mp_v:+.2f}%，陡峭 contango。做空波动率 carry 收益丰厚，但卖点③（<−20%）已在附近。"})
    else:
        watch.append({"sev": "good", "tag": "正常 contango",
                      "text": f"VIX/VIX3M−1 = {mp_v:+.2f}%，期限结构处于正常陡度。近月低于远月，市场没有为眼前的风险额外定价。"})

# VIX 与 VVIX 的相对位置（常驻）
if vv is not None and vix is not None:
    v_now = float(vix.iloc[-1]); vv_now = float(vv.iloc[-1])
    vv_pct = float(rolling_pct(vv).iloc[-1])
    v_pct = float(rolling_pct(vix).iloc[-1])
    if vv_pct < v_pct - 15:
        watch.append({"sev": "med", "tag": "二阶背离",
                      "text": f"VVIX 分位 {vv_pct:.0f}% 明显低于 VIX 分位 {v_pct:.0f}%。说明市场在为现货波动定价，但没人押注波动率本身会再放大 —— 通常出现在冲击的中后段。"})
    elif vv_pct > v_pct + 15:
        watch.append({"sev": "med", "tag": "二阶领先",
                      "text": f"VVIX 分位 {vv_pct:.0f}% 明显高于 VIX 分位 {v_pct:.0f}%。波动率的波动率先起来，历史上这往往是 VIX 继续上行的前兆。"})

# 估值（常驻，来自已有 CAPE 分位）
try:
    cape = pd.read_csv(os.path.join(PROC, "val_cape.csv"))
    cape.columns = [c.strip() for c in cape.columns]
    ccol = [c for c in cape.columns if c.lower() in ("cape", "value")] or [cape.columns[-1]]
    cser = cape.set_index(cape.columns[0])[ccol[0]].astype(float).dropna()
    c_now = float(cser.iloc[-1])
    c_pct = float(rolling_pct(cser, 2520, 1260).iloc[-1])
    if c_pct > 90:
        watch.append({"sev": "med", "tag": "估值极贵",
                      "text": f"CAPE {c_now:.1f}，10 年分位 {c_pct:.0f}%。注意：CAPE>40 的历史样本全部来自 1999–2000 一段，n=1 个事件，不能当独立择时信号用。"})
    else:
        watch.append({"sev": "info", "tag": "估值",
                      "text": f"CAPE {c_now:.1f}，10 年分位 {c_pct:.0f}%。"})
except Exception as e:
    print("cape skip:", e)

# ---- 10. 数据位置 ----
data_meta = {
    "generatedAt": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M"),
    "lastTradeDate": str(series["VIX"].index[-1].strftime("%Y-%m-%d")),
    "vixSamples": int(len(series["VIX"])),
    "vixStart": str(series["VIX"].index[0].strftime("%Y-%m-%d")),
    "termStart": str(term_series["mid"].dropna().index[0].strftime("%Y-%m-%d")) if "mid" in term_series else None,
    "cotStart": str(cot.iloc[0]["报告日"]),
}


# ---- 11. 运行时重算所需的历史序列（供 App 每日增量更新）----
def _pack(s, n):
    s = s.dropna().iloc[-n:]
    return {
        "dates": [int(d.strftime("%Y%m%d")) for d in s.index],
        "values": [fl(v, 2) for v in s.tolist()],
    }

history = {}
for _t in ["VIX", "VIX9D", "VIX3M", "VIX6M", "VVIX", "SKEW", "VXN", "RVX"]:
    if _t in series and len(series[_t]) > 200:
        history[_t] = _pack(series[_t], 2600)
for _tk, _nm in MKT:
    if _tk in prices.columns:
        _s = prices[_tk].dropna()
        if len(_s) > 200:
            history[_tk] = _pack(_s, 400)
print("history series:", len(history),
      "points:", sum(len(v["dates"]) for v in history.values()))

payload = {
    "meta": data_meta,
    "history": history,
    "family": family_now,
    "term": term_now,
    "curve": curve,
    "ladder": {"rows": ladder_rows, "current": cur_band, "vix": fl(nowvix)},
    "slopes": slope_rows,
    "vvixSkew": {"vvix": vvix_rows, "skew": skew_rows},
    "rules": rules,
    "cot": cot_now,
    "indices": idx_now,
    "signals": signals,
    "watch": watch,
    "verdict": {
        "mode": mode,
        "desc": regime_desc,
        "suggestPos": suggest,
        "vix": fl(nowvix), "vixPct": fl(nowpct, 1),
        "band": cur_band,
        "midSlope": fl(mid_slope, 2),
        "spxAbove": spx_above,
        "spxVsMa200": fl((spx_v / spx_ma200 - 1.0) * 100.0, 2),
    },
}

os.makedirs(os.path.join(APP, "assets"), exist_ok=True)
dst = os.path.join(APP, "assets", "dashboard.json")
with open(dst, "w", encoding="utf-8") as f:
    json.dump(payload, f, ensure_ascii=False, indent=1)
print("WROTE", dst, os.path.getsize(dst), "bytes")
print("mode=", mode, "suggest=", suggest, "band=", cur_band)
