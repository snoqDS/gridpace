"""
GridPace Dashboard — Real-time grid intelligence.
Reads from DuckDB gold layer. Run with: make run
"""

import pandas as pd
import streamlit as st

from gridpace.config import app_config
from gridpace.grid.storage import get_connection
from gridpace.intelligence.detection.anomaly import detect_anomalies
from gridpace.monitoring.logger import get_logger
from gridpace.ui.components.iso_cards import render_iso_cards
from gridpace.ui.components.price_charts import (
    render_generation_mix_timeseries,
    render_lmp_boxplot,
    render_lmp_cdf,
    render_lmp_histogram,
    render_price_spread,
)

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
    Load full gold ISO summary history for price analytics.
    Returns all available history — not limited to lookback window.
    Used for histogram, CDF, box plots, and spread charts.
    Returns None if no data exists.
    """
    try:
        conn = get_connection()
        df = conn.execute("""
            SELECT iso, window_start, avg_lmp
            FROM gold.iso_summary
            ORDER BY iso, window_start
        """).df()
        conn.close()
        log.info("dashboard_history_loaded", rows=len(df))
        return df
    except Exception as e:
        log.warning("dashboard_history_load_failed", error=str(e))
        return None


@st.cache_data(ttl=app_config["dashboard"]["cache_ttl_seconds"])
def load_iso_summary_history():
    """
    Load full gold ISO summary history including fuel mix columns.
    Returns all available history for generation mix time series chart.
    Returns None if no data exists.
    """
    try:
        conn = get_connection()
        df = conn.execute("""
            SELECT
                iso, window_start, window_end,
                avg_lmp, renewable_pct,
                natural_gas, wind, solar, coal, nuclear, other
            FROM gold.iso_summary
            ORDER BY iso, window_start
        """).df()
        conn.close()
        log.info("dashboard_summary_history_loaded", rows=len(df))
        return df
    except Exception as e:
        log.warning("dashboard_summary_history_load_failed", error=str(e))
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

        st.divider()

        st.subheader("System Health")
        try:
            from gridpace.monitoring.health import get_health_summary
            summary = get_health_summary()

            status_colors = {
                "ok": "✅",
                "warning": "⚠️",
                "error": "❌",
            }
            for check, result in summary.items():
                emoji = status_colors.get(result["status"], "⚪")
                st.caption(f"{emoji} {check.replace('_', ' ').title()}: {result['message']}")
                if result.get("details") and result["status"] != "ok":
                    for _key, val in result["details"].items():
                        if isinstance(val, list):
                            for item in val:
                                st.caption(f"　　• {item}")
        except Exception as e:
            st.caption(f"⚪ Health checks unavailable: {e}")


def render_main():
    """Render the main dashboard content with tab structure."""
    st.title("Grid Intelligence Dashboard")
    poll_minutes = app_config["ingestion"]["poll_interval_minutes"]
    st.caption(f"Real-time ISO grid conditions — data refreshes every {poll_minutes} minutes")

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
        history_df = load_iso_history()
        gen_history = load_iso_summary_history()

        if history_df is None or history_df.empty:
            st.info("No price history available. Run the pipeline or seed the database first.")
            st.code("make seed")
        else:
            # Date range slider
            min_date = history_df["window_start"].min().to_pydatetime()
            max_date = history_df["window_start"].max().to_pydatetime()

            selected_range = st.slider(
                "Filter all charts by date range (UTC)",
                min_value=min_date,
                max_value=max_date,
                value=(min_date, max_date),
                format="MM/DD/YY HH:mm",
            )

            # Convert slider values to UTC-aware for comparison
            start = pd.Timestamp(selected_range[0])
            end = pd.Timestamp(selected_range[1])
            if start.tzinfo is None:
                start = start.tz_localize("UTC")
            else:
                start = start.tz_convert("UTC")
            if end.tzinfo is None:
                end = end.tz_localize("UTC")
            else:
                end = end.tz_convert("UTC")

            mask = (
                (history_df["window_start"] >= start) &
                (history_df["window_start"] <= end)
            )
            filtered_history = history_df[mask]

            if gen_history is not None:
                gen_mask = (
                    (gen_history["window_start"] >= start) &
                    (gen_history["window_start"] <= end)
                )
                filtered_gen = gen_history[gen_mask]
            else:
                filtered_gen = None

            st.caption(
                f"Showing {len(filtered_history) // len(history_df['iso'].unique())} hours per ISO"
            )

            st.divider()

            st.subheader("Price Distribution")
            col1, col2 = st.columns(2)
            with col1:
                render_lmp_histogram(filtered_history)
            with col2:
                render_lmp_cdf(filtered_history)

            st.divider()

            col3, col4 = st.columns(2)
            with col3:
                render_lmp_boxplot(filtered_history)
            with col4:
                render_price_spread(filtered_history)

            st.divider()

            st.subheader("Generation Mix Over Time")
            render_generation_mix_timeseries(filtered_gen)

    with tab3:
        st.subheader("Nodal Price Analysis")
        st.info("Coming soon — key node prices per ISO (ERCOT hubs, CAISO zones, PJM hubs).")

    with tab4:
        st.subheader("Cross-Variable Correlations")
        st.info("Coming soon — weather vs LMP, renewable vs price, correlation matrix.")


def render_footer():
    """Render the GridStatus attribution footer per ToS Section 4.4."""
    st.divider()
    poll_minutes = app_config["ingestion"]["poll_interval_minutes"]
    st.caption(
        f"Powered by [Grid Status](https://www.gridstatus.io/) | "
        f"Data refreshes every {poll_minutes} minutes | "
        "GridPace is open source under Apache 2.0"
    )

def main():
    """Main dashboard entrypoint."""
    render_sidebar()
    render_main()
    render_footer()


if __name__ == "__main__":
    main()
