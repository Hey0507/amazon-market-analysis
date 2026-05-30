# 🎙️ Amazon 便携领夹无线麦克风市场深度 BI 分析系统 (V5.2 专业纯净版)

> **Amazon Wireless Microphone Market Business Intelligence Analysis System (Version 5.2 - Pure Wireless-Only Edition)**

本系统是一套专为 **便携领夹式/声卡类数码无线麦克风系统**（以 Hollyland Lark、DJI Mic、RØDE Wireless、Shure MoveMic 为代表的 Vlogger/创作者级市场）打造的商业智能（BI）数据化运营与大盘深度分析决策系统。

系统贯穿了 **Sellersprite CLI 数据自动化拉取 -> 向量化清洗与税率汇率调整 (ETL) -> 统计引擎与预测模型 -> openpyxl 专家级商务报表生成 -> Streamlit 交互式 BI 大屏** 的完整商业闭环。

---

## 📅 数据覆盖与统计周期

* **全量数据周期**：**2024-04 ~ 2026-04 (共 25 个月历史数据)**，用以单站点趋势的深度挖掘、大盘季节性波动及生命周期分析。
* **多站点对齐周期（方案B对齐）**：**2024-12 ~ 2026-04 (共 17 个月)**，为保障英国、德国、日本、美国等不同国家市场横向对比的绝对数学公平，多国对比分析自动切换至该共有时间线，杜绝时间线长度不一导致的销量偏置。

---

## 🌟 核心技术亮点与系统架构

### 1. 高保真 O(N) 向量化清洗引擎 (`final_processor.py`)
* **税前净值向量化重构**：规避逐行缓慢循环，利用 Pandas 向量化映射（`EXCHANGE_RATES` 与 `TAX_RATES`），一键剥离欧洲（如英国 20%、德国 19%）与日本（10%）含税前台售价，并统一换算为税前 USD 销售额，确保跨国对比指标的真实有效性。
* **代表性子变体去重逻辑**：Amazon 同一 Listing 下的多变体经常导致销量重复计算。系统自动按月度销量（Volume）降序排列并去重，以销售最旺盛的子变体作为 Canonical 节点，规避了直接合并或随意抽取导致的平均价格通胀。
* **V5.2 专业纯净版分类过滤器**：通过精准的文本边界与排除正则，**彻底剥离了 standalone 有线领夹麦配件（如 Rode Lavalier GO/II）、塑料 Interview GO 手柄适配器、舞台 UHF 模拟无线系统（如 Shure BLX）以及 PartyBox 麦克风**。净化后共剔除 245 条噪音记录，JBL 占比归零，Shure 纯净化为 MoveMic，提供真正垂直、纯净的高清领夹无线麦市场洞察。

### 2. 商务大师级 Excel 导出引擎 (`export_excel.py`)
* **行写入性能爆发式跃升**：彻底移除旧版本中 $O(N^2)$ 延迟的查表迭代，通过 `enumerate()` 增量偏移写入，将 **9 个多维数据分析 Sheets** 的生成时间缩短至 **1.8 秒**。
* **高级视觉呈现规范**：
  * 强制全局关闭 Excel 网格线 (`ws.sheet_view.showGridLines = False`)，建立以板岩灰、卡其白交替行条纹为主的视觉体系。
  * 全部指标进行 explicit 格式化（如 `$#,##0.00`、`0.0%`、`0.00x`）。
  * 在所有 9 个 Sheet 的 Title 标题行上，均**动态/显式标注了对应的统计周期**（如单站点标记 `2024-04 ~ 2026-04`，对齐站点标记 `对齐 2024-12 ~ 2026-04`），防止管理决策层混淆。

### 3. 多维分析与置信度预测引擎 (`analytics_engine.py`)
* **趋势预测外推模型**：采用基于最小二乘法的线性趋势外推，并计算残差标准误，在输出中提供 **95% 置信区间（CI）上限与下限**，且包含非负下限护栏（防止预测出负值销量），为供应链备货提供科学依据。
* **多维统计矩阵**：提供品牌在各价格段的市场占比、Listing Quality Score (LQS) Listing 质量优化排行、以及卖家来源地（CN 卖家 vs Local 本地卖家）份额趋势。

### 4. 极致响应式 Streamlit BI 大屏 (`app.py`)
* **缓存加速**：通过 `@st.cache_data(ttl=300)` 缓存文件加载与解析，保障高频筛选站点、品牌、价格段时界面 sub-second 级刷新。
* **极简美感图表（防图例疲劳）**：对品牌份额饼图、价格段堆叠条形图，全面采用直接折行标签显示（如 `Brand<br>Share%`）并隐藏多余侧边图例（`showlegend=False`），视觉质感高端，直观呈现头部品牌割据状态。

