# -*- coding: utf-8 -*-
"""用 TradingView scanner 做第三方独立快照（无法取历史，只取当期），
并与 CBOE / Yahoo 三源比对当期读数。
产出：
  data/output/tv_snapshot.csv      TradingView 当期读数
  data/output/vol_three_source.csv 三源当期比对
"""
import json
import os
import urllib.error
import urllib.request

import pandas as pd

BASE = r"E:\workspace\new"
RAW = os.path.join(BASE, "data", "raw", "cboe_vol")
OUT = os.path.join(BASE, "data", "output")
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")
PROXY = "http://127.0.0.1:7897"


def get(url, timeout=30, headers=None, data=None):
    h = {"User-Agent": UA, "Accept": "application/json", "Accept-Language": "en-US,en;q=0.9"}
    if headers:
        h.update(headers)
    op = urllib.request.build_opener(urllib.request.ProxyHandler({"http": PROXY, "https": PROXY}))
    try:
        with op.open(urllib.request.Request(url, headers=h, data=data), timeout=timeout) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()[:300]
    except Exception as e:
        return None, str(e).encode()


SYMS = {
    "VIX": "CBOE:VIX", "VXN": "CBOE:VXN", "RVX": "CBOE:RVX",
    "VIX3M": "CBOE:VIX3M", "VIX9D": "CBOE:VIX9D", "VIX6M": "CBOE:VIX6M",
    "VVIX": "CBOE:VVIX", "SKEW": "CBOE:SKEW",
}
COLS = ["name", "close", "change", "high", "low", "open", "Perf.W", "Perf.M", "RSI"]

tv = {}
for market in ["america", "cboe", "global"]:
    body = json.dumps({"symbols": {"tickers": list(SYMS.values()), "query": {"types": []}},
                       "columns": COLS}).encode()
    st, b = get("https://scanner.tradingview.com/%s/scan" % market, 40,
                headers={"Content-Type": "application/json"}, data=body)
    print("TradingView scanner [%s] -> %s" % (market, st))
    if st != 200:
        print("   body:", b[:160])
        continue
    for x in json.loads(b).get("data", []):
        code = x["s"].split(":")[1]
        if code in tv:
            continue
        r = dict(zip(COLS, x["d"]))
        tv[code] = r
        print("   %-8s close=%s chg=%s RSI=%s" % (code, r.get("close"), r.get("change"), r.get("RSI")))

# 缺失的逐个用 symbol 端点补齐
for code in SYMS:
    if code in tv:
        continue
    u = "https://scanner.tradingview.com/symbol?symbol=CBOE%%3A%s&fields=close,change,high,low,open,RSI" % code
    st3, b3 = get(u, 25)
    if st3 == 200 and b3[:1] == b"{":
        try:
            r = json.loads(b3)
            r["name"] = code
            tv[code] = r
            print("   [single] %-8s close=%s" % (code, r.get("close")))
        except Exception:
            pass
    else:
        print("   [single] %-8s -> %s" % (code, st3))

df_tv = pd.DataFrame([{"代码": k, **v} for k, v in tv.items()])
df_tv.to_csv(os.path.join(OUT, "tv_snapshot.csv"), index=False, encoding="utf-8-sig")

# ---------- 三源比对：CBOE CSV / Yahoo / TradingView ----------
print("\n=== 三源当期比对 ===")
rows = []
for code in SYMS:
    cboe_last = None
    p = os.path.join(RAW, code + "_History.csv")
    if os.path.exists(p):
        d = pd.read_csv(p)
        col = "CLOSE" if "CLOSE" in d.columns else d.columns[-1]
        cboe_last = float(d[col].iloc[-1])
    tvl = tv.get(code, {}).get("close")
    rows.append({"指标": code, "CBOE官方": cboe_last, "TradingView": tvl,
                 "差值": (None if (cboe_last is None or tvl is None) else round(float(tvl) - cboe_last, 4))})
cmp = pd.DataFrame(rows)
cmp.to_csv(os.path.join(OUT, "vol_three_source.csv"), index=False, encoding="utf-8-sig")
print(cmp.to_string(index=False))

# ---------- Yahoo 当日 ----------
print("\n=== Yahoo 当日（2026-11-09）===")
import datetime
for code in ["VIX", "VIX3M", "VIX9D", "VIX6M", "VVIX", "SKEW"]:
    u = ("https://query1.finance.yahoo.com/v8/finance/chart/%%5E%s?range=5d&interval=1d" % code)
    st2, b2 = get(u)
    if st2 == 200:
        try:
            d = json.loads(b2)["chart"]["result"][0]
            ts = d["timestamp"][-1]
            c = d["indicators"]["quote"][0]["close"][-1]
            print("  %-7s %s  %.4f" % (code, datetime.datetime.utcfromtimestamp(ts).strftime("%Y-%m-%d"), c))
        except Exception as e:
            print("  ", code, "parse fail", e)
