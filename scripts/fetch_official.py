# -*- coding: utf-8 -*-
"""抓取 CBOE 官方指数 CSV、纳斯达克官方 API、美国财政部国债收益率，用于交叉校验与无风险利率。"""
import urllib.request, json, time, calendar, csv, os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(BASE, "data", "raw")
os.makedirs(RAW, exist_ok=True)
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"}

def fetch(url, timeout=90, retries=3):
    last = None
    for k in range(retries):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=timeout) as f:
                return f.read()
        except Exception as e:
            last = e; time.sleep(2 * (k + 1))
    raise last

# ---------- CBOE 官方 CSV ----------
for name in ["SPX", "RUT", "RUI", "DJX", "OEX", "VIX", "VXN", "RVX"]:
    url = "https://cdn.cboe.com/api/global/us_indices/daily_prices/%s_History.csv" % name
    try:
        d = fetch(url)
        with open(os.path.join(RAW, "cboe_%s.csv" % name), "wb") as f:
            f.write(d)
        lines = d.decode("utf-8", "ignore").strip().splitlines()
        print("CBOE", name, len(lines) - 1, lines[1].split(",")[0], "->", lines[-1].split(",")[0])
    except Exception as e:
        print("CBOE", name, "ERR", type(e).__name__, str(e)[:70])
    time.sleep(0.4)

# ---------- Nasdaq 官方 API ----------
def nasdaq(sym, start, end):
    url = ("https://api.nasdaq.com/api/quote/%s/historical?assetclass=index&fromdate=%s&todate=%s&limit=9999"
           % (sym, start, end))
    j = json.loads(fetch(url))
    return j["data"]["tradesTable"]["rows"]

def nq_range(sym, a, b, chunk=6):
    """按年分块抓取，返回 [(date, close)] 升序。"""
    out = {}
    y0, y1 = int(a[:4]), int(b[:4])
    for y in range(y0, y1 + 1, chunk):
        s = max(a, "%d-01-01" % y)
        e = min(b, "%d-12-31" % (y + chunk - 1))
        try:
            rows = nasdaq(sym, s, e)
            for r in rows:
                d = time.strftime("%Y-%m-%d", time.strptime(r["date"], "%m/%d/%Y"))
                out[d] = float(r["close"].replace(",", ""))
        except Exception as ex:
            print("NQ", sym, s, e, "ERR", str(ex)[:60])
        time.sleep(0.5)
    return sorted(out.items())

for sym, name, a, b in [("COMP", "IXIC", "1971-02-05", "2026-11-07"), ("NDX", "NDX", "1985-10-01", "2026-11-07")]:
    try:
        rows = nq_range(sym, a, b)
        with open(os.path.join(RAW, "nq_%s.csv" % name), "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f); w.writerow(["date", "close"]); w.writerows(rows)
        print("NQ", name, len(rows), rows[0][0], "->", rows[-1][0])
    except Exception as e:
        print("NQ", name, "ERR", type(e).__name__, str(e)[:80])

# ---------- 美国财政部：13 周国库券(次级市场)利率 ----------
def treas_bill(year):
    url = ("https://home.treasury.gov/resource-center/data-chart-center/interest-rates/daily-treasury-rates.csv/%d/all"
           "?type=daily_treasury_bill_rates&field_tdr_date_value=%d&page&_format=csv" % (year, year))
    txt = fetch(url, timeout=60).decode("utf-8", "ignore")
    lines = [l for l in txt.strip().splitlines() if l.strip()]
    if not lines:
        return []
    hdr = [h.strip().strip('"') for h in lines[0].split(",")]
    idx = None
    for i, h in enumerate(hdr):
        if h.upper().startswith("13 WEEKS COUPON"):
            idx = i; break
    if idx is None:
        return []
    out = []
    for l in lines[1:]:
        p = [x.strip().strip('"') for x in l.split(",")]
        if len(p) <= idx:
            continue
        try:
            d = time.strftime("%Y-%m-%d", time.strptime(p[0], "%m/%d/%Y"))
            out.append([d, float(p[idx])])
        except Exception:
            continue
    return out

allrows = []
for y in range(1990, 2027):
    try:
        r = treas_bill(y)
        allrows.extend(r)
        print("TREAS", y, len(r))
    except Exception as e:
        print("TREAS", y, "ERR", type(e).__name__, str(e)[:60])
    time.sleep(0.3)
allrows.sort()
with open(os.path.join(RAW, "treasury_13w.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f); w.writerow(["date", "yield_pct"]); w.writerows(allrows)
print("TREAS total", len(allrows), allrows[0] if allrows else None, allrows[-1] if allrows else None)
