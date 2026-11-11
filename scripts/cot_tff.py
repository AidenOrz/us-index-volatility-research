# -*- coding: utf-8 -*-
r"""
VIX 期货 COT —— TFF（Traders in Financial Futures）口径分析（第 3 部分）
输入：data\raw\cftc_vix_tff.csv, data\processed\prices_close.csv, data\raw\cboe_vol\VIX_History.csv
输出：data\output\cot_tff.csv, data\output\cot_tff_signal.csv

口径说明（关键，避免符号陷阱）：
  lev_net      = lev_money_long - lev_money_short   （负值 = 净空波动率）
  lev_short_crowding = -lev_net                     （越大 = 净空越拥挤）
  滚动 3 年分位在 lev_short_crowding 上计算 → 分位 >90% 即「空头极度拥挤」。
  若直接在 lev_net 上算分位，>90% 反而是「最不看空」，方向会完全反过来。
信号统一延后 3 个交易日（COT 周二报告、周五公布）再交易。
幂等、可重复运行。
"""
import os
import json
import numpy as np
import pandas as pd

ROOT = r"E:\workspace\new"
RAW_TFF = os.path.join(ROOT, "data", "raw", "cftc_vix_tff.csv")
RAW_VIX = os.path.join(ROOT, "data", "raw", "cboe_vol", "VIX_History.csv")
OUT_DIR = os.path.join(ROOT, "data", "output")

HORIZONS = [(4, 20), (13, 65), (26, 130), (52, 260)]
BUCKETS = [
    ("<10%", 0.0, 10.0),
    ("10-25%", 10.0, 25.0),
    ("25-50%", 25.0, 50.0),
    ("50-75%", 50.0, 75.0),
    ("75-90%", 75.0, 90.0),
    (">90%", 90.0, 100.01),
]


def shift_trading(idx_arr, d, n):
    pos = np.searchsorted(idx_arr, np.datetime64(d), side="right")
    tgt = pos + n - 1
    return idx_arr[tgt] if tgt < len(idx_arr) else np.datetime64("NaT")


def rolling_rank(s, window=156, minp=104):
    return s.rolling(window, min_periods=minp).apply(
        lambda w: float(pd.Series(w).rank(pct=True).iloc[-1]) * 100.0, raw=False)


def load_tff():
    d = pd.read_csv(RAW_TFF, low_memory=False)
    o = pd.DataFrame()
    o["report_date"] = pd.to_datetime(d["report_date_as_yyyy_mm_dd"])
    n = ["open_interest_all",
         "dealer_positions_long_all", "dealer_positions_short_all", "dealer_positions_spread_all",
         "asset_mgr_positions_long", "asset_mgr_positions_short", "asset_mgr_positions_spread",
         "lev_money_positions_long", "lev_money_positions_short", "lev_money_positions_spread",
         "other_rept_positions_long", "other_rept_positions_short", "other_rept_positions_spread",
         "nonrept_positions_long_all", "nonrept_positions_short_all"]
    for c in n:
        o[c] = pd.to_numeric(d[c], errors="coerce")
    o = o.sort_values("report_date").drop_duplicates("report_date").reset_index(drop=True)
    return o[(o["open_interest_all"] > 0) & o["open_interest_all"].notna()].reset_index(drop=True)


