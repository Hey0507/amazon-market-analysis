"""
chart_components.py - Premium Plotly chart components for Amazon Market Analysis
"""

import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

# --- Premium Color Palette ---
COLOR_PALETTE = {
    'primary': '#2563eb',    # Royal Blue
    'secondary': '#10b981',  # Emerald
    'accent': '#f43f5e',     # Rose
    'warning': '#f59e0b',    # Amber
    'neutral': '#64748b',    # Slate
    'background': '#ffffff',
    'grid': '#f1f5f9'
}

# Standard layout configuration for a clean, premium look
PREMIUM_LAYOUT = dict(
    template='plotly_white',
    font=dict(family='Inter, "Segoe UI", Roboto, sans-serif', size=12),
    margin=dict(l=40, r=40, t=60, b=40),
    plot_bgcolor='rgba(0,0,0,0)',
    paper_bgcolor='rgba(0,0,0,0)',
    xaxis=dict(gridcolor=COLOR_PALETTE['grid'], showline=False),
    yaxis=dict(gridcolor=COLOR_PALETTE['grid'], showline=False),
)

def create_site_distribution_chart(site_stats_df):
    """
    Create site distribution visualization (Donut + Bar)
    """
    # Pie chart (Donut)
    pie_fig = px.pie(
        site_stats_df,
        values='总销售额',
        names='站点',
        title='全球市场份额 (销售额)',
        hole=0.5,
        color_discrete_sequence=px.colors.qualitative.Prism
    )
    pie_fig.update_layout(**PREMIUM_LAYOUT, height=450)
    pie_fig.update_traces(
        textposition='outside',
        textinfo='label+percent',
        marker=dict(line=dict(color='#FFFFFF', width=2)),
        hovertemplate='<b>%{label}</b><br>销售额: $%{value:,.0f}<br>份额: %{percent}<extra></extra>'
    )

    # Bar chart
    top_sites = site_stats_df.head(10).sort_values('总销售额', ascending=True)
    bar_fig = px.bar(
        top_sites,
        y='站点',
        x='总销售额',
        orientation='h',
        title='各站点市场销售额 (Top 10)',
        color='总销售额',
        color_continuous_scale='Blues',
        text='总销售额'
    )
    bar_fig.update_layout(**PREMIUM_LAYOUT, height=450, showlegend=False)
    bar_fig.update_traces(
        texttemplate='$%{text:,.0s}',
        textposition='outside',
        marker_color=COLOR_PALETTE['primary'],
        hovertemplate='<b>%{y}</b><br>销售额: $%{x:,.0f}<extra></extra>'
    )
    bar_fig.update_coloraxes(showscale=False)

    return pie_fig, bar_fig

def create_top_sites_trend_chart(trend_df, top_sites):
    """
    Multi-line trend chart with area fill and premium styling
    """
    fig = go.Figure()
    site_colors = ['#2563eb', '#10b981', '#f43f5e', '#8b5cf6', '#f59e0b']

    for i, site in enumerate(top_sites):
        site_data = trend_df[trend_df['站点'] == site].sort_values('月份')
        color = site_colors[i % len(site_colors)]

        fig.add_trace(go.Scatter(
            x=site_data['月份'],
            y=site_data['销售额'],
            mode='lines+markers',
            name=site,
            line=dict(color=color, width=3),
            marker=dict(size=8, symbol='circle', line=dict(color='white', width=1)),
            fill='tozeroy' if i == 0 else None,
            fillcolor=f'rgba({int(color[1:3], 16)}, {int(color[3:5], 16)}, {int(color[5:7], 16)}, 0.1)',
            hovertemplate='<b>' + site + '</b><br>月份: %{x}<br>销售额: $%{y:,.0f}<extra></extra>'
        ))

    fig.update_layout(**PREMIUM_LAYOUT, height=500, title='Top 5 站点: 销售额增长趋势', 
                      legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
                      hovermode='x unified')
    return fig

