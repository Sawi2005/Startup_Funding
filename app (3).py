"""
🚀 Startup Funding Insights Dashboard
-------------------------------------
A polished, dark-themed Streamlit dashboard for exploring Indian startup
funding data (works with the classic `startup_cleaned.csv` dataset:
Date, Startup, Vertical/Industry, SubVertical, City, Investors,
InvestmentnType/Funding Round, Amount).

Run with:
    streamlit run app.py
"""

import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# ---------------------------------------------------------------------------
# PAGE CONFIG (must be the first Streamlit call)
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Startup Funding Insights Dashboard",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# THEME / CSS  -> dark, card-based, "fintech dashboard" look
# ---------------------------------------------------------------------------
PALETTE = ["#5B8CFF", "#22D3B0", "#F97066", "#F5B942", "#B892FF", "#4AD4E0"]

st.markdown(
    """
    <style>
    .stApp {
        background-color: #0E1117;
        color: #E6E6E6;
    }
    /* KPI cards */
    .kpi-card {
        background: linear-gradient(145deg, #171B24, #12151C);
        border: 1px solid #262B36;
        border-radius: 14px;
        padding: 18px 20px;
        text-align: left;
    }
    .kpi-label {
        font-size: 13px;
        color: #9AA4B2;
        margin-bottom: 6px;
        letter-spacing: .3px;
    }
    .kpi-value {
        font-size: 28px;
        font-weight: 700;
        color: #FFFFFF;
    }
    .section-title {
        font-size: 16px;
        font-weight: 600;
        color: #E6E6E6;
        margin: 6px 0 2px 0;
    }
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] { gap: 4px; }
    .stTabs [data-baseweb="tab"] {
        background-color: #171B24;
        border-radius: 8px 8px 0 0;
        padding: 8px 18px;
        color: #9AA4B2;
    }
    .stTabs [aria-selected="true"] {
        background-color: #1E2430;
        color: #FFFFFF !important;
        border-bottom: 2px solid #5B8CFF;
    }
    div[data-testid="stMetricValue"] { color: #FFFFFF; }
    </style>
    """,
    unsafe_allow_html=True,
)

PLOTLY_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color="#C9D1D9", size=12),
    margin=dict(l=10, r=10, t=40, b=10),
    legend=dict(bgcolor="rgba(0,0,0,0)"),
)


# ---------------------------------------------------------------------------
# DATA LOADING
# ---------------------------------------------------------------------------
@st.cache_data
def load_data(path: str = "startup_cleaned.csv") -> pd.DataFrame:
    df = pd.read_csv(path)

    # Normalise column names so the app works whether the file uses the
    # "raw" Kaggle column names or already-cleaned ones.
    rename_map = {
        "Date dd/mm/yyyy": "date",
        "Date": "date",
        "Startup Name": "startup",
        "Startup": "startup",
        "Industry Vertical": "industry",
        "Vertical": "industry",
        "SubVertical": "subvertical",
        "City  Location": "city",
        "City Location": "city",
        "City": "city",
        "Investors Name": "investors",
        "Investors": "investors",
        "InvestmentnType": "round",
        "Investment Type": "round",
        "Round": "round",
        "Amount in USD": "amount",
        "Amount_USD": "amount",
        "Amount": "amount",
    }
    df = df.rename(columns={c: rename_map[c] for c in df.columns if c in rename_map})

    required = ["date", "startup", "industry", "city", "investors", "round", "amount"]
    for col in required:
        if col not in df.columns:
            df[col] = np.nan

    # Clean amount -> numeric (in USD, then derive a millions column)
    df["amount"] = (
        df["amount"]
        .astype(str)
        .str.replace(",", "", regex=False)
        .str.replace("undisclosed", "", case=False, regex=False)
        .str.extract(r"([\d\.]+)")[0]
    )
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce")
    df["amount_usd_mn"] = df["amount"] / 1_000_000

    # Parse dates (dayfirst, coerce errors)
    df["date"] = pd.to_datetime(df["date"], errors="coerce", dayfirst=True)
    df["year"] = df["date"].dt.year
    df["month"] = df["date"].dt.to_period("M").astype(str)

    # Tidy text columns
    for col in ["startup", "industry", "city", "investors", "round"]:
        df[col] = df[col].astype(str).str.strip()
        df[col] = df[col].replace({"nan": "Unknown", "": "Unknown"})

    df = df.dropna(subset=["amount"])
    df = df[df["amount"] > 0]

    return df