def build():
    t = load_tff()
    t["dealer_net"] = t["dealer_positions_long_all"] - t["dealer_positions_short_all"]
    t["asset_mgr_net"] = t["asset_mgr_positions_long"] - t["asset_mgr_positions_short"]
    t["lev_net"] = t["lev_money_positions_long"] - t["lev_money_positions_short"]
    t["other_rept_net"] = t["other_rept_positions_long"] - t["other_rept_positions_short"]
    t["nonrept_net"] = t["nonrept_positions_long_all"] - t["nonrept_positions_short_all"]

    oi = t["open_interest_all"]
    t["lev_net_pct"] = t["lev_net"] / oi * 100.0
    t["asset_mgr_net_pct"] = t["asset_mgr_net"] / oi * 100.0
    t["dealer_net_pct"] = t["dealer_net"] / oi * 100.0
    t["lev_short_pct"] = t["lev_money_positions_short"] / oi * 100.0
    # 空头拥挤度（越大=净空越极端）
    t["lev_short_crowding"] = -t["lev_net"]
    t["lev_short_rank"] = rolling_rank(t["lev_short_crowding"])
    t["lev_net_rank"] = rolling_rank(t["lev_net"])          # 对照：直接在净头寸上算分位
    t["asset_mgr_rank"] = rolling_rank(t["asset_mgr_net"])  # 机构净多分位
    t["dealer_rank"] = rolling_rank(t["dealer_net"])

    # ---------------- 对齐价格与 VIX
    px = pd.read_csv(os.path.join(ROOT, "data", "processed", "prices_close.csv"),
                     index_col=0, parse_dates=True).sort_index()
    px = px[px["SPX"].notna()]
    cal = px.index.values.astype("datetime64[ns]")
    spx = px["SPX"]

    v = pd.read_csv(RAW_VIX)
    v["date"] = pd.to_datetime(v["DATE"], format="%m/%d/%Y")
    v["vix"] = pd.to_numeric(v["CLOSE"], errors="coerce")
    vix_s = v.dropna(subset=["vix"]).set_index("date")["vix"].sort_index()

    t["trade_date"] = [shift_trading(cal, d, 3) for d in t["report_date"]]
    t = t[t["trade_date"].notna()].reset_index(drop=True)
    t["spx0"] = spx.reindex(pd.DatetimeIndex(t["trade_date"])).values
    t["vix0"] = vix_s.reindex(pd.DatetimeIndex(t["trade_date"])).values
    for wks, nd in HORIZONS:
        fd = [shift_trading(cal, d, nd) for d in t["trade_date"]]
        t["spx_%dw" % wks] = spx.reindex(pd.DatetimeIndex(fd)).values
        t["ret_%dw" % wks] = (t["spx_%dw" % wks] / t["spx0"] - 1.0) * 100.0
        t["vix_%dw" % wks] = vix_s.reindex(pd.DatetimeIndex(fd)).values
        t["dvix_%dw" % wks] = t["vix_%dw" % wks] - t["vix0"]
        t["dvol_%dw" % wks] = (t["vix_%dw" % wks] / t["vix0"] - 1.0) * 100.0
    return t, spx


def tstat(s, nd):
    s = s.dropna()
    if len(s) < 5:
        return np.nan
    eff = max(len(s) / max(nd / 5.0, 1.0), 3.0)
    sd = s.std(ddof=1)
    return float(s.mean() / (sd / np.sqrt(eff))) if np.isfinite(sd) and sd > 0 else np.nan


def stat_block(sub):
    o = {"n": int(len(sub))}
    for wks, nd in HORIZONS:
        r = sub["ret_%dw" % wks].dropna()
        dv = sub["dvix_%dw" % wks].dropna()
        o["mean_ret_%dw" % wks] = float(r.mean()) if len(r) else np.nan
        o["win_%dw" % wks] = float((r > 0).mean() * 100) if len(r) else np.nan
        o["t_%dw" % wks] = tstat(r, nd)
        o["mean_dvix_%dw" % wks] = float(dv.mean()) if len(dv) else np.nan
        o["up_vix_prob_%dw" % wks] = float((dv > 0).mean() * 100) if len(dv) else np.nan
        # VIX 跳升频率：涨幅超过 +25%
        o["vix_jump25_prob_%dw" % wks] = float((sub["dvol_%dw" % wks].dropna() > 25).mean() * 100) if len(dv) else np.nan
        # SPX 回撤频率：跌幅超过 -5%
        o["spx_dd5_prob_%dw" % wks] = float((sub["ret_%dw" % wks].dropna() < -5).mean() * 100) if len(r) else np.nan
    return o


