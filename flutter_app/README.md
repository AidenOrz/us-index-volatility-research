# 波动率看盘（Flutter）

一屏读完的每日波动率面板。数据来自本项目已有的 32 年回测结论，
把「VIX 高低 → 未来一年收益」「期限结构斜率」「VVIX 二阶信号」
「COT 持仓」压缩进一个不用滚动就能看完的界面。

## 它回答什么

打开就能看到四件事：

1. **现在该拿多少仓位** —— 顶部仪表盘直接给出百分比，由 VIX 分档表查得
2. **六条买卖点哪条触发了** —— 每条都写明距触发还差多少
3. **今天有什么异常** —— 按历史统计影响排序，最多四条
4. **八个波动率指数各自在什么位置** —— 数值 + 10 年分位 + 近 120 日走势

## 目录

```
flutter_app/
├── assets/
│   ├── dashboard.json      # 唯一数据源，由 scripts/build_dashboard_json.py 生成
│   └── fonts/              # 4 个子集化字体，共约 400 KB
├── lib/
│   ├── main.dart           # 界面：7 个面板 + 响应式布局
│   ├── model.dart          # dashboard.json 的类型化解析
│   ├── theme.dart          # 配色与数字格式化
│   └── graphics.dart       # 走势线 / 期限曲线 / 仓位表盘（全部 CustomPaint）
└── test/widget_test.dart   # 数据完整性测试
```

## 数据自动更新

应用**每次启动会自动尝试拉取最新交易日数据**，无需手动操作。顶部状态徽标显示当前状态：

| 徽标 | 含义 |
|---|---|
| 🟢 最新 | 数据就是最近一个交易日 |
| 🟡 滞后 N 天 | 有几天没补上（周末/假期正常） |
| 🔴 更新失败 | 所有数据源都不可达，显示的是打包快照 |

失败时会**弹窗**列出每个数据源的具体原因，并提供「重试」按钮。点右上角「刷新」可手动重试。

### 各平台能拿到什么

这是实测结果，不是设计取舍：

| 数据源 | 桌面端 | 浏览器端 | 原因 |
|---|---|---|---|
| **CBOE**（VIX/VIX3M/VIX9D/VIX6M/VVIX/SKEW/VXN/RVX） | ✅ | ❌ | 响应头**没有 CORS**，浏览器一律拦截 |
| **东方财富**（SPX/IXIC/NDX/DJI/SOX） | ✅ | ✅ | 有 `Access-Control-Allow-Origin: *` |
| **CFTC**（持仓） | ✅ | ✅ | Socrata 带 CORS |
| 腾讯 VIX | ❌ | ❌ | 数据停在 2026-09-15，已过期 |
| Yahoo | 仅脚本 | ❌ | 403 拦截 Dart/浏览器 UA |

**结论：桌面版能补齐全部波动率数据；Web 版只能补指数，波动率沿用打包快照。**

### 数据校验

补齐的数据在合并前要过三道闸，任何一道不过就整段丢弃：

1. **日期严格递增** —— 防止乱序
2. **数值范围** —— 必须是正数且在合理量级
3. **重叠段交叉校验** —— 与本地已有数据重叠部分的中位相对偏差必须 < 2%

第 3 条是关键：东财、Yahoo、CBOE 各有自己的复权口径，如果某天换了标的数据源，重叠段的偏差会立刻暴露。实测东财与本地 SPX/DJI/IXIC/NDX 的中位偏差都是 **0.0000%**，可以直接混用。

## 每天怎么用

```powershell
# 1. 刷新数据（抓 CBOE 23 个指数 + CFTC 持仓 + 指数收盘价）
python scripts\refresh_dashboard.py

# 2. 刷新后顺便重建应用
python scripts\refresh_dashboard.py --build
```

刷新脚本做三件事：**检测缺口 → 多源补齐 → 交叉校验**，然后重新生成
`flutter_app/assets/dashboard.json`。

应用启动时先读这个打包快照（保证立刻有画面），再后台联网补当日数据。
**完全断网也能打开**，只是顶部会显示红色「更新失败」。

## 构建与运行

```powershell
$env:Path = "E:\flutter_dl\sdk\flutter\bin;" + $env:Path
$env:PUB_HOSTED_URL = "https://pub.flutter-io.cn"
$env:FLUTTER_STORAGE_BASE_URL = "https://storage.flutter-io.cn"

cd flutter_app
flutter run -d windows          # 桌面调试
flutter run -d edge             # 浏览器调试
flutter build web --release     # 产物 build\web
flutter build windows --release # 产物 build\windows\x64\runner\Release\vol_dashboard.exe
flutter test                    # 数据完整性校验
```

> 国内网络必须设 `PUB_HOSTED_URL` 与 `FLUTTER_STORAGE_BASE_URL` 两个镜像变量，
> 否则 `pub get` 会卡在 github.com 上。

## 界面结构

宽屏（≥1120px）三栏两行，一屏不滚动：

```
┌─ 标题 / 数据日期 ────────────────────────────────────┐
├─ 六大指数收盘条 ─────────────────────────────────────┤
├─ 结论条：VIX 大数 + 分位 + 档位 + 斜率 + 仓位表盘 ────┤
├─ 波动率族(8)  │  期限结构(曲线+4斜率)  │  买卖点(6)  ─┤
└─ VIX 分档(6档)│  VVIX·SKEW(5档)        │  今日提醒(4) ┘
```

窄屏（<1120px）自动堆叠为单列，卡片定高，整页可滚动。

## 关键设计决定

**为什么用 log 时间轴画期限曲线** —— 9 / 30 / 91 / 182 天如果等距排列，
9 天到 30 天这段（历史上最敏感）会被压成一个点。对数轴让短端展开。

**为什么建议仓位是查表而不是算出来** —— 仓位来自 VIX 分档的实测胜率与盈亏比，
不是拟合函数。改表就能改结论，可追溯。

**为什么 VVIX 比 VIX 更值得看** —— VIX 低只说明当下没事；VVIX 低说明
市场连「会不会出事」都不讨论了。实测 VVIX<80 时未来 12 个月仅 +3.71%，
是全部指标里最差的一组。

**颜色** —— 涨红跌绿沿用 A 股习惯；分位数用绿→黄→红表示警戒度；
每个色块都同时给出数字，不依赖颜色单独传达信息。