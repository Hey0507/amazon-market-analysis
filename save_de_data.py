import json
import sys
from pathlib import Path

def save_data(month, items_json_str):
    year = month.split('-')[0]
    output_base = Path('./raw_data')
    output_base.mkdir(exist_ok=True)
    file_path = output_base / f'德国_{year}.json'
    
    try:
        json_data = json.loads(items_json_str)
        if isinstance(json_data, dict) and 'data' in json_data and 'items' in json_data['data']:
            items = json_data['data']['items']
        else:
            items = json_data if isinstance(json_data, list) else []
    except json.JSONDecodeError:
        print("Invalid JSON")
        return
        
    # 过滤销量 < 200
    valid_items = [item for item in items if item.get('units', 0) >= 200]
    
    # 读取已存在的数据
    data = []
    if file_path.exists():
        with open(file_path, 'r', encoding='utf-8') as f:
            try:
                data = json.load(f)
            except:
                data = []
            
    # 检查该月是否已存在，如果存在则合并去重
    month_entry = next((entry for entry in data if entry['month'] == month), None)
    if month_entry:
        seen = {x['asin'] for x in month_entry['data']}
        for item in valid_items:
            if item['asin'] not in seen:
                month_entry['data'].append(item)
                seen.add(item['asin'])
    else:
        data.append({'month': month, 'data': valid_items})
        
    # 按月份降序排序
    data.sort(key=lambda x: x['month'], reverse=True)
    
    # 保存
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        
    print(f'已保存 {month} 的数据，包含 {len(valid_items)} 个有效商品到 {file_path.name}')

if __name__ == '__main__':
    if len(sys.argv) < 2:
        sys.exit(1)
    month = sys.argv[1]
    if len(sys.argv) >= 3:
        file_path = sys.argv[2]
        with open(file_path, 'r', encoding='utf-8') as f:
            items_json_str = f.read()
    else:
        items_json_str = sys.stdin.read()
    save_data(month, items_json_str)
