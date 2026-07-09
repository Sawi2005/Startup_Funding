"""
Indian Startup Funding Dashboard
---------------------------------
An interactive Streamlit app for exploring startup funding data:
overall market trends, per-startup profiles, and per-investor portfolios.

Author: Sawi2005
"""

import re
from difflib import SequenceMatcher

import pandas as pd
import plotly.express as px
import streamlit as st

# ----------------------------------------------------------------------------
# Page config
# ----------------------------------------------------------------------------
st.set_page_config(
    page_title="Startup Funding Dashboard",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded",
)

DATA_PATH = "startup_clear.csv"
FUZZY_MATCH_THRESHOLD = 0.90  # 0-1, higher = stricter matching


# ----------------------------------------------------------------------------
# Text / entity cleaning helpers
# ----------------------------------------------------------------------------
def _basic_clean(text: str) -> str:
    """Strip stray whitespace, non-breaking spaces, and trailing punctuation
    that shows up a lot in this dataset (e.g. 'Sequoia Capital\\xa0.')."""
    text = text.replace("\xa0", " ").replace("\\xc2\\xa0", " ")
    text = re.sub(r"\s+", " ", text).strip()
    text = text.strip(" .,-")
    return text


def _canonicalize_names(names: list[str]) -> dict:
    """Cluster near-duplicate names (typos, casing, spacing) into a single
    canonical spelling using similarity ratio + union-find, so 'Sequoia
    Capital', 'sequoia capital', 'Sequoia  Capital.' all collapse to one
    entry. Canonical form = the most frequently occurring exact variant in
    each cluster, so the "correct"/most common spelling wins."""
    unique = sorted(set(names))
    parent = {n: n for n in unique}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb

    # Bucket by lowercase first-3-chars to avoid full O(n^2) comparison
    # on large investor lists, then fuzzy-compare within each bucket.
    buckets: dict = {}
    for n in unique:
        key = n.lower()[:3]
        buckets.setdefault(key, []).append(n)

    for bucket in buckets.values():
        for i in range(len(bucket)):
            for j in range(i + 1, len(bucket)):
                a, b = bucket[i], bucket[j]
                ratio = SequenceMatcher(None, a.lower(), b.lower()).ratio()
                if ratio >= FUZZY_MATCH_THRESHOLD:
                    union(a, b)

    clusters: dict = {}
    for n in unique:
        clusters.setdefault(find(n), []).append(n)

    counts = pd.Series(names).value_counts()
    mapping = {}
    for members in clusters.values():
        canonical = max(members, key=lambda m: (counts.get(m, 0), -len(m)))
        for m in members:
            mapping[m] = canonical
    return mapping


@st.cache_data
def load_data(path: str) -> pd.DataFrame:
    """Load and clean the funding dataset:
    - normalizes whitespace/encoding artifacts across text columns
    - fills missing city / sub-vertical with an explicit 'Unknown' instead
      of leaving blanks / NaN
    - fuzzy-deduplicates near-identical investor name spellings so the same
      investor isn't split across multiple entries in charts and filters
    """
    df = pd.read_csv(path)
    df.columns = [c.strip().lower() for c in df.columns]

    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce")
    df["month"] = df["date"].dt.month
    df["year"] = df["date"].dt.year

    for col in ["startup", "vertical", "subvertical", "city", "investors", "rounds"]:
        if col in df.columns:
            df[col] = df[col].astype(str).apply(_basic_clean)
            df[col] = df[col].replace({"nan": "", "": pd.NA})

    # Explicit "Unknown" instead of blank/NaN so filters and charts don't
    # silently drop rows or show empty labels.
    for col in ["city", "subvertical", "vertical", "rounds"]:
        if col in df.columns:
            df[col] = df[col].fillna("Unknown")

    df["startup"] = df["startup"].fillna("Unknown")

    # --- Fuzzy-dedupe investor names -----------------------------------
    if "investors" in df.columns:
        df["investors"] = df["investors"].fillna("Unknown")
        all_investor_tokens = [
            tok.strip()
            for group in df["investors"].str.split(",")
            for tok in group
            if tok.strip()
        ]
        name_map = _canonicalize_names(all_investor_tokens)

        def _rejoin(cell: str) -> str:
            tokens = [t.strip() for t in cell.split(",") if t.strip()]
            canon = [name_map.get(t, t) for t in tokens]
            # de-dupe while preserving order (a round can double-list an
            # investor after normalization collapses two spellings)
            seen, ordered = set(), []
            for c in canon:
                if c not in seen:
                    seen.add(c)
                    ordered.append(c)
            return ", ".join(ordered) if ordered else "Unknown"

        df["investors"] = df["investors"].apply(_rejoin)

    df = df.dropna(subset=["date", "amount"])
    return df


