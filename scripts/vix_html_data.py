# -*- coding: utf-8 -*-
"""把 VIX 专题的全部 CSV 汇总成 data/output/vix_html_data.json"""
import os
import json
import numpy as np
import pandas as pd

BASE = r"E:\workspace\new"
OUT = os.path.join(BASE, "data", "output")

FILES = ["vix_crosscheck", "vix_vrp", "vix_family", "vix_family_sig", "vix_family_now",
         "vix_level_bins", "vix_pct_bins", "vix_ts_bins", "vix_events", "vix_by_index",
         "vix_path", "vix_robust", "vix_peak", "vix_quad2", "vix_extreme",
         "vix_interaction", "vix_ushape", "vix_ushape_strat", "vix_analog",
         "vix_strategy", "vix_strategy_oos", "vix_now", "vix_rulebook", "vix_ladder"]

D = {}
for f in FILES:
    p = os.path.join(OUT, f + ".csv")
    d = pd.read_csv(p)
    d = d.replace([np.inf, -np.inf], np.nan)
    recs = []
    for _, r in d.iterrows():
        rec = {}
        for c in d.columns:
            v = r[c]
            if isinstance(v, (np.floating, float)):
                rec[c] = None if (v != v) else float(v)
            elif isinstance(v, (np.integer,)):
                rec[c] = int(v)
            elif isinstance(v, (np.bool_, bool)):
                rec[c] = bool(v)
            elif v is None or (isinstance(v, float) and v != v):
                rec[c] = None
            else:
                rec[c] = str(v)
        recs.append(rec)
    D[f] = recs
    print(f, len(recs))

with open(os.path.join(OUT, "vix_html_data.json"), "w", encoding="utf-8") as fh:
    json.dump(D, fh, ensure_ascii=False, indent=1)
print("saved vix_html_data.json", os.path.getsize(os.path.join(OUT, "vix_html_data.json")) // 1024, "KB")
