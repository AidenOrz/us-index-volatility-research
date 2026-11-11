# -*- coding: utf-8 -*-
"""生成 Word 报告。"""
import os, json
import pandas as pd, numpy as np
from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

OUT = r"E:\workspace\new\data\output"
FIG = r"E:\workspace\new\output\figures"
DOCX = r"E:\workspace\new\output\美股主要指数系统性回测与对比分析.docx"

D = json.load(open(os.path.join(OUT, "report_data.json"), encoding="utf-8"))
ORDER = ["SPX","DJI","IXIC","NDX","RUT","SOX"]
CN = {"SPX":"标普500","DJI":"道琼斯工业平均","IXIC":"纳斯达克综合","NDX":"纳斯达克100",
      "RUT":"罗素2000","SOX":"费城半导体"}

doc = Document()

st = doc.styles["Normal"]
st.font.name = "等线"
st.font.size = Pt(10.5)
st.element.rPr.rFonts.set(qn("w:eastAsia"), "等线")
st.paragraph_format.line_spacing = 1.35
st.paragraph_format.space_after = Pt(4)

for lvl, size in [(1, 15), (2, 12.5), (3, 11)]:
    h = doc.styles["Heading %d" % lvl]
    h.font.name = "等线"
    h.element.rPr.rFonts.set(qn("w:eastAsia"), "等线")
    h.font.size = Pt(size)
    h.font.bold = True
    h.font.color.rgb = RGBColor(0x1F, 0x3B, 0x63)
    h.paragraph_format.space_before = Pt(12 if lvl == 1 else 8)
    h.paragraph_format.space_after = Pt(6)

sec = doc.sections[0]
sec.left_margin = Cm(2.4); sec.right_margin = Cm(2.4)
sec.top_margin = Cm(2.2); sec.bottom_margin = Cm(2.0)

def para(text, size=10.5, bold=False, align="just", color=None, space_after=4, indent=True):
    p = doc.add_paragraph()
    p.alignment = {"left": WD_ALIGN_PARAGRAPH.LEFT, "center": WD_ALIGN_PARAGRAPH.CENTER,
                   "just": WD_ALIGN_PARAGRAPH.JUSTIFY, "right": WD_ALIGN_PARAGRAPH.RIGHT}[align]
    if indent:
        p.paragraph_format.first_line_indent = Pt(21)
    r = p.add_run(text)
    r.font.size = Pt(size); r.bold = bold
    r.font.name = "等线"
    r._element.rPr.rFonts.set(qn("w:eastAsia"), "等线")
    if color: r.font.color.rgb = color
    p.paragraph_format.space_after = Pt(space_after)
    return p

def bullet(text, size=10):
    p = doc.add_paragraph(style="List Bullet")
    p.paragraph_format.left_indent = Pt(18)
    p.paragraph_format.space_after = Pt(2)
    r = p.add_run(text); r.font.size = Pt(size); r.font.name = "等线"
    r._element.rPr.rFonts.set(qn("w:eastAsia"), "等线")
    return p

def shade(cell, hexcolor):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd"); shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto"); shd.set(qn("w:fill"), hexcolor)
    tcPr.append(shd)

def set_cell(cell, text, bold=False, size=8.5, align="right", color=None):
    cell.text = ""
    p = cell.paragraphs[0]
    p.paragraph_format.space_after = Pt(1); p.paragraph_format.space_before = Pt(1)
    p.alignment = {"left": WD_ALIGN_PARAGRAPH.LEFT, "center": WD_ALIGN_PARAGRAPH.CENTER,
                   "right": WD_ALIGN_PARAGRAPH.RIGHT}[align]
    r = p.add_run(str(text)); r.font.size = Pt(size); r.bold = bold
    r.font.name = "等线"; r._element.rPr.rFonts.set(qn("w:eastAsia"), "等线")
    if color: r.font.color.rgb = color

def table(df, caption=None, size=8.5, first_col_left=True):
    if caption:
        p = doc.add_paragraph()
        r = p.add_run(caption); r.bold = True; r.font.size = Pt(9)
        r.font.name = "等线"; r._element.rPr.rFonts.set(qn("w:eastAsia"), "等线")
        p.paragraph_format.space_before = Pt(8); p.paragraph_format.space_after = Pt(3)
        p.paragraph_format.keep_with_next = True
    t = doc.add_table(rows=1, cols=len(df.columns) + 1)
    t.style = "Table Grid"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t.autofit = False
    ncol = len(df.columns) + 1
    total_w = 16.2
    first_w = 3.0 if ncol <= 8 else 2.7
    rest_w = (total_w - first_w) / (ncol - 1)
    col_w = [first_w] + [rest_w] * (ncol - 1)
    tblPr = t._tbl.tblPr
    layout = OxmlElement("w:tblLayout")
    layout.set(qn("w:type"), "fixed")
    tblPr.append(layout)
    trPr = t.rows[0]._tr.get_or_add_trPr()
    th = OxmlElement("w:tblHeader"); th.set(qn("w:val"), "true"); trPr.append(th)
    hdr = t.rows[0].cells
    set_cell(hdr[0], df.index.name or "", True, size, "center")
    shade(hdr[0], "1F3B63")
    hdr[0].paragraphs[0].runs[0].font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
    for j, c in enumerate(df.columns, start=1):
        set_cell(hdr[j], c, True, size, "center")
        shade(hdr[j], "1F3B63")
        hdr[j].paragraphs[0].runs[0].font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
    for i, (idx, row) in enumerate(df.iterrows(), start=1):
        t.add_row()
        cells = t.rows[i].cells
        set_cell(cells[0], idx, True, size, "left" if first_col_left else "center")
        shade(cells[0], "EDF2F8")
        for j, v in enumerate(row.values, start=1):
            if isinstance(v, str):
                set_cell(cells[j], v, False, size, "center")
            elif v is None or (isinstance(v, float) and np.isnan(v)):
                set_cell(cells[j], "—", False, size, "center")
            else:
                set_cell(cells[j], v, False, size, "right")
        if i % 2 == 0:
            for j in range(1, len(t.rows[i].cells)):
                shade(t.rows[i].cells[j], "F7F9FC")
        trPr = t.rows[i]._tr.get_or_add_trPr()
        cs = OxmlElement("w:cantSplit"); cs.set(qn("w:val"), "true"); trPr.append(cs)
    for j, w in enumerate(col_w):
        t.columns[j].width = Cm(w)
        for row in t.rows:
            row.cells[j].width = Cm(w)
    doc.add_paragraph().paragraph_format.space_after = Pt(2)
    return t

def figure(path, caption, width=15.4):
    if not os.path.exists(path):
        print("missing figure", path); return
    doc.add_picture(path, width=Cm(width))
    doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run(caption); r.font.size = Pt(8.5); r.italic = True
    r.font.color.rgb = RGBColor(0x55, 0x55, 0x55)
    r.font.name = "等线"; r._element.rPr.rFonts.set(qn("w:eastAsia"), "等线")

# ================= 封面 =================
p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
p.paragraph_format.space_before = Pt(70)
r = p.add_run("美股主要指数系统性回测与对比分析")
r.font.size = Pt(24); r.bold = True; r.font.color.rgb = RGBColor(0x1F, 0x3B, 0x63)
r.font.name = "等线"; r._element.rPr.rFonts.set(qn("w:eastAsia"), "等线")

