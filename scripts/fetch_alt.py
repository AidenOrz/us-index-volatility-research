# -*- coding: utf-8 -*-
"""抓取多源交叉比对数据：东方财富 / 新浪 / 雪球 / CBOE / Nasdaq / 美国财政部。"""
import urllib.request, urllib.parse, json, time, calendar, csv, os, http.cookiejar, re

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(BASE, "data", "raw")
os.makedirs(RAW, exist_ok=True)
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"}

def fetch(url, timeout=60, retries=3, headers=None):
    h = dict(UA); h.update(headers or {})
    last = None
    for k in range(retries):
        try:
            req = urllib.request.Request(url, headers=h)
            with urllib.request.urlopen(req, timeout=timeout) as f:
                return f.read()
        except Exception as e:
            last = e
            time.sleep(1.5 * (k + 1))
    raise last

def save(name, data):
    p = os.path.join(RAW, name)
    with open(p, "wb") as f:
        f.write(data)
    return p

# ---------- 1. 东方财富 ----------
EM = {"SPX": "100.SPX", "DJI": "100.DJIA", "IXIC": "105.IXIC", "NDX": "100.NDX",
      "NDX100": "100.NDX100", "SOX": "251.SOX"}
for name, sec in EM.items():
    url = ("https://push2his.eastmoney.com/api/qt/stock/kline/get?secid=%s"
           "&fields1=f1&fields2=f51,f53&klt=101&fqt=0&beg=19600101&end=20500101&lmt=30000" % sec)
    try:
        d = fetch(url)
        j = json.loads(d)
        kl = (j.get("data") or {}).get("klines") or []
        if not kl:
            print("EM", name, "EMPTY")
            continue
        p = os.path.join(RAW, "em_%s.csv" % name)
        with open(p, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f); w.writerow(["date", "close"])
            for row in kl:
                dt, c = row.split(",")[:2]
                w.writerow([dt, c])
        print("EM", name, len(kl), kl[0][:10], "->", kl[-1][:10])
    except Exception as e:
        print("EM", name, "ERR", type(e).__name__, str(e)[:80])
    time.sleep(0.6)

# IWM 作为罗素2000代理
url = ("https://push2his.eastmoney.com/api/qt/stock/kline/get?secid=107.IWM"
       "&fields1=f1&fields2=f51,f53&klt=101&fqt=1&beg=19600101&end=20500101&lmt=30000")
try:
    j = json.loads(fetch(url)); kl = j["data"]["klines"]
    with open(os.path.join(RAW, "em_IWM.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(["date", "close"])
        for row in kl:
            dt, c = row.split(",")[:2]; w.writerow([dt, c])
    print("EM IWM", len(kl), kl[0][:10], "->", kl[-1][:10])
except Exception as e:
    print("EM IWM ERR", type(e).__name__, str(e)[:80])

# ---------- 2. 新浪 ----------
for sym, name in [(".INX", "SPX"), (".DJI", "DJI"), (".IXIC", "IXIC"),
                  (".NDX", "NDX"), (".SOX", "SOX")]:
    url = ("https://stock.finance.sina.com.cn/usstock/api/jsonp.php/var%%20t=/"
           "US_MinKService.getDailyK?symbol=%s&___qn=3" % sym)
    try:
        txt = fetch(url, headers={"Referer": "https://finance.sina.com.cn"}).decode("utf-8", "ignore")
        m = re.search(r"var t=\((\[.*\])\);", txt, re.S)
        arr = json.loads(m.group(1))
        rows = [[x["d"], x["c"]] for x in arr]
        with open(os.path.join(RAW, "sina_%s.csv" % name), "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f); w.writerow(["date", "close"]); w.writerows(rows)
        print("SINA", name, len(rows), rows[0][0], "->", rows[-1][0])
    except Exception as e:
        print("SINA", name, "ERR", type(e).__name__, str(e)[:80])
    time.sleep(0.5)

# ---------- 3. 雪球 ----------
cj = http.cookiejar.CookieJar()
op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
op.addheaders = list(UA.items())
try:
    op.open("https://xueqiu.com/", timeout=30).read()
except Exception:
    pass
def xq(sym, count=-10000):
    url = ("https://stock.xueqiu.com/v5/stock/chart/kline.json?symbol=%s&begin=%d"
           "&period=day&type=before&count=%d&indicator=kline" % (sym, int(time.time() * 1000), count))
    req = urllib.request.Request(url, headers=dict(UA, Referer="https://xueqiu.com/"))
    j = json.loads(op.open(req, timeout=60).read())
    it = (j.get("data") or {}).get("item") or []
    rows = [[time.strftime("%Y-%m-%d", time.localtime(r[0] / 1000)), r[5]] for r in it]
    rows.sort()
    return rows

for sym, name in [(".DJI", "DJI"), (".INX", "SPX"), (".IXIC", "IXIC"),
                  (".NDX", "NDX"), (".SOX", "SOX"), ("RUT", "RUT")]:
    try:
        rows = xq(sym)
        if not rows:
            print("XQ", name, "EMPTY"); continue
        with open(os.path.join(RAW, "xq_%s.csv" % name), "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f); w.writerow(["date", "close"]); w.writerows(rows)
        print("XQ", name, len(rows), rows[0][0], "->", rows[-1][0])
    except Exception as e:
        print("XQ", name, "ERR", type(e).__name__, str(e)[:80])
    time.sleep(0.6)
