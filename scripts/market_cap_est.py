# -*- coding: utf-8 -*-
"""用抽样成分股的真实市值反推各指数总市值，估计市值覆盖。"""
import os, re, json, time, csv
import urllib.request
import pandas as pd, numpy as np

RAW = r"E:\workspace\new\data\raw"; PROC = r"E:\workspace\new\data\processed"; OUT = r"E:\workspace\new\data\output"
UA = {"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"}
CACHE = os.path.join(RAW, "shares_cache.json")
cache = json.load(open(CACHE)) if os.path.exists(CACHE) else {}

def shares(tk):
    tk = tk.strip().strip('"')
    if tk in cache and cache[tk]:
        return cache[tk]
    u = "https://stockanalysis.com/stocks/%s/statistics/" % tk.lower().replace(".", "-")
    for k in range(2):
        try:
            with urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=15) as f:
                h = f.read().decode("utf-8", "ignore")
            m = re.search(r'<span><!---->Shares Outstanding<!----></span>.*?title="([\d,]+)"', h, re.S)
            v = float(m.group(1).replace(",", "")) if m else None
            cache[tk] = v
            return v
        except Exception:
            time.sleep(1)
    cache[tk] = None
    return None

def load(n):
    lines = open(os.path.join(RAW, n+"_holdings.txt"), encoding="utf-8", errors="ignore").read().splitlines()
    hi = next(i for i,l in enumerate(lines) if l.startswith("Ticker,Name,"))
    rows = list(csv.reader(lines[hi:]))
    df = pd.DataFrame([r[:len(rows[0])] for r in rows[1:] if len(r) >= len(rows[0])], columns=rows[0])
    w = df["Weight (%)"] if "Weight (%)" in df.columns else df["Market Weight"]
    df["W"] = pd.to_numeric(w.astype(str).str.replace(",",""), errors="coerce")
    df["P"] = pd.to_numeric(df["Price"].astype(str).str.replace(",",""), errors="coerce")
    return df[df["Asset Class"].str.contains("Equity", na=False)].copy()

FUNDS = [("IVV","标普500"), ("IWM","罗素2000"), ("SOXX","费城半导体"), ("IWF","罗素1000成长"), ("IWD","罗素1000价值")]
res = []
for n, label in FUNDS:
    d = load(n).nlargest(15, "W")
    ests = []
    for _, r in d.iterrows():
        s = shares(r["Ticker"])
        if not s or not r["P"] or s <= 0: continue
        mcap = s * r["P"]
        ests.append(mcap / (r["W"]/100))
        time.sleep(0.15)
    if not ests:
        print(label, "no data"); continue
    e = np.array(ests)
    tot = np.median(e)
    res.append(dict(指数=label, 抽样数=len(ests), 估算总市值万亿美元=round(tot/1e12,2),
                    抽样离散度=round(np.std(e)/np.mean(e)*100,1),
                    中位成分市值十亿美元=round(tot/len(load(n))/1e9,2)))
    print(label, "n=%d 总值 %.2f 万亿, 离散 %.1f%%" % (len(ests), tot/1e12, np.std(e)/np.mean(e)*100), flush=True)

json.dump(cache, open(CACHE, "w"), indent=1)
df = pd.DataFrame(res)
df.to_csv(os.path.join(OUT, "market_cap_est.csv"), index=False, encoding="utf-8-sig")
print(df.to_string())