def investor_mask(df: pd.DataFrame, investor: str) -> pd.Series:
    """Exact match against comma-separated investor lists (fixes the
    substring-collision bug in the original str.contains(investor) calls)."""
    pattern = r"(^|,\s*)" + re.escape(investor) + r"(\s*,|$)"
    return df["investors"].str.contains(pattern, regex=True, na=False)


def format_cr(x: float) -> str:
    return f"₹{x:,.0f} Cr"


# ----------------------------------------------------------------------------
# Overall analysis
# ----------------------------------------------------------------------------
def load_overall_analysis(df: pd.DataFrame):
    st.title("📊 Overall Analysis")

    total = df["amount"].sum()
    max_funding = df.groupby("startup")["amount"].max().sort_values(ascending=False)
    avg_fund = df.groupby("startup")["amount"].sum().mean()
    n_startups = df["startup"].nunique()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Funding", format_cr(total))
    c2.metric("Top Single Round", format_cr(max_funding.iloc[0]), max_funding.index[0])
    c3.metric("Average Ticket Size", format_cr(avg_fund))
    c4.metric("Funded Startups", f"{n_startups:,}")

    st.divider()

    left, right = st.columns([2, 1])

    with left:
        st.subheader("Month-over-Month Trend")
        metric = st.radio("View", ["Total Amount (₹Cr)", "Deal Count"], horizontal=True)
        temp = df.dropna(subset=["year", "month"]).copy()
        temp["year"] = temp["year"].astype(int)
        temp["month"] = temp["month"].astype(int)
        temp["period"] = pd.to_datetime(
            temp["year"].astype(str) + "-" + temp["month"].astype(str) + "-01"
        )
        if metric == "Total Amount (₹Cr)":
            grouped = temp.groupby("period")["amount"].sum().reset_index()
            y = "amount"
        else:
            grouped = temp.groupby("period")["amount"].count().reset_index()
            y = "amount"
        grouped = grouped.sort_values("period")
        fig = px.line(grouped, x="period", y=y, markers=True)
        fig.update_layout(xaxis_title="Month", yaxis_title=metric, height=380)
        st.plotly_chart(fig, use_container_width=True)

    with right:
        st.subheader("Top Sectors")
        sector = (
            df.groupby("vertical")["amount"].sum().sort_values(ascending=False).head(8)
        )
        fig = px.pie(values=sector.values, names=sector.index, hole=0.45)
        fig.update_layout(height=380, showlegend=False)
        fig.update_traces(textposition="inside", textinfo="percent+label")
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("Top 10 Funded Startups")
    top_startups = (
        df.groupby("startup")["amount"].sum().sort_values(ascending=False).head(10)
    )
    fig = px.bar(
        x=top_startups.values, y=top_startups.index, orientation="h",
        labels={"x": "Total Funding (₹Cr)", "y": "Startup"},
    )
    fig.update_layout(yaxis={"categoryorder": "total ascending"}, height=420)
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Top 10 Investors by Deal Count")
    inv_counts = (
        df.assign(investors=df["investors"].str.split(","))
        .explode("investors")
        .assign(investors=lambda d: d["investors"].str.strip())
    )
    inv_counts = inv_counts[inv_counts["investors"].ne("") & inv_counts["investors"].ne("nan")]
    top_investors = inv_counts["investors"].value_counts().head(10)
    fig = px.bar(
        x=top_investors.index, y=top_investors.values,
        labels={"x": "Investor", "y": "Number of Deals"},
    )
    fig.update_layout(height=380)
    st.plotly_chart(fig, use_container_width=True)


