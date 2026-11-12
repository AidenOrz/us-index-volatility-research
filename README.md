# 美股指数与波动率研究

32 年美股回测、VIX 择时体系，以及一个每天打开就能一屏读完的波动率看盘应用。

## 交付物

| 文件 | 内容 |
|---|---|
| [美股主要指数系统性回测与对比分析.html](output/美股主要指数系统性回测与对比分析.html) | 六大指数 1994–2026 全口径对比，10 章 31 表 12 图 |
| [美股主要指数系统性回测与对比分析.docx](output/美股主要指数系统性回测与对比分析.docx) | 同一份报告的 Word 版，22 页 |
| [VIX类指数买卖点判断专题.html](output/VIX类指数买卖点判断专题.html) | VIX 择时：U 型曲线、事件检验、策略回测 |
| [波动率数据源尽调与新增指标.html](output/波动率数据源尽调与新增指标.html) | 四个站点实测 + COT 持仓 + 期限结构四斜率 |
| [美股主要指数回测数据册.xlsx](output/美股主要指数回测数据册.xlsx) | 59 个工作表的完整数据 |
| 波动率看盘 Windows 包 | Flutter 桌面应用，按需自行构建（见下） |

## 快速上手

### 运行应用

Windows 包不入库（其中 20 MB 是 Flutter SDK 自带运行库，可完全重建），需要本地构建：

```powershell
cd flutter_app
flutter pub get
flutter build windows --release
# 产物在 build\windows\x64\runner\Release\vol_dashboard.exe
```

启动会自动联网补当日数据，断网则显示打包快照并弹窗提示。

改应用代码见 [flutter_app/README.md](flutter_app/README.md)。

### 刷新数据

```powershell
$py = "C:\Users\Lenovo\.dsh\dsh-runtimes\dsh-primary-runtime\dependencies\python\python.exe"

# 只补数据 + 重算指标
& $py scripts\refresh_dashboard.py

# 补完顺便重建 app
& $py scripts\refresh_dashboard.py --build
```

刷新脚本做三件事：**检测缺口 → 多源补齐 → 交叉校验**。

### 重新生成报告

```powershell
& $py scripts\metrics.py        # 算指标
& $py scripts\build_html.py     # 出 HTML
& $py scripts\build_report.py   # 出 DOCX
```

## 数据从哪来

| 源 | 内容 | 访问方式 |
|---|---|---|
| CBOE CDN | 23 个波动率指数日线 | **本机可直连**，但无 CORS，浏览器拿不到 |
| CFTC Socrata | VIX 期货持仓（Legacy + TFF） | 带 CORS，浏览器可用 |
| 东方财富 | 六大指数日线 | 带 CORS；命名有坑，见 MEMORY.md |
| Yahoo Finance | 指数回补 | 需代理 7897 |

## 核心结论速查

- **VIX 与未来收益是 U 型**：20–25 档最差（12M +4.38%/胜率 64.4%），>40 档最好（+32.95%/96.2%）
- **期限结构越陡，未来一年越差**：中端斜率 VIX3M/VIX 分位 0-10% → 12M +18.94%，90-100% → +8.38%
- **VVIX 低才是该担心的**：VVIX<80 时 12M 仅 +3.71%，是所有指标里最差的
- **COT 空头拥挤不是择时信号**：控制当期 VIX 后 t 值仅 0.15

详细推导见各 HTML 报告。

## 环境

- Python 3.12（pandas / numpy / matplotlib / openpyxl / python-docx，**无 scipy、无 requests**）
- Flutter 3.47.9（装在 `E:\flutter_dl\sdk\flutter`）
- 网络代理常用端口 **7897**

## 许可

本项目采用 [GNU General Public License v3.0](LICENSE)（GPL-3.0）。

你可以自由使用、修改和分发本项目，但衍生作品必须以相同许可开源。
若需要不同的授权条款，请联系作者。