try:
    data = load_data()
except FileNotFoundError:
    st.error(
        "Couldn't find **startup_cleaned.csv** next to app.py. "
        "Place your dataset in the same folder (or edit the `load_data()` path) and rerun."
    )
    st.stop()

# ---------------------------------------------------------------------------
# SIDEBAR FILTERS
# ---------------------------------------------------------------------------
st.sidebar.markdown("## 📊 Filter Ecosystem Metrics")

industries = sorted(data["industry"].dropna().unique().tolist())
rounds = sorted(data["round"].dropna().unique().tolist())
cities = sorted(data["city"].dropna().unique().tolist())

sel_industries = st.sidebar.multiselect("Select industry sectors", industries)
sel_rounds = st.sidebar.multiselect("Select funding rounds", rounds)
sel_cities = st.sidebar.multiselect("Select cities", cities)

min_year = int(data["year"].min()) if data["year"].notna().any() else 2015
max_year = int(data["year"].max()) if data["year"].notna().any() else 2020
year_range = st.sidebar.slider(
    "Select year range", min_value=min_year, max_value=max_year,
    value=(min_year, max_year),
)

# Apply filters
f = data.copy()
if sel_industries:
    f = f[f["industry"].isin(sel_industries)]
if sel_rounds:
    f = f[f["round"].isin(sel_rounds)]
if sel_cities:
    f = f[f["city"].isin(sel_cities)]
f = f[(f["year"] >= year_range[0]) & (f["year"] <= year_range[1])]

st.sidebar.markdown("---")
st.sidebar.caption(f"Showing **{len(f):,}** of {len(data):,} funding records")

# ---------------------------------------------------------------------------
# HEADER
# ---------------------------------------------------------------------------
st.markdown("# 🚀 Startup Funding Insights Dashboard")
st.caption("An interactive look at capital flow across India's startup ecosystem")

if f.empty:
    st.warning("No records match the current filters — try widening your selection.")
    st.stop()

# ---------------------------------------------------------------------------
# KPI CARDS
# ---------------------------------------------------------------------------
total_capital = f["amount_usd_mn"].sum()
avg_ticket = f["amount_usd_mn"].mean()
unique_startups = f["startup"].nunique()
top_round = f["round"].mode().iloc[0] if not f["round"].mode().empty else "N/A"

k1, k2, k3, k4 = st.columns(4)
kpi_data = [
    (k1, "💰 Total Capital Deployed", f"${total_capital:,.0f}M"),
    (k2, "🎟️ Average Ticket Size", f"${avg_ticket:,.1f}M"),
    (k3, "🏢 Unique Funded Startups", f"{unique_startups:,}"),
    (k4, "🔥 Most Common Round", top_round),
]
for col, label, value in kpi_data:
    with col:
        st.markdown(
            f"""<div class="kpi-card">
                    <div class="kpi-label">{label}</div>
                    <div class="kpi-value">{value}</div>
                </div>""",
            unsafe_allow_html=True,
        )

st.write("")

# ---------------------------------------------------------------------------
# TABS
# ---------------------------------------------------------------------------
tab1, tab2, tab3 = st.tabs(["📈 Market Trends", "🧭 Sector Analysis", "🔍 Deep-Dive Explorer"])

