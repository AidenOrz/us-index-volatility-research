# AGENTS.md — 项目入口

这是一个**美股主要指数与波动率研究**项目。四轮工作产出了：
回测分析报告、VIX 择时专题、数据源尽调、以及一个 Flutter 看盘应用。

## 从哪开始

| 我想… | 看这里 |
|---|---|
| 了解项目能做什么、怎么跑 | [README.md](README.md) |
| 接手继续做，知道做到哪了 | [HANDOFF.md](HANDOFF.md) |
| 查事实、约定、踩过的坑 | [MEMORY.md](MEMORY.md) |
| 改进 Flutter 应用 | [flutter_app/AGENTS.md](flutter_app/AGENTS.md) |

## 目录

```
data/
  raw/        原始数据（CBOE 23 个波动率文件、CFTC 持仓、各源指数 CSV）
  processed/  清洗后的价格与估值序列
  output/     分析产出的中间表（CSV/JSON）
scripts/      88 个 Python 脚本，见下方「脚本地图」
flutter_app/  Flutter 看盘应用（有独立 AGENTS.md）
output/       最终交付物（HTML/DOCX/XLSX/PNG/Windows 包）
```

## 脚本地图

88 个脚本不用全看，按用途分四类，每类只需记住入口：

**抓数据**
- `fetch_cboe_vol.py` — CBOE 23 个波动率指数
- `fetch_cftc.py` / `fetch_cftc_tff.py` — CFTC 持仓两套口径
- `refresh_prices.py` — 指数收盘价（走代理 7897）
- `probe_*.py` — 数据源探测，一次性，留档备查

**算指标**
- `metrics.py` `phases.py` `annual.py` — 主回测
- `timing_*.py` — 位置择时指标族（IC、分位、复合评分）
- `vix_*.py` — VIX 分层、U 型、事件、策略
- `cot_*.py` — COT 持仓分析
- `analyze_vix_term.py` — 期限结构斜率

**出交付物**
- `build_report.py` → DOCX
- `build_html.py` → 主分析 HTML
- `build_vix_html.py` → VIX 专题 HTML
- `build_src_html.py` → 数据源尽调 HTML
- `make_xlsx*.py` → Excel 数据册
- `make_*figures.py` → 图

**运维**
- `fill_gaps.py` — 增量补齐引擎（缺口检测 + 多源回退 + 交叉校验）
- `refresh_dashboard.py` — 一键刷新数据并重建看盘 app
- `build_dashboard_json.py` — 生成 app 的 dashboard.json
- `build_font_subsets.py` — 中文字体子集化

## 硬性约定

- **中文文档、中文提交信息**，提交前缀用 `feat:` / `fix:` / `docs:` / `chore:`
- 临时文件一律 `.tmp-` 前缀，任务结束清理干净
- Python 用 `C:\Users\Lenovo\.dsh\dsh-runtimes\dsh-primary-runtime\dependencies\python\python.exe`
- 改数据口径要同时改 `build_dashboard_json.py` 和 `flutter_app/lib/recompute.dart`