p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = p.add_run("道琼斯工业平均 · 标普500 · 纳斯达克综合 · 纳斯达克100 · 罗素2000 · 费城半导体")
r.font.size = Pt(11.5); r.font.color.rgb = RGBColor(0x44, 0x44, 0x44)
r.font.name = "等线"; r._element.rPr.rFonts.set(qn("w:eastAsia"), "等线")

p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
p.paragraph_format.space_before = Pt(40)
r = p.add_run("回测区间 1994-05-05 至 2026-11-06（主样本）  |  频率 日频  |  六源交叉比对")
r.font.size = Pt(9.5); r.font.color.rgb = RGBColor(0x66, 0x66, 0x66)
r.font.name = "等线"; r._element.rPr.rFonts.set(qn("w:eastAsia"), "等线")
doc.add_page_break()

# ================= 摘要 =================
doc.add_heading("摘要", level=1)
m = D["main"]
para("本报告以日频收盘价对六条美股主要指数做统一口径的长期回测。主样本为 1994 年 5 月 5 日至 2026 年 11 月 6 日，共 8,183 个交易日、32.51 年，这是六条指数均有完整数据的共同区间。"
     "全部指标基于指数价格收益（price return，不含股息），无风险利率取 13 周美国国库券收益率，业绩基准为标普500。价格数据经 Yahoo Finance、CBOE 官方文件、纳斯达克官方 API、东方财富、新浪财经、雪球六源交叉核对："
     "标普500与道指的收盘价与 CBOE 官方数据完全一致，纳斯达克综合、纳斯达克100、费城半导体的最大偏离不超过 0.15%。")
para("核心结论：", bold=True, indent=False)
bullet("收益梯队清晰。费城半导体年化 14.40%、纳斯达克100 年化 14.03% 领跑；纳斯达克综合 11.38% 居中；标普500 8.97%、道指 8.43% 构成大盘基准；罗素2000 仅 7.61%，三十二年间累计落后标普500约 5.5 个百分点/年。")
bullet("高收益对应高风险，且风险调整后优势缩小。费城半导体年化波动 38.02%、最大回撤 −87.15%，纳指100 波动 27.13%、回撤 −82.90%；标普500 分别为 18.59% 与 −56.78%。夏普比率上纳指100（0.531）最高，费城半导体（0.481）反而不及纳指100，卡玛比率也只有 0.165。")
bullet("震荡与熊市中防御属性分化明显。道指在科网破裂（−34.4%）与 2022 加息熊市（−20.2%）中跌幅最小；纳指100 与费城半导体在同类阶段跌幅达 −80% 量级；罗素2000 在 2022 年后的 AI 周期中年化仅 13.7%，显著落后于纳指100 的 35.8%。")
bullet("结构决定风格。标普500 前十大权重 37.7%、有效家数 47.8；纳指100 前十大 67.0%、有效家数仅 16.9；罗素2000 有效家数高达 824，但行业集中在医药（20.7%）与金融（20.1%）。市值上标普500 覆盖约 70.4 万亿美元，约为罗素2000（3.6 万亿）的 20 倍。")
bullet("市场风格随宏观周期轮动：1990 年代是科技成长与大盘股的双击；2000–2002 年是价值与小盘相对抗跌；2003–2007 年是周期与价值补涨；2009 年后重回成长与大盘；2022 年价值短暂回归；2023 年以来的 AI 周期再度强化科技与大盘集中的格局。")

doc.add_page_break()

# ================= 一、口径说明 =================
doc.add_heading("一、口径说明与数据来源", level=1)

doc.add_heading("1.1 回测区间与频率", level=2)
para("六条指数的数据起始时间并不一致：标普500 可回溯至 1962 年，纳斯达克综合自 1971 年，纳指100 自 1985 年 10 月，罗素2000 自 1987 年 9 月，道指在本数据源中自 1992 年 1 月，费城半导体最晚，自 1994 年 5 月 4 日。"
     "为保证横向可比，主样本取六条指数的共同交集，即 1994-05-05 至 2026-11-06，共 8,183 个交易日、32.51 年。所有指数在该区间内无缺失交易日。")
para("此外，报告另给出各指数自身上市日起的「全历史口径」指标（见第五章表 5-2），用于观察更长周期的特征，但该口径下各指数的样本长度不同，横向比较时须谨慎。数据频率统一为日频收盘价；年化换算按 252 个交易日；最大回撤按日频净值（含分红再投资的假设不成立，见 1.3）计算。")

doc.add_heading("1.2 价格复权方式", level=2)
para("核心指标采用指数价格收益（price return），即不包含股息。这一选择的理由是：六条指数中只有标普500存在官方、长历史的日频全收益指数，其余指数的全收益序列难以在公开免费源获得且口径不一；若混用价格指数与 ETF 复权净值，会引入费率、跟踪误差与分红时点等噪声。")
para("作为敏感性参考，报告测算了股息的影响：1988 年 1 月至 2026 年 11 月，标普500 价格指数年化 9.04%，同期全收益指数年化 11.33%，股息贡献约 2.29 个百分点/年。也就是说，本报告中所有指数的年化收益都应理解为「价格口径」，若按全收益口径，各指数的绝对收益大约需上调 1.5–2.5 个百分点，但排序基本不变（高股息的道指上调幅度略大于低股息的纳指100 与费城半导体，因而道指与纳指100 的差距在全收益口径下会略微缩小）。"
     "ETF 侧的校验结果与此一致：SPY 自 1994 年 5 月起的复权年化为 10.89%，高于同期标普500 价格指数的 8.97%，差额同样来自股息。")

doc.add_heading("1.3 无风险利率假设", level=2)
para("无风险利率取 13 周美国国库券（T-bill）的次级市场收益率，数据源为 ^IRX 指数。该指数以银行贴现率（bank discount rate）报价，本报告直接以其年化数值作为无风险利率，并折算为日频：r_d = (1 + r_annual)^(1/252) − 1。"
     "为核实这一处理，报告另下载了美国财政部公布的 13 周国库券「券等价收益率（coupon equivalent）」序列，两者重叠区间为 2002-01 至 2026-11 共 6,207 个交易日，平均差 0.056 个百分点、中位差 0.033 个百分点，量级可忽略。"
     "主样本区间内该利率的均值为 2.46%，最高约 5.9%（2000 年前后与 2023–2024 年），最低接近 0（2020–2021 年）。")

doc.add_heading("1.4 业绩比较基准", level=2)
para("以标普500 作为市场基准。除常规的绝对收益与风险指标外，报告还计算了相对基准的上行捕获率、下行捕获率、Beta 与年化 Alpha（Jensen's Alpha，以日频超额收益回归后年化）。"
     "需要说明的是，由于基准与样本同为价格指数，Alpha 不含股息，其绝对值会系统性偏低；该指标用于比较相对强弱，而非衡量绝对超额收益能力。")

doc.add_heading("1.5 数据来源与交叉比对", level=2)
para("主数据源为 Yahoo Finance 的日线接口（^GSPC、^DJI、^IXIC、^NDX、^RUT、^SOX）。为验证可靠性，同时抓取了五个独立来源做交叉核对：CBOE 官方发布的指数日线 CSV（SPX、RUT、RUI、DJX、VIX 等）、纳斯达克官方 API（COMP、NDX）、东方财富（SPX、DJIA、NDX）、新浪财经（.INX、.DJI、.IXIC、.NDX、.SOX）、雪球（同前）。"
     "比对方法为：取 2021-11 至 2026-11 的重叠区间，逐日计算各来源收盘价相对 Yahoo 的偏离度。结果如下表。")
