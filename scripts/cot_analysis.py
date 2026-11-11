# -*- coding: utf-8 -*-
r"""
VIX 期货 CFTC COT 持仓实证分析（第 1 部分：持仓结构 + 对齐 VIX）
输入：data\raw\cftc_vix_cot.csv, data\raw\cboe_vol\VIX_History.csv
输出：data\output\cot_positions.csv, data\output\cot_vs_vix.csv
幂等、可重复运行。
"""
import os
import numpy as np
import pandas as pd

ROOT = r"E:\workspace\new"
RAW_COT = os.path.join(ROOT, "data", "raw", "cftc_vix_cot.csv")
RAW_VIX = os.path.join(ROOT, "data", "raw", "cboe_vol", "VIX_History.csv")
OUT_DIR = os.path.join(ROOT, "data", "output")
os.makedirs(OUT_DIR, exist_ok=True)


# ---------------------------------------------------------------- 1. 载入 COT
def load_cot():
    d = pd.read_csv(RAW_COT, low_memory=False)
    out = pd.DataFrame()
    out["report_date"] = pd.to_datetime(d["report_date_as_yyyy_mm_dd"])
    out["oi"] = pd.to_numeric(d["open_interest_all"], errors="coerce")
    out["nc_long"] = pd.to_numeric(d["noncomm_positions_long_all"], errors="coerce")
    out["nc_short"] = pd.to_numeric(d["noncomm_positions_short_all"], errors="coerce")
    out["nc_spread"] = pd.to_numeric(d["noncomm_postions_spread_all"], errors="coerce")
    out["c_long"] = pd.to_numeric(d["comm_positions_long_all"], errors="coerce")
    out["c_short"] = pd.to_numeric(d["comm_positions_short_all"], errors="coerce")
    out["nr_long"] = pd.to_numeric(d["nonrept_positions_long_all"], errors="coerce")
    out["nr_short"] = pd.to_numeric(d["nonrept_positions_short_all"], errors="coerce")
    out["traders_nc_long"] = pd.to_numeric(d["traders_noncomm_long_all"], errors="coerce")
    out["traders_nc_short"] = pd.to_numeric(d["traders_noncomm_short_all"], errors="coerce")
    out = out.sort_values("report_date").drop_duplicates("report_date").reset_index(drop=True)
    # 剔除总持仓无效或为 0 的记录
    out = out[(out["oi"].notna()) & (out["oi"] > 0)].reset_index(drop=True)
    return out


def build_positions(cot):
    p = cot.copy()
    p["nc_net"] = p["nc_long"] - p["nc_short"]
    p["comm_net"] = p["c_long"] - p["c_short"]
    p["nr_net"] = p["nr_long"] - p["nr_short"]
    p["nc_net_pct"] = p["nc_net"] / p["oi"] * 100.0
    p["ls_ratio"] = np.where(p["nc_short"] > 0, p["nc_long"] / p["nc_short"], np.nan)
    p["nc_short_pct"] = p["nc_short"] / p["oi"] * 100.0
    p["nc_long_pct"] = p["nc_long"] / p["oi"] * 100.0
    # 滚动 3 年分位（156 周，最少 104 周）
    p["net_pct_rank"] = (
        p["nc_net_pct"].rolling(156, min_periods=104).apply(
            lambda w: float(pd.Series(w).rank(pct=True).iloc[-1]) * 100.0, raw=False
        )
    )
    return p


# ------------------------------------------------------- 2. 交易日对齐工具
def price_calendar():
    p = pd.read_csv(os.path.join(ROOT, "data", "processed", "prices_close.csv"),
                    index_col=0, parse_dates=True)
    p = p.sort_index()
    p = p[p["SPX"].notna()]
    return p


def load_vix():
    v = pd.read_csv(RAW_VIX)
    v["date"] = pd.to_datetime(v["DATE"], format="%m/%d/%Y")
    v["vix"] = pd.to_numeric(v["CLOSE"], errors="coerce")
    v = v[["date", "vix"]].dropna().sort_values("date").reset_index(drop=True)
    return v


