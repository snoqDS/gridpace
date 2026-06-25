"""
DuckDB storage layer for GridPace.
Implements bronze/silver/gold medallion architecture.

Schema managed via src/gridpace/grid/migrator.py.
Run migrations before using storage functions:
    from gridpace.grid.migrator import run_migrations
    run_migrations()
"""

import json
from datetime import UTC, datetime

import duckdb
import pandas as pd

from gridpace.config import ROOT, app_config
from gridpace.monitoring.logger import get_logger

log = get_logger(__name__)

DB_PATH = ROOT / "data" / "gridpace.duckdb"


def get_connection() -> duckdb.DuckDBPyConnection:
    """Return a connection to the GridPace DuckDB database."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    return duckdb.connect(str(DB_PATH))


def _coalesce(row, *keys):
    """Return first non-None value from row for given keys.
    Handles zero values correctly — unlike 'or' chaining which treats 0 as falsy.
    """
    for key in keys:
        val = row.get(key)
        if val is not None:
            return val
    return None


def write_bronze_lmp(df: pd.DataFrame, iso: str) -> int:
    """
    Write raw LMP data to bronze layer.
    Stores original data plus raw_json for audit trail.
    Returns number of rows written.
    """
    conn = get_connection()
    rows_written = 0

    for _, row in df.iterrows():
        conn.execute("""
            INSERT INTO bronze.lmp (
                iso, interval_start, interval_end,
                location, location_type, lmp, market, raw_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, [
            iso,
            _coalesce(row, "Interval Start", "time", "interval_start"),
            _coalesce(row, "Interval End", "interval_end"),
            _coalesce(row, "Location", "location"),
            _coalesce(row, "Location Type", "location_type"),
            _coalesce(row, "LMP", "lmp"),
            _coalesce(row, "Market", "market"),
            json.dumps(row.to_dict(), default=str),
        ])
        rows_written += 1

    conn.close()
    return rows_written


