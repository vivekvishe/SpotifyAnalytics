"""
Spotify Analytics Dashboard
============================
Streamlit + DuckDB app for advanced Spotify artist analytics.

Usage:
    pip install streamlit duckdb plotly pandas
    streamlit run app.py

Then upload your two CSVs via the sidebar:
  - Audience Timeline CSV  (columns: date, listeners, streams, followers)
  - Songs CSV              (columns: song, listeners, streams, saves, release_date)
"""

import io
import duckdb
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Spotify Analytics",
    page_icon="🎵",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
# Palette inspired by Jono Pandolfi ceramics: warm cream, terracotta, sage, dusty lavender, deep navy
st.markdown("""
<style>
    /* ── Global background: warm cream ── */
    .main, [data-testid="stAppViewContainer"], [data-testid="stMain"] {
        background-color: #FAF6F0 !important;
    }

    /* ── ALL text on light background = black ── */
    body, p, span, div, li, td, th, label, input, textarea,
    [data-testid="stMarkdownContainer"],
    [data-testid="stMarkdownContainer"] *,
    [data-testid="stText"],
    .stMarkdown, .stMarkdown *,
    [data-testid="stAppViewContainer"] p,
    [data-testid="stAppViewContainer"] span,
    [data-testid="stAppViewContainer"] div,
    [data-testid="stAppViewContainer"] li,
    [data-testid="stAppViewContainer"] label,
    h1, h2, h3, h4, h5, h6 {
        color: #111111 !important;
    }

    /* ── Sidebar: dark background → white text ── */
    [data-testid="stSidebar"] {
        background-color: #6e7586 !important;
        min-width: 340px !important;
        max-width: 340px !important;
    }
    [data-testid="stSidebar"] > div:first-child {
        width: 340px !important;
    }
    [data-testid="stSidebar"],
    [data-testid="stSidebar"] *,
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] span,
    [data-testid="stSidebar"] div,
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3,
    [data-testid="stSidebar"] h4,
    [data-testid="stSidebar"] li,
    [data-testid="stSidebar"] small,
    [data-testid="stSidebar"] .stCaption {
        color: #FFFFFF !important;
    }

    /* ── Section headers on light bg: dark terracotta = readable ── */
    .section-header {
        font-size: 1.25rem;
        font-weight: 800;
        color: #111111 !important;
        border-bottom: 3px solid #C1553A;
        padding-bottom: 6px;
        margin: 28px 0 16px 0;
        letter-spacing: 0.02em;
    }

    /* ── KPI metric cards: white card, black text ── */
    div[data-testid="stMetric"] {
        background-color: #FFFFFF !important;
        border-radius: 12px;
        padding: 16px 20px;
        border-left: 5px solid #C1553A;
        box-shadow: 0 2px 12px rgba(28,43,58,0.08);
    }
    div[data-testid="stMetric"] label,
    div[data-testid="stMetric"] [data-testid="stMetricLabel"],
    div[data-testid="stMetric"] [data-testid="stMetricLabel"] * {
        color: #444444 !important;
        font-weight: 700 !important;
        font-size: 0.78rem !important;
        text-transform: uppercase;
        letter-spacing: 0.06em;
    }
    div[data-testid="stMetric"] [data-testid="stMetricValue"],
    div[data-testid="stMetric"] [data-testid="stMetricValue"] * {
        color: #111111 !important;
        font-size: 1.9rem !important;
        font-weight: 800 !important;
    }
    div[data-testid="stMetric"] [data-testid="stMetricDelta"],
    div[data-testid="stMetric"] [data-testid="stMetricDelta"] * {
        color: #5A7A6A !important;
    }

    /* ── Tabs: light bg tabs → black text; active tab → white text ── */
    .stTabs [data-baseweb="tab-list"] {
        background-color: #EDE8E0 !important;
        border-radius: 10px 10px 0 0;
        gap: 4px;
        padding: 4px 4px 0 4px;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: transparent !important;
        font-weight: 600;
        border-radius: 8px 8px 0 0;
        padding: 10px 20px;
    }
    .stTabs [data-baseweb="tab"] p,
    .stTabs [data-baseweb="tab"] span,
    .stTabs [data-baseweb="tab"] div {
        color: #111111 !important;
    }
    .stTabs [aria-selected="true"] {
        background-color: #C1553A !important;
    }
    .stTabs [aria-selected="true"] p,
    .stTabs [aria-selected="true"] span,
    .stTabs [aria-selected="true"] div {
        color: #FFFFFF !important;
    }

    /* ── Primary buttons: dark bg → white text ── */
    .stButton > button {
        background-color: #C1553A !important;
        color: #FFFFFF !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 700 !important;
        padding: 8px 20px !important;
    }
    .stButton > button:hover {
        background-color: #A8432A !important;
        color: #FFFFFF !important;
    }
    .stButton > button * { color: #FFFFFF !important; }

    /* ── Download buttons: dark bg → white text ── */
    .stDownloadButton > button {
        background-color: #5A7A6A !important;
        color: #FFFFFF !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
    }
    .stDownloadButton > button * { color: #FFFFFF !important; }

    /* ── Text area: white bg → black text ── */
    textarea, .stTextArea textarea {
        background-color: #FFFFFF !important;
        color: #111111 !important;
        border: 1.5px solid #C1553A !important;
        border-radius: 8px !important;
    }

    /* ── Caption / small text on light bg ── */
    .stCaption, .stCaption *, small {
        color: #555555 !important;
    }

    /* ── File uploader in sidebar: label = white, dropzone text = black ── */
    [data-testid="stSidebar"] [data-testid="stFileUploader"] label,
    [data-testid="stSidebar"] [data-testid="stFileUploader"] > label {
        color: #FFFFFF !important;
    }
    /* Dropzone box: white background, all inner text forced black */
    [data-testid="stFileUploaderDropzone"] {
        background-color: #FFFFFF !important;
        border: 2px dashed #C1553A !important;
        border-radius: 8px !important;
    }
    [data-testid="stFileUploaderDropzone"] *,
    [data-testid="stFileUploaderDropzone"] span,
    [data-testid="stFileUploaderDropzone"] p,
    [data-testid="stFileUploaderDropzone"] small,
    [data-testid="stFileUploaderDropzone"] div {
        color: #111111 !important;
    }
    /* Browse files button inside dropzone */
    [data-testid="stFileUploaderDropzone"] button {
        background-color: #6e7586 !important;
        border-color: #1C2B3A !important;
        border-radius: 6px !important;
    }
    [data-testid="stFileUploaderDropzone"] button * {
        color: #FFFFFF !important;
    }

</style>
""", unsafe_allow_html=True)