---

## 📁 项目目录结构

```
Market_Analysis/
├── app.py                      # Streamlit 交互式 BI 大屏主程序
├── analytics_engine.py         # 大盘多维数据分析与趋势预测引擎
├── export_excel.py             # 专家级 Excel 导出引擎
├── final_processor.py          # O(N) 变体去重、税前价格及分类清洗 ETL 核心
├── chart_components.py         # 高级 Plotly 绘图组件库
├── style.css                   # Streamlit 配套的透明磨砂质感 CSS 样式表
├── requirements.txt            # 项目 Python 依赖项声明
├── venv/                       # Python 虚拟环境 (已配置)
│
├── data/                       # 按站点归类的 Sellersprite 年月份清洗后数据
│   ├── US/                     # 美国市场 (25 个月)
│   ├── JP/                     # 日本市场 (24 个月)
│   ├── UK/                     # 英国市场 (25 个月)
│   └── DE/                     # 德国市场 (25 个月)
│
├── raw_data/                   # Sellersprite 原始采集大文件暂存区
│
├── collect_de_fulldata.py      # 德国历史全量数据自动化拉取 CLI 工具
├── collect_uk_fulldata.py      # 英国历史全量数据自动化拉取 CLI 工具
├── collect_jp_fulldata.py      # 日本历史全量数据自动化拉取 CLI 工具
├── collect_202604_multisite.py # 202604 多站点最新数据全量同步器
│
├── walkthrough.md              # V5.2 最新高保真站点指标及过滤算法说明
├── handover_plan.md            # 项目后续升级与交接方案
└── README.md                   # 本系统说明主文档
```

---

## 🚀 快速启动指南

### 1. 环境准备
确保您的计算机上已安装 **Python 3.8+**。在项目根目录下激活预配置的虚拟环境并安装依赖：

```bash
# 激活虚拟环境 (Windows PowerShell)
.\venv\Scripts\Activate.ps1

# 安装依赖项
pip install -r requirements.txt
```

### 2. 运行数据清洗与大盘聚合 (ETL Pipeline)
如果您新增了 Sellersprite CLI 拉取的数据，或者修改了 `is_unrelated` 的清洗过滤条件，请直接运行 ETL 主程序：

```bash
python final_processor.py
```
这会根据变体去重、税率除外、USD 换算和 V5.2 领夹麦纯净过滤器重新洗牌数据，并在根目录下输出：
* `processed_market_data.pkl` (Pandas 数据缓存，大屏与 Excel 引擎的单一数据源)
* `market_analysis_24m.xlsx` (Excel 数据底表)

### 3. 生成企业级 Excel 商业报告
直接运行 Excel 导出脚本，可在根目录下立即编译生成一份大师级商务分析报表：

```bash
python export_excel.py
```
* **输出文件**：`Amazon市场分析报告_YYYYMMDD.xlsx` (包含 KPI 趋势、品牌份额、价位段结构、Hollyland专项、原始明细、站点概览、Top5站点趋势、竞品基准、LQS与卖家分析共 9 大主题 Sheets，附带折线图与柱状图)。

### 4. 启动交互式 BI 洞察大屏
使用下述命令启动本地 Streamlit Web 服务器：

```bash
streamlit run app.py
```
* **访问入口**：在浏览器中打开 `http://localhost:8501`。
* 您可以通过侧边栏的高级筛选器，跨站点、跨品牌、跨价格段与卖家归属地，秒级透视高清无线领夹麦的竞争格局！

---

## 🛠️ 版本演进历史 (V5.2 认证)

* **V5.2 (当前版本 - 领夹麦专业纯净版)**：新增 Section 8 & 9 分类纯净规则，彻底过滤 standalone wired lavalier 配件、塑料 Interview GO 手柄、BLX/SLXD 舞台 UHF 模拟系统及 PartyBox vocal 话筒。JBL 净化至 0 记录，Shure 纯净化为 MoveMic。Excel 各 sheet 显式标注统计时间跨度。
* **V5.1 (质量与卖家透视版)**：全渠道数据源合并。新增 **Listing 质量分 (LQS)** 优化排行榜，以及 **CN 卖家 vs 本地卖家** 销售额月度占比趋势分析。
* **V5.0 (方案B对齐版)**：针对不同站点时间线长短不一问题，全面实现**方案 B (多站点对齐周期 `2024-12 ~ 2026-04`)** 计算，确保跨国大盘份额对比绝对公平。
* **V4.0 (CLI 自动化采销版)**：打通 `sellersprite-cli` 本地接口，用 100% 真实拉取数据取代模拟备份，日本、英国、德国及美国全量入库。

---

**Status: Approved for Production Use (V5.2 Certified)**
