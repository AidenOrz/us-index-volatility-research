# -*- coding: utf-8 -*-
"""批量抓 vixcentral 历史期限结构，评估覆盖率：抽样 200 个交易日。"""
import json
import os
import time
import urllib.error
import urllib.request

import pandas as pd

BASE = r"E:\workspace\new"
PROC = os.path.join(BASE, "data", "processed")
OUT = os.path.join(BASE, "data", "output")
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")

px = pd.read_csv(os.path.join(PROC, "prices_close.csv"), index_col=0, parse_dates=True)
idx = px.loc["2005-01-01":"2026-11-06"].index
# 均匀抽样 200 个交易日
sample = idx[:: max(1, len(idx) // 200)][:200]
print("抽样 %d 个交易日 (%s ~ %s)" % (len(sample), sample[0].date(), sample[-1].date()))


def get(url, timeout=15):
    req = urllib.request.Request(url, headers={
        "User-Agent": UA, "X-Requested-With": "XMLHttpRequest",
        "Accept": "application/json", "Referer": "https://vixcentral.com/"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, b""
    except Exception:
        return None, b""


ok, err, empty = [], [], []
rows = []
for i, d in enumerate(sample):
    ds = d.strftime("%Y-%m-%d")
    st, b = get("https://vixcentral.com/ajax_historical?n1=" + ds)
    txt = b.decode("utf-8", "replace") if b else ""
    if txt.startswith("[") and len(txt) > 5:
        try:
            arr = json.loads(txt)
        except Exception:
            err.append(ds); continue
        vals = [v for v in arr[1:] if v > 0]
        if len(vals) >= 2:
            rows.append({"日期": ds, "月份数": arr[0], "合约数_有效": len(vals),
                         "M1": vals[0], "M2": vals[1] if len(vals) > 1 else None,
                         "M3": vals[2] if len(vals) > 2 else None,
                         "M4": vals[3] if len(vals) > 3 else None,
                         "M6": vals[5] if len(vals) > 5 else None,
                         "全曲线": ";".join("%.3f" % v for v in vals)})
            ok.append(ds)
        else:
            empty.append(ds)
    elif '"error"' in txt:
        err.append(ds)
    else:
        empty.append(ds)
    if (i + 1) % 25 == 0:
        print("  进度 %d/%d  成功 %d 错误 %d 空 %d" % (i + 1, len(sample), len(ok), len(err), len(empty)))
    time.sleep(0.18)

print("\n=== 结果 ===")
print("成功 %d / %d = %.1f%%" % (len(ok), len(sample), 100.0 * len(ok) / len(sample)))
print("错误(error) %d，空数据 %d" % (len(err), len(empty)))
print("错误日期示例:", err[:12])
print("空数据示例:", empty[:12])

d_ok = pd.DataFrame(rows)
if len(d_ok):
    d_ok.to_csv(os.path.join(OUT, "vc_curve_test.csv"), index=False, encoding="utf-8-sig")
    print("\n成功样本前 5 行:")
    print(d_ok.head(5).to_string(index=False))
    # 按年份统计覆盖率
    d_ok["年"] = d_ok["日期"].str[:4]
    cnt = d_ok.groupby("年").size()
    print("\n分年成功数:")
    print(cnt.to_string())
