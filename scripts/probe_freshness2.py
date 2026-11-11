# -*- coding: utf-8 -*-
"""补：TradingView scanner 详细字段 + investing.com VIX id + 最新交易日核对。"""
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
print("A. TradingView scanner 全字段")
print("=" * 70)
syms = ["CBOE:VIX", "CBOE:VXN", "CBOE:RVX", "CBOE:VIX3M", "CBOE:VIX9D", "CBOE:VIX6M",
        "CBOE:VVIX", "CBOE:SKEW", "CBOE:SPX", "CBOE:OVX", "CBOE:GVZ", "CBOE:VXTLT"]
cols = ["name", "close", "change", "high", "low", "open", "Perf.W", "Perf.M", "Perf.Y",
        "RSI", "Volatility.D", "Recommend.All"]
body = json.dumps({"symbols": {"tickers": syms, "query": {"types": []}},
                   "columns": cols}).encode()
st, b = get("https://scanner.tradingview.com/america/scan", data=body,
            headers={"Content-Type": "application/json"})
print("status", st)
if st == 200:
    d = json.loads(b)
    print("  %-12s %s" % ("symbol", cols[1:]))
    for x in d.get("data", []):
        vals = []
        for v in x["d"]:
            vals.append(round(v, 2) if isinstance(v, (int, float)) else v)
        print("  %-12s %s" % (x["s"], vals))

print()
print("=" * 70)
print("B. investing.com —— 用页面 HTML 里的 44271/41279 等 id 逐个验证")
print("=" * 70)
# 从上次抓取结果里候选：先试能返回 25 附近或 7500 附近数值的
for pid in [44271, 41279, 43433, 43430, 43465, 44266, 41146, 41042, 40034, 40006,
            943427, 942944, 940801, 942611, 1223898, 1244280, 1153688, 1115063,
            1076610, 1050737, 103233, 103469, 103240, 44336, 44337, 44338]:
    u = ("https://api.investing.com/api/financialdata/%s/historical/chart/?period=P5D&interval=P1D" % pid)
    st, b = get(u, headers={"domain-id": "www"})
    if st == 200 and b[:1] == b"{":
        try:
            d = json.loads(b)
        except Exception:
            continue
        arr = d.get("data") or []
        if arr:
            print("  id=%-8s rows=%-3d last_close=%s" % (pid, len(arr), arr[-1][4] if len(arr[-1]) > 4 else arr[-1]))

print()
print("=" * 70)
print("C. investing.com —— 直接抓 VIX 历史页里的 JSON")
print("=" * 70)
import re
st, b = get("https://www.investing.com/indices/volatility-s-p-500-historical-data")
t = b.decode("utf-8", "replace")
print("page", st, len(t))
m = re.search(r'"instrumentId":"(\d+)"', t)
print("instrumentId:", m.group(1) if m else None)
# 找包含 'volatility' 的 breadcrumb 附近
for mm in re.finditer(r'"url":"([^"]*volatility[^"]*)"', t, re.I):
    print("   url:", mm.group(1)[:80])
