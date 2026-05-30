"""
export_excel.py - 市场分析报告 Excel 导出脚本
运行: python export_excel.py
"""
import pandas as pd
import pickle
from pathlib import Path
from datetime import datetime
from openpyxl import Workbook
from openpyxl.styles import (PatternFill, Font, Alignment, Border, Side,
                              GradientFill)
from openpyxl.utils import get_column_letter
from openpyxl.chart import BarChart, LineChart, PieChart, Reference
from openpyxl.chart.series import DataPoint

# ── 颜色常量 ───────────────────────────────────────────────
BLUE_DARK   = "1E3A5F"
BLUE_MID    = "2563EB"
BLUE_LIGHT  = "DBEAFE"
GRAY_HEADER = "F1F5F9"
GRAY_ROW    = "F8FAFC"
WHITE       = "FFFFFF"
RED_ACCENT  = "E11D48"
GREEN_ACC   = "10B981"
BORDER_COL  = "CBD5E1"

def make_border():
    s = Side(style='thin', color=BORDER_COL)
    return Border(left=s, right=s, top=s, bottom=s)

def header_style(ws, row, col, value, bg=BLUE_DARK, fg=WHITE, bold=True, size=11):
    cell = ws.cell(row=row, column=col, value=value)
    cell.fill = PatternFill("solid", fgColor=bg)
    cell.font = Font(bold=bold, color=fg, size=size, name="Calibri")
    cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    cell.border = make_border()
    return cell

def data_style(ws, row, col, value, bg=WHITE, bold=False, num_fmt=None, align="center"):
    cell = ws.cell(row=row, column=col, value=value)
    cell.fill = PatternFill("solid", fgColor=bg)
    cell.font = Font(bold=bold, color="1E293B", size=10, name="Calibri")
    cell.alignment = Alignment(horizontal=align, vertical="center")
    cell.border = make_border()
    if num_fmt:
        cell.number_format = num_fmt
    return cell

def set_col_widths(ws, widths):
    for i, w in enumerate(widths, 1):
        ws.column_dimensions[get_column_letter(i)].width = w

def title_row(ws, text, row, ncols, bg=BLUE_DARK):
    ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=ncols)
    cell = ws.cell(row=row, column=1, value=text)
    cell.fill = PatternFill("solid", fgColor=bg)
    cell.font = Font(bold=True, color=WHITE, size=13, name="Calibri")
    cell.alignment = Alignment(horizontal="center", vertical="center")
    ws.row_dimensions[row].height = 28

# ══════════════════════════════════════════════════════════════
# 加载数据
# ══════════════════════════════════════════════════════════════
print("[Loading] Loading data...")
df = pd.read_pickle("processed_market_data.pkl")
df['销量'] = pd.to_numeric(df['销量'], errors='coerce')
df['销售额'] = pd.to_numeric(df['销售额'], errors='coerce')
df['月份_dt'] = pd.to_datetime(df['月份'])

# 最新完整季度
df['季度'] = df['月份_dt'].dt.to_period('Q')
q_counts = df.groupby('季度')['月份'].nunique()
complete_qs = q_counts[q_counts == 3].index
latest_q = complete_qs.max() if not complete_qs.empty else df['季度'].max()
q_df = df[df['季度'] == latest_q]

price_order = ['0-30', '30-50', '50-100', '100-150', '150+']

wb = Workbook()

# ══════════════════════════════════════════════════════════════
# Sheet 1: 市场概览
# ══════════════════════════════════════════════════════════════
print("[Sheet] 1: 市场概览...")
ws1 = wb.active
ws1.title = "市场概览"
ws1.sheet_view.showGridLines = False
ws1.row_dimensions[1].height = 40
ws1.row_dimensions[2].height = 20

title_row(ws1, f"Amazon 无线麦克风市场分析报告  |  数据区间: {df['月份'].min()} ~ {df['月份'].max()}  |  生成时间: {datetime.now().strftime('%Y-%m-%d')}", 1, 6)

# KPI 卡片
kpis = [
    ("总销量", f"{int(df['销量'].sum()):,}", BLUE_MID),
    ("总销售额 (USD)", f"${df['销售额'].sum()/1e6:.1f}M", BLUE_MID),
    ("覆盖 ASIN 数", str(df['ASIN'].nunique()), BLUE_MID),
    ("市场均价 (USD)", f"${df['价格'].mean():.2f}", BLUE_MID),
    ("数据月份数", str(df['月份'].nunique()), BLUE_MID),
    ("覆盖品牌数", str(df['品牌'].nunique()), BLUE_MID),
]

