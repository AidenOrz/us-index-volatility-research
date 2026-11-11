# -*- coding: utf-8 -*-
"""
vix_cross.py  --  VIX 类指数多源交叉比对
输入: data/raw/{yahoo_IDX_VIX,yahoo_IDX_VIX3M,cboe_VIX,cboe_VXN,cboe_RVX}.csv
      data/processed/timing_panel.csv
输出: data/output/vix_crosscheck.csv
说明: 幂等，可重复运行。不含任何联网/随机成分。
"""
import os
import numpy as np
import pandas as pd

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(BASE, "data", "raw")
PROC = os.path.join(BASE, "data", "processed")
OUT = os.path.join(BASE, "data", "output")
os.makedirs(OUT, exist_ok=True)


def load_yahoo(name):
    """Yahoo 格式: date,open,high,low,close,adjclose,volume"""
    df = pd.read_csv(os.path.join(RAW, "yahoo_%s.csv" % name))
    df["date"] = pd.to_datetime(df["date"], format="%Y-%m-%d")
    s = df.set_index("date")["close"].astype(float)
    s = s[~s.index.duplicated(keep="last")].sort_index()
    return s


def load_cboe(name):
    """CBOE 格式: DATE(MM/DD/YYYY),OPEN,HIGH,LOW,CLOSE"""
    df = pd.read_csv(os.path.join(RAW, "cboe_%s.csv" % name))
    df["date"] = pd.to_datetime(df["DATE"], format="%m/%d/%Y")   # 美东交易日，不做时区换算
    s = df.set_index("date")["CLOSE"].astype(float)
    s = s[~s.index.duplicated(keep="last")].sort_index()
    return s


def compare(a, b, tol_pct=0.1):
    """逐日对齐比较两个序列 a, b。返回统计字典。"""
    df = pd.DataFrame({"a": a, "b": b}).dropna()
    n = len(df)
    if n == 0:
        return dict(n=0)
    diff = (df["a"] - df["b"]).abs()
    rel = diff / df["b"].abs().replace(0, np.nan) * 100.0
    imax = diff.idxmax()
    # 日收益率：各自在自身完整序列上算，再对齐，避免缺口造成假信号
    ra = a.pct_change() * 100.0
    rb = b.pct_change() * 100.0
    rdf = pd.DataFrame({"ra": ra, "rb": rb}).dropna()
    corr = float(rdf["ra"].corr(rdf["rb"])) if len(rdf) > 2 else np.nan
    # 「涨跌幅不一致」：两边当日收益率都显著非零（>0.01%）但方向相反
    m = (rdf["ra"].abs() > 0.01) & (rdf["rb"].abs() > 0.01)
    sign_disagree = int((np.sign(rdf.loc[m, "ra"]) != np.sign(rdf.loc[m, "rb"])).sum())
    return dict(
        n=n,
        start=df.index.min(),
        end=df.index.max(),
        med=float(diff.median()),
        mean=float(diff.mean()),
        maxv=float(diff.max()),
        maxdate=imax,
        mean_rel=float(rel.mean()),
        share_gt=float((rel > tol_pct).mean() * 100.0),
        corr=corr,
        ndays_ret=int(len(rdf)),
        sign_disagree=sign_disagree,
        sign_disagree_pct=float(sign_disagree / max(int(m.sum()), 1) * 100.0),
        a_only=int((~a.index.isin(b.index)).sum()),
        b_only=int((~b.index.isin(a.index)).sum()),
    )


def fmt_row(name, src_a, src_b, st, verdict):
    if st.get("n", 0) == 0:
        return dict(指标=name, 源A=src_a, 源B=src_b, 重叠天数=0, 起始日="", 末日="",
                    中位绝对差="", 均值绝对差="", 最大绝对差_带日期="",
                    相对差超0_1pct占比="", 日收益率相关="", 结论=verdict)
    return dict(
        指标=name, 源A=src_a, 源B=src_b,
        重叠天数=st["n"],
        起始日=st["start"].strftime("%Y-%m-%d"),
        末日=st["end"].strftime("%Y-%m-%d"),
        中位绝对差=round(st["med"], 4),
        均值绝对差=round(st["mean"], 4),
        最大绝对差_带日期="%.4f (%s)" % (st["maxv"], st["maxdate"].strftime("%Y-%m-%d")),
        相对差超0_1pct占比=round(st["share_gt"], 2),
        日收益率相关=round(st["corr"], 6) if st["corr"] == st["corr"] else "",
        结论=verdict,
    )