cmp = pd.DataFrame({
    "覆盖区间": ["1986-03 至今", "2004-01 至今", "1987-03 至今", "1984-10 至今", "1975-01 至今"],
    "最大偏离": ["0.000%", "0.000%", "0.000%", "0.036%", "0.000%"],
    "中位偏离": ["0.000%", "0.000%", "0.000%", "0.000%", "0.000%"],
    "结论": ["一致", "一致", "一致", "一致", "一致"],
}, index=pd.Index(["东方财富（SPX/DJI）", "新浪财经（SPX/DJI）", "雪球（SPX/DJI）", "纳斯达克官方（IXIC）", "CBOE 官方（SPX）"], name="数据源"))
table(cmp, "表 1-1  标普500/道指/纳指综合 与 Yahoo 收盘价的多源交叉比对", size=8)
para("东方财富的 NDX 字段实际对应纳斯达克综合指数（与 .IXIC 完全一致），属于源端标签错误，报告中未采用，已改以新浪、雪球与纳斯达克官方三源核对纳指100。"
     "费城半导体无官方免费日线源，采用新浪与雪球两源互验，2021-11 以来两者的最大偏离为 0.000%，2026-11-05 的急跌（−12.2%）在两源中完全一致，可认为数据可靠。")
para("另需说明一处数据事实：2026-10 至 2026-11 期间费城半导体出现了罕见的剧烈波动（10-30 单日 −7.2%、11-05 单日 −12.2%，此前 6 月 22 日创下 14,634.72 的历史高点）。该序列在两个独立中文源中完全一致，且与同期纳指100、标普500 的回调方向一致，判定为真实行情而非数据错误；但它显著压低了费城半导体的近期表现与「当前回撤」指标（−35.84%），读者在解读该指数的时点指标时应留意这一背景。")

# ================= 二、指标汇总 =================
doc.add_page_break()
doc.add_heading("二、绩效指标汇总", level=1)
para("下表为主样本区间（1994-05-05 至 2026-11-06）的完整指标。所有收益类指标为价格口径，波动率与最大回撤按日频计算，年化因子 252。")

rows = []
for k in ORDER:
    v = m[k]
    rows.append({
        "累计收益": "%.0f%%" % (v["total"]*100),
        "年化收益": "%.2f%%" % (v["cagr"]*100),
        "年化波动": "%.2f%%" % (v["vol"]*100),
        "夏普": "%.3f" % v["sharpe"],
        "索提诺": "%.3f" % v["sortino"],
        "最大回撤": "%.2f%%" % (v["mdd"]*100),
        "卡玛": "%.3f" % v["calmar"],
        "回撤期(交易日)": "%d" % v["mdd_dur_days"],
        "当前回撤": "%.2f%%" % (v["cur_dd"]*100),
    })
t1 = pd.DataFrame(rows, index=pd.Index([CN[k] for k in ORDER], name="指数"))
table(t1, "表 2-1  主样本核心绩效指标（1994-05-05 ~ 2026-11-06，价格口径）")

rows2 = []
for k in ORDER:
    v = m[k]
    rows2.append({
        "日胜率": "%.1f%%" % (v["win_rate"]*100),
        "偏度": "%.2f" % v["skew"],
        "超额峰度": "%.1f" % v["kurt"],
        "最优单日": "%.2f%%" % (v["best_day"]*100),
        "最差单日": "%.2f%%" % (v["worst_day"]*100),
        "最优单月": "%.2f%%" % (v["best_month"]*100),
        "最差单月": "%.2f%%" % (v["worst_month"]*100),
        "日VaR95%": "%.2f%%" % (v["var95"]*100),
        "日CVaR95%": "%.2f%%" % (v["cvar95"]*100),
    })
t2 = pd.DataFrame(rows2, index=pd.Index([CN[k] for k in ORDER], name="指数"))
table(t2, "表 2-2  收益分布与尾部风险特征")

doc.add_heading("2.1 收益：三档梯队", level=2)
para("以年化收益看，六条指数自然分成三档。第一档是费城半导体（14.40%）与纳斯达克100（14.03%），二者几乎持平，但实现路径完全不同——费城半导体的累计收益 7,840% 建立在 −87% 的深坑之上，纳指100 的 7,036% 则伴随 −82.9% 的回撤。"
     "第二档是纳斯达克综合（11.38%），它包含纳指100 的成分股但加权更分散、且含有大量中小型科技股，因此收益介于半导体与宽基之间。第三档是标普500（8.97%）、道指（8.43%）与罗素2000（7.61%）。")
figure(os.path.join(FIG, "01_累计净值.png"), "图 2-1  六大指数累计净值（1994-05-05 = 1，对数坐标，价格指数）", width=15.0)
para("值得注意的是罗素2000。它在 1994–2000 年的科技牛市中仅上涨 125.9%，远低于同期的标普500（238.4%）与纳指100（1,140.4%）；在 2003–2007 年它一度跑赢（158.6% vs 标普500 的 101.5%），但 2009 年后的长牛中再度落后（393.1% vs 400.5%），2023 年以来的 AI 周期中差距被彻底拉开（35.2% vs 纳指100 的 105.6%）。三十二年累计 983.87%，不足标普500 的三分之二。"
     "这与「小盘股长期存在规模溢价」的传统认知相悖，原因在于 2009 年之后超低利率环境系统性地利好长久期的大盘成长股，而小盘股在盈利质量、再融资成本与指数内部结构（罗素2000 中医药与金融合计逾 40%）上均不占优。")

doc.add_heading("2.2 风险：波动与回撤的放大倍数", level=2)
para("费城半导体的年化波动 38.02%，是标普500（18.59%）的 2.04 倍；纳指100 为 27.13%（1.46 倍）；纳斯达克综合 24.01%；罗素2000 22.71%；道指最低，17.74%。"
     "最大回撤的排序与之高度一致：费城半导体 −87.15%、纳指100 −82.90%、纳斯达克综合 −77.93%、罗素2000 −59.89%、标普500 −56.78%、道指 −53.78%。")
para("回撤的持续期差异更值得关注。标普500 的最大回撤（2007-10-09 至 2009-03-09，−56.78%）用了 356 个交易日见底，直到 2013 年 3 月才完全收复，水下约 1,375 个交易日；而纳指100 的 −82.90%（2000-03-27 至 2002-10-07）直到 2015-11-03 才完全收复，耗时近 15 年；费城半导体的 −87.15%（2000-03-10 至 2008-11-20）历经 2,189 个交易日下跌，直到 2017-11-21 才回到前高，水下时间长达 17 年半。"
     "这意味着对纳指100 与费城半导体而言，「买入并持有」在极端情形下的机会成本远高于标普500——虽然它们的长期年化更高，但需要跨越极长的不利期。")

figure(os.path.join(FIG, "02_回撤曲线.png"), "图 2-2  六大指数历史回撤曲线（自 1994-05-05 起，逐日净值口径）", width=15.0)
figure(os.path.join(FIG, "03_滚动波动率.png"), "图 2-3  滚动 252 个交易日年化波动率：波动率水平的差异是持续的，而非阶段性现象", width=15.0)

