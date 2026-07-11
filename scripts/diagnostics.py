"""
GridPace diagnostics script.
Prints a full system status report including config, health checks,
database stats, data date ranges, and security scan summary.

Usage:
    uv run python scripts/diagnostics.py
    uv run python scripts/diagnostics.py --security   # include pip-audit scan

API quota tracking: not required for gridstatus open-source library which
pulls directly from ISO public portals with no request limits.
If switching to the paid gridstatusio API (250 requests/month free tier),
add quota monitoring here. See docs/architecture.md Key Decisions for rationale.
"""

import sys
import subprocess
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import argparse

from gridpace.config import ROOT, app_config
from gridpace.monitoring.logger import get_logger

log = get_logger(__name__)


def print_section(title: str) -> None:
    """Print a section header."""
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print(f"{'=' * 60}")


def print_config() -> None:
    """Print current configuration summary."""
    print_section("Configuration")
    isos = app_config.get("isos", [])
    poll = app_config["ingestion"]["poll_interval_minutes"]
    dry_run = app_config["ingestion"]["dry_run"]

    print(f"  ISOs configured:     {', '.join(isos)}")
    print(f"  Poll interval:       {poll} minutes")
    print(f"  Dry run mode:        {dry_run}")
    print(f"  DB path:             {ROOT / 'data' / 'gridpace.duckdb'}")
    print(f"  Report generated:    {datetime.now(UTC).strftime('%Y-%m-%d %H:%M UTC')}")
    print(f"  Seed behavior:       use 'make reseed' to wipe and regenerate")
    print(f"                       use 'make seed' to append if empty")
    print(f"                       use 'make seed-week' to wipe and seed 168h")


def print_health() -> None:
    """Print health check results."""
    print_section("System Health")
    from gridpace.monitoring.health import get_health_summary

    status_icons = {"ok": "✓", "warning": "!", "error": "✗"}
    summary = get_health_summary()

    for check, result in summary.items():
        icon = status_icons.get(result["status"], "?")
        label = check.replace("_", " ").title()
        print(f"  [{icon}] {label}: {result['message']}")
        if result.get("details") and result["status"] != "ok":
            for _key, val in result["details"].items():
                if isinstance(val, list):
                    for item in val:
                        print(f"        • {item}")


def print_db_stats() -> None:
    """Print database row counts and size per layer."""
    print_section("Database Statistics")
    try:
        from gridpace.grid.storage import get_connection, DB_PATH

        path = Path(DB_PATH)
        if not path.exists():
            print("  Database file does not exist — run migrations first.")
            return

        size_mb = round(path.stat().st_size / 1024 / 1024, 1)
        print(f"  File size: {size_mb}MB")
        print()

        conn = get_connection()
        layers = {
            "bronze.lmp":        "Bronze LMP",
            "bronze.fuel_mix":   "Bronze Fuel Mix",
            "silver.lmp":        "Silver LMP",
            "silver.fuel_mix":   "Silver Fuel Mix",
            "gold.iso_summary":  "Gold ISO Summary",
        }

        for table, label in layers.items():
            try:
                count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
                print(f"  {label:<25} {count:>8} rows")
            except Exception:
                print(f"  {label:<25} {'N/A':>8}")
        conn.close()
    except Exception as e:
        print(f"  Error reading database: {e}")


def print_date_ranges() -> None:
    """Print date ranges of data in the database, split by synthetic and real."""
    print_section("Data Date Ranges")
    try:
        from gridpace.grid.storage import get_connection

        conn = get_connection()

        # Silver LMP date ranges
        print("  Silver LMP:")
        try:
            result = conn.execute("""
                SELECT
                    iso,
                    market,
                    COUNT(*) as rows,
                    MIN(interval_start) as earliest,
                    MAX(interval_start) as latest
                FROM silver.lmp
                GROUP BY iso, market
                ORDER BY iso, market
            """).df()

            if result.empty:
                print("    No data in silver LMP layer.")
            else:
                for _, row in result.iterrows():
                    data_type = "synthetic" if row["market"] == "SYNTHETIC" else "real"
                    earliest = str(row["earliest"])[:16]
                    latest = str(row["latest"])[:16]
                    print(f"    {row['iso']:<8} {data_type:<10} {row['rows']:>6} rows  {earliest} → {latest}")
        except Exception as e:
            print(f"    Error: {e}")

        print()

        # Gold ISO Summary date ranges
        print("  Gold ISO Summary:")
        try:
            result = conn.execute("""
                SELECT
                    iso,
                    COUNT(*) as rows,
                    MIN(window_start) as earliest,
                    MAX(window_start) as latest
                FROM gold.iso_summary
                GROUP BY iso
                ORDER BY iso
            """).df()

            if result.empty:
                print("    No data in gold layer.")
            else:
                for _, row in result.iterrows():
                    earliest = str(row["earliest"])[:16]
                    latest = str(row["latest"])[:16]
                    print(f"    {row['iso']:<8} {row['rows']:>6} rows  {earliest} → {latest}")
        except Exception as e:
            print(f"    Error: {e}")

        conn.close()
    except Exception as e:
        print(f"  Error reading database: {e}")


def print_security_scan() -> None:
    """Run pip-audit and print summary."""
    print_section("Security Scan (pip-audit)")
    try:
        result = subprocess.run(
            ["uv", "run", "pip-audit", "--format", "columns"],
            capture_output=True,
            text=True,
            cwd=ROOT,
        )
        if result.returncode == 0:
            print("  ✓ No known vulnerabilities found.")
        else:
            print("  ! Vulnerabilities detected:")
            for line in result.stdout.strip().split("\n"):
                if line.strip():
                    print(f"    {line}")
    except Exception as e:
        print(f"  Error running pip-audit: {e}")


def main() -> None:
    parser = argparse.ArgumentParser(description="GridPace system diagnostics")
    parser.add_argument(
        "--security",
        action="store_true",
        help="Include pip-audit security scan (slower)",
    )
    args = parser.parse_args()

    # Suppress structlog output during diagnostics for cleaner output
    import logging
    logging.disable(logging.CRITICAL)

    print("\nGridPace Diagnostics")
    print(f"{'=' * 60}")

    print_config()
    print_health()
    print_db_stats()
    print_date_ranges()

    if args.security:
        print_security_scan()
    else:
        print_section("Security Scan")
        print("  Skipped — run with --security to include pip-audit scan.")

    print(f"\n{'=' * 60}\n")


if __name__ == "__main__":
    main()
