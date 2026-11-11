# -*- coding: utf-8 -*-
"""汇总数据源尽调专题所需的全部 CSV → data/output/src_html_data.json"""
import json
import os
import numpy as np
import pandas as pd

OUT = r"E:\workspace\new\data\output"

FILES = ["source_inventory", "vol_three_source", "vix_term_slopes", "skew_vvix_stat",
         "vix_now_20261109", "cot_signal", "cot_tff_signal", "vc_curve_test"]

D = {}
for f in FILES:
    p = os.path.join(OUT, f + ".csv")
    if not os.path.exists(p):
        print("MISSING", f)
        continue
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
            else:
                rec[c] = None if (v is None or (isinstance(v, float) and v != v)) else str(v)
        recs.append(rec)
    D[f] = recs
    print(f, len(recs))

with open(os.path.join(OUT, "src_html_data.json"), "w", encoding="utf-8") as fh:
    json.dump(D, fh, ensure_ascii=False, indent=1)
print("saved", os.path.getsize(os.path.join(OUT, "src_html_data.json")) // 1024, "KB")
