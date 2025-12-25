import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import timedelta

# ---------------------------------
# Page config
# ---------------------------------
st.set_page_config(
    page_title="RTA | Sector Overview",
    layout="wide"
)

# ---------------------------------
# Load data
# ---------------------------------
@st.cache_data
def load_data():
    df = pd.read_parquet("data/processed/price_history.parquet")
    df["date"] = pd.to_datetime(df["date"]).dt.tz_localize(None)
    return df

price_history = load_data()

# ---------------------------------
# Helpers
# ---------------------------------
def get_target_start_date(ref_date, period):
    if period == "1W":
        return ref_date - timedelta(weeks=1)
    if period == "1M":
        return ref_date - pd.DateOffset(months=1)
    if period == "3M":
        return ref_date - pd.DateOffset(months=3)
    if period == "6M":
        return ref_date - pd.DateOffset(months=6)
    if period == "1Y":
        return ref_date - pd.DateOffset(years=1)

def compute_return(df, window_start, window_end):
    df_window = df[
        (df["date"] >= window_start) &
        (df["date"] <= window_end)
    ].sort_values("date")

    if len(df_window) < 2:
        return None

    start_price = df_window.iloc[0]["close"]
    end_price = df_window.iloc[-1]["close"]

    return (end_price / start_price - 1) * 100

# ---------------------------------
# Page Title
# ---------------------------------
st.title("Sector Overview")
st.caption("Sectoral index returns as of selected reference date")

# ---------------------------------
# Reference Date
# ---------------------------------
max_available_date = price_history["date"].max().date()

reference_date = st.date_input(
    "Reference Date",
    value=max_available_date,
    max_value=max_available_date
)

reference_date = pd.to_datetime(reference_date)

# ---------------------------------
# Timeframe buttons (stateful)
# ---------------------------------
if "sector_period" not in st.session_state:
    st.session_state.sector_period = "1W"

st.subheader("Timeframe")

tf_cols = st.columns(5)
timeframes = ["1W", "1M", "3M", "6M", "1Y"]

for col, tf in zip(tf_cols, timeframes):
    if tf == st.session_state.sector_period:
        col.button(
            tf,
            use_container_width=True,
            type="primary",
            key=f"sector_tf_active_{tf}"
        )
    else:
        if col.button(
            tf,
            use_container_width=True,
            key=f"sector_tf_{tf}"
        ):
            st.session_state.sector_period = tf

period = st.session_state.sector_period

# ---------------------------------
# Frozen Sector Universe
# ---------------------------------
SECTOR_INDICES = [
    "IDX_NIFTY AUTO",
    "IDX_NIFTY BANK",
    "IDX_NIFTY ENERGY",
    "IDX_NIFTY FMCG",
    "IDX_NIFTY IT",
    "IDX_NIFTY MEDIA",
    "IDX_NIFTY METAL",
    "IDX_NIFTY OIL AND GAS",
    "IDX_NIFTY PHARMA",
    "IDX_NIFTY PSU BANK",
    "IDX_NIFTY PVT BANK",
    "IDX_NIFTY REALTY",
    "IDX_NIFTY INFRA",
    "IDX_NIFTY MNC",
    "IDX_NIFTY CONSUMPTION",
    "IDX_NIFTY FINANCIAL SERVICES"
    "IDX_NIFTY CPSE"
    "IDX_NIFTY PSE"
    "IDX_NIFTY INDIA DEFENCE"
    "IDX_NIFTY INDIA TOURISM"
    "IDX_NIFTY COMMODITIES"
    "IDX_NIFTY FIN SERVICE"
    "IDX_NIFTY CAPITAL MARKETS"
    
]

# ---------------------------------
# Compute returns
# ---------------------------------
target_start_date = get_target_start_date(reference_date, period)

rows = []
for idx in SECTOR_INDICES:
    df_idx = price_history[price_history["entity_id"] == idx]

    ret = compute_return(df_idx, target_start_date, reference_date)

    rows.append({
        "Sector": idx.replace("IDX_NIFTY ", ""),
        "Return (%)": round(ret, 2) if ret is not None else None
    })

result_df = (
    pd.DataFrame(rows)
    .dropna()
    .sort_values("Return (%)", ascending=False)
)

# ---------------------------------
# Plot
# ---------------------------------
fig = px.bar(
    result_df,
    x="Sector",
    y="Return (%)",
    text="Return (%)",
    title=f"Sector Returns – {period}",
    color_discrete_sequence=["#0A8F79"]
)

fig.update_traces(
    texttemplate="%{text:.2f}%",
    textposition="outside"
)

fig.update_layout(
    height=380,
    margin=dict(t=60, l=20, r=20, b=40),
    yaxis_title="Return (%)",
    xaxis_title="",
    uniformtext_minsize=10,
    uniformtext_mode="hide"
)

st.plotly_chart(fig, use_container_width=True)
