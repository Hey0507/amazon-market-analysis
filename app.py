import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path

# ── 页面配置 ──────────────────────────────────────────────────────
st.set_page_config(
    page_title="Amazon 无线麦克风市场分析",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── 调色板 ────────────────────────────────────────────────────────
COLORS = [
    '#2563eb', '#e11d48', '#10b981', '#f59e0b', '#8b5cf6',
    '#06b6d4', '#ec4899', '#14b8a6', '#f97316', '#6366f1',
    '#84cc16', '#ef4444', '#0ea5e9', '#d946ef', '#78716c'
]

CHART_LAYOUT = dict(
    template='plotly_white',
    plot_bgcolor='rgba(0,0,0,0)',
    paper_bgcolor='rgba(0,0,0,0)',
    font=dict(family='Inter, PingFang SC, Microsoft YaHei, sans-serif',
              size=12, color='#334155'),
    hoverlabel=dict(bgcolor='white', bordercolor='#e2e8f0',
                    font=dict(size=12, color='#1e293b')),
)

# ── CSS ───────────────────────────────────────────────────────────
with open('style.css') as f:
    st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

# ── 数据加载 ──────────────────────────────────────────────────────
@st.cache_data(ttl=300)
def load_data():
    if not Path('processed_market_data.pkl').exists():
        return pd.DataFrame()
    df = pd.read_pickle('processed_market_data.pkl')
    df['销量']  = pd.to_numeric(df['销量'],  errors='coerce').fillna(0)
    df['销售额'] = pd.to_numeric(df['销售额'], errors='coerce').fillna(0)
    df['价格']  = pd.to_numeric(df['价格'],  errors='coerce').fillna(0)
    df['评分']  = pd.to_numeric(df['评分'],  errors='coerce').fillna(0)
    df['month_dt'] = pd.to_datetime(df['月份'], errors='coerce')
    df['季度'] = df['month_dt'].dt.to_period('Q')
    return df

df_raw = load_data()

if df_raw.empty:
    st.error("未找到数据，请先运行 final_processor.py")
    st.stop()

# ── 季度选择辅助（多市场覆盖优先） ───────────────────────────────
def best_quarter_for_market(df, min_markets=2):
    """选取覆盖站点数最多的季度，同时保证是3个月完整季度。"""
    q_month_cnt = df.groupby('季度')['月份'].nunique()
    q_site_cnt  = df.groupby('季度')['站点'].nunique()
    complete    = q_month_cnt[q_month_cnt >= 3].index   # ≥3个月
    if complete.empty:
        return df['季度'].max()
    # 在完整季度中，选覆盖站点最多的（最近的优先）
    scored = q_site_cnt[q_site_cnt.index.isin(complete)].sort_values(ascending=False)
    top_cnt = scored.iloc[0]
    # 如果有多个季度覆盖相同站点数，取最近的
    candidates = scored[scored == top_cnt].index
    return max(candidates)

# ── Sidebar ───────────────────────────────────────────────────────
st.sidebar.title("🔍 筛选器")

# 站点多选
all_sites = sorted(df_raw['站点'].unique())
selected_sites = st.sidebar.multiselect(
    "🌍 站点", options=all_sites, default=all_sites,
    help="选择需要分析的市场站点"
)

# 品牌多选
all_brands = sorted(df_raw['品牌'].unique())
selected_brands = st.sidebar.multiselect(
    "🏷️ 品牌", options=all_brands,
    help="留空=全部品牌"
)

# 价格区间
price_order = ['0-30', '30-50', '50-100', '100-150', '150+']
avail_tiers = [t for t in price_order if t in df_raw['价格区间'].unique()]
price_tiers = st.sidebar.multiselect(
    "💰 价格区间 (USD)", options=avail_tiers, default=avail_tiers
)

# 卖家来源地区多选
all_regions = sorted(df_raw['地区'].dropna().unique())
selected_regions = st.sidebar.multiselect(
    "🌏 卖家来源地区", options=all_regions, default=all_regions,
    help="选择卖家的国别地区，例如 CN (中国), US (美国), JP (日本)"
)

# 月份范围
all_months = sorted(df_raw['月份'].unique())
month_range = st.sidebar.select_slider(
    "📅 月份范围",
    options=all_months,
    value=(all_months[0], all_months[-1])
)

st.sidebar.markdown("---")
st.sidebar.info(
    "**V5.2 领夹式无线麦专业版**\n"
    "- 仅包含便携领夹式数字无线系统，已剔除全部手持/舞台话筒及配件\n"
    "- 价格/销售额已转换为税前 USD\n"
    "- 动态销量阈值：US≥200，英/德/日≥80，其他≥50\n"
    "- 已合并 HollyView → Hollyland\n"
    f"- 完整统计周期：{all_months[0]} ~ {all_months[-1]}\n"
    "- 站点对齐对比周期：2024-12 ~ 2026-04"
)

# ── 数据过滤 ──────────────────────────────────────────────────────
mask = (
    df_raw['价格区间'].isin(price_tiers) &
    df_raw['站点'].isin(selected_sites if selected_sites else all_sites) &
    df_raw['地区'].isin(selected_regions if selected_regions else all_regions) &
    df_raw['月份'].between(month_range[0], month_range[1])
)
if selected_brands:
    mask = mask & df_raw['品牌'].isin(selected_brands)

df = df_raw[mask].copy()

if df.empty:
    st.warning("当前筛选条件下无数据，请调整筛选器。")
    st.stop()

# ── Header ────────────────────────────────────────────────────────
st.markdown(f"""
<div style='background:linear-gradient(135deg,#1e3a5f 0%,#2563eb 100%);
     padding:28px 32px;border-radius:16px;margin-bottom:24px;'>
  <h1 style='color:white;margin:0;font-size:1.8rem;font-weight:700;'>
    🎙️ Amazon 便携领夹无线麦克风市场深度洞察
  </h1>
  <p style='color:rgba(255,255,255,0.85);margin:6px 0 0;font-size:0.95rem;font-weight:500;'>
    全量统计周期: {all_months[0]} ~ {all_months[-1]} (25个月)  |  多站点对齐周期: 2024-12 ~ 2026-04 (17个月)  |  V5.2 专业纯净版
  </p>
</div>
""", unsafe_allow_html=True)

# ── KPI 卡片 ──────────────────────────────────────────────────────
total_rev   = df['销售额'].sum()
total_vol   = df['销量'].sum()
total_asins = df['ASIN'].nunique()
avg_price   = df['价格'].mean()
brands_cnt  = df['品牌'].nunique()
hl_rev      = df[df['品牌'] == 'Hollyland']['销售额'].sum()
hl_share    = hl_rev / total_rev * 100 if total_rev > 0 else 0
avg_lqs     = df['lqs'].dropna().mean() if 'lqs' in df.columns else 0

c1, c2, c3, c4, c5, c6, c7 = st.columns(7)
kpi_style = lambda val, sub: f"<div style='text-align:center'><div style='font-size:1.6rem;font-weight:700;color:#1e293b'>{val}</div><div style='font-size:0.75rem;color:#64748b;margin-top:4px'>{sub}</div></div>"

with c1: st.metric("📦 总销量",    f"{total_vol:,.0f}", help="所有筛选条件下的月度销量合计")
with c2: st.metric("💵 总销售额",  f"${total_rev/1e6:.1f}M", help="税前 USD 销售额")
with c3: st.metric("🔑 覆盖ASIN", f"{total_asins:,}")
with c4: st.metric("💲 均价",      f"${avg_price:.0f}", help="税前 USD 均价")
with c5: st.metric("🏷️ 品牌数",   f"{brands_cnt}")
with c6: st.metric("🎯 平均 LQS",  f"{avg_lqs:.1f}" if avg_lqs > 0 else "N/A", help="详情页质量分 (LQS) 平均值")
with c7: st.metric("🔴 Hollyland占比", f"{hl_share:.1f}%", delta=f"${hl_rev/1e6:.1f}M")

st.markdown("---")

# ══════════════════════════════════════════════════════════════════
# Section 1: 月度销售趋势
# ══════════════════════════════════════════════════════════════════
st.subheader(f"📈 月度销售趋势 — 全市场 vs Hollyland (全量数据周期: {all_months[0]} ~ {all_months[-1]})")

trend_total = df.groupby('月份')[['销售额', '销量']].sum().reset_index().sort_values('月份')
trend_hl    = df[df['品牌'] == 'Hollyland'].groupby('月份')['销售额'].sum().reset_index()
trend_hl.columns = ['月份', 'HL销售额']
trend_df    = trend_total.merge(trend_hl, on='月份', how='left').fillna(0)
trend_df['HL占比'] = (trend_df['HL销售额'] / trend_df['销售额'] * 100).round(1)
trend_df['HL占比_str'] = trend_df['HL占比'].astype(str) + '%'

fig_trend = go.Figure()
fig_trend.add_trace(go.Scatter(
    x=trend_df['月份'], y=trend_df['销售额'],
    mode='lines+markers', name='全市场销售额',
    fill='tozeroy', fillcolor='rgba(37,99,235,0.08)',
    line=dict(color='#2563eb', width=2.5, shape='spline'),
    marker=dict(size=5),
    hovertemplate='<b>%{x}</b><br>全市场: $%{y:,.0f}<extra></extra>'
))
fig_trend.add_trace(go.Scatter(
    x=trend_df['月份'], y=trend_df['HL销售额'],
    mode='lines+markers+text', name='Hollyland',
    line=dict(color='#e11d48', width=2.5, shape='spline'),
    marker=dict(size=5),
    text=trend_df['HL占比_str'],
    textposition='top center',
    textfont=dict(size=9, color='#e11d48'),
    hovertemplate='<b>%{x}</b><br>Hollyland: $%{y:,.0f}<br>占比: %{text}<extra></extra>'
))
fig_trend.update_layout(
    **CHART_LAYOUT,
    height=400,
    hovermode='x unified',
    yaxis=dict(title='销售额 (USD)', tickformat='$,.0f'),
    xaxis=dict(title='', tickangle=-30),
    legend=dict(orientation='h', y=1.08, x=1, xanchor='right'),
    margin=dict(t=60, b=60, l=60, r=20)
)
st.plotly_chart(fig_trend, width='stretch')

# ── 多站点月度趋势（并列） ────────────────────────────────────────
st.markdown("---")
col_t1, col_t2 = st.columns([3, 2])

# 🔑 方案B对齐：对比图表统一使用共有时间段 (2024-12 ~ 2026-04)
df_aligned = df[df['月份'] >= '2024-12']

with col_t1:
    st.subheader("🌐 各站点月度销售额趋势 (对齐周期)")
    st.caption("注：为确保站点间对比公平，已对齐至共有周期 2024-12 ~ 2026-04")
    top5_sites = (df_aligned.groupby('站点')['销售额'].sum()
                  .sort_values(ascending=False).head(5).index.tolist())
    site_trend = (df_aligned[df_aligned['站点'].isin(top5_sites)]
                  .groupby(['站点', '月份'])['销售额'].sum().reset_index())
    fig_site = px.line(
        site_trend, x='月份', y='销售额', color='站点',
        color_discrete_sequence=COLORS,
        markers=True
    )
    fig_site.update_traces(line=dict(width=2), marker=dict(size=4))
    fig_site.update_layout(
        **CHART_LAYOUT,
        height=380,
        yaxis=dict(title='销售额 (USD)', tickformat='$,.0f'),
        xaxis=dict(title='', tickangle=-30),
        legend=dict(orientation='h', y=1.08, x=1, xanchor='right'),
        margin=dict(t=60, b=60, l=60, r=20)
    )
    st.plotly_chart(fig_site, width='stretch')

with col_t2:
    st.subheader("📊 站点销售额占比 (对齐周期)")
    st.caption("注：为确保站点间对比公平，已对齐至共有周期 2024-12 ~ 2026-04")
    site_rev = df_aligned.groupby('站点')['销售额'].sum().sort_values(ascending=False).reset_index()
    site_rev['占比'] = (site_rev['销售额'] / site_rev['销售额'].sum() * 100).round(1)
    fig_site_pie = px.pie(
        site_rev, values='销售额', names='站点',
        hole=0.45, color_discrete_sequence=COLORS
    )
    fig_site_pie.update_traces(
        textinfo='label+percent',
        textposition='outside',
        hovertemplate='<b>%{label}</b><br>$%{value:,.0f}<br>%{percent}<extra></extra>',
        marker=dict(line=dict(color='white', width=1.5))
    )
    fig_site_pie.update_layout(
        **CHART_LAYOUT,
        height=380,
        showlegend=False,
        margin=dict(t=30, b=30, l=20, r=20)
    )
    st.plotly_chart(fig_site_pie, width='stretch')

# ══════════════════════════════════════════════════════════════════
# Section 2: 品牌市场份额
# ══════════════════════════════════════════════════════════════════
st.markdown("---")

# 🔑 关键修复：使用 2026 年统计周期数据
q_df = df[df['月份'].str.startswith('2026')]
q_sites = q_df['站点'].nunique()

st.subheader(f"🏆 品牌市场份额分析 — 2026年统计周期 (2026-01 ~ 2026-04, {q_sites} 个站点)")

col_b1, col_b2 = st.columns([1, 1])

with col_b1:
    # 按销售额的 Top10 品牌饼图
    q_brand_rev = (q_df.groupby('品牌')['销售额'].sum()
                   .sort_values(ascending=False).head(10).reset_index())
    q_brand_rev.columns = ['品牌', '销售额']
    q_total_rev = q_brand_rev['销售额'].sum()
    q_brand_rev['占比'] = (q_brand_rev['销售额'] / q_total_rev * 100).round(1)

    fig_pie = px.pie(
        q_brand_rev, values='销售额', names='品牌',
        hole=0.42, color_discrete_sequence=COLORS,
        title='销售额占比 Top 10'
    )
    fig_pie.update_traces(
        textinfo='label+percent',
        textposition='outside',
        hovertemplate='<b>%{label}</b><br>$%{value:,.0f}<br>%{percent}<extra></extra>',
        marker=dict(line=dict(color='white', width=1.5)),
        textfont=dict(size=10)
    )
    fig_pie.update_layout(
        **CHART_LAYOUT,
        height=420,
        showlegend=False,
        margin=dict(t=50, b=20, l=60, r=60)
    )
    st.plotly_chart(fig_pie, width='stretch')

with col_b2:
    # 品牌销售额横向条形图
    q_brand_bar = (q_df.groupby('品牌')['销售额'].sum()
                   .sort_values(ascending=True).tail(12).reset_index())
    fig_bar = go.Figure(go.Bar(
        x=q_brand_bar['销售额'],
        y=q_brand_bar['品牌'],
        orientation='h',
        marker=dict(
            color=q_brand_bar['销售额'],
            colorscale='Blues',
            showscale=False
        ),
        text=q_brand_bar['销售额'].apply(lambda v: f'${v/1e3:.0f}K' if v < 1e6 else f'${v/1e6:.1f}M'),
        textposition='outside',
        textfont=dict(size=10),
        hovertemplate='<b>%{y}</b><br>销售额: $%{x:,.0f}<extra></extra>'
    ))
    fig_bar.update_layout(
        **CHART_LAYOUT,
        title='品牌销售额排名 Top 12',
        height=420,
        xaxis=dict(title='销售额 (USD)', tickformat='$,.0f'),
        yaxis=dict(title='', automargin=True),
        margin=dict(t=50, b=20, l=20, r=80)
    )
    # Highlight Hollyland
    colors_bar = ['#e11d48' if b == 'Hollyland' else '#3b82f6'
                  for b in q_brand_bar['品牌']]
    fig_bar.data[0].marker.color = colors_bar
    fig_bar.data[0].marker.colorscale = None
    st.plotly_chart(fig_bar, width='stretch')

# ══════════════════════════════════════════════════════════════════
# Section 3: 价位段分析
# ══════════════════════════════════════════════════════════════════
st.markdown("---")
st.header("💰 价位段深度分析")

col_p1, col_p2 = st.columns([1, 1])

with col_p1:
    st.subheader("各价位段销售规模")
    price_metrics = (df.groupby('价格区间')[['销量', '销售额']].sum()
                     .reindex([t for t in price_order if t in df['价格区间'].unique()])
                     .dropna().reset_index())

    fig_price = go.Figure()
    fig_price.add_trace(go.Bar(
        x=price_metrics['价格区间'], y=price_metrics['销售额'],
        name='销售额', marker_color='#3b82f6',
        text=price_metrics['销售额'].apply(lambda v: f'${v/1e6:.1f}M'),
        textposition='outside', textfont=dict(size=10),
        hovertemplate='<b>%{x}</b><br>销售额: $%{y:,.0f}<extra></extra>'
    ))
    fig_price.add_trace(go.Scatter(
        x=price_metrics['价格区间'], y=price_metrics['销量'],
        name='销量', yaxis='y2',
        line=dict(color='#10b981', width=2.5),
        marker=dict(size=8, symbol='circle'),
        hovertemplate='<b>%{x}</b><br>销量: %{y:,.0f}<extra></extra>'
    ))
    fig_price.update_layout(
        **CHART_LAYOUT,
        height=380,
        yaxis=dict(title='销售额 (USD)', tickformat='$,.0f', side='left'),
        yaxis2=dict(title='销量', side='right', overlaying='y',
                    showgrid=False),
        legend=dict(orientation='h', y=1.1, x=1, xanchor='right'),
        margin=dict(t=60, b=40, l=70, r=60),
        bargap=0.35
    )
    st.plotly_chart(fig_price, width='stretch')

with col_p2:
    st.subheader("各价位段均价分布")
    price_detail = (df.groupby('价格区间').agg(
        均价=('价格', 'mean'),
        ASIN数=('ASIN', 'nunique'),
        品牌数=('品牌', 'nunique')
    ).reindex([t for t in price_order if t in df['价格区间'].unique()])
    .dropna().reset_index())

    fig_scatter = go.Figure()
    for i, row in price_detail.iterrows():
        fig_scatter.add_trace(go.Scatter(
            x=[row['价格区间']],
            y=[row['均价']],
            mode='markers+text',
            name=row['价格区间'],
            marker=dict(
                size=max(15, min(50, row['ASIN数'] * 0.5)),
                color=COLORS[i % len(COLORS)],
                opacity=0.85,
                line=dict(color='white', width=2)
            ),
            text=[f"${row['均价']:.0f}"],
            textposition='middle center',
            textfont=dict(color='white', size=9, family='Inter'),
            hovertemplate=(
                f"<b>{row['价格区间']}</b><br>"
                f"均价: ${row['均价']:.2f}<br>"
                f"ASIN数: {int(row['ASIN数'])}<br>"
                f"品牌数: {int(row['品牌数'])}<extra></extra>"
            )
        ))
    fig_scatter.update_layout(
        **CHART_LAYOUT,
        height=380,
        showlegend=False,
        yaxis=dict(title='均价 (USD)', tickformat='$,.0f'),
        xaxis=dict(title='价格区间'),
        margin=dict(t=30, b=40, l=70, r=20)
    )
    st.plotly_chart(fig_scatter, width='stretch')

# ── 价位段品牌占比堆叠图 ─────────────────────────────────────────
st.markdown("---")
st.subheader(f"🏆 各价位段 Top 5 品牌占比 — 2026年统计周期 (2026-01 ~ 2026-04)")

price_tiers_list = [t for t in price_order if t in q_df['价格区间'].unique()]
brand_ratio_data = []
for tier in price_tiers_list:
    tier_df = q_df[q_df['价格区间'] == tier]
    total = tier_df['销售额'].sum()
    if total > 0:
        brand_revs = (tier_df.groupby('品牌')['销售额'].sum()
                      .sort_values(ascending=False).head(5))
        for brand, rev in brand_revs.items():
            brand_ratio_data.append({
                '价格区间': tier, '品牌': brand,
                '占比': rev / total * 100,
                '销售额': rev
            })

if brand_ratio_data:
    chart_df = pd.DataFrame(brand_ratio_data)
    # 🔑 方案B对齐设计：将品牌名称与占比直接合并，换行显示在柱状图切片上
    chart_df['标签'] = chart_df['品牌'] + '<br>' + chart_df['占比'].round(0).astype(int).astype(str) + '%'
    fig_stack = px.bar(
        chart_df, x='价格区间', y='占比', color='品牌',
        text='标签',
        color_discrete_sequence=COLORS,
        barmode='stack'
    )
    fig_stack.update_traces(
        textposition='inside',
        insidetextanchor='middle',
        textfont=dict(color='white', size=9), # slightly smaller for premium fit
        hovertemplate='<b>%{x}</b><br>品牌: %{data.name}<br>占比: %{y:.1f}%<extra></extra>'
    )
    fig_stack.update_layout(
        **CHART_LAYOUT,
        height=420,
        yaxis=dict(title='在该价位段占比 (%)', range=[0, 105]),
        xaxis=dict(title='价格区间 (USD)'),
        showlegend=False, # 隐藏多余图例，提升BI大屏极简美感
        margin=dict(t=40, b=40, l=60, r=20)
    )
    st.plotly_chart(fig_stack, width='stretch')
else:
    st.info(f"⚠️ 2026年统计周期无多站点数据，请查看全时段数据")

# ── 价位段品牌领跑者 ──────────────────────────────────────────────
st.markdown("---")
st.subheader("🥇 各价位段品牌全时段领跑者")
tiers_show = [t for t in price_order if t in df['价格区间'].unique()]
leader_cols = st.columns(len(tiers_show))
for i, tier in enumerate(tiers_show):
    with leader_cols[i]:
        st.markdown(f"**${tier}**")
        tier_brands = (df[df['价格区间'] == tier]
                       .groupby('品牌')['销售额'].sum()
                       .sort_values(ascending=False).head(5))
        for rank, (brand, rev) in enumerate(tier_brands.items(), 1):
            color = '🔴' if brand == 'Hollyland' else f'{rank}.'
            st.caption(f"{color} {brand}\n${rev/1e6:.2f}M")

# ══════════════════════════════════════════════════════════════════
# Section 4: Hollyland 专项
# ══════════════════════════════════════════════════════════════════
st.markdown("---")
st.header("🔴 Hollyland 品牌专项分析")

hl_df = df[df['品牌'] == 'Hollyland']

if hl_df.empty:
    st.warning("当前筛选范围内无 Hollyland 数据")
else:
    col_h1, col_h2, col_h3 = st.columns([2, 1, 1])

    with col_h1:
        st.subheader("Hollyland 月度销售额 & 市场占比")
        hl_monthly = (hl_df.groupby('月份')['销售额'].sum()
                      .reset_index().sort_values('月份'))
        mkt_monthly = (df.groupby('月份')['销售额'].sum()
                       .reset_index().rename(columns={'销售额': '总销售额'}))
        hl_monthly = hl_monthly.merge(mkt_monthly, on='月份', how='left')
        hl_monthly['占比'] = (hl_monthly['销售额'] / hl_monthly['总销售额'] * 100).round(1)

        fig_hl = go.Figure()
        fig_hl.add_trace(go.Bar(
            x=hl_monthly['月份'], y=hl_monthly['销售额'],
            name='Hollyland', marker_color='#e11d48',
            opacity=0.85,
            hovertemplate='<b>%{x}</b><br>销售额: $%{y:,.0f}<extra></extra>'
        ))
        fig_hl.add_trace(go.Scatter(
            x=hl_monthly['月份'], y=hl_monthly['占比'],
            mode='lines+markers+text', name='市场占比',
            yaxis='y2',
            line=dict(color='#1e3a5f', width=2),
            marker=dict(size=5),
            text=hl_monthly['占比'].apply(lambda v: f'{v:.1f}%'),
            textposition='top center',
            textfont=dict(size=8, color='#1e3a5f'),
            hovertemplate='<b>%{x}</b><br>占比: %{y:.1f}%<extra></extra>'
        ))
        fig_hl.update_layout(
            **CHART_LAYOUT,
            height=350,
            yaxis=dict(title='销售额 (USD)', tickformat='$,.0f'),
            yaxis2=dict(title='市场占比 (%)', overlaying='y', side='right',
                        range=[0, 60], showgrid=False),
            xaxis=dict(tickangle=-30),
            legend=dict(orientation='h', y=1.1, x=1, xanchor='right'),
            margin=dict(t=70, b=60, l=70, r=60)
        )
        st.plotly_chart(fig_hl, width='stretch')

    with col_h2:
        st.subheader("站点分布")
        hl_site = (hl_df.groupby('站点')['销售额'].sum()
                   .sort_values(ascending=False).reset_index())
        fig_hl_site = px.pie(
            hl_site, values='销售额', names='站点',
            hole=0.4, color_discrete_sequence=COLORS
        )
        fig_hl_site.update_traces(
            textinfo='label+percent',
            textposition='auto',
            textfont=dict(size=9),
            hovertemplate='<b>%{label}</b><br>$%{value:,.0f}<extra></extra>',
            marker=dict(line=dict(color='white', width=1))
        )
        fig_hl_site.update_layout(
            **CHART_LAYOUT,
            height=320,
            showlegend=False,
            margin=dict(t=20, b=20, l=10, r=10)
        )
        st.plotly_chart(fig_hl_site, width='stretch')

    with col_h3:
        st.subheader("核心指标")
        hl_total_rev = hl_df['销售额'].sum()
        hl_total_vol = hl_df['销量'].sum()
        hl_avg_price = hl_df['价格'].mean()
        hl_avg_rating = hl_df['评分'].replace(0, float('nan')).mean()
        hl_asins = hl_df['ASIN'].nunique()
        mkt_total = df['销售额'].sum()
        hl_mkt_share = hl_total_rev / mkt_total * 100 if mkt_total > 0 else 0

        st.metric("总销售额", f"${hl_total_rev/1e6:.2f}M")
        st.metric("总销量",   f"{hl_total_vol:,.0f}")
        st.metric("市场占比", f"{hl_mkt_share:.1f}%")
        st.metric("ASIN数",  f"{hl_asins}")
        st.metric("均价",    f"${hl_avg_price:.0f}")
        if not pd.isna(hl_avg_rating):
            st.metric("平均评分", f"⭐ {hl_avg_rating:.2f}")

# ══════════════════════════════════════════════════════════════════
# Section 5: LQS与卖家竞争格局深度分析
# ══════════════════════════════════════════════════════════════════
st.markdown("---")
st.header("🎯 LQS与卖家竞争格局深度分析")

col_l1, col_l2 = st.columns([1, 1])

# 🔑 方案B对齐：对比图表统一使用共有时间段 (2024-12 ~ 2026-04)
df_aligned_lqs = df[df['月份'] >= '2024-12']

with col_l1:
    st.subheader("🏆 头部品牌 LQS 详情页质量分对比 (对齐周期)")
    st.caption("注：已对齐至共有周期 2024-12 ~ 2026-04 进行跨站点公平品牌提取")
    # Group by Brand, calculate mean LQS, filter only top 15 brands by revenue
    top_15_brands = df_aligned_lqs.groupby('品牌')['销售额'].sum().sort_values(ascending=False).head(15).index
    brand_lqs = df_aligned_lqs[df_aligned_lqs['品牌'].isin(top_15_brands)].groupby('品牌')['lqs'].mean().reset_index()
    brand_lqs = brand_lqs.sort_values(by='lqs', ascending=True) # Ascending for horizontal bar
    
    fig_brand_lqs = go.Figure(go.Bar(
        x=brand_lqs['lqs'],
        y=brand_lqs['品牌'],
        orientation='h',
        marker=dict(color='#0ea5e9'),
        text=brand_lqs['lqs'].apply(lambda v: f'{v:.1f}'),
        textposition='outside',
        hovertemplate='<b>%{y}</b><br>平均 LQS: %{x:.2f}<extra></extra>'
    ))
    
    # Highlight Hollyland in Red
    colors_lqs = ['#e11d48' if b == 'Hollyland' else '#2563eb' for b in brand_lqs['品牌']]
    fig_brand_lqs.data[0].marker.color = colors_lqs
    
    fig_brand_lqs.update_layout(
        **CHART_LAYOUT,
        height=380,
        xaxis=dict(title='Listing Quality Score (LQS)', range=[0, 110]),
        yaxis=dict(title='', automargin=True),
        margin=dict(t=20, b=40, l=20, r=60)
    )
    st.plotly_chart(fig_brand_lqs, width='stretch')

with col_l2:
    st.subheader("🌍 卖家来源地区销售额占比 (对齐周期)")
    st.caption("注：已对齐至共有周期 2024-12 ~ 2026-04 确保销售额跨站点占比公平")
    geo = df_aligned_lqs.groupby('地区')['销售额'].sum().sort_values(ascending=False).reset_index()
    # Map country codes for high premium aesthetics
    country_map = {
        'CN': '中国 (CN)', 'US': '美国 (US)', 'JP': '日本 (JP)', 'DE': '德国 (DE)', 
        'GB': '英国 (GB)', 'FR': '法国 (FR)', 'IT': '意大利 (IT)', 'ES': '西班牙 (ES)', 
        'IN': '印度 (IN)', 'HK': '中国香港 (HK)', 'TW': '中国台湾 (TW)', 'KR': '韩国 (KR)'
    }
    geo['地区名称'] = geo['地区'].map(country_map).fillna(geo['地区'])
    
    fig_geo_pie = px.pie(
        geo, values='销售额', names='地区名称',
        hole=0.45, color_discrete_sequence=COLORS
    )
    fig_geo_pie.update_traces(
        textinfo='label+percent',
        textposition='outside',
        hovertemplate='<b>%{label}</b><br>销售额: $%{value:,.0f}<br>占比: %{percent}<extra></extra>',
        marker=dict(line=dict(color='white', width=1.5))
    )
    fig_geo_pie.update_layout(
        **CHART_LAYOUT,
        height=380,
        showlegend=False,
        margin=dict(t=20, b=20, l=20, r=20)
    )
    st.plotly_chart(fig_geo_pie, width='stretch')

# Correlation of LQS vs Sales
st.markdown("---")
col_lc1, col_lc2 = st.columns([3, 2])

with col_lc1:
    st.subheader("💡 销量 vs Listing 质量分 (LQS) 相关性分布")
    # Drop rows without LQS
    corr_df = df.dropna(subset=['lqs']).copy()
    if not corr_df.empty:
        # Group by ASIN to get average monthly sales and LQS
        asin_corr = corr_df.groupby(['ASIN', '品牌', '站点']).agg(
            平均销量=('销量', 'mean'),
            LQS=('lqs', 'first'),
            平均价格=('价格', 'mean')
        ).reset_index()
        
        fig_corr = px.scatter(
            asin_corr, x='LQS', y='平均销量', color='品牌', size='平均价格',
            color_discrete_sequence=COLORS,
            hover_name='ASIN',
            hover_data={'平均销量': ':.0f', 'LQS': ':.1f', '平均价格': ':$.2f', '站点': True}
        )
        fig_corr.update_layout(
            **CHART_LAYOUT,
            height=400,
            yaxis=dict(title='月均销量 (件)', tickformat=',.0f'),
            xaxis=dict(title='Listing 质量分 (LQS)', range=[20, 105]),
            margin=dict(t=20, b=40, l=60, r=20)
        )
        st.plotly_chart(fig_corr, width='stretch')
    else:
        st.info("当前筛选条件无 LQS 记录，无法显示相关性散点图。")

with col_lc2:
    st.subheader("🇨🇳 中国卖家 (CN) 市场销售额占比月度趋势")
    # Calculate CN seller revenue share month by month
    cn_monthly = df.groupby(['月份', df['地区'].str.upper() == 'CN'])['销售额'].sum().unstack().fillna(0)
    if not cn_monthly.empty:
        # Check if True column exists
        if True in cn_monthly.columns:
            cn_monthly['CN_Share'] = (cn_monthly[True] / cn_monthly.sum(axis=1) * 100).round(1)
        else:
            cn_monthly['CN_Share'] = 0.0
            
        cn_monthly = cn_monthly.reset_index().sort_values('月份')
        
        fig_cn_trend = go.Figure()
        fig_cn_trend.add_trace(go.Scatter(
            x=cn_monthly['月份'], y=cn_monthly['CN_Share'],
            mode='lines+markers', name='CN 卖家占比',
            fill='tozeroy', fillcolor='rgba(16,185,129,0.08)',
            line=dict(color='#10b981', width=2.5, shape='spline'),
            marker=dict(size=6),
            hovertemplate='<b>%{x}</b><br>中国卖家占比: %{y:.1f}%<extra></extra>'
        ))
        fig_cn_trend.update_layout(
            **CHART_LAYOUT,
            height=400,
            yaxis=dict(title='销售额占比 (%)', range=[0, 105], tickformat='.0f'),
            xaxis=dict(title='', tickangle=-30),
            margin=dict(t=20, b=60, l=60, r=20)
        )
        st.plotly_chart(fig_cn_trend, width='stretch')
    else:
        st.info("数据不足，无法计算中国卖家占比趋势。")

# ══════════════════════════════════════════════════════════════════
# Section 6: 销售数据明细
# ══════════════════════════════════════════════════════════════════
st.markdown("---")
st.subheader("📋 销售明细 Top 100")
display_cols = ['月份', '站点', '品牌', 'ASIN', '价格区间', '价格', '销量', '销售额', '评分', 'BSR', 'lqs']
display_cols = [c for c in display_cols if c in df.columns]
detail_df = (df[display_cols]
             .sort_values('销售额', ascending=False)
             .head(100)
             .reset_index(drop=True))
# Format numeric columns
fmt_df = detail_df.copy()
if '价格' in fmt_df.columns:
    fmt_df['价格'] = fmt_df['价格'].apply(lambda v: f'${v:.2f}')
if '销售额' in fmt_df.columns:
    fmt_df['销售额'] = fmt_df['销售额'].apply(lambda v: f'${v:,.0f}')
st.dataframe(fmt_df, width='stretch', height=400)

# ── 下载 ─────────────────────────────────────────────────────────
st.markdown("---")
csv = df.to_csv(index=False).encode('utf-8-sig')
st.download_button(
    label="📥 下载筛选后完整数据 (CSV)",
    data=csv,
    file_name='amazon_wireless_mic_analysis.csv',
    mime='text/csv',
    help="下载当前筛选条件下的全量数据"
)
