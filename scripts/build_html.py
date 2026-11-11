# -*- coding: utf-8 -*-
"""生成单文件 HTML 版报告（含新增的「位置指标与择时」章节）。"""
import os, json, base64, html

BASE = r"E:\workspace\new"
OUT = os.path.join(BASE, "data", "output")
FIG = os.path.join(BASE, "output", "figures")
HTML_OUT = os.path.join(BASE, "output", "美股主要指数系统性回测与对比分析.html")

D = json.load(open(os.path.join(OUT, "report_data.json"), encoding="utf-8"))
T = json.load(open(os.path.join(OUT, "html_data.json"), encoding="utf-8"))
NOW = T["now"]

ORDER = ["SPX", "DJI", "IXIC", "NDX", "RUT", "SOX"]
CN = {"SPX": "标普500", "DJI": "道琼斯工业平均", "IXIC": "纳斯达克综合",
      "NDX": "纳斯达克100", "RUT": "罗素2000", "SOX": "费城半导体"}
SHORT = {"SPX": "标普500", "DJI": "道指", "IXIC": "纳指综合", "NDX": "纳指100",
         "RUT": "罗素2000", "SOX": "费半"}

def fill(tpl, *args):
    """把 %% 还原成 %，并按顺序替换 %s；避免正文中的单个 % 触发格式化错误。"""
    s = tpl.replace("%%", "%")
    parts = s.split("%s")
    if len(parts) - 1 != len(args):
        raise ValueError("fill: placeholder %d but args %d" % (len(parts) - 1, len(args)))
    out = parts[0]
    for a, b in zip(args, parts[1:]):
        out += str(a) + b
    return out

def esc(s):
    return html.escape(str(s))

def fig(name, caption=""):
    p = os.path.join(FIG, name)
    if not os.path.exists(p):
        return '<p class="warn">[缺图: %s]</p>' % esc(name)
    b64 = base64.b64encode(open(p, "rb").read()).decode("ascii")
    cap = '<figcaption>%s</figcaption>' % esc(caption) if caption else ""
    return '<figure><img src="data:image/png;base64,%s" alt="%s">%s</figure>' % (b64, esc(caption), cap)

def table(rows, header, cls="", align=None, caption=""):
    """rows: list of list（已转成展示字符串）"""
    n = len(header)
    al = align or (["l"] + ["r"] * (n - 1))
    th = "".join('<th class="%s">%s</th>' % ("l" if a == "l" else "r", esc(h)) for h, a in zip(header, al))
    body = []
    for r in rows:
        tds = "".join('<td class="%s">%s</td>' % ("l" if a == "l" else "r", c) for c, a in zip(r, al))
        body.append("<tr>%s</tr>" % tds)
    cap = '<caption>%s</caption>' % esc(caption) if caption else ""
    return '<table class="%s">%s<thead><tr>%s</tr></thead><tbody>%s</tbody></table>' % (
        cls, cap, th, "".join(body))

def num(v, d=2, suffix=""):
    if v is None:
        return "—"
    try:
        f = float(v)
    except Exception:
        return esc(v)
    if f != f:
        return "—"
    if suffix == "%d":
        return "%d" % round(f)
    return ("%." + str(d) + "f") % f + suffix

def fp(v, d=2):
    """fraction -> percent"""
    if v is None: return "—"
    try: f = float(v)
    except Exception: return esc(v)
    if f != f: return "—"
    return ("%." + str(d) + "f%%") % (f * 100.0)

def pv(v, d=2):
    """already percent"""
    if v is None: return "—"
    try: f = float(v)
    except Exception: return esc(v)
    if f != f: return "—"
    return ("%." + str(d) + "f%%") % f

CSS = """
:root{
  --ink:#1a1f27; --muted:#5d6875; --line:#e2e6ec; --bg:#ffffff; --soft:#f6f8fa;
  --navy:#1f3b63; --accent:#c0392b; --teal:#0f8b8d; --gold:#bf8f00;
}
*{box-sizing:border-box}
html{scroll-behavior:smooth}
body{margin:0;background:var(--bg);color:var(--ink);
  font-family:"Microsoft YaHei","PingFang SC","Hiragino Sans GB","Source Han Sans SC",system-ui,-apple-system,"Segoe UI",sans-serif;
  font-size:15.5px;line-height:1.85;-webkit-font-smoothing:antialiased}
.wrap{max-width:1180px;margin:0 auto;padding:0 28px}

/* 侧栏目录 */
#toc{position:fixed;top:0;left:0;width:230px;height:100vh;overflow-y:auto;
  background:#fbfcfd;border-right:1px solid var(--line);padding:22px 16px;font-size:13.5px;z-index:20}
#toc h4{margin:0 0 10px;font-size:13px;letter-spacing:.08em;color:var(--muted);text-transform:uppercase}
#toc a{display:block;padding:5px 9px;color:#39424e;text-decoration:none;border-radius:5px;line-height:1.5}
#toc a:hover{background:#eef2f7;color:var(--navy)}
#toc a.sub{padding-left:22px;font-size:12.8px;color:#5d6875}
#toc a.active{background:var(--navy);color:#fff}
main{margin-left:230px}
@media (max-width:900px){
  #toc{display:none} main{margin-left:0} .wrap{padding:0 16px}
}

/* 封面 */
header.cover{padding:76px 0 54px;border-bottom:3px solid var(--navy);background:linear-gradient(180deg,#fafcff,#fff)}
header.cover .kicker{font-size:13px;letter-spacing:.22em;color:var(--muted);text-transform:uppercase;margin-bottom:16px}
header.cover h1{font-size:40px;line-height:1.25;margin:0 0 14px;color:var(--navy);letter-spacing:-.5px}
header.cover .sub{font-size:16px;color:#41505f;margin-bottom:22px}
header.cover .meta{display:flex;flex-wrap:wrap;gap:10px 26px;font-size:13.5px;color:var(--muted)}
header.cover .meta b{color:var(--ink);font-weight:600}

/* 标题 */
h2{font-size:26px;margin:56px 0 18px;padding-bottom:10px;border-bottom:2px solid var(--navy);color:var(--navy);letter-spacing:-.2px}
h3{font-size:19.5px;margin:34px 0 12px;color:var(--navy)}
h4{font-size:16px;margin:24px 0 8px;color:#2c3b4f}
p{margin:0 0 13px}
p.lead{font-size:16.5px;color:#33404f}

/* 表格 */
table{border-collapse:collapse;width:100%;margin:10px 0 14px;font-size:13.2px;
  font-variant-numeric:tabular-nums;background:#fff;box-shadow:0 1px 2px rgba(16,24,40,.06)}
caption{caption-side:top;text-align:left;font-size:13px;color:var(--muted);padding:2px 0 8px;font-weight:600}
th,td{padding:7px 10px;border-bottom:1px solid var(--line)}
thead th{background:var(--navy);color:#fff;font-weight:600;font-size:12.8px;white-space:nowrap;
  position:sticky;top:0;z-index:2}
tbody tr:nth-child(even){background:#fafbfc}
tbody tr:hover{background:#eef4fb}
td.l,th.l{text-align:left}
td.r,th.r{text-align:right}
table.small{font-size:12.4px}
table.small th,table.small td{padding:5px 8px}
.hl{color:var(--accent);font-weight:700}
.up{color:#1e7a3c}
.down{color:var(--accent)}

/* 卡片 */
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:14px;margin:20px 0 26px}
.card{border:1px solid var(--line);border-radius:8px;padding:14px 16px;background:#fff}
.card .k{font-size:12.5px;color:var(--muted);letter-spacing:.04em}
.card .v{font-size:25px;font-weight:700;color:var(--navy);line-height:1.25;margin:3px 0}
.card .d{font-size:12.5px;color:var(--muted)}

/* 提示条 */
.note{border-left:4px solid var(--navy);background:#f4f7fb;padding:12px 16px;margin:16px 0;border-radius:0 6px 6px 0;font-size:14.2px}
.note.warn{border-left-color:var(--accent);background:#fdf5f4}
.note.ok{border-left-color:#1e7a3c;background:#f3faf5}
.note b{color:var(--navy)}

/* 图 */
figure{margin:22px 0 26px;text-align:center}
figure img{max-width:100%;height:auto;border:1px solid var(--line);border-radius:6px}
figcaption{font-size:13px;color:var(--muted);margin-top:8px}
.warn{color:var(--accent);font-size:13px}

ul,ol{margin:0 0 14px;padding-left:24px}
li{margin:5px 0}
b,strong{color:#16202c}
code{background:#f1f3f6;padding:1px 5px;border-radius:4px;font-size:.92em;
  font-family:Consolas,"Cascadia Mono",Menlo,monospace}

/* 分节锚点偏移 */
section{scroll-margin-top:12px}
hr{border:0;border-top:1px solid var(--line);margin:38px 0}
footer{margin-top:70px;padding:26px 0 60px;border-top:1px solid var(--line);color:var(--muted);font-size:13px}

@media print{
  #toc{display:none} main{margin-left:0}
  header.cover{padding:20px 0}
  h2{page-break-after:avoid} table,figure{page-break-inside:avoid}
  thead th{position:static}
}
"""

M = D["main"]

def mval(code, k, d=2, kind="f"):
    v = M[code][k]
    if kind == "f":
        return fp(v, d)
    if kind == "p":
        return pv(v, d)
    return num(v, d)

# ============================ 目录 ============================
TOC = [
    ("summary", "摘要", 0),
    ("c1", "一、口径说明", 0),
    ("c1-1", "1.1 区间与频率", 1), ("c1-2", "1.2 复权方式", 1),
    ("c1-3", "1.3 无风险利率", 1), ("c1-4", "1.4 业绩基准", 1),
    ("c1-5", "1.5 多源交叉比对", 1),
    ("c2", "二、绩效指标汇总", 0),
    ("c2-1", "2.1 收益", 1), ("c2-2", "2.2 风险", 1),
    ("c2-3", "2.3 风险调整后收益", 1), ("c2-4", "2.4 尾部风险", 1),
    ("c3", "三、分阶段对比", 0),
    ("c3-1", "3.1 划分方法", 1), ("c3-2", "3.2 累计收益", 1),
    ("c3-3", "3.3 波动率", 1), ("c3-4", "3.4 夏普", 1),
    ("c3-5", "3.5 牛熊震荡汇总", 1), ("c3-6", "3.6 捕获率", 1),
    ("c4", "四、结构特征", 0),
    ("c5", "五、市场风格演变", 0),
    ("c6", "六、位置指标与择时能力", 0),
    ("c6-1", "6.1 问题定义", 1), ("c6-2", "6.2 指标体系", 1),
    ("c6-3", "6.3 单指标有效性", 1), ("c6-4", "6.4 反直觉的核心发现", 1),
    ("c6-5", "6.5 估值的非线性", 1), ("c6-6", "6.6 位置温度计", 1),
    ("c6-7", "6.7 双轴框架", 1), ("c6-8", "6.8 择时策略回测", 1),
    ("c6-9", "6.9 当前读数", 1), ("c6-10", "6.10 操作建议与陷阱", 1),
    ("c7", "七、数据局限", 0),
    ("c8", "八、结论", 0),
    ("appendix", "附录：图表与数据索引", 0),
]
toc_html = "".join(
    '<a href="#%s" class="%s" data-target="%s">%s</a>' % (i, "sub" if lv else "", i, esc(t))
    for i, t, lv in TOC)

# ============================ 封面 ============================
cover = """
<header class="cover"><div class="wrap">
  <div class="kicker">Systematic Backtest &amp; Comparative Study</div>
  <h1>美股主要指数系统性回测与对比分析</h1>
  <div class="sub">道琼斯工业平均 · 标普500 · 纳斯达克综合 · 纳斯达克100 · 罗素2000 · 费城半导体<br>
  附：位置指标与择时能力专题</div>
  <div class="meta">
    <span>回测区间 <b>1994-05-05 ~ 2026-11-06</b>（主样本，32.51 年 / 8,183 个交易日）</span>
    <span>数据频率 <b>日频</b></span>
    <span>价格口径 <b>价格指数（不含股息）</b></span>
    <span>交叉比对 <b>6 个独立数据源</b></span>
  </div>
</div></header>
"""

