# -*- coding: utf-8 -*-
"""核对各源最新日期，确认 2026-11-06 之后市场是否已有新数据。"""
import json
import urllib.error
import urllib.request

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")
PROXY = "http://127.0.0.1:7897"


def get(url, proxy=PROXY, timeout=30, headers=None, data=None):
    h = {"User-Agent": UA, "Accept": "*/*", "Accept-Language": "en-US,en;q=0.9"}
    if headers:
        h.update(headers)
    op = (urllib.request.build_opener(urllib.request.ProxyHandler({"http": proxy, "https": proxy}))
          if proxy else urllib.request.build_opener(urllib.request.ProxyHandler({})))
    try:
        with op.open(urllib.request.Request(url, headers=h, data=data), timeout=timeout) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()[:300]
    except Exception as e:
        return None, str(e).encode()


print("=" * 70)
print("A. Yahoo ^VIX / ^GSPC 最近 5 个交易日")
print("=" * 70)
import datetime
for sym in ["%5EVIX", "%5EGSPC", "%5EVIX3M", "%5EVIX9D", "%5EVIX6M", "%5EVVIX", "%5ESKEW"]:
    u = ("https://query1.finance.yahoo.com/v8/finance/chart/%s?range=10d&interval=1d" % sym)
    st, b = get(u)
    if st != 200:
        print(sym, "->", st, b[:80])
        continue
    try:
        d = json.loads(b)
        res = d["chart"]["result"][0]
        ts = res.get("timestamp") or []
        cl = res["indicators"]["quote"][0]["close"]
        rows = []
        for t, c in list(zip(ts, cl))[-5:]:
            rows.append((datetime.datetime.utcfromtimestamp(t).strftime("%Y-%m-%d"), None if c is None else round(c, 2)))
        print("%-10s %s" % (sym.replace("%5E", "^"), rows))
    except Exception as e:
        print(sym, "parse fail", e, b[:150])

print()
print("=" * 70)
print("B. CBOE CSV 末尾")
print("=" * 70)
for t in ["VIX", "VIX3M", "VIX9D", "VIX6M", "VVIX", "SKEW"]:
    u = "https://cdn.cboe.com/api/global/us_indices/daily_prices/%s_History.csv" % t
    st, b = get(u, proxy=None)
    if st == 200:
        lines = b.decode("utf-8", "replace").strip().split("\n")
        print("%-7s 末两行: %s | %s" % (t, lines[-2], lines[-1]))

print()
print("=" * 70)
print("C. TradingView scanner 实时")
print("=" * 70)
syms = ["CBOE:VIX", "CBOE:VXN", "CBOE:RVX", "CBOE:VIX3M", "CBOE:VVIX", "CBOE:SKEW",
        "CBOE:SPX", "CBOE:VXAPL", "CBOE:OVX", "CBOE:GVZ"]
body = json.dumps({"symbols": {"tickers": syms, "query": {"types": []}},
                   "columns": ["name", "close", "change", "high", "low", "open",
                               "Perf.W", "Perf.M", "Perf.Y"]}).encode()
st, b = get("https://scanner.tradingview.com/america/scan", data=body,
            headers={"Content-Type": "application/json"})
print("status", st)
if st == 200:
    d = json.loads(b)
    for x in d.get("data", []):
        print("  %-10s close=%-9s chg=%-9s high=%-9s low=%-9s W=%-8s M=%-8s Y=%-8s" % tuple(
            [x["s"]] + [round(v, 3) if isinstance(v, (int, float)) else v for v in x["d"]]))

print()
print("=" * 70)
print("D. investing.com 历史数据（用 SPX id=8839 已验证可用；再找 VIX）")
print("=" * 70)
for pid in [8869, 8874, 8839, 408, 409, 166, 169, 171, 172, 178, 179]:
    u = ("https://api.investing.com/api/financialdata/%s/historical/chart/?period=P5D&interval=P1D" % pid)
    st, b = get(u, headers={"domain-id": "www"})
    if st == 200 and b[:1] == b"{":
        try:
            d = json.loads(b)
        except Exception:
            continue
        arr = d.get("data") or []
        if arr:
            print("  id=%-6s rows=%-3d last=%s" % (pid, len(arr), arr[-1][:6]))