def create_brand_share_chart(df, metric='销售额', top_n=10):
    """
    Treemap for brand market share distribution.
    """
    brand_data = df.groupby('品牌')[metric].sum().reset_index()
    brand_data = brand_data.sort_values(metric, ascending=False)
    
    top_brands = brand_data.head(top_n).copy()
    others_val = brand_data.iloc[top_n:][metric].sum()
    if others_val > 0:
        others_df = pd.DataFrame([{'品牌': '其他 (Others)', metric: others_val}])
        top_brands = pd.concat([top_brands, others_df], ignore_index=True)
    
    fig = px.treemap(
        top_brands,
        path=[px.Constant("全量市场"), '品牌'],
        values=metric,
        color=metric,
        color_continuous_scale='Blues',
        title=f'各品牌市场份额分布 ({metric})',
    )
    
    fig.update_layout(**PREMIUM_LAYOUT, height=500)
    fig.update_traces(
        textinfo="label+percent parent",
        hovertemplate='<b>%{label}</b><br>' + metric + ': $%{value:,.0f}<extra></extra>'
    )
    fig.update_coloraxes(showscale=False)
    
    return fig

def create_product_lifecycle_chart(lifecycle_df):
    """
    Stacked area chart showing sales contribution of new vs old products.
    """
    fig = px.area(
        lifecycle_df,
        x='月份',
        y='销售额',
        color='产品生命周期',
        title='新老产品销售额贡献趋势 (新品定义：近6个月内上架)',
        color_discrete_map={'新品 (New)': '#10b981', '老品 (Old)': '#64748b'},
        category_orders={'产品生命周期': ['老品 (Old)', '新品 (New)']}
    )
    
    fig.update_layout(**PREMIUM_LAYOUT, height=450)
    fig.update_xaxes(title='月份')
    fig.update_yaxes(title='销售额 ($)', tickformat='$,.0s')
    fig.update_traces(hovertemplate='<b>%{fullData.name}</b><br>月份: %{x}<br>销售额: $%{y:,.0f}<extra></extra>')
    
    return fig

def create_competitor_positioning(benchmark_df):
    """
    Brand Positioning Map (Bubble Chart): Avg Price vs Total Units
    """
    fig = px.scatter(
        benchmark_df,
        x='平均价格',
        y='总销量',
        size='总销售额',
        color='平均评分',
        hover_name='品牌',
        text='品牌',
        color_continuous_scale='RdYlGn',
        title='品牌竞争定位矩阵 (价格 vs 销量 vs 销售额)'
    )

    fig.update_traces(textposition='top center', marker=dict(line=dict(width=1, color='rgba(0,0,0,0.3)')), opacity=0.85)

    avg_price = benchmark_df['平均价格'].median()
    avg_units = benchmark_df['总销量'].median()
    fig.add_vline(x=avg_price, line_dash="dot", line_color=COLOR_PALETTE['neutral'], opacity=0.3)
    fig.add_hline(y=avg_units, line_dash="dot", line_color=COLOR_PALETTE['neutral'], opacity=0.3)

    fig.update_layout(**PREMIUM_LAYOUT, height=600, xaxis_title='平均价格 ($)', yaxis_title='总销量 (Units)',
                      coloraxis_colorbar=dict(title="评分"))
    return fig

