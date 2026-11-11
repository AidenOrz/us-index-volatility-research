# -*- coding: utf-8 -*-
"""第三轮：CFTC 全数据集搜 VIX；vixcentral 内联数据解析；investing 找 VIX id；tradingview 历史。"""
import json
import re
import urllib.error
import urllib.request

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")
PROXY = "http://127.0.0.1:7897"


def get(url, proxy=PROXY, timeout=30, headers=None, data=None):
    h = {"User-Agent": UA, "Accept": "*/*", "Accept-Language": "en-US,en;q=0.9"}
    if headers:
        h.update(headers)
    if proxy:
        op = urllib.request.build_opener(urllib.request.ProxyHandler({"http": proxy, "https": proxy}))
    else:
        op = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    req = urllib.request.Request(url, headers=h, data=data)
    try:
        with op.open(req, timeout=timeout) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()[:400]
    except Exception as e:
        return None, str(e).encode()


print("=" * 72)
print("A. CFTC —— 在全部 COT 数据集里搜 VIX / VOLATILITY / CBOE")
print("=" * 72)
DATASETS = ["6dca-aqww", "gpe5-46if", "72hh-3qpy", "ubmb-6exi", "98ig-3k9y",
            "8jj7-5vf4", "dw8z-x6ih", "kh3c-gbw2", "srt6-5q2f"]
for ds in DATASETS:
    q = ("https://publicreporting.cftc.gov/resource/%s.json?"
         "$select=market_and_exchange_names,count(*)&$group=market_and_exchange_names&$limit=5000" % ds)
    st, b = get(q)
    if st != 200:
        print(ds, "->", st, b[:100])
        continue
    try:
        arr = json.loads(b)
    except Exception:
        print(ds, "parse fail", b[:150])
        continue
    hits = [x for x in arr if ("VOLATILITY" in x["market_and_exchange_names"].upper()
                               or "VIX" in x["market_and_exchange_names"].upper()
                               or "CBOE" in x["market_and_exchange_names"].upper()
                               or "CBT" in x["market_and_exchange_names"].upper()[:40])]
    print("%s  市场数=%d  命中:" % (ds, len(arr)))
    for x in hits[:12]:
        print("    ", x["market_and_exchange_names"], "| rows =", x["count"])

print()
print("=" * 72)
print("B. vixcentral.com —— 提取内联 JS 数据")
print("=" * 72)
st, b = get("https://vixcentral.com/", proxy=None)
t = b.decode("utf-8", "replace")
print("status", st, "len", len(t))
for varname in ["time_data_var", "last_data_var", "vcurve_data_var", "previous_close_var", "b"]:
    m = re.search(r"var\s+" + re.escape(varname) + r"\s*=\s*(\[.*?\]);", t, re.S)
    if m:
        val = m.group(1)
        print("\nvar %s (len=%d):" % (varname, len(val)))
        print("  ", val[:400].replace("\n", " "))
    else:
        print("\nvar %s 未找到" % varname)
# 找所有 var
allvars = re.findall(r"var\s+(\w+)\s*=\s*([^;]{0,200});", t)
print("\n全部内联变量:", [(k, v[:40]) for k, v in allvars][:30])

print()
print("=" * 72)
print("C. investing.com —— 找 VIX 的 pair ID")
print("=" * 72)
# 常见 VIX id 猜测
for pid in [8839, 443, 409, 262, 286, 8859, 166, 8874]:
    u = ("https://api.investing.com/api/financialdata/%d/historical/chart/?period=P1M&interval=P1D" % pid)
    st, b = get(u, headers={"domain-id": "www"})
    if st == 200 and b[:1] == b"{":
        d = json.loads(b)
        arr = d.get("data", [])
        print("id=%-6d rows=%-4d first=%s" % (pid, len(arr), arr[0] if arr else None))
# 用搜索接口
for q in ["VIX", "CBOE Volatility Index", "VXN"]:
    u = "https://api.investing.com/api/search/v2/search?q=" + urllib.parse.quote(q)
    st, b = get(u, headers={"domain-id": "www"})
    print("search %-24s -> %s %s" % (q, st, b[:300]))

print()
print("=" * 72)
print("D. tradingview —— 历史数据尝试")
print("=" * 72)
# scanner 多列
body = json.dumps({"symbols": {"tickers": ["CBOE:VIX", "CBOE:VXN", "CBOE:RVX", "CBOE:VIX3M", "CBOE:SPX"],
                               "query": {"types": []}},
                   "columns": ["name", "close", "change", "high", "low",
                               "Recommend.All", "Volatility.D", "Perf.Y"]}).encode()
st, b = get("https://scanner.tradingview.com/america/scan", data=body,
            headers={"Content-Type": "application/json"})
print("scanner ->", st, b[:400])
