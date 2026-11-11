# -*- coding: utf-8 -*-
"""增量补齐引擎：检测缺口 → 多源补齐 → 校验 → 报告。

设计要点：
  1. 每个数据源独立探测，一个失败不拖垮全局
  2. 缺口分两类：尾部缺失（缺最近几天）与内部空洞（历史中间缺）
  3. 补齐后必须校验（单调日期、数值范围、样本量），不合格的补丁直接丢弃
  4. 所有失败都要能说清「哪个源、哪个指标、什么原因」，供 UI 弹窗
"""
import os, sys, json, csv, io, datetime, urllib.request, urllib.error, time

sys.stdout.reconfigure(encoding="utf-8")

ROOT = r"E:\workspace\new"
CBOE = os.path.join(ROOT, "data", "raw", "cboe_vol")
PROC = os.path.join(ROOT, "data", "processed")
OUTD = os.path.join(ROOT, "data", "output")
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

PROXY_CANDIDATES = ["http://127.0.0.1:7897", "http://127.0.0.1:7890",
                    "http://127.0.0.1:10809", "http://127.0.0.1:1080"]


# ────────────────────────── 基础 HTTP ──────────────────────────
def http_get(url, timeout=25, headers=None, proxy=None, retries=2):
    """带重试的 GET。东财对高频请求会主动断连（Remote end closed without
    response），重试一次通常就恢复，没必要直接判定为失败。"""
    h = {"User-Agent": UA, "Accept": "*/*"}
    if headers:
        h.update(headers)
    last = None
    for attempt in range(retries + 1):
        req = urllib.request.Request(url, headers=h)
        if proxy:
            op = urllib.request.build_opener(
                urllib.request.ProxyHandler({"http": proxy, "https": proxy}))
        else:
            op = urllib.request.build_opener()
        try:
            with op.open(req, timeout=timeout) as r:
                return r.read()
        except Exception as e:
            last = e
            if attempt < retries:
                time.sleep(0.8 * (attempt + 1))
    raise last


def http_get_json(url, timeout=25, headers=None, proxy=None):
    return json.loads(http_get(url, timeout, headers, proxy).decode("utf-8", "ignore"))


def find_working_proxy():
    """依次试候选代理，能连上 Google 生成器才算真的可用。"""
    for p in PROXY_CANDIDATES:
        try:
            http_get("https://storage.googleapis.com/flutter_infra_release/releases/releases_windows.json",
                     timeout=8, proxy=p)
            return p
        except Exception:
            continue
    return None


# ────────────────────────── 读取现有 CSV ──────────────────────────
def read_cboe(ticker):
    """返回 {date: close} 字典；自动兼容 2 列与 4 列格式。"""
    p = os.path.join(CBOE, ticker + "_History.csv")
    if not os.path.exists(p):
        return {}
    out = {}
    with open(p, encoding="utf-8", errors="ignore") as f:
        lines = [l.strip() for l in f if l.strip()]
    if not lines:
        return {}
    hdr = [c.strip().upper() for c in lines[0].split(",")]
    ci = hdr.index("CLOSE") if "CLOSE" in hdr else len(hdr) - 1
    for ln in lines[1:]:
        parts = ln.split(",")
        if len(parts) <= ci:
            continue
        try:
            d = datetime.datetime.strptime(parts[0], "%m/%d/%Y").date()
            v = float(parts[ci])
        except Exception:
            continue
        if v > 0:
            out[d] = v
    return out


def write_cboe(ticker, series):
    """按 CBOE 原始格式写回（DATE,OPEN,HIGH,LOW,CLOSE 或 DATE,CLOSE）。"""
    p = os.path.join(CBOE, ticker + "_History.csv")
    orig = {}
    if os.path.exists(p):
        with open(p, encoding="utf-8", errors="ignore") as f:
            lines = [l.strip() for l in f if l.strip()]
        if lines:
            hdr = [c.strip().upper() for c in lines[0].split(",")]
            for ln in lines[1:]:
                parts = ln.split(",")
                try:
                    d = datetime.datetime.strptime(parts[0], "%m/%d/%Y").date()
                except Exception:
                    continue
                orig[d] = parts[1:]
            merged = dict(orig)
            for d, v in series.items():
                if d not in merged:
                    merged[d] = [("%f" % v)] * (len(hdr) - 1)
    else:
        hdr = ["DATE", "CLOSE"]
        merged = {d: ["%f" % v] for d, v in series.items()}
    tmp = p + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:
        f.write(",".join(hdr) + "\n")
        for d in sorted(merged):
            f.write(d.strftime("%m/%d/%Y") + "," + ",".join(merged[d]) + "\n")
    os.replace(tmp, p)


