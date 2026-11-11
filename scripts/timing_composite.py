# -*- coding: utf-8 -*-
"""位置温度计 v2：统一方向（0=极冷/便宜，100=极热/贵/过热），并重做分位分层。

方向约定（全部换算成"越高=位置越高"）：
  估值热  = mean(CAPE 10年分位, PE 10年分位)
  趋势热  = mean(200日线偏离分位, RSI 分位)
  情绪热  = mean(1 - VIX 分位, 1 - VIX期限倒挂分位)     低波动/低恐慌 = 自满
  信用热  = mean(信用资产动量分位, 等权/市值宽度分位)      信用与宽度同步走强 = 风险偏好高
  宏观热  = mean(10Y 利率分位, 1 - 期限利差分位)           利率高 + 曲线平 = 晚周期
"""
import os
import numpy as np
import pandas as pd

BASE = r"E:\workspace\new"
PROC = os.path.join(BASE, "data", "processed"); OUT = os.path.join(BASE, "data", "output")

def roll_pct(s, win=2520, minp=1260):
    return s.rolling(win, min_periods=minp).apply(lambda a: (a[-1] > a[:-1]).mean(), raw=True)

panel = pd.read_csv(os.path.join(PROC, "timing_panel.csv"), index_col=0, parse_dates=True)
p = panel.copy()

p["q_cape"] = roll_pct(p["cape"].astype(float))
p["q_pe"]   = roll_pct(p["pe"].astype(float))
p["q_ma200"]= roll_pct(p["ma200_dev"].astype(float))
p["q_rsi"]  = roll_pct(p["rsi14"].astype(float))
p["q_vix"]  = roll_pct(p["VIX"].astype(float))
p["q_vts"]  = roll_pct(p["vix_ts"].astype(float))
p["q_credit"] = roll_pct(p["credit_mom63"].astype(float))
p["q_breadth"]= roll_pct(p["breadth_mom63"].astype(float))
p["q_tnx"]  = roll_pct(p["TNX"].astype(float))
p["q_curve"]= roll_pct(p["curve"].astype(float))

comp = pd.DataFrame(index=p.index)
comp["估值热"] = ((p["q_cape"] + p["q_pe"]) / 2 * 100)
comp["趋势热"] = ((p["q_ma200"] + p["q_rsi"]) / 2 * 100)
comp["情绪热"] = (((1 - p["q_vix"]) + (1 - p["q_vts"])) / 2 * 100)
comp["信用热"] = ((p["q_credit"] + p["q_breadth"]) / 2 * 100)
comp["宏观热"] = ((p["q_tnx"] + (1 - p["q_curve"])) / 2 * 100)
comp["综合"] = comp[["估值热","趋势热","情绪热","信用热","宏观热"]].mean(axis=1)
comp = comp.dropna(how="all")

comp.to_csv(os.path.join(PROC, "timing_composite.csv"), encoding="utf-8")
p.to_csv(os.path.join(PROC, "timing_panel.csv"), encoding="utf-8")

px = p["SPX"].astype(float)
d = comp.loc["1994-05-05":]
rows = []
for lab, n in [("1年",252),("3年",756),("5年",1260)]:
    f = px.shift(-n)/px - 1
    for col in ["估值热","趋势热","情绪热","信用热","宏观热","综合"]:
        s = d[col]; m = s.notna() & f.notna()
        sub = pd.DataFrame({"s": s[m], "f": f[m]})
        if len(sub) < 500: continue
        sub["q"] = pd.qcut(sub["s"], 5, labels=False, duplicates="drop")
        g = sub.groupby("q")["f"].mean()*100
        idx = np.arange(0, len(sub), n)
        ic = float(pd.Series(sub["s"].values[idx]).rank().corr(pd.Series(sub["f"].values[idx]).rank()))
        rows.append({"期限": lab, "分项": col, "IC": ic,
                     "Q1冷%": g.get(0), "Q2%": g.get(1), "Q3%": g.get(2), "Q4%": g.get(3), "Q5热%": g.get(4),
                     "Q5-Q1": (g.get(4)-g.get(0)) if 0 in g and 4 in g else np.nan, "样本": len(sub)})
r = pd.DataFrame(rows)
r.to_csv(os.path.join(OUT, "timing_subscore.csv"), index=False, encoding="utf-8")
pd.set_option("display.width", 220)
print("=== 分项热度的统一方向检验（Q1=最冷/最便宜，Q5=最热/最贵）===")
print(r.round(2).to_string(index=False))

q1 = d["综合"].dropna()
print("\n当前综合温度 = %.1f，1994 以来分位 %.1f%%" % (q1.iloc[-1], (q1 < q1.iloc[-1]).mean()*100))
print("当前分项：", d[["估值热","趋势热","情绪热","信用热","宏观热"]].iloc[-1].round(1).to_dict())

# 五分层（综合）
rows2 = []
for lab, n in [("1年",252),("3年",756),("5年",1260)]:
    f = px.shift(-n)/px - 1
    s = d["综合"]; m = s.notna() & f.notna()
    sub = pd.DataFrame({"s": s[m], "f": f[m]})
    sub["q"] = pd.qcut(sub["s"], 5, labels=["Q1最冷","Q2","Q3","Q4","Q5最热"])
    for qq, g in sub.groupby("q", observed=True):
        rows2.append({"期限": lab, "分层": str(qq), "样本日": len(g),
                      "均值%": g["f"].mean()*100, "中位%": g["f"].median()*100, "胜率%": (g["f"]>0).mean()*100})
fq = pd.DataFrame(rows2)
fq.to_csv(os.path.join(OUT, "timing_composite_quintile.csv"), index=False, encoding="utf-8")
print("\n=== 综合温度 五分层 ===")
print(fq.round(2).to_string(index=False))
