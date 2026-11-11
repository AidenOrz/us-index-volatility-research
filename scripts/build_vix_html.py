# -*- coding: utf-8 -*-
"""生成单文件 HTML：VIX 类指数买卖点判断专题。"""
import os
import json
import base64
import html

BASE = r"E:\workspace\new"
OUT = os.path.join(BASE, "data", "output")
FIG = os.path.join(BASE, "output", "figures")
HTML_OUT = os.path.join(BASE, "output", "VIX类指数买卖点判断专题.html")

D = json.load(open(os.path.join(OUT, "vix_html_data.json"), encoding="utf-8"))


def esc(s):
    return html.escape(str(s))


def fig(name, caption=""):
    p = os.path.join(FIG, name)
    if not os.path.exists(p):
        return '<p class="warn">[缺图: ' + esc(name) + ']</p>'
    b64 = base64.b64encode(open(p, "rb").read()).decode("ascii")
    cap = '<figcaption>' + esc(caption) + '</figcaption>' if caption else ""
    return '<figure><img src="data:image/png;base64,' + b64 + '" alt="' + esc(caption) + '">' + cap + '</figure>'


def table(rows, header, cls="", align=None, caption=""):
    n = len(header)
    al = align or (["l"] + ["r"] * (n - 1))
    th = "".join('<th class="' + ("l" if a == "l" else "r") + '">' + esc(h) + '</th>'
                 for h, a in zip(header, al))
    body = []
    for r in rows:
        tds = "".join('<td class="' + ("l" if a == "l" else "r") + '">' + str(c) + '</td>'
                      for c, a in zip(r, al))
        body.append("<tr>" + tds + "</tr>")
    cap = '<caption>' + esc(caption) + '</caption>' if caption else ""
    return ('<table class="' + cls + '">' + cap + '<thead><tr>' + th +
            '</tr></thead><tbody>' + "".join(body) + '</tbody></table>')


def f2(v, d=2):
    if v is None:
        return "—"
    try:
        x = float(v)
    except Exception:
        return esc(v)
    if x != x:
        return "—"
    return ("%." + str(d) + "f") % x


def pct(v, d=2, sign=False):
    if v is None:
        return "—"
    try:
        x = float(v)
    except Exception:
        return esc(v)
    if x != x:
        return "—"
    s = ("%." + str(d) + "f%%") % x
    if sign and x > 0:
        s = "+" + s
    return s


def cls_of(v, base="num"):
    if v is None:
        return base
    try:
        x = float(v)
    except Exception:
        return base
    if x != x:
        return base
    if x > 0:
        return base + " up"
    if x < 0:
        return base + " down"
    return base


CSS = """
:root{--ink:#1a1f27;--muted:#5d6875;--line:#e2e6ec;--bg:#fff;--soft:#f6f8fa;
  --navy:#1f3b63;--accent:#c0392b;--teal:#0f8b8d;--gold:#bf8f00;--orange:#d1691c}
*{box-sizing:border-box}
html{scroll-behavior:smooth}
body{margin:0;background:var(--bg);color:var(--ink);
  font-family:"Microsoft YaHei","PingFang SC","Hiragino Sans GB",system-ui,-apple-system,"Segoe UI",sans-serif;
  font-size:15.5px;line-height:1.85;-webkit-font-smoothing:antialiased}
.wrap{max-width:1160px;margin:0 auto;padding:0 28px}
#toc{position:fixed;top:0;left:0;width:238px;height:100vh;overflow-y:auto;
  background:#fbfcfd;border-right:1px solid var(--line);padding:22px 16px;font-size:13.4px;z-index:20}
#toc h4{margin:0 0 10px;font-size:12.5px;letter-spacing:.08em;color:var(--muted);text-transform:uppercase}
#toc a{display:block;padding:5px 9px;color:#39424e;text-decoration:none;border-radius:5px;line-height:1.5}
#toc a:hover{background:#eef2f7;color:var(--navy)}
#toc a.sub{padding-left:22px;font-size:12.7px;color:#5d6875}
#toc a.active{background:var(--navy);color:#fff}
main{margin-left:238px}
@media (max-width:900px){#toc{display:none}main{margin-left:0}.wrap{padding:0 16px}}
header.cover{padding:72px 0 46px;border-bottom:3px solid var(--navy);
  background:linear-gradient(180deg,#fafcff,#fff)}
header.cover .kicker{font-size:12.5px;letter-spacing:.22em;color:var(--muted);text-transform:uppercase;margin-bottom:16px}
header.cover h1{font-size:38px;line-height:1.26;margin:0 0 14px;color:var(--navy);letter-spacing:-.5px}
header.cover .sub{font-size:16px;color:#41505f;margin-bottom:22px}
header.cover .meta{display:flex;flex-wrap:wrap;gap:10px 26px;font-size:13.5px;color:var(--muted)}
header.cover .meta b{color:var(--ink);font-weight:600}
h2{font-size:25px;margin:54px 0 16px;padding-bottom:10px;border-bottom:2px solid var(--navy);color:var(--navy)}
h3{font-size:19px;margin:32px 0 10px;color:var(--navy)}
h4{font-size:16px;margin:22px 0 8px;color:#2c3b4f}
p{margin:0 0 13px}
p.lead{font-size:16.5px;color:#33404f}
table{border-collapse:collapse;width:100%;margin:10px 0 14px;font-size:13.2px;
  font-variant-numeric:tabular-nums;background:#fff;box-shadow:0 1px 2px rgba(16,24,40,.06)}
caption{caption-side:top;text-align:left;font-size:13px;color:var(--muted);padding:2px 0 8px;font-weight:600}
th,td{padding:7px 10px;border-bottom:1px solid var(--line)}
thead th{background:var(--navy);color:#fff;font-weight:600;font-size:12.7px;white-space:nowrap;position:sticky;top:0;z-index:2}
tbody tr:nth-child(even){background:#fafbfc}
tbody tr:hover{background:#eef4fb}
td.l,th.l{text-align:left}
td.r,th.r{text-align:right}
table.small{font-size:12.4px}
table.small th,table.small td{padding:5px 8px}
td.up{color:#1e7a3c;font-weight:600}
td.down{color:var(--accent);font-weight:600}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(186px,1fr));gap:14px;margin:20px 0 26px}
.card{border:1px solid var(--line);border-radius:8px;padding:14px 16px;background:#fff}
.card .k{font-size:12.5px;color:var(--muted);letter-spacing:.04em}
.card .v{font-size:24px;font-weight:700;color:var(--navy);line-height:1.25;margin:3px 0}
.card .d{font-size:12.5px;color:var(--muted)}
.note{border-left:4px solid var(--navy);background:#f4f7fb;padding:12px 16px;margin:16px 0;
  border-radius:0 6px 6px 0;font-size:14.2px}
.note.warn{border-left-color:var(--accent);background:#fdf5f4}
.note.ok{border-left-color:#1e7a3c;background:#f3faf5}
.note b{color:var(--navy)}
figure{margin:22px 0 26px;text-align:center}
figure img{max-width:100%;height:auto;border:1px solid var(--line);border-radius:6px}
figcaption{font-size:13px;color:var(--muted);margin-top:8px}
.warn{color:var(--accent);font-size:13px}
ul,ol{margin:0 0 14px;padding-left:24px}
li{margin:5px 0}
b,strong{color:#16202c}
code{background:#f1f3f6;padding:1px 5px;border-radius:4px;font-size:.92em;
  font-family:Consolas,Menlo,monospace}
section{scroll-margin-top:12px}
hr{border:0;border-top:1px solid var(--line);margin:38px 0}
footer{margin-top:70px;padding:26px 0 60px;border-top:1px solid var(--line);color:var(--muted);font-size:13px}
.two{display:grid;grid-template-columns:1fr 1fr;gap:20px}
@media (max-width:900px){.two{grid-template-columns:1fr}}
.sigbox{border:1px solid var(--line);border-radius:8px;padding:16px 18px;background:#fff;margin:14px 0}
.sigbox h4{margin-top:0}
.badge{display:inline-block;padding:1px 9px;border-radius:11px;font-size:12px;font-weight:600;margin-left:6px}
.badge.buy{background:#e8f5ec;color:#1e7a3c}
.badge.sell{background:#fdeceb;color:#c0392b}
.badge.hold{background:#eef1f5;color:#4a5560}
@media print{#toc{display:none}main{margin-left:0}header.cover{padding:20px 0}
  h2{page-break-after:avoid}table,figure{page-break-inside:avoid}thead th{position:static}}
"""