# ============================ TAB 1: MARKET TRENDS ==========================
with tab1:
    c1, c2 = st.columns(2)

    with c1:
        st.markdown('<div class="section-title">Total Capital Inflow Over Time ($)</div>', unsafe_allow_html=True)
        trend = f.groupby("month", as_index=False)["amount_usd_mn"].sum().sort_values("month")
        fig = px.area(trend, x="month", y="amount_usd_mn",
                       color_discrete_sequence=[PALETTE[0]])
        fig.update_traces(line=dict(width=2), fillcolor="rgba(91,140,255,0.15)")
        fig.update_layout(**PLOTLY_LAYOUT, xaxis_title="", yaxis_title="Capital ($M)")
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        st.markdown('<div class="section-title">Investment Spread by Funding Stage</div>', unsafe_allow_html=True)
        top_rounds = f["round"].value_counts().nlargest(6).index
        box_df = f[f["round"].isin(top_rounds)]
        fig = px.box(box_df, x="round", y="amount_usd_mn", color="round",
                     color_discrete_sequence=PALETTE)
        fig.update_layout(**PLOTLY_LAYOUT, xaxis_title="", yaxis_title="Amount ($M)", showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    c3, c4 = st.columns(2)

    with c3:
        st.markdown('<div class="section-title">Market Share by Industry Sector</div>', unsafe_allow_html=True)
        sector_share = f.groupby("industry", as_index=False)["amount_usd_mn"].sum()
        sector_share = sector_share.nlargest(8, "amount_usd_mn")
        fig = px.pie(sector_share, names="industry", values="amount_usd_mn", hole=0.55,
                     color_discrete_sequence=PALETTE)
        fig.update_layout(**PLOTLY_LAYOUT)
        st.plotly_chart(fig, use_container_width=True)

    with c4:
        st.markdown('<div class="section-title">Top Startup Hubs by Capital Size</div>', unsafe_allow_html=True)
        city_cap = f.groupby("city", as_index=False)["amount_usd_mn"].sum()
        city_cap = city_cap.nlargest(8, "amount_usd_mn").sort_values("amount_usd_mn")
        fig = px.bar(city_cap, x="amount_usd_mn", y="city", orientation="h",
                     color="amount_usd_mn", color_continuous_scale="Tealgrn")
        fig.update_layout(**PLOTLY_LAYOUT, xaxis_title="Capital ($M)", yaxis_title="",
                           coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)

# ============================ TAB 2: SECTOR ANALYSIS ========================
with tab2:
    c1, c2 = st.columns(2)

    with c1:
        st.markdown('<div class="section-title">Total Funding by Sector</div>', unsafe_allow_html=True)
        sector_total = f.groupby("industry", as_index=False)["amount_usd_mn"].sum()
        sector_total = sector_total.nlargest(10, "amount_usd_mn").sort_values("amount_usd_mn")
        fig = px.bar(sector_total, x="amount_usd_mn", y="industry", orientation="h",
                     color_discrete_sequence=[PALETTE[1]])
        fig.update_layout(**PLOTLY_LAYOUT, xaxis_title="Capital ($M)", yaxis_title="")
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        st.markdown('<div class="section-title">Deal Count by Sector</div>', unsafe_allow_html=True)
        sector_count = f["industry"].value_counts().nlargest(10).reset_index()
        sector_count.columns = ["industry", "deals"]
        fig = px.bar(sector_count, x="industry", y="deals", color="deals",
                     color_continuous_scale="Blues")
        fig.update_layout(**PLOTLY_LAYOUT, xaxis_title="", yaxis_title="Number of Deals",
                           coloraxis_showscale=False)
        fig.update_xaxes(tickangle=-35)
        st.plotly_chart(fig, use_container_width=True)

    st.markdown('<div class="section-title">Average Ticket Size Trend by Sector (Top 5)</div>', unsafe_allow_html=True)
    top5 = f["industry"].value_counts().nlargest(5).index
    trend_sector = (
        f[f["industry"].isin(top5)]
        .groupby(["month", "industry"], as_index=False)["amount_usd_mn"].mean()
    )
    fig = px.line(trend_sector, x="month", y="amount_usd_mn", color="industry",
                  color_discrete_sequence=PALETTE)
    fig.update_layout(**PLOTLY_LAYOUT, xaxis_title="", yaxis_title="Avg Deal Size ($M)")
    st.plotly_chart(fig, use_container_width=True)

# ============================ TAB 3: DEEP-DIVE EXPLORER ======================
with tab3:
    st.markdown('<div class="section-title">Granular Data Matrix</div>', unsafe_allow_html=True)

    display_cols = ["date", "startup", "industry", "city", "investors", "round", "amount_usd_mn"]
    display_df = f[display_cols].rename(columns={
        "date": "Date", "startup": "Startup", "industry": "Industry",
        "city": "City", "investors": "Investor", "round": "Funding_Round",
        "amount_usd_mn": "Amount_USD_Mn",
    }).sort_values("Date", ascending=False)

    st.dataframe(display_df, use_container_width=True, height=420)

    csv_bytes = display_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        "⬇️ Download Filtered Data as CSV",
        data=csv_bytes,
        file_name="filtered_startup_data.csv",
        mime="text/csv",
    )

    with st.expander("📌 Top 10 Biggest Deals in Current Selection"):
        st.dataframe(
            display_df.nlargest(10, "Amount_USD_Mn")[["Date", "Startup", "Industry", "Funding_Round", "Amount_USD_Mn"]],
            use_container_width=True,
        )
