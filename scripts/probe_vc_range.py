# -*- coding: utf-8 -*-
"""系统探测 vixcentral /ajax_historical 的可回溯范围与返回格式。"""
import json
import time
import urllib.error
import urllib.request

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")


def get(url, timeout=20):
    req = urllib.request.Request(url, headers={
        "User-Agent": UA, "X-Requested-With": "XMLHttpRequest",
        "Accept": "application/json", "Referer": "https://vixcentral.com/"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()[:200]
    except Exception as e:
        return None, str(e).encode()


print("=== 逐年抽样，看哪些年有数据 ===")
for y in range(2004, 2027):
    d = "%d-06-15" % y
    st, b = get("https://vixcentral.com/ajax_historical?n1=" + d)
    txt = b.decode("utf-8", "replace") if b else ""
    ok = txt.startswith("[") and len(txt) > 20 and '"error"' not in txt
    print("  %s -> %s  %s" % (d, st, txt[:100] if ok else ("(err)" if txt == '"error"' else txt[:60])))
    time.sleep(0.25)

print()
print("=== 数据格式说明（已知样例）===")
for d in ["2026-11-06", "2020-03-16", "2008-10-10", "2011-08-08"]:
    st, b = get("https://vixcentral.com/ajax_historical?n1=" + d)
    txt = b.decode("utf-8", "replace")
    print("  %s -> %s" % (d, txt))
    if txt.startswith("["):
        try:
            arr = json.loads(txt)
            print("     解析: 月份数=%s, 合约价=%s" % (arr[0], arr[1:]))
        except Exception as e:
            print("     parse fail", e)
    time.sleep(0.2)