# ── Plotly theme: warm cream background, deep navy text ──────────────────────
PLOTLY_THEME = dict(
    template="plotly_white",
    paper_bgcolor="#FAF6F0",
    plot_bgcolor="#FAF6F0",
    font_color="#1C2B3A",
)

# Jono Pandolfi-inspired palette
TERRACOTTA  = "#C1553A"
SAGE        = "#5A7A6A"
LAVENDER    = "#9B8DB5"
DUNE        = "#C4A882"
NAVY        = "#1C2B3A"
BLUSH       = "#E8A598"
MOSS        = "#7A9B6A"
CLAY        = "#B87355"
SKY         = "#7AB0C8"
PERSIMMON   = "#E8724A"

HAPPY_COLORS = [TERRACOTTA, SAGE, LAVENDER, DUNE, BLUSH, MOSS, SKY, CLAY, PERSIMMON, "#D4B8E0"]
HAPPY_SCALE  = [[0.0, "#EDE8E0"], [0.35, "#C4A882"], [0.7, "#C1553A"], [1.0, "#1C2B3A"]]
COLOR_SEQ    = HAPPY_COLORS


# ── Helpers ───────────────────────────────────────────────────────────────────
@st.cache_data(show_spinner=False)
def load_csv(file_bytes: bytes, name: str) -> pd.DataFrame:
    df = pd.read_csv(io.BytesIO(file_bytes))
    df.columns = df.columns.str.strip().str.lstrip("\ufeff")
    return df