TOC = [
    ("summary", "摘要", 0),
    ("c1", "一、先讲清楚 VIX 是什么", 0),
    ("c1-1", "1.1 它度量的是保险费，不是方向", 1),
    ("c1-2", "1.2 波动率风险溢价（VRP）", 1),
    ("c2", "二、数据与交叉验证", 0),
    ("c2-1", "2.1 四个波动率指数", 1),
    ("c2-2", "2.2 双源比对", 1),
    ("c2-3", "2.3 对口指数 vs 通用 VIX", 1),
    ("c3", "三、VIX 水平能判断买卖点吗", 0),
    ("c3-1", "3.1 分层：不是单调线，是 U 型", 1),
    ("c3-2", "3.2 加上趋势过滤：唯一负值区间", 1),
    ("c3-3", "3.3 盈亏比视角", 1),
    ("c4", "四、期限结构：VIX 与 VIX3M 的关系", 0),
    ("c5", "五、事件检验：具体在哪些点动手", 0),
    ("c5-1", "5.1 上穿阈值", 1),
    ("c5-2", "5.2 分位与急冲", 1),
    ("c5-3", "5.3 恐慌见顶确认", 1),
    ("c5-4", "5.4 收益路径", 1),
    ("c6", "六、在六个指数上是否普适", 0),
    ("c7", "七、稳健性：换个年代还成立吗", 0),
    ("c8", "八、把信号变成仓位", 0),
    ("c8-1", "8.1 策略回测", 1),
    ("c8-2", "8.2 样本外 2011 年以后", 1),
    ("c9", "九、与估值、期限结构的组合", 0),
    ("c10", "十、局限与六个陷阱", 0),
    ("c11", "十一、可执行的规则手册", 0),
    ("c11-1", "11.1 三买三卖", 1),
    ("c11-2", "11.2 仓位刻度", 1),
    ("c11-3", "11.3 当前读数（2026-11-09）", 1),
    ("appendix", "附录：数据文件", 0),
]

toc_html = "".join(
    '<a href="#' + tid + '" data-target="' + tid + '"' + (' class="sub"' if lvl else "") + '>' + esc(name) + '</a>'
    for tid, name, lvl in TOC)

# ============================ 封面 ============================
cover = """
<header class="cover"><div class="wrap">
<div class="kicker">Volatility Index · Timing Research</div>
<h1>VIX 类指数如何用于买卖点判断</h1>
<p class="sub">对 VIX / VIX3M / VXN / RVX 做过拟合、事件与策略三层检验后，一份可以照着做的规则手册</p>
<div class="meta">
<span><b>样本区间</b> 1990-01-02 ~ 2026-11-06</span>
<span><b>策略回测</b> 1994-05-05 ~ 2026-11-06（8,183 个交易日）</span>
<span><b>标的</b> 标普500 / 纳指100 / 罗素2000</span>
<span><b>数据源</b> CBOE 官方 + Yahoo（双源比对）</span>
</div>
</div></header>
"""

# ============================ 摘要 ============================
summary = """
<section id="summary"><div class="wrap">
<h2>摘要</h2>
<div class="cards">
""" + "".join([
    '<div class="card"><div class="k">VIX 与未来 1 年收益的单调性</div><div class="v" style="color:#c0392b">不存在</div>'
    '<div class="d">20-25 区最差（+4.4%），两端更好</div></div>',
    '<div class="card"><div class="k">VIX ≥ 40 之后 1 年</div><div class="v">+32.95%</div>'
    '<div class="d">胜率 96.2%，超额 +22.5pp</div></div>',
    '<div class="card"><div class="k">VIX ≥ 40 的天数占比</div><div class="v">2.5%</div>'
    '<div class="d">208 天，仅 10 段独立事件</div></div>',
    '<div class="card"><div class="k">VRP 为正的交易日</div><div class="v">85.31%</div>'
    '<div class="d">中位溢价 4.66 点（26.91%）</div></div>',
    '<div class="card"><div class="k">当前 VIX（2026-11-09）</div><div class="v">19.92</div>'
    '<div class="d">68.2% 分位，期限正常 contango</div></div>',
    '<div class="card"><div class="k">按刻度建议仓位</div><div class="v">80%</div>'
    '<div class="d">落在 13-20 档</div></div>',
]) + """
</div>

<p class="lead">VIX 类指数在择时上的价值，被高估的部分和真实存在的部分差别很大。市场上的普遍说法是「VIX 高就买、
VIX 低就卖」，这句话在数据上<b>只有一半对</b>：VIX 高的时候买，长期确实好；但 VIX 低的时候卖，长期是错的。</p>

<div class="note"><b>六条核心结论</b>
<ol>
<li><b>VIX 与未来收益的关系是 U 型，不是单调反向。</b>全样本里 VIX 20-25 档未来 1 年只有 +4.38%（胜率 64.4%），
比 VIX&lt;13 的 +12.00%（胜率 89.6%）和 VIX&gt;40 的 +32.95%（胜率 96.2%）都差。真正该减仓的是「温和警觉」这一档，不是「极度平静」。</li>
<li><b>U 型的最深处要叠加趋势才致命。</b>VIX 20-25 且 SPX 跌破 200 日线时，未来 1 年 <b>−6.54%、胜率仅 40.1%</b>（597 个交易日）——
这是全部 12 个交叉格子里唯一的负值。同样是 VIX 20-25 但站上年线，收益是 +10.54%。</li>
<li><b>恐慌见顶的「确认」比「触发」重要得多。</b>VIX 上穿 25 之后 1 年只有 +3.56%（跑输基准 6.9pp，六指数全部跑输）；
但 VIX 自 63 日高点回落 40% 以上且仍高于 25 时买入，1 年 +23.58%、胜率 96.8%（31 次）。前者是「还在跌」，后者是「跌完了」。</li>
<li><b>短周期唯一有统计显著性的用法，是逆向。</b>VIX 水平的 IC21 = +0.125（t=2.46）、期限倒挂 IC63 = +0.369（t=3.05），
都是正号——即 VIX 越高，随后收益越高。等权/市值宽度 IC21 = −0.189（t=−2.83）方向相反，别把「宽度恶化」当恐慌买点。</li>
<li><b>VIX 本身不预测方向，它预测的是波动。</b>VIX 与随后 21 日已实现波动的相关是 0.717，VIX 中位高于随后实现波动 4.66 点，
85.31% 的交易日为正。所以 VIX 的第一用途是<b>定仓位与定风险预算</b>，第二用途才是择时。</li>
<li><b>把 VIX 当唯一信号做策略，全样本小幅改善夏普，样本外全部跑输买入持有。</b>最好的一档是「U 型 + 跌破年线再砍半」，
夏普 0.63 vs 买入持有 0.56、最大回撤 −32.98% vs −56.78%，代价是年化从 8.98% 降到 6.75%。2011 年以后所有 VIX 策略夏普都低于买入持有的 0.74。</li>
</ol></div>

<p>所以这份报告的主线是：<b>不要用 VIX 猜方向，要用 VIX 定仓位；不要在 VIX 上升途中买，要在 VIX 见顶确认后买；
不要卖掉「太安静」的市场，要减掉「温和警觉 + 趋势走坏」的市场。</b></p>
</div></section>
"""