ws1.merge_cells("A3:F3")
ws1.cell(row=3, column=1, value="📌 核心 KPI 指标").font = Font(bold=True, size=11, color=BLUE_DARK)

for i, (label, val, color) in enumerate(kpis, 1):
    col = i
    ws1.row_dimensions[4].height = 18
    ws1.row_dimensions[5].height = 32
    ws1.row_dimensions[6].height = 18
    header_style(ws1, 4, col, label, bg=GRAY_HEADER, fg=BLUE_DARK, bold=True, size=10)
    cell = ws1.cell(row=5, column=col, value=val)
    cell.fill = PatternFill("solid", fgColor=BLUE_LIGHT)
    cell.font = Font(bold=True, size=14, color=BLUE_DARK, name="Calibri")
    cell.alignment = Alignment(horizontal="center", vertical="center")
    cell.border = make_border()

set_col_widths(ws1, [18, 18, 18, 18, 18, 18])

# ── 月度趋势表 ──
ws1.merge_cells("A8:F8")
ws1.cell(row=8, column=1, value="[Trend] 月度销售趋势 (全市场 vs Hollyland)").font = Font(bold=True, size=11, color=BLUE_DARK)
ws1.row_dimensions[8].height = 22

hdrs = ["月份", "全市场销量", "全市场销售额 (USD)", "Hollyland销量", "Hollyland销售额 (USD)", "Hollyland占比"]
for j, h in enumerate(hdrs, 1):
    header_style(ws1, 9, j, h, bg=BLUE_DARK)

total_trend = df.groupby('月份')[['销量','销售额']].sum().reset_index().sort_values('月份')
hl_trend = df[df['品牌']=='Hollyland'].groupby('月份')[['销量','销售额']].sum().reset_index()
trend = total_trend.merge(hl_trend, on='月份', how='left', suffixes=('_全市场','_Hollyland')).fillna(0)
trend['占比'] = trend['销售额_Hollyland'] / trend['销售额_全市场']

for r_off, (_, row) in enumerate(trend.iterrows()):
    r = 10 + r_off
    bg = GRAY_ROW if (r % 2 == 0) else WHITE
    data_style(ws1, r, 1, row['月份'], bg=bg)
    data_style(ws1, r, 2, int(row['销量_全市场']), bg=bg, num_fmt='#,##0')
    data_style(ws1, r, 3, row['销售额_全市场'], bg=bg, num_fmt='$#,##0')
    data_style(ws1, r, 4, int(row['销量_Hollyland']), bg=bg, num_fmt='#,##0')
    data_style(ws1, r, 5, row['销售额_Hollyland'], bg=bg, num_fmt='$#,##0')
    data_style(ws1, r, 6, row['占比'], bg=bg, num_fmt='0.0%')

# 折线图
last_r = 9 + len(trend)
chart = LineChart()
chart.title = "全市场 vs Hollyland 月度销售额趋势"
chart.style = 10
chart.y_axis.title = "销售额 (USD)"
chart.x_axis.title = "月份"
chart.height = 12
chart.width = 24

data_ref1 = Reference(ws1, min_col=3, min_row=9, max_row=last_r)
data_ref2 = Reference(ws1, min_col=5, min_row=9, max_row=last_r)
cats = Reference(ws1, min_col=1, min_row=10, max_row=last_r)

chart.add_data(data_ref1, titles_from_data=True)
chart.add_data(data_ref2, titles_from_data=True)
chart.set_categories(cats)
chart.series[0].graphicalProperties.line.solidFill = BLUE_MID
chart.series[0].graphicalProperties.line.width = 20000
chart.series[1].graphicalProperties.line.solidFill = RED_ACCENT
chart.series[1].graphicalProperties.line.width = 20000

ws1.add_chart(chart, f"A{last_r + 2}")


# ══════════════════════════════════════════════════════════════
# Sheet 2: 品牌份额
# ══════════════════════════════════════════════════════════════
print("[Sheet] 2: 品牌份额...")
ws2 = wb.create_sheet("品牌市场份额")
ws2.sheet_view.showGridLines = False
title_row(ws2, f"Top 15 品牌市场份额分析 (统计周期: {df['月份'].min()} ~ {df['月份'].max()})", 1, 5)
set_col_widths(ws2, [5, 24, 16, 16, 14])

