"""
Data availability and quality health checks for GridPace.
Covers last ingest time, row counts per layer, and data gap detection.

All functions return HealthResult dicts — see monitoring/health.py for structure.
Thresholds configured in config/settings.yml under health:
    data_gap_warning_minutes — warn if no new data within this window
    data_gap_error_minutes   — error if no new data within this window
"""

from datetime import UTC, datetime

from gridpace.config import app_config
from gridpace.monitoring.logger import get_logger
from gridpace.monitoring.types import HealthResult, make_result

log = get_logger(__name__)

# Thresholds loaded from config — never hardcode here
_health_cfg = app_config.get("health", {})
GAP_WARNING_MINUTES = _health_cfg.get("data_gap_warning_minutes", 15)
GAP_ERROR_MINUTES = _health_cfg.get("data_gap_error_minutes", 60)


def check_last_ingest() -> HealthResult:
    """
    Check when bronze layer was last written to.
    Uses poll_interval_minutes to determine if data is stale.
    """
    try:
        from gridpace.grid.storage import get_last_ingested_at
        last = get_last_ingested_at("lmp")

        if last is None:
            return make_result(
                status="warning",
                message="No data ingested yet — run the pipeline",
                value=None,
            )

        now = datetime.now(UTC)
        gap_minutes = round((now - last).total_seconds() / 60, 1)

        if gap_minutes >= GAP_ERROR_MINUTES:
            status = "error"
            message = f"No new data for {gap_minutes} minutes"
        elif gap_minutes >= GAP_WARNING_MINUTES:
            status = "warning"
            message = f"No new data for {gap_minutes} minutes"
        else:
            status = "ok"
            message = f"Last ingest {gap_minutes} minutes ago"

        log.info("last_ingest_checked", gap_minutes=gap_minutes)
        return make_result(
            status=status,
            message=message,
            value=gap_minutes,
            details={"last_ingested_at": str(last)},
        )
    except Exception as e:
        log.warning("last_ingest_check_failed", error=str(e))
        return make_result(
            status="error",
            message=f"Last ingest check failed: {e}",
            value=None,
        )


def check_row_counts() -> HealthResult:
    """
    Check row counts across bronze, silver, and gold layers.
    Returns warning if any layer is empty.
    """
    try:
        from gridpace.grid.storage import get_connection
        conn = get_connection()

        counts = {
            "bronze_lmp": conn.execute("SELECT COUNT(*) FROM bronze.lmp").fetchone()[0],
            "bronze_fuel_mix": conn.execute("SELECT COUNT(*) FROM bronze.fuel_mix").fetchone()[0],
            "silver_lmp": conn.execute("SELECT COUNT(*) FROM silver.lmp").fetchone()[0],
            "silver_fuel_mix": conn.execute("SELECT COUNT(*) FROM silver.fuel_mix").fetchone()[0],
            "gold_iso_summary": conn.execute("SELECT COUNT(*) FROM gold.iso_summary").fetchone()[0],
        }
        conn.close()

        empty_layers = [k for k, v in counts.items() if v == 0]

        if empty_layers:
            return make_result(
                status="warning",
                message=f"Empty layers: {', '.join(empty_layers)}",
                value=counts,
                details={"empty": empty_layers},
            )

        return make_result(
            status="ok",
            message=f"All layers populated — gold: {counts['gold_iso_summary']} rows",
            value=counts,
        )
    except Exception as e:
        log.warning("row_counts_check_failed", error=str(e))
        return make_result(
            status="error",
            message=f"Row count check failed: {e}",
            value=None,
        )


def check_data_gap() -> HealthResult:
    """
    Check for unexpected gaps in data collection.
    Compares expected vs actual poll intervals in gold layer.
    """
    try:
        from gridpace.grid.storage import get_connection
        poll_minutes = app_config["ingestion"]["poll_interval_minutes"]
        conn = get_connection()

        result = conn.execute("""
            SELECT
                iso,
                COUNT(*) as rows,
                MIN(window_start) as earliest,
                MAX(window_start) as latest,
                ROUND(
                    (EXTRACT(EPOCH FROM (MAX(window_start) - MIN(window_start))) / 60)
                    / NULLIF(COUNT(*) - 1, 0)
                , 1) as avg_interval_minutes
            FROM gold.iso_summary
            GROUP BY iso
            ORDER BY iso
        """).df()
        conn.close()

        if result.empty:
            return make_result(
                status="warning",
                message="No gold data available for gap analysis",
                value=None,
            )

        gaps = []
        for _, row in result.iterrows():
            if row["avg_interval_minutes"] and row["avg_interval_minutes"] > poll_minutes * 2:
                gaps.append(f"{row['iso']}: avg {row['avg_interval_minutes']}min intervals")

        if gaps:
            return make_result(
                status="warning",
                message=f"{len(gaps)} ISO(s) with gaps",
                value=result.to_dict(orient="records"),
                details={"gaps": gaps},
            )

        return make_result(
            status="ok",
            message="No significant data gaps detected",
            value=result.to_dict(orient="records"),
        )
    except Exception as e:
        log.warning("data_gap_check_failed", error=str(e))
        return make_result(
            status="error",
            message=f"Data gap check failed: {e}",
            value=None,
        )
