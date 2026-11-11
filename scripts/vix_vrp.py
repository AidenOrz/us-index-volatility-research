# -*- coding: utf-8 -*-
"""
vix_vrp.py  --  VIX 相对随后已实现波动的偏差（波动率风险溢价 VRP）
输入: data/processed/timing_panel.csv (VIX), data/processed/prices_close.csv (SPX)
输出: data/output/vix_vrp.csv
定义:
  fwd_rv21 = std(log(SPX/SPX.shift(1)) 未来21个交易日的样本标准差) * sqrt(252) * 100
           = (lr.rolling(21).std()).shift(-21) * sqrt(252) * 100
  VRP      = VIX - fwd_rv21
幂等，可重复运行。
"""
import os
import numpy as np
import pandas as pd

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROC = os.path.join(BASE, "data", "processed")
OUT = os.path.join(BASE, "data", "output")
os.makedirs(OUT, exist_ok=True)

BINS = [-np.inf, 12, 15, 20, 25, 30, 40, np.inf]
LABELS = ["<12", "12-15", "15-20", "20-25", "25-30", "30-40", ">40"]


def build():
    px = pd.read_csv(os.path.join(PROC, "prices_close.csv"), index_col=0, parse_dates=True)
    spx = px["SPX"].astype(float).dropna()

    panel = pd.read_csv(os.path.join(PROC, "timing_panel.csv"), index_col=0, parse_dates=True)
    vix = panel["VIX"].astype(float)

    df = pd.DataFrame({"SPX": spx, "VIX": vix})

    # 对数收益
    lr = np.log(df["SPX"] / df["SPX"].shift(1))

    # 未来 21 个交易日的已实现波动（末尾 21 行天然为 NaN，不 fillna）
    fwd_rv21 = lr.rolling(21).std().shift(-21) * np.sqrt(252.0) * 100.0
    df["fwd_rv21"] = fwd_rv21

    # 未来 21 个交易日 SPX 收益（用于胜率/平均收益）
    df["fwd_ret21"] = (df["SPX"].shift(-21) / df["SPX"] - 1.0) * 100.0

    df["VRP"] = df["VIX"] - df["fwd_rv21"]
    return df.dropna(subset=["VIX", "fwd_rv21", "VRP"])


def agg_block(sub):
    return dict(
        天数=len(sub),
        VRP中位数=round(float(sub["VRP"].median()), 3),
        VRP占VIX比=round(float((sub["VRP"] / sub["VIX"]).median() * 100.0), 2),
        VRP均值=round(float(sub["VRP"].mean()), 3),
        VRP标准差=round(float(sub["VRP"].std(ddof=1)), 3),
        VRP正数占比=round(float((sub["VRP"] > 0).mean() * 100.0), 2),
        未来21日实现波动中位数=round(float(sub["fwd_rv21"].median()), 3),
        随后21日SPX平均收益=round(float(sub["fwd_ret21"].mean()), 3),
        随后21日胜率=round(float((sub["fwd_ret21"] > 0).mean() * 100.0), 2),
    )


def describe(sub, ref_ratio=None):
    """自动生成中文短说明；ref_ratio 为相邻档位的相对溢价率，用于判断收窄/放大"""
    vrp_med = float(sub["VRP"].median())
    vrp_pos = float((sub["VRP"] > 0).mean() * 100.0)
    ratio = float((sub["VRP"] / sub["VIX"]).median() * 100.0)
    if vrp_med > 6:
        base = "绝对偏差最大的两档之一（%.2f 点），但溢价率只有 %.1f%%，恐慌期 VIX 相对自身量级并不最贵" % (vrp_med, ratio)
    elif vrp_med > 4:
        base = "绝对偏差偏高（%.2f 点），溢价率 %.1f%%，保险明显偏贵" % (vrp_med, ratio)
    elif vrp_med > 2:
        base = "绝对偏差温和（%.2f 点），溢价率 %.1f%%，风险溢价稳定存在" % (vrp_med, ratio)
    elif vrp_med > 0:
        base = "绝对偏差最薄（%.2f 点），溢价率 %.1f%%，此时买保险相对便宜" % (vrp_med, ratio)
    else:
        base = "负溢价：VIX 低于随后实现波动，买入波动反而合算"
    if ref_ratio is not None:
        if ratio < ref_ratio - 0.3:
            base += "（较上一档 %.1f%% 收窄）" % ref_ratio
        elif ratio > ref_ratio + 0.3:
            base += "（较上一档 %.1f%% 放大）" % ref_ratio
        else:
            base += "（与上一档 %.1f%% 基本持平）" % ref_ratio
    return base