# ============================ 一、VIX 是什么 ============================
c1 = """
<section id="c1"><div class="wrap">
<h2>一、先讲清楚 VIX 是什么</h2>

<h3 id="c1-1">1.1 它度量的是保险费，不是方向</h3>
<p>VIX 是 CBOE 用标普500 期权的一整条行权价链反解出来的<b>30 天隐含波动率</b>，年化、以百分数计。
它回答的问题是：<i>未来 30 天，期权市场愿意为「标普500 的年化波动会有多大」付多少钱</i>。
它<b>不回答</b>涨还是跌——期权定价对方向是中性的。</p>
<p>这一点直接决定了它的用法。把 VIX 当「恐慌指数」然后反向操作，隐含了一个未经检验的假设：
恐慌之后必然反弹。这个假设在极端区间大致成立，在中间区间完全不成立，下面第三章会用数据把这件事讲透。</p>

<h3 id="c1-2">1.2 波动率风险溢价（VRP）</h3>
<p>既然 VIX 是「保险的价格」，那么保险通常比实际赔付贵，这个差价叫<b>波动率风险溢价 VRP = VIX − 随后 21 个交易日的已实现波动</b>。
我们按 1990-01-02 ~ 2026-10-08 共 9,260 个有效交易日做了测算（末尾 21 个交易日留空，不用未来数据回填）：</p>
""" + table([
    ["VRP 中位数", "4.66 点", "VIX 中位比随后实现波动中位高 4.66 个点"],
    ["VRP 均值", "4.06 点", "标准差 6.70，厚尾明显"],
    ["VRP 为正的交易日占比", "85.31%", "保险长期系统性偏贵"],
    ["溢价占 VIX 比例（中位）", "26.91%", "VIX 里有约四分之一是风险溢价"],
    ["VRP 为负的交易日", "1,360 天（14.69%）", "极端值 2020-02-19 为 −69.90 点"],
    ["VIX 与未来 21 日实现波动相关", "0.717", "VIX 是有效的波动先行读数"],
], ["指标", "数值", "说明"], caption="表 1-1  波动率风险溢价（VRP）全样本统计", align=["l", "r", "l"]) + """

<p>按 VIX 分档看，会出现一个反直觉但很稳定的现象：<b>VIX 越高，绝对溢价越大，但相对溢价率反而越小</b>。</p>
""" + table([
    [esc(r["VIX档"]), f2(r["天数"], 0), pct(r["VRP中位数"]), pct(r["VRP占VIX比"]), pct(r["未来21日实现波动中位数"]), pct(r["随后21日SPX平均收益"], 2, True), pct(r["随后21日胜率"])]
    for r in D["vix_vrp"]
], ["VIX 档", "天数", "VRP 中位（点）", "VRP 占 VIX 比", "随后实现波动（中位）", "随后 21 日 SPX 收益", "胜率"],
    cls="small", align=["l", "r", "r", "r", "r", "r", "r"], caption="表 1-2  按 VIX 分档的波动率风险溢价") + """

<div class="note"><b>怎么读这张表：</b>
<ul>
<li>VIX 在 15-20 时保险最贵（溢价率 29.37%）——这是「不痛不痒的贵」，最难忍，也最难赚。</li>
<li>VIX 掉到 12 以下，溢价率 28.67%，绝对溢价缩到 3.12 点。市场安静时买保险的性价比并不差。</li>
<li>VIX 冲到 40 以上，绝对溢价 8.06 点看着吓人，但相对 VIX 自身只有 16.18%——<b>极端恐慌时，VIX 相对自己的量级并不算贵</b>。
这解释了一个常见困惑：「VIX 都 40 了还买股票？」——因为 40 的世界里，波动本来就该这么大。</li>
<li>收益侧完全非单调：VIX &lt;12 档随后 21 日 +0.73%（胜率 67.7%），&gt;40 档 +2.80%（胜率 63.5%，但样本只有 208 天），
中间 20-25 档最差 +0.44%（胜率 59.7%）。<b>用 VIX 预测一个月的涨跌，做不到。</b></li>
</ul></div>

""" + fig("18_VIX与实现波动.png",
          "图 1-1  VIX 是未来波动的先行读数（相关 0.72），但溢价率随恐慌加深而收窄") + """
</div></section>
"""

# ============================ 二、数据与交叉验证 ============================
c2 = """
<section id="c2"><div class="wrap">
<h2>二、数据与交叉验证</h2>

<h3 id="c2-1">2.1 四个波动率指数</h3>
<p>本报告用到 CBOE 官方的四个波动率指数，都是收盘价、日频、年化百分数：</p>
""" + table([
    [esc(r["指数"]), esc(r["起始"]), esc(r["末日"]), f2(r["交易日"], 0), f2(r["均值"]), f2(r["中位"]),
     f2(r["最小值"]), f2(r["最大值"]), f2(r["P10"]), f2(r["P90"])]
    for r in D["vix_family"]
], ["指数", "起始", "末日", "交易日", "均值", "中位", "最小值", "最大值", "P10", "P90"],
    cls="small", align=["l", "l", "l", "r", "r", "r", "r", "r", "r", "r"],
    caption="表 2-1  VIX 家族描述统计（CBOE 官方文件）") + """

<p>三者的水平相关系数在 0.906~0.953 之间，日变化相关 0.915~0.933，均值比 VXN/VIX = 1.182、RVX/VIX = 1.301。
也就是说<b>小盘股的隐含波动长期比大盘贵三成</b>，纳指比标普贵不到两成。这个结构性差异意味着：
用同一个 VIX 阈值去判断罗素2000 的买卖点，阈值天生偏低。</p>

<h3 id="c2-2">2.2 双源比对</h3>
<p>波动率数据一旦算错，所有结论都会错。我们把能拿到两个独立来源的指标全部逐日对齐：</p>
""" + table([
    [esc(r["指标"]), esc(r["源A"]), esc(r["源B"]), f2(r["重叠天数"], 0),
     f2(r["中位绝对差"], 4) if r["中位绝对差"] is not None else "—",
     f2(r["均值绝对差"], 4) if r["均值绝对差"] is not None else "—",
     esc(r["最大绝对差_带日期"]) if r["最大绝对差_带日期"] else "—",
     pct(r["相对差超0_1pct占比"]) if r["相对差超0_1pct占比"] is not None else "—",
     f2(r["日收益率相关"], 6) if r["日收益率相关"] is not None else "—",
     esc(r["结论"])]
    for r in D["vix_crosscheck"]
], ["指标", "源 A", "源 B", "重叠天数", "中位绝对差", "均值绝对差", "最大绝对差", "相对差>0.1% 占比", "日收益相关", "结论"],
    cls="small", align=["l", "l", "l", "r", "r", "r", "r", "r", "r", "l"],
    caption="表 2-2  VIX 类数据的多源交叉比对") + """

<div class="note ok"><b>结论：</b>VIX 是这四个指标里<b>唯一可以交叉验证</b>的——Yahoo 与 CBOE 官方在 9,279 个交易日上重叠，
中位绝对差 0.0000、均值 0.0006、相对差超过 0.1% 的交易日只占 0.12%、日收益率相关 0.998676、涨跌方向不一致只有 6 天。
VIX3M（Yahoo 单源 5,111 天）、VXN（CBOE 单源 4,317 天）、RVX（CBOE 单源 4,308 天）都只有单一来源，无法互校，
使用时应当保留这个前提。另外我们做了冗余校验：本报告使用的日频面板里的 VIX / VIX3M 与原始数据逐日差为 0，下游无二次加工误差。</div>

<h3 id="c2-3">2.3 对口指数 vs 通用 VIX</h3>
<p>既然纳指和罗素都有自己的波动率指数，直接用对口的会不会更准？答案是<b>不一定</b>，这个检验值得单独说。</p>
""" + table([
    [esc(r["标的"]), esc(r["波动率指数"]), esc(r["信号"]), f2(r["次数"], 0),
     pct(r["12M均值%"]), pct(r["12M胜率%"]), pct(r["超额pp"], 2, True)]
    for r in D["vix_family_sig"]
], ["标的", "用哪个波动率", "信号", "次数", "未来 12M 均值", "12M 胜率", "超额 pp"],
    cls="small", align=["l", "c", "l", "r", "r", "r", "r"],
    caption="表 2-3  对口波动率指数与通用 VIX 的效果对比（2009-09 以后同区间）") + """

<p>以「波动率 ≥ 40」这一个信号为例：2009-09 之后的同一样本里，用 VIX 判断纳指的点位超额 +35.50pp，
改用对口的 VXN 是 +32.60pp；判断罗素时用 VIX 是 +34.87pp，改用 RVX 是 +37.51pp。
<b>两者互有胜负、量级相当</b>，结论是：
用通用 VIX 就够了，不必为了「更对口」而牺牲样本长度——VIX 有 36 年历史，VXN/RVX 只有 17 年。
只有在 VIX 与 VXN/RVX 出现<b>明显背离</b>时才值得看后者（例如科技板块独跌而大盘平稳）。</p>

<p>当前三者读数：VIX 25.64（10 年分位 86.7%）、VXN 34.02（92.4%）、RVX 26.16（71.9%）。
<b>VXN 分位明显高于 VIX，说明这轮担忧集中在科技/成长，不是全面的流动性危机。</b></p>
</div></section>
"""

