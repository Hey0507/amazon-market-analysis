"""
collect_single_site.py
单站点数据采集脚本 - 每次只拉取一个站点的数据

使用方法:
  python collect_single_site.py US
  python collect_single_site.py UK
  python collect_single_site.py UK --months 6

数据存储:
  /mnt/c/Users/alecl/.gemini/antigravity/brain/2f8e5fa7-6cfb-4693-b4e8-3a63fd1c4daf/.system_generated/steps/
  按站点分目录存储:
    site_us/  - 美国站数据
    site_uk/  - 英国站数据
    ...
"""

import httpx
import asyncio
import json
import os
import sys
import argparse
from datetime import datetime
from pathlib import Path

# MCP 配置
MCP_BASE_URL = "https://mcp.sellersprite.com/mcp"
MCP_SECRET_KEY = "953f8211226e4d31bcba3237ae18f21f"

# 站点配置
SITES_CONFIG = {
    'US': {'name': '美国', 'lav_node': '11974761', 'tx_node': '10677099011'},
    'UK': {'name': '英国', 'lav_node': '11974761', 'tx_node': '10677099011'},
    'DE': {'name': '德国', 'lav_node': '11974761', 'tx_node': '10677099011'},
    'FR': {'name': '法国', 'lav_node': '11974761', 'tx_node': '10677099011'},
    'IT': {'name': '意大利', 'lav_node': '11974761', 'tx_node': '10677099011'},
    'ES': {'name': '西班牙', 'lav_node': '11974761', 'tx_node': '10677099011'},
    'JP': {'name': '日本', 'lav_node': '11974761', 'tx_node': '10677099011'},
    'AU': {'name': '澳大利亚', 'lav_node': '11974761', 'tx_node': '10677099011'},
    'CA': {'name': '加拿大', 'lav_node': '11974761', 'tx_node': '10677099011'},
    'MX': {'name': '墨西哥', 'lav_node': '11974761', 'tx_node': '10677099011'},
}

# 数据存储基础路径
BASE_PATH = Path("C:/Users/alecl/.gemini/antigravity/brain/2f8e5fa7-6cfb-4693-b4e8-3a63fd1c4daf/.system_generated/steps")


async def call_mcp_tool(tool_name: str, params: dict) -> dict:
    """调用 MCP 工具"""
    async with httpx.AsyncClient() as client:
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": params
            }
        }

        headers = {
            "Content-Type": "application/json",
            "secret-key": MCP_SECRET_KEY
        }

        try:
            response = await client.post(
                MCP_BASE_URL,
                json=payload,
                headers=headers,
                timeout=60.0
            )
            response.raise_for_status()
            result = response.json()
            return result if result else {}
        except Exception as e:
            print(f"[ERROR] MCP call failed: {e}")
            return {"error": str(e)}


async def collect_site_monthly(site: str, category: str, node_id: str, month: str, size: int = 50) -> dict:
    """采集单个站点单个月份的单个品类数据"""
    print(f"  Collecting {site}/{category}/{month}...")

    result = await call_mcp_tool("competitor_lookup", {
        "marketplace": site,
        "nodeIdPaths": [node_id],
        "variation": "Y",
        "size": size
    })

    return {
        "site": site,
        "category": category,
        "month": month,
        "result": result,
        "timestamp": datetime.now().isoformat()
    }


def save_site_data(site: str, data: dict):
    """保存单个站点的数据"""
    site_folder = BASE_PATH / f"site_{site.lower()}"
    site_folder.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = site_folder / f"{site}_{timestamp}.json"

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"  [OK] Saved: {output_file}")
    return output_file


async def collect_single_site(site: str, months_back: int = 3):
    """采集单个站点的数据"""
    if site not in SITES_CONFIG:
        print(f"[ERROR] Unknown site: {site}")
        print(f"Available sites: {', '.join(SITES_CONFIG.keys())}")
        return

    config = SITES_CONFIG[site]
    print(f"\n[Site] {site} ({config['name']})")
    print(f"[Months] Last {months_back} months")

    # 生成月份列表
    from datetime import datetime, timedelta
    months = []
    for i in range(months_back):
        d = datetime.now() - timedelta(days=30 * i)
        months.append(d.strftime("%Y-%m"))

    # 采集数据
    all_data = {
        "site": site,
        "site_name": config['name'],
        "months": months,
        "collected_at": datetime.now().isoformat(),
        "lavalier": [],
        "transmitter": []
    }

    for month in months:
        # Lavalier
        print(f"\n  [{month}] Lavalier...")
        result = await collect_site_monthly(site, 'Lavalier', config['lav_node'], month)
        all_data['lavalier'].append(result)
        await asyncio.sleep(0.3)

        # Transmitter
        print(f"\n  [{month}] Transmitter...")
        result = await collect_site_monthly(site, 'Transmitter', config['tx_node'], month)
        all_data['transmitter'].append(result)
        await asyncio.sleep(0.3)

    # 保存数据
    output_file = save_site_data(site, all_data)

    print(f"\n[OK] Site {site} collection completed!")
    return output_file


async def main():
    parser = argparse.ArgumentParser(description="单站点Amazon数据采集")
    parser.add_argument("site", type=str, help="站点代码，如: US, UK, DE")
    parser.add_argument("--months", type=int, default=3, help="回溯月份数 (默认3)")

    args = parser.parse_args()

    site = args.site.upper()

    print(f"[Target] Site: {site}")
    print(f"[Months] {args.months}")
    print("=" * 50)

    await collect_single_site(site, args.months)

    print("\n[Done] Next steps:")
    print(f"  1. Data saved to: {BASE_PATH}/site_{site.lower()}/")
    print(f"  2. Run final_processor.py to process data")
    print(f"  3. Run export_excel.py to generate report")


if __name__ == "__main__":
    asyncio.run(main())