def align_after_n_trading_days(report_dates, calendar, n=3):
    """把报告日映射到「报告日之后第 n 个交易日」（COT 周五公布，周二报告日 + 3 交易日≈周五）。
    calendar: 升序 DatetimeIndex（价格交易日）。
    返回与 report_dates 等长的 DatetimeIndex。"""
    idx = calendar.values.astype("datetime64[ns]")
    out = []
    for rd in report_dates.values.astype("datetime64[ns]"):
        pos = np.searchsorted(idx, rd, side="right")  # 第一个 > rd 的位置
        tgt = pos + (n - 1)
        if tgt >= len(idx):
            out.append(np.datetime64("NaT"))
        else:
            out.append(idx[tgt])
    return pd.DatetimeIndex(out)


def main():
    cot = load_cot()
    pos = build_positions(cot)
    px = price_calendar()
    cal = px.index

    # ------------------------------------------------------ cot_positions.csv
    colmap = {
        "report_date": "报告日",
        "oi": "总持仓",
        "nc_long": "非商业多头",
        "nc_short": "非商业空头",
        "nc_net": "非商业净持仓",
        "nc_net_pct": "净持仓占总持仓%",
        "ls_ratio": "多空比",
        "comm_net": "商业净持仓",
        "nc_short_pct": "非商业空头占比%",
        "net_pct_rank": "净持仓分位%",
    }
    outpos = pos[list(colmap)].rename(columns=colmap).copy()
    outpos["报告日"] = outpos["报告日"].dt.strftime("%Y-%m-%d")
    for c in outpos.columns[1:]:
        outpos[c] = outpos[c].astype(float).round(4)
    outpos.to_csv(os.path.join(OUT_DIR, "cot_positions.csv"), index=False, encoding="utf-8-sig")

    # ---------------------------------------------------------- cot_vs_vix.csv
    vix = load_vix()
    vix_s = vix.set_index("date")["vix"]

    tmp = pos[["report_date", "nc_net", "nc_net_pct", "nc_short_pct", "oi",
               "nc_long", "nc_short", "comm_net", "net_pct_rank"]].copy()
    tmp["trade_date"] = align_after_n_trading_days(tmp["report_date"], cal, n=3)
    # 同期 VIX 收盘（以 trade_date 当日为准）
    tmp = tmp.dropna(subset=["trade_date"]).reset_index(drop=True)
    tmp["vix"] = vix_s.reindex(tmp["trade_date"]).values
    # 未来 4 / 13 / 26 / 52 周 VIX 水平与变化（按交易日定位，周≈5 个交易日）
    for wks, suffix in [(4, "4w"), (13, "13w"), (26, "26w"), (52, "52w")]:
        fut = tmp["trade_date"].map(lambda d: _shift_trading(cal, d, wks * 5))
        tmp["vix_" + suffix] = vix_s.reindex(pd.DatetimeIndex(fut)).values
        tmp["dvix_" + suffix] = tmp["vix_" + suffix] - tmp["vix"]
    # 滚动 52 周相关
    tmp = tmp.dropna(subset=["vix"]).reset_index(drop=True)
    roll_corr_level = tmp["nc_net"].rolling(52, min_periods=26).corr(tmp["vix"])
    roll_corr_short = tmp["nc_short_pct"].rolling(52, min_periods=26).corr(tmp["vix"])
    dvix4 = tmp["vix_4w"] - tmp["vix"]
    roll_corr_d4 = tmp["nc_net"].rolling(52, min_periods=26).corr(dvix4)

    outvix = pd.DataFrame({
        "报告日": tmp["report_date"].dt.strftime("%Y-%m-%d"),
        "交易对齐日": tmp["trade_date"].dt.strftime("%Y-%m-%d"),
        "非商业净持仓": tmp["nc_net"].astype(float).round(0),
        "净持仓占总持仓%": tmp["nc_net_pct"].astype(float).round(4),
        "非商业空头占比%": tmp["nc_short_pct"].astype(float).round(4),
        "净持仓分位%": tmp["net_pct_rank"].astype(float).round(2),
        "VIX收盘": tmp["vix"].astype(float).round(4),
        "VIX_4周后": tmp["vix_4w"].astype(float).round(4),
        "VIX_4周变化": (tmp["vix_4w"] - tmp["vix"]).astype(float).round(4),
        "滚动52周相关_净持仓vsVIX": roll_corr_level.round(6),
        "滚动52周相关_空头占比vsVIX": roll_corr_short.round(6),
        "滚动52周相关_净持仓vs未来4周VIX变化": roll_corr_d4.round(6),
    })
    outvix.to_csv(os.path.join(OUT_DIR, "cot_vs_vix.csv"), index=False, encoding="utf-8-sig")

    # ------------------------------------------------------------- 关键统计
    corr_level = tmp["nc_net"].corr(tmp["vix"])
    corr_level_pct = tmp["nc_net_pct"].corr(tmp["vix"])
    corr_short = tmp["nc_short_pct"].corr(tmp["vix"])
    corr_d4 = tmp["nc_net"].corr(tmp["vix_4w"] - tmp["vix"])
    corr_d13 = tmp["nc_net"].corr(tmp["vix_13w"] - tmp["vix"])
    corr_d4_pct = tmp["nc_net_pct"].corr(tmp["vix_4w"] - tmp["vix"])
    corr_s_d4 = tmp["nc_short_pct"].corr(tmp["vix_4w"] - tmp["vix"])

    stats = {
        "n_weeks": int(len(pos)),
        "n_aligned": int(len(tmp)),
        "date_min": str(pos["report_date"].min().date()),
        "date_max": str(pos["report_date"].max().date()),
        "net_neg_share": float((pos["nc_net"] < 0).mean() * 100),
        "net_pct_mean": float(pos["nc_net_pct"].mean()),
        "net_pct_median": float(pos["nc_net_pct"].median()),
        "net_pct_min": float(pos["nc_net_pct"].min()),
        "net_pct_max": float(pos["nc_net_pct"].max()),
        "short_pct_mean": float(pos["nc_short_pct"].mean()),
        "ls_ratio_median": float(pos["ls_ratio"].median()),
        "comm_net_mean": float(pos["comm_net"].mean()),
        "comm_short_share": float((pos["comm_net"] < 0).mean() * 100),
        "corr_level": float(corr_level),
        "corr_level_pct": float(corr_level_pct),
        "corr_short": float(corr_short),
        "corr_d4": float(corr_d4),
        "corr_d13": float(corr_d13),
        "corr_d4_pct": float(corr_d4_pct),
        "corr_s_d4": float(corr_s_d4),
        "roll_level_median": float(roll_corr_level.median()),
        "roll_short_median": float(roll_corr_short.median()),
        "roll_d4_median": float(roll_corr_d4.median()),
        "roll_d4_pos_share": float((roll_corr_d4.dropna() > 0).mean() * 100),
        "vix_mean": float(tmp["vix"].mean()),
        "vix_median": float(tmp["vix"].median()),
    }
    import json
    with open(os.path.join(OUT_DIR, "..", ".tmp-cot-stage1.json"), "w", encoding="utf-8") as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)
    print(json.dumps(stats, ensure_ascii=False, indent=2))
    print("\nWROTE:", os.path.join(OUT_DIR, "cot_positions.csv"))
    print("WROTE:", os.path.join(OUT_DIR, "cot_vs_vix.csv"))


def _shift_trading(cal, d, n):
    """从交易日历的 d 之后第 n 个交易日。"""
    idx = cal.values.astype("datetime64[ns]")
    pos = np.searchsorted(idx, np.datetime64(d), side="right")
    tgt = pos + n - 1
    return idx[tgt] if tgt < len(idx) else np.datetime64("NaT")


if __name__ == "__main__":
    main()
