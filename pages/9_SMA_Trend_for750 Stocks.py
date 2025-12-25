# pages/9_Stock_Snapshot_All_Universe.py

import streamlit as st
import pandas as pd
import numpy as np

# --------------------------------------------------
# Page config
# --------------------------------------------------
st.set_page_config(
    page_title="Stock Snapshot – All Universe (750 Stocks)",
    layout="wide"
)
st.title("Stock Snapshot – All Universe (750 Stocks)")

# --------------------------------------------------
# Load data
# --------------------------------------------------
@st.cache_data
def load_data():
    price = pd.read_parquet("data/processed/price_history.parquet")
    master = pd.read_parquet("data/processed/entity_master.parquet")

    price["date"] = pd.to_datetime(price["date"]).dt.tz_localize(None)
    return price, master

price_df, master_df = load_data()

# --------------------------------------------------
# Join + keep only stocks
# --------------------------------------------------
df = price_df.merge(
    master_df[["entity_id", "entity_type", "entity_name", "symbol"]],
    on="entity_id",
    how="left"
)

df = df[df["entity_type"] == "STOCK"].copy()

# --------------------------------------------------
# Reference date
# --------------------------------------------------
available_dates = pd.to_datetime(sorted(df["date"].unique()))

ref_date_input = st.date_input(
    "Select Reference Date",
    value=available_dates.max().date(),
    min_value=available_dates.min().date(),
    max_value=available_dates.max().date(),
)

ref_date_input = pd.to_datetime(ref_date_input)
ref_date = available_dates[available_dates <= ref_date_input].max()

st.caption(f"Effective trade date used: {ref_date.strftime('%Y-%m-%d')}")

# --------------------------------------------------
# Helper functions
# --------------------------------------------------
def past_close(g, ref_date, n):
    d = g[g["date"] <= ref_date].sort_values("date")
    if len(d) < n + 1:
        return np.nan
    return d.iloc[-(n + 1)]["close"]

def sma(g, ref_date, n):
    d = g[g["date"] <= ref_date].sort_values("date").tail(n)
    if len(d) < n:
        return np.nan
    return d["close"].mean()

def high_52w(g, ref_date):
    d = g[
        (g["date"] <= ref_date) &
        (g["date"] >= ref_date - pd.Timedelta(days=365))
    ]
    if d.empty:
        return np.nan
    return d["close"].max()

def yn(cond):
    return "Yes" if cond else "No"

# --------------------------------------------------
# Core computation
# --------------------------------------------------
rows = []

for entity_id, g in df.groupby("entity_id"):
    g = g.sort_values("date")

    today = g[g["date"] == ref_date]
    if today.empty:
        continue

    close = today.iloc[0]["close"]

    c1m = past_close(g, ref_date, 21)
    c3m = past_close(g, ref_date, 63)
    c6m = past_close(g, ref_date, 126)
    c1y = past_close(g, ref_date, 252)

    def ret(c):
        return round((close / c - 1) * 100, 1) if pd.notna(c) else np.nan

    sma20  = sma(g, ref_date, 20)
    sma50  = sma(g, ref_date, 50)
    sma100 = sma(g, ref_date, 100)
    sma200 = sma(g, ref_date, 200)

    h52 = high_52w(g, ref_date)
    pct_52w = round((close - h52) / h52 * 100, 1) if pd.notna(h52) else np.nan

    rows.append({
        "entity_id": entity_id,
        "symbol": today.iloc[0]["symbol"],
        "entity_name": today.iloc[0]["entity_name"],
        "Close": round(close, 1),
        "1M_Return_%": ret(c1m),
        "3M_Return_%": ret(c3m),
        "6M_Return_%": ret(c6m),
        "1Y_Return_%": ret(c1y),
        "SMA_20": round(sma20, 1),
        "SMA_50": round(sma50, 1),
        "SMA_100": round(sma100, 1),
        "SMA_200": round(sma200, 1),
        "20D_SMA_gt_50D_SMA": yn(pd.notna(sma20) and pd.notna(sma50) and sma20 > sma50),
        "50D_SMA_gt_100D_SMA": yn(pd.notna(sma50) and pd.notna(sma100) and sma50 > sma100),
        "100D_SMA_gt_200D_SMA": yn(pd.notna(sma100) and pd.notna(sma200) and sma100 > sma200),
        "Pct_Diff_52W_High": f"{pct_52w}%" if pd.notna(pct_52w) else np.nan
    })

final_df = pd.DataFrame(rows)

# --------------------------------------------------
# Display
# --------------------------------------------------
st.dataframe(final_df, use_container_width=True, height=700)
