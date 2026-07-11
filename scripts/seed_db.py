"""
Seed script for GridPace development database.
Generates realistic fake historical data for testing and development.

Usage:
    uv run python scripts/seed_db.py

This populates DuckDB with N hours of synthetic LMP and fuel mix data
per ISO, enabling anomaly detection baselines and dashboard testing
without consuming GridStatus API quota.

Safe to run multiple times — checks for existing data before inserting.

WARNING: --force wipes ALL data across bronze, silver, and gold layers.
Use with care. Safe for development only.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import numpy as np
import pandas as pd

from gridpace.config import app_config
from gridpace.grid.migrator import run_migrations
from gridpace.grid.storage import (
    compute_gold_iso_summary,
    get_connection,
    transform_to_silver_fuel_mix,
    transform_to_silver_lmp,
    write_bronze_fuel_mix,
    write_bronze_lmp,
)
from gridpace.monitoring.logger import get_logger

log = get_logger(__name__)

# Load seed parameters from config
_seed_cfg = app_config.get("seed", {})
ISO_LMP_PARAMS = _seed_cfg.get("lmp_params", {})
ISO_FUEL_MIX = _seed_cfg.get("fuel_mix", {})


def check_existing_data() -> int:
    """Return number of existing bronze LMP rows."""
    try:
        conn = get_connection()
        count = conn.execute("SELECT COUNT(*) FROM bronze.lmp").fetchone()[0]
        conn.close()
        return count
    except Exception:
        return 0


def generate_lmp_df(iso: str, hours: int, end_time: pd.Timestamp) -> pd.DataFrame:
    """
    Generate synthetic LMP data using raw API column names.
    Mimics GridStatus API output — transformer handles normalization.
    Price distribution driven by config/settings.yml seed.lmp_params.
    """
    params = ISO_LMP_PARAMS[iso]
    timestamps = pd.date_range(end=end_time, periods=hours, freq="h", tz="UTC")

    np.random.seed(42)
    base_prices = np.random.normal(params["mean"], params["std"], hours)
    hour_of_day = timestamps.hour
    peak_multiplier = np.where((hour_of_day >= 7) & (hour_of_day <= 22), 1.2, 0.85)
    prices = np.clip(base_prices * peak_multiplier, 5.0, 200.0)

    return pd.DataFrame({
        "time": timestamps,           # transformer maps this to interval_start
        "iso": iso,
        "lmp": prices.round(2),
        "energy": (prices * 0.95).round(2),
        "congestion": (prices * 0.05).round(2),
        "Market": "SYNTHETIC",        # preserved through transformer as market field
    })


def generate_fuel_mix_df(iso: str, hours: int, end_time: pd.Timestamp) -> pd.DataFrame:
    """
    Generate synthetic fuel mix data using raw API column names.
    Mimics GridStatus API output — transformer computes renewable_pct.
    Fuel mix distribution driven by config/settings.yml seed.fuel_mix.
    """
    mix = ISO_FUEL_MIX[iso]
    timestamps = pd.date_range(end=end_time, periods=hours, freq="h", tz="UTC")

    np.random.seed(42)
    rows = []
    for ts in timestamps:
        row = {"time": ts, "iso": iso}
        for fuel, base_pct in mix.items():
            row[fuel] = round(max(0.0, base_pct + np.random.normal(0, 2)), 2)
        row["other"] = 0.0
        rows.append(row)

    return pd.DataFrame(rows)


def seed_database(hours: int = None, force: bool = False) -> None:
    """
    Seed the database with synthetic historical data.

    Args:
        hours: number of hours of history to generate (default from config)
        force: if True, wipe all existing data and reseed from scratch.
               Without force, skips seeding if data already exists.
    """
    log.info("seed_started", hours=hours)
    if hours is None:
        hours = app_config.get("seed", {}).get("default_hours", 48)

    # Run migrations first
    run_migrations()

    # Check existing data
    existing = check_existing_data()
    if existing > 0 and not force:
        log.info("seed_skipped", reason="data already exists", existing_rows=existing)
        print(f"Database already has {existing} rows. Use --force to wipe and reseed.")
        return

    if existing > 0 and force:
        print("Wiping existing data...")
        conn = get_connection()
        conn.execute("DELETE FROM bronze.lmp")
        conn.execute("DELETE FROM bronze.fuel_mix")
        conn.execute("DELETE FROM silver.lmp")
        conn.execute("DELETE FROM silver.fuel_mix")
        conn.execute("DELETE FROM gold.iso_summary")
        conn.close()
        log.info("database_wiped")
        print("Done.")
    isos = app_config["isos"]
    end_time = pd.Timestamp.now(tz="UTC").floor("h")

    print(f"Seeding {hours} hours of data for {isos}...")

    for iso in isos:
        print(f"  Generating {iso} LMP data...")
        lmp_df = generate_lmp_df(iso, hours, end_time)
        rows = write_bronze_lmp(lmp_df, iso)
        log.info("bronze_lmp_seeded", iso=iso, rows=rows)

        print(f"  Generating {iso} fuel mix data...")
        fuel_df = generate_fuel_mix_df(iso, hours, end_time)
        rows = write_bronze_fuel_mix(fuel_df, iso)
        log.info("bronze_fuel_mix_seeded", iso=iso, rows=rows)

    print("Transforming to silver...")
    transform_to_silver_lmp()
    transform_to_silver_fuel_mix()

    print("Computing gold aggregations...")
    rows = compute_gold_iso_summary()

    print(f"Done. {rows} gold rows computed.")
    log.info("seed_complete", gold_rows=rows)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Seed GridPace database with synthetic data")
    parser.add_argument("--hours", type=int, default=48, help="Hours of history to generate")
    parser.add_argument("--force", action="store_true", help="Reseed even if data exists")
    args = parser.parse_args()

    seed_database(hours=args.hours, force=args.force)