def create_market_share_trend_chart(trend_df, brand='Hollyland'):
    """
    Dual-axis combo chart: Market Total vs Brand Share %
    """
    share_col = f'{brand}市占率'
    rev_col = f'{brand}销售额'

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=trend_df['月份'], y=trend_df['总销售额'], name='大盘总计',
        marker=dict(color='#f1f5f9', line=dict(color='#cbd5e1', width=0.5)),
        yaxis='y', hovertemplate='<b>%{x}</b><br>大盘总额: $%{y:,.0f}<extra></extra>'
    ))

    fig.add_trace(go.Scatter(
        x=trend_df['月份'], y=trend_df[rev_col], name=f'{brand} 销售额',
        mode='lines+markers', line=dict(color='#f43f5e', width=3),
        marker=dict(size=8, symbol='circle', line=dict(color='white', width=2)),
        yaxis='y', hovertemplate=f'<b>%{{x}}</b><br>{brand}销售额: $%{{y:,.0f}}<extra></extra>'
    ))

    fig.add_trace(go.Scatter(
        x=trend_df['月份'], y=trend_df[share_col], name=f'{brand} 市占率 %',
        mode='lines+markers+text', line=dict(color='#1d4ed8', width=3, dash='dot'),
        marker=dict(size=9, symbol='diamond', line=dict(color='white', width=2)),
        text=[f'{v:.1f}%' if v > 0 else '' for v in trend_df[share_col]],
        textposition='top center', yaxis='y2',
        hovertemplate=f'<b>%{{x}}</b><br>{brand}份额: %{{y:.2f}}%<extra></extra>'
    ))

    max_share = max(trend_df[share_col].max() * 1.5, 15)
    fig.update_layout(**PREMIUM_LAYOUT, height=500, title=f'📈 市场趋势与 {brand} 份额表现', 
                      barmode='overlay', hovermode='x unified',
                      yaxis=dict(title='销售额 ($)', gridcolor=COLOR_PALETTE['grid'], tickformat='$,.0s'),
                      yaxis2=dict(title='市占率 (%)', overlaying='y', side='right', ticksuffix='%', range=[0, max_share], 
                                  showgrid=False, tickfont=dict(color='#1d4ed8')))
    return fig

def create_price_tier_brand_chart(tier_brand_df, top_n=5):
    """
    Stacked horizontal bar for price tiers
    """
    if tier_brand_df.empty: return go.Figure()
    tiers_present = sorted(tier_brand_df['价格区间'].unique())
    all_brands = tier_brand_df['品牌'].unique().tolist()
    if 'Hollyland' in all_brands:
        all_brands.remove('Hollyland')
        all_brands = ['Hollyland'] + all_brands
    if '其他 (Others)' in all_brands:
        all_brands.remove('其他 (Others)')
        all_brands.append('其他 (Others)')

    fig = go.Figure()
    colors = px.colors.qualitative.Prism
    color_map = {}
    for i, b in enumerate(all_brands):
        if b == 'Hollyland': color_map[b] = '#f43f5e'
        elif '其他' in b: color_map[b] = '#cbd5e1'
        else: color_map[b] = colors[i % len(colors)]

    for brand in all_brands:
        brand_data = tier_brand_df[tier_brand_df['品牌'] == brand]
        shares = [brand_data[brand_data['价格区间'] == tier]['份额'].values[0] * 100 if len(brand_data[brand_data['价格区间'] == tier]) > 0 else 0 for tier in tiers_present]
        fig.add_trace(go.Bar(name=brand, y=tiers_present, x=shares, orientation='h', marker_color=color_map.get(brand)))

    fig.update_layout(**PREMIUM_LAYOUT, height=500, title=f'🏷️ 价格带竞争格局 (Top {top_n} 品牌占有率)', 
                      barmode='stack', xaxis_title='份额 (%)', yaxis_title='价格区间 ($)')
    return fig

def create_heatmap(pivot_df, title="价格与品牌敏感度热力图"):
    fig = go.Figure(go.Heatmap(
        z=pivot_df.values, x=pivot_df.columns, y=pivot_df.index,
        colorscale=[[0, '#f8fafc'], [0.1, '#dbeafe'], [1, '#1e40af']], showscale=True
    ))
    fig.update_layout(**PREMIUM_LAYOUT, title=title, height=550, xaxis_title='价格区间', yaxis_title='品牌')
    return fig

def create_forecast_chart(forecast_df, historical_df, brand_name='Market Total'):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=historical_df['月份'], y=historical_df['销售额'], mode='lines+markers', name='历史数据'))
    if not forecast_df.empty:
        fig.add_trace(go.Scatter(x=forecast_df['月份'], y=forecast_df['预测销售额'], mode='lines+markers', name='预测数据', line=dict(dash='dot')))
    fig.update_layout(**PREMIUM_LAYOUT, height=500, title=f'未来6个月销售额预测 – {brand_name}', hovermode='x unified')
    return fig