# ============================ 摘要 ============================
def kpi_card(k, v, d):
    return '<div class="card"><div class="k">%s</div><div class="v">%s</div><div class="d">%s</div></div>' % (k, v, d)

summary = fill("""
<section id="summary"><div class="wrap">
<h2>摘要</h2>
<p class="lead">本文用同一套日频、同口径、经六源交叉验证的数据，对美股六条主要指数做了 32.5 年的系统性回测，
并在此基础上回答一个更实用的问题：<b>有没有可靠的「位置」指标，能在指数明显偏高或偏低时提示我们调整仓位，
从而获得更高的风险调整后收益？</b></p>

<div class="cards">
%s
%s
%s
%s
</div>

<h3>五点核心结论</h3>
<ol>
<li><b>收益呈三档梯队，但风险调整后的差距远小于绝对收益的差距。</b>
费城半导体（年化 14.40%%）与纳斯达克100（14.03%%）约为标普500（8.97%%）的 1.6 倍，
但费半的夏普比率（0.481）反而<b>低于</b>纳指100（0.531），也不是标普500（0.426）的 1.15 倍——
超额收益几乎被 38.02%% 的年化波动全部吃掉。</li>
<li><b>牛市弹性与熊市杀伤力同序，Beta 是双刃剑。</b>
牛市中费半年化 44.56%%、纳指100 39.07%%，熊市中分别是 −49.90%% 与 −45.16%%；
上行捕获 162.9%% 的费半，下行捕获也高达 158.9%%。</li>
<li><b>结构决定行为。</b>
费半 99.78%% 的权重集中在信息技术一个行业，因此最大回撤 −87.15%%、水下 4453 个交易日（约 17 年半）；
标普500 有 11 个 GICS 一级行业，最大回撤 −56.78%%。行业集中度是波动与回撤的第一解释变量。</li>
<li><b>「位置高就该减仓」在 1 年尺度上基本不成立，在 3–5 年尺度上才成立。</b>
标普500 在 RSI&gt;70、高于 200 日线 10%% 以上、距 52 周高点不足 1%% 这些"高位"状态下，
未来 1 年平均收益反而是 13.7%%–14.4%%，胜率 85%%–92%%；而"低位"状态（价格低于 200 日线）未来 1 年平均只有 5.75%%、胜率 62.8%%。
真正有预测力的是<b>估值</b>，但它只在 5–10 年尺度上表现稳定。</li>
<li><b>可执行的部分是"控制回撤"而不是"提高收益"。</b>
双均线（50/200）择时把最大回撤从 −56.78%% 压到 −22.91%%、夏普从 0.556 提到 0.676，
但年化收益从 8.98%% 降到 7.20%%；叠加估值封顶后回撤进一步降到 −17.60%%、夏普 0.752。
<b>择时的确定性收益是风险，不是收益。</b></li>
</ol>

<div class="note warn"><b>先看这一条：</b>本报告的所有"位置"指标都用<b>滚动 10 年分位</b>计算（不含未来信息）。
如果你期待的是一个"贵了就卖、便宜了就买"的简单开关，本文的数据会告诉你：这样的开关在美股上长期是亏钱的——
它让你在牛市里反复下车。真正有效的是「<b>趋势决定仓位方向、估值决定仓位上限</b>」的两层结构。</div>
</div></section>
""",  kpi_card("主样本交易日", "8,183", "1994-05-05 ~ 2026-11-06"),
       kpi_card("标普500 年化", "8.97%", "累计 1534.3%／最大回撤 −56.78%"),
       kpi_card("最高年化", "14.40%", "费城半导体，波动 38.02%"),
       kpi_card("当前综合温度", "%s" % num(NOW["综合"], 1), "1994 年以来 %s%% 分位" % num(NOW["综合分位"], 1)))

# ============================ 一、口径说明 ============================
cmp_rows = [
    ["标普500", "1994-05-05", "2021-11 ~ 2026-11", "0.000%", "0.000%", "0.000%"],
    ["道琼斯工业平均", "1992-01-02", "2021-11 ~ 2026-11", "0.000%", "0.000%", "0.000%"],
    ["纳斯达克综合", "1971-02-05", "2021-11 ~ 2026-11", "0.115%", "0.036%", "0.036%"],
    ["纳斯达克100", "1985-10-01", "2021-11 ~ 2026-11", "8.98%（标签错误）", "0.126%", "0.033%"],
    ["罗素2000", "1987-09-10", "2021-11 ~ 2026-11", "—", "数据止于 2017-11", "只自 2020-11 起"],
    ["费城半导体", "1994-05-04", "2021-11 ~ 2026-11", "0.145%", "0.000%", "—"],
]

c1 = fill("""
<section id="c1"><div class="wrap">
<h2>一、口径说明</h2>

<h3 id="c1-1">1.1 回测区间与数据频率</h3>
<p>主样本取 <b>1994-05-05 至 2026-11-06</b>，共 8,183 个交易日、32.51 年。
起点不是任意选定的：六条指数中历史最短的是费城半导体（1994-05-04 起），
为确保横向可比，所有指数都用同一区间、同一交易日序列。</p>
<p>各指数的完整历史长度另列如下，用于观察更长周期的特征（全历史口径仅作参考）：</p>
%s

<h3 id="c1-2">1.2 价格复权方式</h3>
<p>主表使用<b>价格指数</b>（不含股息再投资），这是指数本身的定义口径，也是各家数据源最一致的口径。
但价格指数会系统性低估长期总回报。为量化这一偏差，本文另做了两组对照：</p>
<ul>
<li>标普500 <b>价格指数</b> vs <b>全收益指数</b>（1988-01 ~ 2026-11，38.84 年）：年化 <b>9.04%%</b> vs <b>11.33%%</b>，
股息贡献 <b>2.29 个百分点/年</b>。</li>
<li>SPY（含股息再投资，1994-05 起）：复权年化 <b>10.89%%</b>，同期价格指数 8.97%%。</li>
</ul>
<div class="note">因此本报告中所有指数的绝对收益都<b>系统性偏低约 2 个百分点</b>；
但六条指数的股息率差异不大（1%%–2%% 区间），<b>横向比较的排序不受影响</b>。</div>

<h3 id="c1-3">1.3 无风险利率假设</h3>
<p>无风险利率取 <b>13 周美国国库券次级市场贴现率（^IRX）</b>，日化方式为
<code>r_d = (1 + r_annual)^(1/252) − 1</code>。
为避免贴现率报价口径造成偏差，本文将其与<b>美国财政部券等价收益率（coupon-equivalent yield）</b>做了逐日比对：
2002-01 ~ 2026-11 共 <b>6,207 个交易日</b>，平均差 <b>0.056 个百分点</b>、中位差 <b>0.033 个百分点</b>，
差异来自贴现率与等价收益率的换算公式，量级可忽略。主样本无风险利率均值 <b>2.46%%</b>。</p>
<p>所有策略回测中的"空仓"收益均按此日化利率计息，而非按 0 计。</p>

<h3 id="c1-4">1.4 业绩比较基准</h3>
<p>统一以<b>标普500（SPX）</b>为基准，理由是：它覆盖 503 只成分、11 个 GICS 一级行业、约 70.4 万亿美元市值，
是美股最接近"市场组合"的可投资代理，也是所有机构业绩评价的默认参照。
超额收益、Beta、上下行捕获率均相对标普500 计算。</p>

<h3 id="c1-5">1.5 数据源与多源交叉比对</h3>
<p>主数据源为 <b>Yahoo Finance chart API</b>（日频 OHLC + 复权收盘），
交叉验证源包括：东方财富 push2his、新浪财经 US_MinKService、雪球 kline、CBOE 官方 CSV、
纳斯达克官方 historical API、美国财政部 13 周券收益率。
比对方法：取 2021-11 ~ 2026-11 的重叠区间，逐日计算该源相对 Yahoo 收盘价的偏离度，取最大值。</p>
%s
<div class="note warn"><b>发现并剔除的一处数据陷阱：</b>东方财富的 <code>100.NDX</code> 实际返回的是<b>纳斯达克综合指数</b>，
而非纳斯达克100，偏离中位数达 8.98%%。若不核对就直接使用，会把纳指综合的收益当成纳指100 的收益，结论将完全错误。</div>
<div class="note"><b>另两处数据可用性问题：</b>雪球的罗素2000 数据止于 2017-11-01（已停更），
CBOE 的 RUT_History.csv 只从 2020-11-27 开始。因此罗素2000 统一采用 Yahoo 数据，并用东方财富 IWM（罗素2000 ETF）做二级校验。</div>
<p>极端单日也逐一核对过，均为真实行情而非数据错误：1987-10-19 标普 −20.47%%（黑色星期一）、
2001-01-03 纳指100 +18.77%%、2020-03-16 费半 −15.90%%、<b>2026-11-05 费半 −12.2%%</b>
（新浪与雪球两个独立中文源的尾值完全一致：9011.137 → 9390.250，故判定为真实行情，这也是费半当前回撤达 −35.84%% 的直接原因）。</p>
</div></section>
""",  
    table([[CN[c], D["full"][c]["start"], num(D["full"][c]["years"], 2), fp(D["full"][c]["cagr"]),
            fp(D["full"][c]["vol"]), num(D["full"][c]["sharpe"], 3)] for c in ORDER],
          ["指数", "数据起点", "年数", "年化收益", "年化波动", "夏普"], caption="表 1-1  各指数全历史覆盖（价格口径）"),
    table(cmp_rows, ["指数", "主样本起点", "比对区间", "东方财富", "新浪财经", "雪球 / 其他"],
          caption="表 1-2  多源交叉比对：相对 Yahoo 收盘价的最大偏离度", cls="small")
)

# ============================ 二、绩效指标 ============================
def main_row(c):
    m = M[c]
    return [CN[c], fp(m["total"], 2), fp(m["cagr"], 2), fp(m["vol"], 2), num(m["sharpe"], 3),
            num(m["sortino"], 3), fp(m["mdd"], 2), num(m["calmar"], 3), num(m["mdd_dur_days"], 0, "%d")]

def dist_row(c):
    m = M[c]
    return [CN[c], num(m["win_rate"]*100, 1), num(m["skew"], 3), num(m["kurt"], 2),
            fp(m["var95"], 2), fp(m["cvar95"], 2), fp(m["best_month"], 2), fp(m["worst_month"], 2)]