def main():
    df = build()
    total = len(df)

    rows = []
    # ---- 分档 ----
    grp = pd.cut(df["VIX"], bins=BINS, labels=LABELS, right=False)
    prev_ratio = None
    for lab in LABELS:
        sub = df[grp == lab]
        if len(sub) == 0:
            rows.append(dict(VIX档=lab, 天数=0, **{"占比%": 0.0}, VRP中位数="", VRP均值="",
                             VRP标准差="", VRP正数占比="", VRP占VIX比="",
                             未来21日实现波动中位数="", 随后21日SPX平均收益="", 随后21日胜率="",
                             说明="该档无样本"))
            continue
        a = agg_block(sub)
        ratio = float((sub["VRP"] / sub["VIX"]).median() * 100.0)
        rows.append(dict(
            VIX档=lab,
            天数=a["天数"],
            **{"占比%": round(a["天数"] / total * 100.0, 2)},
            VRP中位数=a["VRP中位数"],
            VRP均值=a["VRP均值"],
            VRP标准差=a["VRP标准差"],
            VRP正数占比=a["VRP正数占比"],
            VRP占VIX比=a["VRP占VIX比"],
            未来21日实现波动中位数=a["未来21日实现波动中位数"],
            随后21日SPX平均收益=a["随后21日SPX平均收益"],
            随后21日胜率=a["随后21日胜率"],
            说明=describe(sub, prev_ratio),
        ))
        prev_ratio = ratio

    # ---- 全样本 ----
    a = agg_block(df)
    rows.append(dict(
        VIX档="全样本",
        天数=a["天数"],
        **{"占比%": 100.0},
        VRP中位数=a["VRP中位数"],
        VRP均值=a["VRP均值"],
        VRP标准差=a["VRP标准差"],
        VRP正数占比=a["VRP正数占比"],
        VRP占VIX比=a["VRP占VIX比"],
        未来21日实现波动中位数=a["未来21日实现波动中位数"],
        随后21日SPX平均收益=a["随后21日SPX平均收益"],
        随后21日胜率=a["随后21日胜率"],
        说明=("样本 %s~%s，VIX 中位数 %.2f、未来实现波动中位数 %.2f，"
              "VRP 中位数 %.2f，%0.2f%% 的交易日 VIX 高于随后实现波动"
              % (df.index.min().strftime("%Y-%m-%d"), df.index.max().strftime("%Y-%m-%d"),
                 float(df["VIX"].median()), a["未来21日实现波动中位数"],
                 a["VRP中位数"], a["VRP正数占比"])),
    ))

    out = pd.DataFrame(rows, columns=["VIX档", "天数", "占比%", "VRP中位数", "VRP均值", "VRP标准差",
                                      "VRP正数占比", "VRP占VIX比", "未来21日实现波动中位数",
                                      "随后21日SPX平均收益", "随后21日胜率", "说明"])
    out.to_csv(os.path.join(OUT, "vix_vrp.csv"), index=False, encoding="utf-8-sig")

    # ---- 控制台摘要 ----
    print("样本区间: %s ~ %s, 有效天数 %d" % (df.index.min().date(), df.index.max().date(), total))
    print("VIX 中位数 %.2f, 分位: p10=%.2f p25=%.2f p75=%.2f p90=%.2f"
          % (df["VIX"].median(), df["VIX"].quantile(.10), df["VIX"].quantile(.25),
             df["VIX"].quantile(.75), df["VIX"].quantile(.90)))
    print("fwd_rv21 中位数 %.2f, VRP 中位数 %.2f, 均值 %.2f, 标准差 %.2f, 正占比 %.2f%%"
          % (df["fwd_rv21"].median(), df["VRP"].median(), df["VRP"].mean(),
             df["VRP"].std(ddof=1), (df["VRP"] > 0).mean() * 100))
    print("VRP 分位: p10=%.2f p25=%.2f p75=%.2f p90=%.2f"
          % (df["VRP"].quantile(.10), df["VRP"].quantile(.25),
             df["VRP"].quantile(.75), df["VRP"].quantile(.90)))
    print("VRP 年化? 占 VIX 比例中位数 %.2f%%" % float((df["VRP"] / df["VIX"] * 100).median()))
    print()
    print(out[["VIX档", "天数", "占比%", "VRP中位数", "VRP占VIX比", "未来21日实现波动中位数", "随后21日SPX平均收益", "随后21日胜率"]].to_string(index=False))
    print()
    # 单调性/关键关系摘要
    print("== 关系摘要 ==")
    fwd = df["fwd_rv21"]
    print("VIX 与 fwd_rv21 全样本相关(原始) %.4f" % df["VIX"].corr(fwd))
    print("VIX 与 fwd_rv21 相关(对数) %.4f" % np.log(df["VIX"]).corr(np.log(fwd)))
    print("VRP 与 VIX 相关 %.4f" % df["VRP"].corr(df["VIX"]))
    print("VRP 与 fwd_ret21 相关 %.4f" % df["VRP"].corr(df["fwd_ret21"]))
    print("VIX 与 fwd_ret21 相关 %.4f" % df["VIX"].corr(df["fwd_ret21"]))
    # 双侧：VIX 高于/低于中位数时后续收益
    for lo, hi, tag in [(0, 0.2, "VIX最低20%"), (0.8, 1.0, "VIX最高20%")]:
        m = (df["VIX"] >= df["VIX"].quantile(lo)) & (df["VIX"] <= df["VIX"].quantile(hi))
        s = df[m]
        print("%s (VIX %.2f~%.2f): fwd_ret21 均值 %.2f%% 中位 %.2f%% 胜率 %.1f%%"
              % (tag, s["VIX"].min(), s["VIX"].max(), s["fwd_ret21"].mean(),
                 s["fwd_ret21"].median(), (s["fwd_ret21"] > 0).mean() * 100))
    print()
    print("写出:", os.path.join(OUT, "vix_vrp.csv"))


if __name__ == "__main__":
    main()
