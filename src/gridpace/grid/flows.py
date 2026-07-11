"""
Prefect flows for GridPace data pipeline.
Orchestrates the bronze to silver to gold pipeline on a schedule.

Run manually:
    uv run python -m gridpace.grid.flows

Deploy to Prefect Cloud (future addition):
    prefect deploy
"""

from prefect import flow, task

from gridpace.config import app_config
from gridpace.monitoring.logger import get_logger

log = get_logger(__name__)

@task(retries=2, retry_delay_seconds=30)
def fetch_lmp_task(iso: str):
    """Fetch LMP data for a single ISO with retry on failure."""
    from gridpace.grid.clients.gridstatus import get_lmp
    df = get_lmp(iso)
    if df is None:
        log.warning("lmp_fetch_skipped", iso=iso)
        return None
    log.info("lmp_fetched", iso=iso, rows=len(df))
    return df


@task(retries=2, retry_delay_seconds=30)
def fetch_fuel_mix_task(iso: str):
    """Fetch fuel mix data for a single ISO with retry on failure."""
    from gridpace.grid.clients.gridstatus import get_fuel_mix
    df = get_fuel_mix(iso)
    if df is None:
        log.warning("fuel_mix_fetch_skipped", iso=iso)
        return None
    log.info("fuel_mix_fetched", iso=iso, rows=len(df))
    return df


@task
def write_bronze_task(df, iso: str, dataset: str):
    """Write raw data to bronze layer."""
    from gridpace.grid.storage import write_bronze_fuel_mix, write_bronze_lmp
    if dataset == "lmp":
        rows = write_bronze_lmp(df, iso)
    else:
        rows = write_bronze_fuel_mix(df, iso)
    log.info("bronze_written", iso=iso, dataset=dataset, rows=rows)
    return rows


@task
def transform_silver_task():
    """Transform bronze to silver for all ISOs."""
    from gridpace.grid.storage import (
        transform_to_silver_fuel_mix,
        transform_to_silver_lmp,
    )
    lmp_rows = transform_to_silver_lmp()
    fuel_rows = transform_to_silver_fuel_mix()
    log.info("silver_transform_complete", lmp_rows=lmp_rows, fuel_rows=fuel_rows)
    return {"lmp_rows": lmp_rows, "fuel_rows": fuel_rows}


@task
def compute_gold_task():
    """Compute gold layer aggregations."""
    from gridpace.grid.storage import compute_gold_iso_summary
    rows = compute_gold_iso_summary()
    log.info("gold_computed", rows=rows)
    return rows


@task
def retention_task():
    """Apply bronze data retention policy."""
    from gridpace.grid.storage import apply_retention_policy
    deleted = apply_retention_policy()
    log.info("retention_applied", rows_deleted=deleted)
    return deleted


@task
def gap_check_task():
    """Check for data gaps and log results."""
    from gridpace.grid.storage import check_data_gap
    result = check_data_gap("lmp")
    if result["has_gap"]:
        log.warning("data_gap_detected", **result)
    return result

@flow(name="grid-pipeline", log_prints=True)
def grid_pipeline():
    """
    Main GridPace data pipeline flow.
    Runs on a 2-hour schedule via Prefect deployment.

    Steps:
        1. Check for data gaps
        2. Fetch LMP and fuel mix per ISO in parallel
        3. Write all raw data to bronze layer
        4. Transform bronze to silver
        5. Compute gold aggregations
        6. Apply retention policy
    """
    from gridpace.grid.migrator import run_migrations

    log.info("pipeline_started")

    # Ensure DB is up to date
    run_migrations()

    # Check for gaps before fetching
    gap_check_task()

    # Get configured ISOs
    isos = app_config["isos"]

    # Fetch all ISOs in parallel
    lmp_futures = [fetch_lmp_task.submit(iso) for iso in isos]
    fuel_futures = [fetch_fuel_mix_task.submit(iso) for iso in isos]

# Write bronze — wait for fetches to complete, skip None results
    for iso, lmp_future in zip(isos, lmp_futures, strict=True):
        result = lmp_future.result()
        if result is not None:
            write_bronze_task(result, iso, "lmp")
        else:
            log.warning("bronze_lmp_skipped", iso=iso)

    for iso, fuel_future in zip(isos, fuel_futures, strict=True):
        result = fuel_future.result()
        if result is not None:
            write_bronze_task(result, iso, "fuel_mix")
        else:
            log.warning("bronze_fuel_mix_skipped", iso=iso)

    # Transform to silver
    transform_silver_task()

    # Compute gold
    compute_gold_task()

    # Apply retention
    retention_task()

    log.info("pipeline_complete")


if __name__ == "__main__":
    grid_pipeline()
