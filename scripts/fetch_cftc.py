# -*- coding: utf-8 -*-
"""从 CFTC Socrata 拉 VIX 期货 COT 持仓数据（独立于价格数据的第三方源）。
产出：
  data/raw/cftc_vix_cot.csv        VIX 期货持仓（Legacy Futures Only）
  data/output/cftc_vix_meta.csv    字段与覆盖说明
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
os.makedirs(RAW, exist_ok=True)


def get_json(url, proxy=PROXY, timeout=60, tries=3):
    op = urllib.request.build_opener(urllib.request.ProxyHandler({"http": proxy, "https": proxy})) \
        if proxy else urllib.request.build_opener(urllib.request.ProxyHandler({}))
    last = None
    for i in range(tries):
        req = urllib.request.Request(url, headers={
            "User-Agent": UA, "Accept": "application/json", "Accept-Language": "en-US,en;q=0.9"})
        try:
            with op.open(req, timeout=timeout) as r:
                return json.loads(r.read())
        except Exception as e:
            last = e
            time.sleep(1.5 * (i + 1))
    raise RuntimeError("fetch failed: %s (%s)" % (url[:90], last))


# ---------- 1) VIX 期货 Legacy Futures Only ----------
print("=== 1. VIX FUTURES COT (Legacy, Futures Only, 6dca-aqww) ===")
BASE_Q = "https://publicreporting.cftc.gov/resource/6dca-aqww.json"
where = urllib.parse.quote("market_and_exchange_names='VIX FUTURES - CBOE FUTURES EXCHANGE'")
order = urllib.parse.quote("report_date_as_yyyy_mm_dd ASC")
rows = []
offset = 0
PAGE = 1000
while True:
    url = ("%s?$where=%s&$order=%s&$limit=%d&$offset=%d"
           % (BASE_Q, where, order, PAGE, offset))
    arr = get_json(url)
    if not arr:
        break
    rows.extend(arr)
    print("  fetched %d (total %d)" % (len(arr), len(rows)))
    if len(arr) < PAGE:
        break
    offset += PAGE
    time.sleep(0.3)

print("  共 %d 行" % len(rows))
if not rows:
    raise SystemExit("no rows")

df = pd.DataFrame(rows)
df.to_csv(os.path.join(RAW, "cftc_vix_cot.csv"), index=False, encoding="utf-8-sig")
print("  字段 %d 个：" % len(df.columns))
print("  ", sorted(df.columns))

# ---------- 2) 元数据 ----------
meta = pd.DataFrame([
    {"项目": "数据源", "值": "CFTC Public Reporting Environment (Socrata)"},
    {"项目": "数据集", "值": "6dca-aqww = Legacy - Futures Only"},
    {"项目": "合约", "值": "VIX FUTURES - CBOE FUTURES EXCHANGE"},
    {"项目": "行数", "值": str(len(df))},
    {"项目": "起始报告日", "值": str(pd.to_datetime(df["report_date_as_yyyy_mm_dd"]).min().date())},
    {"项目": "最新报告日", "值": str(pd.to_datetime(df["report_date_as_yyyy_mm_dd"]).max().date())},
    {"项目": "报告频率", "值": "每周二收盘，周五 15:30 ET 发布（有 3 天滞后）"},
    {"项目": "口径", "值": "非商业(Non-commercial)=投机/基金；商业(Commercial)=套保；Legacy 旧版分类"},
])
meta.to_csv(os.path.join(OUT, "cftc_vix_meta.csv"), index=False, encoding="utf-8-sig")
print("\n元数据：")
print(meta.to_string(index=False))

print("\n最近 3 期：")
cols = [c for c in ["report_date_as_yyyy_mm_dd", "open_interest_all",
                    "noncomm_positions_long_all", "noncomm_positions_short_all",
                    "noncomm_postions_spread_all", "comm_positions_long_all",
                    "comm_positions_short_all", "change_in_noncomm_long_all",
                    "change_in_noncomm_short_all", "pct_of_oi_noncomm_long_all",
                    "pct_of_oi_noncomm_short_all", "traders_noncomm_long_all",
                    "traders_noncomm_short_all"] if c in df.columns]
print(df[cols].tail(3).to_string(index=False))
