"""
Backfill script for GridPace.
Handles two backfill scenarios:

1. Gold NULL column backfill: after adding new columns via migration,
   populate NULL values in existing gold rows from silver data.
   Run after any migration that adds columns to gold.iso_summary.

2. Historical data backfill: fetch real historical LMP and fuel mix
   data from gridstatus for a specified date range.
   Used to seed the database with real data instead of synthetic.

Usage:
    uv run python scripts/backfill_events.py --gold     # backfill gold NULLs
    uv run python scripts/backfill_events.py --history  # fetch real historical data
    uv run python scripts/backfill_events.py --all      # both

WARNING: --history makes live API calls to ISO portals.
         Set dry_run: false in config/settings.yml first.
         For 30 days x 9 ISOs expect significant data volume.
"""

import sys
import argparse
from pathlib import Path
from datetime import datetime, timedelta, UTC

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from gridpace.config import app_config
from gridpace.monitoring.logger import get_logger

log = get_logger(__name__)


def backfill_gold_nulls() -> None:
    """
    Backfill NULL columns in gold.iso_summary from silver data.
    Run after any migration that adds new columns to gold layer.
    Safe to run multiple times — only updates NULL rows.
    """
    from gridpace.grid.storage import get_connection

    print("Backfilling gold NULL columns from silver data...")
    conn = get_connection()

    try:
        # Check which gold rows have NULL fuel mix columns
        null_count = conn.execute("""
            SELECT COUNT(*) FROM gold.iso_summary
            WHERE natural_gas IS NULL
            OR wind IS NULL
            OR solar IS NULL
        """).fetchone()[0]

        if null_count == 0:
            print("No NULL columns found in gold layer — nothing to backfill.")
            conn.close()
            return

        print(f"Found {null_count} gold rows with NULL fuel mix columns.")

        # Update gold rows with fuel mix data from silver
        conn.execute("""
            UPDATE gold.iso_summary g
            SET
                natural_gas = (
                    SELECT ROUND(AVG(f.natural_gas), 2)
                    FROM silver.fuel_mix f
                    WHERE f.iso = g.iso
                    AND date_trunc('hour', f.time) = g.window_start
                ),
                wind = (
                    SELECT ROUND(AVG(f.wind), 2)
                    FROM silver.fuel_mix f
                    WHERE f.iso = g.iso
                    AND date_trunc('hour', f.time) = g.window_start
                ),
                solar = (
                    SELECT ROUND(AVG(f.solar), 2)
                    FROM silver.fuel_mix f
                    WHERE f.iso = g.iso
                    AND date_trunc('hour', f.time) = g.window_start
                ),
                coal = (
                    SELECT ROUND(AVG(f.coal), 2)
                    FROM silver.fuel_mix f
                    WHERE f.iso = g.iso
                    AND date_trunc('hour', f.time) = g.window_start
                ),
                nuclear = (
                    SELECT ROUND(AVG(f.nuclear), 2)
                    FROM silver.fuel_mix f
                    WHERE f.iso = g.iso
                    AND date_trunc('hour', f.time) = g.window_start
                ),
                other = (
                    SELECT ROUND(AVG(f.other), 2)
                    FROM silver.fuel_mix f
                    WHERE f.iso = g.iso
                    AND date_trunc('hour', f.time) = g.window_start
                ),
                renewable_pct = (
                    SELECT ROUND(AVG(f.renewable_pct), 2)
                    FROM silver.fuel_mix f
                    WHERE f.iso = g.iso
                    AND date_trunc('hour', f.time) = g.window_start
                )
            WHERE natural_gas IS NULL
        """)

        updated = conn.execute("""
            SELECT COUNT(*) FROM gold.iso_summary
            WHERE natural_gas IS NOT NULL
        """).fetchone()[0]

        print(f"Backfill complete. {updated} gold rows now have fuel mix data.")
        log.info("gold_backfill_complete", updated_rows=updated)

    except Exception as e:
        print(f"Error during gold backfill: {e}")
        log.warning("gold_backfill_failed", error=str(e))
    finally:
        conn.close()


def backfill_historical(days: int = 30) -> None:
    """
    Fetch real historical LMP and fuel mix data from gridstatus.
    Populates bronze, silver, and gold layers with real data.

    Args:
        days: number of days of history to fetch (default 30)

    WARNING: Makes live API calls. Set dry_run: false in config first.
    """
    from gridpace.grid.clients.gridstatus import ISO_CLASSES
    from gridpace.grid.storage import (
        write_bronze_lmp,
        write_bronze_fuel_mix,
        transform_to_silver_lmp,
        transform_to_silver_fuel_mix,
        compute_gold_iso_summary,
    )
    from gridpace.grid.migrator import run_migrations

    dry_run = app_config["ingestion"]["dry_run"]
    if dry_run:
        print("ERROR: dry_run is True in config/settings.yml.")
        print("Set dry_run: false before running historical backfill.")
        return

    run_migrations()

    isos = app_config["isos"]
    end_date = datetime.now(UTC).date()
    start_date = end_date - timedelta(days=days)

    print(f"Fetching {days} days of real data: {start_date} to {end_date}")
    print(f"ISOs: {isos}")
    print("This may take several minutes...")

    for iso_name in isos:
        if iso_name not in ISO_CLASSES:
            print(f"  {iso_name}: skipped — not in ISO_CLASSES")
            continue

        print(f"\n  Fetching {iso_name}...")
        try:
            iso_class, kwargs = ISO_CLASSES[iso_name]

            if iso_name == "PJM" and not kwargs.get("api_key"):
                print(f"  {iso_name}: skipped — PJM_API_KEY not set")
                continue

            iso = iso_class(**kwargs)

            # Fetch LMP history
            print(f"    LMP {start_date} to {end_date}...")
            lmp_df = iso.get_lmp(date=str(start_date), end=str(end_date))
            rows = write_bronze_lmp(lmp_df, iso_name)
            print(f"    LMP: {rows} rows written to bronze")
            log.info("historical_lmp_fetched", iso=iso_name, rows=rows)

            # Fetch fuel mix history
            print(f"    Fuel mix {start_date} to {end_date}...")
            fuel_df = iso.get_fuel_mix(date=str(start_date), end=str(end_date))
            rows = write_bronze_fuel_mix(fuel_df, iso_name)
            print(f"    Fuel mix: {rows} rows written to bronze")
            log.info("historical_fuel_mix_fetched", iso=iso_name, rows=rows)

        except Exception as e:
            print(f"  {iso_name}: FAILED — {e}")
            log.warning("historical_fetch_failed", iso=iso_name, error=str(e))

    print("\nTransforming to silver...")
    transform_to_silver_lmp()
    transform_to_silver_fuel_mix()

    print("Computing gold aggregations...")
    gold_rows = compute_gold_iso_summary()
    print(f"Done. {gold_rows} gold rows computed.")
    log.info("historical_backfill_complete", gold_rows=gold_rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="GridPace backfill script")
    parser.add_argument("--gold", action="store_true", help="Backfill gold NULL columns from silver")
    parser.add_argument("--history", action="store_true", help="Fetch real historical data from gridstatus")
    parser.add_argument("--days", type=int, default=30, help="Days of history to fetch (default 30)")
    parser.add_argument("--all", action="store_true", dest="all_flags", help="Run all backfill operations")
    args = parser.parse_args()

    if not any([args.gold, args.history, args.all_flags]):
        parser.print_help()
        return

    if args.gold or args.all_flags:
        backfill_gold_nulls()

    if args.history or args.all_flags:
        backfill_historical(days=args.days)


if __name__ == "__main__":
    main()
