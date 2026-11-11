# -*- coding: utf-8 -*-
"""生成 Excel 数据册（多工作表）。"""
import os
import numpy as np, pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from openpyxl.utils.dataframe import dataframe_to_rows

RAW = r"E:\workspace\new\data\raw"; PROC = r"E:\workspace\new\data\processed"
OUT = r"E:\workspace\new\data\output"; XLSX = r"E:\workspace\new\output\美股主要指数回测数据册.xlsx"
os.makedirs(os.path.dirname(XLSX), exist_ok=True)

ORDER = ["SPX","DJI","IXIC","NDX","RUT","SOX"]
CN = {"SPX":"标普500","DJI":"道琼斯工业平均","IXIC":"纳斯达克综合","NDX":"纳斯达克100",
      "RUT":"罗素2000","SOX":"费城半导体"}
C = pd.read_csv(os.path.join(PROC,"prices_close.csv"), index_col=0, parse_dates=True)

# ---- 指标表 ----
m = pd.read_csv(os.path.join(OUT,"metrics_main.csv"), index_col=0)
mf = pd.read_csv(os.path.join(OUT,"metrics_full.csv"), index_col=0)
m.index = [CN[i] for i in m.index]; mf.index = [CN[i] for i in mf.index]

def build_main(m):
    t = pd.DataFrame({
        "指数": m.index,
        "数据起点": m["start"], "数据终点": m["end"],
        "样本交易日": m["n"].astype(int), "年数": m["years"].round(2),
        "累计收益%": (m["total"]*100).round(2), "年化收益%": (m["cagr"]*100).round(2),
        "年化波动%": (m["vol"]*100).round(2), "夏普比率": m["sharpe"].round(3),
        "索提诺比率": m["sortino"].round(3), "最大回撤%": (m["mdd"]*100).round(2),
        "卡玛比率": m["calmar"].round(3), "最大回撤持续(交易日)": m["mdd_dur_days"].astype(int),
        "当前回撤%": (m["cur_dd"]*100).round(2),
        "偏度": m["skew"].round(3), "超额峰度": m["kurt"].round(2),
        "日胜率%": (m["win_rate"]*100).round(2),
        "单日最大涨幅%": (m["best_day"]*100).round(2), "单日最大跌幅%": (m["worst_day"]*100).round(2),
        "单月最大涨幅%": (m["best_month"]*100).round(2), "单月最大跌幅%": (m["worst_month"]*100).round(2),
        "VaR95%(日)%": (m["var95"]*100).round(2), "CVaR95%(日)%": (m["cvar95"]*100).round(2),
        "均值无风险利率%": (m["rf_avg"]*100).round(2),
    })
    return t.set_index("指数")

t_main = build_main(m)
t_full = build_main(mf)

ph = pd.read_csv(os.path.join(OUT,"phases.csv"))
ph["指数名"] = ph["指数"].map(CN)
piv_cum = (ph.pivot_table(index=["类型","阶段"], columns="指数名", values="cumret", sort=False)*100).round(1)
piv_ann = (ph.pivot_table(index=["类型","阶段"], columns="指数名", values="ann", sort=False)*100).round(1)
piv_vol = (ph.pivot_table(index=["类型","阶段"], columns="指数", values="vol", sort=False)*100).round(1)
piv_shp = ph.pivot_table(index=["类型","阶段"], columns="指数", values="sharpe", sort=False).round(2)
piv_mdd = (ph.pivot_table(index=["类型","阶段"], columns="指数", values="mdd", sort=False)*100).round(1)
for d in (piv_vol, piv_shp, piv_mdd):
    d.columns = [CN[c] for c in d.columns]
rng = ph.drop_duplicates("阶段").set_index("阶段")[["起始","结束","类型"]]

def with_meta(p, cols):
    out = p.copy()
    out.insert(0, "类型", [i[0] for i in out.index])
    out.insert(1, "起始", [rng.loc[i[1],"起始"] for i in out.index])
    out.insert(2, "结束", [rng.loc[i[1],"结束"] for i in out.index])
    out.index = [i[1] for i in out.index]
    out.index.name = "阶段"
    return out

ann = pd.read_csv(os.path.join(OUT,"annual_returns.csv"), index_col=0)
ann.columns = [CN[c] for c in ann.columns]
sec = pd.read_csv(os.path.join(OUT,"sector_weights.csv"), index_col=0)
conc = pd.read_csv(os.path.join(OUT,"concentration.csv"), index_col=0)
cap = pd.read_csv(os.path.join(OUT,"market_cap_est.csv"))
style = pd.read_csv(os.path.join(OUT,"style_corr.csv"), index_col=0)
style.index = [CN[i] for i in style.index]
cap_cols = pd.read_csv(os.path.join(OUT,"capture_beta.csv"), index_col=0)
cap_cols.index = [CN[i] for i in cap_cols.index]
corr = pd.read_csv(os.path.join(OUT,"corr_daily.csv"), index_col=0)
corr.index = [CN[i] for i in corr.index]; corr.columns = [CN[c] for c in corr.columns]
dd_ep = pd.read_csv(os.path.join(OUT,"drawdown_episodes.csv"))
dd_ep["指数"] = dd_ep["指数"].map(CN)

# ---- 写 Excel ----
HEAD = PatternFill("solid", fgColor="1F4E79")
HF = Font(color="FFFFFF", bold=True, size=10, name="微软雅黑")
BF = Font(size=10, name="微软雅黑")
THIN = Side(style="thin", color="BFBFBF")
BD = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)

wb = Workbook(); wb.remove(wb.active)