def row(label, st):
    def f(k, d=2):
        v = st.get(k, np.nan)
        return "" if pd.isna(v) else round(v, d)
    return {
        "分档": label, "样本周数": st["n"],
        "4周SPX均值%": f("mean_ret_4w"), "4周胜率%": f("win_4w"),
        "13周SPX均值%": f("mean_ret_13w"), "13周胜率%": f("win_13w"),
        "26周SPX均值%": f("mean_ret_26w"), "26周胜率%": f("win_26w"),
        "52周SPX均值%": f("mean_ret_52w"), "52周胜率%": f("win_52w"),
        "13周SPX跌超5%概率%": f("spx_dd5_prob_13w"),
        "52周SPX跌超5%概率%": f("spx_dd5_prob_52w"),
        "4周VIX变化": f("mean_dvix_4w"), "13周VIX变化": f("mean_dvix_13w"),
        "26周VIX变化": f("mean_dvix_26w"), "52周VIX变化": f("mean_dvix_52w"),
        "13周VIX上行概率%": f("up_vix_prob_13w"),
        "13周VIX涨超25%概率%": f("vix_jump25_prob_13w"),
        "26周VIX涨超25%概率%": f("vix_jump25_prob_26w"),
        "52周VIX涨超25%概率%": f("vix_jump25_prob_52w"),
        "13周t值": f("t_13w"), "52周t值": f("t_52w"),
    }


def table(t, rank_col, prefix):
    rows = [row(prefix + "全样本（基准）", stat_block(t))]
    v = t.dropna(subset=[rank_col])
    rows = [row(prefix + "全样本（基准）", stat_block(v))]
    for name, lo, hi in BUCKETS:
        sub = v[(v[rank_col] >= lo) & (v[rank_col] < hi)]
        rows.append(row(prefix + name, stat_block(sub)))
    return rows


