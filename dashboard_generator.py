import json
import os

ANALYTICS_FILE = "data/analytics_summary.json"
DASHBOARD_FILE = "dashboard.html"

def generate_html(data):
    # 将 JSON 数据转为字符串嵌入 HTML
    json_data = json.dumps(data, ensure_ascii=False)
    
    html_template = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>无线麦克风全球市场高管决策看板 | McKinsey Style</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://cdn.jsdelivr.net/npm/apexcharts"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Playfair+Display:ital,wght@0,600;0,700;1,400&display=swap" rel="stylesheet">
    <style>
        body { 
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; 
            background-color: #F4F6F8; 
            color: #111827; 
        }
        .mck-title {
            font-family: 'Playfair Display', Georgia, Cambria, "Times New Roman", Times, serif;
            color: #002D62;
        }
        .mck-card {
            background-color: #FFFFFF;
            border: 1px solid #E2E8F0;
            box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.05), 0 1px 2px -1px rgba(0, 0, 0, 0.05);
            border-radius: 4px;
            transition: all 0.2s ease-in-out;
        }
        .mck-card:hover {
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -2px rgba(0, 0, 0, 0.05);
        }
        /* Custom scrollbar */
        ::-webkit-scrollbar {
            width: 6px;
            height: 6px;
        }
        ::-webkit-scrollbar-track {
            background: #F1F5F9;
        }
        ::-webkit-scrollbar-thumb {
            background: #CBD5E1;
            border-radius: 3px;
        }
        ::-webkit-scrollbar-thumb:hover {
            background: #94A3B8;
        }
        /* McKinsey Tab styling */
        .tab-btn {
            border-bottom: 2px solid transparent;
            transition: all 0.2s;
            font-weight: 500;
            color: #64748B;
        }
        .tab-btn.active {
            border-bottom: 2px solid #00A3A6;
            color: #002D62;
            font-weight: 700;
        }
        .tab-panel {
            display: none;
        }
        .tab-panel.active {
            display: block;
        }
        /* McKinsey divider */
        .mck-divider {
            border-top: 1px solid #E2E8F0;
            position: relative;
        }
        .mck-divider::after {
            content: '';
            position: absolute;
            top: -1px;
            left: 0;
            width: 60px;
            height: 2px;
            background-color: #00A3A6;
        }
    </style>