# ----------------------------------------------------------------------------
# Startup profile
# ----------------------------------------------------------------------------
def load_startup_details(df: pd.DataFrame, startup: str):
    sub = df[df["startup"] == startup]
    st.title(startup)

    if sub.empty:
        st.warning("No records found for this startup.")
        return

    c1, c2, c3 = st.columns(3)
    c1.metric("Total Raised", format_cr(sub["amount"].sum()))
    c2.metric("Funding Rounds", sub.shape[0])
    c3.metric("City", sub["city"].mode().iat[0] if not sub["city"].mode().empty else "Unknown")

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Industries")
        st.dataframe(sub["vertical"].dropna().drop_duplicates(), use_container_width=True, hide_index=True)
    with col2:
        st.subheader("Sub-industries")
        st.dataframe(sub["subvertical"].dropna().drop_duplicates(), use_container_width=True, hide_index=True)

    st.subheader("Funding History")
    hist = sub[["date", "investors", "rounds", "amount", "city"]].sort_values("date")
    st.dataframe(hist, use_container_width=True, hide_index=True)

    fig = px.bar(hist, x="date", y="amount", hover_data=["rounds", "investors"],
                 labels={"amount": "Amount (₹Cr)", "date": "Date"})
    fig.update_layout(height=350)
    st.plotly_chart(fig, use_container_width=True)


# ----------------------------------------------------------------------------
# Investor profile
# ----------------------------------------------------------------------------
def load_investor_details(df: pd.DataFrame, investor: str):
    sub = df[investor_mask(df, investor)]
    st.title(investor)

    if sub.empty:
        st.warning("No records found for this investor.")
        return

    st.subheader("Most Recent Investments")
    recent = sub.sort_values("date", ascending=False).head(5)[
        ["date", "startup", "vertical", "city", "rounds", "amount"]
    ]
    st.dataframe(recent, use_container_width=True, hide_index=True)

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.subheader("Biggest Bets")
        big = sub.groupby("startup")["amount"].sum().sort_values(ascending=False).head()
        fig = px.bar(x=big.index, y=big.values, labels={"x": "", "y": "₹Cr"})
        fig.update_layout(height=320)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("Sectors")
        sec = sub.groupby("vertical")["amount"].sum()
        fig = px.pie(values=sec.values, names=sec.index, hole=0.4)
        fig.update_layout(height=320, showlegend=False)
        fig.update_traces(textposition="inside", textinfo="percent")
        st.plotly_chart(fig, use_container_width=True)

    with col3:
        st.subheader("Stage")
        rounds = sub.groupby("rounds")["amount"].sum()
        fig = px.pie(values=rounds.values, names=rounds.index, hole=0.4)
        fig.update_layout(height=320, showlegend=False)
        fig.update_traces(textposition="inside", textinfo="percent")
        st.plotly_chart(fig, use_container_width=True)

    with col4:
        st.subheader("Cities")
        city = sub.groupby("city")["amount"].sum()
        fig = px.pie(values=city.values, names=city.index, hole=0.4)
        fig.update_layout(height=320, showlegend=False)
        fig.update_traces(textposition="inside", textinfo="percent")
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("Year-over-Year Investment")
    yoy = sub.dropna(subset=["year"]).groupby("year")["amount"].sum().reset_index()
    fig = px.line(yoy, x="year", y="amount", markers=True,
                   labels={"amount": "₹Cr", "year": "Year"})
    fig.update_layout(height=320)
    st.plotly_chart(fig, use_container_width=True)


# ----------------------------------------------------------------------------
# App shell
# ----------------------------------------------------------------------------
def main():
    try:
        df = load_data(DATA_PATH)
    except FileNotFoundError:
        st.error(f"Couldn't find `{DATA_PATH}`. Make sure it sits next to app.py.")
        st.stop()

    st.sidebar.title("🚀 Startup Funding Analysis")
    option = st.sidebar.selectbox("View", ["Overall Analysis", "Startup", "Investor"])

    if option == "Overall Analysis":
        load_overall_analysis(df)

    elif option == "Startup":
        selected_startup = st.sidebar.selectbox(
            "Select Startup", sorted(df["startup"].dropna().unique().tolist())
        )
        if st.sidebar.button("Find Startup Details", use_container_width=True):
            load_startup_details(df, selected_startup)
        else:
            st.title("Startup Analysis")
            st.caption("Pick a startup from the sidebar and hit **Find Startup Details**.")

    else:
        investors = sorted(
            set(
                i.strip()
                for group in df["investors"].dropna().str.split(",")
                for i in group
                if i.strip()
            )
        )
        selected_investor = st.sidebar.selectbox("Select Investor", investors)
        if st.sidebar.button("Find Investor Details", use_container_width=True):
            load_investor_details(df, selected_investor)
        else:
            st.title("Investor Analysis")
            st.caption("Pick an investor from the sidebar and hit **Find Investor Details**.")

    st.sidebar.divider()
    st.sidebar.caption("Data: Indian Startup Funding dataset · Built with Streamlit & Plotly")


if __name__ == "__main__":
    main()
