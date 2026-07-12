"""
Health tab component for GridPace dashboard.
Shows detailed system health across six monitoring domains:
    1. Data Freshness
    2. Data Quality
    3. Storage
    4. Pipeline Health
    5. System
    6. ISO Coverage
"""

from pathlib import Path

import pandas as pd
import streamlit as st

from gridpace.config import ROOT, app_config
from gridpace.monitoring.logger import get_logger

log = get_logger(__name__)


def _status_icon(status: str) -> str:
    return {"ok": "✅", "warning": "⚠️", "error": "❌"}.get(status, "⚪")


def render_health_tab() -> None:
    """Render the full health dashboard tab."""
    from gridpace.grid.storage import DB_PATH, get_layer_sizes
    from gridpace.monitoring.health import get_health_summary

    try:
        summary = get_health_summary()
    except Exception as e:
        st.error(f"Health checks unavailable: {e}")
        return

    storage_cfg = app_config.get("storage", {})

    # ── 1. Data Freshness ──────────────────────────────────────────
    st.subheader("1. Data Freshness")
    col1, col2 = st.columns(2)
    with col1:
        last_ingest = summary.get("last_ingest", {})
        icon = _status_icon(last_ingest.get("status", "grey"))
        st.metric(
            label=f"{icon} Last Ingest",
            value=f"{last_ingest.get('value', 'N/A')} min ago"
            if last_ingest.get("value") is not None else "No data",
        )
    with col2:
        poll_minutes = app_config["ingestion"]["poll_interval_minutes"]
        st.metric(label="Poll Interval", value=f"{poll_minutes} min")

    details = last_ingest.get("details", {})
    if details.get("last_ingested_at"):
        st.caption(f"Last ingested at: {details['last_ingested_at']}")

    st.divider()

    # ── 2. Data Quality ────────────────────────────────────────────
    st.subheader("2. Data Quality")
    data_gap = summary.get("data_gap", {})
    row_counts = summary.get("row_counts", {})

    icon = _status_icon(data_gap.get("status", "grey"))
    st.write(f"{icon} **Gap Detection:** {data_gap.get('message', 'N/A')}")

    gap_details = data_gap.get("details", {})
    if gap_details.get("gaps"):
        for gap in gap_details["gaps"]:
            st.caption(f"  • {gap}")

    # Row counts table
    if row_counts.get("value"):
        counts = row_counts["value"]
        counts_df = pd.DataFrame([
            {"Layer": k, "Rows": v}
            for k, v in counts.items()
        ])
        st.dataframe(counts_df, hide_index=True, use_container_width=True)

    st.divider()

    # ── 3. Storage ─────────────────────────────────────────────────
    st.subheader("3. Storage")
    try:
        db_path = Path(DB_PATH)
        db_size_mb = round(db_path.stat().st_size / 1024 / 1024, 1)
        db_size_gb = round(db_path.stat().st_size / 1024 / 1024 / 1024, 4)
        bronze_cap_gb = storage_cfg.get("bronze_cap_gb", 5.0)
        bronze_warning_gb = storage_cfg.get("bronze_warning_gb", 4.0)

        st.metric(label="Total DB Size", value=f"{db_size_mb}MB")

        # Progress bar toward bronze cap
        progress = min(db_size_gb / bronze_cap_gb, 1.0)
        st.caption(f"DB size toward {bronze_cap_gb}GB cap:")
        st.progress(progress)

        if db_size_gb >= bronze_warning_gb:
            st.warning(f"Approaching {bronze_cap_gb}GB cap — consider running make backfill")

        # Layer row counts
        sizes = get_layer_sizes()
        size_data = []
        for layer, info in sizes.items():
            size_data.append({
                "Layer": layer,
                "Rows": info.get("rows", 0),
            })
        st.dataframe(pd.DataFrame(size_data), hide_index=True, use_container_width=True)

        # Archive history
        st.caption("**Archive History:**")
        archive_dir = ROOT / storage_cfg.get("archive_dir", "data/archive") / "bronze"
        parquet_files = sorted(archive_dir.glob("*.parquet"), reverse=True)
        if parquet_files:
            for f in parquet_files[:10]:
                size_mb = round(f.stat().st_size / 1024 / 1024, 1)
                st.caption(f"  • {f.name} ({size_mb}MB)")
        else:
            st.caption("  No archived files yet.")

    except Exception as e:
        st.error(f"Storage check failed: {e}")

    st.divider()

    # ── 4. Pipeline Health ─────────────────────────────────────────
    st.subheader("4. Pipeline Health")
    st.caption("Prefect .serve() not yet running — pipeline executes manually.")
    st.code("uv run python -m gridpace.grid.flows")

    st.divider()

    # ── 5. System ──────────────────────────────────────────────────
    st.subheader("5. System")
    db_conn = summary.get("db_connectivity", {})
    migrations = summary.get("migrations", {})
    db_size_check = summary.get("db_size", {})

    checks = [
        ("DB Connectivity", db_conn),
        ("Migrations", migrations),
        ("DB Size", db_size_check),
    ]
    for label, check in checks:
        icon = _status_icon(check.get("status", "grey"))
        st.write(f"{icon} **{label}:** {check.get('message', 'N/A')}")

    st.divider()

    # ── 6. ISO Coverage ────────────────────────────────────────────
    st.subheader("6. ISO Coverage")
    import os

    from gridpace.grid.clients.gridstatus import ISO_CLASSES

    all_isos = list(ISO_CLASSES.keys())
    configured_isos = app_config.get("isos", [])

    iso_data = []
    for iso in all_isos:
        if iso == "PJM":
            has_key = bool(os.getenv("PJM_API_KEY"))
            status = "✅ Active" if has_key else "⚠️ No API key"
        else:
            status = "✅ Active" if iso in configured_isos else "⬜ Not configured"
        iso_data.append({"ISO": iso, "Status": status})

    st.dataframe(pd.DataFrame(iso_data), hide_index=True, use_container_width=True)
