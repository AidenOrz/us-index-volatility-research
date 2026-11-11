# -*- coding: utf-8 -*-
"""小样本（40 个交易日）验证 vixcentral 历史期限结构可用率，超时压到 8 秒。"""
import json
import os
import time
import urllib.error
import urllib.request

import pandas as pd

BASE = r"E:\workspace\new"
PROC = os.path.join(BASE, "data", "processed")
OUT = os.path.join(BASE, "data", "output")
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")

px = pd.read_csv(os.path.join(PROC, "prices_close.csv"), index_col=0, parse_dates=True)
idx = px.loc["2005-01-01":"2026-11-06"].index
sample = idx[:: max(1, len(idx) // 40)][:40]
print("抽样 %d 日: %s ~ %s" % (len(sample), sample[0].date(), sample[-1].date()))


def get(url, timeout=8):
    req = urllib.request.Request(url, headers={
        "User-Agent": UA, "X-Requested-With": "XMLHttpRequest",
        "Accept": "application/json", "Referer": "https://vixcentral.com/"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.read()
    except Exception:
        return b""


rows, ok, bad = [], 0, 0
for d in sample:
    ds = d.strftime("%Y-%m-%d")
    b = get("https://vixcentral.com/ajax_historical?n1=" + ds)
    txt = b.decode("utf-8", "replace") if b else ""
    if txt.startswith("[") and '"error"' not in txt:
        try:
            arr = json.loads(txt)
            vals = [v for v in arr[1:] if v > 0]
            if len(vals) >= 3:
                rows.append({"日期": ds, "有效合约": len(vals), "M1": vals[0],
                             "M2": vals[1], "M3": vals[2],
                             "M1/M2-1%": (vals[1] / vals[0] - 1) * 100})
                ok += 1
                continue
        except Exception:
            pass
    bad += 1
    time.sleep(0.1)

print("可用 %d / %d = %.0f%%，不可用 %d" % (ok, len(sample), 100.0 * ok / max(len(sample), 1), bad))
d = pd.DataFrame(rows)
if len(d):
    d.to_csv(os.path.join(OUT, "vc_curve_test.csv"), index=False, encoding="utf-8-sig")
    print(d.to_string(index=False))
    print("\nM1/M2-1 中位: %.2f%%  （contango 为正）" % d["M1/M2-1%"].median())