def main():
    t, spx = build()

    # ------------------------------------------------------ cot_tff.csv
    out = pd.DataFrame({
        "报告日": t["report_date"].dt.strftime("%Y-%m-%d"),
        "交易对齐日": t["trade_date"].astype("datetime64[ns]").astype(str).str[:10],
        "总持仓": t["open_interest_all"],
        "杠杆基金多头": t["lev_money_positions_long"],
        "杠杆基金空头": t["lev_money_positions_short"],
        "杠杆基金净持仓": t["lev_net"],
        "杠杆基金净持仓占持仓%": t["lev_net_pct"].round(4),
        "杠杆基金空头拥挤度分位%": t["lev_short_rank"].round(2),
        "杠杆基金净持仓分位%(对照)": t["lev_net_rank"].round(2),
        "资管多头": t["asset_mgr_positions_long"],
        "资管空头": t["asset_mgr_positions_short"],
        "资管净持仓": t["asset_mgr_net"],
        "资管净持仓占持仓%": t["asset_mgr_net_pct"].round(4),
        "资管净持仓分位%": t["asset_mgr_rank"].round(2),
        "交易商净持仓": t["dealer_net"],
        "交易商净持仓占持仓%": t["dealer_net_pct"].round(4),
        "交易商净持仓分位%": t["dealer_rank"].round(2),
        "其他报告净持仓": t["other_rept_net"],
        "非报告净持仓": t["nonrept_net"],
        "VIX收盘": t["vix0"].round(4),
        "SPX收盘": t["spx0"].round(4),
        "SPX_4周收益%": t["ret_4w"].round(3),
        "SPX_13周收益%": t["ret_13w"].round(3),
        "SPX_26周收益%": t["ret_26w"].round(3),
        "SPX_52周收益%": t["ret_52w"].round(3),
        "VIX_13周变化": t["dvix_13w"].round(4),
        "VIX_26周变化": t["dvix_26w"].round(4),
        "VIX_52周变化": t["dvix_52w"].round(4),
    })
    out.to_csv(os.path.join(OUT_DIR, "cot_tff.csv"), index=False, encoding="utf-8-sig")

    # ------------------------------------------------ cot_tff_signal.csv
    rows = []
    rows += table(t, "lev_short_rank", "[杠杆基金空头拥挤度] ")
    rows += table(t, "asset_mgr_rank", "[资管净多分位] ")
    rows += table(t, "dealer_rank", "[交易商净多分位] ")
    sig = pd.DataFrame(rows)
    sig.to_csv(os.path.join(OUT_DIR, "cot_tff_signal.csv"), index=False, encoding="utf-8-sig")

    # ------------------------------------------- 与 Legacy 净头寸的相关
    legacy = pd.read_csv(os.path.join(OUT_DIR, "cot_positions.csv"),
                         encoding="utf-8-sig", parse_dates=["报告日"])
    m = t.merge(legacy[["报告日", "非商业净持仓"]].rename(columns={"报告日": "report_date"}),
                on="report_date", how="inner").sort_values("report_date")
    corr = {
        "n": int(len(m)),
        "corr_legacy_lev": float(m["lev_net"].corr(m["非商业净持仓"])),
        "corr_legacy_asset_mgr": float(m["asset_mgr_net"].corr(m["非商业净持仓"])),
        "corr_legacy_dealer": float(m["dealer_net"].corr(m["非商业净持仓"])),
        "corr_lev_asset_mgr": float(m["lev_net"].corr(m["asset_mgr_net"])),
        "corr_lev_dealer": float(m["lev_net"].corr(m["dealer_net"])),
        "corr_chg_legacy_lev": float(m["lev_net"].diff().corr(m["非商业净持仓"].diff())),
        "corr_chg_legacy_asset_mgr": float(m["asset_mgr_net"].diff().corr(m["非商业净持仓"].diff())),
        "corr_chg_legacy_dealer": float(m["dealer_net"].diff().corr(m["非商业净持仓"].diff())),
    }
    # 谁的信息更丰富：与未来 SPX 收益 / VIX 变化的相关系数对比
    for w, _ in HORIZONS:
        corr["corr_levnet_ret_%dw" % w] = float(t["lev_net"].corr(t["ret_%dw" % w]))
        corr["corr_asset_ret_%dw" % w] = float(t["asset_mgr_net"].corr(t["ret_%dw" % w]))
        corr["corr_dealer_ret_%dw" % w] = float(t["dealer_net"].corr(t["ret_%dw" % w]))
        corr["corr_legacy_ret_%dw" % w] = float(m["非商业净持仓"].corr(m["ret_%dw" % w])) \
            if "ret_%dw" % w in m.columns else np.nan
    for w, _ in HORIZONS:
        corr["corr_levcrowd_dvix_%dw" % w] = float(t["lev_short_crowding"].corr(t["dvix_%dw" % w]))
        corr["corr_levnet_dvix_%dw" % w] = float(t["lev_net"].corr(t["dvix_%dw" % w]))

    stats = {
        "n": int(len(t)),
        "dmin": str(t["report_date"].min().date()),
        "dmax": str(t["report_date"].max().date()),
        "lev_net_mean": float(t["lev_net"].mean()),
        "lev_net_neg_share": float((t["lev_net"] < 0).mean() * 100),
        "asset_net_mean": float(t["asset_mgr_net"].mean()),
        "asset_net_pos_share": float((t["asset_mgr_net"] > 0).mean() * 100),
        "dealer_net_mean": float(t["dealer_net"].mean()),
        "dealer_net_pos_share": float((t["dealer_net"] > 0).mean() * 100),
        "sum_nets_mean": float((t["dealer_net"] + t["asset_mgr_net"] + t["lev_net"]
                                + t["other_rept_net"] + t["nonrept_net"]).mean()),
        "lev_short_rank_max": float(t["lev_short_rank"].max()),
        "n_lev_crowd_gt90": int((t["lev_short_rank"] > 90).sum()),
        "lev_last_net": float(t["lev_net"].iloc[-1]),
        "lev_last_rank": float(t["lev_short_rank"].iloc[-1]) if pd.notna(t["lev_short_rank"].iloc[-1]) else None,
        "corr": corr,
    }
    with open(os.path.join(OUT_DIR, "..", ".tmp-cot-stage3.json"), "w", encoding="utf-8") as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)

    pd.set_option("display.width", 250)
    print(sig.to_string(index=False))
    print("\n" + json.dumps(stats, ensure_ascii=False, indent=2))
    print("\nWROTE:", os.path.join(OUT_DIR, "cot_tff.csv"))
    print("WROTE:", os.path.join(OUT_DIR, "cot_tff_signal.csv"))


if __name__ == "__main__":
    main()
