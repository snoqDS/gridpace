"""
GridStatus specific transformers for GridPace pipeline.
Converts raw GridStatus API data to silver layer schema.

Each function is a pure transformation — no I/O, no side effects.
Silver column definitions live in grid/contracts/gridstatus.yml — single source of truth.

Adding a new GridStatus dataset:
    1. Add column_map, silver_columns, and fields to grid/contracts/gridstatus.yml
    2. Add a new transform function here following the same pattern
"""

from pathlib import Path

import pandas as pd
import yaml

from gridpace.grid.transformers.utils import (
    coerce_numeric,
    filter_to_schema,
    load_column_map,
    normalize_timestamps,
)

CONTRACTS_DIR = Path(__file__).parent.parent / "contracts"


def _load_silver_columns(dataset: str) -> list:
    """Load silver schema column list from gridstatus.yml contract."""
    with open(CONTRACTS_DIR / "gridstatus.yml") as f:
        contract = yaml.safe_load(f)
    return contract["datasets"][dataset]["silver_columns"]


def transform_lmp(df: pd.DataFrame, iso: str) -> pd.DataFrame:
    """
    Transform raw GridStatus LMP data to silver schema.

    Steps:
        1. Rename columns per gridstatus.yml contract mapping
        2. Add iso column
        3. Normalize timestamps to UTC
        4. Coerce lmp to float
        5. Default missing market to 'UNKNOWN'
        6. Filter to silver schema columns from contract

    Args:
        df: raw LMP DataFrame from bronze layer
        iso: ISO name e.g. 'ERCOT'

    Returns:
        Normalized DataFrame ready for validation and silver write
    """
    column_map = load_column_map("gridstatus", "lmp")
    silver_columns = _load_silver_columns("lmp")

    df = df.rename(columns=column_map)

    if "iso" not in df.columns:
        df["iso"] = iso

    df = normalize_timestamps(df, ["interval_start", "interval_end"])
    df = coerce_numeric(df, ["lmp"], fill_value=0.0)

    # Default missing market — business logic lives here not in storage
    if "market" in df.columns:
        df["market"] = df["market"].fillna("UNKNOWN")
    else:
        df["market"] = "UNKNOWN"

    df = filter_to_schema(df, silver_columns)

    return df


def transform_fuel_mix(df: pd.DataFrame, iso: str) -> pd.DataFrame:
    """
    Transform raw GridStatus fuel mix data to silver schema.

    Steps:
        1. Rename columns per gridstatus.yml contract mapping
        2. Add iso column
        3. Normalize timestamps to UTC
        4. Coerce generation columns to float, fill missing with 0.0
        5. Compute renewable_pct
        6. Filter to silver schema columns from contract

    Args:
        df: raw fuel mix DataFrame from bronze layer
        iso: ISO name e.g. 'ERCOT'

    Returns:
        Normalized DataFrame ready for validation and silver write
    """
    column_map = load_column_map("gridstatus", "fuel_mix")
    silver_columns = _load_silver_columns("fuel_mix")

    df = df.rename(columns=column_map)

    if "iso" not in df.columns:
        df["iso"] = iso

    df = normalize_timestamps(df, ["time"])
    df = coerce_numeric(
        df,
        ["natural_gas", "wind", "solar", "coal", "nuclear", "other"],
        fill_value=0.0,
    )

# Compute renewable_pct — business logic lives here not in storage
    gen_cols = ["natural_gas", "wind", "solar", "coal", "nuclear", "other"]
    available_cols = [c for c in gen_cols if c in df.columns]
    total = (
        df[available_cols]
        .fillna(0)
        .sum(axis=1)
        .replace(0, float("nan"))
    )
    df["renewable_pct"] = (
        (df.get("wind", 0) + df.get("solar", 0)) / total * 100
    ).round(2)

    df = filter_to_schema(df, silver_columns)

    return df
