# AGENTS.md — 波动率看盘 Flutter 应用

## 这是什么

`flutter_app/` 是一个 Flutter 应用，把 `data/` 里 32 年回测的结论做成
每日可打开的一屏看板。**它不做计算**，所有统计量在构建 `dashboard.json`
时已经算好。

## 两条数据路径

应用有**两条**数据路径，改代码前必须分清：

1. **打包快照**（assets/dashboard.json）—— Python 脚本生成，保证离线可用
2. **运行时增量**（lib/live_data.dart + lib/recompute.dart）—— App 启动后联网补当日数据

运行时只做「补数据 + 重算」，不改变任何统计口径。
`recompute.dart` 必须与 `build_dashboard_json.py` 保持同一套算法，
否则界面会出现自相矛盾的数字。测试里的**恒等性用例**就是守这条底线：
无新数据时重算必须复现原值。

## 数据源能力（实测，不是假设）

| 源 | 桌面 | 浏览器 | 说明 |
|---|---|---|---|
| CBOE CDN | ✅ | ❌ | 无 CORS 头 |
| 东方财富 kline | ✅ | ✅ | 有 `ACAO:*` |
| CFTC Socrata | ⚠️ 403 | ✅ | Dart 的 TLS 指纹被拦，浏览器反而可以 |
| 腾讯 usVIX | ❌ | ❌ | 数据停在 2026-09-15 |

**浏览器端拿不到 VIX，这是 CORS 决定的，不要在 Dart 侧反复试。**
公共 CORS 代理（allorigins / corsproxy.io / codetabs 等 10 个）实测全部失效。

## 数据流（单向，不要反向改）

```
data/raw/cboe_vol/*.csv          CBOE 23 个波动率指数官方文件
data/raw/cftc_vix_tff.csv        CFTC 杠杆基金持仓
data/processed/prices_close.csv  六大指数收盘价
data/output/vix_ladder.csv       VIX 分档统计（来自已有回测）
        ↓  scripts/build_dashboard_json.py
flutter_app/assets/dashboard.json
        ↓  flutter build
应用
```

改指标口径要改 `build_dashboard_json.py`，不要改 Dart 侧的显示逻辑。

## 改动前必看

- **字体是子集化的**。新增中文文案后，必须重跑
  `python scripts\build_font_subsets.py`，否则新字会显示成豆腐块。
  该脚本扫描 `lib/*.dart` 和 `assets/dashboard.json` 收集字符。
- **改布局要验证三种宽度**：1600 / 1280 / 430。窄屏是单列堆叠。
- **每次改完跑 `flutter test`**，它会校验 json 结构与字段完整性。

## 已知坑

- `flutter doctor` 会报 github.com 超时 —— 不影响构建，只是版本检查。
- `flutter test` 里不能用 `rootBundle` 加载资源（会挂 10 分钟然后超时），
  测试里用 `File('assets/dashboard.json').readAsStringSync()` + `Dash.parse()`。
- Windows 版构建必须装 VS BuildTools 的 C++ 工作负载。
- `cdn.cboe.com` 本机可直连，但**响应头没有 CORS**，所以不能在浏览器里
  runtime 抓数据。这也是数据必须打包进应用的原因。
- **东财 `100.NDX` 是纳斯达克综指（IXIC）不是 NDX**，NDX 要用 `100.NDX100`。
  这个命名陷阱很容易搞错。
- 窗口标题必须写成 UTF-16 转义（`L"\u6CE2..."`），因为 MSVC 按 GBK 读 .cpp，
  写中文会触发 C4819 并且该警告被当作错误。
- `Win32Window::Size` 是**物理像素**，会被 DPI 缩放放大。150% 缩放下写 1440
  实际占 2160 像素，直接超出屏幕。要按 `GetDpiForWindow` 反算。
- 桌面端截图有时抓到旧帧（DWM 合成延迟），验证布局**用 Web 无头截图更可靠**。
- 验证失败弹窗用 `--dart-define=FORCE_OFFLINE=true` 构建，见 live_data.dart 的
  `forceOffline`。