"""
Shared transformation utilities for GridPace data pipeline.
Used by source-specific transformers in this package.

Pipeline: bronze -> transformers/<source>.py -> validation -> silver

Future: these utilities are designed for migration to dbt macros.
"""

from pathlib import Path

import pandas as pd
import yaml

CONTRACTS_DIR = Path(__file__).parent.parent / "contracts"


def load_column_map(source: str, dataset: str) -> dict:
    """
    Load column mapping from contract YAML.
    Maps raw API column names to internal silver schema names.

    Args:
        source: data source name e.g. 'gridstatus'
        dataset: dataset name e.g. 'lmp'

    Returns:
        dict mapping raw column names to normalized names
    """
    contract_path = CONTRACTS_DIR / f"{source}.yml"
    with open(contract_path) as f:
        contract = yaml.safe_load(f)
    return contract["datasets"][dataset].get("column_map", {})


def normalize_timestamps(df: pd.DataFrame, columns: list) -> pd.DataFrame:
    """
    Convert timestamp columns to UTC timezone-aware datetimes.
    Handles mixed timezone inputs gracefully.

    Args:
        df: DataFrame to modify
        columns: list of column names to normalize

    Returns:
        DataFrame with normalized timestamp columns
    """
    for col in columns:
        if col not in df.columns:
            continue
        try:
            df[col] = pd.to_datetime(df[col], utc=True)
        except Exception:
            # TODO: replace with structlog logger.warning() in Session 4
            print(f"WARNING: Could not normalize timestamp column '{col}'")
    return df


def coerce_numeric(df: pd.DataFrame, columns: list, fill_value: float = 0.0) -> pd.DataFrame:
    """
    Coerce columns to numeric types.
    Non-parseable values become fill_value.

    Args:
        df: DataFrame to modify
        columns: list of column names to coerce
        fill_value: value to use for unparseable entries

    Returns:
        DataFrame with numeric columns coerced
    """
    for col in columns:
        if col not in df.columns:
            continue
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(fill_value)
    return df


def filter_to_schema(df: pd.DataFrame, columns: list) -> pd.DataFrame:
    """
    Keep only columns that exist in both the DataFrame and the target schema.
    Silently drops extra columns, never errors on missing optional ones.

    Args:
        df: DataFrame to filter
        columns: list of target schema column names

    Returns:
        DataFrame with only schema columns present in df
    """
    return df[[col for col in columns if col in df.columns]]