def register_tables(con: duckdb.DuckDBPyConnection, timeline: pd.DataFrame, songs: pd.DataFrame):
    con.register("timeline", timeline)
    con.register("songs", songs)


def fmt(n) -> str:
    if n is None:
        return "–"
    n = int(n)
    if n >= 1_000_000:
        return f"{n/1_000_000:.2f}M"
    if n >= 1_000:
        return f"{n/1_000:.1f}K"
    return str(n)


def badge(label, color):
    return f'<div style="background:{color};color:#fff;padding:6px 14px;border-radius:6px;font-weight:700;font-size:0.85rem;display:inline-block;margin-top:4px">{label}</div>'


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<p style="font-size:2rem;font-weight:900;color:#fff;margin:0 0 8px 0;">🎵 Spotify Analytics</p>', unsafe_allow_html=True)
    st.markdown("---")

    # Artist CTA
    st.markdown(
        '<a href="https://open.spotify.com/artist/1j71gO9gHulj7w1KXBtDXi" target="_blank" '
        'style="display:block;background:#C1553A;color:#fff;text-align:center;'
        'padding:10px 16px;border-radius:8px;font-weight:700;font-size:0.95rem;'
        'text-decoration:none;margin-bottom:12px;">🎵 Follow on Spotify</a>',
        unsafe_allow_html=True
    )

    # Playlist embed
    st.markdown("**🎧 Listen Now**")
    st.components.v1.iframe(
        "https://open.spotify.com/embed/playlist/38PWTug6fz72EdznsQsP0K?utm_source=generator",
        height=200,
        scrolling=False
    )

    st.markdown("---")
    st.subheader("📂 Upload CSVs")
    timeline_file = st.file_uploader("Audience Timeline CSV", type="csv", key="timeline")
    songs_file    = st.file_uploader("Songs CSV",             type="csv", key="songs")
    st.markdown("---")
    st.caption("Built with Streamlit + DuckDB 🦆")


# ── Guard ─────────────────────────────────────────────────────────────────────
if not timeline_file or not songs_file:
    st.markdown("""
    ## 🎵 Spotify Analytics Dashboard
    Upload your two Spotify CSV exports in the **sidebar** to get started.

    **Required files:**
    - **Audience Timeline CSV** — columns: `date, listeners, streams, followers`
    - **Songs CSV** — columns: `song, listeners, streams, saves, release_date`
    """)
    st.stop()


# ── Load data ─────────────────────────────────────────────────────────────────
with st.spinner("Loading data into DuckDB…"):
    timeline_df = load_csv(timeline_file.read(), "timeline")
    songs_df    = load_csv(songs_file.read(),    "songs")

    timeline_df["date"]      = pd.to_datetime(timeline_df["date"])
    songs_df["release_date"] = pd.to_datetime(songs_df["release_date"])

    for col in ["listeners", "streams", "followers"]:
        if col in timeline_df.columns:
            timeline_df[col] = pd.to_numeric(timeline_df[col], errors="coerce").fillna(0).astype(int)
    for col in ["listeners", "streams", "saves"]:
        if col in songs_df.columns:
            songs_df[col] = pd.to_numeric(songs_df[col], errors="coerce").fillna(0).astype(int)

    con = duckdb.connect(":memory:")
    register_tables(con, timeline_df, songs_df)


# ── Date filter ───────────────────────────────────────────────────────────────
min_date = timeline_df["date"].min().date()
max_date = timeline_df["date"].max().date()

with st.sidebar:
    st.subheader("📅 Date Range")
    date_range = st.date_input("Select range", value=(min_date, max_date),
                               min_value=min_date, max_value=max_date)
    if len(date_range) == 2:
        start_date, end_date = date_range
    else:
        start_date, end_date = min_date, max_date

tl = timeline_df[(timeline_df["date"].dt.date >= start_date) &
                 (timeline_df["date"].dt.date <= end_date)].copy()