c2 = fill("""
<section id="c2"><div class="wrap">
<h2>二、绩效指标汇总</h2>

<h3 id="c2-1">2.1 收益：三档梯队</h3>
%s
<p>收益分成三档：<b>费城半导体（14.40%%）与纳斯达克100（14.03%%）</b>为第一档；
<b>纳斯达克综合（11.38%%）</b>居中；<b>标普500（8.97%%）与道指（8.43%%）</b>为第三档；<b>罗素2000（7.61%%）</b>垫底。</p>
<p>值得注意的是罗素2000 的位置。它在 1994–2000 年的科技牛市中仅上涨 <b>125.9%%</b>（同期纳斯达克100 上涨 <b>1140.4%%</b>），
此后每一轮牛市都稳定跑输：AI 牛市（2022-10 ~ 2025-02）只涨 35.2%%，同期费半涨 141.5%%。
33 个完整年度中，它只有 16 次跑赢标普500（48%%），从未成为真正的"小盘复兴"载体。</p>
%s

<h3 id="c2-2">2.2 风险：波动与回撤的放大倍数</h3>
<p>费城半导体的年化波动 <b>38.02%%</b>，是标普500（18.59%%）的 <b>2.04 倍</b>。
这个倍数直接反映在回撤上：费半最大回撤 <b>−87.15%%</b>，出现在 2000-03-10 至 2008-11-20，
历时 <b>2,189 个交易日</b>，直到 <b>2017-11-21</b> 才收复——<b>水下时间接近 17 年半</b>。</p>
<p>纳斯达克100 的回撤 −82.90%%，水下 3,925 个交易日（约 15.6 年）；
纳斯达克综合 −77.93%%，水下 3,801 个交易日。相比之下，罗素2000 的回撤 −59.89%% 反而小于纳指系，
水下时间仅 1,021 个交易日——<b>小盘股的风险特征是"跟涨跟跌但幅度更大"的对称放大，不是单边尾部风险</b>。</p>

<h3 id="c2-3">2.3 风险调整后收益：高波动没有换来高夏普</h3>
<p>这是本文最重要的一组数字：</p>
<ul>
<li>夏普比率排序：<b>纳指100 0.531 &gt; 费半 0.481 &gt; 纳指综合 0.469 &gt; 标普500 0.426 &gt; 道指 0.410 &gt; 罗素2000 0.331</b>。</li>
<li>费半的收益是标普的 1.60 倍，但夏普只有标普的 1.13 倍——<b>超额收益的绝大部分被波动消耗掉了</b>。</li>
<li>卡玛比率（年化/最大回撤）排序则几乎反过来：<b>纳指100 0.169 &gt; 费半 0.165 &gt; 标普500 0.158 &gt; 道指 0.157 &gt; 纳指综合 0.146 &gt; 罗素2000 0.127</b>。
六条指数的卡玛都在 0.13–0.17 的窄区间内，<b>说明以"承受最大回撤"为代价换取收益这件事，六条指数做得一样差</b>。</li>
</ul>
%s

<h3 id="c2-4">2.4 尾部风险与收益分布</h3>
%s
<p>六条指数的日收益分布都呈现明显的<b>尖峰厚尾</b>。超额峰度上，道指 12.27、标普500 10.42 最高，
说明宽基指数的大幅波动更多来自系统性冲击（1987、2008、2020）；费城半导体仅 3.56，
因为它日常波动本就很大，极端日的"相对意外程度"反而较小。</p>
<p>偏度上，罗素2000 为 <b>−0.307</b>（左偏最明显），纳指100 与费半为 <b>+0.201 / +0.207</b>（右偏），
意味着后者更多依赖少数暴涨日贡献收益——费半的最优单月达 <b>+50.37%%</b>、最差单月 <b>−33.53%%</b>，
单月振幅超过 80 个百分点。</p>
<p>在 95%% 置信度下，费半的单日 VaR 为 <b>−3.83%%</b>、CVaR 为 <b>−5.38%%</b>，标普500 分别为 −1.78%% 与 −2.79%%。
若以 1 亿元名义本金计，费半在最差的 5%% 交易日中平均单日损失约 <b>538 万元</b>，是道指的 2 倍以上。</p>
<p>日胜率方面，六条指数都在 52%%–55%% 之间，差异不大（纳指综合 54.9%% 最高，费半 52.3%% 最低），
说明收益差异主要来自"<b>赢时赢多少</b>"而非"<b>赢的频率</b>"。</p>
</div></section>
""",  
    table([main_row(c) for c in ORDER],
          ["指数", "累计收益", "年化", "年化波动", "夏普", "索提诺", "最大回撤", "卡玛", "回撤持续(日)"],
          caption="表 2-1  核心绩效指标（1994-05-05 ~ 2026-11-06，价格口径）"),
    fig("01_累计净值.png", "图 2-1  六大指数累计净值（1994-05-05 = 1，对数坐标，价格口径）"),
    fig("04_风险收益散点.png", "图 2-2  风险—收益散点：左为 1994-05 起全样本，右为近 10 年，可见风险调整后的排序差异"),
    table([dist_row(c) for c in ORDER],
          ["指数", "日胜率%", "偏度", "超额峰度", "VaR95", "CVaR95", "最优单月", "最差单月"],
          caption="表 2-2  收益分布与尾部风险"),
)

# ============================ 三、分阶段 ============================
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
PORDER = [x[0] for x in PH]
piv = {}
for row in D["phases"]:
    piv.setdefault(row["阶段"], {})[row["指数"]] = row

def phase_table(key, fmt, title, note_short=True):
    rows = []
    for phn in PORDER:
        r = piv[phn]
        cells = [phn, r["SPX"]["类型"]]
        for c in ORDER:
            v = r[c][key]
            if r["SPX"]["short"] and key in ("ann", "sharpe", "sortino"):
                cells.append("—")
            else:
                cells.append(fmt(v))
        rows.append(cells)
    return table(rows, ["阶段", "类型"] + [SHORT[c] for c in ORDER], caption=title, cls="small")

c3 = fill("""
<section id="c3"><div class="wrap">
<h2>三、市场阶段划分与分阶段对比</h2>

<h3 id="c3-1">3.1 划分方法</h3>
<p>阶段划分采用<b>事后（ex-post）</b>方法，以标普500 的阶段高点与低点为界，并结合大型宏观事件命名。
这一方法的好处是每个阶段内部的市场方向高度一致，便于观察指数在不同环境下的相对表现；
缺点是存在前视偏差，<b>不能作为实时择时的依据</b>。</p>
<p>判定规则：标普500 自阶段低点上行并持续，至下一轮显著回撤（≥15%%）前的高点为止，记为牛市；
自高点回撤 ≥15%% 并持续，至低点为止，记为熊市；持续时间较短（&lt;6 个月）且幅度在 15%%–25%% 之间的急跌与随后的修复，记为震荡。
共划分 <b>11 个阶段：5 个牛市、4 个熊市、2 个震荡阶段</b>。</p>
%s

<h3 id="c3-2">3.2 累计收益：牛市弹性与熊市杀伤力</h3>
%s
%s
<p>三个阶段值得单独说明：</p>
<ul>
<li><b>科网泡沫牛市（1994-05 ~ 2000-03）</b>：纳指100 累计 +1140.4%%、费半 +988.6%%，
而罗素2000 只有 +125.9%%、道指 +200.7%%。这是"大盘成长 vs 小盘"差距最大的一轮，
也是纳指100 长期年化领先的主要来源。</li>
<li><b>科网泡沫破裂（2000-03 ~ 2002-10）</b>：纳指100 −82.8%%、费半 −83.4%%，
而道指只跌 −34.4%%。<b>这是"高估值 + 业绩证伪"的双杀</b>。</li>
<li><b>加息熊市（2022-01 ~ 2022-10）</b>：纳指100 −34.6%%、费半 −45.4%%，道指仅 −20.2%%。
与科网破裂不同，2022 年的下跌源于<b>无风险利率快速上行对长久期资产的估值压缩</b>，
半导体同时承受库存周期下行，因此跌幅甚至超过纳指100——这是"高估值 + 周期下行"双重打击的典型样本。</li>
</ul>

<h3 id="c3-3">3.3 分阶段风险：波动率的时变特征</h3>
%s
<p>波动率的绝对水平随阶段剧烈变化：新冠闪崩期间，六条指数的年化波动率全部飙升至 80%% 以上
（罗素2000 达 90.8%%、费半 104.1%%），是常态水平的 4–5 倍；而流动性牛市期间标普500 仅 20.0%%。</p>
<p>值得强调的是，<b>费城半导体的波动率在任何阶段都是最高的</b>——即使在最平静的 AI 牛市（2022-10 ~ 2025-02），
其波动率也有 33.5%%，高于标普500 在新冠闪崩以外任何阶段的水平。
这说明<b>半导体的高波动是结构性的，而非特定阶段的产物</b>。</p>

<h3 id="c3-4">3.4 分阶段夏普</h3>
%s
<p>牛市阶段的夏普排序并不稳定：科网泡沫牛市中纳指100（1.49）最高、罗素2000（0.70）最低；
后危机长牛中纳指100（1.21）再次领先，罗素2000（0.78）仍垫底；AI 牛市中纳指100（1.41）与标普500（1.36）接近，
罗素2000 仅 0.49。<b>罗素2000 的"低夏普"是跨阶段的稳定特征，而非某一轮行情的偶然结果。</b></p>
<p>熊市阶段的夏普全部为负，且绝对值与跌幅成正比：全球金融危机中六条指数集中在 −1.16 至 −1.44；
科网破裂中道指（−0.81）与费半（−0.76）反而"最好"——后者是因为波动率高，同样的跌幅在风险调整后显得没那么极端。
这也提示<b>夏普比率在极端行情下的解释力有限</b>，应与最大回撤、卡玛比率结合使用。</p>

<h3 id="c3-5">3.5 牛市 / 熊市 / 震荡的汇总对比</h3>
%s
<p>汇总层面呈现出清晰的权衡：牛市中西数达克100（39.1%%）与费城半导体（44.6%%）的年化收益接近标普500（26.6%%）的 1.5–1.7 倍，
但在熊市中回吐得更多（−45.2%%、−49.9%% vs −34.0%%）。将牛熊合并看，
<b>纳指100 的"牛市超额"大于"熊市超额损失"</b>，因此长期年化领先；费城半导体的牛熊弹性都最大，但胜率并不占优；
罗素2000 的牛市年化（24.7%%）低于标普500（26.6%%），熊市跌幅（−33.5%%）与标普500 相当，<b>这是它长期落后的直接原因</b>。</p>

<h3 id="c3-6">3.6 捕获率与 Alpha</h3>
%s
<p>以标普500 为基准，上行捕获率排序为：费半 162.9%% &gt; 纳指100 133.0%% &gt; 纳指综合 121.0%% &gt; 罗素2000 108.7%% &gt; 道指 90.2%% &gt; 标普500 100%%。
下行捕获率几乎同序：费半 158.9%%、纳指100 129.8%%、纳指综合 119.8%%、罗素2000 110.1%%、道指 89.8%%。</p>
<p><b>罗素2000 是唯一"下行捕获高于上行捕获"的指数</b>（108.7%% vs 110.1%%，捕获比 0.99），
这从机制上解释了它为何长期跑输：它在下跌时比上涨时更"跟得住"。
年化 Alpha 方面，只有费半（6.92%%）、纳指100（4.67%%）、纳指综合（2.10%%）显著为正，
罗素2000 为 <b>−0.90%%</b>，道指为 0.02%%。</p>
</div></section>
""",  
    table([[x[0], x[1], x[2], x[3], x[4]] for x in PH],
          ["阶段", "类型", "起始", "结束", "宏观背景"], caption="表 3-1  阶段划分与宏观背景", cls="small",
          align=["l","c","c","c","l"]),
    phase_table("cumret", lambda v: fp(v, 1), "表 3-2  分阶段累计收益（%，价格口径）"),
    fig("05_分阶段热力图.png", "图 3-1  分阶段累计收益热力图（绿涨红跌，色标上限 ±250% 后截断）"),
    phase_table("vol", lambda v: fp(v, 2), "表 3-3  分阶段年化波动率（%）"),
    phase_table("sharpe", lambda v: num(v, 2), "表 3-4  分阶段夏普比率（不足 1 年的阶段不年化）"),
    table([["标普500", "26.6%", "−34.0%", "28.2%", "1.31", "−1.31", "−14.7%", "−52.9%"],
           ["道琼斯工业平均", "23.1%", "−28.7%", "21.6%", "1.17", "−1.12", "−14.4%", "−44.6%"],
           ["纳斯达克综合", "34.2%", "−43.7%", "35.2%", "1.39", "−1.26", "−19.4%", "−66.6%"],
           ["纳斯达克100", "39.1%", "−45.2%", "33.5%", "1.44", "−1.13", "−18.0%", "−68.3%"],
           ["罗素2000", "24.7%", "−33.5%", "32.7%", "0.94", "−1.07", "−22.6%", "−51.2%"],
           ["费城半导体", "44.6%", "−49.9%", "84.7%", "1.16", "−1.06", "−32.2%", "−74.5%"]],
          ["指数", "牛市年化", "熊市年化", "震荡年化", "牛市夏普", "熊市夏普", "牛市最大回撤", "熊市最大回撤"],
          caption="表 3-5  分市场环境的平均表现（年化为各阶段年化收益的简单平均；熊市仅 2 个可年化阶段）", cls="small"),
    table([[CN[c], pv(D["capture"][c]["上行捕获"], 1), pv(D["capture"][c]["下行捕获"], 1),
            num(D["capture"][c]["捕获比"], 2), num(D["capture"][c]["Beta"], 3), pv(D["capture"][c]["年化Alpha"], 2)]
           for c in ORDER],
          ["指数", "上行捕获", "下行捕获", "捕获比", "Beta", "年化 Alpha"],
          caption="表 3-6  上下行捕获率、Beta 与年化 Alpha（相对标普500）", cls="small"),
)

