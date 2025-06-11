import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

# ---- CONFIG ----
st.set_page_config(page_title="📊 Phys Position Dashboard", layout="wide")

# ---- LOAD DATA ----
@st.cache_data
def load_data():
    df = pd.read_csv("Phys_Position_20250610.csv")
    df.columns = df.columns.str.strip()

    # Columns that should be numeric
    numeric_cols = ["Leg-Position", "BBL-Position", "USG-Position",
                    "LBS-Position", "M3-Position",
                    "bbl_product_factor", "usg_product_factor", 
                    "lbs_product_factor", "m3_product_factor",
                    "bbl2_factor", "lbs2_factor", "usg_factor", "m3_2_factor"]

    # Remove commas and convert to float
    for col in numeric_cols:
        df[col] = df[col].astype(str).str.replace(',', '').str.replace(' ', '').str.strip()
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    return df

df = load_data()

# Mask real Business Unit names with dummy names
unique_bu = df["Int BU"].unique()
bu_mapping = {real_bu: f"BU-{i+1}" for i, real_bu in enumerate(unique_bu)}
df["Int BU"] = df["Int BU"].map(bu_mapping)

# ---- SIDEBAR ----
from datetime import datetime

with st.sidebar:
    st.title("🔍 Filters")

    # Internal Business Unit filter
    selected_bu = st.multiselect("Select Internal BU(s)", df["Int BU"].unique(), default=df["Int BU"].unique())

    # Convert Flow Month to datetime (first day of month for consistency)
    df["Flow Month"] = pd.to_datetime(df["Flow Month"], format="%m/%Y", errors="coerce")

    min_date = df["Flow Month"].min()
    max_date = df["Flow Month"].max()

    start_date = st.date_input("📅 Start Month", min_value=min_date, max_value=max_date, value=min_date)
    end_date = st.date_input("📅 End Month", min_value=min_date, max_value=max_date, value=max_date)


    df_filtered = df[
    (df["Int BU"].isin(selected_bu)) &
    (df["Flow Month"] >= pd.to_datetime(start_date)) &
    (df["Flow Month"] <= pd.to_datetime(end_date))
]
    
df_filtered["Flow Month Label"] = df_filtered["Flow Month"].dt.strftime('%b %Y')

# ---- METRICS ----
st.title("📈 Physical Positions Dashboard")
col1, col2, col3 = st.columns(3)
col1.metric("Total M3 Position", f"{df_filtered['M3-Position'].sum():,.2f}")
col2.metric("Total BBL Position", f"{df_filtered['BBL-Position'].sum():,.2f}")
col3.metric("Total LBS Position", f"{df_filtered['LBS-Position'].sum():,.2f}")

# ---- GROUPED BAR ----
st.subheader("🔷 Volume by Internal Business Unit")
bu_group = df_filtered.groupby("Int BU")[["M3-Position", "BBL-Position", "LBS-Position"]].sum().reset_index()
fig_bu = px.bar(bu_group, x="Int BU", y=["M3-Position", "BBL-Position", "LBS-Position"],
                barmode="group", title="Volume Distribution by Business Unit")
st.plotly_chart(fig_bu, use_container_width=True)

# ---- LINE CHART: Monthly Trend ----
st.subheader("📉 Monthly Position Trend")
month_group = df_filtered.groupby("Flow Month")[["M3-Position", "BBL-Position"]].sum().reset_index()
fig_trend = px.line(month_group, x="Flow Month", y=["M3-Position", "BBL-Position"],
                    markers=True, title="Trend Over Time")
st.plotly_chart(fig_trend, use_container_width=True)

# ---- PIE: Conversion Factor Distribution ----
st.subheader("🧪 Avg Product Conversion Factors")
factor_data = df_filtered[["bbl_product_factor", "usg_product_factor", "lbs_product_factor"]].mean().reset_index()
factor_data.columns = ["Product Factor", "Average"]
fig_pie = px.pie(factor_data, names="Product Factor", values="Average", title="Avg Conversion Factors", hole=0.4)
st.plotly_chart(fig_pie, use_container_width=True)

# ---- RAW DATA ----
with st.expander("🔎 View Raw Data"):
    st.dataframe(df_filtered, use_container_width=True)

# ---- INSIGHTS ----
st.subheader("📌 Insights")
top_bu = bu_group.sort_values("M3-Position", ascending=False).iloc[0]
least_bu = bu_group.sort_values("M3-Position").iloc[0]

st.success(f"✅ **Top Business Unit by M3 Volume**: `{top_bu['Int BU']}` ({top_bu['M3-Position']:,.2f})")
st.error(f"❌ **Least Active Business Unit**: `{least_bu['Int BU']}` ({least_bu['M3-Position']:,.2f})")

if df_filtered['M3-Position'].sum() < 0:
    st.info("Overall trend shows **net withdrawal** in M3 positions.")
else:
    st.info("Overall trend shows **net injection** in M3 positions.")
