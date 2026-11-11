# -*- coding: utf-8 -*-
r"""
VIX 期货 COT 信号检验（第 2 部分）
输入：data\output\cot_positions.csv, data\processed\prices_close.csv
输出：data\output\cot_signal.csv, data\output\.tmp-cot-stage2.json
口径：
  * COT 报告日 = 周二；持仓数据周五收盘后才公布 → 信号日统一后移 3 个交易日（≈周五），
    此后才允许交易，避免前视偏差。
  * 未来收益 = SPX 在信号日后 20/65/130/260 个交易日的收盘收益（≈4/13/26/52 周）。
  * 分位基于滚动 156 周（3 年）窗口，最少 104 周。
幂等、可重复运行。
"""
import os
import sys
import json
import numpy as np
import pandas as pd

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = r"E:\workspace\new"
OUT_DIR = os.path.join(ROOT, "data", "output")

HORIZONS = [(4, 20), (13, 65), (26, 130), (52, 260)]  # (周, 交易日)
BUCKETS = [
    ("<10%（极度看空）", 0.0, 10.0),
    ("10-25%（看空）", 10.0, 25.0),
    ("25-50%（偏空）", 25.0, 50.0),
    ("50-75%（偏多）", 50.0, 75.0),
    ("75-90%（看多）", 75.0, 90.0),
    (">90%（极度看多）", 90.0, 100.01),
]


def load_prices():
    p = pd.read_csv(os.path.join(ROOT, "data", "processed", "prices_close.csv"),
                    index_col=0, parse_dates=True)
    p = p.sort_index()
    return p[p["SPX"].notna()]


def shift_trading(idx_arr, d, n):
    """d 之后第 n 个交易日（n>=1）。"""
    pos = np.searchsorted(idx_arr, np.datetime64(d), side="right")
    tgt = pos + n - 1
    return idx_arr[tgt] if tgt < len(idx_arr) else np.datetime64("NaT")


def build_panel():
    pos = pd.read_csv(os.path.join(OUT_DIR, "cot_positions.csv"),
                      encoding="utf-8-sig", parse_dates=["报告日"])
    pos = pos.sort_values("报告日").reset_index(drop=True)
    px = load_prices()
    cal = px.index.values.astype("datetime64[ns]")
    spx = px["SPX"]

    df = pd.DataFrame({
        "report_date": pos["报告日"],
        "nc_net": pos["非商业净持仓"],
        "nc_net_pct": pos["净持仓占总持仓%"],
        "nc_short_pct": pos["非商业空头占比%"],
        "net_rank": pos["净持仓分位%"],
    })
    # 报告日 + 3 个交易日 = 可用信号日
    df["trade_date"] = [shift_trading(cal, d, 3) for d in df["report_date"]]
    df = df[df["trade_date"].notna()].reset_index(drop=True)
    df["spx0"] = spx.reindex(pd.DatetimeIndex(df["trade_date"])).values
    for wks, nd in HORIZONS:
        fut_d = [shift_trading(cal, d, nd) for d in df["trade_date"]]
        df["spx_%dw" % wks] = spx.reindex(pd.DatetimeIndex(fut_d)).values
        df["ret_%dw" % wks] = (df["spx_%dw" % wks] / df["spx0"] - 1.0) * 100.0

    # 空头占比的滚动 3 年分位（用于第二套分档做稳健性检验）
    df["short_rank"] = df["nc_short_pct"].rolling(156, min_periods=104).apply(
        lambda w: float(pd.Series(w).rank(pct=True).iloc[-1]) * 100.0, raw=False)
    return df, cal, spx


def tstat_overlap(s, horizon_days):
    """重叠收益序列的 t 值；用 horizon 长度做有效样本折扣（Newey-West 简化版）。
    无 scipy，手工计算。"""
    s = s.dropna()
    if len(s) < 5:
        return np.nan
    eff_n = max(len(s) / max(horizon_days / 5.0, 1.0), 3.0)
    sd = s.std(ddof=1)
    if not np.isfinite(sd) or sd == 0:
        return np.nan
    return float(s.mean() / (sd / np.sqrt(eff_n)))


def desc_stat(sub):
    out = {"n": int(len(sub))}
    for wks, nd in HORIZONS:
        s = sub["ret_%dw" % wks].dropna()
        out["n_%dw" % wks] = int(len(s))
        out["mean_%dw" % wks] = float(s.mean()) if len(s) else np.nan
        out["med_%dw" % wks] = float(s.median()) if len(s) else np.nan
        out["win_%dw" % wks] = float((s > 0).mean() * 100.0) if len(s) else np.nan
        out["t_%dw" % wks] = tstat_overlap(s, nd)
    return out


def bucket_table(df, rank_col, label_prefix):
    rows = []
    valid = df.dropna(subset=[rank_col])
    rows.append(("全样本（基准）", desc_stat(valid)))
    for name, lo, hi in BUCKETS:
        sub = valid[(valid[rank_col] >= lo) & (valid[rank_col] < hi)]
        rows.append((label_prefix + name, desc_stat(sub)))
    return rows


