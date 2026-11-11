# MEMORY.md — 长期知识

事实速查、约定、以及踩过的坑。改代码前先扫一遍。

## 环境事实

| 项 | 值 |
|---|---|
| Python | `C:\Users\Lenovo\.dsh\dsh-runtimes\dsh-primary-runtime\dependencies\python\python.exe` |
| Python 版本 | 3.12.14 |
| 已装库 | pandas 3.0.1 / numpy 2.3.5 / matplotlib 3.11.2 / openpyxl / python-docx / fontTools 4.68 |
| **未装** | scipy、requests、yfinance —— 用 urllib 替代 |
| Flutter | 3.47.9，`E:\flutter_dl\sdk\flutter\bin\flutter.bat` |
| Dart | 3.13.7，注意 `dart.exe` 在 `bin\cache\dart-sdk\bin\` 下，不在 `bin\` |
| 代理 | **7897**（实测可用）；7890/10808/10809 本机常关 |
| 屏幕 | 1707×1067 物理像素，**150% 缩放**（AppliedDPI=144） |

## 踩过的坑

### 数据源

- **东财 `100.NDX` 是纳斯达克综指（IXIC），不是 NDX**。NDX 用 `100.NDX100`。搞错会让两个数字刻度错位。
- **东财 SOX 只有 91 根**，RUT 没有对应 secid，别指望用东财补这两个。
- **CBOE 的 `NDX_History.csv` 与 `SPXPM_History.csv` 返回 403**，其他 21 个正常。
- **VVIX/SKEW/OVX/GVZ/VXHYG/VXTLT 是 2 列格式**（`DATE,CLOSE`），其余是 4 列，读列要 fallback 到最后一列。
- **腾讯 `usVIX` 数据停在 2026-09-15**，看着像能用，实际过期两个月，已排除。
- **CFTC Socrata 的 `$order` 含空格必须 quote**，否则 `URL can't contain control characters`。
- **CFTC 有 4 个 Combined 数据集返回 403**「non-tabular tables」，只有 Futures Only 可查。
- **CFTC 列名 `noncomm_postions_spread_all` 少个 i**，是官方拼写错误，按正确拼写取列会 KeyError。

### CORS（决定 Web 端能力边界）

实测结论，别再重复试：

| 源 | 浏览器 | 桌面 |
|---|---|---|
| CBOE CDN | ❌ 无 ACAO 头 | ✅ |
| 东方财富 kline | ✅ `ACAO:*` | ✅ |
| CFTC Socrata | ✅ `ACAO:*` | ❌ 403 |
| Yahoo | ❌ 403 | ❌ 403（需 Python 代理） |
| 腾讯 | ✅ 但数据过期 | ✅ 但数据过期 |

**10 个公共 CORS 代理全部失效**：allorigins / corsproxy.io / codetabs / corsproxy.org / thingproxy / whateverorigin / proxy.cors.sh / cors.workers.dev / isomorphic-git / crossorigin.me。

### Flutter

- **`flutter test` 里不能用 `rootBundle`**，会挂 10 分钟然后超时。用 `File('assets/dashboard.json').readAsStringSync()` + `Dash.parse()`。
- **window 标题必须写 UTF-16 转义** `L"\u6CE2..."`，因为 MSVC 按 GBK 读 .cpp，写中文触发 C4819 而该警告被当错误。
- **`Win32Window::Size` 是物理像素**，会被 DPI 放大。150% 缩放下写 1440 实际占 2160 像素，超出屏幕。要按 `GetDpiForWindow` 反算。
- **桌面端截图会抓到旧帧**（DWM 合成延迟），验证布局用 Web 无头截图更可靠。
- **pandas 3.0 移除了 `applymap`**，用 `.map`。
- **Windows 写 JSON 必须 `encoding="utf-8"`**，否则中文乱码。

### 工具链

- **`flutter doctor` 报 github.com 超时是正常的**，不影响构建。
- **国内必须设 `PUB_HOSTED_URL=https://pub.flutter-io.cn` 和 `FLUTTER_STORAGE_BASE_URL=https://storage.flutter-io.cn`**，否则 pub get 卡死。
- **`storage.flutter-io.cn` 比 googleapis 快 16 倍**（11.3 MB/s vs 706 KB/s）。
- **`run_code` 有 120 秒硬上限**，长任务用 `run_in_background` + `job_output`。

## 关键数字（截至 2026-11-10）

### 指数长期表现（1994-05-05 ~ 2026-11-06，价格口径）

| 指数 | 累计 | 年化 | 波动 | Sharpe | 最大回撤 |
|---|---|---|---|---|---|
| SOX | — | 14.40% | — | 0.481 | −87.15% |
| NDX | — | 14.03% | — | 0.531 | −82.90% |
| IXIC | — | 11.38% | — | 0.469 | −77.93% |
| SPX | 1534% | 8.97% | 18.59% | 0.426 | −56.78% |
| DJI | — | 8.43% | — | 0.410 | — |
| RUT | — | 7.61% | — | 0.331 | −59.89% |

### VIX U 型（最反直觉的发现）

| VIX 档 | 天数 | 12M 均值 | 12M 胜率 | 建议仓位 |
|---|---|---|---|---|
| <13 | 1365 | +12.00% | 89.6% | 95% |
| 13–20 | 3629 | +11.32% | 83.6% | 80% |
| **20–25** | 1677 | **+4.38%** | **64.4%** | **45%** |
| 25–30 | 807 | +6.70% | 68.7% | 80% |
| 30–40 | 497 | +17.46% | 83.0% | 95% |
| >40 | 208 | **+32.95%** | **96.2%** | 100% |

**20–25 是全表最差**，不是 30–40。中间地带最危险。

### 期限结构四斜率（2011 起，3986 日）

| 斜率 | 0-10% 分位 12M | 90-100% 分位 12M | 相关 |
|---|---|---|---|
| 短端 VIX/VIX9D | +16.63% | +8.54% | −0.1718 |
| 中端 VIX3M/VIX | +18.94% | +8.38% | −0.2494 |
| 长端 VIX6M/VIX3M | +18.76% | +11.54% | −0.2752 |
| 全曲线 VIX6M/VIX9D | +18.51% | +7.25% | −0.2474 |

**越陡未来越差**，与直觉相反。长端斜率相关系数绝对值最大。

### COT（别当成择时信号）

- 杠杆基金 82.9% 的周数净空，均值 −49,309 张
- 空头拥挤度 >90% 时 52 周 SPX **+14.71%/95.5%**，比基准还好
- **控制当期 VIX 后拥挤度 t 值仅 0.15**（VIX 自身 4.90）→ 超额来自 VIX 均值回归，不是持仓

## 约定

- 中文文档、中文提交信息
- 提交前缀：`feat:` / `fix:` / `docs:` / `chore:`
- 临时文件 `.tmp-` 前缀，用完删
- 报告里的百分比字符串拼接要转义 `%%`
- HTML 构建脚本用 `NL = chr(10)` 拼接，避免多行单引号字符串断开
