# -*- coding: utf-8 -*-
"""解析 multpl 月度估值表 -> data/processed/val_*.csv"""
import re, os, html as htmlmod
import pandas as pd

BASE = r"E:\workspace\new"; RAW = os.path.join(BASE, "data", "raw"); PROC = os.path.join(BASE, "data", "processed")
os.makedirs(PROC, exist_ok=True)

def clean(s):
    s = htmlmod.unescape(s)
    s = s.replace("\u2002", " ").replace("\xa0", " ")
    return s.strip()

def parse_multpl(path):
    raw = open(path, encoding="utf-8", errors="ignore").read()
    rows = re.findall(r"<tr[^>]*>\s*<td[^>]*>([^<]+)</td>\s*<td[^>]*>([^<]*)</td>", raw)
    out = []
    for d, v in rows:
        d = clean(d); v = clean(v).replace(",", "").replace("%", "").replace("$", "")
        if not d or not v: continue
        try:
            dt = pd.to_datetime(d, format="%b %d, %Y")
        except Exception:
            continue
        try:
            val = float(v)
        except Exception:
            continue
        out.append((dt, val))
    return pd.DataFrame(out, columns=["date", "value"]).drop_duplicates("date").sort_values("date").reset_index(drop=True)

for k in ["multpl_cape", "multpl_pe", "multpl_dy", "multpl_ey"]:
    p = os.path.join(RAW, k + ".html")
    df = parse_multpl(p)
    short = k.replace("multpl_", "")
    df.to_csv(os.path.join(PROC, "val_%s.csv" % short), index=False)
    print("%-4s rows=%4d  %s -> %s  last=%s" % (short, len(df), df["date"].dt.date.min(), df["date"].dt.date.max(), df["value"].iloc[-1]))
