# -*- coding: utf-8 -*-
"""穷举 CBOE 官方 CDN 上可下载的波动率指数历史文件。"""
import urllib.error
import urllib.request

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")

CANDS = ["VIX", "VIX3M", "VIX9D", "VIX6M", "VXN", "RVX", "VVIX", "SKEW", "OVX", "GVZ",
         "VXAPL", "VXAZN", "VXGOG", "VXGS", "VXIBM", "VXEEM", "VXEWZ", "VXXLE", "VXSLV",
         "VXHYG", "VXTYN", "VXTLT", "VXGOLD", "VXGDX", "VXCL", "VXFXI", "VXEFA"]

OK = []
for c in CANDS:
    u = "https://cdn.cboe.com/api/global/us_indices/daily_prices/%s_History.csv" % c
    req = urllib.request.Request(u, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            d = r.read()
        head = d[:70].decode("utf-8", "replace").replace("\n", "|")
        lines = d.decode("utf-8", "replace").count("\n")
        print("[OK]   %-8s %8d bytes  rows~%-6d %s" % (c, len(d), lines, head))
        OK.append((c, len(d), lines))
    except urllib.error.HTTPError as e:
        print("[%s] %-8s" % (e.code, c))
    except Exception as e:
        print("[ERR]  %-8s %s" % (c, type(e).__name__))

print("\n可用文件 %d 个: %s" % (len(OK), [x[0] for x in OK]))