# ── Calculations ──────────────────────────────────────────────────────────────
total_streams   = int(tl["streams"].sum())
total_listeners = int(tl["listeners"].sum()) if tl["listeners"].sum() > 0 else int(songs_df["listeners"].sum())
max_listeners   = int(tl["listeners"].max()) if tl["listeners"].max() > 0 else int(songs_df["listeners"].max())
total_followers = int(tl.sort_values("date").iloc[-1]["followers"])
follower_growth = int(tl.sort_values("date").iloc[-1]["followers"] - tl.sort_values("date").iloc[0]["followers"])
total_songs     = len(songs_df)
total_saves     = int(songs_df["saves"].sum())

# Advanced KPIs
fcr                    = (follower_growth / total_listeners * 100) if total_listeners > 0 else 0
stickiness             = (total_streams / total_listeners) if total_listeners > 0 else 0
save_rate              = (total_saves / total_streams * 100) if total_streams > 0 else 0
stream_listener_ratio  = (total_streams / total_listeners) if total_listeners > 0 else 0
save_rate_by_listeners = (total_saves / total_listeners * 100) if total_listeners > 0 else 0


# ── Status helpers ────────────────────────────────────────────────────────────
def fcr_status(v):
    if v >= 2:   return ("🟢 Healthy", "#2d6a4f")
    if v >= 0.5: return ("🟡 Low", "#b5770d")
    return ("🔴 Critical", "#6e7586")

def stickiness_status(v):
    if v >= 3:   return ("🟢 Strong", "#2d6a4f")
    if v >= 1.5: return ("🟡 Low", "#b5770d")
    return ("🔴 Very Low", "#6e7586")

def save_status(v):
    if v >= 6:   return ("🟢 Healthy", "#2d6a4f")
    if v >= 2:   return ("🟡 Low", "#b5770d")
    return ("🔴 Danger", "#6e7586")

def slr_status(v):
    if v >= 2.0: return ("🟢 Healthy", "#2d6a4f")
    if v >= 1.2: return ("🟡 Low", "#b5770d")
    return ("🔴 Very Low", "#6e7586")

def slr_save_status(v):
    if v >= 10:  return ("🟢 Healthy", "#2d6a4f")
    if v >= 3:   return ("🟡 Low", "#b5770d")
    return ("🔴 Danger", "#6e7586")

fcr_label,      fcr_color      = fcr_status(fcr)
stick_label,    stick_color    = stickiness_status(stickiness)
save_label,     save_color     = save_status(save_rate)
slr_label,      slr_color      = slr_status(stream_listener_ratio)
slr_save_label, slr_save_color = slr_save_status(save_rate_by_listeners)


# ══════════════════════════════════════════════════════════════════════════════
# ROW 1 — Base Metrics
# ══════════════════════════════════════════════════════════════════════════════
st.markdown('<div class="section-header">📊 Key Metrics</div>', unsafe_allow_html=True)
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("🎧 Total Streams",   fmt(total_streams))
c2.metric("👥 Peak Listeners",  fmt(max_listeners))
c3.metric("❤️ Followers",       fmt(total_followers))
c4.metric("📈 Follower Growth", f"+{fmt(follower_growth)}")
c5.metric("🎵 Catalogue Size",  f"{total_songs} tracks")


# ══════════════════════════════════════════════════════════════════════════════
# ROW 2 — Advanced Health KPIs
# ══════════════════════════════════════════════════════════════════════════════
st.markdown('<div class="section-header">🧠 Advanced Health KPIs</div>', unsafe_allow_html=True)
a1, a2, a3 = st.columns(3)

with a1:
    st.metric("🎯 Fan Conversion Rate", f"{fcr:.2f}%",
              help="New Followers ÷ Total Listeners × 100. Healthy = 2%+.")
    st.markdown(badge(fcr_label, fcr_color), unsafe_allow_html=True)
    if fcr < 0.5:
        st.caption("⚠️ Only 1 in 1,000 listeners is following. Improve your profile bio, photos, and artist story.")
    elif fcr < 2:
        st.caption("💡 Decent but room to grow. Try adding a compelling artist bio and pinning your best track.")
    else:
        st.caption("✅ Great job converting listeners into fans!")

