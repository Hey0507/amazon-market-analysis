import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path

# Page config
st.set_page_config(page_title="Amazon Market Analysis BI", layout="wide")

# Custom Color Palette for better visibility
COLOR_PALETTE = px.colors.qualitative.Bold

# Load CSS
with open('style.css') as f:
    st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

@st.cache_data
def load_data():
    if Path('processed_market_data.pkl').exists():
        df = pd.read_pickle('processed_market_data.pkl')
        # Ensure numerical types
        df['销量'] = pd.to_numeric(df['销量'], errors='coerce')
        df['销售额'] = pd.to_numeric(df['销售额'], errors='coerce')
        return df
    return pd.DataFrame()

df = load_data()

if df.empty:
    st.error("未找到处理后的数据，请先运行采集和处理脚本。")
    st.stop()

# Sidebar
st.sidebar.title("🔍 市场过滤器")
st.sidebar.info("🚀 **V3 更新**: 已合并 HollyView 至 Hollyland，且整合了所有相关品类数据。")
# Removed category filter for V3 (Combined Market)
selected_brands = st.sidebar.multiselect("品牌", options=df['品牌'].unique())
price_tiers_order = ['0-30', '30-50', '50-100', '100-150', '150+']
available_tiers = sorted(df['价格区间'].unique(), key=lambda x: price_tiers_order.index(x) if x in price_tiers_order else 99)
price_tiers = st.sidebar.multiselect("价格区间", options=available_tiers, default=available_tiers)

# Filtering
mask = df['价格区间'].isin(price_tiers)
if selected_brands:
    mask = mask & df['品牌'].isin(selected_brands)
filtered_df = df[mask].copy()

# Header
st.title("🚀 Amazon 市场深度洞察看板 (V3 - 统一市场版)")
st.markdown("---")

# Metrics
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("总销量", f"{filtered_df['销量'].sum():,.0f}")
with col2:
    st.metric("总销售额", f"${filtered_df['销售额'].sum():,.0f}")
with col3:
    st.metric("覆盖 ASIN 数", f"{filtered_df['ASIN'].nunique()}")
with col4:
    st.metric("市场均价", f"${filtered_df['价格'].mean():.2f}")

# --- Row 1: Trend & Overall Brand Share ---
row1_col1, row1_col2 = st.columns([2, 1])

with row1_col1:
    st.subheader("📈 市场销售趋势分析 (按月)")
    
    # 1. Total Market Trend
    total_trend = filtered_df.groupby(['月份'])['销售额'].sum().reset_index()
    total_trend.rename(columns={'销售额': '全市场销售额'}, inplace=True)
    
    # 2. Hollyland Trend
    hollyland_df = filtered_df[filtered_df['品牌'] == 'Hollyland']
    hollyland_trend = hollyland_df.groupby(['月份'])['销售额'].sum().reset_index()
    hollyland_trend.rename(columns={'销售额': 'Hollyland销售额'}, inplace=True)
    
    # 3. Merge and Calculate Percentage
    trend_df = pd.merge(total_trend, hollyland_trend, on='月份', how='left').fillna(0)
    trend_df['Hollyland占比'] = (trend_df['Hollyland销售额'] / trend_df['全市场销售额'] * 100).round(1)
    
    # 4. Plot
    fig_trend = go.Figure()
    
    # Total Market Line
    fig_trend.add_trace(go.Scatter(
        x=trend_df['月份'], y=trend_df['全市场销售额'],
        mode='lines+markers',
        name='全市场',
        line=dict(color='#2563eb', width=3, shape='spline'),
        hovertemplate='全市场: $%{y:,.0f}<extra></extra>'
    ))
    
    # Hollyland Line
    fig_trend.add_trace(go.Scatter(
        x=trend_df['月份'], y=trend_df['Hollyland销售额'],
        mode='lines+markers+text',
        name='Hollyland',
        line=dict(color='#e11d48', width=3, shape='spline'),
        text=trend_df['Hollyland占比'].astype(str) + '%',
        textposition='top center',
        textfont=dict(color='#e11d48', size=11, weight='bold'),
        hovertemplate='Hollyland: $%{y:,.0f}<br>占比: %{text}<extra></extra>'
    ))
    
    fig_trend.update_layout(
        title='全市场 vs Hollyland 月度销售趋势',
        template='plotly_white',
        plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
        font=dict(size=13, color="#334155"),
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    st.plotly_chart(fig_trend, use_container_width=True)

with row1_col2:
    st.subheader("📊 Top 10 品牌市场份额")
    brand_df = filtered_df.groupby('品牌')['销售额'].sum().sort_values(ascending=False).head(10).reset_index()
    fig_brand = px.pie(brand_df, values='销售额', names='品牌', 
                        template='plotly_white',
                        hole=0.4, color_discrete_sequence=COLOR_PALETTE)
    fig_brand.update_traces(
        textinfo='label+percent', 
        textposition='outside', 
        insidetextorientation='radial',
        marker=dict(line=dict(color='#ffffff', width=2))
    )
    fig_brand.update_layout(
        showlegend=False, 
        margin=dict(t=40, b=40, l=20, r=20),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(size=13, color="#334155")
    )
    st.plotly_chart(fig_brand, use_container_width=True)

# --- Row 2: Price Segment Analysis ---
st.markdown("---")
st.header("💰 价位段深度分析")
row2_col1, row2_col2 = st.columns(2)

with row2_col1:
    st.subheader("🛒 各价位段销售规模")
    price_metrics = filtered_df.groupby('价格区间')[['销量', '销售额']].sum().reindex(price_tiers_order).dropna().reset_index()
    fig_price_metrics = go.Figure()
    fig_price_metrics.add_trace(go.Bar(x=price_metrics['价格区间'], y=price_metrics['销售额'], name='销售额', marker_color='#3b82f6'))
    fig_price_metrics.add_trace(go.Scatter(x=price_metrics['价格区间'], y=price_metrics['销量'], name='销量', yaxis='y2', line=dict(color='#10b981', width=3)))
    
    fig_price_metrics.update_layout(
        title='价位段销量 vs 销售额',
        template='plotly_white',
        yaxis=dict(title='销售额 (USD)', side='left'),
        yaxis2=dict(title='销量 (Units)', side='right', overlaying='y'),
        legend=dict(x=0.01, y=0.99),
        plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color="#334155")
    )
    st.plotly_chart(fig_price_metrics, use_container_width=True)

