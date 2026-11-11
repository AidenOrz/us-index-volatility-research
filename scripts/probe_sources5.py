# -*- coding: utf-8 -*-
"""第五轮：vixcentral 内部 ajax 接口实测 + investing 搜索实证。"""
import json
import urllib.error
import urllib.parse
import urllib.request

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")
PROXY = "http://127.0.0.1:7897"


def get(url, proxy=None, timeout=30, headers=None, data=None, method=None):
    h = {"User-Agent": UA, "Accept": "application/json, text/javascript, */*; q=0.01",
         "Accept-Language": "en-US,en;q=0.9",
         "X-Requested-With": "XMLHttpRequest",
         "Referer": "https://vixcentral.com/"}
    if headers:
        h.update(headers)
    op = (urllib.request.build_opener(urllib.request.ProxyHandler({"http": proxy, "https": proxy}))
          if proxy else urllib.request.build_opener(urllib.request.ProxyHandler({})))
    req = urllib.request.Request(url, headers=h, data=data, method=method)
    try:
        with op.open(req, timeout=timeout) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()[:300]
    except Exception as e:
        return None, str(e).encode()


print("=" * 72)
print("A. vixcentral /ajax_update  （实时 VIX 期货曲线）")
print("=" * 72)
for proxy in [None, PROXY]:
    st, b = get("https://vixcentral.com/ajax_update", proxy=proxy)
    print(("直连" if proxy is None else "代理"), "->", st, "len", len(b) if b else 0)
    if st == 200 and b:
        try:
            d = json.loads(b)
            print("   顶层类型:", type(d).__name__, "长度", len(d) if hasattr(d, "__len__") else "-")
            print("   内容:", json.dumps(d)[:800])
        except Exception as e:
            print("   parse fail:", e, b[:300])
    print()

print("=" * 72)
print("B. vixcentral /ajax_historical  （历史某一天的完整期限结构）")
print("=" * 72)
for dt in ["2026-11-06", "2020-03-16", "2008-10-10"]:
    for params in [{"n1": dt}, {"n1": dt.replace("-", "/")}, {"d": dt}]:
        st, b = get("https://vixcentral.com/ajax_historical?" + urllib.parse.urlencode(params), proxy=None)
        if st == 200 and b and b[:1] in (b"[", b"{"):
            print(dt, params, "->", st, "len", len(b))
            print("   ", b[:600])
            break
    else:
        print(dt, "全部失败")

print()
print("=" * 72)
print("C. vixcentral /ajax_get_contango_data")
print("=" * 72)
for proxy in [None, PROXY]:
    st, b = get("https://vixcentral.com/ajax_get_contango_data", proxy=proxy)
    print(("直连" if proxy is None else "代理"), "->", st, "len", len(b) if b else 0, b[:400])
