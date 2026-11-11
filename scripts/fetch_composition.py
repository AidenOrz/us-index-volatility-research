# -*- coding: utf-8 -*-
"""抓取指数成分、权重与行业结构数据（slickcharts / Wikipedia / iShares）。"""
import urllib.request, json, time, os, re
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(BASE, "data", "raw")
os.makedirs(RAW, exist_ok=True)
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"}
def fetch(url, timeout=60, retries=3):
    last=None
    for k in range(retries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout) as f:
                return f.read()
        except Exception as e:
            last=e; time.sleep(2*(k+1))
    raise last

targets = {
 "slick_sp500": "https://www.slickcharts.com/sp500",
 "slick_ndx": "https://www.slickcharts.com/nasdaq100",
 "wiki_sp500": "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies",
 "wiki_ndx": "https://en.wikipedia.org/wiki/Nasdaq-100",
 "wiki_sox": "https://en.wikipedia.org/wiki/PHLX_Semiconductor_Sector_index",
 "wiki_rut": "https://en.wikipedia.org/wiki/Russell_2000_Index",
 "wiki_dji": "https://en.wikipedia.org/wiki/Dow_Jones_Industrial_Average",
 "ishares_iwm": "https://www.ishares.com/us/products/239710/ishares-russell-2000-etf",
}
for name, url in targets.items():
    try:
        d = fetch(url, timeout=60)
        with open(os.path.join(RAW, name + ".html"), "wb") as f:
            f.write(d)
        print(name, len(d))
    except Exception as e:
        print(name, "ERR", type(e).__name__, str(e)[:80])
    time.sleep(1.0)
