# -*- coding: utf-8 -*-
"""把本轮数据源尽调的新增表追加进 Excel 数据册。"""
import os
import pandas as pd

BASE = r"E:\workspace\new"
OUT = os.path.join(BASE, "data", "output")
XLSX = os.path.join(BASE, "output", "美股主要指数回测数据册.xlsx")

existing = {}
if os.path.exists(XLSX):
    xl = pd.ExcelFile(XLSX)
    for nm in xl.sheet_names:
        existing[nm] = xl.parse(nm)
    print("原有工作表:", len(existing))

add = {
    "数据源_实测清单": "source_inventory",
    "数据源_三源比对": "vol_three_source",
    "数据源_TradingView": "tv_snapshot",
    "COT_Legacy持仓": "cot_positions",
    "COT_Legacy信号": "cot_signal",
    "COT_TFF持仓": "cot_tff",
    "COT_TFF信号": "cot_tff_signal",
    "COT_与VIX关系": "cot_vs_vix",
    "期限_四斜率分档": "vix_term_slopes",
    "VVIX与SKEW": "skew_vvix_stat",
    "vixcentral抽检": "vc_curve_test",
    "当期读数20261109": "vix_now_20261109",
}

frames = dict(existing)
for sheet, f in add.items():
    p = os.path.join(OUT, f + ".csv")
    if os.path.exists(p):
        d = pd.read_csv(p)
        frames[sheet[:31]] = d
        print("+", sheet, d.shape)
    else:
        print("MISSING", f)

with pd.ExcelWriter(XLSX, engine="openpyxl") as w:
    for nm, d in frames.items():
        d.to_excel(w, sheet_name=nm[:31], index=False)
print("saved", XLSX, "%.1f KB" % (os.path.getsize(XLSX) / 1024), "sheets:", len(frames))
