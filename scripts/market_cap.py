# -*- coding: utf-8 -*-
"""计算各指数的成分股总市值（sum of 总股本×价格），用于市值覆盖分析。"""
import os, re, json, time, csv, random
import urllib.request
import pandas as pd, numpy as np

RAW = r"E:\workspace\new\data\raw"; PROC = r"E:\workspace\new\data\processed"; OUT = r"E:\workspace\new\data\output"
UA = {"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"}
CACHE = os.path.join(RAW, "shares_cache.json")
cache = json.load(open(CACHE)) if os.path.exists(CACHE) else {}

def shares(tk):
    tk = str(tk).strip().strip('"')
    if tk in cache and cache[tk]:
        return cache[tk]
    u = "https://stockanalysis.com/stocks/%s/statistics/" % tk.lower().replace(".", "-").replace(" ", "-")
    v = None
    for k in range(2):
        try:
            with urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=12) as f:
                h = f.read().decode("utf-8", "ignore")
            m = re.search(r'<span><!---->Shares Outstanding<!----></span>.*?title="([\d,]+)"', h, re.S)
            v = float(m.group(1).replace(",", "")) if m else None
            break
        except Exception:
            time.sleep(0.6)
    cache[tk] = v
    return v

def load_ishares(n):
    lines = open(os.path.join(RAW, n+"_holdings.txt"), encoding="utf-8", errors="ignore").read().splitlines()
    hi = next(i for i,l in enumerate(lines) if l.startswith("Ticker,Name,"))
    rows = list(csv.reader(lines[hi:]))
    df = pd.DataFrame([r[:len(rows[0])] for r in rows[1:] if len(r) >= len(rows[0])], columns=rows[0])
    w = df["Weight (%)"] if "Weight (%)" in df.columns else df["Market Weight"]
    df["W"] = pd.to_numeric(w.astype(str).str.replace(",",""), errors="coerce")
    df["P"] = pd.to_numeric(df["Price"].astype(str).str.replace(",",""), errors="coerce")
    df["Ticker"] = df["Ticker"].str.strip().str.strip('"')
    return df[df["Asset Class"].str.contains("Equity", na=False)].copy()

def slick(nm):
    df = pd.read_csv(os.path.join(PROC, "weights_%s.csv" % nm))
    df["Symbol"] = df["Symbol"].str.strip()
    df["Price"] = pd.to_numeric(df["Price"].astype(str).str.replace(",","").str.replace("$",""), errors="coerce")
    return df

jobs = []
sp = slick("SP500"); jobs.append(("SPX_标普500", sp[["Symbol","Price"]].rename(columns={"Symbol":"Ticker"})))
ndx = slick("NDX"); jobs.append(("NDX_纳斯达克100", ndx[["Symbol","Price"]].rename(columns={"Symbol":"Ticker"})))
sox = load_ishares("SOXX"); jobs.append(("SOX_费城半导体", sox[["Ticker","P"]].rename(columns={"P":"Price"})))
iwm = load_ishares("IWM")
random.seed(42)
idx = sorted(random.sample(range(len(iwm)), 150))
ruts = iwm.iloc[idx]; jobs.append(("RUT_罗素2000(抽样150)", ruts[["Ticker","P"]].rename(columns={"P":"Price"})))

out = []
for label, d in jobs:
    tot, n, miss = 0.0, 0, 0
    vals = []
    for _, r in d.iterrows():
        if not r["Price"] or pd.isna(r["Price"]):
            miss += 1; continue
        s = shares(r["Ticker"])
        if not s:
            miss += 1; continue
        v = s * r["Price"]
        vals.append(v); tot += v; n += 1
        time.sleep(0.05)
    json.dump(cache, open(CACHE, "w"), indent=1)
    extra = ""
    if "抽样" in label:
        tot = np.mean(vals) * len(iwm)
        extra = " (均值×1971)"
    out.append(dict(指数=label, 全部成分=len(d), 有效样本=n, 缺失=miss,
                    总市值万亿美元=round(tot/1e12, 2), 说明=extra))
    print(label, "n=%d/%d 总市值 %.2f 万亿美元%s" % (n, len(d), tot/1e12, extra), flush=True)

json.dump(cache, open(CACHE, "w"), indent=1)
df = pd.DataFrame(out)
df.to_csv(os.path.join(OUT, "market_cap.csv"), index=False, encoding="utf-8-sig")
print(df.to_string())