with a2:
    st.metric("🔁 Content Stickiness", f"{stickiness:.2f}x",
              help="Total Streams ÷ Total Listeners. Healthy = 3x+. Shows if listeners replay your music.")
    st.markdown(badge(stick_label, stick_color), unsafe_allow_html=True)
    if stickiness < 1.5:
        st.caption("⚠️ Listeners aren't coming back. Focus on more cohesive playlists and EPs.")
    elif stickiness < 3:
        st.caption("💡 Some replays but could be stronger. Try releasing music in series or themes.")
    else:
        st.caption("✅ Listeners are hooked and coming back for more!")

with a3:
    st.metric("💾 Save-to-Stream Ratio", f"{save_rate:.2f}%",
              help="Total Saves ÷ Total Streams × 100. Healthy = 6–10%.")
    st.markdown(badge(save_label, save_color), unsafe_allow_html=True)
    if save_rate < 2:
        st.caption("⚠️ Almost nobody is saving your tracks. Try stronger hooks and memorable melodies.")
    elif save_rate < 6:
        st.caption("💡 Below benchmark. Try releasing shorter, more memorable hooks to drive saves.")
    else:
        st.caption("✅ Healthy save rate — listeners want your music in their library!")


# ══════════════════════════════════════════════════════════════════════════════
# ROW 3 — Engagement Depth KPIs
# ══════════════════════════════════════════════════════════════════════════════
st.markdown('<div class="section-header">🎯 Engagement Depth KPIs</div>', unsafe_allow_html=True)
b1, b2, b3, b4 = st.columns(4)

with b1:
    st.metric("🔂 Stream-to-Listener Ratio", f"{stream_listener_ratio:.2f}x",
              help="Total Streams ÷ Unique Listeners. 2.0+ means people are repeating the song.")
    st.markdown(badge(slr_label, slr_color), unsafe_allow_html=True)
    if stream_listener_ratio < 1.2:
        st.caption("⚠️ People are not replaying. Songs may not be hooking listeners in.")
    elif stream_listener_ratio < 2.0:
        st.caption("💡 Some replays but below 2.0x benchmark. Work on more replayable hooks.")
    else:
        st.caption("✅ Listeners are coming back to replay — great sign of a strong track!")

with b2:
    st.metric("💿 Save Rate (by Listeners)", f"{save_rate_by_listeners:.2f}%",
              help="Saves ÷ Listeners × 100. Healthy = 3–10%. Below 3% suggests passive listening.")
    st.markdown(badge(slr_save_label, slr_save_color), unsafe_allow_html=True)
    if save_rate_by_listeners < 3:
        st.caption("⚠️ Very few listeners are saving. Suggests passive or algorithm-driven listening.")
    elif save_rate_by_listeners < 10:
        st.caption("💡 Decent but aim for 10%+. Try music that rewards repeated listens.")
    else:
        st.caption("✅ Strong save rate — your listeners are actively keeping your music!")

with b3:
    st.metric("⏭️ Skip Rate", "N/A",
              help="Skips ÷ Total Plays. Benchmark: under 25%. Not in standard Spotify CSV exports.")
    st.markdown(badge("⚪ Data Not Available", "#6c757d"), unsafe_allow_html=True)
    st.caption("📊 Requires Spotify for Artists advanced data. Benchmark: under 25% skips.")

with b4:
    st.metric("🎯 Intent Rate", "N/A",
              help="Streams from Profile/Library ÷ Total Streams. Benchmark: 20%+.")
    st.markdown(badge("⚪ Data Not Available", "#6c757d"), unsafe_allow_html=True)
    st.caption("📊 Requires Spotify for Artists stream source breakdown. Benchmark: 20%+.")


# ── Tab layout ────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs(["📈 Audience Trends", "🎵 Song Performance", "📅 Release Intelligence", "🔍 Deep Dive"])