def sheet(name, df, note=None, widths=None):
    ws = wb.create_sheet(name)
    r0 = 1
    if note:
        ws.cell(1,1,note).font = Font(bold=True, size=10, name="微软雅黑", color="C00000")
        r0 = 3
    ws.cell(r0-1 if r0==3 else 1, 1)
    start_row = r0
    # 表头
    for j, c in enumerate([df.index.name or ""] + list(df.columns), start=1):
        cell = ws.cell(start_row, j, c)
        cell.fill = HEAD; cell.font = HF; cell.border = BD
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    for i, (idx, row) in enumerate(df.iterrows(), start=start_row+1):
        c0 = ws.cell(i, 1, str(idx)); c0.font = BF; c0.border = BD
        for j, v in enumerate(row.values, start=2):
            cell = ws.cell(i, j, v); cell.font = BF; cell.border = BD
            cell.alignment = Alignment(horizontal="right")
    if widths:
        for col, w in widths.items():
            ws.column_dimensions[col].width = w
    else:
        ws.column_dimensions["A"].width = 18
        for j in range(2, len(df.columns)+2):
            ws.column_dimensions[chr(64+j) if j <= 26 else "A"+chr(64+j-26)].width = 12
    ws.freeze_panes = ws.cell(start_row+1, 2)
    return ws

# 说明页
ws = wb.create_sheet("00_口径说明")
lines = [
 ("美股主要指数系统性回测与对比分析 — 数据册", 14, True),
 ("", 11, False),
 ("1. 回测区间", 11, True),
 ("主样本 1994-05-05 至 2026-11-06（六个指数均有数据的共同区间，共 8,183 个交易日，32.51 年）；各指数另有自身上市日起的全历史口径。", 10, False),
 ("2. 数据频率", 11, True),
 ("日频收盘价；年化换算按 252 个交易日；最大回撤按日频净值计算。", 10, False),
 ("3. 价格复权方式", 11, True),
 ("核心指标使用指数价格（price return），不含股息；另以标普500全收益指数与 SPY/QQQ/DIA/IWM 等 ETF 的复权净值作为股息影响的敏感性参考。", 10, False),
 ("4. 无风险利率", 11, True),
 ("13 周美国国库券次级市场收益率（^IRX，以贴现率报价），年化折算为日频 (1+r)^(1/252)-1；与财政部公布的券等价收益率交叉核对，中位差 0.033 个百分点。", 10, False),
 ("5. 业绩比较基准", 11, True),
 ("以标普500（SPX）为市场基准，计算上行/下行捕获率、Beta 与年化 Alpha；夏普比率的超额收益均相对上述无风险利率。", 10, False),
 ("6. 数据源与交叉核对", 11, True),
 ("主源 Yahoo Finance 日线；交叉核对源：CBOE 官方指数 CSV、纳斯达克官方 API、东方财富、新浪财经、雪球。重叠区间内 SPX/DJI 收盘价与 CBOE 完全一致，IXIC/NDX/SOX 与纳斯达克官方最大偏离 ≤0.15%。", 10, False),
 ("7. 阶段划分", 11, True),
 ("事后（ex-post）划分，以标普500的阶段高点/低点为界；不足 1 年的阶段不年化，夏普与卡玛标记为 n.a.。", 10, False),
]
for i, (txt, sz, bold) in enumerate(lines, start=1):
    c = ws.cell(i, 1, txt)
    c.font = Font(size=sz, bold=bold, name="微软雅黑")
    c.alignment = Alignment(wrap_text=True, vertical="top")
ws.column_dimensions["A"].width = 150
for i in range(1, len(lines)+1):
    ws.row_dimensions[i].height = None

sheet("01_绩效指标_主样本", t_main, "口径：1994-05-05 ~ 2026-11-06，指数价格收益，无风险利率=13周国库券")
sheet("02_绩效指标_全历史", t_full, "口径：各指数自身上市日起至 2026-11-06")
sheet("03_分阶段_累计收益", with_meta(piv_cum, list(piv_cum.columns)), "单位：%，阶段内累计涨跌幅")
sheet("04_分阶段_年化收益", with_meta(piv_ann, list(piv_ann.columns)), "单位：%；不足 1 年的阶段留空")
sheet("05_分阶段_波动率", with_meta(piv_vol, list(piv_vol.columns)), "单位：%，年化")
sheet("06_分阶段_夏普", with_meta(piv_shp, list(piv_shp.columns)), "不足 1 年的阶段留空")
sheet("07_分阶段_最大回撤", with_meta(piv_mdd, list(piv_mdd.columns)), "单位：%，阶段内峰谷回撤")
sheet("08_年度收益", ann, "单位：%，自然年（1994 年为 5 月起）")
sheet("09_行业权重", sec, "GICS 一级行业，2026-11-05 持仓快照（单位：%）")
conc.index.name = "指数"
sheet("10_集中度", conc, "HHI 与有效家数按权重平方和计算")
sheet("11_市值估计", cap, "以成分股市值/权重反推指数总市值，抽样估计")
sheet("12_风格相关", style, "日收益相关系数，2000-07 起")
sheet("13_捕获率Beta", cap_cols.round(3), "相对标普500，1994-05 起")
sheet("14_相关性矩阵", corr.round(3), "日收益相关系数")
sheet("15_回撤事件", dd_ep.set_index("指数"), "各指数前 5 大回撤，1994-05 起")

wb.save(XLSX)
print("saved", XLSX, os.path.getsize(XLSX)/1024, "KB", "sheets:", len(wb.sheetnames))
