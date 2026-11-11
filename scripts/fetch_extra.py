# -*- coding: utf-8 -*-
"""拉取估值/情绪/信用类辅助序列：^TNX, HYG, IEF, ^VIX3M, RSP 已有。"""
import urllib.request, json, time, calendar, csv, os, datetime
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(BASE, "data", "raw")
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"}

def fetch(url, timeout=60, retries=3):
    last=None
    for k in range(retries):
        try:
            req=urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=timeout) as f:
                return f.read()
        except Exception as e:
            last=e; time.sleep(1.5*(k+1))
    raise last

def ts(s): return calendar.timegm(time.strptime(s, "%Y-%m-%d"))

def yahoo(sym, start="1988-01-01", end="2026-11-07"):
    url=("https://query1.finance.yahoo.com/v8/finance/chart/%s?period1=%d&period2=%d"
         "&interval=1d&events=div%%2Csplit&includeAdjustedClose=true" % (urllib.parse.quote(sym), ts(start), ts(end)))
    j=json.loads(fetch(url))
    res=j["chart"]["result"][0]
    t=res["timestamp"]; q=res["indicators"]["quote"][0]
    adj=res["indicators"].get("adjclose",[{}])[0].get("adjclose",[None]*len(t))
    rows=[]
    for i,ti in enumerate(t):
        d=(datetime.datetime(1970,1,1)+datetime.timedelta(seconds=int(ti))).strftime("%Y-%m-%d")
        c=q["close"][i]
        if c is None: continue
        rows.append([d,q["open"][i],q["high"][i],q["low"][i],c,adj[i] if adj[i] is not None else c, q["volume"][i] or 0])
    path=os.path.join(RAW,"yahoo_%s.csv" % sym.replace("^","IDX_").replace(".","_"))
    with open(path,"w",newline="",encoding="utf-8") as f:
        w=csv.writer(f); w.writerow(["date","open","high","low","close","adjclose","volume"]); w.writerows(rows)
    print("%-10s rows=%5d %s -> %s" % (sym,len(rows),rows[0][0],rows[-1][0]))

for s in ["^TNX","^VIX3M","HYG","IEF","TLT","^GSPC"]:
    try: yahoo(s)
    except Exception as e: print(s,"FAILED",str(e)[:120])
    time.sleep(0.4)
