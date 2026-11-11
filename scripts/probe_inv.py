# -*- coding: utf-8 -*-
"""用 instrumentId=44336 验证 investing.com VIX 历史数据接口。"""
import json
import urllib.error
import urllib.request

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")
PROXY = "http://127.0.0.1:7897"


def get(url, proxy=PROXY, timeout=30, headers=None):
    h = {"User-Agent": UA, "Accept": "application/json, text/plain, */*",
         "Accept-Language": "en-US,en;q=0.9", "domain-id": "www"}
    if headers:
        h.update(headers)
    op = (urllib.request.build_opener(urllib.request.ProxyHandler({"http": proxy, "https": proxy}))
          if proxy else urllib.request.build_opener(urllib.request.ProxyHandler({})))
    try:
        with op.open(urllib.request.Request(url, headers=h), timeout=timeout) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()[:300]
    except Exception as e:
        return None, str(e).encode()


print("=" * 70)
print("A. instrumentId=44336 (VIX) 各种 period")
print("=" * 70)
PID = 44336
for period, interval in [("P5D", "P1D"), ("P1M", "P1D"), ("P1Y", "P1D"),
                         ("P5Y", "P1D"), ("MAX", "P1D"), ("MAX", "P1M")]:
    u = ("https://api.investing.com/api/financialdata/%d/historical/chart/?period=%s&interval=%s"
         % (PID, period, interval))
    st, b = get(u)
    if st == 200 and b[:1] == b"{":
        d = json.loads(b)
        arr = d.get("data") or []
        if arr:
            import datetime
            def fmt(row):
                return datetime.datetime.utcfromtimestamp(row[0] / 1000).strftime("%Y-%m-%d")
            print("  %-5s %-5s rows=%-5d  %s ~ %s   last_close=%s" % (
                period, interval, len(arr), fmt(arr[0]), fmt(arr[-1]),
                arr[-1][4] if len(arr[-1]) > 4 else "?"))
        else:
            print("  %-5s %-5s 空  %s" % (period, interval, b[:200]))
    else:
        print("  %-5s %-5s -> %s %s" % (period, interval, st, b[:120]))

print()
print("=" * 70)
print("B. 取 MAX 全历史，检查与 CBOE 官方是否一致")
print("=" * 70)
u = ("https://api.investing.com/api/financialdata/%d/historical/chart/?period=MAX&interval=P1M" % PID)
st, b = get(u)
if st == 200:
    d = json.loads(b)
    arr = d.get("data") or []
    print("行数:", len(arr), "字段数:", len(arr[0]) if arr else 0)
    print("前 2 行:", arr[:2])
    print("末 3 行:", arr[-3:])
