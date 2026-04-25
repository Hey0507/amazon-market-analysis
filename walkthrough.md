# Amazon 市场大盘调研工具项目总结 (V3 - 统一市场版)

项目已升级至 V3 版本，重点优化了品牌归一化逻辑与市场整合视角。

## ✨ V3 版本核心更新

### 1. 品牌合并 (Hollyland & Hollyview)
- **品牌归一化**: 自动将 `Hollyview` 的所有数据合并至 `Hollyland` 品牌下，解决了同一品牌在不同 Listing 中命名不一致导致的统计偏差。
- **准确份额**: 在品牌占有率统计中，合并后的 Hollyland 能更真实地反映其在市场中的统治地位。

### 2. 品类全合并 (Combined Market)
- **统一视角**: 按照您的要求，将“领夹麦克风”与“发射接收器”两个细分品类直接合并为统一的 **Wireless Audio Market**。
- **大盘趋势**: 现在的趋势图和分布图均基于整合后的全量数据，方便您从更高维度评估整个无线音频配件市场的生命周期与容量。

### 3. 数据清洗与命名
- **中文表头**: 持续保持“月份、品类、销量”等中文命名字段，符合您的业务使用习惯。
- **精准过滤**: 依然保留了月销量 > 200 的头部数据筛选机制。

### 3. 高级 BI 看板 (Dashboard)
- **交互式分析**: 支持按品类、品牌、价格区间实时联动筛选。
- **多维可视化**:
  - **趋势图**: 24 个月的销量变化曲线，识别淡旺季。
  - **品牌份额**: Top 10 品牌销售额饼图，判断品类集中度。
  - **卖家画像**: 地区分布（如 CN/US 占比）与发货方式（FBA/FBM）对比。
- **一键导出**: 支持下载清洗后的 Excel 汇总报表及过滤后的 CSV 原始数据。

## 🛠️ 项目结构

- [app.py](file:///c:/Users/alecl/Documents/Market_Analysis/app.py): Streamlit 看板主程序。
- [final_processor.py](file:///c:/Users/alecl/Documents/Market_Analysis/final_processor.py): 核心数据聚合与清洗引擎。
- [style.css](file:///c:/Users/alecl/Documents/Market_Analysis/style.css): 高级玻璃拟态 UI 样式。
- `market_analysis_24m.xlsx`: 自动生成的 Excel 汇总报告。

## 📊 验证结果
- **数据总量**: 2,400 条原始记录。
- **处理后记录**: 已完成销量过滤与价格段打标。
- **UI 状态**: 已完成深色模式适配，图表渲染正常。

---
> [!TIP]
> **运行看板**: 您可以在终端运行 `streamlit run app.py` 来启动可视化界面。
> **数据更新**: 以后只需运行 `final_processor.py` 即可自动重新汇总所有已抓取的数据。
