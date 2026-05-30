# Handover: Amazon Market Analysis BI Tool

## 1. Project Overview
A Streamlit-based BI tool for analyzing Amazon market segments across multiple sites (US/UK). It features historical trend analysis, market concentration metrics (HHI, CR3), and 6-month demand forecasting.

## 2. Current Status
- **Infrastructure**: Fully refactored for multi-site/multi-category support.
- **Data Collection**: **3 months** of data (March 2026, February 2026, January 2026) have been fetched and saved for all 3 target segments.
- **Processing Engine**: `final_processor.py` has been executed successfully.
- **Output Generated**: `processed_market_data.pkl` is ready for the dashboard.
- **Dashboard**: `app.py` is ready to visualize processed data with a premium UI.

## 3. Directory Structure
```text
/Market_Analysis
├── raw_data/
│   ├── us/
│   │   ├── lavalier/ (2026-03.json, 2026-02.json, 2026-01.json)
│   │   └── transmitter/ (2026-03.json, 2026-02.json, 2026-01.json)
│   └── uk/
│       └── wireless/ (2026-03.json, 2026-02.json, 2026-01.json)
├── final_processor.py   # Aggregates raw JSONs into .pkl
├── app.py               # Streamlit dashboard
├── style.css            # Premium UI styling
├── chart_components.py  # Plotly chart builders
└── processed_market_data.pkl # CURRENT SOURCE FOR DASHBOARD
```

## 4. Key Configurations & Node IDs
- **US Lavalier**: `11091801:11974521:8882489011:11974711:11974761`
- **US Transmitter**: `11091801:11974521:8882489011:11974711:10677099011`
- **UK Wireless**: `340837031:407786031:407791031`
- **User Filter**: ASINs with monthly sales > 200.

## 5. Next Steps for Claude Code / Agent
1. **Backfill Earlier Data**: Continue fetching data for 2025 (Dec, Nov, Oct...) to build a full 24-month timeline.
   - Use `competitor_lookup` tool for each month.
   - Save to `raw_data/{site}/{category}/YYYY-MM.json`.
2. **Re-run Aggregation**:
   `.\venv\Scripts\python.exe final_processor.py`
3. **Launch Streamlit Dashboard**:
   `.\venv\Scripts\streamlit.exe run app.py`

## 6. Known Issues
- `collect_multi_site_data.py` (Automated script) has API auth/format issues (400 Bad Request). **Manual fetching via SellerSprite MCP tools is the current reliable method.**
- Terminal encoding might show garbled text for Chinese characters (like site names '美国', '英国'), but the data logic remains correct.