# ============================ 四、结构特征 ============================
SEC_CN = {"Information Technology": "信息技术", "Financials": "金融", "Health Care": "医疗保健",
          "Industrials": "工业", "Communication": "通信服务", "Consumer Discretionary": "可选消费",
          "Consumer Staples": "必需消费", "Energy": "能源", "Utilities": "公用事业",
          "Real Estate": "房地产", "Materials": "原材料"}
SEC_ORDER = ["Information Technology", "Financials", "Health Care", "Industrials", "Communication",
             "Consumer Discretionary", "Consumer Staples", "Energy", "Utilities", "Real Estate", "Materials"]
SEC_COLS = ["标普500", "罗素2000", "罗素1000成长", "罗素1000价值", "费城半导体"]
conc_rows = []
for k in ["SP500", "NDX", "DJI", "标普500(IVV)", "罗素2000(IWM)", "费城半导体(SOXX)"]:
    v = D["conc"][k]
    conc_rows.append([k, num(v["成分数"], 0, "%d"), pv(v["前十"], 2), pv(v["第一大"], 2),
                      num(v["HHI"], 1), num(v["有效家数"], 1)])

def _s(v):
    if v is None:
        return ""
    if isinstance(v, float) and v != v:
        return ""
    return str(v)

mcap_rows = []
for r in D["mcap"]:
    note = _s(r.get("说明")).strip()
    if note == "nan":
        note = ""
    mcap_rows.append([_s(r["指数"]).replace("_", " · "), num(r["全部成分"], 0, "%d"),
                      num(r["有效样本"], 0, "%d"), num(r["总市值万亿美元"], 2), esc(note)])

style_rows = [[CN[c]] + [num(D["style"][c][k], 3) for k in ["IWF", "IWD", "IWO", "IWN"]] for c in ORDER]

c4 = fill("""
<section id="c4"><div class="wrap">
<h2>四、指数结构特征</h2>
<p>指数的长期行为不是偶然的，它是<b>成分结构</b>的函数：市值覆盖决定流动性，行业集中度决定波动，
成长/价值倾向决定它对利率的敏感度。本章逐项量化这些结构差异（数据快照日 2026-11-05）。</p>

<h3>4.1 市值覆盖</h3>
%s
<p>标普500 覆盖 503 只成分、总市值约 <b>70.4 万亿美元</b>，约为罗素2000（3.6 万亿）的 <b>20 倍</b>；
纳斯达克100 以 101 只成分覆盖 <b>42.2 万亿</b>，费城半导体以 30 只成分覆盖 <b>19.4 万亿</b>。
<b>费半用 30 只股票撑起了 19.4 万亿市值，这本身就说明其单只权重之大与集中度之高。</b></p>
<div class="note">罗素2000 的市值由 150 只抽样成分均值外推至 1,971 只（抽样离散度较高），费半含 ADR 折算误差，
两项均为估算值，仅供量级参考。</div>

<h3>4.2 行业结构（GICS 一级）</h3>
%s
%s
<p>行业结构是理解六条指数行为差异的关键。</p>
<ul>
<li><b>费城半导体 99.78%% 集中于信息技术</b>——严格说它本身就是一个行业指数的子集，
所以它的 −87.15%% 回撤、38.02%% 的波动、4453 个交易日的水下时间，都不是"运气差"，而是<b>结构决定的</b>。</li>
<li><b>标普500 覆盖全部 11 个 GICS 一级行业</b>，最大的信息技术 35.51%%，金融 12.78%%、医疗 10.51%%。
这种分散是它最大回撤只有 −56.78%% 的直接原因。</li>
<li><b>罗素2000 的金融（20.10%%）与医疗（20.72%%）合计超过 40%%</b>，信息技术仅 12.17%%。
它本质上是"<b>小盘金融 + 小盘医疗 + 小盘工业</b>"的组合，而不是"小盘科技"——
这解释了它为何在 1994–2000 的科技牛市中几乎没参与，也解释了它在 2023 年以后的 AI 行情中大幅落后。</li>
</ul>

<h3>4.3 集中度</h3>
%s
<p>集中度用三个指标刻画：前十大权重、最大单一成分权重、以及 HHI（赫芬达尔指数）及其倒数"<b>有效成分数</b>"。</p>
<ul>
<li><b>纳斯达克100 的集中度最高</b>：前十大占 66.96%%、最大单一成分 12.85%%、HHI 590.5，有效成分数仅 <b>16.9 只</b>。
标普500 有效成分数 47.8 只，罗素2000 达 <b>824 只</b>。</li>
<li>集中度还在持续上升。标普500 前十大权重从 2015 年的约 18%% 升至当前的 <b>37.72%%</b>，
前 20 大占 49.38%%、前 50 大占 62.98%%——<b>一半以上的市值由 20 只股票决定</b>。</li>
<li>这个变化直接削弱了"指数化投资天然分散"的假设：买入标普500 指数基金，实质上越来越接近买入一个
以大型科技股为核心的组合。</li>
</ul>

<h3>4.4 成长 vs 价值</h3>
%s
<p>用四个风格 ETF 与各指数的日收益相关性来定位风格倾向：IWF（罗素1000成长）、IWD（罗素1000价值）、
IWO（罗素2000成长）、IWN（罗素2000价值）。</p>
<ul>
<li><b>纳斯达克100</b>：与 IWF 相关 0.935、与 IWD 仅 0.740——典型的大盘成长。</li>
<li><b>罗素2000</b>：与 IWO/IWN 相关 0.968/0.971，两者几乎无差异——<b>它本质是"小盘"风格，而非"小盘成长"</b>。</li>
<li><b>道指</b>：与 IWD 相关 0.952 高于 IWF 的 0.880——它是六条指数中最偏价值的。</li>
<li><b>费城半导体</b>：与 IWF 0.804、与 IWD 仅 0.635——成长属性极强，但相关性绝对值低于纳指100，
说明它有大量<b>独立的行业周期驱动</b>，不能简单看作"高 Beta 的成长股组合"。</li>
</ul>

<h3>4.5 波动与流动性</h3>
%s
<p>流动性用近一年日均成交额衡量（取对应 ETF）：SPY <b>451.4 亿美元</b>、QQQ 323.8 亿、IWM 86.0 亿、
SMH 45.3 亿、SOXX 37.5 亿、DIA 25.5 亿。</p>
<p>值得注意的是，<b>跟踪工具层面的流动性差异远小于指数市值差异</b>：DIA 的市值敞口是 IWM 的近 20 倍，
但日均成交额只有 IWM 的 30%%。这意味着对于中小规模资金，六条指数的可交易性差异并不显著，
真正的约束是波动与回撤，而不是流动性。</p>
</div></section>
""",  
    table(mcap_rows, ["指数", "全部成分", "有效样本", "总市值（万亿美元）", "说明"],
          caption="表 4-1  市值覆盖估算", cls="small"),
    table([[SEC_CN.get(k, k)] + [pv(D["sector"][k][c], 2) for c in SEC_COLS] for k in SEC_ORDER],
          ["GICS 一级行业"] + SEC_COLS, caption="表 4-2  GICS 一级行业权重（%，2026-11-05）", cls="small"),
    fig("07_行业权重.png", "图 4-1  行业权重结构对比"),
    table(conc_rows, ["指数 / 跟踪工具", "成分数", "前十大", "最大单一", "HHI", "有效成分数"],
          caption="表 4-3  集中度指标", cls="small"),
    table(style_rows, ["指数", "IWF 成长", "IWD 价值", "IWO 小盘成长", "IWN 小盘价值"],
          caption="表 4-4  与风格 ETF 的日收益相关性（2000-07 起）", cls="small"),
    table([["标普500", "18.59%", "−56.78%", "451.4（SPY）", "11"], ["道琼斯工业平均", "17.74%", "−53.78%", "25.5（DIA）", "—"],
           ["纳斯达克综合", "24.01%", "−77.93%", "323.8（QQQ）", "—"], ["纳斯达克100", "27.13%", "−82.90%", "323.8（QQQ）", "—"],
           ["罗素2000", "22.71%", "−59.89%", "86.0（IWM）", "—"], ["费城半导体", "38.02%", "−87.15%", "37.5（SOXX）／45.3（SMH）", "1"]],
          ["指数", "年化波动", "最大回撤", "近一年日均成交额（亿美元）", "GICS 行业数"],
          caption="表 4-5  波动、回撤与流动性", cls="small"),
)

# ============================ 五、风格演变 ============================
AN = D["annual"]
YEARS = sorted(AN.keys())
decade = {}
for y in YEARS:
    dkey = y[:3] + "0s"
    if dkey == "2020s" or dkey == "2020":
        dkey = "2020-2026"
    decade.setdefault(dkey, []).append(y)
def decade_mean(yrs):
    return {c: sum(AN[y][c] for y in yrs) / len(yrs) for c in ORDER}

dec_rows = []
for dk in ["1990s", "2000s", "2010s"] + ["2020-2026"]:
    if dk not in decade:
        continue
    yr = decade[dk]
    mm = decade_mean(yr)
    dec_rows.append([dk if dk != "1990s" else "1994–1999"] + [pv(mm[c], 1) for c in ORDER])

# 年度冠军
champ = {c: 0 for c in ORDER}
beat = {c: 0 for c in ORDER}
for y in YEARS:
    vals = {c: AN[y][c] for c in ORDER}
    best = max(vals, key=vals.get)
    champ[best] += 1
    for c in ORDER:
        if c != "SPX" and vals[c] > vals["SPX"]:
            beat[c] += 1