# ============================ 三、VIX 水平 ============================
c3 = """
<section id="c3"><div class="wrap">
<h2>三、VIX 水平能判断买卖点吗</h2>

<h3 id="c3-1">3.1 分层：不是单调线，是 U 型</h3>
<p>把 1994-05-05 以来的每个交易日按 VIX 收盘分成 9 档，统计其后 1 个月到 1 年的表现：</p>
""" + table([
    [esc(r["分组"]), f2(r["天数"], 0), pct(r["占比%"]), f2(r["VIX中位"]),
     pct(r["1M均值%"], 2, True), pct(r["1M胜率%"]),
     pct(r["12M均值%"], 2, True), pct(r["12M胜率%"]),
     pct(r["未来21日实现波动%"]), esc(r["说明"])]
    for r in D["vix_level_bins"]
], ["VIX 档", "天数", "占比", "中位 VIX", "1M 均值", "1M 胜率", "12M 均值", "12M 胜率", "随后实现波动", "定性"],
    cls="small", align=["l", "r", "r", "r", "r", "r", "r", "r", "r", "l"],
    caption="表 3-1  VIX 绝对水平分层（SPX，1994-05~2026-11）") + """

<p>全样本基准是未来 1 年 +10.49%、胜率 79.46%。上表读出来的形状是：</p>
<ul>
<li><b>左端不差</b>：VIX 11-13 档 12M +13.01%（胜率 91.6%），是除极端恐慌外最好的一档。市场安静不等于危险。</li>
<li><b>中间塌陷</b>：VIX 20-25 档 12M 只有 +4.38%、胜率 64.4%，是整张表<b>唯一明显低于基准</b>的区间。</li>
<li><b>右端最好</b>：VIX 30-40 档 +17.46%（83.0%），&gt;40 档 +32.95%（96.2%）。恐慌越深，随后的赔率越好。</li>
<li><b>20-25 档占了 20.5% 的交易日，是九档里出现频率最高的一档</b>——正因为它常见又温和，才特别容易被忽视。</li>
</ul>

""" + fig("15_VIX水平分层.png",
          "图 3-1  VIX 水平分层：越恐慌，未来一年越好（1994-05~2026-11，SPX）") + """

<h3 id="c3-2">3.2 加上趋势过滤：唯一负值区间</h3>
<p>UV 型本身还不够，因为它没区分「恐慌是因为企业盈利塌了，还是因为流动性冲击」。加一条最简单的趋势过滤——SPX 是否站上 200 日线——就能把风险定位到具体格子里：</p>
""" + table([
    [esc(r["VIX区间"]), esc(r["趋势"]), f2(r["天数"], 0),
     pct(r["12M均值%"], 2, True), pct(r["12M胜率%"]), pct(r["12M最差%"], 2, True)]
    for r in D["vix_ushape"]
], ["VIX 区间", "趋势状态", "天数", "未来 12M 均值", "12M 胜率", "12M 最差"],
    cls="small", align=["l", "l", "r", "r", "r", "r"],
    caption="表 3-2  VIX 区间 × 200 日线趋势（SPX，未来 12 个月）") + """

""" + fig("16_VIX_U型曲线.png",
          "图 3-2  VIX 与未来收益不是单调关系：两端高、中间（20-25）最低") + """

<div class="note warn"><b>这是整份报告最有用的一张表。</b>
<ul>
<li><b>VIX 20-25 + 跌破 200 日线 = −6.54%、胜率 40.1%（597 天）</b>。这是 12 个格子里唯一的负值，
也是「最该减仓」的精确刻画。它同时满足三个条件：情绪已有警觉、趋势已经走坏、还没到真正的恐慌。</li>
<li>VIX 25-30 + 跌破年线 = +0.09%、胜率 53.5%（452 天），基本是白干。</li>
<li>反过来，VIX 30-40 + 跌破年线 = <b>+16.36%、胜率 80.3%</b>（408 天）；VIX &gt;40 + 跌破年线 = <b>+32.97%、胜率 96.1%</b>（206 天）。
一旦恐慌进入两位数尾部，趋势坏不坏已经不重要了。</li>
<li>VIX &lt;13 + 跌破年线 = +24.83%（95 天）——但这种组合极其罕见（安静的市场里跌破年线），统计意义有限。</li>
</ul>
减仓的准确条件不是「VIX 低」，而是「VIX 温和偏高（20-30）+ 趋势走坏」。这两条同时出现才动手。</div>

<h3 id="c3-3">3.3 盈亏比视角</h3>
<p>只看期望收益会漏掉一个重要维度：涨跌空间的不对称性。我们统计每个 VIX 档位在未来 1 年内的最大上行与最大下行的中位数
（相对当日价格），再算盈亏比：</p>
""" + table([
    [esc(r["分组"]), f2(r["VIX中位"]), pct(r["未来1年最大上行%"]), pct(r["未来1年最大下行%"]), f2(r["盈亏比"]),
     pct(r["12M均值%"], 2, True)]
    for r in D["vix_level_bins"]
], ["VIX 档", "中位 VIX", "未来 1 年最大上行（中位）", "未来 1 年最大下行（中位）", "盈亏比", "12M 均值"],
    cls="small", align=["l", "r", "r", "r", "r", "r"],
    caption="表 3-3  各 VIX 档位的盈亏比结构") + """

<p>盈亏比是一条 U 型曲线的镜像：VIX 0-11 档盈亏比 7.31、11-13 档 4.48、30-40 档 4.17，而
<b>20-25 档只有 1.87</b>，是全表最低。这意味着在 20-25 这一档买进去，即使最后没亏，过程也最难受——
上行空间只有下行空间的不到两倍。</p>
<p>这也解释了为什么很多人在 VIX 20 出头的时候「觉得便宜就买」然后被震出去：不是方向错了，是<b>过程中的赔率不对</b>。</p>
</div></section>
"""

# ============================ 四、期限结构 ============================
c4 = """
<section id="c4"><div class="wrap">
<h2>四、期限结构：VIX 与 VIX3M 的关系</h2>
<p>单一 VIX 水平有一个明显缺陷：不同年代的「正常波动水平」不一样。1990 年代 VIX 常态 12-15，2008 年以后常态 15-20。
滚动 10 年分位解决了这个问题；另一个更干净的解法是看<b>期限结构</b>——
VIX（30 天）与 VIX3M（3 个月）的比值。正常情况下远期波动率高于近期（contango），
一旦倒挂，说明市场认为<b>眼前的冲击比三个月后更严重</b>。</p>

""" + table([
    [esc(r["分组"]), f2(r["天数"], 0), pct(r["占比%"]), f2(r["VIX中位"]),
     pct(r["1M均值%"], 2, True), pct(r["1M胜率%"]),
     pct(r["12M均值%"], 2, True), pct(r["12M胜率%"]),
     pct(r["未来21日实现波动%"]), esc(r["说明"]) if r["说明"] else "—"]
    for r in D["vix_ts_bins"]
], ["VIX/VIX3M−1", "天数", "占比", "中位 VIX", "1M 均值", "1M 胜率", "12M 均值", "12M 胜率", "随后实现波动", "定性"],
    cls="small", align=["l", "r", "r", "r", "r", "r", "r", "r", "r", "l"],
    caption="表 4-1  VIX 期限结构分层（VIX3M 自 2006-07 起）") + """

<div class="note"><b>期限结构是这份报告里「最诚实」的指标。</b>
<ul>
<li><b>深度倒挂（&gt;+10%）时，短期更痛</b>：未来 1 个月 −1.48%、胜率只有 58.7%，随后 21 日实现波动中位 46.62——
这是全表最高的。也就是说，倒挂是一个「现在就很危险」的读数。</li>
<li><b>但一年后是好的</b>：12M +15.03%、胜率 74.4%、超额 +4.54pp。</li>
<li><b>极度 contango（&lt;−20%）时并不差</b>：12M +8.73%，只是略低于基准（−1.76pp）。所谓「市场太自满要跌」，数据不支持。</li>
</ul>
所以期限倒挂的正确用法是：<b>它不是当天买入的理由，而是「开始分批」的理由。</b>
先建 1/3 仓，一个月后再看是否止跌——因为倒挂期间短期大概率还要再挨一下。</div>

<p>把 VIX 分位与期限结构交叉，会得到一张更细的四象限（分位阈值取 75%）：</p>
""" + table([
    [esc(r["象限"]), f2(r["天数"], 0), pct(r["占比%"]), pct(r["1M均值%"], 2, True), pct(r["1M胜率%"]),
     pct(r["12M均值%"], 2, True), pct(r["12M胜率%"]), pct(r["12M最差%"], 2, True)]
    for r in D["vix_quad2"]
], ["象限", "天数", "占比", "1M 均值", "1M 胜率", "12M 均值", "12M 胜率", "12M 最差"],
    cls="small", align=["l", "r", "r", "r", "r", "r", "r", "r"],
    caption="表 4-2  VIX 分位 × 期限结构四象限") + """

<p>关键一行是 <b>「VIX 低 × 倒挂」：1M +1.62%（胜率 71.3%）看着不错，但 12M 只有 +0.06%、胜率 53.2%</b>，
是四个象限里唯一一年后接近零的。这个组合的意思是「眼下不慌，但远期被定价得更糟」——
典型的事件驱动型担忧（关税、财报、选举），随后往往演化成慢跌。这是全表最该警惕的状态，而不是「VIX 高」。</p>
</div></section>
"""

