# -*- coding: utf-8 -*-
"""拉 CFTC TFF（Traders in Financial Futures）口径的 VIX 期货持仓。
TFF 比 Legacy 更细：Dealer/Intermediary、Asset Manager/Institutional、
Leveraged Funds、Other Reportables —— 对波动率交易者的刻画更准。
产出 data/raw/cftc_vix_tff.csv
"""
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request

import pandas as pd

BASE = r"E:\workspace\new"
RAW = os.path.join(BASE, "data", "raw")
OUT = os.path.join(BASE, "data", "output")
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")
PROXY = "http://127.0.0.1:7897"


def get_json(url, timeout=60, tries=3):
    op = urllib.request.build_opener(urllib.request.ProxyHandler({"http": PROXY, "https": PROXY}))
    last = None
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={
                "User-Agent": UA, "Accept": "application/json"})
            with op.open(req, timeout=timeout) as r:
                return json.loads(r.read())
        except Exception as e:
            last = e
            time.sleep(1.5 * (i + 1))
    raise RuntimeError("fail %s (%s)" % (url[:100], last))


# gpe5-46if = TFF - Futures Only
BASE_Q = "https://publicreporting.cftc.gov/resource/gpe5-46if.json"
where = urllib.parse.quote("market_and_exchange_names='VIX FUTURES - CBOE FUTURES EXCHANGE'")
order = urllib.parse.quote("report_date_as_yyyy_mm_dd ASC")
rows, offset, PAGE = [], 0, 1000
while True:
    url = "%s?$where=%s&$order=%s&$limit=%d&$offset=%d" % (BASE_Q, where, order, PAGE, offset)
    arr = get_json(url)
    if not arr:
        break
    rows.extend(arr)
    print("  TFF fetched %d (total %d)" % (len(arr), len(rows)))
    if len(arr) < PAGE:
        break
    offset += PAGE
    time.sleep(0.3)

print("TFF 共 %d 行" % len(rows))
df = pd.DataFrame(rows)
df.to_csv(os.path.join(RAW, "cftc_vix_tff.csv"), index=False, encoding="utf-8-sig")

# 挑出 TFF 特有列
tff_cols = [c for c in df.columns if any(k in c for k in
            ["dealer", "asset_mgr", "lev_money", "other_rept"])]
print("TFF 专属列 %d 个:" % len(tff_cols))
for c in sorted(tff_cols):
    print("   ", c)

key = ["report_date_as_yyyy_mm_dd", "open_interest_all"] + sorted(tff_cols)[:6]
print("\n最近 2 期:")
print(df[[c for c in key if c in df.columns]].tail(2).to_string(index=False))