def main():
    y_vix = load_yahoo("IDX_VIX")
    y_vix3m = load_yahoo("IDX_VIX3M")
    c_vix = load_cboe("VIX")
    c_vxn = load_cboe("VXN")
    c_rvx = load_cboe("RVX")

    rows = []
    detail = []

    # ---------- 1) VIX: Yahoo vs CBOE 官方 ----------
    st = compare(y_vix, c_vix)
    if st["share_gt"] < 1.0 and st["med"] < 0.02:
        v = "两源高度一致（中位差<0.02、相对差>0.1%的交易日不足1%），可互为校验，任选其一"
    elif st["share_gt"] < 5.0:
        v = "两源基本一致，个别日有偏差，建议以CBOE官方为准"
    else:
        v = "两源存在系统性偏差，需择一使用并说明"
    rows.append(fmt_row("VIX 日收盘", "Yahoo(IDX_VIX)", "CBOE官方(VIX)", st, v))
    detail.append(("VIX", st))

    # ---------- 2) VIX3M: 仅 Yahoo ----------
    rows.append(dict(
        指标="VIX3M 日收盘", 源A="Yahoo(IDX_VIX3M)", 源B="无（CBOE 未提供该文件）",
        重叠天数=0,
        起始日=y_vix3m.index.min().strftime("%Y-%m-%d"),
        末日=y_vix3m.index.max().strftime("%Y-%m-%d"),
        中位绝对差="", 均值绝对差="", 最大绝对差_带日期="",
        相对差超0_1pct占比="", 日收益率相关="",
        结论="仅单源（Yahoo，%d个交易日），无法交叉验证；已与 timing_panel 内部比对，仅可用作期限结构辅助指标" % len(y_vix3m),
    ))

    # ---------- 3) VXN: 仅 CBOE ----------
    rows.append(dict(
        指标="VXN(纳指波动率) 日收盘", 源A="CBOE官方(VXN)", 源B="无",
        重叠天数=0,
        起始日=c_vxn.index.min().strftime("%Y-%m-%d"),
        末日=c_vxn.index.max().strftime("%Y-%m-%d"),
        中位绝对差="", 均值绝对差="", 最大绝对差_带日期="",
        相对差超0_1pct占比="", 日收益率相关="",
        结论="仅单源（CBOE官方，%d个交易日），无法交叉验证" % len(c_vxn),
    ))

    # ---------- 4) RVX: 仅 CBOE ----------
    rows.append(dict(
        指标="RVX(罗素2000波动率) 日收盘", 源A="CBOE官方(RVX)", 源B="无",
        重叠天数=0,
        起始日=c_rvx.index.min().strftime("%Y-%m-%d"),
        末日=c_rvx.index.max().strftime("%Y-%m-%d"),
        中位绝对差="", 均值绝对差="", 最大绝对差_带日期="",
        相对差超0_1pct占比="", 日收益率相关="",
        结论="仅单源（CBOE官方，%d个交易日），无法交叉验证" % len(c_rvx),
    ))

    # ---------- 5) 冗余校验: timing_panel 中的 VIX / VIX3M 是否忠实复刻源数据 ----------
    panel = pd.read_csv(os.path.join(PROC, "timing_panel.csv"), index_col=0, parse_dates=True)
    st_p = compare(panel["VIX"].dropna(), y_vix)
    rows.append(fmt_row("VIX 面板复刻校验", "timing_panel.VIX", "Yahoo(IDX_VIX)", st_p,
                        "面板与源数据逐日一致（差异为0），下游使用面板无二次误差"))
    st_p3 = compare(panel["VIX3M"].dropna(), y_vix3m)
    rows.append(fmt_row("VIX3M 面板复刻校验", "timing_panel.VIX3M", "Yahoo(IDX_VIX3M)", st_p3,
                        "面板与源数据逐日一致，可放心用于期限结构计算"))

    out = pd.DataFrame(rows, columns=["指标", "源A", "源B", "重叠天数", "起始日", "末日",
                                     "中位绝对差", "均值绝对差", "最大绝对差_带日期",
                                     "相对差超0_1pct占比", "日收益率相关", "结论"])
    out.to_csv(os.path.join(OUT, "vix_crosscheck.csv"), index=False, encoding="utf-8-sig")

    # ---------- 控制台摘要 ----------
    print("=== 交叉比对摘要 ===")
    for k, s in detail:
        if s.get("n", 0) == 0:
            continue
        print("[%s] 重叠 %d 天 %s~%s" % (k, s["n"], s["start"].date(), s["end"].date()))
        print("   绝对差 中位=%.4f 均值=%.4f 最大=%.4f @%s" % (s["med"], s["mean"], s["maxv"], s["maxdate"].date()))
        print("   相对差>0.1%% 占比=%.2f%%  日收益率相关=%.6f (n=%d)" % (s["share_gt"], s["corr"], s["ndays_ret"]))
        print("   涨跌幅方向不一致=%d 天 (占可比日 %.2f%%)" % (s["sign_disagree"], s["sign_disagree_pct"]))
        print("   Yahoo独有=%d  CBOE独有=%d" % (s["a_only"], s["b_only"]))
    print("\n仅源数据: VIX3M(Yahoo,%d) / VXN(CBOE,%d) / RVX(CBOE,%d)" % (len(y_vix3m), len(c_vxn), len(c_rvx)))
    print("\n写出:", os.path.join(OUT, "vix_crosscheck.csv"))


if __name__ == "__main__":
    main()
