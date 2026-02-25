"""
Blue Frog — Spotify Analytics Dashboard
========================================
Streamlit + DuckDB | Run: streamlit run app.py
"""

import io
import duckdb
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

st.set_page_config(
    page_title="Blue Frog · Spotify Analytics",
    page_icon="🐸",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ═══════════════════════════════════════════════════════════════════════════════
# DESIGN SYSTEM
# ═══════════════════════════════════════════════════════════════════════════════
CREAM      = "#FAF6F0"
WHITE      = "#FFFFFF"
NAVY       = "#1C2B3A"
TERRACOTTA = "#C1553A"
SAGE       = "#5A7A6A"
LAVENDER   = "#9B8DB5"
DUNE       = "#C4A882"
BLUSH      = "#E8A598"
MOSS       = "#7A9B6A"
CLAY       = "#B87355"
SKY        = "#7AB0C8"
PERSIMMON  = "#E8724A"
SLATE      = "#6e7586"
LIGHT_GRAY = "#F2EDE8"
MID_GRAY   = "#E0D9D0"
TEXT_DARK  = "#1A1A1A"
TEXT_MID   = "#444444"
TEXT_LIGHT = "#777777"

PALETTE    = [TERRACOTTA, SAGE, LAVENDER, DUNE, BLUSH, MOSS, SKY, CLAY, PERSIMMON, "#D4B8E0"]
SCALE      = [[0.0, LIGHT_GRAY], [0.4, DUNE], [0.75, TERRACOTTA], [1.0, NAVY]]

CHART = dict(
    template="plotly_white",
    paper_bgcolor=WHITE,
    plot_bgcolor=WHITE,
    font=dict(family="Inter, -apple-system, sans-serif", color=TEXT_DARK, size=13),
    margin=dict(l=20, r=20, t=50, b=20),
    hoverlabel=dict(bgcolor=WHITE, font_color=TEXT_DARK, bordercolor=MID_GRAY),
)

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');

/* ── Reset & base ── */
*, *::before, *::after {{ box-sizing: border-box; }}
html, body, [data-testid="stAppViewContainer"], [data-testid="stMain"], .main {{
    background-color: {CREAM} !important;
    font-family: 'Inter', -apple-system, sans-serif !important;
}}
[data-testid="stSidebar"] {{ display: none !important; }}
[data-testid="stHeader"] {{ background: transparent !important; }}
[data-testid="stDecoration"] {{ display: none !important; }}
.block-container {{ padding: 2rem 3rem 4rem 3rem !important; max-width: 1400px !important; }}

/* ── Typography ── */
body, p, span, div, li, td, th, label, input, textarea,
[data-testid="stMarkdownContainer"],
[data-testid="stMarkdownContainer"] *,
h1, h2, h3, h4, h5, h6 {{
    color: {TEXT_DARK} !important;
}}

/* ── Hero header ── */
.hero {{
    background: linear-gradient(135deg, #C8DEF0 0%, #E2EFF8 100%);
    border-radius: 20px;
    padding: 36px 40px;
    margin-bottom: 32px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 24px;
    border: 1.5px solid #A8C8E0;
}}
.hero-left h1 {{
    color: #1A1A1A !important;
    font-size: 2.4rem !important;
    font-weight: 900 !important;
    margin: 0 0 4px 0 !important;
    letter-spacing: -0.02em;
}}
.hero-left p {{
    color: #444444 !important;
    font-size: 1rem !important;
    margin: 0 !important;
}}
.hero-cta {{
    display: inline-flex;
    align-items: center;
    gap: 8px;
    background: {TERRACOTTA};
    color: {WHITE} !important;
    text-decoration: none;
    padding: 12px 24px;
    border-radius: 50px;
    font-weight: 700;
    font-size: 0.95rem;
    transition: background 0.2s;
    white-space: nowrap;
}}
.hero-cta:hover {{ background: #a8432a; }}

/* ── Upload zone ── */
.upload-zone {{
    background: {WHITE};
    border: 2px dashed {MID_GRAY};
    border-radius: 16px;
    padding: 28px 32px;
    margin-bottom: 8px;
    transition: border-color 0.2s;
}}
.upload-zone:hover {{ border-color: {TERRACOTTA}; }}
.upload-title {{
    font-size: 1rem;
    font-weight: 700;
    color: {TEXT_DARK} !important;
    margin: 0 0 4px 0;
}}
.upload-sub {{
    font-size: 0.82rem;
    color: {TEXT_LIGHT} !important;
    margin: 0 0 16px 0;
}}

/* ── Section headers ── */
.section-header {{
    font-size: 1.1rem;
    font-weight: 800;
    color: {TEXT_DARK} !important;
    border-left: 4px solid {TERRACOTTA};
    padding-left: 12px;
    margin: 32px 0 16px 0;
    letter-spacing: 0.01em;
}}

/* ── KPI cards ── */
div[data-testid="stMetric"] {{
    background: {WHITE} !important;
    border-radius: 14px !important;
    padding: 20px 22px !important;
    border: 1.5px solid {MID_GRAY} !important;
    box-shadow: 0 1px 4px rgba(0,0,0,0.05) !important;
    transition: box-shadow 0.2s, transform 0.2s;
}}
div[data-testid="stMetric"]:hover {{
    box-shadow: 0 4px 16px rgba(0,0,0,0.10) !important;
    transform: translateY(-2px);
}}
div[data-testid="stMetric"] [data-testid="stMetricLabel"],
div[data-testid="stMetric"] [data-testid="stMetricLabel"] * {{
    color: {TEXT_LIGHT} !important;
    font-size: 0.72rem !important;
    font-weight: 600 !important;
    text-transform: uppercase;
    letter-spacing: 0.08em;
}}
div[data-testid="stMetric"] [data-testid="stMetricValue"],
div[data-testid="stMetric"] [data-testid="stMetricValue"] * {{
    color: {TEXT_DARK} !important;
    font-size: 1.8rem !important;
    font-weight: 800 !important;
    letter-spacing: -0.02em;
}}

/* ── Divider ── */
.divider {{
    height: 1px;
    background: {MID_GRAY};
    margin: 32px 0;
    border: none;
}}

/* ── Badge ── */
.badge {{
    display: inline-block;
    padding: 4px 12px;
    border-radius: 50px;
    font-size: 0.78rem;
    font-weight: 700;
    margin-top: 6px;
    letter-spacing: 0.02em;
}}

/* ── Insight card ── */
.insight-card {{
    background: {WHITE};
    border-radius: 12px;
    padding: 16px 20px;
    border: 1.5px solid {MID_GRAY};
    margin-top: 8px;
    font-size: 0.85rem;
    color: {TEXT_MID} !important;
    line-height: 1.5;
}}

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] {{
    background: {LIGHT_GRAY} !important;
    border-radius: 12px !important;
    padding: 4px !important;
    gap: 2px !important;
    border: none !important;
}}
.stTabs [data-baseweb="tab"] {{
    background: transparent !important;
    border-radius: 8px !important;
    padding: 10px 22px !important;
    font-weight: 600 !important;
    font-size: 0.9rem !important;
    border: none !important;
    transition: all 0.2s !important;
}}
.stTabs [data-baseweb="tab"] * {{ color: {TEXT_MID} !important; }}
.stTabs [aria-selected="true"] {{
    background: {WHITE} !important;
    box-shadow: 0 2px 8px rgba(0,0,0,0.08) !important;
}}
.stTabs [aria-selected="true"] * {{ color: {TERRACOTTA} !important; font-weight: 700 !important; }}

/* ── Buttons ── */
.stButton > button {{
    background: {TERRACOTTA} !important;
    color: {WHITE} !important;
    border: none !important;
    border-radius: 10px !important;
    font-weight: 700 !important;
    font-size: 0.9rem !important;
    padding: 10px 24px !important;
    transition: background 0.2s, transform 0.1s !important;
}}
.stButton > button:hover {{
    background: #a8432a !important;
    transform: translateY(-1px) !important;
}}
.stButton > button * {{ color: {WHITE} !important; }}
.stDownloadButton > button {{
    background: {SAGE} !important;
    color: {WHITE} !important;
    border: none !important;
    border-radius: 10px !important;
    font-weight: 600 !important;
}}
.stDownloadButton > button * {{ color: {WHITE} !important; }}

/* ── Text area ── */
textarea {{
    background: {WHITE} !important;
    color: {TEXT_DARK} !important;
    border: 1.5px solid {MID_GRAY} !important;
    border-radius: 10px !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.85rem !important;
}}
textarea:focus {{ border-color: {TERRACOTTA} !important; outline: none !important; }}

/* ── File uploader ── */
[data-testid="stFileUploaderDropzone"] {{
    background: {CREAM} !important;
    border: 2px dashed {DUNE} !important;
    border-radius: 10px !important;
    transition: border-color 0.2s;
}}
[data-testid="stFileUploaderDropzone"]:hover {{ border-color: {TERRACOTTA} !important; }}
[data-testid="stFileUploaderDropzone"] *,
[data-testid="stFileUploaderDropzone"] span,
[data-testid="stFileUploaderDropzone"] p,
[data-testid="stFileUploaderDropzone"] small,
[data-testid="stFileUploaderDropzone"] div {{ color: {TEXT_DARK} !important; }}
[data-testid="stFileUploaderDropzone"] button {{
    background: #C8DEF0 !important;
    border-radius: 6px !important;
    border: 1.5px solid #A8C8E0 !important;
}}
[data-testid="stFileUploaderDropzone"] button * {{ color: #1A1A1A !important; }}
[data-testid="stFileUploader"] label {{ color: {TEXT_DARK} !important; font-weight: 600 !important; }}

/* ── Caption ── */
.stCaption, .stCaption *, small {{ color: {TEXT_LIGHT} !important; }}

/* ── Dataframe ── */
[data-testid="stDataFrame"] {{ border-radius: 12px !important; border: 1.5px solid {MID_GRAY} !important; overflow: hidden; }}

/* ── Chart containers ── */
.chart-card {{
    background: {WHITE};
    border-radius: 14px;
    border: 1.5px solid {MID_GRAY};
    padding: 8px;
    margin-bottom: 8px;
}}

/* ── Step indicator for upload ── */
.step-pill {{
    display: inline-flex;
    align-items: center;
    gap: 8px;
    background: {LIGHT_GRAY};
    border-radius: 50px;
    padding: 6px 16px 6px 6px;
    font-size: 0.82rem;
    font-weight: 600;
    color: {TEXT_MID} !important;
    margin-bottom: 20px;
}}
.step-dot {{
    width: 24px; height: 24px;
    background: {TERRACOTTA};
    border-radius: 50%;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    color: white !important;
    font-size: 0.75rem;
    font-weight: 800;
}}

/* ── Scrollbar ── */
::-webkit-scrollbar {{ width: 6px; height: 6px; }}
::-webkit-scrollbar-track {{ background: {LIGHT_GRAY}; }}
::-webkit-scrollbar-thumb {{ background: {DUNE}; border-radius: 3px; }}
::-webkit-scrollbar-thumb:hover {{ background: {TERRACOTTA}; }}
</style>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════════════════════════
@st.cache_data(show_spinner=False)
def load_csv(file_bytes: bytes) -> pd.DataFrame:
    df = pd.read_csv(io.BytesIO(file_bytes))
    df.columns = df.columns.str.strip().str.lstrip("\ufeff")
    return df

def register_tables(con, timeline, songs):
    con.register("timeline", timeline)
    con.register("songs", songs)

def fmt(n) -> str:
    if n is None: return "–"
    n = int(n)
    if n >= 1_000_000: return f"{n/1_000_000:.2f}M"
    if n >= 1_000: return f"{n/1_000:.1f}K"
    return str(n)

def badge(label, color, text_color="#fff"):
    return f'<span class="badge" style="background:{color};color:{text_color};">{label}</span>'

def insight(text, emoji="💡"):
    return f'<div class="insight-card">{emoji} {text}</div>'

def status(val, thresholds, labels, colors):
    for i, t in enumerate(thresholds):
        if val >= t:
            return labels[i], colors[i]
    return labels[-1], colors[-1]

def wrap_chart(fig):
    st.markdown('<div class="chart-card">', unsafe_allow_html=True)
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    st.markdown('</div>', unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# HERO HEADER
# ═══════════════════════════════════════════════════════════════════════════════
st.markdown(f"""
<div class="hero">
  <div class="hero-left">
    <h1>🐸 Blue Frog Analytics</h1>
    <p>Spotify performance dashboard · powered by DuckDB</p>
  </div>
  <a class="hero-cta" href="https://open.spotify.com/artist/1j71gO9gHulj7w1KXBtDXi" target="_blank">
    ♫ Follow Blue Frog on Spotify
  </a>
</div>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# TOP SECTION: Playlist + Upload
# ═══════════════════════════════════════════════════════════════════════════════
col_left, col_right = st.columns([1, 2], gap="large")

with col_left:
    st.markdown("**🎧 Latest Release**")
    st.components.v1.iframe(
        "https://open.spotify.com/embed/playlist/38PWTug6fz72EdznsQsP0K?utm_source=generator&theme=0",
        height=352,
        scrolling=False
    )

with col_right:
    st.markdown("""
    <div style="margin-bottom:20px;">
      <div class="step-pill"><span class="step-dot">↑</span> Upload your Spotify CSV exports to unlock your dashboard</div>
    </div>
    """, unsafe_allow_html=True)

    u1, u2 = st.columns(2, gap="medium")
    with u1:
        st.markdown('<p class="upload-title">📅 Audience Timeline</p><p class="upload-sub">date · listeners · streams · followers</p>', unsafe_allow_html=True)
        timeline_file = st.file_uploader("", type="csv", key="timeline", label_visibility="collapsed")
    with u2:
        st.markdown('<p class="upload-title">🎵 Songs Data</p><p class="upload-sub">song · listeners · streams · saves · release_date</p>', unsafe_allow_html=True)
        songs_file = st.file_uploader("", type="csv", key="songs", label_visibility="collapsed")

    if not timeline_file or not songs_file:
        st.markdown(f"""
        <div style="background:{WHITE};border-radius:12px;padding:24px 28px;border:1.5px solid {MID_GRAY};margin-top:8px;">
          <p style="font-weight:800;margin:0 0 16px 0;font-size:0.95rem;color:{TEXT_DARK};">📥 How to export from Spotify for Artists</p>
          <ol style="margin:0;padding-left:20px;color:{TEXT_MID};font-size:0.85rem;line-height:2.4;">
            <li>Go to <a href="https://artists.spotify.com" target="_blank" style="color:{TERRACOTTA};font-weight:600;">artists.spotify.com</a> and log in</li>
            <li>Click <strong>Music</strong> in the top nav → select a song or go to <strong>Audience</strong></li>
            <li>For the <strong>Timeline CSV</strong>: go to <strong>Audience</strong> tab → click the <img src="data:image/png;base64,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" style="width:80px;height:80px;vertical-align:middle;margin:0 3px;" /> icon in the top right corner</li>
            <li>For the <strong>Songs CSV</strong>: go to <strong>Music</strong> tab → click the <img src="data:image/png;base64,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" style="width:80px;height:80px;vertical-align:middle;margin:0 3px;" /> icon at the top of the songs table</li>
          </ol>
          <div style="margin-top:16px;padding:12px 16px;background:{LIGHT_GRAY};border-radius:8px;font-size:0.8rem;color:{TEXT_LIGHT};">
            💡 <strong>Tip:</strong> Look for this icon in Spotify for Artists to download your data: <img src="data:image/png;base64,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" style="width:80px;height:80px;vertical-align:middle;margin:0 3px;" />
          </div>
        </div>
        """, unsafe_allow_html=True)

st.markdown('<hr class="divider">', unsafe_allow_html=True)

if not timeline_file or not songs_file:
    st.stop()


# ═══════════════════════════════════════════════════════════════════════════════
# LOAD DATA
# ═══════════════════════════════════════════════════════════════════════════════
with st.spinner(""):
    timeline_df = load_csv(timeline_file.read())
    songs_df    = load_csv(songs_file.read())

    timeline_df["date"]         = pd.to_datetime(timeline_df["date"])
    songs_df["release_date"]    = pd.to_datetime(songs_df["release_date"])

    for col in ["listeners", "streams", "followers"]:
        if col in timeline_df.columns:
            timeline_df[col] = pd.to_numeric(timeline_df[col], errors="coerce").fillna(0).astype(int)
    for col in ["listeners", "streams", "saves"]:
        if col in songs_df.columns:
            songs_df[col] = pd.to_numeric(songs_df[col], errors="coerce").fillna(0).astype(int)

    con = duckdb.connect(":memory:")
    register_tables(con, timeline_df, songs_df)

tl = timeline_df.copy()


# ═══════════════════════════════════════════════════════════════════════════════
# CALCULATIONS
# ═══════════════════════════════════════════════════════════════════════════════
total_streams   = int(tl["streams"].sum())
total_listeners = int(tl["listeners"].sum()) if tl["listeners"].sum() > 0 else int(songs_df["listeners"].sum())
max_listeners   = int(tl["listeners"].max()) if tl["listeners"].max() > 0 else int(songs_df["listeners"].max())
total_followers = int(tl.sort_values("date").iloc[-1]["followers"])
follower_growth = int(tl.sort_values("date").iloc[-1]["followers"] - tl.sort_values("date").iloc[0]["followers"])
total_songs     = len(songs_df)
total_saves     = int(songs_df["saves"].sum())

fcr                    = (follower_growth / total_listeners * 100) if total_listeners > 0 else 0
stickiness             = (total_streams / total_listeners) if total_listeners > 0 else 0
save_rate_stream       = (total_saves / total_streams * 100) if total_streams > 0 else 0
stream_listener_ratio  = stickiness
save_rate_by_listeners = (total_saves / total_listeners * 100) if total_listeners > 0 else 0

G, Y, R = "#2d6a4f", "#b5770d", "#9b2226"


# ═══════════════════════════════════════════════════════════════════════════════
# ROW 1 — KEY METRICS
# ═══════════════════════════════════════════════════════════════════════════════
st.markdown('<div class="section-header">Key Metrics</div>', unsafe_allow_html=True)
m1, m2, m3, m4, m5 = st.columns(5, gap="medium")
m1.metric("🎧 Total Streams",   fmt(total_streams))
m2.metric("👥 Peak Listeners",  fmt(max_listeners))
m3.metric("❤️ Followers",       fmt(total_followers))
m4.metric("📈 Follower Growth", f"+{fmt(follower_growth)}")
m5.metric("🎵 Catalogue",       f"{total_songs} tracks")

st.markdown('<hr class="divider">', unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# ROW 2 — ADVANCED HEALTH KPIs
# ═══════════════════════════════════════════════════════════════════════════════
st.markdown('<div class="section-header">Advanced Health KPIs</div>', unsafe_allow_html=True)
h1, h2, h3 = st.columns(3, gap="medium")

fcr_lbl, fcr_col = status(fcr, [2, 0.5], ["🟢 Healthy", "🟡 Low"], [G, Y]) if fcr >= 0.5 else ("🔴 Critical", R)
stk_lbl, stk_col = status(stickiness, [3, 1.5], ["🟢 Strong", "🟡 Low"], [G, Y]) if stickiness >= 1.5 else ("🔴 Very Low", R)
sav_lbl, sav_col = status(save_rate_stream, [6, 2], ["🟢 Healthy", "🟡 Low"], [G, Y]) if save_rate_stream >= 2 else ("🔴 Danger", R)

with h1:
    st.metric("🎯 Fan Conversion Rate", f"{fcr:.2f}%", help="New Followers ÷ Total Listeners × 100. Benchmark: 2%+")
    st.markdown(badge(fcr_lbl, fcr_col), unsafe_allow_html=True)
    msg = "Only 1 in 1,000 listeners is following. Work on your profile — bio, photos, pinned track." if fcr < 0.5 else ("Decent but room to grow. Pin your best track and improve your artist bio." if fcr < 2 else "Great conversion — you're turning listeners into real fans!")
    st.markdown(insight(msg, "⚠️" if fcr < 0.5 else ("💡" if fcr < 2 else "✅")), unsafe_allow_html=True)

with h2:
    st.metric("🔁 Content Stickiness", f"{stickiness:.2f}x", help="Total Streams ÷ Total Listeners. Benchmark: 3x+")
    st.markdown(badge(stk_lbl, stk_col), unsafe_allow_html=True)
    msg = "Listeners aren't replaying. Focus on stronger hooks and cohesive EPs." if stickiness < 1.5 else ("Some replays but below 3x. Try releasing music in thematic series." if stickiness < 3 else "Listeners are hooked and keep coming back!")
    st.markdown(insight(msg, "⚠️" if stickiness < 1.5 else ("💡" if stickiness < 3 else "✅")), unsafe_allow_html=True)

with h3:
    st.metric("💾 Save-to-Stream Ratio", f"{save_rate_stream:.2f}%", help="Total Saves ÷ Total Streams × 100. Benchmark: 6–10%")
    st.markdown(badge(sav_lbl, sav_col), unsafe_allow_html=True)
    msg = "Almost nobody is saving. This is a major red flag — focus on memorable, replayable melodies." if save_rate_stream < 2 else ("Below benchmark. Shorter, hookier tracks tend to drive more saves." if save_rate_stream < 6 else "Healthy save rate — listeners want your music in their library!")
    st.markdown(insight(msg, "⚠️" if save_rate_stream < 2 else ("💡" if save_rate_stream < 6 else "✅")), unsafe_allow_html=True)

st.markdown('<hr class="divider">', unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# ROW 3 — ENGAGEMENT DEPTH KPIs
# ═══════════════════════════════════════════════════════════════════════════════
st.markdown('<div class="section-header">Engagement Depth KPIs</div>', unsafe_allow_html=True)
e1, e2, e3, e4 = st.columns(4, gap="medium")

slr_lbl, slr_col = status(stream_listener_ratio, [2.0, 1.2], ["🟢 Healthy", "🟡 Low"], [G, Y]) if stream_listener_ratio >= 1.2 else ("🔴 Very Low", R)
svl_lbl, svl_col = status(save_rate_by_listeners, [10, 3], ["🟢 Healthy", "🟡 Low"], [G, Y]) if save_rate_by_listeners >= 3 else ("🔴 Danger", R)

with e1:
    st.metric("🔂 Stream / Listener", f"{stream_listener_ratio:.2f}x", help="Total Streams ÷ Unique Listeners. Benchmark: 2.0+")
    st.markdown(badge(slr_lbl, slr_col), unsafe_allow_html=True)
    msg = "People aren't replaying — songs may not be hooking listeners in." if stream_listener_ratio < 1.2 else ("Some replays but below the 2.0x benchmark." if stream_listener_ratio < 2.0 else "Strong replays — listeners keep coming back!")
    st.markdown(insight(msg, "⚠️" if stream_listener_ratio < 1.2 else ("💡" if stream_listener_ratio < 2.0 else "✅")), unsafe_allow_html=True)

with e2:
    st.metric("💿 Save Rate (Listeners)", f"{save_rate_by_listeners:.2f}%", help="Saves ÷ Listeners × 100. Benchmark: 3–10%")
    st.markdown(badge(svl_lbl, svl_col), unsafe_allow_html=True)
    msg = "Very few listeners are saving — suggests passive or bot listening." if save_rate_by_listeners < 3 else ("Decent but aim for 10%+. Try music that rewards repeated listens." if save_rate_by_listeners < 10 else "Strong save rate — your audience is genuinely engaged!")
    st.markdown(insight(msg, "⚠️" if save_rate_by_listeners < 3 else ("💡" if save_rate_by_listeners < 10 else "✅")), unsafe_allow_html=True)

with e3:
    st.metric("⏭️ Skip Rate", "N/A", help="Skips ÷ Total Plays. Benchmark: under 25%")
    st.markdown(badge("⚪ Not in CSV", "#6c757d"), unsafe_allow_html=True)
    st.markdown(insight("Requires Spotify for Artists advanced export. Benchmark: under 25% skips.", "📊"), unsafe_allow_html=True)

with e4:
    st.metric("🎯 Intent Rate", "N/A", help="Streams from Profile/Library ÷ Total Streams. Benchmark: 20%+")
    st.markdown(badge("⚪ Not in CSV", "#6c757d"), unsafe_allow_html=True)
    st.markdown(insight("Requires stream source breakdown from Spotify for Artists. Benchmark: 20%+.", "📊"), unsafe_allow_html=True)

st.markdown('<hr class="divider">', unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# TABS
# ═══════════════════════════════════════════════════════════════════════════════
tab1, tab2, tab3, tab4 = st.tabs(["  📈  Audience Trends  ", "  🎵  Song Performance  ", "  📅  Release Intelligence  ", "  🔍  Deep Dive  "])


# ── TAB 1: AUDIENCE TRENDS ────────────────────────────────────────────────────
with tab1:
    st.markdown('<div class="section-header">Streams · Listeners · Followers Over Time</div>', unsafe_allow_html=True)

    fig = make_subplots(rows=3, cols=1, shared_xaxes=True,
                        subplot_titles=("Streams", "Listeners", "Followers"),
                        vertical_spacing=0.06)
    fig.add_trace(go.Scatter(x=tl["date"], y=tl["streams"], fill="tozeroy",
                             line=dict(color=TERRACOTTA, width=2.5), fillcolor="rgba(193,85,58,0.12)",
                             name="Streams"), row=1, col=1)
    fig.add_trace(go.Scatter(x=tl["date"], y=tl["listeners"], fill="tozeroy",
                             line=dict(color=SAGE, width=2.5), fillcolor="rgba(90,122,106,0.12)",
                             name="Listeners"), row=2, col=1)
    fig.add_trace(go.Scatter(x=tl["date"], y=tl["followers"], fill="tozeroy",
                             line=dict(color=LAVENDER, width=2.5), fillcolor="rgba(155,141,181,0.12)",
                             name="Followers"), row=3, col=1)
    fig.update_layout(**CHART, height=520, showlegend=True,
                      legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
    for i in range(1, 4):
        fig.update_xaxes(showgrid=False, row=i, col=1)
        fig.update_yaxes(showgrid=True, gridcolor=LIGHT_GRAY, gridwidth=1, row=i, col=1)
    wrap_chart(fig)

    c_l, c_r = st.columns(2, gap="medium")
    with c_l:
        st.markdown('<div class="section-header">7-Day Rolling Average</div>', unsafe_allow_html=True)
        tl_roll = tl.set_index("date").sort_index()
        tl_roll["streams_7d"]   = tl_roll["streams"].rolling(7).mean()
        tl_roll["listeners_7d"] = tl_roll["listeners"].rolling(7).mean()
        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(x=tl_roll.index, y=tl_roll["streams_7d"],
                                  name="Streams", line=dict(color=TERRACOTTA, width=2.5)))
        fig2.add_trace(go.Scatter(x=tl_roll.index, y=tl_roll["listeners_7d"],
                                  name="Listeners", line=dict(color=SAGE, width=2.5)))
        fig2.update_layout(**CHART, height=280,
                           legend=dict(orientation="h", yanchor="bottom", y=1.02))
        fig2.update_xaxes(showgrid=False)
        fig2.update_yaxes(showgrid=True, gridcolor=LIGHT_GRAY)
        wrap_chart(fig2)

    with c_r:
        st.markdown('<div class="section-header">Avg Streams by Day of Week</div>', unsafe_allow_html=True)
        tl_dow = tl.copy()
        tl_dow["dow"] = tl_dow["date"].dt.day_name()
        dow_order = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
        dow_agg = tl_dow.groupby("dow")["streams"].mean().reindex(dow_order).reset_index()
        fig4 = px.bar(dow_agg, x="dow", y="streams", color="streams",
                      color_continuous_scale=SCALE, labels={"streams": "Avg Streams", "dow": ""})
        fig4.update_layout(**CHART, height=280, coloraxis_showscale=False)
        fig4.update_traces(marker_line_width=0)
        fig4.update_xaxes(showgrid=False)
        fig4.update_yaxes(showgrid=True, gridcolor=LIGHT_GRAY)
        wrap_chart(fig4)

    st.markdown('<div class="section-header">Monthly Stream Volume</div>', unsafe_allow_html=True)
    monthly = con.execute("""
        SELECT strftime(date, '%Y-%m') AS month,
               SUM(streams) AS total_streams, AVG(listeners) AS avg_listeners
        FROM timeline GROUP BY month ORDER BY month
    """).df()
    fig3 = px.bar(monthly, x="month", y="total_streams", color="total_streams",
                  color_continuous_scale=SCALE,
                  labels={"total_streams": "Total Streams", "month": ""})
    fig3.update_layout(**CHART, height=300, coloraxis_showscale=False)
    fig3.update_traces(marker_line_width=0)
    fig3.update_xaxes(showgrid=False)
    fig3.update_yaxes(showgrid=True, gridcolor=LIGHT_GRAY)
    wrap_chart(fig3)


# ── TAB 2: SONG PERFORMANCE ───────────────────────────────────────────────────
with tab2:
    songs_sorted = songs_df.sort_values("streams", ascending=False).reset_index(drop=True)
    songs_sorted.index += 1

    s_l, s_r = st.columns([3, 2], gap="large")
    with s_l:
        st.markdown('<div class="section-header">Top 10 Songs by Streams</div>', unsafe_allow_html=True)
        top10 = songs_sorted.head(10)
        fig5 = px.bar(top10, x="streams", y="song", orientation="h",
                      color="streams", color_continuous_scale=SCALE,
                      labels={"streams": "Total Streams", "song": ""})
        fig5.update_layout(**CHART, height=380, yaxis=dict(autorange="reversed"),
                           coloraxis_showscale=False)
        fig5.update_traces(marker_line_width=0)
        fig5.update_xaxes(showgrid=True, gridcolor=LIGHT_GRAY)
        fig5.update_yaxes(showgrid=False)
        wrap_chart(fig5)

    with s_r:
        st.markdown('<div class="section-header">Stream Share</div>', unsafe_allow_html=True)
        pie_df = songs_sorted.copy()
        if len(pie_df) > 8:
            top8  = pie_df.head(8)
            other = pd.DataFrame([{"song": "Other", "streams": pie_df.iloc[8:]["streams"].sum()}])
            pie_df = pd.concat([top8, other], ignore_index=True)
        fig7 = px.pie(pie_df, values="streams", names="song",
                      color_discrete_sequence=PALETTE, hole=0.45)
        fig7.update_traces(textposition="outside", textinfo="label+percent",
                           textfont_size=11)
        fig7.update_layout(**CHART, height=380,
                           legend=dict(orientation="v", font=dict(size=11)))
        wrap_chart(fig7)

    st.markdown('<div class="section-header">Full Song Catalogue</div>', unsafe_allow_html=True)
    display_songs = songs_sorted.copy()
    display_songs["release_date"] = display_songs["release_date"].dt.strftime("%Y-%m-%d")
    st.dataframe(display_songs, use_container_width=True, height=320,
                 column_config={
                     "streams": st.column_config.ProgressColumn("Streams", format="%d", min_value=0,
                                                                  max_value=int(songs_sorted["streams"].max())),
                     "saves":   st.column_config.NumberColumn("Saves", format="%d"),
                 })


# ── TAB 3: RELEASE INTELLIGENCE ──────────────────────────────────────────────
with tab3:
    st.markdown('<div class="section-header">Stream Performance by Release Date</div>', unsafe_allow_html=True)
    songs_rel = songs_df.sort_values("release_date").copy()
    fig8 = px.scatter(songs_rel, x="release_date", y="streams",
                      size="streams", color="streams", color_continuous_scale=SCALE,
                      hover_name="song",
                      labels={"release_date": "Release Date", "streams": "Total Streams"})
    fig8.update_layout(**CHART, height=380, coloraxis_showscale=False)
    fig8.update_xaxes(showgrid=False)
    fig8.update_yaxes(showgrid=True, gridcolor=LIGHT_GRAY)
    wrap_chart(fig8)

    songs_rel["release_month"] = songs_rel["release_date"].dt.to_period("M").astype(str)
    monthly_rel = songs_rel.groupby("release_month").agg(
        tracks=("song", "count"), total_streams=("streams", "sum")).reset_index()

    r1, r2 = st.columns(2, gap="medium")
    with r1:
        st.markdown('<div class="section-header">Tracks Released per Month</div>', unsafe_allow_html=True)
        fig9 = px.bar(monthly_rel, x="release_month", y="tracks",
                      color="tracks", color_continuous_scale=SCALE,
                      labels={"tracks": "# Tracks", "release_month": ""})
        fig9.update_layout(**CHART, height=280, coloraxis_showscale=False)
        fig9.update_traces(marker_line_width=0)
        fig9.update_xaxes(showgrid=False, tickangle=-30)
        fig9.update_yaxes(showgrid=True, gridcolor=LIGHT_GRAY)
        wrap_chart(fig9)

    with r2:
        st.markdown('<div class="section-header">Streams per Release Month</div>', unsafe_allow_html=True)
        fig10 = px.bar(monthly_rel, x="release_month", y="total_streams",
                       color="total_streams", color_continuous_scale=SCALE,
                       labels={"total_streams": "Streams", "release_month": ""})
        fig10.update_layout(**CHART, height=280, coloraxis_showscale=False)
        fig10.update_traces(marker_line_width=0)
        fig10.update_xaxes(showgrid=False, tickangle=-30)
        fig10.update_yaxes(showgrid=True, gridcolor=LIGHT_GRAY)
        wrap_chart(fig10)

    st.markdown('<div class="section-header">Avg Streams per Track by Release Month</div>', unsafe_allow_html=True)
    efficiency = con.execute("""
        SELECT strftime(release_date, '%Y-%m') AS release_month,
               COUNT(*) AS tracks, SUM(streams) AS total_streams,
               AVG(streams) AS avg_streams_per_track
        FROM songs GROUP BY release_month ORDER BY avg_streams_per_track DESC
    """).df()
    fig11 = px.bar(efficiency, x="release_month", y="avg_streams_per_track",
                   color="avg_streams_per_track", color_continuous_scale=SCALE,
                   labels={"avg_streams_per_track": "Avg Streams / Track", "release_month": ""})
    fig11.update_layout(**CHART, height=300, coloraxis_showscale=False)
    fig11.update_traces(marker_line_width=0)
    fig11.update_xaxes(showgrid=False, tickangle=-30)
    fig11.update_yaxes(showgrid=True, gridcolor=LIGHT_GRAY)
    wrap_chart(fig11)


# ── TAB 4: DEEP DIVE ─────────────────────────────────────────────────────────
with tab4:
    d1, d2 = st.columns(2, gap="medium")

    with d1:
        st.markdown('<div class="section-header">Cumulative Streams</div>', unsafe_allow_html=True)
        tl_cum = tl.sort_values("date").copy()
        tl_cum["cumulative_streams"] = tl_cum["streams"].cumsum()
        fig12 = px.area(tl_cum, x="date", y="cumulative_streams",
                        color_discrete_sequence=[TERRACOTTA],
                        labels={"cumulative_streams": "Total Streams", "date": ""})
        fig12.update_traces(fillcolor="rgba(193,85,58,0.15)", line=dict(width=2.5))
        fig12.update_layout(**CHART, height=280)
        fig12.update_xaxes(showgrid=False)
        fig12.update_yaxes(showgrid=True, gridcolor=LIGHT_GRAY)
        wrap_chart(fig12)

    with d2:
        st.markdown('<div class="section-header">Follower Growth Curve</div>', unsafe_allow_html=True)
        fig13 = px.line(tl.sort_values("date"), x="date", y="followers",
                        color_discrete_sequence=[LAVENDER],
                        labels={"followers": "Followers", "date": ""})
        fig13.update_traces(line=dict(width=2.5))
        fig13.update_layout(**CHART, height=280)
        fig13.update_xaxes(showgrid=False)
        fig13.update_yaxes(showgrid=True, gridcolor=LIGHT_GRAY)
        wrap_chart(fig13)

    st.markdown('<div class="section-header">🦆 Custom DuckDB SQL Console</div>', unsafe_allow_html=True)
    st.caption("Tables: `timeline` (date, listeners, streams, followers) · `songs` (song, listeners, streams, saves, release_date)")

    default_sql = "SELECT song, streams, saves,\n       ROUND(saves * 100.0 / NULLIF(streams, 0), 2) AS save_rate_pct\nFROM songs\nORDER BY streams DESC\nLIMIT 20"
    sql_input = st.text_area("", value=default_sql, height=130, label_visibility="collapsed")

    if st.button("▶  Run Query"):
        try:
            result = con.execute(sql_input).df()
            st.dataframe(result, use_container_width=True)
            numeric_cols = result.select_dtypes("number").columns.tolist()
            non_numeric  = [c for c in result.columns if c not in numeric_cols]
            if numeric_cols and non_numeric:
                fig_sql = px.bar(result.head(20), x=non_numeric[0], y=numeric_cols[0],
                                 color=numeric_cols[0], color_continuous_scale=SCALE)
                fig_sql.update_layout(**CHART, height=320, coloraxis_showscale=False)
                fig_sql.update_traces(marker_line_width=0)
                wrap_chart(fig_sql)
        except Exception as e:
            st.error(f"Query error: {e}")

    st.markdown('<div class="section-header">⬇️ Export</div>', unsafe_allow_html=True)
    ex1, ex2, _ = st.columns([1, 1, 2])
    with ex1:
        st.download_button("⬇ Timeline CSV", tl.to_csv(index=False), "timeline.csv", "text/csv", use_container_width=True)
    with ex2:
        st.download_button("⬇ Songs CSV", songs_df.to_csv(index=False), "songs.csv", "text/csv", use_container_width=True)