hdrs2 = ["排名", "品牌", "总销量", "总销售额 (USD)", "销售额占比"]
for j, h in enumerate(hdrs2, 1):
    header_style(ws2, 2, j, h)

brand_df = df.groupby('品牌')[['销量','销售额']].sum().sort_values('销售额', ascending=False).head(15).reset_index()
total_rev = df['销售额'].sum()
brand_df['占比'] = brand_df['销售额'] / total_rev

bar_colors = [BLUE_MID, RED_ACCENT, GREEN_ACC, "F59E0B", "8B5CF6",
              "06B6D4", "EC4899", "14B8A6", "F97316", "6366F1",
              "84CC16", "EF4444", "0EA5E9", "D946EF", "78716C"]

for r_off, (_, row) in enumerate(brand_df.iterrows()):
    r = 3 + r_off
    bg = BLUE_LIGHT if row['品牌'] == 'Hollyland' else (GRAY_ROW if r_off % 2 == 0 else WHITE)
    bold = row['品牌'] == 'Hollyland'
    data_style(ws2, r, 1, r_off+1, bg=bg, bold=bold)
    data_style(ws2, r, 2, row['品牌'], bg=bg, bold=bold, align="left")
    data_style(ws2, r, 3, int(row['销量']), bg=bg, num_fmt='#,##0')
    data_style(ws2, r, 4, row['销售额'], bg=bg, num_fmt='$#,##0')
    data_style(ws2, r, 5, row['占比'], bg=bg, num_fmt='0.0%', bold=bold)

# 柱状图
chart2 = BarChart()
chart2.type = "bar"
chart2.title = "Top 15 品牌销售额"
chart2.style = 10
chart2.y_axis.title = "品牌"
chart2.x_axis.title = "销售额 (USD)"
chart2.height = 16
chart2.width = 22

data_r = Reference(ws2, min_col=4, min_row=2, max_row=2+len(brand_df))
cats_r = Reference(ws2, min_col=2, min_row=3, max_row=2+len(brand_df))
chart2.add_data(data_r, titles_from_data=True)
chart2.set_categories(cats_r)
chart2.series[0].graphicalProperties.solidFill = BLUE_MID
ws2.add_chart(chart2, "G2")


# ══════════════════════════════════════════════════════════════
# Sheet 3: 价位段分析
# ══════════════════════════════════════════════════════════════
print("[Sheet] 3: 价位段分析...")
ws3 = wb.create_sheet("价位段分析")
ws3.sheet_view.showGridLines = False
title_row(ws3, f"各价位段市场结构分析 (统计周期: {df['月份'].min()} ~ {df['月份'].max()})", 1, 7)
set_col_widths(ws3, [14, 14, 16, 14, 12, 14, 14])

hdrs3 = ["价位段 (USD)", "销量", "销售额 (USD)", "销售额占比", "ASIN数", "均价", "Top5品牌集中度"]
for j, h in enumerate(hdrs3, 1):
    header_style(ws3, 2, j, h)

price_df = df.groupby('价格区间').agg(
    销量=('销量','sum'), 销售额=('销售额','sum'),
    ASIN数=('ASIN','nunique'), 均价=('价格','mean')
).reindex(price_order).dropna().reset_index()
price_df['占比'] = price_df['销售额'] / price_df['销售额'].sum()

seg_colors = [BLUE_MID, GREEN_ACC, "F59E0B", RED_ACCENT, "8B5CF6"]

for i, row in price_df.iterrows():
    r = 3 + i
    bg = GRAY_ROW if i % 2 == 0 else WHITE
    tier_total = df[df['价格区间']==row['价格区间']]['销售额'].sum()
    top5 = df[df['价格区间']==row['价格区间']].groupby('品牌')['销售额'].sum().sort_values(ascending=False).head(5).sum()
    conc = top5/tier_total if tier_total > 0 else 0
    data_style(ws3, r, 1, row['价格区间'], bg=bg, bold=True)
    data_style(ws3, r, 2, int(row['销量']), bg=bg, num_fmt='#,##0')
    data_style(ws3, r, 3, row['销售额'], bg=bg, num_fmt='$#,##0')
    data_style(ws3, r, 4, row['占比'], bg=bg, num_fmt='0.0%')
    data_style(ws3, r, 5, int(row['ASIN数']), bg=bg, num_fmt='#,##0')
    data_style(ws3, r, 6, row['均价'], bg=bg, num_fmt='$#,##0.00')
    data_style(ws3, r, 7, conc, bg=bg, num_fmt='0.0%')