# ============================ 五、事件检验 ============================
c5 = """
<section id="c5"><div class="wrap">
<h2>五、事件检验：具体在哪些点动手</h2>
<p>分层统计回答「处于什么状态」，事件检验回答「什么时候扣扳机」。我们检验了 19 个离散信号，全部以信号日为起点、统计其后表现，
并与全样本基准（12M +10.49%、胜率 79.46%）对比。</p>

""" + fig("19_VIX历史与阈值.png",
          "图 5-1  VIX 全历史与买卖点阈值：极端恐慌区极稀薄（VIX≥40 仅 208 天 / 2.5%，10 段事件）") + """

<h3 id="c5-1">5.1 上穿阈值</h3>
""" + table([
    [esc(r["分组"]), f2(r["天数"], 0), f2(r["VIX中位"]),
     pct(r["1M均值%"], 2, True), pct(r["1M胜率%"]),
     pct(r["12M均值%"], 2, True), pct(r["12M胜率%"]),
     pct(r["1M相对基准pp"], 2, True) if r["1M相对基准pp"] is not None else "—",
     pct(r["12M相对基准pp"], 2, True) if r["12M相对基准pp"] is not None else "—",
     f2(r["盈亏比"]), esc(r["最近触发日"]) if r["最近触发日"] else "—"]
    for r in D["vix_events"]
], ["信号", "天数", "中位 VIX", "1M 均值", "1M 胜率", "12M 均值", "12M 胜率", "1M 超额", "12M 超额", "盈亏比", "最近触发"],
    cls="small", align=["l", "r", "r", "r", "r", "r", "r", "r", "r", "r", "c"],
    caption="表 5-1  19 个 VIX 信号的事件检验（1994-05~2026-11）") + """

<div class="note warn"><b>最反直觉的一行：VIX 上穿 25 之后，未来一年只有 +3.56%、胜率 62.6%，跑输基准 6.93pp。</b>
这是全部信号里最差的。而 VIX 上穿 20 也是负超额（−1.92pp）。只有上穿 30（+1.59pp）和上穿 40（+14.54pp）才转正。</div>
<p>为什么？因为「上穿」意味着趋势还在恶化。<b>收盘价第一次越过某条阈值，那只是恐慌的开始，不是结束。</b>
VIX 从 20 涨到 30 的过程里，标普平均还要再跌一段。这解释了为什么很多人在「VIX 破 20 了，该买了」之后又挨了一轮——
他们买在了恐慌的中段。</p>

<h3 id="c5-2">5.2 分位与急冲</h3>
<p>绝对阈值的问题是会随年代漂移——1990 年代 VIX 常态 12-15，2008 年以后常态 15-20。
滚动 10 年分位和「相对自身 20 日均线的倍数」这两个相对化指标更稳健。下表把这 19 个信号按 12 个月超额从高到低排：</p>
""" + table([
    [esc(r["分组"]), f2(r["天数"], 0), pct(r["12M均值%"], 2, True), pct(r["12M胜率%"]),
     pct(r["12M相对基准pp"], 2, True) if r["12M相对基准pp"] is not None else "—",
     pct(r["未来21日实现波动%"]), esc(r["说明"]) if r["说明"] else "—"]
    for r in sorted([x for x in D["vix_events"] if x["分组"] != "全样本基准"],
                    key=lambda x: (x["12M相对基准pp"] if x["12M相对基准pp"] is not None else -999),
                    reverse=True)
], ["信号", "天数", "12M 均值", "12M 胜率", "12M 超额", "随后实现波动", "方向"],
    cls="small", align=["l", "r", "r", "r", "r", "r", "l"],
    caption="表 5-2  19 个信号按 12 个月超额降序排列") + """

<p>把 19 个信号按 12M 超额排序，结论非常整齐：</p>
<ul>
<li><b>正向超额最大的五个</b>：VIX&gt;20 日均线×2（+16.05pp）、VIX 上穿 40（+14.54pp）、分位&gt;95%（+9.22pp）、
VIX&gt;20 日均线×1.5（+8.14pp）、分位&gt;90%（+6.96pp）——全是<b>极端</b>读数。</li>
<li><b>负向超额只有四个</b>，而且全在「温和」区间：VIX 上穿 25（−6.93pp）、VIX 创 1 年新低（−2.17pp）、
VIX 上穿 20（−1.92pp）、深度 contango（−1.76pp）。其余 14 个信号超额均为正。</li>
<li><b>「自满」读数没有想象中危险</b>：VIX&lt;13 后 12M +12.00%、胜率 89.6%，比基准还高；VIX 下穿 12 后 +13.63%、胜率 95.9%。
「VIX 太低所以要跌」这句话在 33 年样本里不成立。</li>
</ul>

<h3 id="c5-3">5.3 恐慌见顶确认</h3>
<p>既然「触发」是坏信号，那什么才是好信号？我们的假设是：<b>恐慌的结束</b>。定义两类确认：</p>
<ul>
<li>温和确认：VIX 自 63 日高点回落 25% 以上，且仍 &gt;20（143 次）</li>
<li>强确认：VIX 自 63 日高点回落 40% 以上，且仍 &gt;25（31 次）</li>
</ul>
""" + table([
    [esc(r["事件"]), f2(r["样本数"], 0)] + [pct(r["%d日均值%%" % h], 2, True) for h in [21, 63, 126, 252, 504]]
    for r in D["vix_path"]
], ["事件", "样本", "21 日", "63 日", "126 日", "252 日", "504 日"],
    cls="small", align=["l", "r", "r", "r", "r", "r", "r"],
    caption="表 5-3  恐慌见顶确认与恐慌触发的事件后收益对比") + """

<p>强确认的 12M 是 +23.58%、胜率 96.8%；温和确认反而只有 +8.16%（低于基准）——
这说明<b>只回落 25% 不算见顶，只是中场休息</b>，回落 40% 才是真的转折。
这条规则把「VIX 上穿 40 后买入」的粗放做法，改造成了可操作的确认机制。</p>

<h3 id="c5-4">5.4 收益路径</h3>
""" + fig("17_VIX事件后路径.png",
          "图 5-2  恐慌信号触发后的收益路径：VIX>40 从第 1 个月起就领先") + """

<p>路径图给出了另一个实用信息：<b>VIX 上穿 40 之后，第 21 日就已经有 +3.16%（胜率 78.8%）</b>，
63 日 +8.79%（90.9%），252 日 +25.03%（87.9%），504 日 +37.46%（96.8%）。
而全样本基准到 252 日才 +10.49%。也就是说极端恐慌买点的优势<b>建立得很快</b>，不需要等一年才见效——
这对实际操作很重要，因为它意味着不必承受漫长的浮亏期。</p>
<p>但对照组也很清楚：VIX 上穿 25 的 252 日只有 +3.56%，504 日仅 +7.97%，全程低于基准。
同一条指标的 25 与 40，是完全相反的用处。</p>
</div></section>
"""

# ============================ 六、六指数普适性 ============================
c6 = """
<section id="c6"><div class="wrap">
<h2>六、在六个指数上是否普适</h2>
<p>只在一个指数上成立的规则不能信。我们把 17 个信号（样本量 ≥30 的）在六个指数上全部重跑，看 12 个月超额的方向是否一致：</p>
""" + table([
    [esc(r["信号"]), esc(r["方向"]), f2(r["信号日数"], 0)] +
    [pct(r[t + "_超额pp"], 2, True) for t in ["SPX", "DJI", "IXIC", "NDX", "RUT", "SOX"]] +
    [pct(r["六指数超额均值pp"], 2, True), f2(r["六指数同向数"], 0) + "/6"]
    for r in D["vix_by_index"]
], ["信号", "方向", "天数", "标普500", "道指", "纳指综合", "纳指100", "罗素2000", "费半", "六指数均值", "同向数"],
    cls="small", align=["l", "c", "r", "r", "r", "r", "r", "r", "r", "r", "r"],
    caption="表 6-1  同一信号在六个指数上的 12 个月超额（pp）") + """

<div class="note ok"><b>结论：极端恐慌类信号在六个指数上 100% 同向。</b>
<ul>
<li>VIX 上穿 40：六指数全部正超额，均值 +23.43pp，费城半导体最高（+38.52pp）。越科技、越beta高的资产，恐慌买点的弹性越大。</li>
<li>VIX 分位&gt;95%：6/6 同向，均值 +14.83pp；VIX&gt;20 日均线×1.5：6/6 同向，均值 +12.28pp。</li>
<li>反过来，VIX 上穿 20 / 上穿 25 / 创 1 年新低：同向数只有 0~1/6，均值 −4.42 / −4.81 / −5.49pp。
<b>这类信号在六个指数上一致地「不是买点」。</b></li>
</ul>
所以规则是跨市场普适的，不需要按指数改阈值——但仓位幅度可以按 beta 调，费半/纳指100 的恐慌加仓应该更激进。</div>
</div></section>
"""