def write_bronze_fuel_mix(df: pd.DataFrame, iso: str) -> int:
    """
    Write raw fuel mix data to bronze layer.
    Returns number of rows written.
    """
    conn = get_connection()
    rows_written = 0

    for _, row in df.iterrows():
        conn.execute("""
            INSERT INTO bronze.fuel_mix (
                iso, time, natural_gas, wind, solar,
                coal, nuclear, other, raw_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, [
            iso,
            _coalesce(row, "Time", "time"),
            _coalesce(row, "Natural Gas", "natural_gas") or 0.0,
            _coalesce(row, "Wind", "wind") or 0.0,
            _coalesce(row, "Solar", "solar") or 0.0,
            _coalesce(row, "Coal", "coal") or 0.0,
            _coalesce(row, "Nuclear", "nuclear") or 0.0,
            _coalesce(row, "Other", "other") or 0.0,
            json.dumps(row.to_dict(), default=str),
        ])
        rows_written += 1

    conn.close()
    return rows_written


def transform_to_silver_lmp() -> int:
    """
    Transform bronze LMP to silver.
    Applies GridStatus transformer then validates against contract.
    Returns number of rows written to silver.
    """
    from gridpace.grid.transformers.gridstatus import transform_lmp
    from gridpace.grid.validation import validate_dataframe

    conn = get_connection()
    raw = conn.execute("SELECT * FROM bronze.lmp").df()

    if raw.empty:
        conn.close()
        return 0

    normalized_frames = []
    for iso in raw["iso"].unique():
        iso_df = raw[raw["iso"] == iso].copy()
        transformed = transform_lmp(iso_df, iso)
        result = validate_dataframe(transformed, "gridstatus", "lmp")
        if not result["valid"]:
            log.warning("lmp_validation_failed", iso=iso, errors=result["errors"])
            continue
        normalized_frames.append(transformed)

    if not normalized_frames:
        conn.close()
        return 0

    combined = pd.concat(normalized_frames, ignore_index=True)
    conn.register("combined", combined)

    conn.execute("""
        INSERT INTO silver.lmp (
            iso, interval_start, location, location_type, lmp, market
        )
        SELECT DISTINCT
            iso,
            interval_start,
            location,
            location_type,
            lmp,
            market
        FROM combined
        WHERE lmp IS NOT NULL
        AND interval_start IS NOT NULL
        AND (iso, interval_start, COALESCE(location, '')) NOT IN (
            SELECT iso, interval_start, COALESCE(location, '') FROM silver.lmp
        )
    """)

    rows = conn.execute("SELECT COUNT(*) FROM silver.lmp").fetchone()[0]
    conn.close()
    return rows


def transform_to_silver_fuel_mix() -> int:
    """
    Transform bronze fuel mix to silver.
    Applies GridStatus transformer then validates against contract.
    Returns number of rows written to silver.
    """
    from gridpace.grid.transformers.gridstatus import transform_fuel_mix
    from gridpace.grid.validation import validate_dataframe

    conn = get_connection()
    raw = conn.execute("SELECT * FROM bronze.fuel_mix").df()

    if raw.empty:
        conn.close()
        return 0

    normalized_frames = []
    for iso in raw["iso"].unique():
        iso_df = raw[raw["iso"] == iso].copy()
        transformed = transform_fuel_mix(iso_df, iso)
        result = validate_dataframe(transformed, "gridstatus", "fuel_mix")
        if not result["valid"]:
            log.warning("fuel_mix_validation_failed", iso=iso, errors=result["errors"])
            continue
        normalized_frames.append(transformed)

    if not normalized_frames:
        conn.close()
        return 0

    combined = pd.concat(normalized_frames, ignore_index=True)
    conn.register("combined", combined)

    conn.execute("""
        INSERT INTO silver.fuel_mix (
            iso, time, natural_gas, wind, solar,
            coal, nuclear, other, renewable_pct
        )
        SELECT DISTINCT
            iso,
            time,
            natural_gas,
            wind,
            solar,
            coal,
            nuclear,
            other,
            renewable_pct
        FROM combined
        WHERE time IS NOT NULL
        AND (iso, time) NOT IN (
            SELECT iso, time FROM silver.fuel_mix
        )
    """)

    rows = conn.execute("SELECT COUNT(*) FROM silver.fuel_mix").fetchone()[0]
    conn.close()
    return rows


def compute_gold_iso_summary() -> int:
    """
    Compute gold ISO summary metrics from silver data.
    Aggregates LMP and renewable_pct per ISO per hour.
    Returns number of rows written.
    """
    conn = get_connection()

    conn.execute("""
            INSERT INTO gold.iso_summary (
                iso, window_start, window_end,
                avg_lmp, max_lmp, min_lmp, renewable_pct,
                natural_gas, wind, solar, coal, nuclear, other
            )
            SELECT
                l.iso,
                date_trunc('hour', l.interval_start) AS window_start,
                date_trunc('hour', l.interval_start) + INTERVAL '1 hour' AS window_end,
                ROUND(AVG(l.lmp), 2) AS avg_lmp,
                ROUND(MAX(l.lmp), 2) AS max_lmp,
                ROUND(MIN(l.lmp), 2) AS min_lmp,
                ROUND(AVG(f.renewable_pct), 2) AS renewable_pct,
                ROUND(AVG(f.natural_gas), 2) AS natural_gas,
                ROUND(AVG(f.wind), 2) AS wind,
                ROUND(AVG(f.solar), 2) AS solar,
                ROUND(AVG(f.coal), 2) AS coal,
                ROUND(AVG(f.nuclear), 2) AS nuclear,
                ROUND(AVG(f.other), 2) AS other
            FROM silver.lmp l
            LEFT JOIN silver.fuel_mix f
                ON l.iso = f.iso
                AND date_trunc('hour', l.interval_start) = date_trunc('hour', f.time)
            WHERE (l.iso, date_trunc('hour', l.interval_start)) NOT IN (
                SELECT iso, window_start FROM gold.iso_summary
            )
            GROUP BY l.iso, date_trunc('hour', l.interval_start)
        """)

    rows = conn.execute("SELECT COUNT(*) FROM gold.iso_summary").fetchone()[0]
    conn.close()
    return rows


def apply_retention_policy() -> int:
    """
    Delete bronze data older than retention window.
    Retention period configured in config/settings.yml.
    Returns number of rows deleted.
    """
    conn = get_connection()

    try:
        retention_days = app_config["retention"]["bronze_days"]
    except KeyError:
        log.warning("retention_config_missing", default_days=90)
        retention_days = 90

    result = conn.execute(f"""
        DELETE FROM bronze.lmp
        WHERE ingested_at < now() - INTERVAL '{retention_days} days'
    """)
    lmp_deleted = max(0, result.rowcount) if result.rowcount else 0

    result = conn.execute(f"""
        DELETE FROM bronze.fuel_mix
        WHERE ingested_at < now() - INTERVAL '{retention_days} days'
    """)
    fuel_deleted = max(0, result.rowcount) if result.rowcount else 0

    conn.close()
    total = lmp_deleted + fuel_deleted
    return total


def get_last_ingested_at(table: str = "lmp") -> str | None:
    """
    Return the most recent ingested_at timestamp from bronze.
    Bronze is checked because it is the first landing zone for raw data.
    Gaps in bronze propagate to silver and gold automatically.
    Returns None if no data exists yet.

    Args:
        table: 'lmp' or 'fuel_mix'
    """
    conn = get_connection()

    try:
        result = conn.execute(f"""
            SELECT MAX(ingested_at)
            FROM bronze.{table}
        """).fetchone()[0]
        conn.close()
        return result
    except Exception as e:
        log.warning("last_ingested_query_failed", table=table, error=str(e))
        conn.close()
        return None


def check_data_gap(table: str = "lmp") -> dict:
    """
    Check if there is a gap in data collection.
    Compares last ingested_at to current time vs poll interval.
    Returns dict with gap info for logging.
    """
    poll_minutes = app_config["ingestion"]["poll_interval_minutes"]
    last = get_last_ingested_at(table)
    now = datetime.now(UTC)

    if last is None:
        return {
            "has_gap": False,
            "last_ingested_at": None,
            "gap_minutes": None,
            "message": "No data in database yet — first run."
        }

    gap_minutes = (now - last).total_seconds() / 60
    expected_intervals = int(gap_minutes / poll_minutes)
    has_gap = expected_intervals > 1

    result = {
        "has_gap": has_gap,
        "last_ingested_at": last,
        "gap_minutes": round(gap_minutes, 1),
        "missed_intervals": max(0, expected_intervals - 1),
        "message": (
            f"Gap detected: {expected_intervals - 1} missed intervals ({round(gap_minutes, 1)} minutes)"
            if has_gap else
            f"No gap detected. Last ingested {round(gap_minutes, 1)} minutes ago."
        )
    }

    log.info("data_gap_check", **result)

    return result