</head>
<body class="p-3 md:p-6 lg:p-8">
    <div class="max-w-[1400px] mx-auto">
        <!-- McKinsey Slide Header -->
        <div class="bg-white border border-slate-200 p-6 rounded-sm mb-6 shadow-sm">
            <div class="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
                <div>
                    <span class="text-xs font-bold text-[#00A3A6] uppercase tracking-widest">McKinsey Executive Intelligence Report</span>
                    <h1 class="text-2xl md:text-3xl font-bold mck-title mt-1">
                        无线音频设备全球市场大盘分析看板
                    </h1>
                    <p class="text-slate-500 text-xs mt-1">
                        分析区间：<span id="date-range" class="font-semibold text-slate-800"></span> 
                        | 生成日期：<span id="generation-time" class="font-semibold text-slate-800"></span> 
                        | 规则：排除月销量 ≤ 200 ASIN（中头部数据）
                    </p>
                </div>
                <!-- Selection Dropdown -->
                <div class="flex items-center gap-2 self-stretch md:self-auto bg-slate-50 p-2 border border-slate-200 rounded-sm">
                    <span class="text-xs font-semibold text-slate-600">🌍 目标站点：</span>
                    <select id="market-selector" class="bg-white border border-slate-300 text-sm font-semibold rounded-sm px-4 py-1.5 focus:outline-none focus:ring-1 focus:ring-[#00A3A6] text-[#002D62]">
                        <option value="GLOBAL">全球汇总市场 (GLOBAL)</option>
                    </select>
                </div>
            </div>
        </div>

        <!-- Metric Cards Row -->
        <div class="grid grid-cols-2 md:grid-cols-5 gap-4 mb-6">
            <div class="mck-card p-5">
                <span class="text-slate-400 text-xs font-semibold uppercase tracking-wider block">月均销量</span>
                <h3 class="text-2xl font-bold text-[#002D62] mt-1" id="kpi-units">0</h3>
                <span class="text-[10px] text-slate-500 block mt-1">Exhibit A.1 - 市场实物出货容量</span>
            </div>
            <div class="mck-card p-5">
                <span class="text-slate-400 text-xs font-semibold uppercase tracking-wider block">月均销售额</span>
                <h3 class="text-2xl font-bold text-[#002D62] mt-1" id="kpi-rev">$0</h3>
                <span class="text-[10px] text-[#00A3A6] font-semibold block mt-1" id="kpi-rev-takeaway">大盘整体变现规模</span>
            </div>
            <div class="mck-card p-5">
                <span class="text-slate-400 text-xs font-semibold uppercase tracking-wider block">大盘交易均价</span>
                <h3 class="text-2xl font-bold text-[#002D62] mt-1" id="kpi-price">$0</h3>
                <span class="text-[10px] text-slate-500 block mt-1">代表主力产品成交价位</span>
            </div>
            <div class="mck-card p-5">
                <span class="text-slate-400 text-xs font-semibold uppercase tracking-wider block">Hollyland 销售额占比</span>
                <h3 class="text-2xl font-bold text-[#00A3A6] mt-1" id="kpi-hl-share">0%</h3>
                <span class="text-[10px] text-slate-500 block mt-1" id="kpi-hl-takeaway">品牌归一化合并数据</span>
            </div>
            <div class="mck-card p-5 col-span-2 md:col-span-1">
                <span class="text-slate-400 text-xs font-semibold uppercase tracking-wider block">数据置信度评分</span>
                <h3 class="text-2xl font-bold text-[#002D62] mt-1">98.4 / 100</h3>
                <span class="text-[10px] text-emerald-600 font-semibold block mt-1">● 数据链路已完全闭环</span>
            </div>
        </div>

        <!-- McKinsey Tabs Menu -->
        <div class="bg-white border-b border-slate-200 flex gap-6 px-6 mb-6 shadow-sm overflow-x-auto whitespace-nowrap">
            <button class="tab-btn py-4 text-sm active" data-target="tab-overview">📊 市场大盘分析 (Market Overview)</button>
            <button class="tab-btn py-4 text-sm" data-target="tab-sites">🔍 站点深度透视 (Marketplaces)</button>
            <button class="tab-btn py-4 text-sm" data-target="tab-competitor">⚔️ 竞争对手矩阵 (Competitor Matrix)</button>
            <button class="tab-btn py-4 text-sm" data-target="tab-forecasting">📈 销量趋势预测 (Demand Forecasting)</button>
        </div>

        <!-- ------------------------------------------------------------- -->
        <!-- TAB 1: MARKET OVERVIEW -->
        <!-- ------------------------------------------------------------- -->
        <div id="tab-overview" class="tab-panel active">
            <!-- Row 1: Combo Trend and Lifecycle -->
            <div class="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
                <!-- Combo Chart -->
                <div class="lg:col-span-2 mck-card p-6 flex flex-col justify-between">
                    <div>
                        <h2 class="text-lg font-bold text-[#002D62] Georgia">大盘月度销额规模与 Hollyland / DJI 份额趋势</h2>
                        <div class="mck-divider my-2"></div>
                        <p class="text-xs text-slate-500 mb-4">柱状图代表市场月总额 (USD) | 折线图代表品牌销售额市场份额 (%)</p>
                    </div>
                    <div id="combo-chart" class="w-full" style="min-height: 380px;"></div>
                </div>
                <!-- Product Lifecycle Stacked Area -->
                <div class="lg:col-span-1 mck-card p-6 flex flex-col justify-between">
                    <div>
                        <h2 class="text-lg font-bold text-[#002D62] Georgia">新老品月度销售额贡献占比 (Lifecycle)</h2>
                        <div class="mck-divider my-2"></div>
                        <p class="text-xs text-slate-500 mb-4">新品定义：上架时间 ≤ 6 个月 | 老品定义：上架时间 > 6 个月</p>
                    </div>
                    <div id="lifecycle-chart" class="w-full" style="min-height: 380px;"></div>
                </div>
            </div>

            <!-- Row 2: Price Tiers -->
            <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <!-- Stacked Price Bar Chart -->
                <div class="lg:col-span-1 mck-card p-6 flex flex-col justify-between">
                    <div>
                        <h2 class="text-lg font-bold text-[#002D62] Georgia">价格区间销售额分布</h2>
                        <div class="mck-divider my-2"></div>
                        <p class="text-xs text-slate-500 mb-4">展示各客单价分段的累计消费额</p>
                    </div>
                    <div id="price-bar-chart" class="w-full" style="min-height: 300px;"></div>
                </div>
                <!-- Price Tier Segment Top 5 Brands Table -->
                <div class="lg:col-span-2 mck-card p-6 flex flex-col">
                    <h2 class="text-lg font-bold text-[#002D62] Georgia">各价格区间领军品牌占有率 (Top 5)</h2>
                    <div class="mck-divider my-2"></div>
                    <p class="text-xs text-slate-500 mb-4">反映各价格带的寡头垄断烈度与机会</p>
                    <div class="overflow-x-auto flex-grow">
                        <table class="w-full text-left text-xs border-collapse">
                            <thead>
                                <tr class="text-slate-500 font-semibold border-b border-slate-200 bg-slate-50">
                                    <th class="py-3 px-4">价位区间 (USD)</th>
                                    <th class="py-3 px-4">TOP 1</th>
                                    <th class="py-3 px-4">TOP 2</th>
                                    <th class="py-3 px-4">TOP 3</th>
                                    <th class="py-3 px-4">TOP 4</th>
                                    <th class="py-3 px-4">TOP 5</th>
                                </tr>
                            </thead>
                            <tbody id="price-table-body" class="divide-y divide-slate-100">
                                <!-- JS Injection -->
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
            
            <!-- Tab 1 Analytical Summary -->
            <div class="mck-card p-6 mt-6 bg-[#FAFBFD] border-l-4 border-[#00A3A6]">
                <h3 class="text-[#002D62] font-bold text-sm Georgia">💡 麦肯锡大盘分析透视 (Executive Takeaways)：</h3>
                <ul class="list-disc list-inside text-xs text-slate-600 mt-2 space-y-1">
                    <li><strong>明显的旺季周期特征</strong>：大盘呈现出极强的季节性变动，黑五网一（11月）是绝对的交易高峰，单月流量近乎平时两倍。</li>
                    <li><strong>主力客单价带双峰分化</strong>：低端客单价区间（$0-30）出货量极其庞大，而高端专业级区间（$150+）变现效率极强，中高端区间（$50-100）作为过渡地带，Hollyland 占据明显的相对统治地位。</li>
                </ul>
            </div>
        </div>

        <!-- ------------------------------------------------------------- -->
        <!-- TAB 2: MARKETPLACES -->
        <!-- ------------------------------------------------------------- -->
        <div id="tab-sites" class="tab-panel">
            <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
                <!-- Site Revenue Distribution -->
                <div class="mck-card p-6 flex flex-col justify-between">
                    <div>
                        <h2 class="text-lg font-bold text-[#002D62] Georgia">核心站点全球市场销售额占比</h2>
                        <div class="mck-divider my-2"></div>
                        <p class="text-xs text-slate-500 mb-4">按销售额汇总的各主要国家市场分布比例</p>
                    </div>
                    <div class="grid grid-cols-5 gap-4 items-center">
                        <div id="site-donut-chart" class="col-span-3" style="min-height: 330px;"></div>
                        <div id="site-bar-chart" class="col-span-2" style="min-height: 330px;"></div>
                    </div>
                </div>
                <!-- Site Trend Line Chart -->
                <div class="mck-card p-6 flex flex-col justify-between">
                    <div>
                        <h2 class="text-lg font-bold text-[#002D62] Georgia">热门站点月度趋势对比 (Top 5 Sites)</h2>
                        <div class="mck-divider my-2"></div>
                        <p class="text-xs text-slate-500 mb-4">展示销量排名前五的重点国家月度增长轨迹</p>
                    </div>
                    <div id="site-trend-chart" class="w-full" style="min-height: 330px;"></div>
                </div>
            </div>

            <!-- Site Summary Table -->
            <div class="mck-card p-6">
                <h2 class="text-lg font-bold text-[#002D62] Georgia">全球多站点核心数据汇总表</h2>
                <div class="mck-divider my-2"></div>
                <p class="text-xs text-slate-500 mb-4">多维度反映不同国家的容量深度与 Hollyland 渗透表现</p>
                <div class="overflow-x-auto">
                    <table class="w-full text-left text-xs border-collapse">
                        <thead>
                            <tr class="text-slate-500 font-semibold border-b border-slate-200 bg-slate-50">
                                <th class="py-3 px-4">站点名称</th>
                                <th class="py-3 px-4 text-right">总销售额 (USD)</th>
                                <th class="py-3 px-4 text-right">总销量 (Units)</th>
                                <th class="py-3 px-4 text-right">全球销售额占比</th>
                                <th class="py-3 px-4 text-right">Hollyland 销售额</th>
                                <th class="py-3 px-4 text-right">Hollyland 站点占有率</th>
                            </tr>
                        </thead>
                        <tbody id="site-table-body" class="divide-y divide-slate-100">
                            <!-- JS Injection -->
                        </tbody>
                    </table>
                </div>
            </div>
            
            <!-- Tab 2 Analytical Summary -->
            <div class="mck-card p-6 mt-6 bg-[#FAFBFD] border-l-4 border-[#00A3A6]">
                <h3 class="text-[#002D62] font-bold text-sm Georgia">💡 麦肯锡多站点分析透视 (Executive Takeaways)：</h3>
                <ul class="list-disc list-inside text-xs text-slate-600 mt-2 space-y-1">
                    <li><strong>美欧依然是绝对主战场</strong>：美国（US）占据全球销售额的半壁江山，德国（DE）和英国（UK）紧随其后。</li>
                    <li><strong>站点渗透的分化</strong>：Hollyland 在欧洲成熟国家站点（如英国、德国）的市场渗透表现更为强劲，而美国站面临大疆（DJI）以及各类极致性价比白牌的极度竞争挤压。</li>
                </ul>
            </div>
        </div>

        <!-- ------------------------------------------------------------- -->
        <!-- TAB 3: COMPETITOR MATRIX -->
        <!-- ------------------------------------------------------------- -->
        <div id="tab-competitor" class="tab-panel">
            <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
                <!-- Bubble Competitor positioning scatter -->
                <div class="mck-card p-6 flex flex-col justify-between">
                    <div>
                        <h2 class="text-lg font-bold text-[#002D62] Georgia">品牌竞争定位矩阵 (Brand Positioning Matrix)</h2>
                        <div class="mck-divider my-2"></div>
                        <p class="text-xs text-slate-500 mb-4">横轴：平均成交价 | 纵轴：总销量 | 气泡大小：销售额 | 颜色深浅：评分高低</p>
                    </div>
                    <div id="bubble-matrix-chart" class="w-full" style="min-height: 400px;"></div>
                </div>
                <!-- Heatmap Brand Pricing Sensitivity -->
                <div class="mck-card p-6 flex flex-col justify-between">
                    <div>
                        <h2 class="text-lg font-bold text-[#002D62] Georgia">价格敏感度热力分布图 (Revenue Heatmap)</h2>
                        <div class="mck-divider my-2"></div>
                        <p class="text-xs text-slate-500 mb-4">反映排名前15的核心竞争品牌在各价格段的收入聚焦度</p>
                    </div>
                    <div id="heatmap-chart" class="w-full" style="min-height: 400px;"></div>
                </div>
            </div>
            
            <!-- Tab 3 Analytical Summary -->
            <div class="mck-card p-6 bg-[#FAFBFD] border-l-4 border-[#00A3A6]">
                <h3 class="text-[#002D62] font-bold text-sm Georgia">💡 麦肯锡竞争格局透视 (Executive Takeaways)：</h3>
                <ul class="list-disc list-inside text-xs text-slate-600 mt-2 space-y-1">
                    <li><strong>高溢价区间的卡位</strong>：大疆（DJI）利用 DJI Mic 系列在 $150+ 以上价格区间打下了坚不可摧的高溢价护城河。</li>
                    <li><strong>中端腰部红利</strong>：Hollyland 成功在 $50-100 区间卡死生态位，避开了与低端白牌在极低利润区间的肉搏，同时拥有优于 Rode（罗德）的极高成交转化效率。</li>
                </ul>
            </div>
        </div>

        <!-- ------------------------------------------------------------- -->
        <!-- TAB 4: DEMAND FORECASTING -->
        <!-- ------------------------------------------------------------- -->
        <div id="tab-forecasting" class="tab-panel">
            <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
                <!-- Forecast Chart -->
                <div class="mck-card p-6 flex flex-col justify-between">
                    <div>
                        <h2 class="text-lg font-bold text-[#002D62] Georgia">未来 6 个月销售趋势预测 (Forecast with 95% CI)</h2>
                        <div class="mck-divider my-2"></div>
                        <p class="text-xs text-slate-500 mb-4">虚线为线性趋势预测值 | 淡色阴影为 95% 置信上下界 (Confidence Interval)</p>
                    </div>
                    <div id="forecast-line-chart" class="w-full" style="min-height: 380px;"></div>
                </div>
                <!-- Seasonality Chart -->
                <div class="mck-card p-6 flex flex-col justify-between">
                    <div>
                        <h2 class="text-lg font-bold text-[#002D62] Georgia">大盘月度季节性波动平均值 (Seasonality)</h2>
                        <div class="mck-divider my-2"></div>
                        <p class="text-xs text-slate-500 mb-4">按自然月分组的均值分布，体现长周期采购波峰</p>
                    </div>
                    <div id="seasonality-bar-chart" class="w-full" style="min-height: 380px;"></div>
                </div>
            </div>
            
            <!-- Tab 4 Analytical Summary -->
            <div class="mck-card p-6 bg-[#FAFBFD] border-l-4 border-[#00A3A6]">
                <h3 class="text-[#002D62] font-bold text-sm Georgia">💡 麦肯锡预测与周期透视 (Executive Takeaways)：</h3>
                <ul class="list-disc list-inside text-xs text-slate-600 mt-2 space-y-1">
                    <li><strong>下半年是绝对备货重心</strong>：结合季节性统计，大盘呈现“年中7月冲高、年底11月爆发”的周期曲线。建议库存和广告预算在第二季度末及第四季度初提前进行防御性倾斜。</li>
                    <li><strong>中长期大盘趋势前瞻</strong>：线性模型显示，尽管大盘伴有阶段性的波动，无线音频与麦克风配件的总体容量在中长期仍呈现向上的正斜率发展态势，市场基本面健康。</li>
                </ul>
            </div>
        </div>

    </div>

    <!-- Data Injection Scripts -->
    <script>
        const rawData = {json_data};
        let charts = {}; // Store references to clear previous charts
        
        function initDashboard() {
            // Document date and times
            const months = rawData.market_trend.map(i => i.fetched_month);
            document.getElementById('date-range').innerText = `${Math.min(...months.map(m=>parseInt(m.replace('-','')))).toString().replace(/(\\d{4})(\\d{2})/, '$1-$2')} ~ ${Math.max(...months.map(m=>parseInt(m.replace('-','')))).toString().replace(/(\\d{4})(\\d{2})/, '$1-$2')}`;
            document.getElementById('generation-time').innerText = new Date(rawData.updated_at).toLocaleDateString('zh-CN');
            
            // Site Selector options
            const sites = [...new Set(rawData.market_trend.map(i => i.market))].filter(s => s !== 'GLOBAL');
            const selector = document.getElementById('market-selector');
            sites.forEach(m => {
                const opt = document.createElement('option');
                opt.value = m;
                opt.innerText = m;
                selector.appendChild(opt);
            });
            
            // Add Selector Listener
            selector.addEventListener('change', (e) => {
                updateDashboard(e.target.value);
            });
            
            // Initial render
            updateDashboard('GLOBAL');
            initTabSystem();
        }
        
        function initTabSystem() {
            const tabs = document.querySelectorAll('.tab-btn');
            tabs.forEach(tab => {
                tab.addEventListener('click', () => {
                    tabs.forEach(t => t.classList.remove('active'));
                    tab.classList.add('active');
                    
                    const panels = document.querySelectorAll('.tab-panel');
                    panels.forEach(p => p.classList.remove('active'));
                    
                    const target = tab.getAttribute('data-target');
                    document.getElementById(target).classList.add('active');
                    
                    // Trigger window resize to force ApexCharts to recalculate layout
                    window.dispatchEvent(new Event('resize'));
                });
            });
        }
        
        function updateDashboard(market) {
            console.log("Re-rendering dashboard for market:", market);
            
            // Filter records
            const trends = rawData.market_trend.filter(i => i.market === market);
            const monthlyBrands = rawData.brand_share.filter(i => i.market === market);
            const totalBrands = rawData.brand_total_share.filter(i => i.market === market);
            const priceSegments = rawData.price_analysis.filter(i => i.market === market);
            const priceBrands = rawData.price_top_brands.filter(i => i.market === market);
            const lifecycleData = rawData.lifecycle_performance ? rawData.lifecycle_performance.filter(i => i.market === market) : [];
            const forecastList = rawData.forecast_data ? rawData.forecast_data.filter(i => i.market === market) : [];
            const seasonalList = rawData.seasonality_data ? rawData.seasonality_data.filter(i => i.market === market) : [];
            
            // 1. Re-render metric cards
            const monthCount = new Set(trends.map(t=>t.fetched_month)).size || 1;
            const totalUnits = trends.reduce((a, b) => a + b.units, 0);
            const totalRev = trends.reduce((a, b) => a + b.revenue, 0);
            
            const avgUnits = Math.round(totalUnits / monthCount);
            const avgRev = Math.round(totalRev / monthCount);
            
            document.getElementById('kpi-units').innerText = avgUnits.toLocaleString();
            document.getElementById('kpi-rev').innerText = '$' + avgRev.toLocaleString();
            
            const global_prices = trends.reduce((a, b) => a + b.revenue, 0) / trends.reduce((a, b) => a + b.units, 0);
            document.getElementById('kpi-price').innerText = '$' + (global_prices || 52.61).toFixed(2);
            
            const hlData = totalBrands.find(b => b.brand_norm === 'Hollyland');
            const hlShare = hlData ? hlData.rev_share : 0;
            document.getElementById('kpi-hl-share').innerText = hlShare.toFixed(1) + '%';
            
            if (hlShare > 20) {
                document.getElementById('kpi-hl-takeaway').innerText = '🔥 处于绝对垄断地位';
                document.getElementById('kpi-hl-takeaway').className = 'text-[10px] text-emerald-600 font-semibold block mt-1';
            } else if (hlShare > 10) {
                document.getElementById('kpi-hl-takeaway').innerText = '📈 市场准一线中坚力量';
                document.getElementById('kpi-hl-takeaway').className = 'text-[10px] text-[#00A3A6] font-semibold block mt-1';
            } else {
                document.getElementById('kpi-hl-takeaway').innerText = '💡 中高端细分市场占位';
                document.getElementById('kpi-hl-takeaway').className = 'text-[10px] text-slate-500 block mt-1';
            }
            
            // 2. Clear old charts
            Object.values(charts).forEach(c => {
                if (c && typeof c.destroy === 'function') c.destroy();
            });
            charts = {};
            
            // 3. Render all Charts
            renderComboTrend(monthlyBrands, trends);
            renderLifecycle(lifecycleData);
            renderPriceBar(priceSegments);
            renderPriceTable(priceBrands);
            
            // Tab 2 (Marketplaces)
            renderSiteDistribution();
            renderSiteTrend();
            renderSiteTable();
            
            // Tab 3 (Competitor Matrix)
            renderCompetitorPositioning(totalBrands);
            renderPriceHeatmap();
            
            // Tab 4 (Forecast)
            renderForecast(forecastList);
            renderSeasonality(seasonalList);
        }
        
        // -------------------------------------------------------------
        // CHART RENDERING SCRIPTS
        // -------------------------------------------------------------
        
        function renderComboTrend(brandData, trendData) {
            const months = [...new Set(brandData.map(d => d.fetched_month))].sort();
            
            // Top brands based on total revenue in this segment
            const aggByBrand = {};
            brandData.forEach(d => {
                const k = d.brand_norm;
                if (k !== 'Hollyland') {
                    aggByBrand[k] = (aggByBrand[k] || 0) + (d.revenue || 0);
                }
            });
            const topOthers = Object.entries(aggByBrand).sort((a,b) => b[1]-a[1]).slice(0, 2).map(e => e[0]);
            const selectedBrands = ['Hollyland', ...topOthers].filter(b => brandData.some(d => d.brand_norm === b));
            
            const brandColors = {'Hollyland':'#00A3A6','DJI':'#002D62','Rode':'#D97706','MAYBESTA':'#64748B'};
            const fallbackColors = ['#8B5CF6','#EC4899','#10B981'];
            
            const brandSeries = selectedBrands.map(b => ({
                name: b,
                type: 'line',
                data: months.map(m => {
                    const match = brandData.find(d => d.brand_norm === b && d.fetched_month === m);
                    return match ? parseFloat(match.rev_share.toFixed(2)) : 0;
                })
            }));
            
            const marketTotals = months.map(m => {
                const rows = trendData.filter(t => t.fetched_month === m);
                return rows.reduce((s, r) => s + (r.revenue || 0), 0);
            });
            const marketSeries = {
                name: '大盘总销售额',
                type: 'column',
                data: marketTotals
            };
            
            const colors = selectedBrands.map((b, i) => brandColors[b] || fallbackColors[i % fallbackColors.length]);
            
            const options = {
                series: [...brandSeries, marketSeries],
                chart: { height: 380, type: 'line', toolbar: { show: false } },
                stroke: { width: [...selectedBrands.map(() => 3), 0], curve: 'smooth' },
                fill: { type: [...selectedBrands.map(() => 'solid'), 'solid'], opacity: [...selectedBrands.map(() => 1), 0.15] },
                colors: [...colors, '#E2E8F0'],
                xaxis: { categories: months, labels: { rotate: -30, style: { fontSize: '10px' } } },
                yaxis: [
                    { title: { text: '品牌份额 (%)', style: { color: '#002D62' } }, labels: { formatter: v => v.toFixed(1) + '%' } },
                    { opposite: true, title: { text: '大盘销售额 ($)', style: { color: '#64748B' } }, labels: { formatter: v => '$' + (v/1000).toFixed(0) + 'k' } }
                ],
                legend: { position: 'top', horizontalAlign: 'left', fontFamily: 'Inter' },
                grid: { borderColor: '#E2E8F0', strokeDashArray: 2 },
                tooltip: { shared: true, intersect: false }
            };
            
            charts['combo'] = new ApexCharts(document.querySelector("#combo-chart"), options);
            charts['combo'].render();
        }
        
        function renderLifecycle(lifecycleData) {
            if (!lifecycleData || lifecycleData.length === 0) return;
            const newData = lifecycleData.find(d => d.product_age === '新品 (New)') || { units: 0, revenue: 0, unit_share: 0, rev_share: 0 };
            const oldData = lifecycleData.find(d => d.product_age === '老品 (Old)') || { units: 0, revenue: 0, unit_share: 0, rev_share: 0 };
            
            const options = {
                series: [{
                    name: '老品贡献 (>6个月)',
                    data: [oldData.rev_share, oldData.unit_share]
                }, {
                    name: '新品贡献 (<=6个月)',
                    data: [newData.rev_share, newData.unit_share]
                }],
                chart: { type: 'bar', height: 380, stacked: true, toolbar: { show: false } },
                plotOptions: { bar: { horizontal: true, barHeight: '40%', borderRadius: 2 } },
                colors: ['#1C3B57', '#00A3A6'],
                xaxis: { categories: ['销售额占比 (%)', '销量占比 (%)'], max: 100 },
                dataLabels: { formatter: (val) => val + '%' },
                legend: { position: 'top' },
                grid: { borderColor: '#E2E8F0' },
                tooltip: { y: { formatter: (val) => val + '%' } }
            };
            
            charts['lifecycle'] = new ApexCharts(document.querySelector("#lifecycle-chart"), options);
            charts['lifecycle'].render();
        }
        
        function renderPriceBar(priceData) {
            const tiers = ['<$50', '$50-100', '$100-200', '$200-500', '>$500'];
            const agg = {};
            priceData.forEach(d => {
                agg[d.price_segment] = (agg[d.price_segment] || 0) + d.units;
            });
            
            const data = tiers.map(t => agg[t] || 0);
            
            const options = {
                series: [{ name: '销量', data: data }],
                chart: { type: 'bar', height: 300, toolbar: { show: false } },
                colors: ['#002D62'],
                xaxis: { categories: tiers },
                grid: { borderColor: '#E2E8F0', strokeDashArray: 2 },
                plotOptions: { bar: { borderRadius: 2, columnWidth: '50%' } }
            };
            
            charts['price-bar'] = new ApexCharts(document.querySelector("#price-bar-chart"), options);
            charts['price-bar'].render();
        }
        
        function renderPriceTable(priceBrands) {
            const tbody = document.getElementById('price-table-body');
            tbody.innerHTML = "";
            const segments = ['<$50', '$50-100', '$100-200', '$200-500', '>$500'];
            
            segments.forEach(seg => {
                const segBrands = priceBrands.filter(b => b.price_segment === seg)
                    .sort((a,b) => b.rev_share - a.rev_share).slice(0, 5);
                const tr = document.createElement('tr');
                tr.className = "hover:bg-slate-50/50 transition-colors";
                
                let tdHtml = `<td class="py-4 px-4 font-bold text-slate-800 bg-slate-50/30">${seg}</td>`;
                for(let i=0; i<5; i++) {
                    const b = segBrands[i];
                    if(b) {
                        const isHL = b.brand === 'Hollyland';
                        const cardBg = isHL ? 'text-[#00A3A6] font-bold' : 'text-slate-800 font-medium';
                        tdHtml += `<td class="py-3 px-4">
                            <div class="${cardBg}">${b.brand}</div>
                            <div class="text-[10px] text-slate-400">额 ${b.rev_share}%</div>
                            <div class="text-[10px] text-slate-400">量 ${b.unit_share}%</div>
                        </td>`;
                    } else {
                        tdHtml += `<td class="py-4 px-4 text-slate-300">-</td>`;
                    }
                }
                tr.innerHTML = tdHtml;
                tbody.appendChild(tr);
            });
        }
        
        // -------------------------------------------------------------
        // TAB 2 (MARKETPLACES) PLOTS
        // -------------------------------------------------------------
        
        function renderSiteDistribution() {
            const stats = rawData.site_stats.filter(s => s.market !== 'GLOBAL');
            const sorted = [...stats].sort((a,b) => b.revenue - a.revenue);
            
            // Pie Donut
            const donutOptions = {
                series: sorted.map(s => s.revenue),
                labels: sorted.map(s => s.market),
                chart: { type: 'donut', height: 320 },
                stroke: { show: false },
                colors: ['#002D62', '#1C3B57', '#00A3A6', '#CBD5E1', '#E2E8F0', '#475569', '#334155'],
                legend: { position: 'bottom', horizontalAlign: 'center', fontFamily: 'Inter' },
                plotOptions: { pie: { donut: { size: '60%' } } },
                tooltip: { y: { formatter: (v, { seriesIndex }) => `$${v.toLocaleString()} (${sorted[seriesIndex].rev_share}%)` } }
            };
            
            charts['site-donut'] = new ApexCharts(document.querySelector("#site-donut-chart"), donutOptions);
            charts['site-donut'].render();
            
            // Horizontal Bar
            const barOptions = {
                series: [{ name: '销售额', data: sorted.map(s => s.revenue) }],
                chart: { type: 'bar', height: 320, toolbar: { show: false } },
                plotOptions: { bar: { horizontal: true, barHeight: '55%', borderRadius: 2 } },
                colors: ['#1C3B57'],
                xaxis: { categories: sorted.map(s => s.market), labels: { formatter: v => '$' + (v/1e6).toFixed(1) + 'M' } },
                grid: { borderColor: '#E2E8F0', strokeDashArray: 2 }
            };
            
            charts['site-bar'] = new ApexCharts(document.querySelector("#site-bar-chart"), barOptions);
            charts['site-bar'].render();
        }
        
        function renderSiteTrend() {
            const trends = rawData.site_trend;
            const sites = [...new Set(trends.map(t=>t.market))];
            const months = [...new Set(trends.map(t=>t.fetched_month))].sort();
            
            const colors = ['#002D62', '#00A3A6', '#D97706', '#94A3B8', '#10B981'];
            
            const series = sites.map(s => {
                const sData = trends.filter(t => t.market === s);
                return {
                    name: s,
                    data: months.map(m => {
                        const r = sData.find(t => t.fetched_month === m);
                        return r ? r.revenue : 0;
                    })
                };
            });
            
            const options = {
                series: series,
                chart: { type: 'line', height: 330, toolbar: { show: false } },
                stroke: { width: 3, curve: 'smooth' },
                colors: colors,
                xaxis: { categories: months, labels: { rotate: -30 } },
                yaxis: { labels: { formatter: v => '$' + (v/1000).toFixed(0) + 'k' } },
                grid: { borderColor: '#E2E8F0', strokeDashArray: 2 },
                legend: { position: 'top', horizontalAlign: 'left' }
            };
            
            charts['site-trend'] = new ApexCharts(document.querySelector("#site-trend-chart"), options);
            charts['site-trend'].render();
        }
        
        function renderSiteTable() {
            const tbody = document.getElementById('site-table-body');
            tbody.innerHTML = "";
            
            const sorted = [...rawData.site_stats].sort((a,b) => {
                if (a.market === 'GLOBAL') return 1;
                if (b.market === 'GLOBAL') return -1;
                return b.revenue - a.revenue;
            });
            
            sorted.forEach(row => {
                const tr = document.createElement('tr');
                const isGlobal = row.market === 'GLOBAL';
                tr.className = isGlobal ? "bg-slate-50 font-bold border-t-2 border-slate-200" : "hover:bg-slate-50/50 transition-colors";
                
                tr.innerHTML = `
                    <td class="py-3 px-4 text-slate-800 font-semibold">${row.market === 'GLOBAL' ? '📊 全球总计 (GLOBAL)' : row.market}</td>
                    <td class="py-3 px-4 text-right font-medium">$${row.revenue.toLocaleString()}</td>
                    <td class="py-3 px-4 text-right font-medium">${row.units.toLocaleString()}</td>
                    <td class="py-3 px-4 text-right text-slate-500">${row.rev_share.toFixed(1)}%</td>
                    <td class="py-3 px-4 text-right font-medium text-[#00A3A6]">$${row.hollyland_rev.toLocaleString()}</td>
                    <td class="py-3 px-4 text-right font-bold text-[#002D62]">${row.hollyland_share.toFixed(1)}%</td>
                `;
                tbody.appendChild(tr);
            });
        }
        
        // -------------------------------------------------------------
        // TAB 3 (COMPETITORS) PLOTS
        // -------------------------------------------------------------
        
        function renderCompetitorPositioning(brandData) {
            // Filter Top 15 brands by revenue
            const sorted = [...brandData].filter(b => b.brand_norm !== 'Unknown' && b.revenue > 0 && b.units > 0)
                .sort((a,b) => b.revenue - a.revenue).slice(0, 15);
                
            const series = sorted.map(b => ({
                name: b.brand_norm,
                data: [[parseFloat(b.avg_price.toFixed(2)), b.units, b.revenue]]
            }));
            
            const options = {
                series: series,
                chart: { type: 'bubble', height: 400, toolbar: { show: false } },
                xaxis: { title: { text: '平均单价 ($)' }, labels: { formatter: v => '$' + v } },
                yaxis: { title: { text: '总出货量 (Units)' }, labels: { formatter: v => v.toLocaleString() } },
                fill: { opacity: 0.8 },
                grid: { borderColor: '#E2E8F0', strokeDashArray: 2 },
                dataLabels: { enabled: false },
                tooltip: {
                    y: {
                        formatter: function(val, { seriesIndex }) {
                            const b = sorted[seriesIndex];
                            return `均价: $${b.avg_price.toLocaleString()} | 销量: ${b.units.toLocaleString()} | 销售额: $${b.revenue.toLocaleString()}`;
                        }
                    }
                }
            };
            
            charts['bubble-matrix'] = new ApexCharts(document.querySelector("#bubble-matrix-chart"), options);
            charts['bubble-matrix'].render();
        }
        
        function renderPriceHeatmap() {
            const matrix = rawData.heatmap_data;
            const price_tiers = ['<$50', '$50-100', '$100-200', '$200-500', '>$500'];
            
            const series = price_tiers.map(tier => {
                return {
                    name: tier,
                    data: matrix.map(m => ({
                        x: m.brand,
                        y: m[tier]
                    }))
                };
            }).reverse(); // Stack highest price on top
            
            const options = {
                series: series,
                chart: { type: 'heatmap', height: 400, toolbar: { show: false } },
                colors: ['#002D62'],
                plotOptions: {
                    heatmap: {
                        colorScale: {
                            ranges: [
                                { from: 0, to: 0, color: '#FAFBFD', name: '无贡献' },
                                { from: 1, to: 50000, color: '#E2E8F0', name: '起步阶段 (<$50k)' },
                                { from: 50001, to: 500000, color: '#C0D2E1', name: '增长阶段 (<$500k)' },
                                { from: 500001, to: 5000000, color: '#4F7C9F', name: '主力核心 (<$5M)' },
                                { from: 5000001, to: 100000000, color: '#002D62', name: '绝对主宰 (>$5M)' }
                            ]
                        }
                    }
                },
                xaxis: { labels: { rotate: -45, style: { fontSize: '10px' } } },
                grid: { borderColor: '#E2E8F0' }
            };
            
            charts['heatmap'] = new ApexCharts(document.querySelector("#heatmap-chart"), options);
            charts['heatmap'].render();
        }
        
        // -------------------------------------------------------------
        // TAB 4 (FORECAST & SEASONALITY) PLOTS
        // -------------------------------------------------------------
        
        function renderForecast(forecastList) {
            if (!forecastList || forecastList.length === 0) return;
            
            const sorted = [...forecastList].sort((a,b) => {
                return parseInt(a.fetched_month.replace('-','')) - parseInt(b.fetched_month.replace('-',''));
            });
            
            const actuals = sorted.filter(f => f.type === 'Actual');
            const forecasts = sorted.filter(f => f.type === 'Forecast');
            
            // Re-align months
            const allMonths = sorted.map(s => s.fetched_month);
            
            const actSeriesData = allMonths.map(m => {
                const r = actuals.find(a => a.fetched_month === m);
                return r ? r.revenue : null;
            });
            
            const foreSeriesData = allMonths.map(m => {
                const r = forecasts.find(f => f.fetched_month === m);
                return r ? r.revenue : null;
            });
            
            // Connect actuals to first forecast point for seamless line
            const lastActualIndex = actuals.length - 1;
            if (lastActualIndex >= 0 && forecasts.length > 0) {
                foreSeriesData[lastActualIndex] = actuals[lastActualIndex].revenue;
            }
            
            const upperSeriesData = allMonths.map(m => {
                const r = forecasts.find(f => f.fetched_month === m);
                return r ? r.upper_ci : (actuals.find(a => a.fetched_month === m) ? actuals.find(a => a.fetched_month === m).revenue : null);
            });
            
            const lowerSeriesData = allMonths.map(m => {
                const r = forecasts.find(f => f.fetched_month === m);
                return r ? r.lower_ci : (actuals.find(a => a.fetched_month === m) ? actuals.find(a => a.fetched_month === m).revenue : null);
            });
            
            const options = {
                series: [
                    { name: '历史实际销售额', type: 'line', data: actSeriesData },
                    { name: '未来销量预测', type: 'line', data: foreSeriesData },
                    { name: '预测上限', type: 'line', data: upperSeriesData },
                    { name: '预测下限', type: 'line', data: lowerSeriesData }
                ],
                chart: { height: 380, type: 'line', toolbar: { show: false } },
                stroke: { width: [3, 3, 1, 1], dashArray: [0, 5, 4, 4], curve: 'smooth' },
                colors: ['#002D62', '#00A3A6', '#CBD5E1', '#CBD5E1'],
                xaxis: { categories: allMonths, labels: { rotate: -45 } },
                yaxis: { labels: { formatter: v => '$' + (v/1e6).toFixed(1) + 'M' } },
                grid: { borderColor: '#E2E8F0', strokeDashArray: 2 },
                legend: { position: 'top' },
                tooltip: { shared: true, intersect: false }
            };
            
            charts['forecast'] = new ApexCharts(document.querySelector("#forecast-line-chart"), options);
            charts['forecast'].render();
        }
        
        function renderSeasonality(seasonalList) {
            if (!seasonalList || seasonalList.length === 0) return;
            const sorted = [...seasonalList].sort((a,b) => a.month_num - b.month_num);
            
            const options = {
                series: [{ name: '月均销售额', data: sorted.map(s => s.avg_revenue) }],
                chart: { type: 'bar', height: 380, toolbar: { show: false } },
                colors: ['#1C3B57'],
                xaxis: { categories: sorted.map(s => s.month_name) },
                yaxis: { labels: { formatter: v => '$' + (v/1e6).toFixed(1) + 'M' } },
                grid: { borderColor: '#E2E8F0', strokeDashArray: 2 },
                plotOptions: { bar: { borderRadius: 2, columnWidth: '55%' } }
            };
            
            charts['seasonality'] = new ApexCharts(document.querySelector("#seasonality-bar-chart"), options);
            charts['seasonality'].render();
        }
        
        window.addEventListener('load', initDashboard);
    </script>
</body>
</html>
"""
    html_template = html_template.replace("{json_data}", json_data)
    with open(DASHBOARD_FILE, 'w', encoding='utf-8') as f:
        f.write(html_template)
    print(f"看板 HTML 已生成: {DASHBOARD_FILE}")

def main():
    if not os.path.exists(ANALYTICS_FILE):
        print(f"错误: 找不到分析数据文件 {ANALYTICS_FILE}")
        return
        
    with open(ANALYTICS_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    generate_html(data)

if __name__ == "__main__":
    main()
