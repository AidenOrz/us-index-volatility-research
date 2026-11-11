# -*- coding: utf-8 -*-
"""深入探测各源能拿到什么：CFTC COT、vixcentral、investing、tradingview。"""
import json
import re
import urllib.error
import urllib.parse
import urllib.request

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")
PROXY = "http://127.0.0.1:7897"


def get(url, proxy=None, timeout=25, headers=None):
    h = {"User-Agent": UA, "Accept": "*/*", "Accept-Language": "en-US,en;q=0.9"}
    if headers:
        h.update(headers)
    if proxy:
        op = urllib.request.build_opener(urllib.request.ProxyHandler({"http": proxy, "https": proxy}))
    else:
        op = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    req = urllib.request.Request(url, headers=h)
    try:
        with op.open(req, timeout=timeout) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()[:500]
    except Exception as e:
        return None, str(e).encode()


print("=" * 70)
print("A. CFTC Socrata —— 找 VIX 期货持仓")
print("=" * 70)
# 先搜数据集
st, b = get("https://publicreporting.cftc.gov/api/views.json?limit=50", PROXY)
if st == 200:
    for d in json.loads(b):
        print("  ", d["id"], "|", d["name"][:70])

for ds in ["6dca-aqww", "gpe5-46if", "yh39-sbu6"]:
    q = ("https://publicreporting.cftc.gov/resource/%s.json?"
         "$select=market_and_exchange_names,count(*)&$group=market_and_exchange_names&$limit=2000" % ds)
    st, b = get(q, PROXY)
    if st != 200:
        print(ds, "->", st)
        continue
    try:
        arr = json.loads(b)
    except Exception:
        print(ds, "parse fail", b[:200])
        continue
    vix = [x for x in arr if "VOLATILITY" in x["market_and_exchange_names"].upper()]
    print("\n数据集", ds, "共", len(arr), "个合约市场；含 VOLATILITY 的：")
    for x in vix:
        print("   ", x["market_and_exchange_names"], "| rows =", x["count"])

print()
print("=" * 70)
print("B. CFTC COT VIX 期货实际数据样例")
print("=" * 70)
q = ("https://publicreporting.cftc.gov/resource/6dca-aqww.json?"
     "$where=market_and_exchange_names like '%25VOLATILITY%25'"
     "&$order=report_date_as_yyyy_mm_dd DESC&$limit=2")
st, b = get(q, PROXY)
print("status", st)
if st == 200:
    arr = json.loads(b)
    if arr:
        print("字段数:", len(arr[0]))
        print("字段:", sorted(arr[0].keys())[:40])
        print("样例:", {k: arr[0][k] for k in list(arr[0])[:12]})
        # 总数
        q2 = ("https://publicreporting.cftc.gov/resource/6dca-aqww.json?"
              "$select=count(*)&$where=market_and_exchange_names like '%25VOLATILITY%25'")
        st2, b2 = get(q2, PROXY)
        print("总行数:", b2.decode()[:200])
    else:
        print("空结果")

print()
print("=" * 70)
print("C. vixcentral.com")
print("=" * 70)
for u in ["https://vixcentral.com/", "https://vixcentral.com/vix_structured_data/"]:
    st, b = get(u, None)
    t = b.decode("utf-8", "replace")
    print(u, "->", st, len(t), "bytes")
    # 找 data / json / csv 线索
    for pat in [r"var\s+\w+\s*=\s*\[", r"fetch\(['\"]([^'\"]+)", r"\.json", r"\.csv",
                r"data-\w+=", r"<table", r"XLSX"]:
        m = re.findall(pat, t)
        if m:
            print("   pattern", pat, "->", len(m), "hits", str(m[:5])[:160])
    # 打印 script src
    srcs = re.findall(r'<script[^>]+src="([^"]+)"', t)
    print("   scripts:", srcs[:8])

print()
print("=" * 70)
print("D. investing.com 历史数据接口")
print("=" * 70)
# investing 的常见内部 API
for u, hd in [
    ("https://api.investing.com/api/financialdata/8839/historical/chart/?period=P1Y&interval=P1D&pointscount=160", {"domain-id": "www"}),
    ("https://www.investing.com/api/financialdata/8839/historical/chart/?period=P1Y&interval=P1D", {}),
    ("https://tvc4.investing.com/1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d/0/0/0/history?symbol=8839&resolution=D&from=1600000000&to=1750000000", {}),
]:
    st, b = get(u, PROXY, headers=hd)
    print(u[:80], "->", st, b[:150])

print()
print("=" * 70)
print("E. tradingview")
print("=" * 70)
# scanner 拿 VIX 报价
body = json.dumps({"symbols": {"tickers": ["CBOE:VIX", "CBOE:VXN", "CBOE:RVX", "CBOE:VIX3M"],
                               "query": {"types": []}},
                   "columns": ["close", "change", "volume", "update_mode"]}).encode()
req = urllib.request.Request("https://scanner.tradingview.com/america/scan", data=body,
                             headers={"User-Agent": UA, "Content-Type": "application/json"})
op = urllib.request.build_opener(urllib.request.ProxyHandler({"http": PROXY, "https": PROXY}))
try:
    with op.open(req, timeout=25) as r:
        print("scanner ->", r.status, r.read()[:400])
except Exception as e:
    print("scanner fail", e)

# history 端点
u = "https://symbol-search.tradingview.com/symbol_search/?text=VIX&exchange=CBOE&type=index"
st, b = get(u, PROXY)
print("symbol-search ->", st, b[:300])
