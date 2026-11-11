# -*- coding: utf-8 -*-
"""多源交叉比对：同一指数在不同数据源之间的收盘价差异。"""
import os, csv, json
import numpy as np, pandas as pd

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(BASE, "data", "raw")

def load_csv(path, datecol="date", valcol="close"):
    df = pd.read_csv(path)
    df[datecol] = pd.to_datetime(df[datecol])
    s = df.set_index(datecol)[valcol].astype(float).sort_index()
    s = s[~s.index.duplicated(keep="last")]
    return s

idx = {}
idx["Yahoo"] = {k: load_csv(os.path.join(RAW, "yahoo_IDX_%s.csv" % k)) for k in ["DJI","IXIC","NDX","RUT","SOX"]}
idx["Yahoo"]["SPX"] = load_csv(os.path.join(RAW, "yahoo_IDX_GSPC.csv"))
idx["Eastmoney"] = {k: load_csv(os.path.join(RAW, "em_%s.csv" % k)) for k in ["SPX","DJI","NDX"]}
idx["Sina"] = {k: load_csv(os.path.join(RAW, "sina_%s.csv" % k)) for k in ["SPX","DJI","IXIC","NDX","SOX"]}
idx["Xueqiu"] = {k: load_csv(os.path.join(RAW, "xq_%s.csv" % k)) for k in ["SPX","DJI","IXIC","NDX","SOX","RUT"]}
idx["Nasdaq"] = {k: load_csv(os.path.join(RAW, "nq_%s.csv" % k)) for k in ["IXIC","NDX"]}
cboe = pd.read_csv(os.path.join(RAW, "cboe_SPX.csv"))
cboe["DATE"] = pd.to_datetime(cboe["DATE"], format="%m/%d/%Y")
idx["CBOE"] = {"SPX": cboe.set_index("DATE")["SPX"].astype(float).sort_index()}

print("=== 各数据源覆盖区间 ===")
for src, d in idx.items():
    for k, s in d.items():
        print("%-10s %-5s n=%5d  %s -> %s" % (src, k, len(s), s.index[0].date(), s.index[-1].date()))

print()
print("=== 与 Yahoo 收盘价的差异（重叠区间，最近 5 年） ===")
ref = idx["Yahoo"]
for src, d in idx.items():
    if src == "Yahoo":
        continue
    for k, s in d.items():
        if k not in ref:
            continue
        r = ref[k]
        both = s.loc["2021-11-08":].index.intersection(r.index)
        if len(both) < 100:
            continue
        a = s.loc[both]; b = r.loc[both]
        diff = (a - b).abs() / b * 100
        print("%-10s %-5s n=%4d  最大偏离 %.3f%%  中位偏离 %.4f%%  末值 源=%.2f  Y=%.2f" %
              (src, k, len(both), diff.max(), diff.median(), a.iloc[-1], b.iloc[-1]))