# ────────────────────────── 交易日历 ──────────────────────────
def trading_days(spx_dates, start, end):
    """用 SPX 已有的日期作为交易日日历；区间内缺的日期视为该补的。"""
    return {d for d in spx_dates if start <= d <= end}


def detect_gaps(series, calendar):
    """返回 (尾部缺失日, 内部空洞日)。

    内部空洞只看「该指标自身有效区间内」的缺失：
    指标上市之前的日子不算空洞（VIX9D 2011 年才有，不能要求 1995 年有值）。
    """
    if not series:
        return set(), set()
    have = set(series)
    first, last = min(have), max(have)
    scope = {d for d in calendar if first <= d <= last}
    tail = {d for d in calendar if d > last}
    inner = scope - have
    return tail, inner


# ────────────────────────── 补齐源 ──────────────────────────
def src_cboe_full(ticker, proxy=None):
    """CBOE 官方完整文件（首选）。"""
    url = "https://cdn.cboe.com/api/global/us_indices/daily_prices/%s_History.csv" % ticker
    raw = http_get(url, timeout=40, proxy=proxy)
    txt = raw.decode("utf-8", "ignore")
    if "<Error>" in txt[:200] or "AccessDenied" in txt[:200]:
        raise RuntimeError("CBOE 拒绝访问该代码")
    out = {}
    lines = [l.strip() for l in txt.strip().splitlines() if l.strip()]
    hdr = [c.strip().upper() for c in lines[0].split(",")]
    ci = hdr.index("CLOSE") if "CLOSE" in hdr else len(hdr) - 1
    for ln in lines[1:]:
        parts = ln.split(",")
        try:
            d = datetime.datetime.strptime(parts[0], "%m/%d/%Y").date()
            v = float(parts[ci])
        except Exception:
            continue
        if v > 0:
            out[d] = v
    if len(out) < 50:
        raise RuntimeError("返回样本过少（%d 行）" % len(out))
    return out


def src_eastmoney(secid, proxy=None):
    """东方财富日K（备用）。返回 {date: close}。"""
    url = ("https://push2his.eastmoney.com/api/qt/stock/kline/get"
           "?secid=%s&fields1=f1,f2,f3&fields2=f51,f52,f53&klt=101&fqt=1&beg=0&end=20500101" % secid)
    j = http_get_json(url, timeout=30, proxy=proxy)
    d = j.get("data")
    if not d:
        raise RuntimeError("东财无该代码数据")
    out = {}
    for k in d.get("klines", []):
        p = k.split(",")
        try:
            dt = datetime.datetime.strptime(p[0], "%Y-%m-%d").date()
            v = float(p[2])
        except Exception:
            continue
        if v > 0:
            out[dt] = v
    if not out:
        raise RuntimeError("东财返回空")
    return out


def src_yahoo(symbol, proxy):
    """Yahoo 日线（需代理）。"""
    url = ("https://query1.finance.yahoo.com/v8/finance/chart/%s"
           "?range=5y&interval=1d&events=div%%2Csplit" % symbol)
    j = http_get_json(url, timeout=30, proxy=proxy)
    res = j["chart"]["result"][0]
    ts = res["timestamp"]
    cl = res["indicators"]["quote"][0]["close"]
    out = {}
    for t, c in zip(ts, cl):
        if c is None:
            continue
        d = datetime.datetime.fromtimestamp(t, datetime.timezone.utc).date()
        if c > 0:
            out[d] = float(c)
    if not out:
        raise RuntimeError("Yahoo 返回空")
    return out


