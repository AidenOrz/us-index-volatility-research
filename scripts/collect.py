# -*- coding: utf-8 -*-
"""汇总报告所需的全部关键数字，输出 JSON 供撰写使用。"""
import os, json
import numpy as np, pandas as pd
RAW = r"E:\workspace\new\data\raw"; PROC = r"E:\workspace\new\data\processed"; OUT = r"E:\workspace\new\data\output"
ORDER = ["SPX","DJI","IXIC","NDX","RUT","SOX"]
CN = {"SPX":"标普500","DJI":"道琼斯工业","IXIC":"纳斯达克综合","NDX":"纳斯达克100","RUT":"罗素2000","SOX":"费城半导体"}

d = {}
m = pd.read_csv(os.path.join(OUT,"metrics_main.csv"), index_col=0)
def conv(row):
    out = {}
    for c, v in row.items():
        if isinstance(v, str):
            out[c] = v
        else:
            out[c] = None if (v is None or pd.isna(v)) else round(float(v), 6)
    return out

d["main"] = {k: conv(m.loc[k]) for k in ORDER}
mf = pd.read_csv(os.path.join(OUT,"metrics_full.csv"), index_col=0)
d["full"] = {k: conv(mf.loc[k]) for k in ORDER}
ph = pd.read_csv(os.path.join(OUT,"phases.csv"))
d["phases"] = ph.to_dict(orient="records")
d["annual"] = pd.read_csv(os.path.join(OUT,"annual_returns.csv"), index_col=0).round(2).to_dict(orient="index")
d["sector"] = pd.read_csv(os.path.join(OUT,"sector_weights.csv"), index_col=0).round(2).to_dict(orient="index")
d["conc"] = pd.read_csv(os.path.join(OUT,"concentration.csv"), index_col=0).round(2).to_dict(orient="index")
d["mcap"] = pd.read_csv(os.path.join(OUT,"market_cap.csv")).to_dict(orient="records")
d["capture"] = pd.read_csv(os.path.join(OUT,"capture_beta.csv"), index_col=0).round(4).to_dict(orient="index")
d["corr"] = pd.read_csv(os.path.join(OUT,"corr_daily.csv"), index_col=0).round(3).to_dict(orient="index")
d["style"] = pd.read_csv(os.path.join(OUT,"style_corr.csv"), index_col=0).round(3).to_dict(orient="index")
d["dd"] = pd.read_csv(os.path.join(OUT,"drawdown_episodes.csv")).to_dict(orient="records")
with open(os.path.join(OUT, "report_data.json"), "w", encoding="utf-8") as f:
    json.dump(d, f, ensure_ascii=False, indent=1)
print("keys:", list(d.keys()))
print("main keys:", list(d["main"]["SPX"].keys()))