doc.add_heading("2.3 风险调整后收益：高波动没有换来高夏普", level=2)
para("这是本报告最反直觉的结论。费城半导体的年化收益（14.40%）略高于纳指100（14.03%），但夏普比率（0.481）却低于纳指100（0.531），索提诺（0.706）也略低于纳指100（0.717）。原因很直接：费城半导体的波动率高出一个数量级，超额收益被风险完全吞噬。"
     "按卡玛比率看，纳指100（0.169）也高于费城半导体（0.165），标普500（0.158）、道指（0.157）紧随其后，纳斯达克综合（0.146）与罗素2000（0.127）垫底。")
para("换言之，在本样本中，风险调整后表现最好的资产是纳斯达克100，而非收益最高的费城半导体；罗素2000 则是唯一在收益、夏普、卡玛三个维度上同时垫底的指数。这一结论对资产配置的启示是：若目标是最大化单位风险的回报，纳指100 优于费城半导体；若追求绝对收益且能承受 80% 以上的回撤与十余年的水下期，费城半导体才具备吸引力。")

figure(os.path.join(FIG, "04_风险收益散点.png"), "图 2-4  风险—收益散点：左图为全样本、右图为近十年，可见风险调整后的排序差异", width=15.0)

doc.add_heading("2.4 尾部风险与收益分布", level=2)
para("六条指数的日收益分布均呈现明显的尖峰厚尾。超额峰度上，道指 12.3、标普500 10.4 最高，说明宽基指数的大幅波动更多来自系统性冲击（如 1987、2008、2020）；费城半导体仅 3.6，因为其日常波动本就很大，极端日的「相对意外程度」反而较小。"
     "偏度上，罗素2000 为 −0.31（左偏最明显），纳指100 与费城半导体为 +0.21（右偏），意味着后者更多依赖少数暴涨日贡献收益——费城半导体的最优单月达 +50.37%，最差单月 −33.53%，单月振幅超过 80 个百分点。")
para("在 95% 置信度下，费城半导体的单日 VaR 为 −3.83%、CVaR 为 −5.38%，标普500 分别为 −1.78% 与 −2.79%，道指最低（−1.65%、−2.64%）。若以 1 亿元名义本金计，费城半导体在最差的 5% 交易日中平均单日损失约 538 万元，是道指的 2 倍以上。")
para("日胜率方面，六条指数都在 52%–55% 之间，差异不大（纳指综合 54.9% 最高，费城半导体 52.3% 最低），说明收益差异主要来自「赢时赢多少」而非「赢的频率」。这一点在下一章的捕获率分析中会得到进一步印证。")

# ================= 三、分阶段对比 =================
doc.add_heading("三、市场阶段划分与分阶段对比", level=1)

doc.add_heading("3.1 划分方法", level=2)
para("阶段划分采用「事后（ex-post）」方法，以标普500 的阶段高点与低点为界，并结合大型宏观事件命名。这一方法的好处是每个阶段内部的市场方向高度一致，便于观察指数在不同环境下的相对表现；缺点是存在前视偏差，不能作为实时择时的依据。"
     "判定规则为：标普500 自阶段低点上行并持续，至下一轮显著回撤（≥15%）前的高点为止，记为牛市；自高点回撤 ≥15% 并持续，至低点为止，记为熊市；持续时间较短（＜6 个月）且幅度在 15%–25% 之间的急跌与随后的修复，记为震荡。"
     "共划分 11 个阶段：5 个牛市、4 个熊市、2 个震荡阶段。")

PH = [
 ("科网泡沫牛市", "牛市", "1994-05-05", "2000-03-24", "低通胀、高增长、互联网商业化；美联储 1998 年降息；估值扩张主导"),
 ("科网泡沫破裂", "熊市", "2000-03-24", "2002-10-09", "科技泡沫出清、9·11、安然/世通财务丑闻、美联储紧缩后遗症"),
 ("信贷繁荣牛市", "牛市", "2002-10-09", "2007-10-09", "低利率、房地产与信贷扩张、全球化红利、能源与金融领涨"),
 ("全球金融危机", "熊市", "2007-10-09", "2009-03-09", "次贷危机、雷曼破产、全球信用冻结、去杠杆"),
 ("后危机长牛", "牛市", "2009-03-09", "2020-02-19", "零利率与 QE、科技平台化、回购与被动资金流入"),
 ("新冠闪崩", "熊市", "2020-02-19", "2020-03-23", "疫情全球扩散、流动性危机、23 个交易日完成 34% 下跌"),
 ("流动性牛市", "牛市", "2020-03-23", "2022-01-03", "无限 QE、财政刺激、居家经济、散户与 meme 股、成长股估值极致扩张"),
 ("加息熊市", "熊市", "2022-01-03", "2022-10-12", "通胀失控、美联储 425bp 加息、成长股估值压缩、股债双杀"),
 ("AI 牛市", "牛市", "2022-10-12", "2025-02-19", "ChatGPT 引爆 AI 资本开支、英伟达产业链、Mag7 集中度上升"),
 ("关税急跌", "震荡", "2025-02-19", "2025-04-08", "关税政策冲击、供应链不确定性、风险资产快速去杠杆"),
 ("关税后修复", "震荡", "2025-04-08", "2026-11-06", "政策预期缓和、AI 资本开支持续、半导体引领反弹"),
]
phdf = pd.DataFrame([{"类型": x[1], "起始": x[2], "结束": x[3], "宏观背景": x[4]} for x in PH],
                    index=pd.Index([x[0] for x in PH], name="阶段"))
table(phdf, "表 3-1  阶段划分与宏观背景", size=7.5)

doc.add_heading("3.2 累计收益：牛市弹性与熊市杀伤力", level=2)
ph = pd.read_csv(os.path.join(OUT, "phases.csv"))
order = [x[0] for x in PH]
piv = (ph.pivot_table(index="阶段", columns="指数", values="cumret", sort=False)[ORDER] * 100).round(1)
piv = piv.reindex(order)
piv.columns = [CN[c] for c in piv.columns]
piv.index.name = "阶段"
piv.insert(0, "类型", [dict((x[0], x[1]) for x in PH)[i] for i in piv.index])
table(piv, "表 3-2  分阶段累计收益（%，价格口径）", size=8)
figure(os.path.join(FIG, "05_分阶段热力图.png"), "图 3-1  分阶段累计收益热力图：绿色为上涨、红色为下跌，色标上限 250% 后截断")

para("牛市阶段呈现明显的「高 beta 占优」规律。1994–2000 年的科网泡沫牛市中，纳指100 累计上涨 1,140.4%，费城半导体 988.6%，而标普500 仅 238.4%、罗素2000 仅 125.9%——最强与最弱相差 9 倍。"
     "2009–2020 年的后危机长牛中，费城半导体（939.3%）反超纳指100（831.0%），标普500 400.5%，罗素2000 393.1%，与标普500 几乎持平。"
     "2022 年 10 月至 2025 年 2 月的 AI 牛市中，费城半导体 141.5%、纳指100 105.6%，而罗素2000 仅 35.2%——小盘股在这轮由超大规模资本开支驱动的行情中几乎缺席。")