# ============================ 七、稳健性 ============================
c7 = """
<section id="c7"><div class="wrap">
<h2>七、稳健性：换个年代还成立吗</h2>
<p>33 年的样本里经历了三到四个完全不同的波动率体制。我们把 VIX 各档位拆成四个子样本重跑：</p>
""" + (lambda: (lambda subs: table(
    [[esc(lab)] + [pct(next((x["12M均值%"] for x in D["vix_robust"] if x["区间"] == lab and x["子样本"] == s), None), 2, True) for s in subs]
     for lab in ["VIX<13", "13-20", "20-25", "25-30", "30-40", "VIX>40"]]
    , ["VIX 档"] + subs, cls="small", align=["l"] + ["r"] * 4,
    caption="表 7-1  未来 12 个月均值的分年代稳健性（%）"))(["1994-2003", "2004-2013", "2014-2019", "2020-2026"]))() + """

""" + (lambda: (lambda subs: table(
    [[esc(lab)] + [f2(next((x["天数"] for x in D["vix_robust"] if x["区间"] == lab and x["子样本"] == s), 0), 0) for s in subs]
     for lab in ["VIX<13", "13-20", "20-25", "25-30", "30-40", "VIX>40"]]
    , ["VIX 档"] + subs, cls="small", align=["l"] + ["r"] * 4,
    caption="表 7-2  对应的样本天数"))(["1994-2003", "2004-2013", "2014-2019", "2020-2026"]))() + """

<div class="note"><b>稳健的部分与脆弱的部分要分开看：</b>
<ul>
<li><b>极端恐慌（&gt;40）四个子样本全是大幅正收益</b>：23.35 / 30.17 / 15.51 / 50.45。但 2014-2019 只有 1 天，是唯一没有统计含量的格子。</li>
<li><b>自满（&lt;13）四个子样本也全正</b>：23.92 / 7.94 / 8.68 / 18.25。再次印证「VIX 低不是卖点」。</li>
<li><b>20-25 档在 2004-2013 是 −3.69%</b>，2020-2026 是 +15.50%。方向不一致——这一档的结论依赖当时的宏观背景，
不能机械套用，必须叠加趋势过滤（第三章 3.2 节）。</li>
</ul>
这也是我们最终把「20-25 档」的减仓规则限定在「且跌破 200 日线」的原因：单独一档不够稳。</div>

<p>另一个容易忽视的问题是<b>极端读数的日期聚集</b>。VIX ≥ 40 看起来有 208 个交易日（占 2.5%），
但把它们按「间隔超过 60 天算一次独立事件」合并后，只有 <b>10 段</b>：</p>
""" + table([
    [esc(r["信号"]), f2(r["天数"], 0), f2(r["独立事件数(间隔>60日)"], 0), esc(r["首次"]), esc(r["末次"])]
    for r in D["vix_extreme"]
], ["信号", "天数", "独立事件数", "首次", "末次"],
    cls="small", align=["l", "r", "r", "c", "c"],
    caption="表 7-3  极端读数的日期聚集：有效样本远小于天数") + """

<p>VIX ≥ 50 只有 75 天、<b>3 段独立事件</b>（2008 金融危机、2020 疫情、2025 关税冲击）。
分位&gt;95% 有 416 天但 17 段，期限倒挂&gt;10% 有 134 天但 18 段——
后两者的有效样本量相对可用。这也提醒：所有「VIX&gt;40 后一年 +33%」的结论，本质上只有 <b>10 个独立观测</b>，
统计显著性远低于表面数字给人的印象。</p>
</div></section>
"""

# ============================ 八、策略 ============================
c8 = """
<section id="c8"><div class="wrap">
<h2>八、把信号变成仓位</h2>
<p>信号只有变成仓位才有意义。所有策略均为 T+1 生效、单边成本 5bp、空仓部分按无风险利率计息，
样本 1994-05-05 ~ 2026-11-06（8,183 个交易日）。</p>

<h3 id="c8-1">8.1 策略回测</h3>
""" + table([
    [esc(r["策略"]), pct(r["累计%"], 1), pct(r["年化%"]), pct(r["波动%"]), f2(r["夏普"], 3),
     pct(r["最大回撤%"]), f2(r["卡玛"], 2), pct(r["平均仓位%"]), f2(r["年换手"], 2)]
    for r in D["vix_strategy"]
], ["策略", "累计收益", "年化", "波动", "夏普", "最大回撤", "卡玛", "平均仓位", "年换手"],
    cls="small", align=["l", "r", "r", "r", "r", "r", "r", "r", "r"],
    caption="表 8-1  VIX 类策略回测（全样本）") + """

<p>买入持有年化 8.98%、夏普 0.556、最大回撤 −56.78%。九种 VIX 用法里：</p>
<ul>
<li><b>夏普最高的是「纯 VIX 分档·顺势」</b>（0.611，年化只有 6.42%，回撤 −35.50%）——
注意这是<b>顺势</b>版本（越平静仓位越重），不是常见的逆向版本。逆向版本（越恐慌越重）只有 0.52。</li>
<li><b>直接用 VIX 定仓位（C：&lt;12 减到 4 成 / &gt;30 满仓）几乎没有改善</b>：年化 8.49%、夏普 0.53、回撤仍是 −56.78%。
原因是这条规则在 2008 和 2020 都没能及时降仓——VIX 触发时跌幅已经发生。</li>
<li><b>「恐慌见顶确认后才买」（E）是全场最差</b>：年化 4.47%、夏普 0.34。它错过了大部分上涨，
且要在回撤里等确认。</li>
<li>把 VIX 与趋势结合（F）能到 8.56% / 0.59 / −46.10%，比纯 VIX 好，但仍不如买入持有的收益。</li>
</ul>

""" + fig("20_VIX仓位刻度.png",
          "图 8-1  U 型仓位刻度：不预测方向，只按情绪定价调仓位") + """

<p>按第三章的 U 型实测结果设计的阶梯（VIX&lt;13→95%、13-20→80%、20-25→45%、25-30→80%、30-40→95%、&gt;40→100%），
加上「跌破年线时最低砍到 50%」的否决条件后：年化 6.75%、夏普 0.63、最大回撤 −32.98%、卡玛 0.20。
<b>用 2.2 个百分点的年化，换回 24 个百分点的最大回撤</b>——这是 VIX 择时最诚实的性价比。</p>

<h3 id="c8-2">8.2 样本外 2011 年以后</h3>
""" + table([
    [esc(r["策略"]), pct(r["年化%"]), pct(r["波动%"]), f2(r["夏普"], 3), pct(r["最大回撤%"]), pct(r["平均仓位%"])]
    for r in D["vix_strategy_oos"]
], ["策略", "年化", "波动", "夏普", "最大回撤", "平均仓位"],
    cls="small", align=["l", "r", "r", "r", "r", "r"],
    caption="表 8-2  样本外检验（2011-01-01 ~ 2026-11-06）") + """

<div class="note warn"><b>必须说清楚：2011 年以后，所有 VIX 策略的夏普都低于买入持有（0.740）。</b>
最接近的是「50% 底仓 + 50% VIX 阈值」（0.72）和「期限结构」（0.71），但它们本质上是<b>降低仓位</b>而不是<b>提高效率</b>：
年化也从 11.75% 降到 11.44% / 11.30%。唯一在风险调整上真正有优势的是「纯 VIX 分档·顺势」——
夏普 0.71 接近基准，但回撤只有 −17.36%（基准 −33.92%），代价是年化 7.53%。</div>

<p>这个结果和整份报告的立场一致：<b>VIX 类指数的确定性价值在于降低尾部风险，
而不在于提高长期收益。</b>如果你的目标是「活得久」，它有用；如果你的目标是「跑得快」，它拖后腿。</p>
</div></section>
"""

