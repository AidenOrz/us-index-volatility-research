# -*- coding: utf-8 -*-
"""第六轮：investing.com VIX ID 定位 + tradingview / CBOE 期货成交持仓补充。"""
import json
import re
import urllib.error
import urllib.parse
import urllib.request

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")
PROXY = "http://127.0.0.1:7897"


def get(url, proxy=PROXY, timeout=30, headers=None):
    h = {"User-Agent": UA, "Accept": "application/json, text/html, */*",
         "Accept-Language": "en-US,en;q=0.9"}
    if headers:
        h.update(headers)
    op = (urllib.request.build_opener(urllib.request.ProxyHandler({"http": proxy, "https": proxy}))
          if proxy else urllib.request.build_opener(urllib.request.ProxyHandler({})))
    req = urllib.request.Request(url, headers=h)
    try:
        with op.open(req, timeout=timeout) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()[:300]
    except Exception as e:
        return None, str(e).encode()


print("=" * 72)
print("A. investing.com —— 从 VIX 页面 HTML 里抠 instrument id")
print("=" * 72)
st, b = get("https://www.investing.com/indices/volatility-s-p-500")
t = b.decode("utf-8", "replace")
print("page ->", st, len(t))
for pat in [r'"instrumentId"\s*:\s*(\d+)', r'pair_id["\']?\s*[:=]\s*["\']?(\d+)',
            r'"pairId"\s*:\s*(\d+)', r'data-pair-id="(\d+)"',
            r'"instrument_id"\s*:\s*(\d+)', r'pairs_id["\']?\s*[:=]\s*["\']?(\d+)']:
    m = re.findall(pat, t)
    if m:
        print(pat, "->", set(m))
# 也试试 historical-data 页面
st2, b2 = get("https://www.investing.com/indices/volatility-s-p-500-historical-data")
t2 = b2.decode("utf-8", "replace")
print("hist page ->", st2, len(t2))
for pat in [r'"instrumentId"\s*:\s*(\d+)', r'data-pair-id="(\d+)"',
            r'"pairId"\s*:\s*(\d+)']:
    m = re.findall(pat, t2)
    if m:
        print(pat, "->", set(m))
# 从页面里找 "identifier"
for m in re.finditer(r'.{40}(?:instrument|pair)[Ii]d["\']?\s*[:=]\s*["\']?\d+.{40}', t2):
    print("   ctx:", m.group(0).replace("\n", " ")[:140])
    break

print()
print("=" * 72)
print("B. 用抓到的 id 试历史接口")
print("=" * 72)
ids = set()
for txt in (t, t2):
    for pat in [r'"instrumentId"\s*:\s*(\d+)', r'data-pair-id="(\d+)"', r'"pairId"\s*:\s*(\d+)']:
        ids.update(re.findall(pat, txt))
print("候选 id:", sorted(ids)[:20])
for pid in sorted(ids)[:20]:
    u = ("https://api.investing.com/api/financialdata/%s/historical/chart/?period=P1M&interval=P1D" % pid)
    st3, b3 = get(u, headers={"domain-id": "www"})
    if st3 != 200 or b3[:1] != b"{":
        continue
    try:
        d = json.loads(b3)
    except Exception:
        continue
    arr = d.get("data") or []
    if arr:
        print("id=%-8s rows=%-3d last=%s" % (pid, len(arr), arr[-1][:6]))

print()
print("=" * 72)
print("C. tradingview —— 试 history 端点 (datafeed)")
print("=" * 72)
for u in ["https://data.tradingview.com/symbols/CBOE-VIX/",
          "https://www.tradingview.com/symbols/CBOE-VIX/",
          "https://scanner.tradingview.com/symbol?symbol=CBOE%3AVIX&fields=close,change,high,low,open"]:
    st4, b4 = get(u)
    print(u[:80], "->", st4, b4[:200])
