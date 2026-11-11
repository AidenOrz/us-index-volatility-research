# -*- coding: utf-8 -*-
import os
import numpy as np, pandas as pd
RAW = r"E:\workspace\new\data\raw"
def load(path):
    df = pd.read_csv(path); df["date"] = pd.to_datetime(df["date"])
    s = df.set_index("date")["close"].astype(float).sort_index()
    return s[~s.index.duplicated(keep="last")]

y = load(os.path.join(RAW, "yahoo_IDX_GSPC.csv"))
c = pd.read_csv(os.path.join(RAW, "cboe_SPX.csv"))
c["DATE"] = pd.to_datetime(c["DATE"], format="%m/%d/%Y")
c = c.set_index("DATE")["SPX"].astype(float).sort_index()

print("Yahoo tail:"); print(y.tail(8))
print("CBOE tail:"); print(c.tail(8))

# 同一交易日对比（去掉 Yahoo 的 11-07 行）
both = y.index.intersection(c.index)
r = (y.loc[both] / c.loc[both] - 1) * 100
print("\n比值偏离(%)统计（全样本）:")
print(r.describe())
print("\n按年抽样:")
print(r.resample("YE").agg(["median", "max", "min", "count"]).tail(12).round(3))

# 收益率相关性
ry = y.loc[both].pct_change(); rc = c.loc[both].pct_change()
print("\n日收益相关性:", round(ry.corr(rc), 4), " 不同日相关(错位1日):", round(ry.corr(rc.shift(1)), 4))
print("最近10天：Yahoo vs CBOE")
tail = both[-10:]
print(pd.DataFrame({"yahoo": y.loc[tail], "cboe": c.loc[tail], "diff_pct": r.loc[tail].round(3)}))