c5 = fill("""
<section id="c5"><div class="wrap">
<h2>五、市场风格演变</h2>
<p>市场风格不是固定的背景，而是会随宏观环境（利率、通胀、产业周期）整体切换的主导力量。
本章用年度收益、分年代均值、以及成长/价值相对强弱三条证据链来刻画这一演变。</p>

<h3>5.1 分年代的风格轮动</h3>
%s
<p>四个年代的风格特征差异极大：</p>
<ul>
<li><b>1994–1999：大盘成长完胜。</b>纳指100 年均 <b>50.0%%</b>、费半 37.5%%、纳指综合 35.1%%，
罗素2000 仅 <b>12.7%%</b>、标普500 22.2%%。驱动力是互联网商业化 + 估值扩张 + 1998 年美联储降息。</li>
<li><b>2000–2009：失去的十年。</b>六条指数年均收益都落在 <b>−0.9%% 至 +4.6%%</b> 的窄区间内，
风格差异基本消失——因为所有指数都被两轮大熊市（2000–2002、2007–2009）抹平。</li>
<li><b>2010–2019：低利率 + QE 推动的"成长回归"。</b>纳指100 17.4%%、费半 20.0%%，
罗素2000 只有 11.3%%。成长/价值比值在这十年 <b>+40.4%%</b>。</li>
<li><b>2020–2026：极端分化。</b>流动性牛市中费半年化 85.2%%、纳指100 61.7%%；
随后的 2022 加息熊市又让成长股估值大幅压缩；2023 年起 AI 资本开支周期让费半再度领跑。</li>
</ul>
%s

<h3>5.2 年度冠军与胜率</h3>
<p>33 个完整年度中，费城半导体拿下 <b>15 次</b>年度冠军，纳斯达克100 <b>7 次</b>，
罗素2000 <b>5 次</b>、道指 <b>4 次</b>、标普500 与纳斯达克综合各 <b>1 次</b>。</p>
<p>但"冠军次数"与"胜率"完全是两回事：</p>
<ul>
<li>费半跑赢标普500 的年份只有 <b>19/33（58%%）</b>——它靠少数几个大年（1999 +101.0%%、2009 +69.6%%、2020 +51.1%%、2023 +64.9%%）
把平均拉高，其余年份经常落后。</li>
<li>纳指100 跑赢标普 <b>22/33（67%%）</b>，是六条指数中超额胜率最高的，
这也是它夏普比率与年化收益同时领先的结构性原因。</li>
<li>道指跑赢标普仅 <b>14/33（42%%）</b>，罗素2000 <b>16/33（48%%）</b>。</li>
</ul>
<div class="note"><b>对配置的含义：</b>如果你追求的是"大概率跑赢基准"，纳指100 是最优选择；
如果你追求的是"少数年份的爆发力"，费半无可替代，但必须承受它在其余年份的系统性落后与 −87%% 级别的回撤。
两者不是同一类资产。</div>

<h3>5.3 成长 / 价值的相对强弱</h3>
%s
<p>用 IWF/IWD 比值（罗素1000成长 / 罗素1000价值）的变化来度量风格切换：</p>
<ul>
<li><b>科网泡沫破裂</b>：−41.9%%（IWF −57.2%% vs IWD −26.3%%）——成长股泡沫出清。</li>
<li><b>信贷繁荣牛市</b>：−20.2%%（IWF +101.0%% vs IWD +151.8%%）——金融与能源主导的价值行情。</li>
<li><b>全球金融危机</b>：+22.0%%（IWF −51.0%% vs IWD −59.8%%）——成长股相对抗跌（因为金融股权重更高）。</li>
<li><b>后危机长牛</b>：<b>+40.4%%</b>（IWF +634.6%% vs IWD +423.3%%）——零利率环境下成长股的系统性重估。</li>
<li><b>AI 牛市</b>：+35.0%%（IWF +102.9%% vs IWD +50.3%%）——AI 资本开支周期再次偏向成长。</li>
<li><b>2025-02 至 2026-11</b>：<b>−20.0%%</b>（IWF +8.0%% vs IWD +35.0%%）——风格正在从成长向价值回摆。</li>
</ul>
%s

<h3>5.4 集中度上升：一个被低估的结构变化</h3>
<p>标普500 前十大权重从 2015 年的约 18%% 升至 2026 年的 <b>37.72%%</b>，HHI 从约 100 升至 <b>209.0</b>，
有效成分数从约 100 只降至 <b>47.8 只</b>。同期六条指数与标普500 的日收益相关性普遍升至 0.85 以上
（费半 0.715 最低，纳指综合 0.960 最高）。</p>
<p>这两件事叠加的后果是：<b>"买指数 = 买分散"这个假设正在失效</b>。
当 20 只股票决定一半以上的市值时，任何以市值加权的指数化组合，本质上都是对这批股票的一次集中押注。
这也是下一章"位置指标"必须把<b>估值与集中度</b>放在一起看的原因。</p>
</div></section>
""",  
    table(dec_rows, ["年代"] + [SHORT[c] for c in ORDER], caption="表 5-1  分年代年度平均收益（%）", cls="small"),
    fig("06_年度收益.png", "图 5-1  六条指数年度收益分布（1994–2026）"),
    fig("08_成长价值.png", "图 5-2  成长 / 价值相对强弱（IWF / IWD，2000-07 起）"),
    table([["科网泡沫破裂", "−41.9%", "−57.2%", "−26.3%"],
           ["信贷繁荣牛市", "−20.2%", "+101.0%", "+151.8%"],
           ["全球金融危机", "+22.0%", "−51.0%", "−59.8%"],
           ["后危机长牛", "+40.4%", "+634.6%", "+423.3%"],
           ["流动性牛市", "+14.9%", "+137.1%", "+106.4%"],
           ["加息熊市", "−17.4%", "−31.9%", "−17.6%"],
           ["AI 牛市", "+35.0%", "+102.9%", "+50.3%"],
           ["2025-02 ~ 2026-11", "−20.0%", "+8.0%", "+35.0%"]],
          ["阶段", "IWF/IWD 比值变动", "罗素1000成长", "罗素1000价值"],
          caption="表 5-2  分阶段成长 / 价值相对强弱", cls="small"),
)

# ============================ 六、位置指标与择时 ============================
def T_rows(key, cols):
    return T[key]

# 表 6-2 指标体系
ind_table = [
 ["估值", "CAPE（席勒市盈率）", "月度", "1871-01", "滚动 10 年分位"],
 ["估值", "标普500 市盈率 PE", "月度", "1871-01", "滚动 10 年分位"],
 ["估值", "股息率", "月度", "1871-01", "滚动 10 年分位（取反）"],
 ["趋势", "相对 200 日均线偏离", "日频", "1962-01", "滚动 10 年分位"],
 ["趋势", "RSI(14)", "日频", "1962-01", "滚动 10 年分位"],
 ["趋势", "12 个月绝对动量", "日频", "1963-01", "滚动 10 年分位"],
 ["情绪", "VIX 水平", "日频", "1990-01", "滚动 10 年分位"],
 ["情绪", "VIX / VIX3M 期限结构", "日频", "2006-07", "滚动 10 年分位"],
 ["信用", "HYG / IEF 相对动量（63 日）", "日频", "2007-04", "滚动 10 年分位"],
 ["宽度", "RSP / SPY 相对动量（63 日）", "日频", "2003-05", "滚动 10 年分位"],
 ["宏观", "10Y 国债收益率", "日频", "1962-01", "滚动 10 年分位"],
 ["宏观", "期限利差（10Y − 3M）", "日频", "1982-01", "滚动 10 年分位"],
]

# 表 6-3 事件检验
ev_rows = []
for r in ["RSI>70（超买）", "RSI<30（超卖）", "高于200日线 10% 以上", "低于200日线 10% 以上",
          "距52周高点<1%（创新高区）", "距52周高点>20%", "自高点回撤>20%", "自高点回撤<3%",
          "VIX>30", "VIX<13", "价格>200日线", "价格<200日线"]:
    d = [x for x in T["events"] if x["情景"] == r][0]
    ev_rows.append([r, num(d["样本日"], 0, "%d"), pv(d["占比%"], 1), pv(d["未来1年均值%"], 2),
                    pv(d["未来1年中位%"], 2), pv(d["未来1年胜率%"], 1)])

# 表 6-4 IC
ic_rows = []
for r in T["ic"]:
    ic_rows.append([r["指标"], num(r["IC21"], 3), num(r["t21"], 2), num(r["IC63"], 3),
                    num(r["t63"], 2), num(r["IC252"], 3), num(r["t252"], 2)])

# 表 6-5 CAPE 分层
cape_rows = []
for r in T["capebins"]:
    if r["期限"] != "1年":
        continue
    pass
cap1 = {r["CAPE区间"]: r for r in T["capebins"] if r["期限"] == "1年"}
cap5 = {r["CAPE区间"]: r for r in T["capebins"] if r["期限"] == "5年"}
cap10 = {r["CAPE区间"]: r for r in T["capebins"] if r["期限"] == "10年"}
for b in ["10-15", "15-20", "20-25", "25-30", "30-40", ">40"]:
    if b not in cap1:
        continue
    cape_rows.append([b, num(cap1[b]["样本日"], 0, "%d"),
                      pv(cap1[b]["年化收益%"], 2), pv(cap5[b]["年化收益%"], 2), pv(cap10[b]["年化收益%"], 2),
                      pv(cap1[b]["胜率%"], 1), pv(cap5[b]["胜率%"], 1)])

# 表 6-6 分项
sub_rows = []
order_sub = ["估值热", "趋势热", "情绪热", "信用热", "宏观热", "综合"]
for nm in order_sub:
    r1 = [x for x in T["sub"] if x["期限"] == "1年" and x["分项"] == nm]
    r3 = [x for x in T["sub"] if x["期限"] == "3年" and x["分项"] == nm]
    if not r1:
        continue
    r1, r3 = r1[0], r3[0]
    sub_rows.append([nm, num(r1["IC"], 3), pv(r1["Q1冷%"], 2), pv(r1["Q5热%"], 2),
                     num(r3["IC"], 3), pv(r3["Q1冷%"], 2), pv(r3["Q5热%"], 2)])

# 表 6-7 策略
st_rows = []
for r in T["final"]:
    st_rows.append([r["策略"], pv(r["累计%"], 1), pv(r["年化%"], 2), pv(r["波动%"], 2), num(r["夏普"], 3),
                    pv(r["最大回撤%"], 2), num(r["卡玛"], 3), pv(r["平均仓位%"], 1), num(r["年换手"], 2)])

# 表 6-8 敏感性
sens_rows = [[r["参数"], pv(r["年化"], 2), pv(r["波动"], 2), num(r["夏普"], 3),
              pv(r["回撤"], 2), num(r["卡玛"], 3), num(r["换手"], 2)] for r in T["sens"]]

# 表 6-9 样本外
oos_rows = [[r["策略"], pv(r["年化%"], 2), pv(r["波动%"], 2), num(r["夏普"], 3), pv(r["最大回撤%"], 2), num(r["卡玛"], 3)]
            for r in T["oos"]]

# 表 6-10 分年代
dec_cols = ["1994-1999", "2000-2009", "2010-2019", "2020-2026"]
dec_rows2 = []
for sname in ["买入持有", "MA200", "双均线50/200", "12M动量"]:
    row = [sname]
    for dc in dec_cols:
        m = [x for x in T["decade"] if x["策略"] == sname and x["年代"] == dc]
        row.append(pv(m[0]["年化%"], 2) if m else "—")
    dec_rows2.append(row)
dec_rows3 = []
for sname in ["买入持有", "MA200", "双均线50/200", "12M动量"]:
    row = [sname]
    for dc in dec_cols:
        m = [x for x in T["decade"] if x["策略"] == sname and x["年代"] == dc]
        row.append(pv(m[0]["最大回撤%"], 2) if m else "—")
    dec_rows3.append(row)

# 表 6-11 四象限
qd_rows = []
for lab in ["1年", "3年"]:
    for q in ["估值低 × 趋势强", "估值低 × 趋势弱", "估值高 × 趋势强", "估值高 × 趋势弱"]:
        m = [x for x in T["quad"] if x["期限"] == lab and x["象限"] == q]
        if not m:
            continue
        d = m[0]
        qd_rows.append([lab, q, num(d["样本日"], 0, "%d"), pv(d["占比%"], 1),
                        pv(d["均值%"], 2), pv(d["中位%"], 2), pv(d["胜率%"], 1)])

# 表 6-12 类比
ana_rows = [[r["日期"], num(r["距离"], 2), pv(r["未来1年%"], 2), pv(r["未来3年%"], 2)] for r in T["analog"]]

# 表 6-13 当前读数
dash_rows = []
for r in T["dash"]:
    v = r["当前值"]
    unit = r["单位"]
    if r["指标"] == "距 200 日线":
        v = v * 100
    elif r["指标"] in ("距历史高点",):
        v = v * 100
    elif r["指标"] in ("20日年化波动",):
        v = v * 100
    elif r["指标"] == "VIX/VIX3M":
        v = v * 100
    unit = unit if isinstance(unit, str) else ""
    if unit == "nan":
        unit = ""
    dash_rows.append([r["指标"], num(v, 2) + unit, pv(r["近10年分位%"], 1), esc(r["含义"] if isinstance(r["含义"], str) else "")])

def _card(k, v, d=""):
    return '<div class="card"><div class="k">%s</div><div class="v">%s</div><div class="d">%s</div></div>' % (k, v, d)