# ── 最新完整季度品牌明细 ──
ws3.merge_cells("A10:G10")
ws3.cell(row=10, column=1, value=f"📊 各价位段 Top 5 品牌占比 — 最新完整季度: {latest_q}").font = Font(bold=True, size=11, color=BLUE_DARK)
ws3.row_dimensions[10].height = 22

hdrs4 = ["价位段", "排名", "品牌", "季度销量", "季度销售额 (USD)", "在该价位段占比", ""]
for j, h in enumerate(hdrs4, 1):
    header_style(ws3, 11, j, h)

r_start = 12
for tier in price_order:
    tier_df = q_df[q_df['价格区间']==tier]
    t_total = tier_df['销售额'].sum()
    brands = tier_df.groupby('品牌')[['销量','销售额']].sum().sort_values('销售额', ascending=False).head(5).reset_index()
    for k, brow in brands.iterrows():
        bg = BLUE_LIGHT if brow['品牌']=='Hollyland' else (GRAY_ROW if k%2==0 else WHITE)
        data_style(ws3, r_start, 1, tier, bg=bg, bold=True)
        data_style(ws3, r_start, 2, k+1, bg=bg)
        data_style(ws3, r_start, 3, brow['品牌'], bg=bg, align="left")
        data_style(ws3, r_start, 4, int(brow['销量']), bg=bg, num_fmt='#,##0')
        data_style(ws3, r_start, 5, brow['销售额'], bg=bg, num_fmt='$#,##0')
        data_style(ws3, r_start, 6, brow['销售额']/t_total if t_total>0 else 0, bg=bg, num_fmt='0.0%')
        r_start += 1


# ══════════════════════════════════════════════════════════════
# Sheet 4: Hollyland 专项
# ══════════════════════════════════════════════════════════════
print("[Sheet] 4: Hollyland 专项...")
ws4 = wb.create_sheet("Hollyland 专项")
ws4.sheet_view.showGridLines = False
title_row(ws4, f"Hollyland 品牌专项分析 (统计周期: {df['月份'].min()} ~ {df['月份'].max()})", 1, 6, bg=RED_ACCENT)
set_col_widths(ws4, [14, 14, 18, 18, 16, 16])

hl_monthly = df[df['品牌']=='Hollyland'].groupby('月份').agg(
    销量=('销量','sum'), 销售额=('销售额','sum'), ASIN数=('ASIN','nunique'), 均价=('价格','mean')
).reset_index().sort_values('月份')
total_by_month = df.groupby('月份')['销售额'].sum()
hl_monthly['市场占比'] = hl_monthly.apply(lambda r: r['销售额']/total_by_month[r['月份']] if r['月份'] in total_by_month else 0, axis=1)

hdrs5 = ["月份", "销量", "销售额 (USD)", "市场占比", "ASIN数", "月均价 (USD)"]
for j, h in enumerate(hdrs5, 1):
    header_style(ws4, 2, j, h, bg=RED_ACCENT)

for r_off, (_, row) in enumerate(hl_monthly.iterrows()):
    r = 3 + r_off
    bg = GRAY_ROW if r%2==0 else WHITE
    data_style(ws4, r, 1, row['月份'], bg=bg)
    data_style(ws4, r, 2, int(row['销量']), bg=bg, num_fmt='#,##0')
    data_style(ws4, r, 3, row['销售额'], bg=bg, num_fmt='$#,##0')
    data_style(ws4, r, 4, row['市场占比'], bg=bg, num_fmt='0.0%')
    data_style(ws4, r, 5, int(row['ASIN数']), bg=bg)
    data_style(ws4, r, 6, row['均价'], bg=bg, num_fmt='$#,##0.00')


