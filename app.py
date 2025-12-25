import streamlit as st

st.set_page_config(
    page_title="Rank Trajectory Analytics (RTA)",
    layout="wide"
)

# -------------------------
# Header
# -------------------------
st.title("Rank Trajectory Analytics (RTA)")
st.caption("Decision intelligence platform for markets")

st.markdown("---")

# -------------------------
# Dashboards section
# -------------------------
st.subheader("Dashboards")

st.markdown(
    """
- 👉 **[Benchmark Indices Overview](./Benchmark_Ind)**
  
  Compare benchmark index performance across selectable timeframes.

- 👉 **[Sector Overview](./Sector_Overview)**
  
  Sector-level performance and momentum across time horizons.

- 👉 **[NIFTY 50 Relative Strength](./Nifty50_Ranks)**
  
  Stock-level relative strength analysis within NIFTY 50 using  
  3M, 6M, 1Y returns, relative ranks, average rank and percentile score.
"""
)

st.markdown("---")

# -------------------------
# Footer / roadmap hint
# -------------------------
st.caption(
    "More modules coming next: Rank Trajectory Maps, Momentum Maturity Matrix, "
    "Rotation Signals, and AI-assisted insights."
)
