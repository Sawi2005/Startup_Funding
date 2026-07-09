import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Startup Funding Dashboard", page_icon="🚀", layout="wide")

@st.cache_data
def load_data():
    df = pd.read_csv("startup_clear.csv")
    df.columns = [c.strip().lower() for c in df.columns]
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        df["year"] = df["date"].dt.year
    if "amount" in df.columns:
        df["amount"] = (
            df["amount"].astype(str)
            .str.replace(",", "", regex=False)
            .str.extract(r"([\d\.]+)")[0]
        )
        df["amount"] = pd.to_numeric(df["amount"], errors="coerce").fillna(0)
    return df

df = load_data()

st.title("🚀 Startup Funding Analytics Dashboard")
st.caption("Interactive dashboard built with Streamlit & Plotly")

st.sidebar.header("Filters")

if "year" in df.columns:
    years = sorted(df["year"].dropna().unique())
    selected_year = st.sidebar.multiselect("Year", years, default=years)
    df = df[df["year"].isin(selected_year)]

for col in ["city","vertical","rounds"]:
    if col in df.columns:
        vals = sorted(df[col].dropna().astype(str).unique())
        sel = st.sidebar.multiselect(col.title(), vals, default=vals)
        df = df[df[col].astype(str).isin(sel)]

c1,c2,c3,c4 = st.columns(4)
c1.metric("Total Funding", f"${df['amount'].sum():,.0f}" if "amount" in df.columns else "-")
c2.metric("Deals", len(df))
c3.metric("Startups", df["startup"].nunique() if "startup" in df.columns else "-")
c4.metric("Investors", df["investors"].nunique() if "investors" in df.columns else "-")

tab1,tab2,tab3 = st.tabs(["Overview","Insights","Data"])

with tab1:
    if {"year","amount"} <= set(df.columns):
        trend=df.groupby("year",as_index=False)["amount"].sum()
        st.plotly_chart(px.area(trend,x="year",y="amount",title="Funding Trend"),use_container_width=True)

    col1,col2=st.columns(2)
    with col1:
        if {"city","amount"}<=set(df.columns):
            city=df.groupby("city",as_index=False)["amount"].sum().sort_values("amount",ascending=False).head(10)
            st.plotly_chart(px.bar(city,x="city",y="amount",color="amount",title="Top Cities"),use_container_width=True)
    with col2:
        if {"vertical","amount"}<=set(df.columns):
            ind=df.groupby("vertical",as_index=False)["amount"].sum()
            st.plotly_chart(px.pie(ind,names="vertical",values="amount",hole=.5,title="Industry Share"),use_container_width=True)

with tab2:
    c1,c2=st.columns(2)
    with c1:
        if {"startup","amount"}<=set(df.columns):
            top=df.groupby("startup",as_index=False)["amount"].sum().nlargest(10,"amount")
            st.plotly_chart(px.bar(top,x="amount",y="startup",orientation="h",color="amount",title="Top Funded Startups"),use_container_width=True)
    with c2:
        if {"investors","amount"}<=set(df.columns):
            inv=df.groupby("investors",as_index=False)["amount"].sum().nlargest(10,"amount")
            st.plotly_chart(px.treemap(inv,path=["investors"],values="amount",title="Top Investors"),use_container_width=True)

    if {"city","vertical","amount"}<=set(df.columns):
        heat=df.pivot_table(index="vertical",columns="city",values="amount",aggfunc="sum",fill_value=0)
        st.plotly_chart(px.imshow(heat,text_auto=True,title="City vs Industry Heatmap"),use_container_width=True)

with tab3:
    st.dataframe(df,use_container_width=True)
    st.download_button("Download CSV",df.to_csv(index=False).encode(),"filtered_startup_data.csv","text/csv")