# ============================ 九、组合 ============================
c9 = """
<section id="c9"><div class="wrap">
<h2>九、与估值、期限结构的组合</h2>
<p>单看 VIX 不够，把它与估值分位交叉，能看到一个很有用的分工：<b>VIX 管短期入场的时点，估值管长期的胜率上限。</b></p>
""" + table([
    [esc(r["组合"]), f2(r["天数"], 0), pct(r["未来1年收益%"], 2, True), pct(r["胜率%"]),
     pct(r["未来1年最大下行%(中位)"]), pct(r["未来1年最大上行%(中位)"])]
    for r in D["vix_interaction"]
], ["VIX 分位 × 估值分位", "天数", "未来 1 年收益", "胜率", "未来 1 年最大下行（中位）", "未来 1 年最大上行（中位）"],
    cls="small", align=["l", "r", "r", "r", "r", "r"],
    caption="表 9-1  VIX 分位 × CAPE 分位 的 12 种组合") + """

<div class="note ok"><b>三个可以直接用的组合：</b>
<ul>
<li><b>VIX&gt;90% 分位 × 估值&lt;33% 分位 = +25.32%、胜率 94.4%（323 天）</b>。恐慌加上便宜，这是全场最好的格子。</li>
<li><b>VIX&gt;90% 分位 × 估值&gt;67% 分位 = +12.28%、胜率 60.9%</b>。恐慌但贵，收益还有，胜率掉到六成——
<b>恐慌不能抵消估值</b>。</li>
<li><b>VIX 50-90% × 估值 33-67% = −0.20%、胜率 53.2%（590 天）</b>。温和警觉加上估值中性，一年后大概率白干。</li>
</ul>
注意第一行与第二行的差别：同样是极端恐慌，便宜的时候胜率 94%，贵的时候 61%。
<b>VIX 决定「现在能不能买」，估值决定「买了以后赢面多大」。</b></div>

<p>这也解释了 1999-2000 与 2008 的区别：1999 年 VIX 也不低（当时多次冲到 30 以上），
但 CAPE 在 44 的历史极值，那之后的一年是负收益；2008 年 VIX 冲到 80，CAPE 跌到 15 以下，之后是十年的牛市起点。
<b>只看 VIX 会在这两次里做出一模一样的动作，而正确的动作正相反。</b></p>
</div></section>
"""

# ============================ 十、局限与陷阱 ============================
c10 = """
<section id="c10"><div class="wrap">
<h2>十、局限与六个陷阱</h2>

<h3>数据局限</h3>
<ul>
<li><b>样本长度不对称。</b>VIX 有 1990 年以来的 9,311 个交易日，但策略回测的公共起点受六个指数中最晚的费半（1994-05-04）限制，
实际回测区间是 1994-05-05 起 8,183 天。VIX3M 从 2006-07 才有，期限结构相关结论的有效样本短得多。</li>
<li><b>极端读数只有极少独立事件。</b>VIX≥40 的 208 天可合并为 10 段，VIX≥50 只有 3 段。所有「极端恐慌后一年 +33%」的结论，
本质上是对 10 次历史事件的描述，不是统计规律。</li>
<li><b>VXN / RVX 单源、单一区间。</b>2009-09 起、4,300 天左右，无法交叉验证，也不覆盖 2008 危机。</li>
<li><b>回测存在前视偏差风险。</b>本报告所有分位均用滚动 10 年窗口（窗口 2,520 天、最少 1,260 天）计算，
不使用全样本分位；信号 T+1 生效；成本按单边 5bp。但 VIX 收盘价与标普收盘价同为收盘时点，
实际操作中 VIX 收盘读数要在收盘后约 15 分钟才能确认，实盘会有一天的滞后。</li>
</ul>

<h3>六个常见陷阱</h3>
<div class="note warn">
<ol>
<li><b>把「VIX 高」等同于「该买」。</b>VIX 上穿 20 是负超额（−1.92pp），上穿 25 是 −6.93pp。
恐慌的<b>中段</b>是最危险的，因为趋势还在恶化、赔率又不够。</li>
<li><b>把「VIX 低」等同于「该卖」。</b>VIX&lt;13 后一年 +12.00%、胜率 89.6%，比基准还高。
自满不等于见顶。</li>
<li><b>忽略趋势过滤。</b>VIX 20-25 单独看是 +4.38%，加上「跌破年线」变成 −6.54%。差 11 个百分点，全靠这一个条件。</li>
<li><b>把期限倒挂当日线买点。</b>倒挂&gt;10% 时未来 1 个月是 −1.48%、胜率 58.7%，随后实现波动中位 46.62%。
它是「开始分批」的信号，不是「满仓」的信号。</li>
<li><b>用 VIX 预测方向。</b>VIX 与未来收益的相关系数在短周期上只有 0.1~0.2 量级，对 21 日收益的 IC 是 +0.125。
它预测的是<b>波动</b>（相关 0.717），不是收益。</li>
<li><b>过度拟合阈值。</b>20 / 25 / 30 / 40 这些整数阈值没有理论依据，只是历史分位的大致位置。
本报告的稳健性检验显示，换成年份或换成相邻阈值，单档结论会漂移——
所以最终规则用「分档 + 趋势 + 分位」三重条件，而不是单一数字。</li>
</ol>
</div>
</div></section>
"""

# ============================ 十一、规则手册 ============================
c11 = """
<section id="c11"><div class="wrap">
<h2>十一、可执行的规则手册</h2>

<h3 id="c11-1">11.1 三买三卖</h3>
<div class="sigbox">
<h4>买点 <span class="badge buy">加仓</span></h4>
<ul>
<li><b>买点① 极端恐慌</b>：VIX ≥ 40 <b>或</b> VIX 滚动 10 年分位 ≥ 95% <b>或</b> VIX &gt; 20 日均线 × 1.5。
动作：把仓位加到满格，2-3 个交易日内分批完成。<br>
依据：处于 VIX≥40 状态的 208 个交易日，其后 12 个月平均 +32.95%、胜率 96.2%（超额 +22.5pp）；
<b>首次</b>上穿 40 的 33 个事件日，其后 12 个月 +25.03%、胜率 87.9%、超额 +14.54pp，且六个指数全部同向；
分位&gt;95% 后 +19.70%/胜率 75.4%/超额 +9.22pp；VIX&gt;20 日均线×1.5 后 +18.62%/83.6%/超额 +8.14pp。</li>
<li><b>买点② 恐慌见顶确认</b>：VIX 自 63 日高点回落 ≥40% 且仍 &gt;25。
动作：确认当日买入，持有 12 个月，不做其他判断。<br>
依据：31 次样本，12M +23.58%/胜率 96.8%，126 日 +15.75%/93.6%。这是本报告里胜率最高的单一规则。</li>
<li><b>买点③ 期限倒挂</b>：VIX/VIX3M − 1 &gt; +10%。
动作：<b>只加不追</b>——先建 1/3 仓，一个月后视是否止跌再补。<br>
依据：1M −1.48%（短期更痛），但 12M +15.03%/胜率 74.4%/超额 +4.5pp。</li>
</ul>
</div>

<div class="sigbox">
<h4>卖点 <span class="badge sell">减仓</span></h4>
<ul>
<li><b>卖点① 温和警觉 + 趋势走坏</b>：VIX 处于 20-30 且 SPX 跌破 200 日线。
动作：把仓位降到 50% 以下。<br>
依据：VIX 20-25 + 跌破年线 = 未来 1 年 −6.54%/胜率 40.1%（597 天），是全部格子唯一的负值；
VIX 25-30 + 跌破年线 = +0.09%/53.5%（452 天），基本白干。</li>
<li><b>卖点② 深度 contango</b>：VIX/VIX3M − 1 &lt; −20%。
动作：减到半仓（防守，不是清仓）。<br>
依据：12M +8.73%，低于基准 1.76pp；但胜率仍有 76.8%，不是灾难信号。</li>
<li><b>卖点③ 极端恐慌中估值也极高</b>：VIX &gt; 90% 分位 且 CAPE &gt; 90% 分位。
动作：可以买，但把仓位上限压到 50%，且缩短持有期到 6 个月。<br>
依据：VIX&gt;90% 分位 × 估值&gt;67% 分位时胜率只有 60.9%（vs 估值&lt;33% 时的 94.4%）。</li>
</ul>
</div>

<div class="note"><b>明确不要做的两件事：</b>
① 不要在 VIX 上升途中（上穿 20/25）加仓——这是全样本里最差的信号；
② 不要因为 VIX 低于 13 或创 1 年新低就减仓——这两条在 33 年里都是错的。</div>

<h3 id="c11-2">11.2 仓位刻度</h3>
<p>如果不想做方向判断，只想要一个仓位刻度，可以按第三章实测的 U 型直接给：</p>
""" + table([
    [esc(r["档位"]), pct(r["建议仓位%"], 0), esc(r["说明"]),
     pct(r["12M均值%"], 2, True), pct(r["12M胜率%"]), f2(r["盈亏比"]), f2(r["天数"], 0)]
    for r in D["vix_ladder"]
], ["VIX 水平", "建议仓位", "含义", "实测 12M 均值", "12M 胜率", "盈亏比", "天数"],
    align=["l", "r", "l", "r", "r", "r", "r"],
    cls="small", caption="表 11-1  U 型仓位刻度（收益与盈亏比均为实算）") + """

<p>再加一条否决条件：<b>当 SPX 跌破 200 日线时，把上表结果再乘 0.5 的上限（即最高 50%）</b>。
这条规则的回测结果：年化 6.75%、夏普 0.63、最大回撤 −32.98%、卡玛 0.20，
对比买入持有的 8.98% / 0.556 / −56.78% / 0.16。</p>

<h3 id="c11-3">11.3 当前读数（2026-11-09）</h3>
<div class="note ok"><b>数据已更新。</b>本报告首次定稿时（2026-11-06）VIX 为 25.64、期限结构倒挂；
做数据源尽调的过程中补到了 <b>2026-11-09</b> 的数据，市场已经发生显著变化：
SPX 两天 +2.35%，VIX 跌到 19.92（−22.3%），期限结构从倒挂 +4.23% 翻回 contango −4.46%。
下表与下文判断均已按 <b>11-09</b> 更新；11-06 的旧读数保留在
<a href="波动率数据源尽调与新增指标.html">《波动率数据源尽调与新增指标》</a> 第七章做对照。</div>
<p>把上面所有规则套用到当期数据上，逐项读数如下：</p>
""" + table([
    [esc(r["项目"]), f2(r["读数"]), esc(r["单位"]) if r["单位"] and r["单位"] != "nan" else "—",
     esc(r["状态"]) if r["状态"] and r["状态"] != "nan" else "—"]
    for r in D["vix_now"]
], ["项目", "读数", "单位", "状态"], align=["l", "r", "c", "l"], cls="small",
    caption="表 11-2  当期逐项读数") + """

<div class="note warn">
<b>把规则套到 2026-11-09 的读数上：</b>
<ul>
<li><b>VIX 19.92，10 年分位 68.2%</b> —— 落在「13~20 常态区」档，按刻度给 <b>80% 仓位</b>。</li>
<li><b>VIX/VIX3M = −4.46%（正常 contango）</b> —— 买点③（倒挂 &gt;+10%）已不成立，从「观察级」退回「无信号」。</li>
<li><b>VIX 距 20 日均线 1.04 倍</b> —— 未达 1.5 倍的急冲标准，买点①未触发。</li>
<li><b>VIX 自 63 日高点回落 29.3%</b> —— 已达温和确认（25%），但 VIX 已低于 25，
不满足强确认（回落 40% 且仍 &gt;25）的条件；按第五章 5.3 节，温和确认的 12 个月只有 +8.16%（低于基准），
<b>不作为买点</b>。</li>
<li><b>SPX 站上 200 日线 +3.03%，距 52 周高点 −3.44%</b> —— 卖点①的「趋势走坏」条件不成立。</li>
<li><b>CAPE 10 年分位 98.1%</b> —— 估值仍极贵。这是唯一持续的压力：一旦 VIX 重新回到 20-30
且 SPX 跌破 200 日线，就会同时满足「温和警觉 + 趋势坏 + 估值贵」，那是最差的三重组合。</li>
</ul>
<b>综合判断：仓位刻度仍是 80%，但状态从「恐慌初期」退回「常态」——风险由急转慢，警戒级别可以降一级。</b>
补充一条 11-09 的新信息：VVIX 从 121.94 回落到 98.43，按本轮新发现的规律（见数据源尽调报告第五章），
VVIX 从 130 以上的极动区回落，意味着短期反弹买点已经过去。</div>

<p>（下表的历史类比基于 <b>11-06</b> 的状态：VIX 分位 80%~95% + 期限倒挂 + 距高点 −3%~−10%，
出现过 62 个交易日、18 段独立事件。11-09 后已不满足「期限倒挂」条件，因此这张表只作参考。）</p>
""" + table([
    [esc(r["期限"]), f2(r["样本天数"], 0), pct(r["均值%"], 2, True), pct(r["中位%"], 2, True),
     pct(r["胜率%"]), pct(r["最差%"], 2, True), pct(r["最好%"], 2, True)]
    for r in D["vix_analog"]
], ["期限", "样本天数", "均值", "中位", "胜率", "最差", "最好"],
    cls="small", align=["l", "r", "r", "r", "r", "r", "r"],
    caption="表 11-3  相似历史状态后的表现") + """

<p>相似状态下未来一年的均值只有 +5.37%（胜率 74.5%），明显低于全样本的 +10.49%，
最差的一次是 −39.82%。<b>这与「当前维持仓位、不加仓」的判断一致。</b>
同时 2 年期均值 +12.99%、中位 +24.61%，说明拉长看这类状态并不致命——只是接下来一年大概率跑输基准。</p>
</div></section>
"""