now_cards = ('<div class="cards">'
    + _card("综合温度", "%.1f" % NOW["综合"], "1994 年以来 %.0f%% 分位" % NOW["综合分位"])
    + _card("估值热", "%.1f" % NOW["估值热"], "CAPE %.2f，历史 %.1f%% 分位" % (NOW["cape"], NOW["cape_pct_all"]))
    + _card("趋势热", "%.1f" % NOW["趋势热"], "距 200 日线 %+.2f%%" % NOW["ma200_dev"])
    + _card("情绪热", "%.1f" % NOW["情绪热"], "VIX %.2f，期限结构 %+.2f%%" % (NOW["vix"], NOW["vix_ts"]))
    + _card("信用热", "%.1f" % NOW["信用热"], "信用与宽度中性偏弱")
    + _card("宏观热", "%.1f" % NOW["宏观热"], "10Y %.2f%%、利差 %.2fpp" % (NOW["tnx"], NOW["curve"]))
    + "</div>")


CH6 = fill("""
<section id="c6"><div class="wrap">
<h2>六、位置指标与择时能力：有没有可靠的高低位信号？</h2>

<h3 id="c6-1">6.1 问题定义</h3>
<p>前五章说明了六条指数的长期收益与风险排序，但对实操者来说，更要紧的问题是：
<b>我能不能在中途看出"现在偏高了"或"现在偏低了"，据此调整仓位，从而获得更好的结果？</b></p>
<p>这个问题必须先拆成两半，否则讨论会陷入混乱：</p>
<ol>
<li><b>预测性（predictive）</b>：某指标处于极端值时，<i>未来的收益分布</i>是否与平常不同？
这可以严格检验——把指标的历史分位分层，看各层的未来 1/3/5 年平均收益与胜率。</li>
<li><b>可交易性（tradable）</b>：把上述信息变成仓位规则后，<i>组合的净值</i>是否真的更好？
这必须做含成本的回测，并区分"提高收益"与"降低风险"两件事。</li>
</ol>
<p>本章的结论可以用一句话概括：<b>预测性存在，但方向与直觉相反；可交易性存在，但换来的是风险而非收益。</b></p>
<div class="note"><b>方法上的三个防前视措施：</b>①所有"分位"都用<b>滚动窗口</b>（估值用 10 年、其余用 10 年）计算，
当日分位只依赖当日之前的数据；②估值数据按<b>月度发布滞后一个月</b>对齐，不会用到"当月就知道当月估值"的假数据；
③信号在 t 日收盘生成，<b>t+1 日才生效</b>，且换手按单边 5bp 计成本。</div>

<h3 id="c6-2">6.2 指标体系：五个维度、12 个指标</h3>
%s
<p>把指标分成五组，是因为它们驱动价格的方式不同：</p>
<ul>
<li><b>估值（value）</b>：均值回归的力量，决定 5–10 年的预期回报中枢，对 1 年几乎没有约束力。</li>
<li><b>趋势（trend）</b>：动量延续的力量，决定未来数周到数月的方向，本质上测的是"市场共识的方向"。</li>
<li><b>情绪（sentiment）</b>：期权隐含波动率与期限结构，测的是"恐慌/自满"的即时状态。</li>
<li><b>信用与宽度（credit &amp; breadth）</b>：高收益债相对国债的强弱、等权指数相对市值权指数的强弱。
这两个是机构资金调仓的先行指标，通常领先股价 1–3 个月。</li>
<li><b>宏观（macro）</b>：无风险利率水平与期限结构，决定贴现率，是长久期资产（成长股、半导体）的估值分母。</li>
</ul>

<h3 id="c6-3">6.3 单指标有效性：IC 检验</h3>
<p>用 Spearman 秩相关计算每个指标（已统一为"越高=位置越高"）与未来收益的 IC。
为避免重叠样本导致的 t 值虚高，按持有期做<b>非重叠抽样</b>（1 年期每 252 个交易日取一点）。</p>
%s
<p>读这张表要注意：<b>所有 |IC| 都在 0.25 以下，且绝大多数 t 值不显著</b>。
只有三个指标在短周期上稳定：<b>VIX 水平（IC21 = +0.125, t = 2.46）、VIX 期限倒挂（IC63 = +0.369, t = 3.05）、
等权/市值宽度（IC21 = −0.189, t = −2.83）</b>。</p>
<div class="note warn"><b>一个反直觉的关键读数：</b>VIX 的 IC 是<b>正的</b>——意味着 VIX 越高（越恐慌），未来收益越高。
这与"恐慌时应该离场"的直觉完全相反。同理，等权/市值宽度的 IC 为<b>负</b>：宽度越差（小盘跑输），未来收益越高。
<b>真正有预测力的短周期指标，全部是"逆向"的。</b></div>

<h3 id="c6-4">6.4 核心发现：高位不等于要跌，低位不等于要涨</h3>
<p>把每个"位置状态"当作事件，统计该状态出现后未来 1 年的表现：</p>
%s
%s
<p>这张表几乎是"低买高卖"直觉的反面教材：</p>
<ul>
<li><b>RSI &gt; 70（超买）</b>：出现 630 次，占 7.7%% 的交易日。之后 1 年平均涨 <b>14.36%%</b>，胜率 <b>89.8%%</b>——
比全样本的 9.5%% 高出近 5 个百分点。</li>
<li><b>高于 200 日线 10%% 以上</b>：1,529 天，之后 1 年平均 <b>13.72%%</b>，胜率 <b>91.7%%</b>。</li>
<li><b>价格低于 200 日线</b>：1,937 天，之后 1 年平均只有 <b>5.75%%</b>，胜率 <b>62.8%%</b>。
这是全表最差的"低位"情景——<b>跌破年线之后继续跌的概率，比反弹的概率大得多</b>。</li>
<li><b>VIX &gt; 30</b>：703 天，之后 1 年平均 <b>22.05%%</b>，胜率 <b>86.9%%</b>——<b>全表最高</b>。
这是唯一一个"低位信号"确实有效的例子，但它成立的原因不是"便宜"，而是<b>恐慌已被定价</b>。</li>
</ul>
<p>为什么会出现这种现象？因为股价是<b>前瞻</b>的。指数处于高位，往往是因为盈利在上修、流动性在扩张；
指数跌破年线，往往是因为基本面已经在恶化。<b>价格位置是结果，不是原因。</b>
把位置当原因，就会在牛市里反复下车、在熊市里反复接刀。</p>

<h3 id="c6-5">6.5 估值：唯一在长周期有效的指标，但它是非线性的</h3>
<p>估值对 1 年收益的 IC 是 −0.095，对 3 年是 −0.131（CAPE），方向正确但强度不高。
真正的信息量出现在<b>极端区间</b>：</p>
%s
%s
<ul>
<li>CAPE 在 20–25 区间时，未来 1 年年化 <b>14.27%%</b>、5 年 <b>12.39%%</b>、10 年 <b>9.50%%</b>，胜率 90%%/98%%/100%%。</li>
<li>CAPE 在 30–40 区间时，5 年年化降到 <b>5.15%%</b>、10 年降到 <b>1.38%%</b>。</li>
<li>CAPE <b>&gt; 40</b> 时，未来 1 年年化 <b>−4.00%%</b>、5 年 <b>−3.40%%</b>、10 年 <b>−2.89%%</b>，
1 年胜率 45%%、5 年胜率 <b>0%%</b>。</li>
</ul>
<div class="note warn"><b>必须诚实说明的局限：</b>CAPE &gt; 40 的样本只有 <b>444 个交易日，且全部来自 1999–2000 年</b>。
换句话说，"CAPE 超过 40 之后 5 年零胜率"这个结论，是<b>由一次样本（科网泡沫）得出的</b>，统计上等于 n=1。
它提供了重要的事前警示，但<b>不能当作概率承诺</b>。这也是为什么本章不把估值做成"开关"，
而是做成"仓位上限"——降低错误判断的代价。</div>
<p>另一个角度：<b>当前 CAPE = 40.42，在 1871 年以来的 778 个月度观测中排第 22 高</b>（分位 97.1%%）。
比现在更贵的月份只有 21 个，全部集中在 1999-12 至 2000-10。</p>

<h3 id="c6-6">6.6 位置温度计：把五个维度合成一个 0–100 的读数</h3>
<p>把 12 个指标归并成 5 个分项，每个分项等权合成，再取平均得到"综合温度"。
0 表示极冷（极便宜、极弱、极恐慌），100 表示极热（极贵、极强、极自满）。</p>
%s
%s
<p>综合温度与未来收益的关系是<b>非单调</b>的，这本身就是重要信息：</p>
%s
<ul>
<li>未来 1 年：最冷组 <b>8.26%%</b>、最热组 <b>13.92%%</b>——<b>温度越高，未来 1 年收益反而越高</b>。</li>
<li>未来 5 年：最冷组 50.33%%、最热组 50.16%%——<b>几乎没有差异</b>。</li>
<li>未来 3 年：最热组 36.14%% &gt; 最冷组 31.91%%。</li>
</ul>
<div class="note"><b>结论：</b>综合温度<b>不是收益预测器</b>，它是<b>风险刻度尺</b>。
温度高不代表马上要跌，而代表"此时的定价已经反映了大量乐观预期，一旦预期落空，下跌的空间更大"。
把它当卖出信号用会亏钱，把它当<b>风险预算</b>用才有价值——这正是 6.8 节策略设计的出发点。</div>

<h3 id="c6-7">6.7 双轴框架：估值定上限，趋势定方向</h3>
<p>既然估值管长周期、趋势管短周期，把它们画成两个轴就得到一张有用得多的地图。
估值轴 = 0.6×CAPE 分位 + 0.4×PE 分位；趋势轴 = 0.45×200 日线偏离分位 + 0.30×RSI 分位 + 0.25×12 月动量分位。</p>
%s
%s
<p>四象限的差异是本章最可操作的发现：</p>
<ul>
<li><b>估值高 × 趋势强</b>：1 年平均 <b>14.12%%</b>、胜率 <b>85.9%%</b>——<b>最好的象限</b>。
"贵但在涨"，说明盈利与流动性在支撑，此时减仓是最贵的错误。</li>
<li><b>估值高 × 趋势弱</b>：1 年平均 <b>8.03%%</b>、胜率仅 <b>65.7%%</b>——<b>最差的象限</b>。
"贵且转弱"，这才是真正该降低风险敞口的组合。</li>
<li><b>估值低 × 趋势弱</b>：8.80%%、胜率 79.6%%——便宜但还在跌，可以开始分批，但不能满仓。</li>
<li><b>估值低 × 趋势强</b>：8.96%%、胜率 87.8%%——便宜且转强，胜率最高的象限，是最理想的加仓点。</li>
</ul>
<div class="note ok"><b>这张图解释了为什么单看估值会亏钱：</b>估值高的时候，趋势往往也强（因为牛市推高了估值），
如果一见高估值就减仓，等于在最好的象限里系统性降低暴露。反过来，把"趋势转弱"作为<b>必要条件</b>，
只在"贵 + 弱"时降仓，就把一个胜率 65.7%% 的坏象限和胜率 85.9%% 的好象限区分开了。</div>

<h3 id="c6-8">6.8 择时策略回测：确定性的收益是风险，不是收益</h3>
%s
%s
<p>把上面的逻辑变成规则，回测结果（1994-05 ~ 2026-11，含单边 5bp 成本）：</p>
<ul>
<li><b>买入持有</b>：年化 8.98%%、波动 18.59%%、夏普 0.556、最大回撤 −56.78%%。</li>
<li><b>双均线（50/200）</b>：年化降到 7.20%%、波动降到 11.21%%、夏普升到 <b>0.676</b>、最大回撤降到 <b>−22.91%%</b>。
<b>用 1.78 个百分点的年化收益，换来了 33.87 个百分点的回撤压缩。</b></li>
<li><b>防御 + 估值封顶</b>：年化 6.40%%、波动 8.77%%、夏普 <b>0.752</b>、最大回撤 <b>−17.60%%</b>——风险调整后最优。</li>
<li><b>仅估值封顶、不做趋势</b>：年化 6.94%%、夏普 0.488、最大回撤仍是 −56.78%%。
<b>单靠估值择时不但没降回撤，还亏了收益</b>——因为估值在高位会持续很久。</li>
<li><b>进攻型（趋势 + VIX&gt;30 逆势满仓）</b>：年化 <b>9.39%%</b>，<b>是唯一超过买入持有的方案</b>，
但波动 16.19%%、最大回撤 −46.10%%，夏普只从 0.556 提到 0.636。</li>
</ul>
%s
<p>风险与收益的分解非常清楚：趋势择时在 2000–2002 与 2007–2009 两轮熊市中避免了大部分损失
（金融危机期间持有 −56.4%%，双均线择时 −6.3%%），但在 2010–2019 与 2020–2026 两轮长牛中
被反复甩下车（年化比买入持有低 3.7–4.7 个百分点）。<b>它的收益来源是"少数几次极端行情的规避"，
而不是"持续的超额"。</b></p>

<h4>样本外检验：一个必须说清楚的不利结果</h4>
%s
<p>如果用 1994–2010 的数据"发现"了均线择时，然后在 <b>2011-01 至 2026-11</b> 的样本外检验：</p>
<ul>
<li>买入持有：年化 <b>11.83%%</b>、夏普 <b>0.740</b>、最大回撤 −33.93%%。</li>
<li>MA200：年化 7.26%%、夏普 0.663、最大回撤 −19.53%%。</li>
<li>双均线、12 月动量：年化 7.8%%/7.7%%，夏普 0.599/0.614。</li>
</ul>
<div class="note warn"><b>在 2011 年之后的样本外区间，所有择时策略的夏普都低于买入持有。</b>
原因很直接：这 16 年只有 2020-03 一次快速深跌（23 个交易日），而择时规则需要时间确认趋势，
等确认时跌幅已经完成，随后 V 型反弹又让它错过了大半涨幅。
<b>择时的收益极度依赖"是否有长而慢的熊市"，2011 年之后没有。</b>
这正是本报告最应该被记住的局限：<b>历史回测里择时策略的优势，可能来自样本期内恰好存在两轮长熊。</b></div>

<h4>参数敏感性</h4>
%s
<p>好消息是参数不是特别敏感：MA150–MA300 的年化都在 5.6%%–7.3%%、夏普 0.53–0.65；
动量窗口 126–252 日的夏普在 0.70–0.73。双均线（MA100/200、MA125/250）的夏普可达 0.67–0.69，
且换手率低至 0.6–0.8 次/年，是成本最优的形态。<b>但没有任何参数组合能把年化做回 8.98%%。</b></p>

<h3 id="c6-9">6.9 当前读数（2026-11-06）</h3>
%s
%s
<p>把当前状态放进双轴框架：<b>估值轴 0.831（1994 年以来 70.5%% 分位）× 趋势轴 0.165（12.2%% 分位）</b>，
落在<b>「估值高 × 趋势弱」</b>象限——四象限中 1 年平均收益最低（8.03%%）、胜率最低（65.7%%）的那一格。</p>
<p>分项读数的组合值得注意：</p>
<ul>
<li><b>估值热 79.4</b>：CAPE 40.42（历史 97.1%% 分位、1871 年以来第 22 高）、股息率仅 1.10%%（10 年分位 0%%）。</li>
<li><b>趋势热 11.6</b>：价格刚跌破 200 日线（偏离仅 +0.71%%）、RSI 35.1（接近超卖）。</li>
<li><b>情绪热 8.4</b>：VIX 25.64（10 年分位 86.8%%）、VIX/VIX3M +4.23%%（<b>已倒挂</b>，短期恐慌高于中期）。</li>
<li><b>信用热 52.9</b>：中性偏弱，尚未出现系统性信用压力。</li>
<li><b>宏观热 68.6</b>：10Y 4.86%%（10 年分位 98.2%%）、期限利差 0.86pp。</li>
</ul>
<div class="note"><b>这个组合的含义：</b>"估值极热 + 趋势刚转弱 + 短期情绪已恐慌"是一个
<b>内部矛盾的组合</b>——估值说很贵，情绪说已经跌了一波。历史类比（见下表）给出的不是"马上大跌"，
而是"未来 1 年期望不高、但 3 年维度仍为正"。</div>
<h4>历史类比</h4>
%s
<p>用 10 个指标的分位向量做欧氏距离，找出与今天最相似的 12 个历史时点（同季度只保留一例）：
未来 1 年平均 <b>+8.38%%</b>（中位 +9.53%%、胜率 75%%），未来 3 年平均 <b>+52.78%%</b>（胜率 100%%）。
<b>这不构成看多理由</b>——样本只有 12 个，且高度集中在 2019 与 2022 两个年份，本质上是在问
"2019 和 2022 后来怎么走"，信息量有限。它的用途是校准预期量级，而不是预测方向。</p>

<h3 id="c6-10">6.10 操作建议与常见陷阱</h3>
<h4>可以用的四条</h4>
<ol>
<li><b>把估值当"仓位上限"，不当"卖出信号"。</b>
例如：CAPE 分位 &gt; 90%% 时把股票敞口上限设为 70%%，而不是清仓。
这样即使估值在高位持续 3 年（2017–2019 就是这样），你也只是"少赚"，而不是"踏空"。</li>
<li><b>把趋势当"方向开关"，但接受它的滞后。</b>
双均线（50/200 或 100/200）是成本最低的形态（换手 0.6–0.9 次/年），
能把 −56.78%% 的回撤压到 −22.91%%，代价是年化少 1.8 个百分点。<b>如果你的回撤容忍度低于 30%%，这是必要的代价。</b></li>
<li><b>把恐慌当"加仓窗口"，但要等确认。</b>
VIX &gt; 30 时未来 1 年平均 22.05%% 是全表最高，但 VIX 冲高的当天往往还在下跌。
稳妥的做法是等 VIX 从高点回落 20%% 以上再分批，而不是在最高点接。</li>
<li><b>用"贵 + 弱"作为降仓条件，而非单看"贵"。</b>
这是四象限给出的最明确的一条规则：单看估值高就减仓，会在胜率 85.9%% 的象限里做错；
加上"趋势转弱"这个必要条件，才把最差象限筛出来。</li>
</ol>
<h4>必须避开的五个陷阱</h4>
<ol>
<li><b>用全样本分位代替滚动分位。</b>估值中枢在漂移。用 1871 年以来的固定分位，
会让你在 1990 年代之后几乎永远处于"高估值"状态，从而永远减仓——这是最典型的前视偏差伪装。</li>
<li><b>把 CAPE &gt; 40 的结论当成概率。</b>那 444 个样本全部来自 1999–2000，等于 n=1。
它是警示，不是预测。</li>
<li><b>忽略股息。</b>本报告用价格指数，年化偏低约 2.29 个百分点。
如果你把"择时赚的 1.5%%"和"股息 2%%"放在一起比，会发现<b>长期持有拿股息往往比频繁择时更划算</b>。</li>
<li><b>忽略交易成本与税。</b>回测用单边 5bp，实际散户的买卖价差 + 佣金 + 资本利得税可能达到 30–50bp/次。
把换手率 7 次/年（VIX 逆向策略）的成本从 5bp 提到 30bp，年化会再掉 1.5 个百分点以上。</li>
<li><b>把"降低回撤"误当成"提高收益"。</b>本章所有防御型策略的年化都低于买入持有。
它们改善的是夏普与卡玛，<b>不是绝对收益</b>。如果你的目标是最大化终值且能承受 −57%% 的回撤，
买入持有仍是最优解。</li>
</ol>
</div></section>
""",  
    table(ind_table, ["维度", "指标", "频率", "数据起点", "分位口径"], caption="表 6-1  位置指标体系", cls="small"),
    table(ic_rows, ["指标", "IC(21日)", "t", "IC(63日)", "t", "IC(252日)", "t"],
          caption="表 6-2  单指标 IC 检验（非重叠抽样，Spearman）", cls="small"),
    fig("13_位置事件检验.png", "图 6-1  「位置」状态与未来 1 年收益：高位状态反而对应更高的未来收益"),
    table(ev_rows, ["情景", "样本日", "占比", "未来1年均值", "中位", "胜率"],
          caption="表 6-3  事件式检验：位置状态出现后的未来 1 年表现", cls="small"),
    table(cape_rows, ["CAPE 区间", "样本日", "未来1年年化", "未来5年年化", "未来10年年化", "1年胜率", "5年胜率"],
          caption="表 6-4  CAPE 绝对值分层与未来年化收益（1962 起，价格口径）", cls="small"),
    fig("10_位置与未来收益.png", "图 6-2  按位置温度分组的未来 1/3/5 年平均收益（非单调：最热组 1 年收益最高，5 年无差异）"),
    fig("09_位置温度计.png", "图 6-3  标普500 走势与综合位置温度计（0=极冷/极便宜，100=极热/极贵）"),
    fig("12_分项温度雷达.png", "图 6-4  当前分项温度 vs 1994 年以来均值"),
    table([[r["期限"], r["分层"], num(r["样本日"], 0, "%d"), pv(r["均值%"], 2), pv(r["中位%"], 2), pv(r["胜率%"], 1)]
           for r in T["composite_q"]],
          ["期限", "温度分层", "样本日", "均值收益", "中位收益", "胜率"],
          caption="表 6-5  综合位置温度分层与未来收益", cls="small"),
    fig("14_双轴四象限.png", "图 6-5  估值轴 × 趋势轴 四象限的未来 1 年与 3 年平均收益"),
    table(qd_rows, ["期限", "象限", "样本日", "占比", "均值收益", "中位收益", "胜率"],
          caption="表 6-6  估值 × 趋势 四象限（V/T 均以 0.5 为界，滚动 10 年分位）", cls="small"),
    table(st_rows, ["策略", "累计收益", "年化", "波动", "夏普", "最大回撤", "卡玛", "平均仓位", "年换手"],
          caption="表 6-7  择时策略回测对比（1994-05 ~ 2026-11，含单边 5bp 成本）", cls="small"),
    fig("11_择时净值.png", "图 6-6  择时策略累计净值（对数坐标）"),
    table(dec_rows2, ["策略"] + dec_cols, caption="表 6-8  分年代年化收益（%）", cls="small"),
    table(oos_rows, ["策略", "年化", "波动", "夏普", "最大回撤", "卡玛"],
          caption="表 6-9  样本外检验（2011-01 ~ 2026-11）", cls="small"),
    table(sens_rows, ["参数", "年化", "波动", "夏普", "最大回撤", "卡玛", "年换手"],
          caption="表 6-10  参数敏感性", cls="small"),
    table(dash_rows, ["指标", "当前值", "近 10 年分位", "含义"], caption="表 6-11  当前位置读数（2026-11-06）", cls="small"),
    now_cards,
    table(ana_rows, ["历史时点", "距离", "未来 1 年", "未来 3 年"],
          caption="表 6-12  与当前最相似的 12 个历史时点（同季度去重）", cls="small"),
)

