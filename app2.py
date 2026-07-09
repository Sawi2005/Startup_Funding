import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

# -----------------------------------------------------------------------------
# 1. PAGE CONFIGURATION & THEME
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Startup Funding Ecosystem Dashboard",
    page_icon="🚀",
    layout="wide",  # Uses the full screen width instead of a narrow central column
    initial_sidebar_state="expanded"
)

# Custom CSS to inject for clean container spacing and polished typography
st.markdown("""
    <style>
    .main-header { font-size:2.5rem !important; font-weight: 700; color: #1E3A8A; margin-bottom: 0.5rem; }
    .sub-header { font-size:1.1rem !important; color: #4B5563; margin-bottom: 2rem; }
    div[data-testid="stMetricValue"] { font-size: 2rem !important; font-weight: 600 !important; }
    </style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. ROBUST DATA LOADING & CLEANING PIPELINE
# -----------------------------------------------------------------------------
@st.cache_data
def load_clean_data():
    """
    Simulating a real-world startup dataset. 
    REPLACE THIS BLOCK with your own data reading logic:
    df = pd.read_csv("your_uploaded_file.csv")
    """
    np.random.seed(42)
    dates = pd.date_range(start='2024-01-01', end='2026-06-01', freq='D')
    sample_size = 350
    
    data = {
        'Date': np.random.choice(dates, sample_size),
        'Startup': np.random.choice(['TechNova', 'QuantumBio', 'FinSphere', 'GreenDrive', 'LogiLink', 'EduPulse', 'CloudShield', 'HealthAI'], sample_size),
        'Industry': np.random.choice(['SaaS', 'HealthTech', 'FinTech', 'CleanTech', 'EdTech', 'Cybersecurity'], sample_size, p=[0.25, 0.20, 0.20, 0.15, 0.10, 0.10]),
        'City': np.random.choice(['Bengaluru', 'Mumbai', 'Delhi NCR', 'Hyderabad', 'Pune'], sample_size),
        'Investor': np.random.choice(['Sequoia Capital', 'Accel Partners', 'Blume Ventures', 'Tiger Global', 'Y Combinator', 'Angel Network'], sample_size),
        'Funding_Round': np.random.choice(['Seed', 'Pre-A', 'Series A', 'Series B', 'Series C'], sample_size, p=[0.35, 0.20, 0.25, 0.15, 0.05]),
        'Amount_USD': np.random.exponential(scale=5000000, size=sample_size) + 100000
    }
    
    df = pd.DataFrame(data)
    
    # Data Cleaning Guardrails (Ensuring correct types for aggregation)
    df['Date'] = pd.to_datetime(df['Date'])
    df['Amount_USD'] = pd.to_numeric(df['Amount_USD'], errors='coerce').fillna(0)
    df['YearMonth'] = df['Date'].dt.to_period('M').astype(str)
    df['Year'] = df['Date'].dt.year
    
    return df

df = load_clean_data()

# -----------------------------------------------------------------------------
# 3. INTERACTIVE SIDEBAR CONTROL PANEL
# -----------------------------------------------------------------------------
st.sidebar.image("https://img.icons8.com/external-flatart-icons-flat-flatarticons/128/external-startup-startup-flatart-icons-flat-flatarticons.png", width=80)
st.sidebar.title("Dashboard Controls")
st.sidebar.markdown("Filter ecosystem parameters dynamically:")

# Dynamic filters populated straight from the data
selected_years = st.sidebar.multiselect("📅 Select Funding Year(s):", options=sorted(df['Year'].unique()), default=sorted(df['Year'].unique()))
selected_industries = st.sidebar.multiselect("💡 Select Industry Verticals:", options=sorted(df['Industry'].unique()), default=sorted(df['Industry'].unique()))
selected_rounds = st.sidebar.multiselect("📊 Select Funding Stage / Rounds:", options=df['Funding_Round'].unique(), default=df['Funding_Round'].unique())

# Minimum funding slider to screen out noise
min_funding = st.sidebar.slider("💰 Minimum Investment Size ($):", min_value=0, max_value=20000000, value=100000, step=500000)

# Filter Application
filtered_df = df[
    (df['Year'].isin(selected_years)) & 
    (df['Industry'].isin(selected_industries)) & 
    (df['Funding_Round'].isin(selected_rounds)) &
    (df['Amount_USD'] >= min_funding)
]

# -----------------------------------------------------------------------------
# 4. MAIN LAYOUT AND DESIGN HEADERS
# -----------------------------------------------------------------------------
st.markdown('<p class="main-header">🚀 Startup Funding Insights Dashboard</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Real-time market intelligence tracking capitalization vectors, sector distribution, and historical deal flow.</p>', unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 5. SCORECARD / KPI GRID BLOCK
# -----------------------------------------------------------------------------
if not filtered_df.empty:
    total_capital = filtered_df['Amount_USD'].sum()
    average_deal = filtered_df['Amount_USD'].mean()
    total_deals = len(filtered_df)
    dominant_sector = filtered_df.groupby('Industry')['Amount_USD'].sum().idxmax()
    
    # Layout KPIs horizontally using columns
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    
    with kpi1:
        st.metric(label="Total Capital Deployed", value=f"${total_capital/1e6:.1f}M", delta=f"{len(selected_years)} Years Active")
    with kpi2:
        st.metric(label="Average Ticket Size", value=f"${average_deal/1e6:.2f}M")
    with kpi3:
        st.metric(label="Total Closed Deals", value=f"{total_deals:,}")
    with kpi4:
        st.metric(label="Top Capital Absorber", value=dominant_sector)
else:
    st.error("🚨 Zero records match your current criteria. Please relax your sidebar filters.")
    st.stop()

st.markdown("---")

# -----------------------------------------------------------------------------
# 6. ENHANCED MULTI-GRAPH GRAPHICAL ANALYTICS (TABS)
# -----------------------------------------------------------------------------
tab_macro, tab_micro, tab_data = st.tabs(["📊 Macro Ecosystem Trends", "🔍 Sector & Geography Deep-Dive", "📋 Raw Data Explorer"])

# ---- TAB 1: MACRO ECOSYSTEM TRENDS ----
with tab_macro:
    col_graph1, col_graph2 = st.columns(2)
    
    with col_graph1:
        st.subheader("Historical Capital Deployment Trajectory")
        # Aggregating timeline trend
        timeline = filtered_df.groupby('YearMonth')['Amount_USD'].sum().reset_index().sort_values('YearMonth')
        fig_line = px.line(
            timeline, x='YearMonth', y='Amount_USD',
            labels={'Amount_USD': 'Capital Invested ($)', 'YearMonth': 'Timeline'},
            markers=True, line_shape='spline',
            color_discrete_sequence=['#2563EB']
        )
        fig_line.update_layout(margin=dict(l=20, r=20, t=30, b=20), height=400, template="plotly_white")
        st.plotly_chart(fig_line, use_container_width=True)
        
    with col_graph2:
        st.subheader("Capital Volatility by Stage (Distribution Spread)")
        fig_box = px.box(
            filtered_df, x='Funding_Round', y='Amount_USD', color='Funding_Round',
            labels={'Amount_USD': 'Deal Valuation ($)', 'Funding_Round': 'Stage'},
            category_orders={"Funding_Round": ["Seed", "Pre-A", "Series A", "Series B", "Series C"]},
            color_discrete_sequence=px.colors.qualitative.Safe
        )
        fig_box.update_layout(margin=dict(l=20, r=20, t=30, b=20), height=400, template="plotly_white", showlegend=False)
        st.plotly_chart(fig_box, use_container_width=True)

# ---- TAB 2: SECTOR & GEOGRAPHY DEEP-DIVE ----
with tab_micro:
    col_graph3, col_graph4 = st.columns(2)
    
    with col_graph3:
        st.subheader("Market Volume Breakdown by Industry")
        sector_pie = filtered_df.groupby('Industry')['Amount_USD'].sum().reset_index()
        fig_pie = px.pie(
            sector_pie, values='Amount_USD', names='Industry',
            hole=0.4,
            color_discrete_sequence=px.colors.qualitative.Pastel
        )
        fig_pie.update_traces(textposition='inside', textinfo='percent+label')
        fig_pie.update_layout(margin=dict(l=20, r=20, t=30, b=20), height=400, template="plotly_white")
        st.plotly_chart(fig_pie, use_container_width=True)
        
    with col_graph4:
        st.subheader("Geographical Distribution Hotspots")
        geo_bar = filtered_df.groupby('City')['Amount_USD'].sum().reset_index().sort_values('Amount_USD', ascending=True)
        fig_bar = px.bar(
            geo_bar, x='Amount_USD', y='City', orientation='h',
            labels={'Amount_USD': 'Aggregate Funding Pool ($)'},
            color='Amount_USD',
            color_continuous_scale=px.colors.sequential.Blugrn
        )
        fig_bar.update_layout(margin=dict(l=20, r=20, t=30, b=20), height=400, template="plotly_white")
        st.plotly_chart(fig_bar, use_container_width=True)

# ---- TAB 3: RAW DATA EXPLORER & REPORT EXPORTER ----
with tab_data:
    st.subheader("Granular Operational Audit Trail")
    st.markdown("You can inline-edit cells, sort columns, or search specific text parameters directly below:")
    
    # Active Editable Matrix
    styled_df = filtered_df.sort_values(by='Date', ascending=False)[['Date', 'Startup', 'Industry', 'City', 'Investor', 'Funding_Round', 'Amount_USD']]
    
    edited_data = st.data_editor(
        styled_df,
        column_config={
            "Amount_USD": st.column_config.NumberColumn("Amount (USD)", format="$%,.2f"),
            "Date": st.column_config.DateColumn("Closing Date", format="YYYY-MM-DD")
        },
        use_container_width=True,
        num_rows="dynamic"
    )
    
    # Clean CSV Exporter Action Block
    csv_data = edited_data.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Download Export Package (CSV)",
        data=csv_data,
        file_name="startup_funding_export.csv",
        mime="text/csv"
    )