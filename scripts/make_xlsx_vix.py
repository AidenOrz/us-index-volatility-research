# -*- coding: utf-8 -*-
"""把 VIX 专题的 12 张核心表追加进 Excel 数据册（保留既有全部工作表）。"""
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
    "VIX_多源比对": "vix_crosscheck.csv",
    "VIX_波动率风险溢价": "vix_vrp.csv",
    "VIX_家族描述统计": "vix_family.csv",
    "VIX_对口vs通用": "vix_family_sig.csv",
    "VIX_水平分层": "vix_level_bins.csv",
    "VIX_分位分层": "vix_pct_bins.csv",
    "VIX_期限结构": "vix_ts_bins.csv",
    "VIX_事件检验": "vix_events.csv",
    "VIX_六指数普适": "vix_by_index.csv",
    "VIX_事件后路径": "vix_path.csv",
    "VIX_分年代稳健": "vix_robust.csv",
    "VIX_极端事件聚集": "vix_extreme.csv",
    "VIX_U型趋势交叉": "vix_ushape.csv",
    "VIX_仓位刻度": "vix_ladder.csv",
    "VIX_估值交叉": "vix_interaction.csv",
    "VIX_策略回测": "vix_strategy.csv",
    "VIX_样本外": "vix_strategy_oos.csv",
    "VIX_历史类比": "vix_analog.csv",
    "VIX_当前读数": "vix_now.csv",
    "VIX_规则手册": "vix_rulebook.csv",
}

frames = dict(existing)
for sheet, f in add.items():
    p = os.path.join(OUT, f)
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