# ════════════════════════════════════════════════════════════════════════════
# TAB 1 — Audience Trends
# ════════════════════════════════════════════════════════════════════════════
with tab1:
    st.markdown('<div class="section-header">Audience Growth Over Time</div>', unsafe_allow_html=True)

    fig = make_subplots(rows=3, cols=1, shared_xaxes=True,
                        subplot_titles=("Streams", "Listeners", "Followers"),
                        vertical_spacing=0.08)
    fig.add_trace(go.Scatter(x=tl["date"], y=tl["streams"],
                             fill="tozeroy", line=dict(color=TERRACOTTA, width=2),
                             fillcolor="rgba(193,85,58,0.15)", name="Streams"), row=1, col=1)
    fig.add_trace(go.Scatter(x=tl["date"], y=tl["listeners"],
                             fill="tozeroy", line=dict(color=SAGE, width=2),
                             fillcolor="rgba(90,122,106,0.15)", name="Listeners"), row=2, col=1)
    fig.add_trace(go.Scatter(x=tl["date"], y=tl["followers"],
                             fill="tozeroy", line=dict(color=LAVENDER, width=2),
                             fillcolor="rgba(155,141,181,0.15)", name="Followers"), row=3, col=1)
    fig.update_layout(height=550, showlegend=True, **PLOTLY_THEME,
                      title_text="Streams · Listeners · Followers Timeline")
    st.plotly_chart(fig, use_container_width=True)

    st.markdown('<div class="section-header">7-Day Rolling Averages</div>', unsafe_allow_html=True)
    tl_roll = tl.set_index("date").sort_index()
    tl_roll["streams_7d"]   = tl_roll["streams"].rolling(7).mean()
    tl_roll["listeners_7d"] = tl_roll["listeners"].rolling(7).mean()
    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(x=tl_roll.index, y=tl_roll["streams_7d"],
                              name="Streams (7d avg)", line=dict(color=TERRACOTTA, width=3)))
    fig2.add_trace(go.Scatter(x=tl_roll.index, y=tl_roll["listeners_7d"],
                              name="Listeners (7d avg)", line=dict(color=SAGE, width=3)))
    fig2.update_layout(height=320, **PLOTLY_THEME, title="Smoothed Trends (7-day rolling avg)")
    st.plotly_chart(fig2, use_container_width=True)

    st.markdown('<div class="section-header">Monthly Summary</div>', unsafe_allow_html=True)
    monthly = con.execute("""
        SELECT strftime(date, '%Y-%m') AS month,
               SUM(streams)   AS total_streams,
               AVG(listeners) AS avg_listeners,
               MAX(followers) AS peak_followers
        FROM timeline
        WHERE date >= ? AND date <= ?
        GROUP BY month ORDER BY month
    """, [str(start_date), str(end_date)]).df()
    fig3 = px.bar(monthly, x="month", y="total_streams",
                  color="total_streams", color_continuous_scale=HAPPY_SCALE,
                  labels={"total_streams": "Total Streams", "month": "Month"},
                  title="Monthly Stream Volume")
    fig3.update_layout(**PLOTLY_THEME, height=320)
    st.plotly_chart(fig3, use_container_width=True)

    st.markdown('<div class="section-header">Streams by Day of Week</div>', unsafe_allow_html=True)
    tl_dow = tl.copy()
    tl_dow["dow"] = tl_dow["date"].dt.day_name()
    dow_order = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
    dow_agg = tl_dow.groupby("dow")["streams"].mean().reindex(dow_order).reset_index()
    fig4 = px.bar(dow_agg, x="dow", y="streams",
                  color="streams", color_continuous_scale=HAPPY_SCALE,
                  title="Average Daily Streams by Day of Week",
                  labels={"streams": "Avg Streams", "dow": ""})
    fig4.update_layout(**PLOTLY_THEME, height=300)
    st.plotly_chart(fig4, use_container_width=True)


