"""
collect_202604_multisite.py
==========================
全站点 2026年4月（202604）数据补齐脚本
- 涵盖站点: US, UK, JP, DE, ES, IT, IN, FR
- 规则: 
  * 销量根据站点动态过滤 (US>=200, UK/DE/JP>=80, 其它>=50)
  * 精准品类剔除 (is_unrelated 规则)
  * 支持每月保存，写入各自站点 data/{site}/2026.json 中以键 "202604" 存储
"""

import json
import os
import time
import subprocess
from datetime import datetime
from pathlib import Path

# ── 站点配置 ──────────────────────────────────────────────────────
SITES_CONFIG = {
    "US": {
        "nodes": ["11091801:11974521:8882489011:11974711"],
        "min_units": 200,
    },
    "UK": {
        "nodes": ["340837031:407786031:407791031"],
        "min_units": 80,
    },
    "JP": {
        "nodes": ["2123629051:2130074051:2130077051"],
        "min_units": 80,
    },
    "DE": {
        "nodes": ["562066:571860:331964031:316880011:1195978"],
        "min_units": 80,
    },
    "ES": {
        "nodes": [
            "3628866031:4965358031:4965500031",
            "599370031:664660031:930692031:930764031:930776031"
        ],
        "min_units": 50,
    },
    "IT": {
        "nodes": ["3628629031:5021799031:5021870031"],
        "min_units": 50,
    },
    "IN": {
        "nodes": ["3677697031:4654321031:4654392031"],
        "min_units": 50,
    },
    "FR": {
        "nodes": [
            "340861031:421618031:421623031",
            "13921051:13910691:342765031:16404611:1444665031"
        ],
        "min_units": 50,
    }
}

TARGET_MONTH = "202604"
PAGE_SIZE = 50
MAX_PAGES = 20

# ── 过滤规则 ──────────────────────────────────────────────────────
def is_unrelated(title: str, brand: str) -> tuple[bool, str]:
    if not isinstance(title, str):
        return False, ""
    title_lower = title.lower()
    brand_lower = str(brand).lower()
    
    # 1. Karaoke / Kids / Toys
    kids_keywords = ['bambini', 'niños', 'kinder', 'jouet', 'juguete', 'おもちゃ', 'bambino', 'niño', 'spielzeug', 'children', 'bambina']
    for kw in kids_keywords:
        if kw in title_lower:
            return True, f"kids/toy ({kw})"
    if 'karaoke' in title_lower:
        if not any(pb in brand_lower for pb in ['hollyland', 'rode', 'rød', 'dji', 'shure', 'sennheiser']):
            return True, "karaoke mic"
            
    # 2. Guitar & Instrument Wireless
    guitar_keywords = ['guitar', 'guitarra', 'gitarre', 'chitarra', 'sax', 'saxophone', 'violin', 'violine', 'flute']
    for kw in guitar_keywords:
        if kw in title_lower:
            return True, f"instrument wireless ({kw})"
            
    # 3. Wired On-Camera Shotgun / Directional Mics
    shotgun_keywords = ['videomic', 'videomicro', 'shotgun', 'filaire', 'câblé', 'directional on-camera']
    for kw in shotgun_keywords:
        if kw in title_lower:
            return True, f"shotgun/wired mic ({kw})"
            
    # 4. Gimbals / Stabilizers — filter bundles containing gimbal + mic
    gimbal_keywords = [
        'gimbal', 'stabilizer', 'stabilisateur', 'estabilizador',
        'ジンバル', 'スタビライザー', 'stabilizzatore', 'stabilisator',
        'osmo mobile',      # DJI Osmo Mobile is a phone gimbal
        'rs 3 mini', 'rs3 mini', 'rs 4 mini', 'rs4 mini',  # DJI RS series camera gimbals
        'pocket 3',         # DJI Pocket 3 is an action camera
    ]
    for kw in gimbal_keywords:
        if kw in title_lower:
            return True, f"gimbal/stabilizer ({kw})"

    # 5. Cameras & Camera bodies
    camera_keywords = [
        'zv-e10', 'zv-1', 'zv e10', 'zv1', 'spiegellose', 'mirrorless', 'vlog-kamera',
        'デジタルカメラ', 'ビデオカメラ',  # JP: digital camera, video camera
        'action cam', 'action camera', 'actioncam',
        'osmo action',       # DJI action camera
    ]
    for kw in camera_keywords:
        if kw in title_lower:
            return True, f"camera ({kw})"
            
    return False, ""


