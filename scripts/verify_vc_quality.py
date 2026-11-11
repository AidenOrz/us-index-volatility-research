# -*- coding: utf-8 -*-
"""核对 vixcentral 历史 M1 与同期 VIX 现货是否吻合，判断可用起点。"""
import json
import os
import time
import urllib.request

import pandas as pd

BASE = r"E:\workspace\new"
CB = os.path.join(BASE, "data", "raw", "cboe_vol")
OUT = os.path.join(BASE, "data", "output")
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")


def load(t):
    d = pd.read_csv(os.path.join(CB, t + "_History.csv"))
    d["DATE"] = pd.to_datetime(d["DATE"], format="%m/%d/%Y")
    col = "CLOSE" if "CLOSE" in d.columns else d.columns[-1]
    return d.set_index("DATE")[col].astype(float).sort_index()


vix = load("VIX")


def get(url, timeout=8):
    req = urllib.request.Request(url, headers={
        "User-Agent": UA, "X-Requested-With": "XMLHttpRequest", "Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.read()
    except Exception:
        return b""


rows = []
dates = pd.date_range("2006-01-03", "2008-12-31", freq="MS")
for d in dates:
    # 找最近的交易日
    idx = vix.index[vix.index <= d]
    if len(idx) == 0:
        continue
    td = idx[-1]
    b = get("https://vixcentral.com/ajax_historical?n1=" + td.strftime("%Y-%m-%d"))
    txt = b.decode("utf-8", "replace") if b else ""
    if not (txt.startswith("[") and '"error"' not in txt):
        rows.append({"日期": td.strftime("%Y-%m-%d"), "VIX现货": vix.loc[td], "M1": None, "偏差%": None})
        time.sleep(0.12)
        continue
    try:
        arr = json.loads(txt)
        vals = [v for v in arr[1:] if v > 0]
        m1 = vals[0] if vals else None
    except Exception:
        m1 = None
    dev = None
    if m1:
        dev = (m1 / vix.loc[td] - 1) * 100
    rows.append({"日期": td.strftime("%Y-%m-%d"), "VIX现货": round(vix.loc[td], 2),
                 "M1": round(m1, 2) if m1 else None,
                 "偏差%": round(dev, 1) if dev is not None else None})
    time.sleep(0.12)

d = pd.DataFrame(rows)
print(d.to_string(index=False))
print("\nM1 与 VIX 现货偏差 >30% 的日期（说明数据不可信）:")
bad = d[(d["偏差%"].notna()) & (d["偏差%"].abs() > 30)]
print(bad.to_string(index=False) if len(bad) else "无")
d.to_csv(os.path.join(OUT, "vc_quality.csv"), index=False, encoding="utf-8-sig")