# ────────────────────────── 校验 ──────────────────────────
def validate(merged, candidate, name, lo=None, hi=None, max_dev=0.02):
    """把 candidate 合进 merged 前先校验，不合格返回 (merged, 拒绝原因)。

    max_dev：重叠日期上允许的最大相对偏差。这是防「串了别的标的」的最后一道闸 ——
    数据源如果给的是复权价或另一个指数，重叠段的偏差会立刻暴露。
    """
    if not candidate:
        return merged, "%s 无数据" % name
    ts = sorted(candidate)
    if any(b <= a for a, b in zip(ts, ts[1:])):
        return merged, "%s 日期非严格递增" % name
    bad = [v for v in candidate.values() if not (0 < v < 1e7)]
    if lo is not None and hi is not None:
        bad += [v for v in candidate.values() if not (lo <= v <= hi)]
    if bad:
        return merged, "%s 数值越界 %d 个" % (name, len(bad))

    # ★ 重叠段交叉校验：这是发现「数据源基准不一致」的唯一手段
    overlap = [d for d in ts if d in merged]
    if len(overlap) >= 20:
        rel = []
        for d in overlap:
            a, b = merged[d], candidate[d]
            if a > 0:
                rel.append(abs(b - a) / a)
        rel.sort()
        med = rel[len(rel) // 2]
        if med > max_dev:
            return merged, ("%s 与本地基准不一致（重叠 %d 天，中位偏差 %.2f%%）"
                            % (name, len(overlap), med * 100))

    new = {d: v for d, v in candidate.items() if d not in merged}
    if not new:
        return merged, None
    out = dict(merged)
    out.update(new)
    return out, None


# ────────────────────────── 主流程 ──────────────────────────
VOL_TICKERS = ["VIX", "VIX9D", "VIX3M", "VIX6M", "VVIX", "SKEW", "VXN", "RVX",
               "OVX", "GVZ", "VXAPL", "VXAZN", "VXGOG", "VXGS", "VXIBM",
               "VXEEM", "VXEWZ", "VXSLV", "VXHYG", "VXTLT", "VXGDX", "VXFXI", "VXEFA"]

IDX_MAP = {
    "SPX":  ("^GSPC", "100.SPX"),
    "DJI":  ("^DJI",  "100.DJIA"),
    "IXIC": ("^IXIC",  "100.NDX"),
    "NDX":  ("^NDX",   "100.NDX100"),
    "RUT":  ("^RUT",   None),
    "SOX":  ("^SOX",   None),
}


def run(verbose=True, allow_proxy=True):
    report = {"startedAt": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
              "sources": {}, "gaps": {}, "filled": {}, "errors": [], "ok": True}

    def log(msg):
        if verbose:
            print(msg)

    # 1) 找代理
    proxy = find_working_proxy() if allow_proxy else None
    report["sources"]["proxy"] = proxy or ""
    log("[1/5] 代理: %s" % (proxy or "无"))

    # 2) 交易日历（用 SPX 收盘价）
    spx_path = os.path.join(PROC, "prices_close.csv")
    spx_dates = set()
    if os.path.exists(spx_path):
        with open(spx_path, encoding="utf-8") as f:
            for row in csv.DictReader(f):
                try:
                    spx_dates.add(datetime.date.fromisoformat(row[list(row)[0]]))
                except Exception:
                    pass
    log("[2/5] 交易日历: %d 天, 最新 %s" % (len(spx_dates), max(spx_dates) if spx_dates else "-"))
    report["sources"]["calendarDays"] = len(spx_dates)

    # 3) 波动率类：CBOE 直连优先
    log("[3/5] 波动率指数（CBOE）")
    cboe_ok, cboe_fail = 0, []
    for t in VOL_TICKERS:
        cur = read_cboe(t)
        if not cur:
            report["errors"].append({"src": "CBOE", "item": t, "msg": "本地无文件"})
            cboe_fail.append(t)
            continue
        tail, inner = detect_gaps(cur, spx_dates)
        if not tail and not inner:
            cboe_ok += 1
            continue
        report["gaps"][t] = {"tail": len(tail), "inner": len(inner)}
        try:
            fresh = src_cboe_full(t, proxy)
            merged, why = validate(cur, fresh, "CBOE")
            if why:
                report["errors"].append({"src": "CBOE", "item": t, "msg": why})
                cboe_fail.append(t)
                continue
            added = len(set(merged) - set(cur))
            write_cboe(t, merged)
            report["filled"][t] = added
            cboe_ok += 1
            log("    %-7s +%d 天" % (t, added))
        except Exception as e:
            report["errors"].append({"src": "CBOE", "item": t, "msg": str(e)[:120]})
            cboe_fail.append(t)
    log("    CBOE 完成 %d/%d" % (cboe_ok, len(VOL_TICKERS)))
    report["sources"]["CBOE"] = "ok" if cboe_ok else "fail"

    # 4) 指数：CBOE → Yahoo → 东财 三级回退
    log("[4/5] 指数收盘价")
    if not spx_dates:
        report["errors"].append({"src": "local", "item": "prices_close", "msg": "本地价格文件缺失"})
        report["ok"] = False
        return report

    prices = {}
    cols = []
    with open(spx_path, encoding="utf-8") as f:
        rd = csv.reader(f)
        hdr = next(rd)
        cols = hdr[1:]
        for row in rd:
            try:
                d = datetime.date.fromisoformat(row[0])
            except Exception:
                continue
            prices[d] = {}
            for i, c in enumerate(cols, 1):
                if i < len(row) and row[i]:
                    try:
                        prices[d][c] = float(row[i])
                    except Exception:
                        pass

    last_local = max(spx_dates)
    idx_filled = {}
    for col in cols:
        cur = {d: v[col] for d, v in prices.items() if col in v}
        if not cur:
            continue
        # 该补的日期：本地全部交易日中缺的
        missing = sorted(set(prices) - set(cur))
        # 没有缺口就别去打扰任何数据源 —— 之前漏了这句，导致数据已经完整时
        # 仍然逐个请求，并把「本来就不需要补」误报成「数据源失败」。
        if not missing:
            continue
        y_sym, em_id = IDX_MAP.get(col, (None, None))
        cand = None
        # 逐源尝试。顺序有讲究：东财的 push2his 接口会对 urllib 持续断连
        # （实测三次重试全失败），所以放到最后，优先用 CBOE 与 Yahoo。
        source_errors = []
        got_any = False
        for label in ("CBOE", "Yahoo", "东财"):
            try:
                if label == "CBOE":
                    if col not in ("SPX", "RUT", "DJX", "OEX"):
                        continue
                    got = src_cboe_full(col, proxy)
                elif label == "Yahoo":
                    if not y_sym or not proxy:
                        continue
                    got = src_yahoo(y_sym, proxy)
                else:
                    if not em_id:
                        continue
                    got = src_eastmoney(em_id, proxy)
                got_any = True  # 这个源确实返回了数据
                merged, why = validate(cur, got, label, max_dev=0.02)
                if why:
                    source_errors.append({"src": label, "item": col, "msg": why})
                    continue
                added = len(set(merged) - set(cur))
                if added:
                    cand = merged
                    idx_filled[col] = {"src": label, "added": added}
                    log("    %-5s +%d 天（%s）" % (col, added, label))
                    break
            except Exception as e:
                source_errors.append({"src": label, "item": col, "msg": str(e)[:100]})
                continue
        else:
            # 所有源都没能补上。区分两种情况：
            #   a) 数据源全挂 → 真失败，要报错
            #   b) 源能访问但确实没有这些日期（休市/停牌）→ 不是失败，记下来即可
            # 之前的实现把 (b) 也当成失败，导致「数据已经最全」时仍报 ok=false。
            # 只在「该指数自身的有效区间内」统计补不上的缺口，
            # 不能把上市之前的年份算成缺口（DJI 1990 年才有数据）。
            _base = cand or cur
            _first, _last = min(_base), max(_base)
            still_missing = sorted(d for d in set(prices) - set(_base)
                                   if _first <= d <= _last)
            if got_any and still_missing:
                # 源能用，但就是没有这些日期 → 休市/停牌，不是失败
                report.setdefault("unfillable", {})[col] = len(still_missing)
            elif not got_any:
                report["errors"].extend(source_errors)
        if cand:
            for d, v in cand.items():
                prices.setdefault(d, {})[col] = v

    # 写回价格
    if idx_filled:
        all_days = sorted(prices)
        tmp = spx_path + ".tmp"
        with open(tmp, "w", encoding="utf-8", newline="") as f:
            w = csv.writer(f)
            w.writerow(["", *cols])
            for d in all_days:
                w.writerow([d.isoformat()] + [("%f" % prices[d][c]) if c in prices[d] else "" for c in cols])
        os.replace(tmp, spx_path)
    report["filled"]["_indices"] = idx_filled

    # 5) 汇总
    log("[5/5] 完成，补齐 %d 项" % (len(report["filled"])))
    report["ok"] = len(report["errors"]) == 0
    report["finishedAt"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return report


if __name__ == "__main__":
    rep = run()
    print()
    print(json.dumps(rep, ensure_ascii=False, indent=1)[:4000])
