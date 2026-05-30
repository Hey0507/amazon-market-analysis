import json
import os
import requests
import time
from datetime import datetime

# MCP API Configuration
MCP_URL = "https://mcp.sellersprite.com/mcp"
SECRET_KEY = "953f8211226e4d31bcba3237ae18f21f"
HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/json",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "secret-key": SECRET_KEY
}

# 站点配置 - 经过确认的无线麦克风类目节点
# MARKETS = { 国家: [类目路径列表] }
MARKETS = {
    "US": ["11091801:11974521:8882489011:11974711"], # Wireless Microphones & Systems
    "DE": [
        "78434031:416393031:416410031",             # Musikinstrumente > Mikrofone > Funkmikrofone
        "571860:162622011:306110031:364417031"      # Kamera & Foto > Zubehör > Camcorderzubehör > Kamera-Mikrofone
    ],
    "FR": [
        "340861031:421618031:421623031",            # Instruments de musique et Sono > Micros sans fil
        "13921051:13910691:342765031:16404611:1444665031" # Photo et caméscopes > Microphones externes
    ],
    "ES": [
        "3628866031:4965358031:4965500031",         # Instrumentos musicales > Micrófonos inalámbricos
        "599370031:664660031:930692031:930764031:930776031" # Electrónica > Micrófonos externos
    ],
    "IT": ["3628629031:5021799031:5021870031"],     # Strumenti musicali > Wireless
    "JP": ["2123629051:2130074051:2130077051"],     # 楽器・音響機器 > ワイヤレス
    "IN": ["3677697031:4654321031:4654392031"],     # Musical Instruments > Wireless
    "AU": ["4852387051:5029133051:5029202051"]      # Musical Instruments > Microphone Sets
}

RAW_DATA_DIR = "data"
os.makedirs(RAW_DATA_DIR, exist_ok=True)

def call_mcp_tool(tool_name, arguments):
    """通用 MCP 工具调用函数"""
    payload = {
        "method": "tools/call",
        "params": {
            "name": tool_name,
            "arguments": arguments
        },
        "jsonrpc": "2.0",
        "id": int(time.time() * 1000)
    }
    try:
        response = requests.post(MCP_URL, headers=HEADERS, json=payload, timeout=60)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"调用工具 {tool_name} 出错: {e}")
        return None

def fetch_market_data(marketplace, nodeIdPath, month):
    """抓取指定站点、类目、月份的数据"""
    print(f"正在抓取 {marketplace} 类目 {nodeIdPath} (月份: {month})...")
    all_items = []
    page = 1
    max_pages = 20 # 最多抓取 20 页 (约 1000 个产品)
    
    while page <= max_pages:
        args = {
            "request": {
                "marketplace": marketplace,
                "nodeIdPath": nodeIdPath,
                "month": month,
                "page": page,
                "size": 50,
                "variation": "Y" # 排除变体以获得准确的市场总量
            }
        }
        
        # 使用 competitor_lookup 抓取类目下的产品
        result = call_mcp_tool("mcp_sellersprite-mcp_competitor_lookup", args)
        
        if not result or "result" not in result:
            print(f"  [警告] {marketplace} 第 {page} 页无返回结果")
            break
            
        content = result.get("result", {}).get("content", [])
        if not content:
            break
            
        try:
            data_str = content[0].get("text", "{}")
            data = json.loads(data_str)
            items = data.get("data", {}).get("items", [])
            
            if not items:
                print(f"  [信息] {marketplace} 第 {page} 页没有更多产品")
                break
            
            # 记录抓取信息并合并
            for item in items:
                item['fetched_month'] = month
                item['fetched_node'] = nodeIdPath
                item['fetched_at'] = datetime.now().isoformat()
            
            all_items.extend(items)
            print(f"  第 {page} 页: 找到 {len(items)} 个产品")
            
            total_pages = data.get("data", {}).get("pages", 1)
            if page >= total_pages:
                break
            
            page += 1
            time.sleep(2) # 速率限制
        except Exception as e:
            print(f"  [错误] 解析 {marketplace} 第 {page} 页数据失败: {e}")
            break
            
    return all_items

def save_annual_data(marketplace, year, items):
    """按年度保存数据，并执行去重和销量过滤"""
    market_dir = os.path.join(RAW_DATA_DIR, marketplace)
    os.makedirs(market_dir, exist_ok=True)
    file_path = os.path.join(market_dir, f"{year}.json")
    
    # 加载现有数据
    existing_data = []
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            try:
                existing_data = json.load(f)
            except:
                existing_data = []
    
    # 合并新旧数据
    combined = existing_data + items
    
    # 按 ASIN + 月份 进行去重 (保留最新的记录)
    unique_records = {}
    for item in combined:
        asin = item.get('asin')
        month = item.get('fetched_month')
        if not asin or not month:
            continue
            
        key = f"{asin}_{month}"
        # 如果已存在，比较抓取时间或直接覆盖（此处选择覆盖，因为 items 是新抓取的）
        unique_records[key] = item
    
    # 执行过滤: 筛除当月销量低于 200 的 ASIN (用户要求)
    # 同时识别主要品牌
    final_items = []
    for key, item in unique_records.items():
        units = item.get('units') or 0
        if units >= 200:
            # 品牌标准化处理
            brand = str(item.get('brand', '')).lower()
            item['is_hollyland'] = 'hollyland' in brand or 'hollyview' in brand
            item['is_dji'] = 'dji' in brand
            final_items.append(item)
            
    # 按月份和销量排序，方便查阅
    final_items.sort(key=lambda x: (x.get('fetched_month', ''), -(x.get('units', 0))))
    
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(final_items, f, ensure_ascii=False, indent=2)
    
    print(f"站点 {marketplace}: 已保存 {len(final_items)} 条记录 (年度: {year}) 到 {file_path}")

def main():
    # 执行抓取的月份
    months_to_fetch = ["202502", "202501"] # 优先抓取最近两个月
    
    for marketplace, nodes in MARKETS.items():
        print(f"\n>>>> 开始处理站点: {marketplace} <<<<")
        
        # 按年度分组存储
        year_groups = {} # { year: [items] }
        
        for month in months_to_fetch:
            year = month[:4]
            if year not in year_groups:
                year_groups[year] = []
                
            month_items = []
            for node in nodes:
                node_items = fetch_market_data(marketplace, node, month)
                month_items.extend(node_items)
            
            # 月度去重 (防止跨类目重复)
            seen_asins = set()
            unique_month_items = []
            for item in month_items:
                if item['asin'] not in seen_asins:
                    unique_month_items.append(item)
                    seen_asins.add(item['asin'])
            
            print(f"  站点 {marketplace} 月份 {month}: 共采集到 {len(unique_month_items)} 个唯一 ASIN")
            year_groups[year].extend(unique_month_items)
        
        # 保存各年度数据
        for year, items in year_groups.items():
            if items:
                save_annual_data(marketplace, year, items)
                
    print("\n==== 所有站点数据采集完成 ====")

if __name__ == "__main__":
    main()