# ══════════════════════════════════════════════════════════════
# Sheet 5: 原始明细
# ══════════════════════════════════════════════════════════════
print("[Sheet] 5: 原始明细 (Top200)...")
ws5 = wb.create_sheet("原始明细 (Top200)")
ws5.sheet_view.showGridLines = False
top200 = df.sort_values('销售额', ascending=False).head(200)
cols_export = ['月份','品牌','ASIN','品类','价格区间','价格','销量','销售额','地区','BSR']
cols_export = [c for c in cols_export if c in top200.columns]

title_row(ws5, f"原始数据明细 (按销售额排名前200条, 统计周期: {df['月份'].min()} ~ {df['月份'].max()})", 1, len(cols_export))
for j, h in enumerate(cols_export, 1):
    header_style(ws5, 2, j, h)

for i, row in top200[cols_export].reset_index(drop=True).iterrows():
    r = 3 + i
    bg = GRAY_ROW if i%2==0 else WHITE
    for j, col in enumerate(cols_export, 1):
        v = row[col]
        fmt = None
        if col == '销售额': fmt = '$#,##0'
        elif col == '价格': fmt = '$#,##0.00'
        elif col == '销量': fmt = '#,##0'
        data_style(ws5, r, j, v, bg=bg, num_fmt=fmt, align="left" if col in ['品牌','ASIN','品类'] else "center")

for j in range(1, len(cols_export)+1):
    ws5.column_dimensions[get_column_letter(j)].width = 16


# ══════════════════════════════════════════════════════════════
# Sheet 6: 站点概览 (V4)
# ══════════════════════════════════════════════════════════════
print("[Sheet] 6: 站点概览...")
ws6 = wb.create_sheet("站点概览")
ws6.sheet_view.showGridLines = False
title_row(ws6, "各站点销售数据概览 (统计周期: 对齐 2024-12 ~ 2026-04)", 1, 6)
set_col_widths(ws6, [16, 18, 16, 12, 14, 14])

hdrs6 = ["站点", "总销售额 (USD)", "总销量", "销售额占比", "Hollyland销售额", "Hollyland占比"]
for j, h in enumerate(hdrs6, 1):
    header_style(ws6, 2, j, h)

# Calculate site stats (🔑 方案B对齐：统一使用共有时间段以确保公平对比)
if '站点' in df.columns:
    df_aligned = df[df['月份'] >= '2024-12']
    site_stats = df_aligned.groupby('站点').agg(
        总销售额=('销售额', 'sum'),
        总销量=('销量', 'sum')
    ).reset_index()

    total_rev = df_aligned['销售额'].sum()
    site_stats['销售额占比'] = site_stats['总销售额'] / total_rev

    hollyland_by_site = df_aligned[df_aligned['品牌'] == 'Hollyland'].groupby('站点')['销售额'].sum()
    site_stats['Hollyland销售额'] = site_stats['站点'].map(hollyland_by_site).fillna(0)
    site_stats['Hollyland占比'] = site_stats['Hollyland销售额'] / site_stats['总销售额']

    site_stats = site_stats.sort_values('总销售额', ascending=False)

    for r_off, (_, row) in enumerate(site_stats.iterrows()):
        r = 3 + r_off
        bg = GRAY_ROW if r_off % 2 == 0 else WHITE
        data_style(ws6, r, 1, row['站点'], bg=bg, bold=True)
        data_style(ws6, r, 2, row['总销售额'], bg=bg, num_fmt='$#,##0')
        data_style(ws6, r, 3, int(row['总销量']), bg=bg, num_fmt='#,##0')
        data_style(ws6, r, 4, row['销售额占比'], bg=bg, num_fmt='0.0%')
        data_style(ws6, r, 5, row['Hollyland销售额'], bg=bg, num_fmt='$#,##0')
        data_style(ws6, r, 6, row['Hollyland占比'], bg=bg, num_fmt='0.0%')

    # Add totals row
    last_r = 3 + len(site_stats)
    data_style(ws6, last_r, 1, "合计", bg=BLUE_LIGHT, bold=True)
    data_style(ws6, last_r, 2, site_stats['总销售额'].sum(), bg=BLUE_LIGHT, num_fmt='$#,##0', bold=True)
    data_style(ws6, last_r, 3, int(site_stats['总销量'].sum()), bg=BLUE_LIGHT, num_fmt='#,##0', bold=True)
    data_style(ws6, last_r, 4, 1.0, bg=BLUE_LIGHT, num_fmt='0.0%', bold=True)
    data_style(ws6, last_r, 5, site_stats['Hollyland销售额'].sum(), bg=BLUE_LIGHT, num_fmt='$#,##0', bold=True)
    data_style(ws6, last_r, 6, site_stats['Hollyland销售额'].sum() / site_stats['总销售额'].sum() if site_stats['总销售额'].sum() > 0 else 0, bg=BLUE_LIGHT, num_fmt='0.0%', bold=True)