# ============================ 七、局限 & 八、结论 ============================
c7 = """
<section id="c7"><div class="wrap">
<h2>七、数据局限与使用说明</h2>
<ol>
<li><b>价格指数口径，不含股息。</b>所有年化收益相对全收益口径系统性偏低约 2.29 个百分点/年。
指数之间的横向排序不受影响，但<b>不能用本报告的数字直接评估投资收益</b>。</li>
<li><b>阶段划分是事后（ex-post）判定。</b>以标普500 的实际高低点为界，存在前视偏差。
它适合做"不同环境下的相对表现"研究，<b>不能作为实时择时依据</b>。</li>
<li><b>部分阶段不足 1 年。</b>新冠闪崩仅 23 个交易日、关税急跌 30 个交易日，
这些阶段的年化指标已标注"—"、不作年化，只使用累计收益与最大回撤。</li>
<li><b>市值数据含估算成分。</b>费城半导体 30 只成分含 ADR，折算误差大；罗素2000 由 150 只抽样外推至 1,971 只，
抽样离散度较高。两项仅供量级参考。</li>
<li><b>成分与权重为 2026-11-05 单一快照。</b>历史成分变动未回溯，<b>存在生存者偏差</b>：
用今天的成分去回测 1994 年，会高估早期收益（因为退市与并购的失败者被剔除）。</li>
<li><b>不含交易成本、冲击成本与税负。</b>择时回测虽计入单边 5bp，但实际散户与机构的摩擦成本更高；
指数本身也不含管理费与跟踪误差。</li>
<li><b>部分早期数据（1962–1980 年代）在各方数据源间存在口径差异。</b>全历史口径仅作参考，
<b>主结论以 1994-05 起的共同样本为准</b>。</li>
<li><b>择时章节的额外局限。</b>CAPE &gt; 40 的样本全部来自 1999–2000（n=1 事件）；
VIX3M 自 2006-07 才有数据、HYG 自 2007-04 才有数据，因此信用与情绪类指标的有效样本更短；
2011 年之后的样本外检验显示所有择时策略的夏普都低于买入持有，<b>这是对本章结论最重要的反向证据</b>。</li>
</ol>
</div></section>
"""

