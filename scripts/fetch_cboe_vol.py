# -*- coding: utf-8 -*-
"""下载 CBOE 官方全部可用波动率指数历史文件到 data/raw/cboe_vol/。
同时探测 vixcentral /ajax_historical 的可回溯范围。
"""
import json
import os
import time
import urllib.error
import urllib.request

BASE = r"E:\workspace\new"
RAW = os.path.join(BASE, "data", "raw", "cboe_vol")
os.makedirs(RAW, exist_ok=True)
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")

TICKERS = ["VIX", "VIX3M", "VIX9D", "VIX6M", "VXN", "RVX", "VVIX", "SKEW", "OVX", "GVZ",
           "VXAPL", "VXAZN", "VXGOG", "VXGS", "VXIBM", "VXEEM", "VXEWZ", "VXSLV",
           "VXHYG", "VXTLT", "VXGDX", "VXFXI", "VXEFA"]

print("=" * 70)
print("A. 下载 CBOE 官方文件")
print("=" * 70)
got = []
for t in TICKERS:
    p = os.path.join(RAW, t + "_History.csv")
    if os.path.exists(p) and os.path.getsize(p) > 1000:
        print("  已有 %-8s %d bytes" % (t, os.path.getsize(p)))
        got.append(t)
        continue
    u = "https://cdn.cboe.com/api/global/us_indices/daily_prices/%s_History.csv" % t
    req = urllib.request.Request(u, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            d = r.read()
        with open(p, "wb") as f:
            f.write(d)
        print("  [OK] %-8s %7d bytes  rows=%d" % (t, len(d), d.count(b"\n")))
        got.append(t)
    except Exception as e:
        print("  [ERR] %-8s %s" % (t, e))
    time.sleep(0.15)

print("\n共 %d 个文件" % len(got))

print()
print("=" * 70)
print("B. vixcentral /ajax_historical 可回溯范围")
print("=" * 70)
for d in ["2004-01-02", "2004-03-26", "2005-01-03", "2006-01-03", "2007-01-03", "2008-01-02"]:
    u = "https://vixcentral.com/ajax_historical?n1=" + d
    req = urllib.request.Request(u, headers={"User-Agent": UA, "X-Requested-With": "XMLHttpRequest",
                                             "Referer": "https://vixcentral.com/"})
    try:
        with urllib.request.urlopen(req, timeout=25) as r:
            b = r.read()
        print("  %s -> %3d bytes  %s" % (d, len(b), b.decode("utf-8", "replace")[:90]))
    except Exception as e:
        print("  %s -> ERR %s" % (d, e))
    time.sleep(0.2)