# ══════════════════════════════════════════════════════════════
# Sheet 7: Top5站点趋势 (V4)
# ══════════════════════════════════════════════════════════════
print("[Sheet] 7: Top5站点趋势...")
ws7 = wb.create_sheet("Top5站点趋势")
ws7.sheet_view.showGridLines = False
title_row(ws7, "销售额排名前5站点月度趋势分析 (统计周期: 对齐 2024-12 ~ 2026-04)", 1, 8)
set_col_widths(ws7, [12, 14, 14, 12, 14, 14, 12, 14])

if '站点' in df.columns:
    # Get top 5 sites (🔑 方案B对齐：基于共有时间段提取排名前5的站点)
    df_aligned = df[df['月份'] >= '2024-12']
    top5_sites = df_aligned.groupby('站点')['销售额'].sum().sort_values(ascending=False).head(5).index.tolist()

    # Build trend data (对齐共有月份以进行跨站点合理对比)
    months = sorted(df_aligned['月份'].unique())
    trend_rows = []

    for site in top5_sites:
        site_df = df_aligned[df_aligned['站点'] == site]
        for month in months:
            month_df = site_df[site_df['月份'] == month]
            total = month_df['销售额'].sum()
            holly = month_df[month_df['品牌'] == 'Hollyland']['销售额'].sum()
            trend_rows.append({
                '站点': site,
                '月份': month,
                '总销售额': total,
                'Hollyland销售额': holly,
                'Hollyland占比': holly / total if total > 0 else 0
            })

    trend_df = pd.DataFrame(trend_rows)

    hdrs7 = ["站点", "月份", "总销售额 (USD)", "Hollyland销售额 (USD)", "Hollyland占比"]
    for j, h in enumerate(hdrs7, 1):
        header_style(ws7, 2, j, h)

    for i, row in trend_df.iterrows():
        r = 3 + i
        bg = GRAY_ROW if i % 2 == 0 else WHITE
        data_style(ws7, r, 1, row['站点'], bg=bg, bold=True)
        data_style(ws7, r, 2, row['月份'], bg=bg)
        data_style(ws7, r, 3, row['总销售额'], bg=bg, num_fmt='$#,##0')
        data_style(ws7, r, 4, row['Hollyland销售额'], bg=bg, num_fmt='$#,##0')
        data_style(ws7, r, 5, row['Hollyland占比'], bg=bg, num_fmt='0.0%')

# ══════════════════════════════════════════════════════════════
# Sheet 8: 竞品基准分析 (V4)
# ══════════════════════════════════════════════════════════════
print("[Sheet] 8: 竞品基准分析...")
ws8 = wb.create_sheet("竞品基准分析")
ws8.sheet_view.showGridLines = False
title_row(ws8, f"品牌竞品基准对比分析 (统计周期: {df['月份'].min()} ~ {df['月份'].max()})", 1, 11)
set_col_widths(ws8, [20, 16, 14, 12, 12, 12, 12, 14, 14, 12, 14])

# Calculate benchmarks
brands = df['品牌'].unique()
benchmarks = []
total_rev = df['销售额'].sum()
total_units = df['销量'].sum()

for brand in brands:
    brand_df = df[df['品牌'] == brand]
    brand_rev = brand_df['销售额'].sum()
    brand_units = brand_df['销量'].sum()

    benchmarks.append({
        '品牌': brand,
        '总销售额': brand_rev,
        '总销量': brand_units,
        '平均价格': brand_df['价格'].mean(),
        '平均评分': brand_df['评分'].mean(),
        'ASIN数量': brand_df['ASIN'].nunique(),
        '平均成交价': brand_rev / brand_units if brand_units > 0 else 0,
        '市场份额': brand_rev / total_rev if total_rev > 0 else 0,
        '与Hollyland差距': brand_rev / df[df['品牌'] == 'Hollyland']['销售额'].sum() if 'Hollyland' in brands else None,
        '平均LQS': brand_df['lqs'].dropna().mean() if 'lqs' in brand_df.columns else None,
        '中国卖家占比': (brand_df['地区'].str.upper() == 'CN').mean() if '地区' in brand_df.columns else 0
    })

