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
    Cached for TTL seconds to avoid hammering DuckDB on every rerun.
    Returns None if no data exists yet.
    Auto-invalidates cache if expected columns are missing (e.g. after migration).
    """
    try:
        from gridpace.grid.storage import get_connection
        conn = get_connection()
        df = conn.execute("""
                    WITH latest AS (
                        SELECT MAX(window_start) as max_window
                        FROM gold.iso_summary
                    ),
                    lookback AS (
                        SELECT 
                            iso,
                            MIN(avg_lmp) as min_lmp,
                            MAX(avg_lmp) as max_lmp
                        FROM gold.iso_summary
                        WHERE window_start >= (SELECT max_window FROM latest) - INTERVAL '48 hours'
                        GROUP BY iso
                    )
                    SELECT
                        g.iso,
                        g.window_start,
                        g.window_end,
                        g.avg_lmp,
                        l.min_lmp,
                        l.max_lmp,
                        g.renewable_pct,
                        g.natural_gas,
                        g.wind,
                        g.solar,
                        g.coal,
                        g.nuclear,
                        g.other,
                        g.computed_at
                    FROM gold.iso_summary g
                    JOIN lookback l ON g.iso = l.iso
                    WHERE g.window_start = (SELECT max_window FROM latest)
                    ORDER BY g.iso
                """).df()
        conn.close()

        # Auto-invalidate cache if expected fuel columns are missing
        expected_fuel_cols = ["wind", "solar", "natural_gas", "coal", "nuclear"]
        if not all(col in df.columns for col in expected_fuel_cols):
            st.cache_data.clear()
            return load_iso_summary()

        log.info("dashboard_data_loaded", rows=len(df))
        return df
    except Exception as e:
        log.warning("dashboard_data_load_failed", error=str(e))
        return None

@st.cache_data(ttl=app_config["dashboard"]["cache_ttl_seconds"])
def load_anomaly_results():
    """
    Load anomaly detection results for all ISOs.
    Returns dict keyed by ISO with status and z_score.
    """
    try:
        from gridpace.grid.storage import get_connection
        from gridpace.intelligence.detection.anomaly import detect_anomalies

        conn = get_connection()
        history_df = conn.execute("SELECT * FROM gold.iso_summary").df()
        current_df = conn.execute("""
            SELECT * FROM gold.iso_summary
            WHERE window_start = (SELECT MAX(window_start) FROM gold.iso_summary)
        """).df()
        conn.close()

        if history_df.empty or current_df.empty:
            return {}

        return detect_anomalies(history_df, current_df)
    except Exception as e:
        log.warning("anomaly_load_failed", error=str(e))
        return {}


@st.cache_data(ttl=app_config["dashboard"]["cache_ttl_seconds"])
def load_iso_history():
    """
    Load full ISO summary history within the lookback window for anomaly baselines.
    Returns one row per ISO per window_start — not aggregated.
    Returns None if no data exists yet.
    """
    try:
        from gridpace.grid.storage import get_connection
        lookback_hours = app_config["dashboard"]["lookback_hours"]
        conn = get_connection()
        df = conn.execute("""
            SELECT iso, window_start, avg_lmp
            FROM gold.iso_summary
            WHERE window_start >= NOW() - INTERVAL (?) HOUR
            ORDER BY iso, window_start
        """, [lookback_hours]).df()
        conn.close()
        log.info("dashboard_history_loaded", rows=len(df), lookback_hours=lookback_hours)
        return df
    except Exception as e:
        log.warning("dashboard_history_load_failed", error=str(e))
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
    """Render the main dashboard content with tab structure."""
    from gridpace.ui.components.iso_cards import render_iso_cards

    st.title("Grid Intelligence Dashboard")
    st.caption("Real-time ISO grid conditions — data refreshes every 2 hours")

    st.divider()

    # Load data
    df = load_iso_summary()

    # Tab structure
    tab1, tab2, tab3, tab4 = st.tabs([
        "Live Conditions",
        "Price Analytics",
        "Nodal Analysis",
        "Correlations",
    ])

    with tab1:
        st.subheader("Current LMP by ISO")
        anomaly_results = load_anomaly_results()
        render_iso_cards(df, anomaly_results)

    with tab2:
        st.subheader("Price Distribution Analytics")
        st.info("Coming soon — histogram, CDF, box plots, and price spread per ISO.")

    with tab3:
        st.subheader("Nodal Price Analysis")
        st.info("Coming soon — key node prices per ISO (ERCOT hubs, CAISO zones, PJM hubs).")

    with tab4:
        st.subheader("Cross-Variable Correlations")
        st.info("Coming soon — weather vs LMP, renewable vs price, correlation matrix.")


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
