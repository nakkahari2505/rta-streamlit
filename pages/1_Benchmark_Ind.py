import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import timedelta

# ---------------------------------
# Page config
# ---------------------------------
st.set_page_config(
    page_title="RTA | Benchmark Indices",
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
# Sidebar
# ---------------------------------
st.sidebar.title("RTA Dashboard")

all_indices = sorted(
    price_history[
        price_history["entity_id"].str.startswith("IDX_")
    ]["entity_id"].unique()
)

selected_indices = st.sidebar.multiselect(
    "Select Indices",
    options=all_indices,
    default=[
        "IDX_NIFTY 50",
        "IDX_NIFTY NEXT 50",
        "IDX_NIFTY 500",
        "IDX_NIFTY MIDCAP 150",
        "IDX_NIFTY SMLCAP 250"
    ]

)

# Reference date selector (GLOBAL anchor)
max_available_date = price_history["date"].max().date()

reference_date = st.sidebar.date_input(
    "Reference Date",
    value=max_available_date,
    max_value=max_available_date
)

reference_date = pd.to_datetime(reference_date)

# ---------------------------------
# Main Page
# ---------------------------------
st.title("Benchmark Indices Overview")
st.caption(f"Returns as of {reference_date.date()} (using nearest available trading day)")

# ---- Timeframe buttons (stateful & highlighted) ----
if "period" not in st.session_state:
    st.session_state.period = "6M"

st.subheader("Timeframe")

tf_cols = st.columns(5)
timeframes = ["1W", "1M", "3M", "6M", "1Y"]

for col, tf in zip(tf_cols, timeframes):
    if tf == st.session_state.period:
        col.button(
            tf,
            use_container_width=True,
            type="primary",
            key=f"tf_active_{tf}"
        )
    else:
        if col.button(
            tf,
            use_container_width=True,
            key=f"tf_{tf}"
        ):
            st.session_state.period = tf

period = st.session_state.period

# ---------------------------------
# Chart
# ---------------------------------
if not selected_indices:
    st.warning("Please select at least one index.")
else:
    target_start_date = get_target_start_date(reference_date, period)

    rows = []
    for idx in selected_indices:
        df_idx = price_history[
            price_history["entity_id"] == idx
        ]

        ret = compute_return(df_idx, target_start_date, reference_date)

        rows.append({
            "Index": idx.replace("IDX_", ""),
            "Return (%)": round(ret, 2) if ret is not None else None
        })

    result_df = (
        pd.DataFrame(rows)
        .dropna()
        .sort_values("Return (%)", ascending=False)
    )

    fig = px.bar(
        result_df,
        x="Index",
        y="Return (%)",
        text="Return (%)",
        title=f"Benchmark Indices Returns – {period}",
        color_discrete_sequence=["#0A8F79"]
    )

    fig.update_traces(
        texttemplate="%{text:.2f}%",
        textposition="outside"
    )

    fig.update_layout(
        height=360,
        margin=dict(t=55, l=20, r=20, b=20),
        yaxis_title="Return (%)",
        xaxis_title="",
        uniformtext_minsize=10,
        uniformtext_mode="hide"
    )

    st.plotly_chart(fig, use_container_width=True)
