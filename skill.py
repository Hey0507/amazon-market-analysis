# Amazon 无线麦克风市场分析 Skill
# 适用于 Antigravity (OpenClaw) - 直接调用即可完成数据采集、处理、Excel 导出
#
# 使用方法：
#   在 OpenClaw 中告诉 AI："运行亚马逊市场分析"或"更新市场报告"
#   AI 会自动调用此 Skill 完成以下步骤：
#   1. 通过 Sellersprite MCP 采集最新月份数据
#   2. 更新 processed_market_data.pkl
#   3. 生成 Excel 报告

## 元信息 ##
SKILL_NAME = "amazon_market_analysis"
SKILL_VERSION = "3.0"
SKILL_DESCRIPTION = """
Amazon 无线麦克风市场月度分析 Skill。
功能：
  - 自动检测并补充缺失月份的市场数据（增量更新）
  - 品牌归一化（Hollyview → Hollyland）
  - 合并两个细分品类为统一市场视图
  - 输出格式化 Excel 报告（5张工作表）
  - 可选：启动本地 Streamlit 看板
触发关键词：
  - "更新市场数据"
  - "生成市场报告"
  - "运行亚马逊分析"
"""

## Skill 执行步骤（AI 应按顺序执行） ##
STEPS = [
    {
        "step": 1,
        "name": "检测缺失月份",
        "description": "读取 processed_market_data.pkl，找出过去24个月中哪些月份+品类的数据缺失",
        "tool": "python_script",
        "script": "skill_steps/step1_detect_missing.py"
    },
    {
        "step": 2,
        "name": "采集缺失数据",
        "description": "通过 Sellersprite MCP competitor_lookup 工具采集缺失月份数据",
        "tool": "mcp_sellersprite",
        "mcp_tool": "competitor_lookup",
        "params": {
            "marketplace": "US",
            "nodeIdPaths": ["11974761", "10677099011"],
            "variation": "Y",
            "size": 50
        }
    },
    {
        "step": 3,
        "name": "处理并更新数据",
        "description": "运行 final_processor.py 合并新数据、归一化品牌、生成 pkl",
        "tool": "python_script",
        "script": "final_processor.py"
    },
    {
        "step": 4,
        "name": "生成 Excel 报告",
        "description": "运行 export_excel.py 生成格式化多工作表报告",
        "tool": "python_script",
        "script": "export_excel.py"
    },
    {
        "step": 5,
        "name": "（可选）启动看板",
        "description": "启动 Streamlit 本地看板，用于交互式数据探索",
        "tool": "shell",
        "command": "streamlit run app.py",
        "optional": True
    }
]

## 关键配置 ##
CONFIG = {
    "marketplace": "US",
    "node_ids": {
        "领夹麦克风": "11974761",
        "发射接收器": "10677099011"
    },
    "lookback_months": 24,
    "top_n_products": 50,
    "min_monthly_sales": 200,        # 过滤低销量 ASIN
    "brand_aliases": {
        "Hollyview": "Hollyland",    # 品牌归一化规则
        "HollyView": "Hollyland",
        "HOLLYVIEW": "Hollyland"
    },
    "price_tiers": ["0-30", "30-50", "50-100", "100-150", "150+"],
    "output_dir": ".",               # Excel 输出目录
    "data_file": "processed_market_data.pkl"
}

## 输出文件说明 ##
OUTPUTS = {
    "Excel报告": "Amazon市场分析报告_{YYYYMMDD}.xlsx",
    "数据文件": "processed_market_data.pkl",
    "看板地址": "http://localhost:8501"
}
