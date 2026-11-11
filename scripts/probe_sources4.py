# -*- coding: utf-8 -*-
"""第四轮：定位各站真正的数据端点。"""
import json
import re
import urllib.error
import urllib.parse
import urllib.request

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")
PROXY = "http://127.0.0.1:7897"


def get(url, proxy=PROXY, timeout=30, headers=None, data=None):
    h = {"User-Agent": UA, "Accept": "*/*", "Accept-Language": "en-US,en;q=0.9"}
    if headers:
        h.update(headers)
    op = (urllib.request.build_opener(urllib.request.ProxyHandler({"http": proxy, "https": proxy}))
          if proxy else urllib.request.build_opener(urllib.request.ProxyHandler({})))
    req = urllib.request.Request(url, headers=h, data=data)
    try:
        with op.open(req, timeout=timeout) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()[:300]
    except Exception as e:
        return None, str(e).encode()


print("=" * 72)
print("A. investing.com —— 用 instrument 搜索接口找 VIX 的 pair ID")
print("=" * 72)
for q in ["VIX", "CBOE VIX", "Volatility Index"]:
    for path in ["https://api.investing.com/api/search/v2/search?q=%s",
                 "https://api.investing.com/api/financialdata/search/?q=%s",
                 "https://www.investing.com/search/service/searchTopBar/%s"]:
        st, b = get(path % urllib.parse.quote(q), headers={"domain-id": "www"})
        if st == 200 and b[:1] == b"{":
            try:
                d = json.loads(b)
            except Exception:
                continue
            txt = json.dumps(d)[:600]
            if '"pairId"' in txt or '"pair_id"' in txt or '"instrumentId"' in txt:
                print(path % q, "->")
                # 提取候选
                for m in re.finditer(r'\{[^{}]*"(?:pairId|pair_id|instrumentId)"[^{}]*\}', txt):
                    seg = m.group(0)
                    if "iolatility" in seg or "VIX" in seg:
                        print("   ", seg[:200])

print()
print("=" * 72)
print("B. investing.com —— 直接试 VIX 相关 ID（看返回的最后一根 K 线价格能否对上）")
print("=" * 72)
# 已知：VIX 2026-11-06 收 25.64。逐个试 ID，看末值是否接近 25 或 26
cands = [443, 409, 262, 286, 166, 8839, 8859, 8874, 444, 408, 407, 406,
         11905, 11906, 11238, 11239, 132, 222, 237, 238, 250]
for pid in cands:
    u = ("https://api.investing.com/api/financialdata/%d/historical/chart/?period=P1M&interval=P1D" % pid)
    st, b = get(u, headers={"domain-id": "www"})
    if st != 200 or b[:1] != b"{":
        continue
    try:
        d = json.loads(b)
    except Exception:
        continue
    arr = d.get("data") or []
    if arr:
        last = arr[-1]
        print("id=%-6d rows=%-3d last_close=%-10s" % (pid, len(arr), last[4] if len(last) > 4 else "?"))

print()
print("=" * 72)
print("C. vixcentral —— 找 ajax / 数据接口")
print("=" * 72)
st, b = get("https://vixcentral.com/", proxy=None)
t = b.decode("utf-8", "replace")
for pat in [r"\$\.(?:get|post|ajax)\(\s*['\"]([^'\"]+)", r"url\s*:\s*['\"]([^'\"]+)",
            r"fetch\(\s*['\"]([^'\"]+)", r"<form[^>]+action=\"([^\"]+)\""]:
    hits = re.findall(pat, t)
    if hits:
        print(pat, "->", hits[:10])
# 页面里的 select / option 线索
print("\n页面中的 option 值:", re.findall(r'<option[^>]*value="([^"]*)"', t)[:15])
print("\n包含 'ajax' 的片段:")
for m in re.finditer(r".{60}ajax.{80}", t, re.S):
    print("   ", m.group(0).replace("\n", " ")[:170])

print()
print("=" * 72)
print("D. tradingview —— 历史 K 线端点")
print("=" * 72)
for u in ["https://scanner.tradingview.com/cboe/scan",
          "https://symbol-search.tradingview.com/symbol_search/v3/?text=VIX&exchange=CBOE",
          "https://www.tradingview.com/api/v1/symbols/"]:
    st, b = get(u)
    print(u[:70], "->", st, b[:150])
