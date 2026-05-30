"""
collect_uk_fulldata.py
==========================
英国站点（UK）全量数据采集脚本
- 类目: Wireless Accessories (nodeIdPath: 340837031:407786031:407791031)
- 月份范围: 2024-04 ~ 2026-03 (最近 24 个月)
- 过滤规则:
  * 月销量 >= 80 (UK 阈值, 与 final_processor.py 保持一致)
  * 排除稳定器 / 捆绑包 / 相机机身 (is_unrelated 同步规则)
- 保存格式: data/UK/{year}.json  (dict: { 'YYYYMM': [items] })
  支持增量更新——已有月份的数据会被新数据覆盖
"""

import json
import os
import time
import subprocess
from datetime import datetime
from pathlib import Path

# ── 配置 ──────────────────────────────────────────────────────────
MARKETPLACE = "UK"
UK_NODE = "340837031:407786031:407791031"   # Wireless Microphones / Accessories UK
DATA_DIR = Path("data/UK")
DATA_DIR.mkdir(parents=True, exist_ok=True)

# 需要拉取的月份（YYYYMM 格式）
MONTHS_TO_FETCH = [
    "202404", "202405", "202406",
    "202407", "202408", "202409",
    "202410", "202411", "202412",
    "202501", "202502", "202503",
    "202504", "202505", "202506",
    "202507", "202508", "202509",
    "202510", "202511", "202512",
    "202601", "202602", "202603"
]

# 销量最低阈值（UK 站点）
UK_MIN_UNITS = 80

# 每页条数
PAGE_SIZE = 50
# 最多翻页数
MAX_PAGES = 20

# ── 过滤规则（与 final_processor.py is_unrelated 完全一致） ───────
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
        # professional brands like Hollyland/RODE/DJI don't make karaoke mics
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


def fetch_month(marketplace: str, node: str, month: str) -> tuple[list[dict], list[tuple], int]:
    """
    调用 sellersprite CLI 工具拉取指定月份的类目全量数据。
    返回过滤后的产品列表、排除的不相关产品列表、以及原始拉取产品数。
    """
    all_items = []
    excluded = []
    raw_count = 0
    page = 1

    while page <= MAX_PAGES:
        # 构建 CLI 调用参数
        cmd = [
            r".\venv\Scripts\sellersprite.exe",
            "product", "search",
            f"nodeIdPath={node}",
            f"month={month}",
            "variation=Y",
            "-m", marketplace,
            "--page", str(page),
            "--size", str(PAGE_SIZE)
        ]

        print(f"  [{marketplace}] {month} 第{page}页 拉取中...", flush=True)

        try:
            result_str = subprocess.check_output(cmd, text=True, encoding="utf-8")
            result = json.loads(result_str)
        except Exception as e:
            print(f"  [{marketplace}] {month} 第{page}页 调用CLI出错: {e}")
            break

        if result is None:
            print(f"  [{marketplace}] {month} 第{page}页 无返回，停止翻页")
            break

        items = result.get("items", [])
        total_pages = result.get("pages", 1)

        if not items:
            print(f"  [{marketplace}] {month} 第{page}页 已无更多产品")
            break

        raw_count += len(items)

        for item in items:
            title = item.get("title", "")
            brand = item.get("brand", "")
            units = item.get("units", 0) or 0
            bad, reason = is_unrelated(title, brand)

            if bad:
                excluded.append((item.get("asin"), reason, title[:60]))
                continue
            if units < UK_MIN_UNITS:
                # 触发销量阈值早停：由于 Sellersprite 数据按销量由高到低排序，一旦遇到低于阈值的产品，后续产品及页面必定全部低于阈值，直接早停。
                print(f"    -> [早停] 发现销量低于阈值产品 ({units} < {UK_MIN_UNITS})，停止此月份后续翻页。")
                page = MAX_PAGES + 1
                break

            # 注入元数据
            item["fetched_month"] = month
            item["fetched_node"] = node
            item["fetched_at"] = datetime.now().isoformat()
            all_items.append(item)

        print(f"    -> 本页有效: {len(items)} 条，累计: {len(all_items)} 条，已排除: {len(excluded)} 条")

        if page >= total_pages:
            break
        page += 1
        time.sleep(1.5)

    return all_items, excluded, raw_count


def load_existing(year: str) -> dict:
    """加载已有年度数据"""
    fp = DATA_DIR / f"{year}.json"
    if not fp.exists():
        return {}
    with open(fp, encoding="utf-8") as f:
        try:
            data = json.load(f)
            if isinstance(data, dict):
                return data
            # 旧格式 list -> 转换为 dict
            d = {}
            for item in data:
                m = item.get("fetched_month", "")
                d.setdefault(m, []).append(item)
            return d
        except Exception:
            return {}


def save_year(year: str, data: dict):
    """保存年度数据（dict 格式）"""
    fp = DATA_DIR / f"{year}.json"
    with open(fp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    total = sum(len(v) for v in data.values())
    print(f"  [保存] {fp} — 共 {len(data)} 个月份，{total} 条记录")


def main():
    print("=" * 60)
    print("  英国站点 (UK) 全量数据采集")
    print(f"  类目: Wireless Accessories")
    print(f"  节点: {UK_NODE}")
    print(f"  月份范围: {MONTHS_TO_FETCH[0]} ~ {MONTHS_TO_FETCH[-1]}")
    print(f"  销量小阈值: >= {UK_MIN_UNITS} 单位/月")
    print("=" * 60)

    # 按年分组月份
    year_months: dict[str, list[str]] = {}
    for m in MONTHS_TO_FETCH:
        y = m[:4]
        year_months.setdefault(y, []).append(m)

    grand_total = 0
    grand_excluded = 0

    for year, months in sorted(year_months.items()):
        print(f"\n>>> 年度 {year}: 需采集 {len(months)} 个月份")

        # 加载已有数据（支持增量更新）
        year_data = load_existing(year)

        for month in months:
            # 判断是否已经抓取过且有有效数据，有则跳过，实现安全回溯
            if month in year_data and len(year_data[month]) > 0:
                print(f"  [{month}] 已有 {len(year_data[month])} 条，跳过（如需重新拉取请删除对应月份）")
                continue

            items, excluded, raw_count = fetch_month(MARKETPLACE, UK_NODE, month)
            year_data[month] = items
            grand_total += len(items)
            grand_excluded += len(excluded)

            print(f"  [{month}] 原始拉取: {raw_count} 条，排除不相关: {len(excluded)} 条，最终保留: {len(items)} 条")
            if excluded:
                for asin, reason, title in excluded[:5]:
                    print(f"    排除: [{asin}] {reason} — {title}")

            # 每月保存一次（防止中断丢失）
            save_year(year, year_data)
            time.sleep(2)  # 月份间隔

    print(f"\n{'='*60}")
    print(f"  采集完成！累计有效记录: {grand_total} 条，过滤记录: {grand_excluded} 条")
    print("=" * 60)


if __name__ == "__main__":
    main()