# ════════════════════════════════════════════════════════════════════════════
# TAB 2 — Song Performance
# ════════════════════════════════════════════════════════════════════════════
with tab2:
    st.markdown('<div class="section-header">Song Leaderboard</div>', unsafe_allow_html=True)
    songs_sorted = songs_df.sort_values("streams", ascending=False).reset_index(drop=True)
    songs_sorted.index += 1

    top10 = songs_sorted.head(10)
    fig5 = px.bar(top10, x="streams", y="song", orientation="h",
                  color="streams", color_continuous_scale=HAPPY_SCALE,
                  title="Top 10 Songs by Streams",
                  labels={"streams": "Total Streams", "song": ""})
    fig5.update_layout(**PLOTLY_THEME, height=380, yaxis=dict(autorange="reversed"))
    st.plotly_chart(fig5, use_container_width=True)

    if songs_df["saves"].sum() > 0:
        st.markdown('<div class="section-header">Saves vs Streams</div>', unsafe_allow_html=True)
        fig6 = px.scatter(songs_df, x="streams", y="saves", text="song",
                          size="streams", color="streams", color_continuous_scale=HAPPY_SCALE,
                          title="Save Rate vs Stream Volume",
                          labels={"streams": "Streams", "saves": "Saves"})
        fig6.update_traces(textposition="top center")
        fig6.update_layout(**PLOTLY_THEME, height=400)
        st.plotly_chart(fig6, use_container_width=True)

    st.markdown('<div class="section-header">Full Song Catalogue</div>', unsafe_allow_html=True)
    display_songs = songs_sorted.copy()
    display_songs["release_date"] = display_songs["release_date"].dt.strftime("%Y-%m-%d")
    st.dataframe(display_songs, use_container_width=True,
                 column_config={
                     "streams": st.column_config.ProgressColumn("Streams", format="%d", min_value=0,
                                                                  max_value=int(songs_sorted["streams"].max())),
                     "saves":   st.column_config.NumberColumn("Saves"),
                 })

    st.markdown('<div class="section-header">Stream Share by Song</div>', unsafe_allow_html=True)
    pie_df = songs_sorted.copy()
    if len(pie_df) > 8:
        top8  = pie_df.head(8)
        other = pd.DataFrame([{"song": "Other", "streams": pie_df.iloc[8:]["streams"].sum()}])
        pie_df = pd.concat([top8, other], ignore_index=True)
    fig7 = px.pie(pie_df, values="streams", names="song",
                  color_discrete_sequence=HAPPY_COLORS,
                  title="Stream Share Distribution")
    fig7.update_layout(**PLOTLY_THEME, height=400)
    st.plotly_chart(fig7, use_container_width=True)


# ════════════════════════════════════════════════════════════════════════════
# TAB 3 — Release Intelligence
# ════════════════════════════════════════════════════════════════════════════
with tab3:
    st.markdown('<div class="section-header">Release Timeline</div>', unsafe_allow_html=True)
    songs_rel = songs_df.sort_values("release_date")
    fig8 = px.scatter(songs_rel, x="release_date", y="streams",
                      size="streams", color="streams", color_continuous_scale=HAPPY_SCALE,
                      hover_name="song", title="Stream Performance by Release Date",
                      labels={"release_date": "Release Date", "streams": "Total Streams"})
    fig8.update_layout(**PLOTLY_THEME, height=400)
    st.plotly_chart(fig8, use_container_width=True)

    songs_rel["release_month"] = songs_rel["release_date"].dt.to_period("M").astype(str)
    monthly_rel = songs_rel.groupby("release_month").agg(
        tracks=("song", "count"), total_streams=("streams", "sum")
    ).reset_index()

    col_a, col_b = st.columns(2)
    with col_a:
        fig9 = px.bar(monthly_rel, x="release_month", y="tracks",
                      color="tracks", color_continuous_scale=HAPPY_SCALE,
                      title="Tracks Released per Month",
                      labels={"tracks": "# Tracks", "release_month": "Month"})
        fig9.update_layout(**PLOTLY_THEME, height=300)
        st.plotly_chart(fig9, use_container_width=True)
    with col_b:
        fig10 = px.bar(monthly_rel, x="release_month", y="total_streams",
                       color="total_streams", color_continuous_scale=HAPPY_SCALE,
                       title="Total Streams by Release Month",
                       labels={"total_streams": "Streams", "release_month": "Month"})
        fig10.update_layout(**PLOTLY_THEME, height=300)
        st.plotly_chart(fig10, use_container_width=True)

    st.markdown('<div class="section-header">Release Efficiency (Streams per Track)</div>', unsafe_allow_html=True)
    efficiency = con.execute("""
        SELECT strftime(release_date, '%Y-%m') AS release_month,
               COUNT(*)  AS tracks,
               SUM(streams) AS total_streams,
               AVG(streams) AS avg_streams_per_track
        FROM songs
        GROUP BY release_month
        ORDER BY avg_streams_per_track DESC
    """).df()
    fig11 = px.bar(efficiency, x="release_month", y="avg_streams_per_track",
                   color="avg_streams_per_track", color_continuous_scale=HAPPY_SCALE,
                   title="Avg Streams per Track by Release Month",
                   labels={"avg_streams_per_track": "Avg Streams/Track", "release_month": "Month"})
    fig11.update_layout(**PLOTLY_THEME, height=320)
    st.plotly_chart(fig11, use_container_width=True)


