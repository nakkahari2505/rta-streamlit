import streamlit as st
import pandas as pd

# -------------------------------------------------
# LOAD DATA
# -------------------------------------------------
price = pd.read_parquet("data/processed/price_history.parquet")
const_map = pd.read_parquet("data/processed/index_constituents_map.parquet")

price["date"] = pd.to_datetime(price["date"]).dt.tz_localize(None)

# -------------------------------------------------
# GET NIFTY 50 STOCKS
# -------------------------------------------------
INDEX_ID = "IDX_NIFTY 50"

nifty50_stocks = (
    const_map
    .query("index_entity_id == @INDEX_ID")["stock_entity_id"]
    .drop_duplicates()
    .sort_values()
    .tolist()
)

# -------------------------------------------------
# SIDEBAR
# -------------------------------------------------
st.sidebar.header("Controls")

selected_stock = st.sidebar.selectbox(
    "Select NIFTY 50 Stock",
    nifty50_stocks
)

# -------------------------------------------------
# FILTER STOCK DATA (LAST 1 YEAR)
# -------------------------------------------------
stk_df = price[price["entity_id"] == selected_stock].sort_values("date")

if stk_df.empty:
    st.warning("No price data available.")
    st.stop()

end_date = stk_df["date"].max()
start_date = end_date - pd.DateOffset(years=1)

stk_df = stk_df[stk_df["date"] >= start_date].copy()

# -------------------------------------------------
# CALCULATE SMAs
# -------------------------------------------------
stk_df["SMA_50"] = stk_df["close"].rolling(window=50).mean()
stk_df["SMA_200"] = stk_df["close"].rolling(window=200).mean()

# -------------------------------------------------
# UI
# -------------------------------------------------
st.title(f"{selected_stock.replace('STK_', '')} – 50 & 200 Day SMA")

st.caption(
    f"Period: {start_date.date()} to {end_date.date()} | Simple Moving Averages"
)

chart_df = stk_df.set_index("date")[["SMA_50", "SMA_200"]]

st.line_chart(chart_df)