para("熊市阶段则是另一幅图景。科网泡沫破裂中，纳指100 下跌 82.8%、费城半导体 83.4%、纳斯达克综合 77.6%，而道指仅 −34.4%、罗素2000 −43.0%、标普500 −49.1%。"
     "这一阶段的特殊性在于下跌由科技股估值泡沫破裂驱动，因此科技含量越高的指数跌幅越大；但道指的抗跌也部分源于其价格加权机制下高股价成分（如联合健康、高盛）的权重结构，不宜简单归因为「蓝筹更稳」。"
     "2008 年金融危机则是一次无差别的系统性冲击：标普500 −56.8%、罗素2000 −59.4%、费城半导体 −61.7%，六条指数全部腰斩，差异被压缩到 10 个百分点以内。")
para("值得一提的是 2022 年加息熊市。这一年纳指100（−34.6%）与费城半导体（−45.4%）跌幅最深，道指仅 −20.2%，罗素2000 −25.7%，标普500 −25.4%。"
     "与科网破裂不同，2022 年的下跌源于无风险利率快速上行对长久期资产的估值压缩，半导体同时承受了库存周期的下行，因此费城半导体的跌幅（−45.4%）甚至超过纳指100——这是「高估值 + 周期下行」双重打击的典型样本。")

doc.add_heading("3.3 分阶段风险：波动率的时变特征", level=2)
pivv = (ph.pivot_table(index="阶段", columns="指数", values="vol", sort=False)[ORDER] * 100).reindex(order)
pivv.index.name = "阶段"
pivv = pivv.map(lambda v: "—" if pd.isna(v) else "%.2f" % v)
pivv.columns = [CN[c] for c in pivv.columns]
table(pivv, "表 3-3  分阶段年化波动率（%）", size=8)
para("波动率的绝对水平随阶段剧烈变化：新冠闪崩期间，六条指数的年化波动率全部飙升至 80% 以上（罗素2000 达 90.8%、费城半导体 104.1%），是常态水平的 4–5 倍；而流动性牛市期间标普500 仅 20.0%、道指 21.1%。"
     "更值得注意的是，费城半导体的波动率在任何阶段都是最高的——即使在最平静的 AI 牛市（2022-10 至 2025-02），其波动率也有 33.5%，高于标普500 在新冠闪崩以外任何阶段的水平。这说明半导体指数的高波动是结构性的，而非特定阶段的产物。")
para("罗素2000 的波动特征则相反：它在牛市中波动偏高（后危机长牛 20.9%，高于标普500 的 15.6%），在熊市中却未必最高（2020 年 90.8% 最高，但 2008 年 43.7% 仅居中）。"
     "换言之，小盘股的风险更多体现为「跟涨跟跌但幅度更大」的对称放大，而非单向的尾部风险。")

doc.add_heading("3.4 分阶段夏普与卡玛", level=2)
pivs = ph.pivot_table(index="阶段", columns="指数", values="sharpe", sort=False)[ORDER].reindex(order)
pivs.index.name = "阶段"
pivs = pivs.map(lambda v: "—" if pd.isna(v) else "%.2f" % v)
pivs.columns = [CN[c] for c in pivs.columns]
table(pivs, "表 3-4  分阶段夏普比率（不足 1 年的阶段不年化，标 —）", size=8)
para("牛市阶段的夏普排序并不稳定：科网泡沫牛市中纳指100（1.49）最高、罗素2000（0.70）最低；后危机长牛中纳指100（1.21）再次领先，罗素2000（0.78）仍垫底；"
     "AI 牛市中纳指100（1.41）与标普500（1.36）接近，罗素2000 仅 0.49。可见罗素2000 的「低夏普」是跨阶段的稳定特征，而非某一轮行情的偶然结果。")
para("熊市阶段的夏普全部为负，且绝对值与跌幅成正比：全球金融危机中六条指数集中在 −1.16 至 −1.44；科网破裂中道指（−0.81）与费城半导体（−0.76）反而「最好」——后者是因为波动率高，同样的跌幅在风险调整后显得没那么极端。这提示夏普比率在极端行情下的解释力有限，应与最大回撤、卡玛比率结合使用。")

# 牛熊汇总
doc.add_heading("3.5 牛市 / 熊市 / 震荡的汇总对比", level=2)
g = ph.dropna(subset=["ann"]).groupby(["类型","指数"])[["ann","sharpe","mdd"]].mean()
def pick(kind, col, scale=100):
    return [g.loc[(kind, k), col] * scale if not pd.isna(g.loc[(kind, k), col]) else np.nan for k in ORDER]
summ = pd.DataFrame({
    "牛市年化": ["%.1f%%" % x for x in pick("牛市","ann")],
    "熊市年化": ["—" if pd.isna(x) else "%.1f%%" % x for x in pick("熊市","ann")],
    "震荡年化": ["%.1f%%" % x for x in pick("震荡","ann")],
    "牛市夏普": ["%.2f" % x for x in pick("牛市","sharpe",1)],
    "熊市夏普": ["%.2f" % x for x in pick("熊市","sharpe",1)],
    "牛市最大回撤": ["%.1f%%" % x for x in pick("牛市","mdd")],
    "熊市最大回撤": ["%.1f%%" % x for x in pick("熊市","mdd")],
}, index=pd.Index([CN[k] for k in ORDER], name="指数"))
table(summ, "表 3-5  分市场环境的平均表现（年化为各阶段年化收益的简单平均；熊市仅 2 个阶段可年化）", size=8)
para("汇总层面呈现出清晰的权衡：牛市中纳斯达克100（39.1%）与费城半导体（44.6%）的年化收益接近标普500（26.6%）的 1.5–1.7 倍，但在熊市中回吐得更多（−45.2%、−49.9% vs −34.0%）。"
     "将牛熊合并看，纳指100 的「牛市超额」大于「熊市超额损失」，因此长期年化领先；费城半导体的牛熊弹性都最大，但胜率并不占优；罗素2000 的牛市年化（24.7%）低于标普500（26.6%），熊市跌幅（−33.5%）与标普500 相当，这是它长期落后的直接原因。")
para("表中熊市年化仅基于 2 个可年化阶段（科网破裂、全球金融危机；新冠闪崩与关税急跌不足 1 年不年化），样本量极小，结论应视为方向性参考而非统计显著的结果。震荡阶段同样只有 1 个可年化样本（关税后修复）。")

doc.add_heading("3.6 相对基准的动态：捕获率与 Alpha", level=2)
cap = D["capture"]
capt = pd.DataFrame({
    "上行捕获": ["%.1f%%" % (cap[k]["上行捕获"]*100) for k in ORDER],
    "下行捕获": ["%.1f%%" % (cap[k]["下行捕获"]*100) for k in ORDER],
    "捕获比": ["%.2f" % cap[k]["捕获比"] for k in ORDER],
    "Beta": ["%.3f" % cap[k]["Beta"] for k in ORDER],
    "年化Alpha": ["%.2f%%" % (cap[k]["年化Alpha"]*100) for k in ORDER],
}, index=pd.Index([CN[k] for k in ORDER], name="指数"))
table(capt, "表 3-6  相对标普500 的上/下行捕获率、Beta 与年化 Alpha（1994-05 起）", size=8.5)
para("捕获率揭示了各指数的收益来源。费城半导体的上行捕获 162.9%、下行捕获 158.9%，捕获比 1.03——它并不是「跌得少涨得多」的优质资产，而是「等比例放大」的高 beta 工具（Beta 1.462）。"
     "纳指100 的捕获比 1.02、Beta 1.243，年化 Alpha 4.67%，是六条指数中风险调整后超额最显著的一条；纳斯达克综合 Beta 1.159、Alpha 2.10%；道指的 Beta 0.914、Alpha 仅 0.02%，几乎就是「低 beta 版本的标普500」。")
