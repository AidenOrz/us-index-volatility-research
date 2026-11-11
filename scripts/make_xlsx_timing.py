# -*- coding: utf-8 -*-
"""把新增择时分析写入 Excel 数据册（新增 8 个工作表），并保留原有 16 表。"""
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
    print("原有工作表:", list(existing.keys()))

# 精简的择时表（放进 Excel）
add = {
    "择时_位置温度计": "timing_composite.csv",
    "择时_温度分层收益": "timing_composite_quintile.csv",
    "择时_事件检验": "timing_events.csv",
    "择时_CAPE分层": "timing_cape_bins.csv",
    "择时_双轴四象限": "timing_quadrant.csv",
    "择时_策略回测": "timing_final.csv",
    "择时_分年代": "timing_by_decade.csv",
    "择时_样本外": "timing_oos.csv",
    "择时_参数敏感性": "timing_sensitivity.csv",
    "择时_历史类比": "timing_analogues.csv",
    "择时_当前读数": "timing_dashboard.csv",
    "择时_IC检验": "timing_ic.csv",
}
frames = dict(existing)
for sheet, f in add.items():
    p = os.path.join(OUT, f)
    if os.path.exists(p):
        frames[sheet] = pd.read_csv(p)
        print("+", sheet, frames[sheet].shape)

with pd.ExcelWriter(XLSX, engine="openpyxl") as w:
    for nm, d in frames.items():
        d.to_excel(w, sheet_name=nm[:31], index=False)
print("saved", XLSX, "%.1f KB" % (os.path.getsize(XLSX)/1024), "sheets:", len(frames))
