import json
import os
import pandas as pd
import numpy as np
from datetime import datetime

DATA_DIR = "data"
ANALYTICS_FILE = os.path.join(DATA_DIR, "analytics_summary.json")

# Site translation dictionary
SITE_NAMES = {
    'US': '美国', 'UK': '英国', 'DE': '德国', 'FR': '法国', 'IT': '意大利', 'ES': '西班牙',
    'JP': '日本', 'AU': '澳大利亚', 'CA': '加拿大', 'IN': '印度'
}

def load_all_data():
    """加载所有站点的年度 JSON 数据"""
    all_records = []
    if not os.path.exists(DATA_DIR):
        print(f"Error: {DATA_DIR} directory does not exist.")
        return all_records

    print(f"Scanning {DATA_DIR} directory...")
    for market in os.listdir(DATA_DIR):
        market_path = os.path.join(DATA_DIR, market)
        if not os.path.isdir(market_path):
            continue
            
        for file_name in os.listdir(market_path):
            if file_name.endswith(".json"):
                year = file_name.replace(".json", "")
                file_path = os.path.join(market_path, file_name)
                with open(file_path, 'r', encoding='utf-8') as f:
                    try:
                        data = json.load(f)
                        # We know raw files are dict of {month_str: [items]}
                        if isinstance(data, dict):
                            for month_str, items in data.items():
                                # Standardize month format to YYYY-MM
                                if len(month_str) == 6: # e.g. 202412
                                    fmt_month = f"{month_str[:4]}-{month_str[4:]}"
                                else:
                                    fmt_month = month_str
                                
                                for item in items:
                                    item['market'] = market
                                    item['year'] = year
                                    item['fetched_month'] = fmt_month
                                    all_records.append(item)
                    except Exception as e:
                        print(f"加载文件 {file_name} 出错: {e}")
    return all_records

def get_price_tier(price):
    """价位段分类（与 final_processor.py 保持一致）"""
    if price is None or price < 0: return 'Unknown'
    if price <= 30: return '0-30'
    if price <= 50: return '30-50'
    if price <= 100: return '50-100'
    if price <= 150: return '100-150'
    return '150+'

def run_linear_forecast(historical_months, historical_revenues):
    """简易而健壮的线性趋势外推预测模型，包含 95% 置信区间"""
    n = len(historical_revenues)
    if n < 3:
        return None
        
    x = np.arange(n)
    y = np.array(historical_revenues)
    
    # Fit linear regression: y = slope * x + intercept
    slope, intercept = np.polyfit(x, y, 1)
    y_fitted = slope * x + intercept
    
    # Calculate residuals standard error
    residuals = y - y_fitted
    std_err = np.std(residuals) if len(residuals) > 1 else 0
    if std_err == 0:
        std_err = np.mean(y) * 0.1 # Fallback to 10% average
        
    # Project next 6 months
    forecast_x = np.arange(n, n + 6)
    forecast_y = slope * forecast_x + intercept
    
    # Standardize predictions to be non-negative
    forecast_y = np.maximum(0, forecast_y)
    
    predictions = []
    # Parse last month date
    try:
        last_dt = datetime.strptime(historical_months[-1], "%Y-%m")
    except:
        last_dt = datetime.now()
        
    for i, fy in enumerate(forecast_y, 1):
        # Calculate future month string
        fut_year = last_dt.year + (last_dt.month + i - 1) // 12
        fut_month = (last_dt.month + i - 1) % 12 + 1
        fut_month_str = f"{fut_year}-{fut_month:02d}"
        
        # Calculate bounds
        lower_bound = max(0, fy - 1.96 * std_err)
        upper_bound = fy + 1.96 * std_err
        
        predictions.append({
            'fetched_month': fut_month_str,
            'revenue': round(float(fy), 2),
            'lower_ci': round(float(lower_bound), 2),
            'upper_ci': round(float(upper_bound), 2),
            'type': 'Forecast'
        })
        
    return predictions