c8 = """
<section id="c8"><div class="wrap">
<h2>八、结论</h2>
<h3>8.1 关于六条指数本身</h3>
<ol>
<li><b>收益排序稳定，风险排序更稳定。</b>
32.5 年里，费半（14.40%%）与纳指100（14.03%%）的收益是标普500（8.97%%）的 1.6 倍，
但这个优势几乎全部被波动抵消：夏普 0.481 与 0.531，仅比标普500 的 0.426 高 13%%–25%%。</li>
<li><b>结构是行为的第一解释变量。</b>
费半 99.78%% 集中于信息技术 → 38.02%% 波动、−87.15%% 回撤、17.5 年水下；
罗素2000 的金融 + 医疗占 40%% → 在科技牛市中几乎没有参与；
标普500 覆盖 11 个行业 → 最大回撤只有 −56.78%%。</li>
<li><b>罗素2000 是六条指数中唯一"结构性劣势"的。</b>
下行捕获 110.1%% 高于上行捕获 108.7%%，年化 Alpha −0.90%%，牛市年化低于标普500 而熊市跌幅相当。
这不是运气问题，是成分结构问题。</li>
<li><b>集中度上升正在改变"指数化 = 分散化"的前提。</b>
标普500 前十大权重已达 37.72%%、有效成分数只有 47.8 只，且仍在上升。</li>
</ol>

<h3>8.2 关于位置指标与择时</h3>
<ol>
<li><b>"位置高就该卖"在 1 年尺度上是错的。</b>
RSI&gt;70、高于年线 10%%、创新高区这些"高位"状态，未来 1 年平均收益 11.6%%–14.4%%、胜率 85%%–92%%；
而"跌破年线"的"低位"状态，未来 1 年平均只有 5.75%%、胜率 62.8%%。</li>
<li><b>唯一稳定的短周期信号是逆向的恐慌指标。</b>
VIX&gt;30 之后未来 1 年平均 +22.05%%；VIX 期限倒挂的 IC(63日) 达 +0.369（t=3.05）。
这是全报告中统计显著性最强的单一发现。</li>
<li><b>估值有效，但只在长周期、且只在极端区间。</b>
CAPE 20–25 → 未来 10 年年化 9.50%%；CAPE 30–40 → 1.38%%；CAPE &gt;40 → −2.89%%。
方向正确、单调，但极端样本只有一次事件。</li>
<li><b>可执行的收益是"降低回撤"，不是"提高收益"。</b>
双均线把回撤从 −56.78%% 压到 −22.91%%、夏普 0.556→0.676，代价是年化 8.98%%→7.20%%；
叠加上限后夏普可达 0.752、回撤 −17.60%%，年化降至 6.40%%。<b>没有一种方案同时提高收益并降低风险。</b></li>
<li><b>正确的结构是两层，不是一层。</b>
趋势决定"方不方向"，估值决定"上不上限"。
单用估值（无趋势）的回测：年化 6.94%%、夏普 0.488、<b>最大回撤仍是 −56.78%%</b>——完全没有起到保护作用。</li>
</ol>

<h3>8.3 对当前时点（2026-11-06）的读数</h3>
<p>综合位置温度 <b>44.2</b>（1994 年以来 39.2%% 分位，不算极热），但内部严重分化：
<b>估值热 79.4（CAPE 40.42，历史 97.1%% 分位）vs 趋势热 11.6、情绪热 8.4</b>。
放在双轴框架中，当前落在<b>「估值高 × 趋势弱」</b>象限——历史统计上 1 年平均 8.03%%、胜率 65.7%%，是四象限中最低的一格。</p>
<p>需要强调三点：①这是<b>概率描述而非预测</b>，该象限仍有 65.7%% 的胜率，不是"必跌"；
②趋势轴只反映了"刚跌破 200 日线"，如果后续重新站上，象限会迅速切换；
③<b>当前 CAPE 的历史高位主要由盈利质量与行业结构变化造成</b>，用 1871–1990 的均值做锚可能本身就偏低，
这是估值指标在当前环境下面临的最大质疑。</p>

<h3>8.4 如果你只能记住一句话</h3>
<div class="note ok"><b>在美股上，"判断贵不贵"能帮你控制风险，"判断该不该买"要靠趋势和恐慌，
而"长期拿住"仍然是收益的最大来源。</b>本报告的六条指数、三十二年数据，
没有找到任何一个既能提高收益又能降低风险的择时开关；找到的只有一系列<b>用收益换风险</b>的权衡。</div>
</div></section>
"""

appendix = fill("""
<section id="appendix"><div class="wrap">
<h2>附录：图表与数据索引</h2>
<h3>A. 图表清单</h3>
%s
<h3>B. 配套数据文件</h3>
<p>所有中间计算数据均在 <code>data/output/</code> 与 <code>data/processed/</code> 目录下，
可直接用 Excel 或 Python 复算：</p>
%s
<h3>C. 复现路径</h3>
<p>全部分析可用 <code>scripts/</code> 下的脚本复现（Python 3.12 + pandas 3.0.1 + numpy 2.3.5 + matplotlib 3.11.2）：</p>
<ol>
<li><b>数据抓取</b>：<code>fetch_yahoo.py</code>（主源）、<code>fetch_alt.py</code>（东财/新浪/雪球）、
<code>fetch_official.py</code>（CBOE/Nasdaq/财政部）、<code>fetch_valuation.py</code>（multpl 估值）、
<code>fetch_extra.py</code>（^TNX/^VIX3M/HYG/IEF/RSP）。</li>
<li><b>交叉校验</b>：<code>crosscheck.py</code>（多源偏离度）、<code>build_panel.py</code>（对齐日频矩阵）、
<code>check_panel.py</code>（完整性检查）。</li>
<li><b>指标计算</b>：<code>metrics.py</code>、<code>phases.py</code>、<code>structure.py</code>、
<code>tables_extra.py</code>、<code>market_cap.py</code>、<code>collect.py</code>。</li>
<li><b>位置与择时</b>：<code>timing_panel.py</code>（指标面板）、<code>timing_signal.py</code>（IC）、
<code>timing_composite.py</code>（温度计）、<code>timing_axes.py</code>（双轴）、
<code>timing_backtest.py</code>／<code>timing_final.py</code>（策略）、<code>timing_deep.py</code>（事件/敏感性/样本外）、
<code>timing_analog.py</code>（历史类比）。</li>
<li><b>产出</b>：<code>make_figures.py</code>、<code>make_timing_figures.py</code>（图表）、
<code>make_xlsx.py</code>（Excel 数据册）、<code>build_report.py</code>（Word）、<code>build_html.py</code>（本文件）。</li>
</ol>
</div></section>
""",  
    table([["图 2-1", "六大指数累计净值", "2.1"], ["图 2-2", "风险—收益散点", "2.2"],
           ["图 3-1", "分阶段累计收益热力图", "3.2"], ["图 4-1", "行业权重结构", "4.2"],
           ["图 5-1", "年度收益分布", "5.1"], ["图 5-2", "成长/价值相对强弱", "5.3"],
           ["图 6-1", "位置状态与未来收益", "6.4"], ["图 6-2", "温度分层与未来收益", "6.6"],
           ["图 6-3", "位置温度计", "6.6"], ["图 6-4", "分项温度雷达", "6.6"],
           ["图 6-5", "双轴四象限", "6.7"], ["图 6-6", "择时策略净值", "6.8"]],
          ["编号", "内容", "所在章节"], caption="表 A-1  图表索引", cls="small",
          align=["c", "l", "c"]),
    table([["metrics_main.csv", "主样本核心指标"], ["metrics_full.csv", "全历史指标"],
           ["phases.csv", "11 阶段 × 6 指数 × 15 指标"], ["annual_returns.csv", "33 年年度收益"],
           ["drawdown_episodes.csv", "30 个回撤事件"], ["sector_weights.csv", "GICS 行业权重"],
           ["concentration.csv", "集中度指标"], ["timing_panel.csv", "位置指标日频面板（54 列）"],
           ["timing_composite.csv", "位置温度计五分量"], ["timing_axes.csv", "估值轴/趋势轴"],
           ["timing_final.csv", "策略回测结果"], ["timing_quintile.csv", "五分层检验"],
           ["html_data.json", "本页全部数据的结构化副本"]],
          ["文件", "内容"], caption="表 A-2  配套数据文件", cls="small"),
)

FOOT = """
<footer><div class="wrap">
<p><b>数据来源</b>：Yahoo Finance chart API（主源）、东方财富、新浪财经、雪球、CBOE、纳斯达克官方、
美国财政部、multpl.com、iShares、slickcharts、Wikipedia。</p>
<p><b>口径说明</b>：主样本 1994-05-05 ~ 2026-11-06（8,183 个交易日，32.51 年）；
价格指数（不含股息）；无风险利率采用 ^IRX 日化；基准为标普500。
择时章节所有分位均为滚动 10 年窗口，信号 T+1 生效，成本按单边 5bp 计。</p>
<p><b>免责声明</b>：本文为历史数据研究与教学用途，不构成任何投资建议。
历史表现不代表未来收益，所有回测结论都存在样本内偏差、生存者偏差与参数过拟合风险。</p>
<p style="color:#8893a1;margin-top:14px">生成时间：2026-11-08　·　分析工具：Python 3.12 / pandas 3.0.1 / matplotlib 3.11.2</p>
</div></footer>
"""

# ============================ 组装 ============================
BODY = (cover + summary + c1 + c2 + c3 + c4 + c5 + CH6 + c7 + c8 + appendix).replace("%%", "%")

JS = """
<script>
(function(){
  var links = Array.prototype.slice.call(document.querySelectorAll('#toc a[data-target]'));
  var targets = links.map(function(a){ return document.getElementById(a.dataset.target); }).filter(Boolean);
  function onScroll(){
    var y = window.scrollY + 120, cur = null;
    for (var i=0;i<targets.length;i++){
      if (targets[i].offsetTop <= y) cur = targets[i].id;
    }
    links.forEach(function(a){ a.classList.toggle('active', a.dataset.target === cur); });
  }
  window.addEventListener('scroll', onScroll, {passive:true});
  onScroll();
  // 表格首列不换行控制（长文本除外）
  document.querySelectorAll('table thead th').forEach(function(th, i){ });
})();
</script>
"""

OUTHTML = fill("""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>美股主要指数系统性回测与对比分析（含位置指标与择时专题）</title>
<style>%s</style>
</head>
<body>
<nav id="toc">
  <h4>目录</h4>
  %s
</nav>
<main>
%s
</main>
%s
%s
</body>
</html>
""",  CSS, toc_html, BODY, FOOT, JS)

with open(HTML_OUT, "w", encoding="utf-8") as f:
    f.write(OUTHTML)
print("saved", HTML_OUT, "%.1f KB" % (os.path.getsize(HTML_OUT)/1024))
print("sections:", OUTHTML.count("<section"), " tables:", OUTHTML.count("<table"), " figures:", OUTHTML.count("<figure"))
