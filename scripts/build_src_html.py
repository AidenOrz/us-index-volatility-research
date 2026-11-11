# -*- coding: utf-8 -*-
"""生成单文件 HTML：波动率数据源尽调与新增指标专题。"""
import os
import json
import base64
import html

BASE = r"E:\workspace\new"
OUT = os.path.join(BASE, "data", "output")
FIG = os.path.join(BASE, "output", "figures")
HTML_OUT = os.path.join(BASE, "output", "波动率数据源尽调与新增指标.html")

D = json.load(open(os.path.join(OUT, "src_html_data.json"), encoding="utf-8"))


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
header.cover h1{font-size:36px;line-height:1.26;margin:0 0 14px;color:var(--navy);letter-spacing:-.5px}
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
table.small{font-size:12.2px}
table.small th,table.small td{padding:5px 8px}
table.wide{font-size:11.8px;table-layout:fixed}
table.wide th,table.wide td{padding:4px 6px;word-break:break-word;overflow-wrap:anywhere}
table.wide code{background:none;padding:0;font-size:11.2px;color:#2c3b4f}
table.wide th:nth-child(1),table.wide td:nth-child(1){width:16%}
table.wide th:nth-child(2),table.wide td:nth-child(2){width:31%}
table.wide th:nth-child(3),table.wide td:nth-child(3){width:11%}
table.wide th:nth-child(4),table.wide td:nth-child(4){width:27%}
table.wide th:nth-child(5),table.wide td:nth-child(5){width:15%}
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
.badge{display:inline-block;padding:1px 9px;border-radius:11px;font-size:12px;font-weight:600;margin-left:6px}
.badge.ok{background:#e8f5ec;color:#1e7a3c}
.badge.mid{background:#fff4e5;color:#b26a00}
.badge.no{background:#fdeceb;color:#c0392b}
@media print{#toc{display:none}main{margin-left:0}header.cover{padding:20px 0}
  h2{page-break-after:avoid}table,figure{page-break-inside:avoid}thead th{position:static}}
"""

TOC = [
    ("summary", "摘要", 0),
    ("c1", "一、逐个站点实测结果", 0),
    ("c1-1", "1.1 CFTC 官网", 1),
    ("c1-2", "1.2 vixcentral.com", 1),
    ("c1-3", "1.3 investing.com", 1),
    ("c1-4", "1.4 TradingView", 1),
    ("c1-5", "1.5 顺手挖到的 CBOE 官方库", 1),
    ("c1-6", "1.6 完整清单", 1),
    ("c2", "二、CFTC：本轮最有价值的发现", 0),
    ("c2-1", "2.1 两套口径：Legacy 与 TFF", 1),
    ("c2-2", "2.2 谁在做空波动率", 1),
    ("c2-3", "2.3 空头拥挤度的实证", 1),
    ("c2-4", "2.4 为什么它不能单独当信号", 1),
    ("c3", "三、vixcentral：期货期限结构", 0),
    ("c4", "四、完整期限结构带来的新指标", 0),
    ("c5", "五、VVIX 与 SKEW", 0),
    ("c6", "六、三期比对的可靠性", 0),
    ("c7", "七、数据已更新到 2026-11-09", 0),
    ("c8", "八、局限与未完成的部分", 0),
    ("appendix", "附录：新增文件清单", 0),
]

toc_html = "".join(
    '<a href="#' + tid + '" data-target="' + tid + '"' + (' class="sub"' if lvl else "") + '>' + esc(name) + '</a>'
    for tid, name, lvl in TOC)

# ============================ 封面 ============================
cover = """
<header class="cover"><div class="wrap">
<div class="kicker">Data Source Due Diligence</div>
<h1>波动率数据源尽调：CFTC、vixcentral、investing、TradingView 实测</h1>
<p class="sub">逐个站点跑通、抓数、验证；哪些能用、哪些不能用、拿到了什么新东西</p>
<div class="meta">
<span><b>实测日期</b> 2026-11-10</span>
<span><b>站点</b> 6 个（CFTC / vixcentral / investing / TradingView / CBOE / Yahoo）</span>
<span><b>新下载</b> 23 个 CBOE 官方文件 + 2 份 CFTC 持仓</span>
<span><b>新增指标</b> 期限结构 4 档斜率、VVIX、SKEW、杠杆基金拥挤度</span>
</div>
</div></header>
"""

# ============================ 摘要 ============================
summary = """
<section id="summary"><div class="wrap">
<h2>摘要</h2>
<div class="cards">
""" + "".join([
    '<div class="card"><div class="k">CFTC 官网</div><div class="v" style="color:#1e7a3c">可用</div>'
    '<div class="d">Socrata API，VIX 期货持仓 1,120 周</div></div>',
    '<div class="card"><div class="k">vixcentral.com</div><div class="v" style="color:#b26a00">部分可用</div>'
    '<div class="d">期货曲线，只有当期 + 逐个日期查</div></div>',
    '<div class="card"><div class="k">investing.com</div><div class="v" style="color:#c0392b">不可用</div>'
    '<div class="d">VIX 历史接口全部返回 500</div></div>',
    '<div class="card"><div class="k">TradingView</div><div class="v" style="color:#b26a00">仅当期</div>'
    '<div class="d">只 VIX / VXN 有报价，其余 404</div></div>',
    '<div class="card"><div class="k">CBOE 官方</div><div class="v" style="color:#1e7a3c">23 个文件</div>'
    '<div class="d">VIX9D / VIX6M / VVIX / SKEW 全是新的</div></div>',
    '<div class="card"><div class="k">数据已更新到</div><div class="v">2026-11-09</div>'
    '<div class="d">比原报告推进 1 个交易日</div></div>',
]) + """
</div>

<p class="lead">你问的四个站点我去逐个实测了。结论是：<b>CFTC 是本轮唯一真正有价值的新数据源</b>，
vixcentral 和 TradingView 只能取当期快照（做交叉验证可以，做历史回测不行），
investing.com 的历史接口对指数类的 VIX 完全不开放。<b>但顺藤摸瓜在 CBOE 官方 CDN 上又挖到 23 个波动率指数文件</b>，
这批数据让「期限结构」从原来的 1 个斜率变成 4 个斜率，还多出 VVIX 和 SKEW 两个指标。</p>

<div class="note"><b>五条核心结论</b>
<ol>
<li><b>CFTC 拿到两套口径，其中 TFF 口径是新的。</b>Legacy 把持仓分成商业/非商业，太粗；
TFF 分成 Dealer（交易商）、Asset Manager（资管）、Leveraged Funds（杠杆基金）、Other Reportables 四类，
能直接识别「谁在做空波动率」。<b>答案是杠杆基金：82.9% 的周数净空，均值 −49,309 张</b>——这是 VIX 期货 contango 下做空波动率 carry 的直接证据。</li>
<li><b>「空头拥挤就要崩」这个直觉，数据不支持。</b>杠杆基金空头拥挤度分位 &gt;90% 的 202 周里，
随后 52 周 VIX 涨超 25% 的概率只有 <b>16.0%</b>，低于基准 27.45%；13 周 SPX 跌超 5% 的概率 10.89%，也低于基准 12.00%。
方向与先验相反。</li>
<li><b>为什么不能据此交易：控制当期 VIX 后，拥挤度的解释力消失。</b>预测 13 周 SPX 时，拥挤度系数 t 值只有 <b>0.15</b>，
而 VIX 自身 t=4.90。且超额在低 VIX 组 +6.77pp、高 VIX 组 −2.38pp，<b>符号翻转</b>——超额来自 VIX 均值回归，不是持仓。</li>
<li><b>CBOE 官方新增 4 档期限结构，斜率方向高度一致。</b>短端（VIX/VIX9D）、中端（VIX3M/VIX）、长端（VIX6M/VIX3M）、
全曲线（VIX6M/VIX9D）四条斜率，<b>全部呈现「越陡、未来一年越差」</b>：分位 0-10% 组的 12 个月收益 16.6%~18.9%，
分位 90-100% 组只有 7.3%~11.5%。</li>
<li><b>VVIX 与 SKEW 补上了一块空白。</b>VVIX 与「未来 21 日 VIX 变化」的相关是 <b>−0.2753</b>（负号意味着 VVIX 越高、VIX 随后越倾向回落），
而 SKEW 与未来收益几乎无关（−0.0114）——它度量的是左尾定价的<b>贵贱</b>，不是方向。</li>
</ol></div>

<p>另外必须说明一个口径变化：<b>数据已经推进到 2026-11-09</b>。11-06 那天 VIX 25.64、期限倒挂 +4.23%，
到 11-09 已经回到 VIX 19.92、期限结构 −4.46%（正常 contango），SPX 两天涨 2.35%。
所以上一份报告里「当前读数」那一节的部分结论需要按新数据更新，本报告第七章给出对照。</p>
</div></section>
"""

# ============================ 一、逐个站点实测 ============================
c1 = """
<section id="c1"><div class="wrap">
<h2>一、逐个站点实测结果</h2>
<p>测试环境：Windows / Python 3.12 / urllib（无 requests、无 yfinance）。
本机 <code>github.com:443</code> 与 Yahoo 直连被阻断，但 <code>127.0.0.1:7897</code> 代理可用；
CFTC 官网与 CBOE CDN 可直连。下面逐站说明。</p>

<h3 id="c1-1">1.1 CFTC 官网 <span class="badge ok">可用</span></h3>
<p>CFTC 有两条路：一是官网的年度压缩包 <code>cftc.gov/files/dea/history/deacot2026.zip</code>（直连 200，1993 年起按年分文件），
二是更现代的 Socrata 公开报表 API <code>publicreporting.cftc.gov</code>。后者能按合约名过滤、分页拉全量，明显更好用。</p>
<p>我们拉了两个数据集，都是 <b>VIX FUTURES - CBOE FUTURES EXCHANGE</b> 这一个合约：</p>
""" + table([
    ["Legacy - Futures Only", "6dca-aqww", "1,120 周", "2004-07-27 ~ 2026-11-03", "133 列", "商业 / 非商业 / 非报告 三分"],
    ["TFF - Futures Only", "gpe5-46if", "1,024 周", "2006-08-29 ~ 2026-11-03", "90 列", "交易商 / 资管 / 杠杆基金 / 其他 四分"],
], ["数据集", "Socrata ID", "行数", "覆盖区间", "列数", "分类口径"],
   cls="small", align=["l", "l", "r", "l", "r", "l"],
   caption="表 1-1  CFTC 两个口径的 VIX 期货持仓数据") + """

<div class="note"><b>三条必须知道的限制：</b>
① <b>周频</b>——每周二收盘的持仓，周五 15:30 ET 才公布，<b>有 3 天滞后</b>；
② 我们验证过：1,120 周里有 1,038 周的报告日+3 个交易日正好落在周五，说明这个滞后规则是稳定的；
③ TFF 起点是 2006-08 而不是 2004，比 Legacy 短两年。</div>

<p>几个实测中踩到的坑，写下来免得重复：</p>
<ul>
<li>Socrata 的 <code>$order</code> 参数里如果有空格会触发
<code>URL can't contain control characters</code>，必须 <code>urllib.parse.quote</code> 编码。</li>
<li>有些数据集（<code>ubmb-6exi</code> / <code>98ig-3k9y</code> / <code>8jj7-5vf4</code> / <code>dw8z-x6ih</code>）返回
403「no row or column access to non-tabular tables」——这是 Combined 口径的视图表，不是可查询的原始表。</li>
<li>Legacy 里那个列名是 <code>noncomm_postions_spread_all</code>，<b>postions 少一个 i</b>，是 CFTC 自己的拼写错误，按正常拼写取列会 KeyError。</li>
</ul>

<h3 id="c1-2">1.2 vixcentral.com <span class="badge mid">部分可用</span></h3>
<p>这个站最有价值的是 VIX 期货完整期限结构。页面本身直连 200，数据在三个内部 ajax 接口里：</p>
""" + table([
    ["/ajax_update", "GET，无参数", "VIX 期货当期 8 个到期月的买卖价/结算价", "可用，返回 15 行 JSON 数组，60 秒刷新"],
    ["/ajax_historical?n1=YYYY-MM-DD", "GET，逐日", "指定交易日的历史期限结构", '可用但只能逐日查，且部分日期返回 "error"'],
    ["/ajax_get_contango_data", "GET", "contango 图数据", "不可用，返回整页 HTML（是页面路由不是数据接口）"],
], ["端点", "调用方式", "内容", "实测结果"], cls="small", align=["l", "l", "l", "l"],
   caption="表 1-2  vixcentral 的三个内部接口") + """

<p>我们做了 <b>40 个交易日的均匀抽样</b>（2005-01-03 ~ 2026-03-31），可用率 <b>95%（38/40）</b>，
返回格式是 <code>[到期月序号, M1, M2, …, M9]</code>，例如 2020-03-16 是
<code>[3, 72.625, 59.15, 44.875, …]</code>——典型的深度倒挂。</p>

<p><b>但有一个致命的数据质量问题。</b>我们把 M1（近月期货）与同期 VIX 现货逐月对比，
发现 <b>2006 年至 2007 年 2 月之间，M1 全是 110~150 量级，而 VIX 现货只有 11~16</b>，偏差高达 900%~990%：</p>
""" + table([
    ["2006-02-01", "12.36", "126.60", "+924.3%", "错误"],
    ["2006-08-01", "15.05", "150.60", "+900.7%", "错误"],
    ["2006-12-29", "11.56", "123.00", "+964.0%", "错误"],
    ["2007-02-01", "10.31", "112.80", "+994.1%", "错误"],
    ["2007-03-30", "14.64", "14.49", "−1.0%", "正常"],
    ["2008-10-01", "39.81", "31.87", "−19.9%", "可接受（期货贴水）"],
    ["2008-12-01", "68.51", "60.45", "−11.8%", "可接受"],
], ["日期", "VIX 现货", "vixcentral M1", "偏差", "判定"], cls="small",
   align=["l", "r", "r", "r", "l"], caption="表 1-3  vixcentral 历史数据的可用性抽检") + """

<div class="note warn"><b>结论：vixcentral 的历史数据在 2007 年 3 月以前不可信</b>（M1 明显不是 VIX 期货价格，
可能是标普或别的标的串了）。<b>2007-03-30 以后偏差降到 ±20% 以内</b>，可以谨慎使用，
但依然要逐日校验，且没有批量接口——要做 20 年回测得发 5,000 次请求，不现实。
本报告只把它用于「当期快照」和少量历史时点对照。</div>

<h3 id="c1-3">1.3 investing.com <span class="badge no">不可用</span></h3>
<p>站点可以访问（走代理），VIX 页面 <code>/indices/volatility-s-p-500</code> 返回 1.07 MB HTML，
从中能抠到 <code>instrumentId = 44336</code>。但核心的历史数据接口打不通：</p>
""" + table([
    ["period=P5D, interval=P1D", "HTTP 500", "{\"@errors\":[\"invalid period time\"]}"],
    ["period=P1M / P1Y / P5Y / MAX", "HTTP 500", "{\"@errors\":[\"Core API respond with invalid status: 500\"]}"],
], ["请求", "响应", "说明"], cls="small", align=["l", "l", "l"],
   caption="表 1-4  investing.com VIX 历史接口的返回") + """

<p>作为对照，同一个接口用标普500 的 id=8839 是<b>完全可用</b>的（返回 OHLCV 数组）。
所以不是接口坏了，是<b>指数类品种（尤其 VIX）没有对公开 API 开放历史数据</b>。
另外 <code>api.investing.com/api/search/v2/search</code> 只返回文章不返回品种，也帮不上忙。
结论：<b>investing.com 这条路放弃</b>，标普500 我们本来就有更好的源。</p>

<h3 id="c1-4">1.4 TradingView <span class="badge mid">仅当期</span></h3>
<p>TradingView 的 scanner 接口 <code>scanner.tradingview.com/america/scan</code> 是 POST，且需要代理。
它能返回当前报价、涨跌幅、RSI、日波动率、技术评分。但覆盖范围很窄：</p>
""" + table([
    ["CBOE:VIX", "19.92", "−22.31%", "51.74", "可用"],
    ["CBOE:VXN", "28.97", "−14.84%", "53.04", "可用"],
    ["CBOE:RVX", "—", "—", "—", "404"],
    ["CBOE:VIX3M", "—", "—", "—", "404"],
    ["CBOE:VIX9D", "—", "—", "—", "404"],
    ["CBOE:VIX6M", "—", "—", "—", "404"],
    ["CBOE:VVIX", "—", "—", "—", "404"],
    ["CBOE:SKEW", "—", "—", "—", "404"],
], ["符号", "收盘", "涨跌", "RSI", "状态"], cls="small",
   align=["l", "r", "r", "r", "l"], caption="表 1-5  TradingView scanner 的实际覆盖（2026-11-09）") + """

<p>历史 K 线走不通：<code>symbol-search.tradingview.com</code> 一律 403，
<code>data.tradingview.com/symbols/</code> 直接断连（需要登录 token）。
另外 <code>scanner.tradingview.com/cboe/scan</code> 这个市场名不存在（404），只能用 <code>america</code>。</p>

<p><b>但它有一个用途：第三方当期校验。</b>我们拿 VIX 与 VXN 的当期收盘跟 CBOE 官方文件比，
<b>差值都是 0.0000</b>，完全一致。所以 TradingView 可以当作「当期读数的独立第三方确认」，
不能当历史数据源。</p>

<h3 id="c1-5">1.5 顺手挖到的 CBOE 官方库 <span class="badge ok">大丰收</span></h3>
<p>investing 和 TradingView 都不行，我们就回头把 CBOE 自己的 CDN 穷举了一遍。
路径规律是 <code>cdn.cboe.com/api/global/us_indices/daily_prices/{代码}_History.csv</code>，
注意那个 <code>index.json</code> 目录文件是 403 的，只能按代码猜。试了 27 个代码，<b>23 个有效</b>：</p>
""" + table([
    ["VIX", "1990-01-02", "9,311", "标普500 30 天"],
    ["VIX9D", "2011-01-04", "3,987", "标普500 9 天"],
    ["VIX3M", "2009-09-18", "4,313", "标普500 3 个月"],
    ["VIX6M", "2008-01-02", "4,745", "标普500 6 个月"],
    ["VVIX", "2006-03-06", "5,144", "VIX 的波动率"],
    ["SKEW", "1990-01-02", "9,267", "尾部风险偏度"],
    ["VXN", "2009-09-14", "4,319", "纳指100"],
    ["RVX", "2009-09-16", "4,310", "罗素2000"],
    ["OVX", "2009-09-18", "4,311", "原油"],
    ["GVZ", "2009-09-18", "4,311", "黄金"],
    ["VXEEM", "2011-03-16", "3,934", "新兴市场"],
    ["VXTLT", "2004-01-02", "5,739", "20+ 年美债"],
    ["其他 11 个", "2008~2011", "3,000~4,700", "个股/行业/商品波动率"],
], ["代码", "起始", "行数", "标的"], cls="small", align=["l", "l", "r", "l"],
   caption="表 1-6  CBOE 官方可下载的 23 个波动率指数文件") + """

<p>这批文件里，<b>对择时研究真正有用的是 VIX9D、VIX6M、VVIX、SKEW 四个</b>——
它们让「期限结构」从一个斜率（VIX/VIX3M）扩展成四个斜率，
并且补上了「尾部风险定价」这个此前完全没有的维度。第三章和第五章分别用上了。</p>

<h3 id="c1-6">1.6 完整清单</h3>
""" + table([
    [esc(r["站点"]), "<code>" + esc(r["端点"]) + "</code>", esc(r["可获取"]),
     esc(r["覆盖范围"]), esc(r["本轮处理"])]
    for r in D["source_inventory"]
], ["站点", "端点", "可获取", "覆盖范围", "本轮处理"], cls="wide",
   align=["l", "l", "l", "l", "l"], caption="表 1-7  六个站点 × 14 个端点的实测清单") + """

""" + fig("24_数据源覆盖.png",
          "图 1-1  本轮实际可用的波动率相关数据源：起点覆盖 1990~2026") + """

<p>这张图有个细节值得看：<b>VIX 现货有 36 年历史，但「期限结构」真正可用的历史只有 2009~2011 年以后</b>
（VIX3M / VIX9D / VIX6M 都是那时才有）。所以任何做期限结构的结论，
样本起点不可能早于 2009，这是数据本身的天花板，不是研究者的选择。</p>
</div></section>
"""

# ============================ 二、CFTC ============================
c2 = """
<section id="c2"><div class="wrap">
<h2>二、CFTC：本轮最有价值的发现</h2>

<h3 id="c2-1">2.1 两套口径：Legacy 与 TFF</h3>
<p>CFTC 对同一份持仓有多个分类口径。Legacy 是最老的，只分商业/非商业；TFF 是 2006 年为金融期货新设的，
把参与者分成四类，对波动率这种「谁在卖保险」的问题更有解释力：</p>
""" + table([
    ["交易商 Dealer/Intermediary", "做市商，双边报价，通常净空波动率", "77.6% 周数净多"],
    ["资管 Asset Manager/Institutional", "养老金、共同基金，买保护的主力", "83.3% 周数净多"],
    ["杠杆基金 Leveraged Funds", "对冲基金、CTA，做空波动率 carry 的主力", "<b>82.9% 周数净空，均值 −49,309 张</b>"],
    ["其他可报告 Other Reportables", "其余达到报告门槛的", "—"],
], ["TFF 分类", "典型行为", "本样本实测"], cls="small", align=["l", "l", "l"],
   caption="表 2-1  TFF 四类交易者的行为与实测结果") + """

<div class="note warn"><b>这里要修正一个常见误解。</b>很多资料说「商业持仓通常是空头」，
但实测 VIX 期货的 Legacy 商业净持仓<b>均值是 +46,934 张，是净多</b>；TFF 的交易商同样净多。
真正的净空方是<b>杠杆基金</b>。原因不难理解：VIX 期货长期 contango，
卖近月买远月（或单纯卖空）能吃到展期收益，这是典型的 carry 交易，杠杆基金是主要玩家。</div>

<h3 id="c2-2">2.2 谁在做空波动率</h3>
""" + fig("23_COT杠杆基金.png",
          "图 2-1  VIX 期货杠杆基金净空持仓：82.9% 的周数为净空，空头拥挤度可算分位") + """

<p>图中蓝线是杠杆基金净持仓（负值 = 净空），红区是「空头拥挤度」的滚动 3 年分位。
可以看到一个很稳定的形态：<b>市场平静时杠杆基金不断加空（蓝线下行、红区上升），
一旦 VIX 跳升就急速回补（蓝线飙升、红区骤降）</b>。2008、2015-08、2018-02、2020-03 都是典型。</p>
<p>这个形态本身很有说服力，但<b>能不能拿来做买卖点，是另一回事</b>——下面用数据检验。</p>

<h3 id="c2-3">2.3 空头拥挤度的实证</h3>
<p>把「杠杆基金空头拥挤度」按滚动 3 年分位分成 6 档，统计其后 SPX 与 VIX 的表现。
信号已按<b>报告日 +3 个交易日</b>对齐到可交易日：</p>
""" + table([
    [esc(r["分档"].replace("[杠杆基金空头拥挤度] ", "")), f2(r["样本周数"], 0),
     pct(r["13周SPX均值%"], 2, True), pct(r["13周胜率%"]),
     pct(r["52周SPX均值%"], 2, True), pct(r["52周胜率%"]),
     pct(r["52周SPX跌超5%概率%"]), pct(r["52周VIX涨超25%概率%"]), f2(r["52周t值"], 2)]
    for r in D["cot_tff_signal"] if "杠杆基金" in r["分档"]
], ["拥挤度分位", "样本周数", "13 周 SPX", "13 周胜率", "52 周 SPX", "52 周胜率",
    "52 周跌超 5% 概率", "52 周 VIX 涨超 25% 概率", "52 周 t 值"],
   cls="small", align=["l", "r", "r", "r", "r", "r", "r", "r", "r"],
   caption="表 2-2  杠杆基金空头拥挤度分档与随后表现（基准 = 全样本）") + """

<div class="note warn"><b>结果与直觉相反。</b>拥挤度 &gt;90%（空头最拥挤，理论上最该崩）的 202 周里：
<ul>
<li>随后 52 周 SPX <b>+14.71%</b>、胜率 <b>95.5%</b>——比基准（+13.42% / 86.39%）还略好；</li>
<li>随后 52 周 VIX 涨超 25% 的概率只有 <b>16.0%</b>，<b>低于</b>基准 27.45%；</li>
<li>随后 13 周 SPX 跌超 5% 的概率 10.89%，也<b>低于</b>基准 12.00%。</li>
</ul>
也就是说：<b>「波动率空头极度拥挤 → 迟早崩盘」这个流行叙事，在 2006-2026 的样本里没有兑现。</b>
反过来，拥挤度最低的 &lt;10% 组（空头最少）反而 52 周胜率只有 74.76%，是全表最低。</div>

<p>资管净多头寸（买保护的一方）同样测了一遍：</p>
""" + table([
    [esc(r["分档"].replace("[资管净多分位] ", "")), f2(r["样本周数"], 0),
     pct(r["13周SPX均值%"], 2, True), pct(r["52周SPX均值%"], 2, True), pct(r["52周胜率%"]),
     pct(r["52周VIX涨超25%概率%"])]
    for r in D["cot_tff_signal"] if "资管" in r["分档"]
], ["资管净多分位", "样本周数", "13 周 SPX", "52 周 SPX", "52 周胜率", "52 周 VIX 涨超 25% 概率"],
   cls="small", align=["l", "r", "r", "r", "r", "r"],
   caption="表 2-3  资管净多头寸分档（基准 13 周 +3.15%、52 周 +13.42%）") + """

<p>资管净多 75-90% 分位（机构买保护最积极）时，随后 52 周 SPX +16.41%、胜率 93.38%，
52 周 VIX 涨超 25% 概率只有 18.38%。<b>方向同样与「机构买保护 = 要跌」相反。</b>
最直观的解释是：机构买保护往往是在市场已经跌了一段、或即将进入低波动慢涨的时候，
保护费便宜才买，而不是因为预测要跌。</p>

<h3 id="c2-4">2.4 为什么它不能单独当信号</h3>
<p>上面的分档看着有单调性，但有一个致命问题：<b>持仓拥挤度和当期 VIX 水平高度共线</b>。
市场平静时 VIX 低、杠杆基金加空；VIX 高时回补。所以「拥挤度高」几乎等价于「VIX 低」，
而 VIX 低本身就对应未来一年收益较好（原报告第三章已经证明）。</p>
<p>我们做了回归检验，把当期 VIX 作为控制变量放进去：</p>
""" + table([
    ["预测 13 周 SPX 收益", "<b>0.15</b>", "4.90", "控制 VIX 后拥挤度完全失去解释力"],
    ["预测 13 周 VIX 变化", "0.83", "—", "同样不显著"],
    ["分组检验：低 VIX 下", "—", "—", "拥挤度 &gt;90% 组超额 <b>+6.77pp</b>"],
    ["分组检验：高 VIX 下", "—", "—", "拥挤度 &gt;90% 组超额 <b>−2.38pp</b>（符号翻转）"],
], ["检验", "拥挤度系数 t 值", "VIX 自身 t 值", "说明"], cls="small",
   align=["l", "r", "r", "l"], caption="表 2-4  控制当期 VIX 后的回归结果") + """

<div class="note"><b>结论：</b>杠杆基金空头拥挤度是一个<b>很好的描述性指标</b>（能讲清楚「谁在做空波动率」），
但<b>不是一个可交易的独立信号</b>。它的超额收益来自与 VIX 水平的共线，不是持仓本身。
真要用于决策，正确的做法是把它当成「市场结构的一个注脚」，而不是触发器。</div>

<p>顺便说一句口径比较：净头寸与未来 52 周 SPX 的相关系数，杠杆基金 −0.30、资管 +0.24、交易商 +0.24，
Legacy 只有 −0.18。<b>TFF 的信息量确实高于 Legacy</b>，Legacy 与杠杆基金的相关是 +0.71，本质是粗代理。</p>
</div></section>
"""

# ============================ 三、vixcentral ============================
c3 = """
<section id="c3"><div class="wrap">
<h2>三、vixcentral：期货期限结构</h2>
<p>vixcentral 的 <code>/ajax_update</code> 返回当期 VIX 期货的完整期限结构，这是 CBOE 的指数文件里没有的
（CBOE 给的是不同期限的<b>指数</b>，vixcentral 给的是<b>期货合约</b>价格）。两者有区别：
期货价格含展期与风险溢价，理论上比指数更能反映实际可交易的定价。</p>
""" + table([
    ["到期月", "Nov", "Dec", "Jan", "Feb", "Mar", "Apr", "May", "Jun"],
    ["结算价", "20.05", "19.55", "20.12", "20.47", "20.60", "20.90", "20.95", "21.10"],
], ["项目", "M1", "M2", "M3", "M4", "M5", "M6", "M7", "M8"], cls="small",
   align=["l", "r", "r", "r", "r", "r", "r", "r", "r"],
   caption="表 3-1  vixcentral 当期（2026-11-09）VIX 期货期限结构快照") + """

<p>有意思的是 M1（20.05）低于 M2（19.55）？不是——按列看是 M1=20.05、M2=19.55，<b>近月略高于次月</b>，
但 M3 以后重新上行。这是一个「驼峰型」的短端结构，说明市场认为<b>下个月的风险比这个月低、但 1 月以后风险回升</b>。
这种形态用单看 VIX/VIX3M 是看不出来的。</p>

<p>但我们最终<b>没有</b>用 vixcentral 做历史回测，三个原因：</p>
<ol>
<li><b>没有批量接口</b>，只能逐日 GET；20 年要约 5,000 次请求，单次 1~3 秒，不现实。</li>
<li><b>可用率 95%</b>（40 个抽样日里 2 个返回 error），有缺失但不致命。</li>
<li><b>2007 年 3 月以前数据明显错误</b>（M1 与 VIX 现货偏差 900%+），可用起点被压到 2007。</li>
</ol>
<p>而 CBOE 的 VIX9D/VIX3M/VIX6M 指数文件能覆盖 2009 年以后，
虽然口径是「指数」不是「期货」，但连续、免费、无缺失，做研究反而更合适。
<b>vixcentral 的正确用法是「看当期的期货曲线形态」，不是「做历史回测」。</b></p>
</div></section>
"""

# ============================ 四、完整期限结构 ============================
c4 = """
<section id="c4"><div class="wrap">
<h2>四、完整期限结构带来的新指标</h2>
<p>原来只有 VIX 与 VIX3M，只能算一个斜率。现在有 9 天 / 30 天 / 3 个月 / 6 个月四档，
可以构造四个斜率，分别刻画曲线的不同段落：</p>
""" + table([
    ["短端", "<code>VIX / VIX9D − 1</code>", "9 天 → 30 天", "对突发冲击最敏感"],
    ["中端", "<code>VIX3M / VIX − 1</code>", "30 天 → 3 个月", "传统 contango 度量"],
    ["长端", "<code>VIX6M / VIX3M − 1</code>", "3 个月 → 6 个月", "中期风险定价"],
    ["全曲线", "<code>VIX6M / VIX9D − 1</code>", "9 天 → 6 个月", "整体陡峭度"],
], ["斜率", "公式", "区间", "含义"], cls="small", align=["l", "l", "l", "l"],
   caption="表 4-1  四条期限结构斜率的定义") + """

""" + fig("21_期限结构曲线.png",
          "图 4-1  VIX 期限结构四档曲线：形态比单点读数信息量大得多") + """

<p>这张图对比了四个时点，能看出期限结构的形态本身就是一种状态描述：</p>
<ul>
<li><b>2020-03-16（疫情崩盘）</b>：9 天 72.6 → 6 个月 54.7，<b>深度倒挂</b>，短端比长端高 33%；
这是典型的「眼前就是灾难」。</li>
<li><b>2026-11-06（上份报告的基准日）</b>：9 天 27.18 → 6 个月 24.70，<b>轻度倒挂</b>。</li>
<li><b>2026-11-09（最新）</b>：9 天 19.88 → 6 个月 22.22，<b>恢复正常 contango</b>，两天内结构完全修复。</li>
<li><b>2017-07-11（极静）</b>：9 天 9.4 → 6 个月 14.9，陡峭 contango。</li>
</ul>

<p>把四条斜率按滚动 10 年分位分档，看未来表现：</p>
""" + table([
    [esc(r["斜率"]), esc(r["分位"]), f2(r["天数"], 0), pct(r["中位斜率%"], 2, True),
     pct(r["1M均值%"], 2, True), pct(r["3M均值%"], 2, True),
     pct(r["12M均值%"], 2, True), pct(r["12M胜率%"])]
    for r in D["vix_term_slopes"]
], ["斜率", "分位", "天数", "中位斜率", "1M 收益", "3M 收益", "12M 收益", "12M 胜率"],
   cls="small", align=["l", "l", "r", "r", "r", "r", "r", "r"],
   caption="表 4-2  四条斜率的分位与未来收益（2011-01 ~ 2026-11）") + """

""" + fig("22_斜率与未来收益.png",
          "图 4-2  期限结构越陡（分位越高），未来一年越差——四条斜率方向一致") + """

<div class="note ok"><b>这是本轮最干净的发现：四条斜率的方向完全一致。</b>
<table class="small" style="margin-top:8px">
<tr><th class="l">斜率</th><th class="r">0-10% 分位 12M</th><th class="r">90-100% 分位 12M</th><th class="r">差</th></tr>
<tr><td class="l">短端 VIX/VIX9D</td><td class="r">+16.63%</td><td class="r">+8.54%</td><td class="r">−8.1pp</td></tr>
<tr><td class="l">中端 VIX3M/VIX</td><td class="r">+18.94%</td><td class="r">+8.38%</td><td class="r">−10.6pp</td></tr>
<tr><td class="l">长端 VIX6M/VIX3M</td><td class="r">+18.76%</td><td class="r">+11.54%</td><td class="r">−7.2pp</td></tr>
<tr><td class="l">全曲线 VIX6M/VIX9D</td><td class="r">+18.51%</td><td class="r">+7.25%</td><td class="r">−11.3pp</td></tr>
</table>
<b>曲线越陡（远期比近期贵得越多），未来一年越差。</b>这一点和直觉相反——一般认为陡峭的 contango
代表市场健康，应该利好。但数据说：陡峭说明「眼下太平静、远期定价过高」，随后一年往往是均值回归。
中端斜率（VIX3M/VIX）区分度最好，0-10% 与 90-100% 组差 10.6 个百分点。</div>

<p>相关系数也印证了这一点（均为负）：</p>
""" + table([
    ["短端 VIX/VIX9D", "−0.0955", "−0.1588", "−0.1718"],
    ["中端 VIX3M/VIX", "−0.1477", "−0.2687", "−0.2494"],
    ["长端 VIX6M/VIX3M", "−0.1623", "−0.2682", "−0.2752"],
    ["全曲线 VIX6M/VIX9D", "−0.1386", "−0.2383", "−0.2474"],
], ["斜率", "vs 1 个月收益", "vs 3 个月收益", "vs 12 个月收益"], cls="small",
   align=["l", "r", "r", "r"], caption="表 4-3  斜率与未来收益的相关系数") + """

<p>注意<b>长端斜率的绝对值最大（−0.2752）</b>，而不是短端。这有点反直觉：
一般认为短端（9 天到 30 天）最能反映恐慌。但恰恰是<b>3 个月到 6 个月</b>这段
最能预测一年后的收益——因为它反映的是「中期风险定价是否过热」，而不是眼前的冲击。</p>

<p>当前四条斜率（2026-11-09）：</p>
""" + table([
    ["短端 VIX/VIX9D", "+0.20%", "23.4%", "偏低"],
    ["中端 VIX3M/VIX", "+4.67%", "18.6%", "偏低，接近陡峭端"],
    ["长端 VIX6M/VIX3M", "+6.57%", "36.4%", "中性"],
    ["全曲线 VIX6M/VIX9D", "+11.77%", "22.3%", "偏低"],
], ["斜率", "当前值", "10 年分位", "判定"], cls="small",
   align=["l", "r", "r", "l"], caption="表 4-4  当前四条斜率读数") + """

<p>四条斜率全在偏低分位（18.6%~36.4%），意味着<b>曲线并不陡</b>。
按上表的规律，这反而对应未来一年收益较好的区间——这是 11-09 相比 11-06 的一个重要变化：
11-06 那天中端斜率是深度倒挂的，两天后不但修复，还落到偏平的一端。</p>
</div></section>
"""

# ============================ 五、VVIX 与 SKEW ============================
c5 = """
<section id="c5"><div class="wrap">
<h2>五、VVIX 与 SKEW</h2>
<p>这两个指标此前完全没有纳入过。它们度量的都不是「波动有多大」，而是「波动率的波动」和「尾部定价的偏斜」。</p>

<h3>5.1 VVIX：波动率的波动率</h3>
<p>VVIX 是 VIX 期权的隐含波动率，简单说就是「市场对标普波动的分歧程度」。
它与 VIX 的相关只有 0.4251，说明它确实携带独立信息。</p>
""" + table([
    [esc(r["分组"]), f2(r["天数"], 0), pct(r["1M均值%"], 2, True), pct(r["3M均值%"], 2, True),
     pct(r["12M均值%"], 2, True), pct(r["12M胜率%"]), f2(r["未来21日VIX变化"], 2)]
    for r in D["skew_vvix_stat"] if r["指标"] == "VVIX"
], ["VVIX 水平", "天数", "1M 收益", "3M 收益", "12M 收益", "12M 胜率", "未来 21 日 VIX 变化（点）"],
   cls="small", align=["l", "r", "r", "r", "r", "r", "r"],
   caption="表 5-1  VVIX 分层（基准 12M +10.49%）") + """

<div class="note"><b>VVIX 的独特之处在于它预测的是「VIX 往哪走」，不仅仅是收益。</b>
<ul>
<li><b>VVIX &gt; 130（极动）</b>：135 天，未来 21 日 VIX <b>平均下降 10.67 点</b>——这是全部指标里最强的 VIX 回落信号；
同时未来 1 个月 SPX +5.01%、胜率 83.46%，3 个月 +8.47%。<b>VVIX 极高时买，是很好的短期买点。</b></li>
<li><b>VVIX &lt; 80（极静）</b>：933 天，未来 12 个月只有 <b>+3.71%</b>、胜率 71.08%——全表最差。
<b>「市场太安静」确实是个值得警惕的信号，而这个信号 VIX 本身给不出来</b>（VIX&lt;13 后一年反而是 +12%）。</li>
</ul>
这是一个真正的新发现：<b>VIX 低不需要担心，但 VVIX 低需要</b>。
两者的区别是：VIX 低只说明大家都觉得没事；VVIX 低说明大家连「会不会出事」都不讨论了。</div>

<p>相关系数验证了这个不对称性：<b>VVIX 与未来 21 日 VIX 变化的相关是 −0.2753</b>，
而 VIX 自身与未来 VIX 变化的相关接近 0（均值回归的必然）。也就是说 VVIX 在「VIX 拐点」上有真正的领先性。</p>

<h3>5.2 SKEW：尾部风险偏度</h3>
<p>SKEW 度量标普期权的左尾偏斜，数值越高说明虚值看跌被定价得越贵（大家在抢保护）。
它与 VIX 的相关是 <b>−0.2249</b>（负相关），与未来 21 日 SPX 的相关只有 <b>−0.0114</b>——几乎无关。</p>
""" + table([
    [esc(r["分组"]), f2(r["天数"], 0), pct(r["1M均值%"], 2, True), pct(r["3M均值%"], 2, True),
     pct(r["12M均值%"], 2, True), pct(r["12M胜率%"]), f2(r["未来21日VIX变化"], 2)]
    for r in D["skew_vvix_stat"] if r["指标"] == "SKEW"
], ["SKEW 水平", "天数", "1M 收益", "3M 收益", "12M 收益", "12M 胜率", "未来 21 日 VIX 变化（点）"],
   cls="small", align=["l", "r", "r", "r", "r", "r", "r"],
   caption="表 5-2  SKEW 分层（基准 12M +10.49%）") + """

<p>SKEW 的区分度很弱：12M 收益在 8.20%~12.34% 之间摆动，没有单调性，胜率也是 67%~86% 来回跳。
<b>结论：SKEW 不适合单独判断买卖点</b>，它的用途是「判断买保护划不划算」，而不是「预测涨跌」。</p>

<p>不过把它跟 VIX 组合起来，会得到一个有意思的组合维度：</p>
""" + table([
    ["VIX 分位 &lt;50% 且 SKEW 分位 &lt;50%", "651", "+0.09%", "59.1%", "+4.73%", "72.9%", "+1.11"],
    ["VIX 分位 &lt;50% 且 SKEW 分位 &gt;75%", "2,055", "+0.51%", "65.4%", "+9.60%", "88.5%", "+1.24"],
    ["VIX 分位 &gt;75% 且 SKEW 分位 &gt;75%", "483", "+0.78%", "65.1%", "+13.68%", "79.1%", "−2.48"],
], ["组合", "天数", "1M 收益", "1M 胜率", "12M 收益", "12M 胜率", "未来 21 日 VIX 变化"],
   cls="small", align=["l", "r", "r", "r", "r", "r", "r"],
   caption="表 5-3  VIX 分位 × SKEW 分位的组合") + """

<div class="note ok"><b>「VIX 低但 SKEW 高」是明显的有利组合</b>：2,055 天，12 个月 <b>+9.60%、胜率 88.5%</b>，
显著好于「VIX 低且 SKEW 也低」的 +4.73% / 72.9%。含义是：<b>市场整体波动低、但尾部保护却在涨价，
说明有人在偷偷买保险——这反而是好事</b>。反过来，VIX 低且 SKEW 也低（没人觉得会有事、也没人买保护），
才是真正危险的组合。</div>

<p>这个发现的价值在于它给了「VIX 低该怎么处理」一个更细的答案。
原报告的结论是「VIX&lt;13 后一年 +12.00%，不用减仓」；现在可以更精确地说：
<b>VIX 低不是减仓的理由，但「VIX 低 + SKEW 低 + VVIX 低」三者同时出现，是</b>。</p>
</div></section>
"""

# ============================ 六、三源比对 ============================
c6 = """
<section id="c6"><div class="wrap">
<h2>六、三期比对的可靠性</h2>
<p>新增的数据源能不能信，要用已知可靠的数据去对。我们用 2026-11-09 这一天的收盘做了三方核对：</p>
""" + table([
    [esc(r["指标"]), f2(r["CBOE官方"], 2) if r["CBOE官方"] is not None else "—",
     f2(r["TradingView"], 2) if r["TradingView"] is not None else "—",
     f2(r["差值"], 4) if r["差值"] is not None else "—",
     "一致" if (r["差值"] is not None and abs(r["差值"]) < 1e-9) else ("TradingView 无此符号" if r["TradingView"] is None else "有差异")]
    for r in D["vol_three_source"]
], ["指标", "CBOE 官方", "TradingView", "差值", "判定"], cls="small",
   align=["l", "r", "r", "r", "l"], caption="表 6-1  CBOE 官方与 TradingView 的当期读数比对") + """

<p>VIX 与 VXN 的差值都是 <b>0.0000</b>，完全一致。其余六个指标 TradingView 没有覆盖，
只能用 CBOE 与 Yahoo 双源比（这个在原报告 2.2 节做过，9,279 个交易日中位绝对差 0.0000）。
所以：<b>当期读数可信，历史序列以 CBOE 官方为准</b>。</p>

<p>还有一层冗余校验：CBOE 的 CSV 文件末尾与 Yahoo 的最近 5 天数据逐日对齐，
VIX 三天（11-05 / 11-06 / 11-09）分别是 28.18 / 25.64 / 19.92，两源一致。
<b>说明 11-06 到 11-09 的剧烈变化是真实行情，不是数据错误。</b></p>
</div></section>
"""

# ============================ 七、数据更新 ============================
c7 = """
<section id="c7"><div class="wrap">
<h2>七、数据已更新到 2026-11-09</h2>
<p>做尽调的过程中发现市场已经多了一个交易日。原报告的基准日是 11-06，现在补到 11-09。
<b>这两天发生了什么，很值得记录</b>：</p>
""" + table([
    [esc(r["项目"]), f2(r["2026-11-09"]), f2(r["2026-11-06"]) if r["2026-11-06"] is not None else "—",
     esc(r["单位"]), esc(r["说明"]) if r["说明"] and r["说明"] != "nan" else "—"]
    for r in D["vix_now_20261109"]
], ["项目", "2026-11-09", "2026-11-06", "单位", "说明"], cls="small",
   align=["l", "r", "r", "c", "l"], caption="表 7-1  两个交易日的读数对照") + """

<div class="note warn"><b>两个交易日的剧变：</b>
<ul>
<li><b>SPX 7376.86 → 7549.94（+2.35%）</b>，距 52 周高点从 −5.65% 收窄到 −3.44%，重新站上 200 日线 3.03%。</li>
<li><b>VIX 25.64 → 19.92（−22.3%）</b>，10 年分位从 86.7% 掉到 68.2%，从「警觉区」回到「常态区」。</li>
<li><b>期限结构从倒挂 +4.23% 翻成 contango −4.46%</b>——两天内完全修复，这是很少见的速度。</li>
<li><b>VIX9D 27.18 → 19.88</b>，短端跌得最狠，说明这波冲击确实是「眼前事」，没有演变成中期担忧。</li>
<li><b>VVIX 121.94 → 98.43（−19.3%）</b>，按第五章的规律，VVIX 从 120 以上回落到 100 以下，
短期买点已经过去了。</li>
<li><b>SKEW 153.55 → 150.34</b>，尾部定价小幅回落，仍处高位。</li>
</ul></div>

<p>按原报告的规则手册重新套一遍：</p>
""" + table([
    ["买点① 极端恐慌", "VIX≥40 或分位≥95% 或 VIX&gt;20MA×1.5", "未触发（VIX 19.92，分位 68.2%，/20MA=1.04）"],
    ["买点② 恐慌见顶确认", "自 63 日高点回落≥40% 且仍&gt;25", "未触发（自高点 28.18 回落 29.3%，但 VIX 已 &lt;25）"],
    ["买点③ 期限倒挂", "VIX/VIX3M−1 &gt; +10%", "未触发（−4.46%，已回归正常 contango）"],
    ["卖点① 温和警觉+趋势坏", "VIX 20-30 且跌破 200 日线", "未触发（VIX 19.92 已跌破 20；SPX 在年线上方 3.03%）"],
    ["卖点② 深度 contango", "VIX/VIX3M−1 &lt; −20%", "未触发（−4.46%，未达 −20%）"],
    ["仓位刻度", "VIX<13→95%；13-20→80%；20-25→45%…", "<b>VIX 19.92 落在 13-20 档 → 建议 80%</b>"],
], ["规则", "条件", "2026-11-09 判定"], cls="small", align=["l", "l", "l"],
   caption="表 7-2  用规则手册复核最新读数") + """

<p>与 11-06 相比，判断其实<b>没变</b>——两天前 VIX 25.64 落在 25-30 档建议 80%，
今天 19.92 落在 13-20 档也建议 80%。但背后的状态完全不同：
<b>两天前是「恐慌初期、期限倒挂、估值极贵」的三重压力，今天是「常态、正常 contango、估值仍贵」。</b>
风险从「急」变成了「慢」，仓位不用动，但警戒级别可以降一级。</p>
</div></section>
"""

# ============================ 八、局限 ============================
c8 = """
<section id="c8"><div class="wrap">
<h2>八、局限与未完成的部分</h2>

<h3>数据本身的天花板</h3>
<ul>
<li><b>期限结构的历史太短。</b>VIX9D 从 2011、VIX6M 从 2008、VIX3M 从 2009 才有。
第四章的所有结论样本起点是 2011-01，只有 3,986 个交易日、15 年，
<b>没有覆盖 2008 金融危机</b>。这是数据决定的，不是选择。</li>
<li><b>CFTC 持仓只有 20 年、周频、3 天滞后。</b>Legacy 1,120 周、TFF 1,024 周，独立事件更少。
第二章的「52 周 t 值」看着有 3.72，但那是<b>重叠样本</b>，有效自由度远低于名义周数。</li>
<li><b>VVIX 只有 2006 年以后</b>（5,144 天），且 2006 年前几个月数据有异常（首个值 71.73 次日跳到 15.71），
用法上以分位而非绝对值更稳妥。</li>
<li><b>vixcentral 的期货曲线无法批量回溯。</b>只能看当期，或手工查单日。</li>
</ul>

<h3>方法上的限制</h3>
<ul>
<li><b>所有新指标都是样本内描述。</b>VVIX&gt;130、SKEW 组合、四条斜率，都是先看到数据再总结规律，
存在数据窥探（data snooping）风险。真正的检验需要样本外，而样本长度不够切。</li>
<li><b>没有计入交易成本与展期损益。</b>第二章若真按 COT 信号做多空，还要考虑期货展期成本，
那个成本在 contango 结构下对空头是有利的（正是 carry 的来源），但对结论方向影响不大。</li>
<li><b>三源比对只在当期做过。</b>TradingView 没有历史，所以「VIX 与 TradingView 一致」只能证明今天一致，
不能证明历史上也一致。历史序列的可信度仍依赖 CBOE 与 Yahoo 的双源比对。</li>
<li><b>2026-11-09 只有一天数据。</b>表 7-1 的对照是「单点 vs 单点」，不能当作趋势。</li>
</ul>

<h3>没做成的事</h3>
<ul>
<li><b>investing.com 的 VIX 历史。</b>接口全部 500，没有绕过的办法（试过 8 个 instrumentId、5 种 period）。</li>
<li><b>TradingView 的历史 K 线。</b>symbol-search 403、datafeed 需登录，没有免费途径。</li>
<li><b>CFTC 的 Combined（期货+期权）口径。</b>对应的 4 个数据集都是 403 不可查询视图，
只有 Futures Only 能用。这对 VIX 影响不大（VIX 期权持仓另有来源），但仍是个缺口。</li>
</ul>
</div></section>
"""

# ============================ 附录 ============================
appendix = """
<section id="appendix"><div class="wrap">
<h2>附录：新增文件清单</h2>
""" + table([
    ["data/raw/cboe_vol/（23 个 CSV）", "CBOE 官方全部可下载波动率指数", "23 个文件，共约 4.5 MB"],
    ["data/raw/cftc_vix_cot.csv", "CFTC Legacy 口径 VIX 期货持仓", "1,120 行 × 133 列"],
    ["data/raw/cftc_vix_tff.csv", "CFTC TFF 口径 VIX 期货持仓", "1,024 行 × 90 列"],
    ["data/output/source_inventory.csv", "14 个端点的实测清单", "6 站点 × 14 端点"],
    ["data/output/cot_positions.csv", "Legacy 净持仓与多空比（周频）", "1,120 行"],
    ["data/output/cot_signal.csv", "Legacy 持仓分档与极端事件", "18 行"],
    ["data/output/cot_tff.csv", "TFF 四类交易者净头寸", "1,024 行 × 28 列"],
    ["data/output/cot_tff_signal.csv", "杠杆基金拥挤度分档", "21 行 × 22 列"],
    ["data/output/cot_vs_vix.csv", "持仓与 VIX 的对齐与滚动相关", "1,120 行"],
    ["data/output/cot_summary.md", "COT 分析摘要", "约 900 字"],
    ["data/output/vix_term_slopes.csv", "四条期限结构斜率分档", "16 行"],
    ["data/output/skew_vvix_stat.csv", "VVIX 与 SKEW 分层", "18 行"],
    ["data/output/vix_now_20261109.csv", "最新读数对照", "13 行"],
    ["data/output/vol_three_source.csv", "CBOE / TradingView 当期比对", "8 行"],
    ["data/output/vc_curve_test.csv", "vixcentral 抽样 38 日", "38 行"],
    ["data/output/vc_quality.csv", "vixcentral M1 与 VIX 现货抽检", "35 行"],
], ["文件", "内容", "规模"], align=["l", "l", "r"], cls="small",
   caption="表 A-1  本轮新增的数据与结果文件") + """

<p style="margin-top:18px"><b>新增脚本</b>（均在 <code>scripts/</code>）：
<code>probe_sources.py</code>（连通性）、<code>probe_sources2~6.py</code>（逐站深入）、
<code>fetch_cftc.py</code>、<code>fetch_cftc_tff.py</code>、<code>fetch_cboe_vol.py</code>、
<code>fetch_tv_snapshots.py</code>、<code>cot_analysis.py</code>、<code>cot_v2.py</code>、<code>cot_tff.py</code>、
<code>analyze_vix_term.py</code>、<code>probe_skew_vvix.py</code>、<code>source_inventory.py</code>、
<code>refresh_prices.py</code>、<code>update_now.py</code>、<code>make_src_figures.py</code>。</p>
</div></section>
"""

FOOT = """
<footer><div class="wrap">
<p><b>数据源</b>：CFTC Public Reporting Environment（Socrata，数据集 6dca-aqww 与 gpe5-46if）、
CBOE 官方 CDN（23 个波动率指数文件）、Yahoo Finance chart API、vixcentral.com、TradingView scanner、investing.com。</p>
<p><b>口径说明</b>：COT 为周频、周二报告、周五公布，信号延后 3 个交易日；期限结构结论样本起点 2011-01；
所有分位为滚动窗口（日频 10 年 / COT 3 年）；当期比对日期 2026-11-09。</p>
<p><b>免责声明</b>：本文为数据源尽调与历史研究，不构成投资建议。样本内结论存在数据窥探风险，
CFTC 持仓结论未计交易成本与展期损益。</p>
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

BODY = cover + summary + c1 + c2 + c3 + c4 + c5 + c6 + c7 + c8 + appendix

NL = chr(10)
OUTHTML = NL.join([
    "<!DOCTYPE html>",
    '<html lang="zh-CN">',
    "<head>",
    '<meta charset="utf-8">',
    '<meta name="viewport" content="width=device-width,initial-scale=1">',
    "<title>波动率数据源尽调：CFTC、vixcentral、investing、TradingView 实测</title>",
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
