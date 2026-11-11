# -*- coding: utf-8 -*-
"""探测外部数据源连通性：CFTC / vixcentral / investing / tradingview / cboe / nasdaq。"""
import json
import socket
import ssl
import sys
import time
import urllib.error
import urllib.request

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")

TARGETS = [
    ("CFTC Socrata 目录", "https://publicreporting.cftc.gov/api/views.json?limit=5"),
    ("CFTC Socrata VIX COT", "https://publicreporting.cftc.gov/resource/6dca-aqww.json?$limit=3"),
    ("CFTC 官网首页", "https://www.cftc.gov/"),
    ("CFTC 历史 COT 压缩包", "https://www.cftc.gov/files/dea/history/deacot2026.zip"),
    ("vixcentral 首页", "https://vixcentral.com/"),
    ("vixcentral 结构化数据", "https://vixcentral.com/vix_structured_data/"),
    ("vixcentral API", "https://vixcentral.com/api/historical?"),
    ("investing.com 首页", "https://www.investing.com/"),
    ("investing VIX 历史", "https://www.investing.com/indices/volatility-s-p-500-historical-data"),
    ("tradingview 首页", "https://www.tradingview.com/"),
    ("tradingview scanner", "https://scanner.tradingview.com/america/scan"),
    ("CBOE VIX 历史", "https://cdn.cboe.com/api/global/us_indices/daily_prices/VIX_History.csv"),
    ("CBOE 期货结算", "https://cdn.cboe.com/api/global/us_indices/daily_prices/VIX3M_History.csv"),
    ("CBOE VX 期货", "https://www.cboe.com/us/futures/market_statistics/settlement/?product=VX"),
    ("CBOE 波动率指数列表", "https://cdn.cboe.com/api/global/us_indices/daily_prices/index.json"),
    ("Nasdaq VIX 期权", "https://api.nasdaq.com/api/quote/VIX/info?assetclass=index"),
    ("Yahoo VIX", "https://query1.finance.yahoo.com/v8/finance/chart/%5EVIX?range=5d&interval=1d"),
]

PROXIES = [None, "http://127.0.0.1:7897", "http://127.0.0.1:7890", "http://127.0.0.1:10809"]


def make_opener(proxy):
    if proxy:
        h = urllib.request.ProxyHandler({"http": proxy, "https": proxy})
    else:
        h = urllib.request.ProxyHandler({})
    return urllib.request.build_opener(h)


def probe(url, proxy, timeout=12):
    req = urllib.request.Request(url, headers={
        "User-Agent": UA,
        "Accept": "*/*",
        "Accept-Language": "en-US,en;q=0.9",
    })
    t0 = time.time()
    try:
        with make_opener(proxy).open(req, timeout=timeout) as r:
            data = r.read(4096)
            return {"ok": True, "status": r.status, "bytes": len(data),
                    "ms": int((time.time() - t0) * 1000),
                    "head": data[:120].decode("utf-8", "replace").replace("\n", " ")}
    except urllib.error.HTTPError as e:
        return {"ok": False, "status": e.code, "err": "HTTPError",
                "ms": int((time.time() - t0) * 1000), "head": str(e)[:120]}
    except Exception as e:
        return {"ok": False, "status": None, "err": type(e).__name__,
                "ms": int((time.time() - t0) * 1000), "head": str(e)[:120]}


# 先看哪个代理可用
print("=== 代理连通性 ===")
for pr in PROXIES:
    r = probe("https://query1.finance.yahoo.com/v8/finance/chart/%5EVIX?range=5d&interval=1d", pr, timeout=8)
    print(("直连" if pr is None else pr), "->", r.get("status"), r.get("err", ""), r.get("ms"), "ms")

print()
print("=== 目标站点（先直连，失败再试可用代理）===")
for name, url in TARGETS:
    tried = []
    res = None
    for pr in PROXIES:
        rr = probe(url, pr, timeout=12)
        tried.append((pr, rr.get("status"), rr.get("err", ""), rr.get("ms")))
        if rr.get("ok"):
            res = (pr, rr)
            break
    tag = "OK  " if res else "FAIL"
    pr_used = ("直连" if res[0] is None else res[0]) if res else "-"
    detail = res[1] if res else None
    print("[%s] %-24s via=%-22s status=%s ms=%s %s" % (
        tag, name, pr_used,
        detail["status"] if detail else (res and "") or [t[1] for t in tried if t[1]][:1],
        detail["ms"] if detail else "-",
        (detail["head"][:70] if detail else str(tried)[:90])))