# ============================ 附录 ============================
appendix = """
<section id="appendix"><div class="wrap">
<h2>附录：数据文件</h2>
""" + table([
    ["vix_crosscheck.csv", "VIX 家族多源逐日比对（6 行）"],
    ["vix_vrp.csv", "波动率风险溢价分档统计"],
    ["vix_family.csv", "VIX / VXN / RVX 描述统计"],
    ["vix_family_sig.csv", "对口波动率 vs 通用 VIX 效果对比"],
    ["vix_family_now.csv", "三者当前读数与 63 日高点回落"],
    ["vix_level_bins.csv", "VIX 绝对水平 9 档分层"],
    ["vix_pct_bins.csv", "VIX 滚动 10 年分位 6 档"],
    ["vix_ts_bins.csv", "期限结构 6 档"],
    ["vix_events.csv", "19 个离散信号事件检验"],
    ["vix_by_index.csv", "17 个信号 × 6 指数"],
    ["vix_path.csv", "事件后 5~504 日收益路径"],
    ["vix_robust.csv", "6 档 × 4 个子样本稳健性"],
    ["vix_peak.csv", "恐慌见顶规则作为策略"],
    ["vix_quad2.csv", "VIX 分位 × 期限结构四象限"],
    ["vix_extreme.csv", "极端读数日期聚集与独立事件数"],
    ["vix_interaction.csv", "VIX 分位 × CAPE 分位 12 组合"],
    ["vix_ushape.csv", "VIX 区间 × 趋势状态"],
    ["vix_ushape_strat.csv", "U 型仓位策略回测"],
    ["vix_analog.csv", "当前状态历史类比"],
    ["vix_strategy.csv", "9 个 VIX 策略回测"],
    ["vix_strategy_oos.csv", "样本外 2011 起回测"],
    ["vix_now.csv", "当期逐项读数"],
    ["vix_rulebook.csv", "规则手册结构化版本"],
], ["文件", "内容"], align=["l", "l"], cls="small", caption="表 A-1  配套数据文件") + """

<p style="margin-top:18px">数据源：CBOE 官方波动率指数（VIX / VXN / RVX，主源）、Yahoo Finance chart API（VIX / VIX3M，用于交叉验证）、
纳斯达克官方指数日线（用于收益端）、美国财政部 13 周贴现率（无风险利率）、multpl.com（CAPE 与估值分位）。</p>
</div></section>
"""

FOOT = """
<footer><div class="wrap">
<p><b>口径说明</b>：波动率数据为 CBOE 官方收盘价、年化百分数；收益端为主样本 1994-05-05 ~ 2026-11-06
（8,183 个交易日，32.51 年）；价格指数（不含股息）；无风险利率采用 ^IRX 日化；
所有分位均为滚动 10 年窗口（2,520 天，最少 1,260 天）；信号 T+1 生效，成本单边 5bp。</p>
<p><b>免责声明</b>：本文为历史数据研究与教学用途，不构成任何投资建议。历史表现不代表未来收益，
所有回测结论都存在样本内偏差、极端事件样本过少与参数过拟合风险。VIX 类衍生品本身具有高风险特征。</p>
<p style="color:#8893a1;margin-top:14px">生成时间：2026-11-10　·　分析工具：Python 3.12 / pandas 3.0.1 / matplotlib 3.11.2</p>
</div></footer>
"""

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
})();
</script>
"""

BODY = cover + summary + c1 + c2 + c3 + c4 + c5 + c6 + c7 + c8 + c9 + c10 + c11 + appendix

NL = chr(10)
OUTHTML = NL.join([
    "<!DOCTYPE html>",
    '<html lang="zh-CN">',
    "<head>",
    '<meta charset="utf-8">',
    '<meta name="viewport" content="width=device-width,initial-scale=1">',
    "<title>VIX 类指数如何用于买卖点判断（专题研究）</title>",
    "<style>" + CSS + "</style>",
    "</head>",
    "<body>",
    '<nav id="toc">',
    "<h4>目录</h4>",
    toc_html,
    "</nav>",
    "<main>",
    BODY,
    "</main>",
    FOOT,
    JS,
    "</body>",
    "</html>",
    "",
])

with open(HTML_OUT, "w", encoding="utf-8") as f:
    f.write(OUTHTML)
print("saved", HTML_OUT, "%.1f KB" % (os.path.getsize(HTML_OUT) / 1024))
print("sections:", OUTHTML.count("<section"), "tables:", OUTHTML.count("<table"), "figures:", OUTHTML.count("<figure"))
