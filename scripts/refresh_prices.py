# -*- coding: utf-8 -*-
"""把价格数据补到最新交易日（2026-11-09），并核对是否新增了交易日。"""
import json
import os
import urllib.error
import urllib.request

import pandas as pd

BASE = r"E:\workspace\new"
PROC = os.path.join(BASE, "data", "processed")
RAW = os.path.join(BASE, "data", "raw")
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")
PROXY = "http://127.0.0.1:7897"
SYMS = {"SPX": "%5EGSPC", "DJI": "%5EDJI", "IXIC": "%5EIXIC",
        "NDX": "%5ENDX", "RUT": "%5ERUT", "SOX": "%5ESOX"}


def get(url, timeout=30):
    op = urllib.request.build_opener(urllib.request.ProxyHandler({"http": PROXY, "https": PROXY}))
    req = urllib.request.Request(url, headers={
        "User-Agent": UA, "Accept": "application/json", "Accept-Language": "en-US,en;q=0.9"})
    with op.open(req, timeout=timeout) as r:
        return json.loads(r.read())


cur = pd.read_csv(os.path.join(PROC, "prices_close.csv"), index_col=0, parse_dates=True)
print("现有 prices_close:", cur.shape, cur.index.min().date(), "~", cur.index.max().date())

new = {}
for k, sym in SYMS.items():
    u = "https://query1.finance.yahoo.com/v8/finance/chart/%s?range=1mo&interval=1d" % sym
    try:
        d = get(u)["chart"]["result"][0]
        ts = d["timestamp"]
        cl = d["indicators"]["quote"][0]["close"]
        # Yahoo 时间戳是美东开盘时间（13:30/14:30 UTC），需按美东日期转换
        idx = pd.to_datetime(ts, unit="s", utc=True).tz_convert("America/New_York").normalize().tz_localize(None)
        s = pd.Series(cl, index=idx).dropna()
        new[k] = s
        print("  %-5s 最新 %s = %.2f" % (k, s.index[-1].date(), s.iloc[-1]))
    except Exception as e:
        print("  %-5s ERR %s" % (k, e))

add = pd.DataFrame(new)
add = add[add.index > cur.index.max()]
print("\n新增交易日:", [str(d.date()) for d in add.index])
if len(add):
    merged = pd.concat([cur, add]).sort_index()
    merged = merged[~merged.index.duplicated(keep="last")]
    merged.to_csv(os.path.join(PROC, "prices_close.csv"), encoding="utf-8")
    print("已更新 prices_close.csv ->", merged.shape, merged.index.max().date())
    print(merged.tail(3).round(2).to_string())
else:
    print("无需更新")
