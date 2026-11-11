# -*- coding: utf-8 -*-
"""解析成分与行业权重，输出 processed 下的结构化文件。"""
import os
import pandas as pd
from lxml import html as LH

RAW = r"E:\workspace\new\data\raw"
OUT = r"E:\workspace\new\data\processed"
os.makedirs(OUT, exist_ok=True)

def slick_table(path):
    doc = LH.parse(path).getroot()
    for tb in doc.xpath("//table"):
        rows = [["".join(c.itertext()).strip() for c in tr.xpath("./th|./td")] for tr in tb.xpath(".//tr")]
        rows = [r for r in rows if r and len(r) >= 4]
        if rows and rows[0][:3] == ["#", "Company", "Symbol"]:
            df = pd.DataFrame(rows[1:], columns=rows[0])
            df["Weight"] = df["Weight"].str.rstrip("%").astype(float)
            return df
    return None

sp = slick_table(os.path.join(RAW, "slick_sp500.html"))
ndx = slick_table(os.path.join(RAW, "slick_ndx.html"))
dji = slick_table(os.path.join(RAW, "slick_dji.txt"))
for name, df in [("SP500", sp), ("NDX", ndx), ("DJI", dji)]:
    if df is None:
        print(name, "FAILED"); continue
    print(name, len(df), "权重合计 %.2f%%" % df["Weight"].sum(),
          "前三:", ", ".join("%s %.2f%%" % (r.Symbol, r.Weight) for r in df.head(3).itertuples()))
    df.to_csv(os.path.join(OUT, "weights_%s.csv" % name), index=False, encoding="utf-8-sig")

# ---------- 2. iShares 持仓（含 GICS 行业） ----------
def parse_ishares(path):
    lines = open(path, encoding="utf-8", errors="ignore").read().splitlines()
    # 找到表头行
    hdr_i = None
    for i, l in enumerate(lines):
        if l.startswith("Ticker,Name,"):
            hdr_i = i; break
    if hdr_i is None:
        return None, None
    asof = lines[1].split(",")[1].strip('"') if len(lines) > 1 else ""
    rows = []
    for l in lines[hdr_i + 1:]:
        if not l.strip() or l.count(",") < 5:
            continue
        p = next(csv.reader([l])) if False else l.split(",")
        if len(p) < 8:
            continue
        rows.append(p[:10])
    hdr = lines[hdr_i].split(",")
    df = pd.DataFrame(rows, columns=hdr[:len(rows[0])])
    if "Sector" not in df.columns and "Type" in df.columns:
        df = df.rename(columns={"Type": "AssetClass"})
    return df, asof

import csv
for name, fn in [("IWM", "iwm_holdings"), ("SOXX", "soxx_holdings"), ("IVV", "ivv_holdings"),
                 ("IWF", "iwf_holdings"), ("IWD", "iwd_holdings")]:
    df, asof = parse_ishares(os.path.join(RAW, fn + ".txt"))
    if df is None:
        print(name, "parse failed"); continue
    print(name, "持仓", len(df), "asof", asof, "列:", list(df.columns)[:8])
    df.to_csv(os.path.join(OUT, "holdings_%s.csv" % name), index=False, encoding="utf-8-sig")
