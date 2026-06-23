"""
GridPace Dashboard — Real-time grid intelligence.
Reads from DuckDB gold layer. Run with: make run
"""

import streamlit as st

from gridpace.config import app_config
from gridpace.monitoring.logger import get_logger

log = get_logger(__name__)

# Page config must be the first Streamlit call
st.set_page_config(
    page_title="GridPace",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

@st.cache_data(ttl=app_config["dashboard"]["cache_ttl_seconds"])
def load_iso_summary():
    """
    Load latest ISO summary from gold layer.
    Cached for 5 minutes to avoid hammering DuckDB on every rerun.
    Returns empty DataFrame if no data exists yet.
    """
    try:
        from gridpace.grid.storage import get_connection
        conn = get_connection()
        df = conn.execute("""
            SELECT
                iso,
                window_start,
                window_end,
                avg_lmp,
                max_lmp,
                min_lmp,
                renewable_pct,
                computed_at
            FROM gold.iso_summary
            WHERE window_start = (
                SELECT MAX(window_start)
                FROM gold.iso_summary
            )
            ORDER BY iso
        """).df()
        conn.close()
        log.info("dashboard_data_loaded", rows=len(df))
        return df
    except Exception as e:
        log.warning("dashboard_data_load_failed", error=str(e))
        return None

def render_sidebar():
    """Render the dashboard sidebar with controls and status."""
    with st.sidebar:
        st.title("⚡ GridPace")
        st.caption("Real-time grid intelligence")

        st.divider()

        st.subheader("Controls")
        if st.button("Refresh Data", use_container_width=True):
            st.cache_data.clear()
            st.rerun()

        st.divider()

        st.subheader("Data Status")
        df = load_iso_summary()
        if df is not None and not df.empty:
            last_updated = df["computed_at"].max()
            st.success(f"Last updated: {last_updated.strftime('%Y-%m-%d %H:%M UTC')}")
        else:
            st.warning("No data yet — run the pipeline first")
            st.code("uv run python -m gridpace.grid.flows")

        st.divider()

        st.subheader("Poll Interval")
        poll_minutes = app_config["ingestion"]["poll_interval_minutes"]
        st.info(f"Data refreshes every {poll_minutes} minutes")

def render_main():
    """Render the main dashboard content."""
    from gridpace.ui.components.iso_cards import render_iso_cards

    st.title("Grid Intelligence Dashboard")
    st.caption("Real-time ISO grid conditions — data refreshes every 2 hours")

    st.divider()

    # Load data
    df = load_iso_summary()

    # ISO price cards
    st.subheader("Current LMP by ISO")
    render_iso_cards(df)


def render_footer():
    """Render the GridStatus attribution footer per ToS Section 4.4."""
    st.divider()
    st.caption(
        "Powered by [Grid Status](https://www.gridstatus.io/) | "
        "Data refreshes every 2 hours on free tier | "
        "GridPace is open source under Apache 2.0"
    )


def main():
    """Main dashboard entrypoint."""
    render_sidebar()
    render_main()
    render_footer()


if __name__ == "__main__":
    main()
