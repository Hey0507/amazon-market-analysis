"""
generate_step_mapping.py
生成多站点的 STEP_MAPPING 配置

每个站点、每个品类、每个月份都需要一个唯一的 step_id
来从 Sellersprite MCP 采集数据

使用方法:
  python generate_step_mapping.py --sites US,UK,DE --months 24
  python generate_step_mapping.py --list-sites
"""

import json
import argparse
from datetime import datetime, timedelta
from pathlib import Path

# 站点列表
SITES = {
    'US': {'code': 'US', 'name': '美国', 'start_month': '2024-05'},
    'UK': {'code': 'UK', 'name': '英国', 'start_month': '2024-05'},
    'DE': {'code': 'DE', 'name': '德国', 'start_month': '2024-05'},
    'FR': {'code': 'FR', 'name': '法国', 'start_month': '2024-05'},
    'IT': {'code': 'IT', 'name': '意大利', 'start_month': '2024-05'},
    'ES': {'code': 'ES', 'name': '西班牙', 'start_month': '2024-05'},
    'JP': {'code': 'JP', 'name': '日本', 'start_month': '2024-05'},
    'AU': {'code': 'AU', 'name': '澳大利亚', 'start_month': '2024-05'},
    'CA': {'code': 'CA', 'name': '加拿大', 'start_month': '2024-05'},
    'MX': {'code': 'MX', 'name': '墨西哥', 'start_month': '2024-05'},
    'NL': {'code': 'NL', 'name': '荷兰', 'start_month': '2024-05'},
    'SE': {'code': 'SE', 'name': '瑞典', 'start_month': '2024-05'},
    'PL': {'code': 'PL', 'name': '波兰', 'start_month': '2024-05'},
    'AE': {'code': 'AE', 'name': '阿联酋', 'start_month': '2024-05'},
    'IN': {'code': 'IN', 'name': '印度', 'start_month': '2024-05'},
}

# 品类列表
CATEGORIES = ['Lavalier', 'Transmitter']

# Step ID 起始值 (每个站点偏移 1000，确保不冲突)
SITE_STEP_OFFSET = {
    'US': 0,
    'UK': 1000,
    'DE': 2000,
    'FR': 3000,
    'IT': 4000,
    'ES': 5000,
    'JP': 6000,
    'AU': 7000,
    'CA': 8000,
    'MX': 9000,
    'NL': 10000,
    'SE': 11000,
    'PL': 12000,
    'AE': 13000,
    'IN': 14000,
}

# 2024-05 开始的 step base
# 448 = 2024-05 Lavalier, 459 = 2024-05 Transmitter
STEP_BASE_LAV = 448
STEP_BASE_TX = 459


def generate_monthly_steps(start_month: str, months: int, site: str):
    """为一个站点生成月份到 step_id 的映射"""
    mapping = {}

    start = datetime.strptime(start_month, "%Y-%m")
    base_offset = SITE_STEP_OFFSET.get(site, 0)

    for i in range(months):
        current = start + timedelta(days=30 * i)
        month_str = current.strftime("%Y-%m")

        # 计算相对月份 (0 = 2024-05)
        months_diff = (current.year - 2024) * 12 + (current.month - 5)

        # Lavalier steps: 448, 447, 446... (每月递减)
        lav_step = STEP_BASE_LAV - months_diff + base_offset
        mapping[lav_step] = (month_str, 'Lavalier', site)

        # Transmitter steps: 459, 458, 457... (每月递减)
        tx_step = STEP_BASE_TX - months_diff + base_offset
        mapping[tx_step] = (month_str, 'Transmitter', site)

    return mapping


def generate_all_mappings(sites: list = None, months: int = 24):
    """生成所有站点的 mappings"""
    all_mappings = {}

    target_sites = sites if sites else list(SITES.keys())

    for site in target_sites:
        if site not in SITES:
            print(f"⚠️ 未知站点: {site}")
            continue

        site_config = SITES[site]
        start_month = site_config['start_month']

        mapping = generate_monthly_steps(start_month, months, site)
        all_mappings.update(mapping)

        print(f"✅ {site} ({site_config['name']}): 生成了 {len(mapping)} 个 step mappings")

    return all_mappings


def list_available_sites():
    """列出所有支持的站点"""
    print("\n支持的站点列表:")
    print("-" * 40)
    for code, config in SITES.items():
        print(f"  {code:4s} - {config['name']}")
    print("-" * 40)
    print(f"共 {len(SITES)} 个站点\n")


def export_mapping_json(mapping: dict, output_file: str = None):
    """导出 mapping 为 JSON 格式（用于调试）"""
    # 转换 tuple 为字典以便 JSON 序列化
    export_data = {}
    for step_id, (month, cat, site) in mapping.items():
        export_data[str(step_id)] = {
            "month": month,
            "category": cat,
            "site": site
        }

    if output_file is None:
        output_file = "step_mapping_export.json"

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(export_data, f, ensure_ascii=False, indent=2)

    print(f"📄 Step mapping 已导出: {output_file}")


def export_python_format(mapping: dict, output_file: str = "step_mapping_generated.py"):
    """导出为 Python 格式（可直接粘贴到 final_processor.py）"""

    lines = [
        "# 自动生成的 Step Mapping",
        "# 生成时间: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "",
        "STEP_MAPPING = {",
    ]

    # 按 step_id 排序
    for step_id in sorted(mapping.keys()):
        month, cat, site = mapping[step_id]
        lines.append(f"    {step_id}: ('{month}', '{cat}', '{site}'),")

    lines.append("}")

    content = "\n".join(lines)

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"📄 Python 格式已导出: {output_file}")
    print(f"   将内容复制到 final_processor.py 的 STEP_MAPPING")


def main():
    parser = argparse.ArgumentParser(description="生成多站点 Step Mapping")
    parser.add_argument("--sites", type=str, default=None,
                        help="站点代码，用逗号分隔，如: US,UK,DE")
    parser.add_argument("--all-sites", action="store_true",
                        help="生成所有站点")
    parser.add_argument("--months", type=int, default=24,
                        help="回溯月份数")
    parser.add_argument("--list", action="store_true",
                        help="列出所有支持的站点")
    parser.add_argument("--export-json", action="store_true",
                        help="导出为 JSON 格式")
    parser.add_argument("--export-python", action="store_true",
                        help="导出为 Python 格式")

    args = parser.parse_args()

    if args.list:
        list_available_sites()
        return

    # 确定站点
    sites = None
    if args.all_sites:
        sites = list(SITES.keys())
    elif args.sites:
        sites = [s.strip().upper() for s in args.sites.split(",")]

    if not sites:
        print("❌ 请指定站点 (--sites) 或使用 --all-sites")
        list_available_sites()
        return

    print(f"🎯 为以下站点生成 mapping: {', '.join(sites)}")
    print(f"📅 回溯月份: {args.months}")
    print()

    mapping = generate_all_mappings(sites, args.months)

    print(f"\n📊 共生成 {len(mapping)} 个 step mappings")

    if args.export_json:
        export_mapping_json(mapping)

    if args.export_python:
        export_python_format(mapping)

    if not args.export_json and not args.export_python:
        print("\n💡 使用 --export-python 生成 Python 代码并更新 final_processor.py")


if __name__ == "__main__":
    main()
