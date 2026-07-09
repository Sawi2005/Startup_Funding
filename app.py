import streamlit as pd
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# 1. Page Configuration (Sets professional look)
st.set_page_config(
    page_title="Startup Funding Analytics Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. Mock Data Loader (Replace this with your pd.read_csv("your_file.csv"))
@st.cache_data
def load_data():
    # Creating a sample dataset mimicking actual startup ecosystem data
    data = {
        'Date': pd.date_range(start='2023-01-01', periods=100, freq='W'),
        'Startup': ['ZetaScale', 'BioPure', 'QuantumAI', 'FinFlow', 'EcoDrive'] * 20,
        'Industry': ['SaaS', 'HealthTech', 'DeepTech', 'FinTech', 'CleanTech'] * 20,
        'City': ['Bengaluru', 'Mumbai', 'Delhi NCR', 'Bengaluru', 'Hyderabad'] * 20,
        'Investor': ['Sequoia Capital', 'Accel', 'Blume Ventures', 'Tiger Global', 'Y Combinator'] * 20,
        'Funding_Round': ['Seed', 'Series A', 'Series B', 'Pre-A', 'Series C'] * 20,
        'Amount_USD': [150000, 2000000, 12000000, 750000, 25000000] * 20,
    }
    df = pd.DataFrame(data)
    df['YearMonth'] = df['Date'].dt.to_period('M').astype(str)
    return df

try:
    df = load_data()
except Exception as e:
    st.error(f"Error loading dataset: {e}")
    st.stop()

# 3. Sidebar Filtering Options
st.sidebar.header("📊 Filter Ecosystem Metrics")
selected_industries = st.sidebar.multiselect(
    "Select Industry sectors:", 
    options=df['Industry'].unique(), 
    default=df['Industry'].unique()
)
selected_rounds = st.sidebar.multiselect(
    "Select Funding Rounds:", 
    options=df['Funding_Round'].unique(), 
    default=df['Funding_Round'].unique()
)

# Apply Sidebar filters to the Dataframe
filtered_df = df[
    (df['Industry'].isin(selected_industries)) & 
    (df['Funding_Round'].isin(selected_rounds))
]

# 4. Main Dashboard Header
st.title("🚀 Startup Funding Insights Dashboard")
st.markdown("An interactive analysis tool for tracking investments, active sectors, and investor behavior.")
st.write("---")

# 5. Key Performance Indicators (KPI Metrics)
if not filtered_df.empty:
    total_funding = filtered_df['Amount_USD'].sum()
    avg_funding = filtered_df['Amount_USD'].mean()
    unique_startups = filtered_df['Startup'].nunique()
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(label="💰 Total Capital Deployed", value=f"${total_funding:,.0f}")
    with col2:
        st.metric(label="📈 Average Ticket Size", value=f"${avg_funding:,.0f}")
    with col3:
        st.metric(label="🏢 Unique Funded Startups", value=f"{unique_startups}")
else:
    st.warning("Please select at least one filter option in the sidebar to populate the metrics.")

st.write("---")

# 6. Analytical Tabs Layout
tab1, tab2, tab3 = st.tabs(["📈 Market Trends", "Sector Analysis", "🔍 Deep-Dive Explorer"])

# --- TAB 1: Market Trends Over Time ---
with tab1:
    st.subheader("Funding Trajectory & Growth Patterns")
    
    if not filtered_df.empty:
        # Graph 1: Line chart showing cumulative or monthly capital flow
        timeline_df = filtered_df.groupby('YearMonth')['Amount_USD'].sum().reset_index()
        fig_line = px.line(
            timeline_df, x='YearMonth', y='Amount_USD',
            title='Total Capital Inflow Over Time ($)',
            labels={'Amount_USD': 'Funding (USD)', 'YearMonth': 'Timeline'},
            markers=True
        )
        fig_line.update_layout(template="plotly_dark", hovermode="x unified")
        st.plotly_chart(fig_line, use_container_width=True)
        
        # Graph 2: Funding Round Distribution (Box Plot to show outliers and valuations)
        fig_box = px.box(
            filtered_df, x='Funding_Round', y='Amount_USD', color='Funding_Round',
            title='Investment Spreads by Funding Stage',
            labels={'Amount_USD': 'Funding Size ($)', 'Funding_Round': 'Stage'}
        )
        fig_box.update_layout(template="plotly_dark")
        st.plotly_chart(fig_box, use_container_width=True)
    else:
        st.info("No data available for the selected filters.")

# --- TAB 2: Sector and Geo-Spatial Dominance ---
with tab2:
    st.subheader("Where is the Capital Flowing?")
    
    chart_col1, chart_col2 = st.columns(2)
    
    if not filtered_df.empty:
        with chart_col1:
            # Graph 3: Pie/Donut Chart for Market Share
            sector_df = filtered_df.groupby('Industry')['Amount_USD'].sum().reset_index()
            fig_pie = px.pie(
                sector_df, values='Amount_USD', names='Industry',
                title='Market Share by Industry Sector',
                hole=0.4
            )
            fig_pie.update_layout(template="plotly_dark")
            st.plotly_chart(fig_pie, use_container_width=True)
            
        with chart_col2:
            # Graph 4: Horizontal Bar Chart for City Hotspots
            city_df = filtered_df.groupby('City')['Amount_USD'].sum().sort_values(ascending=True).reset_index()
            fig_bar = px.bar(
                city_df, x='Amount_USD', y='City', orientation='h',
                title='Top Startup Hubs by Capital Size',
                color='Amount_USD',
                color_continuous_scale='Viridis'
            )
            fig_bar.update_layout(template="plotly_dark")
            st.plotly_chart(fig_bar, use_container_width=True)
    else:
        st.info("No data available to render sector charts.")

# --- TAB 3: Deep-Dive Data Explorer ---
with tab3:
    st.subheader("Granular Data Matrix")
    st.markdown("Review or directly modify the active operational matrix below:")
    
    if not filtered_df.empty:
        # Use st.data_editor instead of regular st.dataframe to allow in-app filtering and search capabilities natively
        edited_df = st.data_editor(
            filtered_df.sort_values(by='Amount_USD', ascending=False),
            use_container_width=True,
            num_rows="dynamic"
        )
        
        # Download Data Button
        csv = edited_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download Filtered Data as CSV",
            data=csv,
            file_name="filtered_startup_funding.csv",
            mime="text/csv",
        )
    else:
        st.info("No records found matching current parameter constraints.")