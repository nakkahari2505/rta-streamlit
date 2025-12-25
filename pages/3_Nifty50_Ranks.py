import streamlit as st
import pandas as pd
from pathlib import Path
from datetime import timedelta

# ---------------- CONFIG ----------------
st.set_page_config(page_title="NIFTY 50 Relative Strength", layout="wide")

DATA_DIR = Path("data/processed")
PRICE_FILE = DATA_DIR / "price_history.parquet"
ENTITY_FILE = DATA_DIR / "entity_master.parquet"
CONSTITUENT_FILE = DATA_DIR / "index_constituents_map.parquet"

INDEX_ID = "IDX_NIFTY 50"

# ---------------- LOAD DATA ----------------
@st.cache_data
def load_price_history():
    df = pd.read_parquet(PRICE_FILE)
    df["date"] = pd.to_datetime(df["date"]).dt.tz_localize(None)
    return df

@st.cache_data
def load_constituents():
    df = pd.read_parquet(CONSTITUENT_FILE)
    return df

price_history = load_price_history()
constituents = load_constituents()

# ---------------- UI ----------------
st.title("NIFTY 50 Relative Strength Score")

ref_date = st.date_input(
    "Select reference date",
    value=price_history["date"].max().date()
)
ref_date = pd.Timestamp(ref_date)

st.caption(f"Relative strength as of {ref_date.date()} (nearest trading day used)")

# ---------------- HELPERS ----------------
def nearest_trading_date(df, entity_id, target_date):
    dates = df.loc[df["entity_id"] == entity_id, "date"]
    dates = dates[dates <= target_date]
    return dates.max() if not dates.empty else None

def compute_return(df, entity_id, months):
    end_date = nearest_trading_date(df, entity_id, ref_date)
    if end_date is None:
        return None

    start_target = end_date - pd.DateOffset(months=months)
    start_date = nearest_trading_date(df, entity_id, start_target)

    if start_date is None:
        return None

    px_end = df.loc[
        (df["entity_id"] == entity_id) & (df["date"] == end_date),
        "close"
    ].values[0]

    px_start = df.loc[
        (df["entity_id"] == entity_id) & (df["date"] == start_date),
        "close"
    ].values[0]

    return ((px_end / px_start) - 1) * 100

# ---------------- DATA PREP ----------------
stock_ids = (
    constituents.loc[constituents["index_entity_id"] == INDEX_ID, "stock_entity_id"]
    .unique()
    .tolist()
)

records = []

for sid in stock_ids:
    r3 = compute_return(price_history, sid, 3)
    r6 = compute_return(price_history, sid, 6)
    r12 = compute_return(price_history, sid, 12)

    records.append({
        "entity_id": sid,
        "ret_3M": r3,
        "ret_6M": r6,
        "ret_1Y": r12
    })

df = pd.DataFrame(records)

# ---------------- RELATIVE RETURNS ----------------
idx_r3 = compute_return(price_history, INDEX_ID, 3)
idx_r6 = compute_return(price_history, INDEX_ID, 6)
idx_r12 = compute_return(price_history, INDEX_ID, 12)

df["rel_3M"] = idx_r3 - df["ret_3M"]
df["rel_6M"] = idx_r6 - df["ret_6M"]
df["rel_1Y"] = idx_r12 - df["ret_1Y"]

# ---------------- RANKS ----------------
df["rank_3M"] = df["rel_3M"].rank(ascending=True, method="min")
df["rank_6M"] = df["rel_6M"].rank(ascending=True, method="min")
df["rank_1Y"] = df["rel_1Y"].rank(ascending=True, method="min")

max_rank = len(df)

df[["rank_3M", "rank_6M", "rank_1Y"]] = (
    df[["rank_3M", "rank_6M", "rank_1Y"]]
    .fillna(max_rank)
)

df["avg_rank"] = df[["rank_3M", "rank_6M", "rank_1Y"]].mean(axis=1)

df["percentile_score"] = (
    1 - (df["avg_rank"] - 1) / (max_rank - 1)
) * 100

# ---------------- FORMATTING ----------------
for c in ["ret_3M", "ret_6M", "ret_1Y", "rel_3M", "rel_6M", "rel_1Y"]:
    df[c] = df[c].round(1)

df[["rank_3M", "rank_6M", "rank_1Y", "avg_rank", "percentile_score"]] = (
    df[["rank_3M", "rank_6M", "rank_1Y", "avg_rank", "percentile_score"]]
    .round(0)
    .astype(int)
)

# Sort by strength
df = df.sort_values("percentile_score", ascending=False)

# ---------------- DISPLAY ----------------
st.dataframe(
    df.style.format({
        "ret_3M": "{:.1f}%",
        "ret_6M": "{:.1f}%",
        "ret_1Y": "{:.1f}%",
        "rel_3M": "{:.1f}%",
        "rel_6M": "{:.1f}%",
        "rel_1Y": "{:.1f}%"
    }),
    use_container_width=True
)