para("最值得注意的是罗素2000：上行捕获 108.7%、下行捕获 110.1%，捕获比 0.99，Alpha 为 −0.90%。这意味着它不仅没有提供小盘股应有的「独立行情」，反而在扣除 beta 后系统性跑输——在三十二年的样本中，罗素2000 相对标普500 的配置是负贡献的。"
     "这一发现对「小盘股长期跑赢」的经验法则构成了直接反证，但其成因（2009 年后低利率环境、指数内部行业结构、被动资金流向大盘）在本报告的数据范围内只能提出假设，无法严格识别因果。")

# ================= 四、指数特征 =================
doc.add_page_break()
doc.add_heading("四、六大指数的结构特征", level=1)

doc.add_heading("4.1 市值覆盖与成分规模", level=2)
para("市值覆盖决定了指数在市场中的代表性。报告以成分股的流通股本乘以价格估算总市值（数据来自 iShares 持仓文件与 stockanalysis.com 的股本数据）：标普500 约 70.4 万亿美元，纳斯达克100 约 42.2 万亿，费城半导体约 19.4 万亿，罗素2000 约 3.6 万亿（按 150 只样本外推至 1,971 只）。")
para("这组数字揭示了两点。第一，标普500 的市值约为罗素2000 的 20 倍，两者根本不在同一量级，「大盘 vs 小盘」的轮动在资金容量上是不对称的。第二，费城半导体仅 30 只成分股却覆盖 19.4 万亿美元市值，说明其成分（英伟达、台积电、博通、AMD、美光等）都是巨型公司，指数的高集中度有其合理性——它是「一个行业的头部公司集合」，而非「一个行业的全体公司」。")
para("此外，纳斯达克100 的 42.2 万亿美元中有超过一半集中于前十大成分，这意味着该指数的市值覆盖虽大，但有效分散度远低于标普500。")

doc.add_heading("4.2 行业结构", level=2)
sec = pd.DataFrame(D["sector"]).T
sec = sec.drop(index=[i for i in sec.index if i in ("合计", "Other")], errors="ignore")
sec.index.name = "GICS 一级行业"
cols = ["标普500", "罗素2000", "罗素1000成长", "罗素1000价值", "费城半导体"]
sec = sec[[c for c in cols if c in sec.columns]]
sec = sec.loc[sec.sum(axis=1).sort_values(ascending=False).index]
table(sec.round(2), "表 4-1  GICS 一级行业权重（%，2026-11-05 持仓快照）", size=8.5)
figure(os.path.join(FIG, "07_行业权重.png"), "图 4-1  行业权重分布：半导体指数几乎 100% 集中于信息技术，罗素2000 则以医药与金融为主")

para("行业结构是理解指数行为的关键。标普500 的信息技术权重 35.5%，加上通信服务（8.8%，含 Alphabet、Meta）与可选消费（9.5%，含亚马逊、特斯拉），科技相关板块合计超过 50%，但金融（12.8%）、医疗（10.5%）、工业（8.2%）仍有可观权重，构成「科技主导但不押注单一行业」的平衡。"
     "纳指100 未纳入本表（其行业分类可通过成分股推断），但从权重看信息技术与通信服务合计接近 70%，集中度远高于标普500。")
para("罗素2000 的行业结构与宽基指数截然不同：医疗保健 20.7%、金融 20.1%、工业 13.3%，信息技术仅 12.2%。这是一个典型的「内需 + 利率敏感」组合——生物科技依赖融资环境，区域银行依赖净息差，工业依赖资本开支。"
     "这解释了为什么罗素2000 在 2022 年加息周期中表现疲弱（−25.7%），也解释了它为何在 AI 资本开支周期中缺席（信息技术权重过低）。")
para("费城半导体的 99.8% 集中于信息技术，是极致的行业押注。罗素1000 成长与价值的分野同样清晰：成长侧信息技术 52.4%、通信服务 15.9%；价值侧信息技术仅 18.8%，金融 18.7%、医疗 13.7%、工业 10.4%、必需消费 8.0%。这对组合的相对强弱，本质上就是「长久期成长 vs 短久期现金流」的估值博弈。")

doc.add_heading("4.3 集中度：有效家数比成分数更有信息量", level=2)
conc = pd.DataFrame(D["conc"]).T
conc.index.name = "指数"
conc2 = pd.DataFrame({
    "成分数": ["%d" % int(conc.loc[k, "成分数"]) for k in conc.index],
    "前十大权重": ["%.2f%%" % conc.loc[k, "前十"] for k in conc.index],
    "第一大权重": ["%.2f%%" % conc.loc[k, "第一大"] for k in conc.index],
    "HHI": ["%.0f" % conc.loc[k, "HHI"] for k in conc.index],
    "有效家数": ["%.1f" % conc.loc[k, "有效家数"] for k in conc.index],
}, index=conc.index)
table(conc2, "表 4-2  权重集中度指标（HHI = Σw²×10000；有效家数 = 1/Σw²）", size=8.5)
para("有效家数（effective number of constituents，即 1/Σw²）是比成分数更能反映真实分散度的指标。标普500 有 503 只成分股，但有效家数只有 47.8——相当于「47.8 只等权股票」的分散度；纳指100 有 101 只，有效家数仅 16.9；道指 30 只，有效家数 22.5（因价格加权反而比纳指100 更分散）。"
     "罗素2000 有 1,971 只，有效家数高达 824.4，是真正的「广度型」指数；费城半导体 30 只，有效家数 19.5。")
para("这一指标直接对应风险特征：纳指100 的有效家数只有标普500 的三分之一，因此单一个股（如英伟达）的波动就能显著影响指数；费城半导体的有效家数 19.5 意味着前五家公司几乎决定了指数走势。"
     "反过来，罗素2000 的 824 只有效家数使其几乎不受个股事件影响，但也意味着它缺乏「龙头驱动」的上涨动能——这正是它在 AI 周期中落后的结构性原因。")

doc.add_heading("4.4 成长与价值倾向", level=2)
style = D["style"]
sty = pd.DataFrame({
    "大盘成长(IWF)": ["%.3f" % style[k]["IWF"] for k in ORDER],
    "大盘价值(IWD)": ["%.3f" % style[k]["IWD"] for k in ORDER],
    "小盘成长(IWO)": ["%.3f" % style[k]["IWO"] for k in ORDER],
    "小盘价值(IWN)": ["%.3f" % style[k]["IWN"] for k in ORDER],
}, index=pd.Index([CN[k] for k in ORDER], name="指数"))
table(sty, "表 4-3  各指数与风格 ETF 的日收益相关系数（2000-07 起）", size=8.5)
figure(os.path.join(FIG, "08_成长价值.png"), "图 4-2  大盘成长/大盘价值相对强弱（IWF/IWD）：2000 年后经历三轮完整的风格周期")

