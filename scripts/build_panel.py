# -*- coding: utf-8 -*-
"""构建对齐的日频价格矩阵：以六大指数为核心，处理停牌/缺失，输出 processed/prices_daily.csv。"""
import os
import numpy as np, pandas as pd

RAW = r"E:\workspace\new\data\raw"
OUT = r"E:\workspace\new\data\processed"
os.makedirs(OUT, exist_ok=True)

def load_yahoo(name):
    df = pd.read_csv(os.path.join(RAW, "yahoo_%s.csv" % name))
    df["date"] = pd.to_datetime(df["date"])
    df = df.drop_duplicates("date").set_index("date").sort_index()
    return df

files = {
    "SPX":  "IDX_GSPC",
    "DJI":  "IDX_DJI",
    "IXIC": "IDX_IXIC",
    "NDX":  "IDX_NDX",
    "RUT":  "IDX_RUT",
    "SOX":  "IDX_SOX",
}
close, adj, high, low, volume = {}, {}, {}, {}, {}
for k, f in files.items():
    d = load_yahoo(f)
    close[k] = d["close"]
    adj[k] = d["adjclose"]
    high[k] = d["high"]; low[k] = d["low"]; volume[k] = d["volume"]

C = pd.DataFrame(close).sort_index()
A = pd.DataFrame(adj).sort_index()
H = pd.DataFrame(high).sort_index()
L = pd.DataFrame(low).sort_index()
V = pd.DataFrame(volume).sort_index()

# 以交易日历（六指数任一有数据）为基准，检查缺失
print("原始行数:", len(C))
first = {k: C[k].first_valid_index().date() for k in C.columns}
last  = {k: C[k].last_valid_index().date() for k in C.columns}
print("起始:", first)
print("结束:", last)

# 各指数在其上市后的缺失交易日数
cal = C.index
for k in C.columns:
    s = C[k]
    v = s.first_valid_index()
    sub = s.loc[v:]
    miss = sub.isna().sum()
    print("%-5s 有效 %5d  缺失 %3d  占比 %.2f%%" % (k, sub.notna().sum(), miss, miss/len(sub)*100))

# 用前值填充极少量缺失（保留 NaN 在起始段）
C2 = C.ffill(limit=3)
A2 = A.ffill(limit=3)

C2.to_csv(os.path.join(OUT, "prices_close.csv"), encoding="utf-8-sig")
A2.to_csv(os.path.join(OUT, "prices_adjclose.csv"), encoding="utf-8-sig")
H.to_csv(os.path.join(OUT, "prices_high.csv"), encoding="utf-8-sig")
L.to_csv(os.path.join(OUT, "prices_low.csv"), encoding="utf-8-sig")
V.to_csv(os.path.join(OUT, "prices_volume.csv"), encoding="utf-8-sig")

# 宽松口径全样本（六指数都有数据）起点
common_start = max(C[k].first_valid_index() for k in C.columns)
print("\n六指数共同起点:", common_start.date())

# 分红/复权差异（价格指数 vs 总收益指数）
tr = load_yahoo("IDX_SP500TR")["adjclose"]
print("SP500 总收益序列:", tr.index[0].date(), "->", tr.index[-1].date(), "n=", len(tr))