bench_df = pd.DataFrame(benchmarks).sort_values('总销售额', ascending=False)

hdrs8 = ["品牌", "总销售额", "总销量", "平均价格", "平均评分", "ASIN数量", "平均成交价", "市场份额", "与Hollyland差距", "平均LQS", "中国卖家占比"]
for j, h in enumerate(hdrs8, 1):
    header_style(ws8, 2, j, h)

hollyland_total_rev = df[df['品牌'] == 'Hollyland']['销售额'].sum()

for r_off, (_, row) in enumerate(bench_df.iterrows()):
    r = 3 + r_off
    bg = BLUE_LIGHT if row['品牌'] == 'Hollyland' else (GRAY_ROW if r_off % 2 == 0 else WHITE)
    bold = row['品牌'] == 'Hollyland'
    # 安全计算 与 Hollyland 差距（防止除零）
    gap_val = (row['总销售额'] / hollyland_total_rev) if hollyland_total_rev > 0 else None
    data_style(ws8, r, 1, row['品牌'], bg=bg, bold=bold, align="left")
    data_style(ws8, r, 2, row['总销售额'], bg=bg, num_fmt='$#,##0', bold=bold)
    data_style(ws8, r, 3, int(row['总销量']), bg=bg, num_fmt='#,##0')
    data_style(ws8, r, 4, row['平均价格'], bg=bg, num_fmt='$#,##0.00')
    data_style(ws8, r, 5, row['平均评分'], bg=bg, num_fmt='0.00')
    data_style(ws8, r, 6, int(row['ASIN数量']), bg=bg, num_fmt='#,##0')
    data_style(ws8, r, 7, row['平均成交价'], bg=bg, num_fmt='$#,##0.00')
    data_style(ws8, r, 8, row['市场份额'], bg=bg, num_fmt='0.1%')
    data_style(ws8, r, 9, gap_val, bg=bg, num_fmt='0.00x' if gap_val is not None else None)
    data_style(ws8, r, 10, row['平均LQS'], bg=bg, num_fmt='0.0')
    data_style(ws8, r, 11, row['中国卖家占比'], bg=bg, num_fmt='0.0%')


# ══════════════════════════════════════════════════════════════
# Sheet 9: LQS与卖家分析 (V5)
# ══════════════════════════════════════════════════════════════
print("[Sheet] 9: LQS与卖家分析...")
ws9 = wb.create_sheet("LQS与卖家分析")
ws9.sheet_view.showGridLines = False
title_row(ws9, f"LQS详情页质量分与卖家分布深度分析 (统计周期: {df['月份'].min()} ~ {df['月份'].max()})", 1, 7)
set_col_widths(ws9, [20, 14, 16, 16, 14, 14, 14])

# ── 1. 卖家国别分布表 ──
ws9.cell(row=3, column=1, value="📌 卖家来源地区国别分布表").font = Font(bold=True, size=11, color=BLUE_DARK)
hdrs9_1 = ["卖家地区", "ASIN数量", "总销量", "总销售额 (USD)", "销售额占比", "平均评分", "平均LQS"]
for j, h in enumerate(hdrs9_1, 1):
    header_style(ws9, 4, j, h)

# Group by seller region
geo_stats = df.groupby('地区').agg(
    ASIN数=('ASIN', 'nunique'),
    总销量=('销量', 'sum'),
    总销售额=('销售额', 'sum'),
    平均评分=('评分', 'mean')
).reset_index()

# Handle LQS
if 'lqs' in df.columns:
    geo_lqs = df.groupby('地区')['lqs'].mean()
    geo_stats['平均LQS'] = geo_stats['地区'].map(geo_lqs)
else:
    geo_stats['平均LQS'] = None

total_geo_rev = geo_stats['总销售额'].sum()
geo_stats['销售额占比'] = geo_stats['总销售额'] / total_geo_rev if total_geo_rev > 0 else 0
geo_stats = geo_stats.sort_values('总销售额', ascending=False)

