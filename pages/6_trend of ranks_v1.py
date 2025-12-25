import streamlit as st
import pandas as pd
import numpy as np

# -------------------------------------------------
# CONFIG
# -------------------------------------------------
INDEX_ID = "IDX_NIFTY 50"

# -------------------------------------------------
# LOAD DATA
# -------------------------------------------------
price = pd.read_parquet("data/processed/price_history.parquet")
const_map = pd.read_parquet("data/processed/index_constituents_map.parquet")

price["date"] = pd.to_datetime(price["date"]).dt.tz_localize(None)

# -------------------------------------------------
# GET NIFTY 50 STOCKS
# -------------------------------------------------
stocks = (
    const_map
    .query("index_entity_id == @INDEX_ID")["stock_entity_id"]
    .unique()
    .tolist()
)

# -------------------------------------------------
# GET LAST 8 FRIDAYS
# -------------------------------------------------
idx_dates = (
    price.loc[price["entity_id"] == INDEX_ID, "date"]
    .drop_duplicates()
    .sort_values()
)

fridays = (
    idx_dates[idx_dates.dt.weekday == 4]   # Friday
    .tail(8)
    .tolist()
)

# -------------------------------------------------
# RETURN FUNCTION
# -------------------------------------------------
def calc_return(df, end_date, months):
    start_date = end_date - pd.DateOffset(months=months)

    px_end = (
        df[df["date"] <= end_date]
        .sort_values("date")
        .groupby("entity_id")
        .tail(1)
        .set_index("entity_id")["close"]
    )

    px_start = (
        df[df["date"] <= start_date]
        .sort_values("date")
        .groupby("entity_id")
        .tail(1)
        .set_index("entity_id")["close"]
    )

    return (px_end / px_start - 1) * 100

# -------------------------------------------------
# BUILD MATRIX
# -------------------------------------------------
matrix = pd.DataFrame(index=stocks)

for ref_date in fridays:
    # Index returns
    idx_df = price[price["entity_id"] == INDEX_ID]
    idx_3M = calc_return(idx_df, ref_date, 3).iloc[0]
    idx_6M = calc_return(idx_df, ref_date, 6).iloc[0]
    idx_1Y = calc_return(idx_df, ref_date, 12).iloc[0]

    # Stock returns
    stk_df = price[price["entity_id"].isin(stocks)]

    r3 = calc_return(stk_df, ref_date, 3) - idx_3M
    r6 = calc_return(stk_df, ref_date, 6) - idx_6M
    r1 = calc_return(stk_df, ref_date, 12) - idx_1Y

    df = pd.DataFrame({
        "rel_3M": r3,
        "rel_6M": r6,
        "rel_1Y": r1
    })

    # Ranks (within NIFTY 50)
    df["rank_3M"] = df["rel_3M"].rank(ascending=False, method="min")
    df["rank_6M"] = df["rel_6M"].rank(ascending=False, method="min")
    df["rank_1Y"] = df["rel_1Y"].rank(ascending=False, method="min")

    # Average rank for the stock on this date
    df["avg_rank"] = (
        df[["rank_3M", "rank_6M", "rank_1Y"]]
        .mean(axis=1, skipna=True)
        .round(0)
    )

    matrix[ref_date.strftime("%d %b")] = df["avg_rank"]

# -------------------------------------------------
# FINAL FORMAT
# -------------------------------------------------
matrix = matrix.dropna(how="all").astype("Int64")

# -------------------------------------------------
# UI
# -------------------------------------------------
st.title("NIFTY 50 – Stock Average Rank Matrix")

st.caption(
    "Rows: Stocks | Columns: Last 8 Fridays | "
    "Cell = Avg Rank of (3M, 6M, 1Y) vs NIFTY 50"
)

st.dataframe(matrix, use_container_width=True)
