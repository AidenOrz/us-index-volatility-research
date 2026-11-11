# -*- coding: utf-8 -*-
"""汇总 HTML 报告所需全部数据 -> data/output/html_data.json"""
import os, json
import pandas as pd, numpy as np

BASE = r"E:\workspace\new"
OUT = os.path.join(BASE, "data", "output")
PROC = os.path.join(BASE, "data", "processed")

def rd(name, base=OUT):
    p = os.path.join(base, name)
    if not os.path.exists(p):
        return None
    return pd.read_csv(p)

D = {}
D["main"] = json.load(open(os.path.join(OUT, "report_data.json"), encoding="utf-8"))

def todict(df):
    if df is None: return None
    df = df.copy()
    for c in df.columns:
        if df[c].dtype.kind in "fi":
            df[c] = df[c].round(4)
    return json.loads(df.to_json(orient="records", force_ascii=False))

for k, f in [("final","timing_final.csv"), ("multi","timing_multi.csv"),
             ("sens","timing_sensitivity.csv"), ("oos","timing_oos.csv"),
             ("events","timing_events.csv"), ("quad","timing_quadrant.csv"),
             ("ic","timing_ic.csv"), ("sub","timing_subscore.csv"),
             ("decade","timing_by_decade.csv"), ("capebins","timing_cape_bins.csv"),
             ("composite_q","timing_composite_quintile.csv"), ("analog","timing_analogues.csv"),
             ("dash","timing_dashboard.csv"), ("horizon","timing_ic_horizon.csv"),
             ("div","timing_divergence.csv")]:
    D[k] = todict(rd(f))

comp = pd.read_csv(os.path.join(PROC, "timing_composite.csv"), index_col=0, parse_dates=True).dropna(subset=["综合"])
axesd = pd.read_csv(os.path.join(PROC, "timing_axes.csv"), index_col=0, parse_dates=True)
panel = pd.read_csv(os.path.join(PROC, "timing_panel.csv"), index_col=0, parse_dates=True)

last = comp.iloc[-1]
D["now"] = {
    "date": str(comp.index[-1].date()),
    "估值热": round(float(last["估值热"]),1), "趋势热": round(float(last["趋势热"]),1),
    "情绪热": round(float(last["情绪热"]),1), "信用热": round(float(last["信用热"]),1),
    "宏观热": round(float(last["宏观热"]),1), "综合": round(float(last["综合"]),1),
    "综合分位": round(float((comp["综合"] < last["综合"]).mean()*100),1),
    "估值轴": round(float(axesd["V"].iloc[-1]),3), "趋势轴": round(float(axesd["T"].iloc[-1]),3),
    "估值轴分位": round(float((axesd["V"] < axesd["V"].iloc[-1]).mean()*100),1),
    "趋势轴分位": round(float((axesd["T"] < axesd["T"].iloc[-1]).mean()*100),1),
    "cape": round(float(panel["cape"].dropna().iloc[-1]),2),
    "cape_pct_all": round(float((panel["cape"].dropna() < panel["cape"].dropna().iloc[-1]).mean()*100),1),
    "cape_rank": int((panel["cape"].dropna().resample("ME").last().dropna() > panel["cape"].dropna().iloc[-1]).sum()),
    "cape_months": int(len(panel["cape"].dropna().resample("ME").last().dropna())),
    "pe": round(float(panel["pe"].dropna().iloc[-1]),2),
    "dy": round(float(panel["dy"].dropna().iloc[-1]),2),
    "vix": round(float(panel["VIX"].dropna().iloc[-1]),2),
    "tnx": round(float(panel["TNX"].dropna().iloc[-1]),2),
    "curve": round(float(panel["curve"].dropna().iloc[-1]),2),
    "ma200_dev": round(float(panel["ma200_dev"].dropna().iloc[-1])*100,2),
    "dd": round(float(panel["dd"].dropna().iloc[-1])*100,2),
    "rsi": round(float(panel["rsi14"].dropna().iloc[-1]),1),
    "vix_ts": round(float(panel["vix_ts"].dropna().iloc[-1])*100,2),
}
json.dump(D, open(os.path.join(OUT, "html_data.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("html_data.json written, keys:", list(D.keys()))
print("now:", json.dumps(D["now"], ensure_ascii=False))