# Map codes
country_map = {
    'CN': '中国 (CN)', 'US': '美国 (US)', 'JP': '日本 (JP)', 'DE': '德国 (DE)', 
    'GB': '英国 (GB)', 'FR': '法国 (FR)', 'IT': '意大利 (IT)', 'ES': '西班牙 (ES)', 
    'IN': '印度 (IN)', 'HK': '中国香港 (HK)', 'TW': '中国台湾 (TW)', 'KR': '韩国 (KR)'
}

for i, (_, row) in enumerate(geo_stats.iterrows()):
    r = 5 + i
    bg = GRAY_ROW if i % 2 == 0 else WHITE
    c_name = country_map.get(row['地区'], row['地区'])
    data_style(ws9, r, 1, c_name, bg=bg, bold=True, align="left")
    data_style(ws9, r, 2, int(row['ASIN数']), bg=bg, num_fmt='#,##0')
    data_style(ws9, r, 3, int(row['总销量']), bg=bg, num_fmt='#,##0')
    data_style(ws9, r, 4, row['总销售额'], bg=bg, num_fmt='$#,##0')
    data_style(ws9, r, 5, row['销售额占比'], bg=bg, num_fmt='0.0%')
    data_style(ws9, r, 6, row['平均评分'], bg=bg, num_fmt='0.00')
    data_style(ws9, r, 7, row['平均LQS'], bg=bg, num_fmt='0.0')

# ── 2. Top Brands LQS 优化排行表 ──
r_start = 5 + len(geo_stats) + 3
ws9.cell(row=r_start-1, column=1, value="📌 Top 15 品牌 Listing 质量分 (LQS) 优化排行").font = Font(bold=True, size=11, color=BLUE_DARK)

hdrs9_2 = ["品牌", "总销售额 (USD)", "平均 LQS", "ASIN数量", "均价", "平均评分", ""]
for j, h in enumerate(hdrs9_2[:-1], 1):
    header_style(ws9, r_start, j, h)

# Group by brand for Top 15
brand_lqs_stats = df.groupby('品牌').agg(
    总销售额=('销售额', 'sum'),
    平均价格=('价格', 'mean'),
    平均评分=('评分', 'mean'),
    ASIN数=('ASIN', 'nunique')
).reset_index()

if 'lqs' in df.columns:
    b_lqs = df.groupby('品牌')['lqs'].mean()
    brand_lqs_stats['平均LQS'] = brand_lqs_stats['品牌'].map(b_lqs)
else:
    brand_lqs_stats['平均LQS'] = None

brand_lqs_stats = brand_lqs_stats.sort_values('总销售额', ascending=False).head(15)

for i, (_, row) in enumerate(brand_lqs_stats.iterrows()):
    r = r_start + 1 + i
    bg = BLUE_LIGHT if row['品牌'] == 'Hollyland' else (GRAY_ROW if i % 2 == 0 else WHITE)
    bold = row['品牌'] == 'Hollyland'
    data_style(ws9, r, 1, row['品牌'], bg=bg, bold=bold, align="left")
    data_style(ws9, r, 2, row['总销售额'], bg=bg, num_fmt='$#,##0', bold=bold)
    data_style(ws9, r, 3, row['平均LQS'], bg=bg, num_fmt='0.0', bold=bold)
    data_style(ws9, r, 4, int(row['ASIN数']), bg=bg, num_fmt='#,##0')
    data_style(ws9, r, 5, row['平均价格'], bg=bg, num_fmt='$#,##0.00')
    data_style(ws9, r, 6, row['平均评分'], bg=bg, num_fmt='0.00')


# ══════════════════════════════════════════════════════════════
# 保存
# ══════════════════════════════════════════════════════════════
out_path = f"Amazon市场分析报告_{datetime.now().strftime('%Y%m%d')}.xlsx"
wb.save(out_path)
print(f"\n[OK] 报告已生成: {out_path}")
print("   包含以下工作表:")
print("   - 市场概览（KPI + 月度趋势图）")
print("   - 品牌市场份额（Top 15 + 柱状图）")
print("   - 价位段分析（结构 + 季度品牌明细）")
print("   - Hollyland 专项（月度明细）")
print("   - 原始明细（Top 200）")
print("   - 站点概览（V4 - 各站点销售数据）")
print("   - Top5站点趋势（V4 - 前5站点月度趋势）")
print("   - 竞品基准分析（V4.1 - 品牌对比 + LQS + 卖家分布）")
print("   - LQS与卖家分析（V5 - 质量分排行与卖家归属分布）")
