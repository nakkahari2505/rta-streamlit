import streamlit as st
import pandas as pd
import numpy as np

# -------------------------------------------------
# LOAD DATA
# -------------------------------------------------
price = pd.read_parquet("data/processed/price_history.parquet")
price["date"] = pd.to_datetime(price["date"]).dt.tz_localize(None)

# -------------------------------------------------
# SIDEBAR
# -------------------------------------------------
st.sidebar.header("Controls")

ref_date = st.sidebar.date_input(
    "Select reference date",
    price["date"].max().date()
)
ref_date = pd.to_datetime(ref_date)

# -------------------------------------------------
# FILTER SECTOR / THEMATIC INDICES
# (EXCLUDES BROAD MARKET INDICES)
# -------------------------------------------------
exclude_indices = {
    "IDX_NIFTY 50",
    "IDX_NIFTY 100",
    "IDX_NIFTY 200",
    "IDX_NIFTY 500",
    "IDX_NIFTY MIDCAP 100",
    "IDX_NIFTY MIDCAP 150",
    "IDX_NIFTY MIDCAP 50",
    "IDX_NIFTY NEXT 50",
    "IDX_NIFTY SMLCAP 50",
    "IDX_NIFTY SMLCAP 100",
    "IDX_NIFTY SMLCAP 250",
    "IDX_NIFTY TOTAL MKT"
}

sector_indices = (
    price.loc[
        price["entity_id"].str.startswith("IDX_")
        & ~price["entity_id"].isin(exclude_indices),
        "entity_id"
    ]
    .drop_duplicates()
    .sort_values()
    .tolist()
)

# -------------------------------------------------
# RETURN FUNCTIONS
# -------------------------------------------------
def calc_return_months(df, end_date, months):
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


def calc_return_weeks(df, end_date, weeks):
    start_date = end_date - pd.DateOffset(weeks=weeks)

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
# CALCULATE RETURNS
# -------------------------------------------------
df = price[price["entity_id"].isin(sector_indices)]

ret_1W = calc_return_weeks(df, ref_date, 1)
ret_1M = calc_return_months(df, ref_date, 1)
ret_3M = calc_return_months(df, ref_date, 3)
ret_6M = calc_return_months(df, ref_date, 6)
ret_1Y = calc_return_months(df, ref_date, 12)

mat = pd.DataFrame({
    "Sector": ret_1M.index,
    "1 Week": ret_1W,
    "1 Month": ret_1M,
    "3 Month": ret_3M,
    "6 Month": ret_6M,
    "1 Year": ret_1Y
}).set_index("Sector")

# -------------------------------------------------
# COLUMN-WISE RANKING
# -------------------------------------------------
rank_mat = mat.rank(ascending=False, method="min")

# -------------------------------------------------
# COLOR LOGIC
# -------------------------------------------------
def color_rank(val, col):
    if pd.isna(val):
        return ""
    if val <= 5:
        return "background-color: #6FCF97"  # green
    elif val > (rank_mat[col].max() - 5):
        return "background-color: #EB5757"  # red
    return ""

styled = rank_mat.style.apply(
    lambda s: [color_rank(v, s.name) for v in s],
    axis=0
).format("{:.0f}")

# -------------------------------------------------
# UI
# -------------------------------------------------
st.title("Sectoral Momentum Matrix")

st.caption(
    f"Ranks as of {ref_date.date()} | "
    "Column-wise ranking | Top 5 = Green, Bottom 5 = Red"
)

st.dataframe(styled, use_container_width=True)