def analyze_data(records):
    if not records:
        return {}
        
    df = pd.DataFrame(records)
    print(f"Loaded {len(df)} total records from raw data. Commencing ETL...")
    
    # Convert numeric fields
    df['units'] = pd.to_numeric(df.get('units', 0), errors='coerce').fillna(0)
    df['revenue'] = pd.to_numeric(df.get('revenue', 0), errors='coerce').fillna(0)
    df['price'] = pd.to_numeric(df.get('price', 0), errors='coerce').fillna(0)
    df['rating'] = pd.to_numeric(df.get('rating', 0.0), errors='coerce').fillna(4.5)
    df['availableDate'] = pd.to_numeric(df.get('availableDate', 0), errors='coerce')
    
    # Handle averagePrice fallback
    if 'averagePrice' in df.columns:
        df['averagePrice'] = pd.to_numeric(df['averagePrice'], errors='coerce').fillna(0)
    else:
        df['averagePrice'] = 0
    df['actual_price'] = df['averagePrice'].where(df['averagePrice'] > 0, df['price'])
    
    # Brand Clean & Normalize
    df['brand_norm'] = df.get('brand', 'Unknown').astype(str).str.strip()
    # Case-insensitive brand merging: Hollyview -> Hollyland
    df['brand_norm'] = df['brand_norm'].apply(
        lambda b: 'Hollyland' if b.lower().startswith('hollyview') else b
    )
    # RODE and Rode normalization
    df['brand_norm'] = df['brand_norm'].apply(
        lambda b: 'Rode' if b.lower().startswith('rode') or b.lower().startswith('r?de') or b.lower().startswith('røde') else b
    )
    
    # Standardize market names to Chinese display
    df['market_cn'] = df['market'].map(SITE_NAMES).fillna(df['market'])
    
    # Category detection
    df['category'] = df.get('nodeLabelPath', '').astype(str).apply(
        lambda x: x.split(':')[-1] if ':' in x else (x if x else 'Wireless Microphone')
    )

    # Dynamic monthly sales threshold by market (matches final_processor.py logic)
    # US: >= 200, UK/DE/JP: >= 80, others: >= 50
    US_MARKETS = {'美国', 'US'}
    MID_MARKETS = {'英国', '德国', '日本', 'UK', 'DE', 'JP'}

    def _get_threshold(market_code):
        if market_code in US_MARKETS:
            return 200
        elif market_code in MID_MARKETS:
            return 80
        return 50

    df['_threshold'] = df.apply(
        lambda r: _get_threshold(r.get('market', '')) if hasattr(r, 'get')
        else _get_threshold(r['market']),
        axis=1
    )
    df = df[df['units'] >= df['_threshold']].drop(columns=['_threshold']).copy()
    print(f"Filtered records with dynamic market thresholds: {len(df)}")
    
    # Product age definition (New <= 180 days from available date)
    df['launch_date'] = pd.to_datetime(df['availableDate'], unit='ms', errors='coerce')
    # Standardize fetched_month to actual date representation
    df['fetch_date'] = pd.to_datetime(df['fetched_month'] + '-01', format='%Y-%m-%d', errors='coerce')
    df['days_since_launch'] = (df['fetch_date'] - df['launch_date']).dt.days
    df['product_age'] = np.where(
        (df['days_since_launch'] >= 0) & (df['days_since_launch'] <= 180),
        '新品 (New)', '老品 (Old)'
    )
    
    # Pricing segments
    df['price_segment'] = df['actual_price'].apply(get_price_tier)
    
    # Deduplicate: same market, same fetched_month, same ASIN -> keep highest units sold
    df = df.sort_values('units', ascending=False).drop_duplicates(subset=['market_cn', 'fetched_month', 'asin']).copy()
    
    # -------------------------------------------------------------
    # ETL Aggregation Engine
    # -------------------------------------------------------------
    
    def get_summaries(target_df, is_global=False):
        market_key = 'GLOBAL' if is_global else 'market_cn'
        
        # 1. Market Trend (Monthly)
        m_trend = target_df.groupby(['fetched_month'] if is_global else ['market_cn', 'fetched_month']).agg({
            'units': 'sum', 'revenue': 'sum'
        }).reset_index()
        if is_global: m_trend['market'] = 'GLOBAL'
        else: m_trend.rename(columns={'market_cn': 'market'}, inplace=True)
        
        # 2. Monthly Brand Share
        b_share = target_df.groupby(['fetched_month', 'brand_norm'] if is_global else ['market_cn', 'fetched_month', 'brand_norm']).agg({
            'units': 'sum', 'revenue': 'sum'
        }).reset_index()
        if is_global: 
            b_share['market'] = 'GLOBAL'
            b_share = b_share.merge(m_trend.rename(columns={'units': 'total_units', 'revenue': 'total_revenue'}), on=['fetched_month'])
        else: 
            b_share.rename(columns={'market_cn': 'market'}, inplace=True)
            b_share = b_share.merge(m_trend.rename(columns={'units': 'total_units', 'revenue': 'total_revenue'}), on=['market', 'fetched_month'])
            
        b_share['unit_share'] = (b_share['units'] / b_share['total_units'] * 100).round(2)
        b_share['rev_share'] = (b_share['revenue'] / b_share['total_revenue'] * 100).round(2)
        b_share.drop(columns=['total_units', 'total_revenue'], inplace=True)
        
        # 3. Overall Brand Total Share (For Competitor Matrix Bubble Chart)
        # We need average rating, average price, unique ASINs count
        b_total = target_df.groupby(['brand_norm'] if is_global else ['market_cn', 'brand_norm']).agg({
            'units': 'sum',
            'revenue': 'sum',
            'rating': 'mean',
            'asin': 'nunique'
        }).reset_index()
        
        if is_global: 
            b_total['market'] = 'GLOBAL'
            global_total_u = target_df['units'].sum()
            global_total_r = target_df['revenue'].sum()
            b_total['unit_share'] = (b_total['units'] / global_total_u * 100).round(2)
            b_total['rev_share'] = (b_total['revenue'] / global_total_r * 100).round(2)
        else:
            b_total.rename(columns={'market_cn': 'market'}, inplace=True)
            # Merge with site total units and revenue
            site_totals = target_df.groupby('market_cn').agg(total_u=('units','sum'), total_r=('revenue','sum')).reset_index()
            b_total = b_total.merge(site_totals.rename(columns={'market_cn': 'market'}), on='market')
            b_total['unit_share'] = (b_total['units'] / b_total['total_u'] * 100).round(2)
            b_total['rev_share'] = (b_total['revenue'] / b_total['total_r'] * 100).round(2)
            b_total.drop(columns=['total_u', 'total_r'], inplace=True)
            
        b_total['avg_price'] = (b_total['revenue'] / b_total['units']).fillna(0).round(2)
        b_total.rename(columns={'rating': 'avg_rating', 'asin': 'asin_count'}, inplace=True)
        
        # 4. Pricing Segments distribution
        p_analysis = target_df.groupby(['price_segment'] if is_global else ['market_cn', 'price_segment'], observed=True).agg({
            'units': 'sum', 'asin': 'nunique'
        }).rename(columns={'asin': 'product_count'}).reset_index()
        if is_global: p_analysis['market'] = 'GLOBAL'
        else: p_analysis.rename(columns={'market_cn': 'market'}, inplace=True)
        
        # 5. Top 5 Brands per Pricing Segment
        p_top = []
        tmp_df = target_df.copy()
        tmp_df['_market'] = 'GLOBAL' if is_global else tmp_df['market_cn']
        
        for (mkt, seg), group in tmp_df.groupby(['_market', 'price_segment'], observed=True):
            top_b = group.groupby('brand_norm').agg({'units': 'sum', 'revenue': 'sum'}).reset_index()
            top_b = top_b.sort_values('revenue', ascending=False).head(5)
            
            total_u = group['units'].sum()
            total_r = group['revenue'].sum()
            
            for _, brow in top_b.iterrows():
                p_top.append({
                    'market': mkt,
                    'price_segment': str(seg),
                    'brand': brow['brand_norm'],
                    'units': int(brow['units']),
                    'revenue': round(float(brow['revenue']), 2),
                    'unit_share': round(brow['units'] / total_u * 100, 2) if total_u > 0 else 0,
                    'rev_share': round(brow['revenue'] / total_r * 100, 2) if total_r > 0 else 0,
                })
                
        # 6. Product Age Lifecycle performance
        lifecycle = target_df.groupby(['product_age'] if is_global else ['market_cn', 'product_age']).agg({
            'units': 'sum', 'revenue': 'sum'
        }).reset_index()
        
        if is_global:
            lifecycle['market'] = 'GLOBAL'
            lifecycle['unit_share'] = (lifecycle['units'] / global_total_u * 100).round(2)
            lifecycle['rev_share'] = (lifecycle['revenue'] / global_total_r * 100).round(2)
        else:
            lifecycle.rename(columns={'market_cn': 'market'}, inplace=True)
            site_totals = target_df.groupby('market_cn').agg(total_u=('units','sum'), total_r=('revenue','sum')).reset_index()
            lifecycle = lifecycle.merge(site_totals.rename(columns={'market_cn': 'market'}), on='market')
            lifecycle['unit_share'] = (lifecycle['units'] / lifecycle['total_u'] * 100).round(2)
            lifecycle['rev_share'] = (lifecycle['revenue'] / lifecycle['total_r'] * 100).round(2)
            lifecycle.drop(columns=['total_u', 'total_r'], inplace=True)

        return m_trend, b_share, b_total, p_analysis, p_top, lifecycle

    # Run aggregates
    m_trend_l, b_share_l, b_total_l, p_analysis_l, p_top_l, lifecycle_l = get_summaries(df, is_global=False)
    m_trend_g, b_share_g, b_total_g, p_analysis_g, p_top_g, lifecycle_g = get_summaries(df, is_global=True)
    
    # -------------------------------------------------------------
    # 7. Site Overview Stats (For Marketplace Summary Table)
    # -------------------------------------------------------------
    print("Computing site overview stats...")
    site_stats = []
    total_global_revenue = df['revenue'].sum()
    
    for site, group in df.groupby('market_cn'):
        site_rev = group['revenue'].sum()
        site_units = group['units'].sum()
        site_asins = group['asin'].nunique()
        
        hl_group = group[group['brand_norm'] == 'Hollyland']
        hl_rev = hl_group['revenue'].sum()
        hl_share = hl_rev / site_rev * 100 if site_rev > 0 else 0
        
        site_stats.append({
            'market': site,
            'revenue': round(float(site_rev), 2),
            'units': int(site_units),
            'asin_count': int(site_asins),
            'rev_share': round(site_rev / total_global_revenue * 100, 2) if total_global_revenue > 0 else 0,
            'hollyland_rev': round(float(hl_rev), 2),
            'hollyland_share': round(float(hl_share), 2)
        })
        
    # Global row for site stats
    global_hl_rev = df[df['brand_norm'] == 'Hollyland']['revenue'].sum()
    global_hl_share = global_hl_rev / total_global_revenue * 100 if total_global_revenue > 0 else 0
    site_stats.append({
        'market': 'GLOBAL',
        'revenue': round(float(total_global_revenue), 2),
        'units': int(df['units'].sum()),
        'asin_count': int(df['asin'].nunique()),
        'rev_share': 100.0,
        'hollyland_rev': round(float(global_hl_rev), 2),
        'hollyland_share': round(float(global_hl_share), 2)
    })
    
    # -------------------------------------------------------------
    # 8. Site Trends (For Line Chart)
    # -------------------------------------------------------------
    print("Computing monthly site trends...")
    site_trend = []
    # Identify top 5 sites
    top_sites = [s['market'] for s in sorted(site_stats, key=lambda x: x['revenue'], reverse=True) if s['market'] != 'GLOBAL'][:5]
    
    trend_group = df[df['market_cn'].isin(top_sites)].groupby(['market_cn', 'fetched_month']).agg({'revenue': 'sum'}).reset_index()
    for _, trow in trend_group.iterrows():
        site_trend.append({
            'market': trow['market_cn'],
            'fetched_month': trow['fetched_month'],
            'revenue': round(float(trow['revenue']), 2)
        })
        
    # -------------------------------------------------------------
    # 9. Price Sensitivity Heatmap (Brands vs. Tiers)
    # -------------------------------------------------------------
    print("Computing price heatmap matrix...")
    heatmap_data = []
    # Identify top 15 brands globally
    top_brands = df.groupby('brand_norm')['revenue'].sum().sort_values(ascending=False).head(15).index.tolist()
    
    price_tiers = ['<$50', '$50-100', '$100-200', '$200-500', '>$500']
    
    for brand in top_brands:
        brand_df = df[df['brand_norm'] == brand]
        brand_tier_revs = brand_df.groupby('price_segment')['revenue'].sum().to_dict()
        
        row_dict = {'brand': brand}
        for tier in price_tiers:
            row_dict[tier] = round(float(brand_tier_revs.get(tier, 0)), 2)
        heatmap_data.append(row_dict)
        
    # -------------------------------------------------------------
    # 10. Forecast Data & 11. Seasonality Data
    # -------------------------------------------------------------
    print("Computing forecast and seasonality...")
    forecast_data = []
    seasonality_data = []
    
    # Predict for GLOBAL and Top 5 sites, and for Hollyland brand
    target_groups = [('GLOBAL', df)] + [(s, df[df['market_cn'] == s]) for s in top_sites] + [('Hollyland', df[df['brand_norm'] == 'Hollyland'])]
    
    for group_name, group_df in target_groups:
        if group_df.empty:
            continue
            
        m_rev = group_df.groupby('fetched_month')['revenue'].sum().reset_index().sort_values('fetched_month')
        if len(m_rev) < 3:
            continue
            
        # Add actual values
        for _, mrow in m_rev.iterrows():
            forecast_data.append({
                'market': group_name,
                'fetched_month': mrow['fetched_month'],
                'revenue': round(float(mrow['revenue']), 2),
                'lower_ci': round(float(mrow['revenue']), 2),
                'upper_ci': round(float(mrow['revenue']), 2),
                'type': 'Actual'
            })
            
        # Run linear trend forecast
        predictions = run_linear_forecast(m_rev['fetched_month'].tolist(), m_rev['revenue'].tolist())
        if predictions:
            for pred in predictions:
                pred['market'] = group_name
                forecast_data.append(pred)
                
        # Compute monthly seasonality (Average revenue for month index 1..12)
        m_rev['month_num'] = pd.to_datetime(m_rev['fetched_month'] + '-01').dt.month
        month_names = {
            1: 'Jan', 2: 'Feb', 3: 'Mar', 4: 'Apr', 5: 'May', 6: 'Jun',
            7: 'Jul', 8: 'Aug', 9: 'Sep', 10: 'Oct', 11: 'Nov', 12: 'Dec'
        }
        
        for m_num, m_group in m_rev.groupby('month_num'):
            avg_rev = m_group['revenue'].mean()
            seasonality_data.append({
                'market': group_name,
                'month_num': int(m_num),
                'month_name': month_names[m_num],
                'avg_revenue': round(float(avg_rev), 2)
            })

    # Combine into a single JSON-serializable dictionary
    summary = {
        "updated_at": datetime.now().isoformat(),
        "market_trend": pd.concat([m_trend_l, m_trend_g]).to_dict(orient='records'),
        "brand_share": pd.concat([b_share_l, b_share_g]).to_dict(orient='records'),
        "brand_total_share": pd.concat([b_total_l, b_total_g]).to_dict(orient='records'),
        "price_analysis": pd.concat([p_analysis_l, p_analysis_g]).to_dict(orient='records'),
        "price_top_brands": p_top_l + p_top_g,
        "lifecycle_performance": pd.concat([lifecycle_l, lifecycle_g]).to_dict(orient='records'),
        "site_stats": site_stats,
        "site_trend": site_trend,
        "heatmap_data": heatmap_data,
        "forecast_data": forecast_data,
        "seasonality_data": seasonality_data
    }
    
    return summary

def main():
    print("开始全局大盘多维数据分析...")
    records = load_all_data()
    print(f"数据加载完成，共读取了 {len(records)} 条原始条目。")
    
    if not records:
        print("未在 data/ 中检索到有效的年度 JSON 数据。")
        return
        
    summary = analyze_data(records)
    
    with open(ANALYTICS_FILE, 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
        
    print(f"\n[Success] 数据分析圆满结束，编译好的数据已保存至 '{ANALYTICS_FILE}'")

if __name__ == "__main__":
    main()
