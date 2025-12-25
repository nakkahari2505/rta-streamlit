import streamlit as st
import pandas as pd
import numpy as np

# -------------------------------------------------
# LOAD DATA
# -------------------------------------------------
price = pd.read_parquet("data/processed/price_history.parquet")
const_map = pd.read_parquet("data/processed/index_constituents_map.parquet")

price["date"] = pd.to_datetime(price["date"]).dt.tz_localize(None)

# -------------------------------------------------
# SIDEBAR
# -------------------------------------------------
st.sidebar.header("Controls")

index_list = (
    price.loc[price["entity_id"].str.startswith("IDX_"), "entity_id"]
    .drop_duplicates()
    .sort_values()
    .tolist()
)

selected_index = st.sidebar.selectbox("Select Index", index_list)

ref_date = st.sidebar.date_input(
    "Select reference date",
    price["date"].max().date()
)
ref_date = pd.to_datetime(ref_date)

# -------------------------------------------------
# GET CONSTITUENTS
# -------------------------------------------------
stocks_in_index = (
    const_map
    .query("index_entity_id == @selected_index")["stock_entity_id"]
    .unique()
    .tolist()
)

if not stocks_in_index:
    st.warning("No constituents mapped for this index.")
    st.stop()

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
# INDEX RETURNS
# -------------------------------------------------
idx_df = price[price["entity_id"] == selected_index]

idx_ret_3M = calc_return(idx_df, ref_date, 3).iloc[0]
idx_ret_6M = calc_return(idx_df, ref_date, 6).iloc[0]
idx_ret_1Y = calc_return(idx_df, ref_date, 12).iloc[0]

# -------------------------------------------------
# STOCK RETURNS
# -------------------------------------------------
stk_df = price[price["entity_id"].isin(stocks_in_index)]

ret_1M = calc_return(stk_df, ref_date, 1)
ret_3M = calc_return(stk_df, ref_date, 3)
ret_6M = calc_return(stk_df, ref_date, 6)
ret_1Y = calc_return(stk_df, ref_date, 12)

out = pd.DataFrame({
    "entity_id": ret_3M.index,
    "ret_1M": ret_1M,
    "ret_3M": ret_3M,
    "ret_6M": ret_6M,
    "ret_1Y": ret_1Y,
})

# -------------------------------------------------
# RELATIVE RETURNS
# -------------------------------------------------
out["rel_3M"] = out["ret_3M"] - idx_ret_3M
out["rel_6M"] = out["ret_6M"] - idx_ret_6M
out["rel_1Y"] = out["ret_1Y"] - idx_ret_1Y

# -------------------------------------------------
# RANKS (WINDOW-WISE, NA SAFE)
# -------------------------------------------------
out["rank_3M"] = out["rel_3M"].rank(ascending=False, method="min")
out["rank_6M"] = out["rel_6M"].rank(ascending=False, method="min")
out["rank_1Y"] = out["rel_1Y"].rank(ascending=False, method="min")

# -------------------------------------------------
# AVG RANK USING AVAILABLE WINDOWS ONLY
# -------------------------------------------------
out["avg_rank"] = (
    out[["rank_3M", "rank_6M", "rank_1Y"]]
    .mean(axis=1, skipna=True)
    .round(0)
)

out = out.dropna(subset=["avg_rank"])

out["avg_rank"] = out["avg_rank"].astype(int)

n = len(out)
out["percentile_score"] = (
    (n - out["avg_rank"]) / n * 100
).round(0).astype(int)

# -------------------------------------------------
# FORMAT
# -------------------------------------------------
for c in ["ret_1M", "ret_3M", "ret_6M", "ret_1Y", "rel_3M", "rel_6M", "rel_1Y"]:
    out[c] = out[c].round(1)

out = out.sort_values("avg_rank")

# -------------------------------------------------
# UI
# -------------------------------------------------
st.title(f"{selected_index.replace('IDX_', '')} – Stock Relative Strength")

st.caption(
    f"Reference date: {ref_date.date()} "
    "| Ranks computed using available history"
)

st.dataframe(out, use_container_width=True)