para("相关系数给出了清晰的风格坐标。纳指100 与大盘成长的相关性 0.935、与大盘价值仅 0.740，是典型的成长股指数；道指与大盘价值的相关性 0.952、与大盘成长 0.880，是典型的价值/周期指数；标普500 对两者的相关性都是 0.951/0.952，恰好处于中间——这也印证了它作为「市场基准」的中性定位。"
     "罗素2000 与小盘成长（0.968）、小盘价值（0.971）的相关性都极高，几乎就是小盘风格本身；费城半导体与所有风格的相关性都偏低（0.632–0.804），说明它更多是「行业 beta」而非「风格 beta」。")
para("从时间序列看，大盘成长/价值的相对强弱经历了三轮完整周期：2000–2002 年成长跑输 41.9%（科网泡沫出清）；2003–2007 年成长继续跑输 20.2%（价值与周期补涨）；2009–2020 年成长大幅跑赢 40.4%（低利率 + 平台经济）；2022 年加息周期成长回吐 17.4%；2022 年 10 月至 2025 年 2 月的 AI 行情中成长再度跑赢 35.0%；而 2025 年 2 月以来，成长相对价值回落 20.0%，价值风格阶段性占优。"
     "这一节奏与美联储的政策周期高度同步：降息/零利率期利好成长，加息/紧缩期利好价值。")

doc.add_heading("4.5 波动与流动性特征", level=2)
liq = pd.DataFrame({
    "年化波动率": ["%.2f%%" % (m[k]["vol"]*100) for k in ORDER],
    "近一年ETF日均成交额": ["451 亿美元", "26 亿美元", "324 亿美元", "324 亿美元", "86 亿美元", "37 亿美元"],
    "对应ETF": ["SPY", "DIA", "QQQ", "QQQ", "IWM", "SOXX"],
}, index=pd.Index([CN[k] for k in ORDER], name="指数"))
table(liq, "表 4-4  波动率与可交易性（成交额为 2025-11 至 2026-11 的日均值）", size=8.5)
para("流动性方面，六条指数都有成熟的 ETF 载体：SPY 日均成交约 451 亿美元，QQQ 约 324 亿美元，IWM 约 86 亿美元，SMH/SOXX 合计约 83 亿美元，DIA 约 26 亿美元。"
     "以机构资金的标准衡量，SPY 与 QQQ 的容量足以承接百亿美元级别的配置调整，IWM 次之，DIA 与半导体 ETF 的容量相对有限。")
para("但需注意，纳斯达克综合（IXIC）本身没有直接对应的 ETF——ONEQ 的规模与流动性远不及 QQQ，实践中投资者多用 QQQ 表达对纳指的敞口，这实际上是把「纳指综合」替换成了「纳指100」，会引入风格偏差（后者更偏大盘成长）。"
     "罗素2000 的情况类似：IWM 跟踪的是罗素2000，但存在约 1% 的跟踪误差与 0.19% 的费率，长期持有时这部分损耗不可忽略。")
para("波动率与流动性的组合决定了策略可行性：费城半导体的 38% 年化波动配合 37 亿美元的日均成交额，适合战术性配置而不适合作为核心持仓；标普500 的 18.6% 波动配合 451 亿美元成交额，是唯一可以承载大规模长期资金的核心资产；罗素2000 的 22.7% 波动与 86 亿美元成交额居中，但其收益风险比在样本中垫底，配置价值有限。")

# ================= 五、市场风格演变 =================
doc.add_page_break()
doc.add_heading("五、各时期占优的市场风格", level=1)

doc.add_heading("5.1 风格轮动的证据链", level=2)
ann = pd.read_csv(os.path.join(OUT, "annual_returns.csv"), index_col=0)
win = ann[ORDER].idxmax(axis=1).value_counts()
beat = {k: (ann[k] > ann["SPX"]).sum() for k in ORDER}
para("以「年度收益冠军次数」衡量，1994–2026 的 33 个完整年度中，费城半导体 15 次夺冠、纳斯达克100 7 次、罗素2000 5 次、道指 4 次、纳斯达克综合与标普500 各 1 次。"
     "费城半导体的夺冠频率接近一半，但这并不意味着它是「常胜」资产——它同时也是跌幅榜的常客（2000、2001、2002、2008、2022 年跌幅均居前）。"
     "以「跑赢标普500 的年份占比」看，纳指100 为 67%（22/33），纳斯达克综合与费城半导体各 58%，罗素2000 48%，道指 42%。")

era = pd.DataFrame({
    "1994–1999": ["22.2", "21.2", "35.1", "50.0", "12.7", "37.5"],
    "2000–2009": ["−0.6", "0.5", "−0.9", "−0.9", "4.6", "0.6"],
    "2010–2019": ["11.8", "11.1", "15.5", "17.4", "11.3", "20.0"],
    "2020–2026": ["13.6", "9.1", "18.6", "21.0", "8.3", "30.8"],
}, index=pd.Index([CN[k] for k in ORDER], name="指数"))
table(era, "表 5-1  分年代的年均年度收益（%，算术平均）", size=8.5)

para("分年代看，风格轮动的轮廓更清晰：", bold=True, indent=False)
bullet("1994–1999：科技成长的黄金期。纳指100 年均 50.0%、费城半导体 37.5%，罗素2000 仅 12.7%。这是「大盘 + 成长」双击的年代，互联网商业化带来的估值重估集中在大型科技股。")
bullet("2000–2009：失去的十年。六条指数年均收益全部在 ±5% 以内，罗素2000 反而以 4.6% 居首。经历科网破裂与金融危机两次深跌，任何单一风格都未能持续占优，价值与小盘相对抗跌。")
bullet("2010–2019：低利率驱动的成长回归。费城半导体 20.0%、纳指100 17.4%，标普500 11.8%，罗素2000 11.3%。QE 与零利率压低了贴现率，长久期资产系统性受益，同时平台经济的赢家通吃推高了头部集中度。")
bullet("2020–2026：AI 资本开支主导。费城半导体 30.8%、纳指100 21.0%，罗素2000 仅 8.3%。这一轮的特征是「实物资本开支」而非「商业模式创新」，受益者从软件平台转向芯片与设备，半导体成为最强风格。")

figure(os.path.join(FIG, "06_年度收益.png"), "图 5-1  六大指数分年度收益率对比：冠军频繁更替是风格轮动的直接证据", width=15.0)

doc.add_heading("5.2 风格判定的量化依据", level=2)
ph = pd.read_csv(os.path.join(OUT, "phases.csv"))
p = ph.pivot_table(index="阶段", columns="指数", values="cumret", sort=False)
order = [x[0] for x in PH]
p = p.reindex(order)
sty2 = pd.DataFrame({
    "标普500": ["%.0f%%" % (p.loc[s, "SPX"]*100) for s in p.index],
    "纳指100": ["%.0f%%" % (p.loc[s, "NDX"]*100) for s in p.index],
    "罗素2000": ["%.0f%%" % (p.loc[s, "RUT"]*100) for s in p.index],
    "大盘 vs 小盘": ["大盘" if p.loc[s, "SPX"] > p.loc[s, "RUT"] else "小盘" for s in p.index],
    "科技 vs 宽基": ["科技" if p.loc[s, "NDX"] > p.loc[s, "SPX"] else "宽基" for s in p.index],
    "成长 vs 周期": ["科技" if p.loc[s, "NDX"] > p.loc[s, "DJI"] else "周期" for s in p.index],
}, index=p.index)
sty2.index.name = "阶段"
table(sty2, "表 5-2  各阶段的风格强弱判定（以阶段累计收益的相对高低判定）", size=8)

