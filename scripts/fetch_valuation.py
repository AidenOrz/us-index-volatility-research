# -*- coding: utf-8 -*-
"""下载 multpl 各月度估值表 + Shiller 原始数据，按明确文件名存盘。"""
import urllib.request, os, time
BASE = r"E:\workspace\new"; RAW = os.path.join(BASE, "data", "raw")
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"}
TARGETS = {
    "multpl_cape": "https://www.multpl.com/shiller-pe/table/by-month",
    "multpl_pe": "https://www.multpl.com/s-p-500-pe-ratio/table/by-month",
    "multpl_dy": "https://www.multpl.com/s-p-500-dividend-yield/table/by-month",
    "multpl_ey": "https://www.multpl.com/s-p-500-earnings-yield/table/by-month",
    "multpl_pb": "https://www.multpl.com/s-p-500-price-to-book-value/table/by-month",
    "multpl_sales": "https://www.multpl.com/s-p-500-price-to-sales-ratio/table/by-month",
    "shiller_xls": "http://www.econ.yale.edu/~shiller/data/ie_data.xls",
}
for name, url in TARGETS.items():
    ext = ".xls" if url.endswith(".xls") else ".html"
    path = os.path.join(RAW, name + ext)
    try:
        req = urllib.request.Request(url, headers=UA)
        with urllib.request.urlopen(req, timeout=60) as f:
            body = f.read()
        open(path, "wb").write(body)
        print("%-14s %8d bytes -> %s" % (name, len(body), os.path.basename(path)))
    except Exception as e:
        print("%-14s FAILED %s" % (name, str(e)[:100]))
    time.sleep(0.6)
