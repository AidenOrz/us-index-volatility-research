# -*- coding: utf-8 -*-
"""外部数据源尽调清单：逐站点实测可获取性、覆盖范围、限制。
产出 data/output/source_inventory.csv
"""
import os
import pandas as pd

OUT = r"E:\workspace\new\data\output"

ROWS = [
    # 站点, 端点, 可获取?, 数据内容, 覆盖范围, 频率, 滞后, 本轮是否采纳, 结论
    ("CBOE 官方 CDN", "cdn.cboe.com/api/global/us_indices/daily_prices/{T}_History.csv",
     "是", "23 个波动率指数完整 OHLC", "VIX 1990-01-02 起；其余 2004~2011 起", "日频", "T+0（收盘后）",
     "采纳（主源）", "最干净的历史源，直接 CSV，无频率限制；已下载 23 个文件"),

    ("CBOE 官方 CDN", "…/daily_prices/index.json",
     "否 403", "指数清单", "—", "—", "—", "未采纳", "目录文件被禁，需按代码逐个猜文件名（已验证有效）"),

    ("Yahoo Finance", "query1.finance.yahoo.com/v8/finance/chart/^VIX",
     "是（需代理 7897）", "OHLCV 日线", "VIX 1990 起；VIX3M 2006 起；VVIX 2006 起；SKEW 1990 起",
     "日频", "T+0", "采纳（交叉验证）", "直连 403，走 127.0.0.1:7897 代理可用"),

    ("CFTC（Socrata 公开报表）", "publicreporting.cftc.gov/resource/6dca-aqww.json（Legacy 期货）",
     "是（需代理）", "VIX 期货 COT 持仓：总持仓、非商业多空、商业多空、非报告、集中度、参与者家数",
     "2004-07-27 ~ 2026-11-03，1,120 期", "周频（每周二）", "3 天（周五 15:30 ET 公布）",
     "采纳（新数据）", "本轮新增。33 列有效，可算净持仓/多空比/空头拥挤度"),

    ("CFTC（Socrata 公开报表）", "publicreporting.cftc.gov/resource/gpe5-46if.json（TFF 期货）",
     "是（需代理）", "VIX 期货 TFF 持仓：Dealer / Asset Manager / Leveraged Funds / Other Reportables",
     "2004-07-27 ~ 2026-11-03，1,024 期", "周频（每周二）", "3 天",
     "采纳（新数据，最有价值）", "四类交易者分离，可识别「杠杆基金做空波动率拥挤度」"),

    ("CFTC 官网", "cftc.gov/files/dea/history/deacot2026.zip",
     "是（直连）", "年度 COT 压缩包（全品种）", "1993 起（按年分文件）", "周频", "3 天",
     "备选", "全量但需解压与筛选，Socrata API 更直接；作为冗余备份"),

    ("vixcentral.com", "vixcentral.com/ajax_update",
     "是（直连）", "VIX 期货当期完整期限结构（8 个到期月 + 买卖价/结算价）", "仅当期", "实时（60 秒刷新）",
     "T+0", "采纳（当期快照）", "返回 15 行 JSON 数组，可算 M1/M2 斜率与 contango"),

    ("vixcentral.com", "vixcentral.com/ajax_historical?n1=YYYY-MM-DD",
     "部分", "指定历史交易日的 VIX 期货完整期限结构", "抽样测试：2005 起有效，但约 30% 日期返回 error",
     "按日查询", "—", "有限采纳", "无批量接口，逐日抓取成本高；2004 年及部分日期缺数据"),

    ("vixcentral.com", "vixcentral.com/ajax_get_contango_data",
     "否", "contango 图数据", "—", "—", "—", "未采纳", "该路径返回整页 HTML，是页面路由而非数据接口"),

    ("investing.com", "www.investing.com/indices/volatility-s-p-500",
     "是（需代理）", "VIX 页面（HTML）", "—", "—", "—", "未采纳", "页面可访问，instrumentId=44336"),

    ("investing.com", "api.investing.com/api/financialdata/{id}/historical/chart/",
     "部分", "历史 K 线 JSON", "SPX(id=8839) 可用；VIX(id=44336) 全部 period 返回 500",
     "日/周/月", "—", "未采纳", "SPX 可用但已有更好源；VIX 历史接口对指数类不开放"),

    ("TradingView", "scanner.tradingview.com/america/scan（POST）",
     "是（需代理）", "当期报价 + RSI + 波动率 + 技术评分", "仅 CBOE:VIX 与 CBOE:VXN 可查",
     "实时（延迟 900 秒）", "15 分钟", "采纳（第三方当期校验）",
     "VIX/VXN 与 CBOE 官方当期值完全一致（差值 0.0000）；RVX/VIX3M/VVIX/SKEW 全部 404"),

    ("TradingView", "symbol-search / data.tradingview.com",
     "否 403", "符号搜索、历史 K 线", "—", "—", "—", "未采纳", "符号搜索 403，datafeed 需登录 token"),

    ("纳斯达克官方", "api.nasdaq.com/api/quote/VIX/info?assetclass=index",
     "返回 400", "VIX 报价", "—", "—", "—", "未采纳", "该 assetclass 不支持指数代码，仅覆盖股票/ETF"),
]

d = pd.DataFrame(ROWS, columns=["站点", "端点", "可获取", "数据内容", "覆盖范围", "频率", "滞后", "本轮处理", "结论"])
d.to_csv(os.path.join(OUT, "source_inventory.csv"), index=False, encoding="utf-8-sig")
print(d[["站点", "端点", "可获取", "覆盖范围", "本轮处理"]].to_string(index=False))
print("\n saved source_inventory.csv", len(d), "行")
