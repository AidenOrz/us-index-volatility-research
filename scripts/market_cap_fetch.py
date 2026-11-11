# -*- coding: utf-8 -*-
"""用真实流通股本估算成分股市值，从而估计各指数的市值覆盖。"""
import os, re, json, time, csv
import urllib.request
import pandas as pd
UA={"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"}
RAW=r"E:\workspace\new\data\raw"
def get(u, timeout=20):
    for k in range(3):
        try:
            with urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=timeout) as f:
                return f.read().decode("utf-8","ignore")
        except Exception:
            time.sleep(1+k)
    return ""

def shares_out(tk):
    h = get("https://stockanalysis.com/stocks/%s/statistics/" % tk.lower().replace(".","-"))
    if not h: return None
    m = re.search(r'<span><!---->Shares Outstanding<!----></span>.*?title="([\d,]+)"', h, re.S)
    if m: return float(m.group(1).replace(",",""))
    return None

if __name__ == "__main__":
    need = {}
    for nm in ["SP500","NDX","DJI"]:
        w = pd.read_csv(os.path.join(r"E:\workspace\new\data\processed", "weights_%s.csv" % nm))
        for _, r in w.head(12).iterrows():
            need[r["Symbol"]] = r["Weight"]
    sx = pd.read_csv(os.path.join(r"E:\workspace\new\data\processed","holdings_SOXX.csv"))
    sx["W"] = pd.to_numeric(sx["Weight (%)"], errors="coerce")
    sx["P"] = pd.to_numeric(sx["Price"], errors="coerce")
    for t in sx.nlargest(12,"W")["Ticker"]: need.setdefault(t, None)
    out = {}
    for i, tk in enumerate(need):
        s = shares_out(tk)
        out[tk] = s
        print(tk, s, flush=True)
        time.sleep(0.3)
    json.dump(out, open(os.path.join(RAW,"shares_outstanding.json"),"w"), indent=1)
