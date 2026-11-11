# -*- coding: utf-8 -*-
"""核对：各指数是否在上市日之前就有数据（Yahoo 的起始点是否可信）+ 检查异常跳变。"""
import os
import numpy as np, pandas as pd
RAW = r"E:\workspace\new\data\raw"
OUT = r"E:\workspace\new\data\processed"
C = pd.read_csv(os.path.join(OUT, "prices_close.csv"), index_col=0, parse_dates=True)

# 已知指数发布日
launch = {"SPX":"1957-03-04","DJI":"1896-05-26","IXIC":"1971-02-05","NDX":"1985-10-01","RUT":"1984-01-01","SOX":"1993-12-01"}
for k,v in launch.items():
    print("%-5s 官方发布 %s  数据起始 %s  差 %.1f 年" % (k, v, C[k].first_valid_index().date(),
        (C[k].first_valid_index() - pd.Timestamp(v)).days/365.25))

# 异常跳变检查（|日收益| > 20%，除 1987 崩盘外都异常）
r = C.pct_change()
print("\n单日涨跌超过 15% 的记录:")
big = r[(r.abs() > 0.15).any(axis=1)]
for dt, row in big.iterrows():
    vals = {k: round(row[k]*100,2) for k in row.index if pd.notna(row[k]) and abs(row[k])>0.15}
    print(" ", dt.date(), vals)

# 每年交易日数 vs 美股实际
cnt = C["SPX"].dropna().groupby(C["SPX"].dropna().index.year).size()
print("\nSPX 每年交易日数（检查是否有断档）:")
print(cnt.loc[[1987,1988,1994,2000,2008,2020,2026]].to_string())
print("异常年份:", cnt[cnt < 240].index.tolist()[:20])