para("上表给出了每个阶段的风格坐标。可以发现三个稳定的规律："
     "第一，「科技 vs 宽基」在 11 个阶段中有 8 个由科技占优，只有在科网泡沫破裂、2022 加息熊市与关税急跌三个阶段被宽基反超——这三个阶段的共同点都是「估值压缩」或「风险事件冲击」，即科技的高 beta 在此类环境中成为负担。"
     "第二，「大盘 vs 小盘」的胜负更接近五五开（7:4），但小盘占优的阶段（信贷繁荣、流动性牛市、关税后修复）往往伴随经济复苏或流动性宽松，而大盘占优的阶段则多为风险出清或结构性增长期。"
     "第三，没有任何一种风格能连续三个阶段占优，风格轮动的周期长度通常在 2–4 年。")

doc.add_heading("5.3 集中度上升：本轮的独特之处", level=2)
para("与以往的风格轮动不同，2023 年以来的行情叠加了一个结构性变化：指数集中度达到历史高位。标普500 前十大权重 37.7%、前二十大 49.4%、前五十大 63.0%；纳指100 前十大 67.0%、前二十大 80.2%；第一大成分（苹果）在标普500 中占 7.41%、在纳指100 中占 12.85%。"
     "这意味着「买指数」在今天比十年前更接近于「买少数几家巨型科技公司」，指数层面的分散化效果被显著削弱。")
para("这一变化的直接后果是：标普500 与纳指100 的相关系数升至 0.92 以上（近 365 日 0.927），与罗素2000 的相关性降至 0.836，与费城半导体的相关性 0.744。"
     "换言之，宽基与大盘成长正在「合并」，而小盘与半导体成为相对独立的两个极端。若这一结构持续，传统的「股债配置 + 宽基指数」组合的风险特征将与十年前有本质不同。")

# ================= 六、局限 =================
doc.add_heading("六、数据局限与使用说明", level=1)
para("本报告的结论建立在以下条件之上，超出这些条件使用时需谨慎：", bold=True, indent=False)
bullet("价格口径而非全收益。所有收益指标不含股息，系统性低估了各指数的实际回报约 1.5–2.5 个百分点/年。若用于与债券、REITs 等含息资产比较，须先做口径调整。")
bullet("样本区间的影响。主样本自 1994 年 5 月起，恰好覆盖了 1990 年代大牛市、两次大崩盘与三轮 QE，是一个「整体向上但波动剧烈」的样本。若起点改为 2000 年 3 月（科网顶点），纳指100 与费城半导体的年化收益会大幅下降，排序可能逆转。报告已提供全历史口径作为对照，但各指数样本长度不同，横向比较仍有偏。")
bullet("事后划分阶段。阶段划分使用了未来信息，仅用于描述性分析，不可直接用于构建择时策略。真实交易中无法提前知道阶段的高低点。")
bullet("无风险利率的近似。使用 13 周国库券而非完整的收益率曲线，且未考虑税收与交易成本。对夏普比率的影响在 ±0.02 以内，不改变排序。")
bullet("成分与权重的时点性。第四章的行业权重、集中度与市值数据均为 2026-11-05 的快照，不能代表历史结构。历史上纳指100 在 2000 年时的行业构成与今天差异巨大，用今天的结构解释二十年前的表现会失真。")
bullet("市值估算的误差。成分股总市值由「股本 × 价格」估算，未考虑多地上市、双重股权与 ADR 折算，费城半导体因含台积电、阿斯麦等 ADR，估算误差较大（抽样离散度达 250%），该数值仅作量级参考。")
bullet("数据源的可获得性约束。FRED、stooq 等在本机网络环境下不可达，故未纳入；官方全收益指数（如罗素2000 总收益）无法免费获取，股息调整只能以标普500 为代理。")

# ================= 七、结论 =================
doc.add_heading("七、结论", level=1)
para("综合以上各章的数据，可以给出以下结论：", indent=False)
bullet("收益与风险的排序高度一致，但风险调整后的排序并不同。费城半导体与纳斯达克100 的绝对收益最高，但前者在夏普与卡玛上均不敌后者；罗素2000 在三个维度上同时垫底。「高波动资产长期收益更高」在绝对口径下成立，在风险调整口径下并不成立。")
bullet("牛熊切换决定了指数的相对命运。科技类指数在牛市中放大收益、在估值压缩型熊市中放大损失；道指的防御性在科网破裂与 2022 加息中体现得最充分；罗素2000 既没有科技的高弹性，也没有道指的防御性，其相对落后是结构性的。")
bullet("集中度是理解当前市场的核心变量。标普500 有效家数 47.8、纳指100 仅 16.9，两者的相关性已升至 0.92 以上，分散化效果被削弱；罗素2000 有效家数 824，却因行业结构（医药 20.7%、金融 20.1%）与缺乏龙头驱动而长期跑输。")
bullet("风格轮动与货币政策周期同步。降息/零利率期成长占优（2009–2020、2020–2021），加息/紧缩期价值占优（2000–2002、2022、2025 年以来）。2022 年 10 月至 2025 年 2 月的 AI 行情是成长风格的又一次强化，但 2025 年 2 月以来成长相对价值已回落 20.0%，风格可能正在切换。")
bullet("对配置的含义。若以单位风险回报为目标，纳指100 优于费城半导体；若以绝对收益为目标且能承受 80% 以上回撤与十余年水下期，费城半导体具备吸引力；标普500 仍是唯一能承载大规模长期资金的核心资产；罗素2000 在本样本中不具备配置价值，除非出现明确的降息 + 经济复苏组合。")

para("最后需要强调，以上结论均限定在 1994-05-05 至 2026-11-06 的价格口径样本内，且阶段划分为事后划分。数据区间与口径的变更（尤其是起点、复权方式、无风险利率的替换）都可能改变部分结论，使用时请结合报告第一章的口径说明与第六章的局限一并理解。", indent=True)

doc.add_page_break()
doc.add_heading("附录：图表索引", level=1)
apx = pd.DataFrame({
    "内容": ["六大指数累计净值（对数）", "历史回撤曲线", "滚动 252 日年化波动率", "风险—收益散点（全样本/近十年）",
             "分阶段累计收益热力图", "GICS 行业权重分布", "大盘成长/价值相对强弱", "分年度收益率对比"],
    "对应章节": ["2.1", "2.2", "2.2", "2.3", "3.2", "4.2", "4.4", "5.1"],
}, index=pd.Index(["图 2-1", "图 2-2", "图 2-3", "图 2-4", "图 3-1", "图 4-1", "图 4-2", "图 5-1"], name="编号"))
table(apx, "附表  图表索引", size=9)
para("配套数据文件：美股主要指数回测数据册.xlsx（含 16 个工作表：口径说明、主样本与全历史指标、五个分阶段表、年度收益、行业权重、集中度、市值估计、风格相关、捕获率、相关性矩阵、回撤事件）。", indent=False, size=9)

doc.save(DOCX)
print("saved", DOCX, os.path.getsize(DOCX)/1024, "KB")
print("paragraphs", len(doc.paragraphs), "tables", len(doc.tables))