with row2_col2:
    # Calculate latest complete quarter
    filtered_df['Date'] = pd.to_datetime(filtered_df['月份'])
    filtered_df['YearQuarter'] = filtered_df['Date'].dt.to_period('Q')
    
    quarter_month_counts = filtered_df.groupby('YearQuarter')['月份'].nunique()
    complete_quarters = quarter_month_counts[quarter_month_counts == 3].index
    
    if not complete_quarters.empty:
        latest_q = complete_quarters.max()
    else:
        latest_q = filtered_df['YearQuarter'].max()
        
    st.subheader(f"🏆 价位段内各品牌占比 ({latest_q})")
    
    q_df = filtered_df[filtered_df['YearQuarter'] == latest_q]
    price_tiers_list = price_metrics['价格区间'].tolist()
    brand_ratio_data = []
    
    for tier in price_tiers_list:
        tier_df = q_df[q_df['价格区间'] == tier]
        total_tier_rev = tier_df['销售额'].sum()
        
        if total_tier_rev > 0:
            brand_revs = tier_df.groupby('品牌')['销售额'].sum().sort_values(ascending=False).head(5)
            for brand, rev in brand_revs.items():
                ratio = (rev / total_tier_rev) * 100
                brand_ratio_data.append({
                    '价格区间': tier,
                    '品牌': brand,
                    '占比': ratio,
                    '销售额': rev
                })
                
    if brand_ratio_data:
        chart_df = pd.DataFrame(brand_ratio_data)
        chart_df['Label'] = chart_df['品牌'] + '<br>' + chart_df['占比'].round(1).astype(str) + '%'
        
        fig_conc = px.bar(chart_df, x='价格区间', y='占比', color='品牌',
                           title=f'各价位段 Top 5 品牌占比 - 最新完整季度 ({latest_q})',
                           text='Label', template='plotly_white',
                           color_discrete_sequence=COLOR_PALETTE)
        
        fig_conc.update_traces(
            textposition='inside',
            insidetextanchor='middle',
            hovertemplate='<b>%{x}</b><br>品牌: %{color}<br>占比: %{y:.1f}%<br>销售额: $%{customdata[0]:,.0f}<extra></extra>',
            customdata=chart_df[['销售额']],
            textfont=dict(color='white')
        )
        
        fig_conc.update_layout(
            plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', 
            font=dict(color="#334155"),
            yaxis_title="占该价位段份额 (%)",
            barmode='stack',
            showlegend=False
        )
        st.plotly_chart(fig_conc, use_container_width=True)
    else:
        st.info("该季度暂无数据")

# --- Row 3: Segment Leaderboard ---
st.markdown("---")
st.subheader("🥇 各价位段品牌领跑者 (Top 5)")
leaderboard_cols = st.columns(len(price_tiers_list))

for i, tier in enumerate(price_tiers_list):
    with leaderboard_cols[i]:
        st.markdown(f"**{tier} USD**")
        tier_brands = filtered_df[filtered_df['价格区间'] == tier].groupby('品牌')['销售额'].sum().sort_values(ascending=False).head(5)
        if not tier_brands.empty:
            for rank, (brand, rev) in enumerate(tier_brands.items(), 1):
                st.caption(f"{rank}. {brand} (${rev/1e6:.1f}M)")
        else:
            st.caption("暂无数据")

# --- Row 3: Geo & Details ---
st.markdown("---")
row3_col1, row3_col2 = st.columns([1, 2])

with row3_col1:
    st.subheader("🌍 卖家地区分布")
    geo_df = filtered_df.groupby('地区')['ASIN'].nunique().sort_values(ascending=False).reset_index()
    fig_geo = px.bar(geo_df, x='地区', y='ASIN', 
                      title='各地区 ASIN 数量', template='plotly_white',
                      color='地区', color_discrete_sequence=COLOR_PALETTE)
    fig_geo.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font=dict(color="#334155"))
    st.plotly_chart(fig_geo, use_container_width=True)

with row3_col2:
    st.subheader("📋 原始数据明细")
    st.dataframe(filtered_df.sort_values(by='销售额', ascending=False).head(100), use_container_width=True)

# Download
csv = filtered_df.to_csv(index=False).encode('utf-8-sig')
st.download_button(
    label="📥 下载完整筛选数据 (CSV)",
    data=csv,
    file_name='amazon_market_analysis_optimized.csv',
    mime='text/csv',
)