# ════════════════════════════════════════════════════════════════════════════
# TAB 4 — Deep Dive / Custom SQL
# ════════════════════════════════════════════════════════════════════════════
with tab4:
    st.markdown('<div class="section-header">📊 Artist Snapshot</div>', unsafe_allow_html=True)
    tl_cum = tl.sort_values("date").copy()
    tl_cum["cumulative_streams"] = tl_cum["streams"].cumsum()
    fig12 = px.area(tl_cum, x="date", y="cumulative_streams",
                    title="Cumulative Streams Over Time",
                    color_discrete_sequence=[TERRACOTTA],
                    labels={"cumulative_streams": "Total Streams", "date": "Date"})
    fig12.update_traces(fillcolor="rgba(193,85,58,0.2)", line=dict(color=TERRACOTTA, width=2))
    fig12.update_layout(**PLOTLY_THEME, height=320)
    st.plotly_chart(fig12, use_container_width=True)

    st.markdown('<div class="section-header">Follower Conversion Rate</div>', unsafe_allow_html=True)
    tl_conv = tl.copy()
    tl_conv["conversion_rate"] = (tl_conv["followers"] / tl_conv["streams"].replace(0, pd.NA)) * 100
    fig13 = px.line(tl_conv, x="date", y="conversion_rate",
                    title="Follower / Stream Conversion Rate (%)",
                    color_discrete_sequence=[SAGE],
                    labels={"conversion_rate": "Conversion %", "date": "Date"})
    fig13.update_traces(line=dict(width=3))
    fig13.update_layout(**PLOTLY_THEME, height=300)
    st.plotly_chart(fig13, use_container_width=True)

    st.markdown('<div class="section-header">🦆 Custom DuckDB SQL Query</div>', unsafe_allow_html=True)
    st.caption("Available tables: `timeline` (date, listeners, streams, followers)  |  `songs` (song, listeners, streams, saves, release_date)")

    default_sql = """SELECT song, streams, saves,
       ROUND(saves * 100.0 / NULLIF(streams, 0), 2) AS save_rate_pct
FROM songs
ORDER BY save_rate_pct DESC NULLS LAST
LIMIT 20"""

    sql_input = st.text_area("SQL Query", value=default_sql, height=140)
    if st.button("▶ Run Query", type="primary"):
        try:
            result = con.execute(sql_input).df()
            st.dataframe(result, use_container_width=True)
            if len(result) > 0 and result.shape[1] >= 2:
                numeric_cols = result.select_dtypes("number").columns.tolist()
                non_numeric  = [c for c in result.columns if c not in numeric_cols]
                if numeric_cols and non_numeric:
                    fig_sql = px.bar(result.head(20), x=non_numeric[0], y=numeric_cols[0],
                                     color=numeric_cols[0], color_continuous_scale=HAPPY_SCALE,
                                     title=f"{numeric_cols[0]} by {non_numeric[0]}")
                    fig_sql.update_layout(**PLOTLY_THEME, height=350)
                    st.plotly_chart(fig_sql, use_container_width=True)
        except Exception as e:
            st.error(f"Query error: {e}")

    st.markdown('<div class="section-header">⬇️ Export Data</div>', unsafe_allow_html=True)
    col_dl1, col_dl2 = st.columns(2)
    with col_dl1:
        st.download_button("Download Timeline CSV", tl.to_csv(index=False),
                           "timeline_filtered.csv", "text/csv")
    with col_dl2:
        st.download_button("Download Songs CSV", songs_df.to_csv(index=False),
                           "songs.csv", "text/csv")