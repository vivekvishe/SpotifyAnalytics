# 🎵 Spotify Analytics Dashboard

A Streamlit + DuckDB app for advanced Spotify artist analytics.

## Setup

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Usage

1. Open the app in your browser (http://localhost:8501)
2. Upload your two Spotify CSV files via the **sidebar**:
   - **Audience Timeline CSV** — `date, listeners, streams, followers`
   - **Songs CSV** — `song, listeners, streams, saves, release_date`
3. Use the date range filter to zoom in on any period

## Dashboard Tabs

| Tab | Content |
|-----|---------|
| 📈 Audience Trends | Multi-metric time series, 7-day rolling averages, monthly bar chart, day-of-week heatmap |
| 🎵 Song Performance | Top 10 leaderboard, saves vs streams scatter, stream share pie, full sortable table |
| 📅 Release Intelligence | Release timeline scatter, tracks released per month, avg streams per release window |
| 🔍 Deep Dive | Cumulative streams, follower conversion rate, live DuckDB SQL console, CSV export |