def fetch_node_data(site: str, node: str, min_units: int) -> list[dict]:
    """拉取指定站点、节点的数据，支持销量早停"""
    all_items = []
    page = 1
    
    while page <= MAX_PAGES:
        cmd = [
            r".\venv\Scripts\sellersprite.exe",
            "product", "search",
            f"nodeIdPath={node}",
            f"month={TARGET_MONTH}",
            "variation=Y",
            "-m", site,
            "--page", str(page),
            "--size", str(PAGE_SIZE)
        ]
        
        print(f"  [{site}] 节点 {node} 第{page}页 拉取中...", flush=True)
        
        try:
            result_str = subprocess.check_output(cmd, text=True, encoding="utf-8")
            result = json.loads(result_str)
        except Exception as e:
            print(f"  [{site}] 节点 {node} 第{page}页 出错: {e}")
            break
            
        if result is None:
            break
            
        items = result.get("items", [])
        total_pages = result.get("pages", 1)
        
        if not items:
            break
            
        early_break = False
        for item in items:
            title = item.get("title", "")
            brand = item.get("brand", "")
            units = item.get("units", 0) or 0
            bad, reason = is_unrelated(title, brand)
            
            if bad:
                continue
            if units < min_units:
                print(f"    -> [早停] 发现销量低于阈值产品 ({units} < {min_units})，停止后续翻页。")
                early_break = True
                break
                
            # 注入元数据
            item["fetched_month"] = TARGET_MONTH
            item["fetched_node"] = node
            item["fetched_at"] = datetime.now().isoformat()
            all_items.append(item)
            
        if early_break or page >= total_pages:
            break
            
        page += 1
        time.sleep(1.5)
        
    return all_items


def load_existing_2026(site: str) -> dict:
    """加载已有的 2026.json 文件"""
    fp = Path(f"data/{site}/2026.json")
    if not fp.exists():
        return {}
    with open(fp, encoding="utf-8") as f:
        try:
            return json.load(f)
        except Exception:
            return {}


def save_2026(site: str, data: dict):
    """保存 2026.json 数据"""
    dp = Path(f"data/{site}")
    dp.mkdir(parents=True, exist_ok=True)
    fp = dp / "2026.json"
    with open(fp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    total = sum(len(v) for v in data.values())
    print(f"  [保存] {fp} — 共 {len(data)} 个月份，{total} 条记录")


def main():
    print("=" * 60)
    print(f"  全球全站点 2026年4月 ({TARGET_MONTH}) 增量拉取")
    print("=" * 60)
    
    for site, config in SITES_CONFIG.items():
        print(f"\n>>> 正在处理站点: {site} (阈值: >= {config['min_units']} 件/月)")
        
        # 抓取所有配置的节点
        all_site_items = []
        for node in config["nodes"]:
            node_items = fetch_node_data(site, node, config["min_units"])
            all_site_items.extend(node_items)
            
        # 节点间 ASIN 去重
        seen_asins = set()
        unique_items = []
        for item in all_site_items:
            asin = item.get("asin")
            if asin not in seen_asins:
                unique_items.append(item)
                seen_asins.add(asin)
                
        print(f"  [{site}] {TARGET_MONTH} 采集完成: 原始合并去重后共 {len(unique_items)} 条记录")
        
        # 增量更新保存
        existing_data = load_existing_2026(site)
        existing_data[TARGET_MONTH] = unique_items
        save_2026(site, existing_data)
        time.sleep(2)  # 站点间隔
        
    print(f"\n{'='*60}")
    print(f"  2026年4月数据全球增量拉取完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()