def extreme_events(df, cal, spx, window=156, minp=104):
    """3 年新高/新低事件。返回事件明细 DataFrame。"""
    s = df["nc_net_pct"]
    # 关键：滚动窗口必须排除当期，否则 min<=s<=max 恒成立、事件标记全为 True。
    # 这里取「截至上一周」的 156 周窗口，再与当期比较。
    rmax_prev = s.rolling(window, min_periods=minp).max().shift(1)
    rmin_prev = s.rolling(window, min_periods=minp).min().shift(1)
    tol = 0.0
    is_low = (s <= rmin_prev + tol) & rmin_prev.notna()
    is_high = (s >= rmax_prev - tol) & rmax_prev.notna()
    df = df.copy()
    df["is_low"] = is_low
    df["is_high"] = is_high
    return df


def decluster(df, flag, gap_weeks=26):
    """贪心去重叠：保留首次触发，之后 gap_weeks 内的事件丢弃，避免重叠样本夸大显著性。"""
    keep = []
    last = None
    for i, (d, f) in enumerate(zip(df["report_date"], df[flag])):
        if not f:
            continue
        if last is not None and (d - last).days < gap_weeks * 7:
            continue
        keep.append(i)
        last = d
    return df.iloc[keep]


def fmt_row(label, st):
    def f(k):
        v = st.get(k, np.nan)
        return "" if pd.isna(v) else round(v, 2)
    return {
        "分档": label,
        "样本周数": st["n"],
        "4周均值%": f("mean_4w"), "4周胜率%": f("win_4w"),
        "13周均值%": f("mean_13w"), "13周胜率%": f("win_13w"),
        "26周均值%": f("mean_26w"), "26周胜率%": f("win_26w"),
        "52周均值%": f("mean_52w"), "52周胜率%": f("win_52w"),
        "13周中位数%": f("med_13w"), "52周中位数%": f("med_52w"),
        "13周t值(重叠调整)": f("t_13w"), "52周t值(重叠调整)": f("t_52w"),
    }


def main():
    df, cal, spx = build_panel()
    df = extreme_events(df, cal, spx)

    rows = []
    # 主口径：净持仓 3 年分位
    for label, st in bucket_table(df, "net_rank", ""):
        rows.append(fmt_row(label, st))
    # 稳健性：空头占比 3 年分位
    for label, st in bucket_table(df, "short_rank", "[空头占比口径] "):
        rows.append(fmt_row(label, st))

    # 极端事件：3 年新低 / 新高
    ev = {}
    for flag, name in [("is_low", "3年新低（最看空）"), ("is_high", "3年新高（最看多）")]:
        allsub = df[df[flag]]
        uniq = decluster(df, flag, gap_weeks=26)
        ev[name] = {
            "all": desc_stat(allsub),
            "declustered": desc_stat(uniq),
            "n_all": int(len(allsub)),
            "n_uniq": int(len(uniq)),
            "first": str(allsub["report_date"].min().date()) if len(allsub) else None,
            "last": str(allsub["report_date"].max().date()) if len(allsub) else None,
        }
        rows.append(fmt_row("[事件·全部] " + name, desc_stat(allsub)))
        rows.append(fmt_row("[事件·26周去重] " + name, desc_stat(uniq)))

    out = pd.DataFrame(rows)
    out.to_csv(os.path.join(OUT_DIR, "cot_signal.csv"), index=False, encoding="utf-8-sig")

    # ------------------------------------------------------- 附：事件明细
    det_cols = ["report_date", "trade_date", "nc_net_pct", "net_rank", "spx0",
                "ret_4w", "ret_13w", "ret_26w", "ret_52w"]
    det = df[df["is_low"] | df["is_high"]][det_cols].copy()
    det["type"] = np.where(df.loc[det.index, "is_low"], "3年新低", "3年新高")
    det["report_date"] = det["report_date"].dt.strftime("%Y-%m-%d")
    det["trade_date"] = det["trade_date"].astype("datetime64[ns]").astype(str).str[:10]
    det = det.round(2)
    det.to_csv(os.path.join(OUT_DIR, "..", ".tmp-cot-events.csv"), index=False, encoding="utf-8-sig")

    stats = {
        "n_panel": int(len(df)),
        "horizons": {str(w): float((df["ret_%dw" % w].dropna()).mean()) for w, _ in HORIZONS},
        "base_win": {str(w): float((df["ret_%dw" % w].dropna() > 0).mean() * 100) for w, _ in HORIZONS},
        "events": ev,
        "rank_min": float(df["net_rank"].min()),
        "rank_max": float(df["net_rank"].max()),
    }
    with open(os.path.join(OUT_DIR, "..", ".tmp-cot-stage2.json"), "w", encoding="utf-8") as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)

    print(out.to_string(index=False))
    print("\nJSON:", os.path.join(OUT_DIR, "..", ".tmp-cot-stage2.json"))
    print("WROTE:", os.path.join(OUT_DIR, "cot_signal.csv"))


if __name__ == "__main__":
    main()
