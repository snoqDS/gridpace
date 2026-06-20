"""
GridStatus client for fetching real-time grid data.
Supports dry_run mode to avoid burning API quota during development.
"""

import gridstatus
import pandas as pd

from gridpace.config import app_config

# Sample data for dry_run mode
SAMPLE_LMP = pd.DataFrame({
    "time": pd.date_range("2026-01-01", periods=5, freq="h"),
    "iso": ["ERCOT"] * 5,
    "lmp": [25.1, 30.4, 28.9, 45.2, 22.7],
    "energy": [24.0, 29.0, 27.5, 43.0, 21.5],
    "congestion": [1.1, 1.4, 1.4, 2.2, 1.2],
})

SAMPLE_FUEL_MIX = pd.DataFrame({
    "time": pd.date_range("2026-01-01", periods=5, freq="h"),
    "iso": ["ERCOT"] * 5,
    "natural_gas": [45.0, 42.0, 40.0, 38.0, 43.0],
    "wind": [25.0, 28.0, 30.0, 32.0, 27.0],
    "solar": [10.0, 12.0, 15.0, 14.0, 11.0],
    "coal": [15.0, 13.0, 10.0, 11.0, 14.0],
    "nuclear": [5.0, 5.0, 5.0, 5.0, 5.0],
})


def _get_iso(iso_name: str):
    """Return a gridstatus ISO object by name."""
    isos = {
        "ERCOT": gridstatus.Ercot,
        "CAISO": gridstatus.CAISO,
        "PJM": gridstatus.PJM,
    }
    if iso_name not in isos:
        raise ValueError(f"Unsupported ISO: {iso_name}. Choose from {list(isos.keys())}")
    return isos[iso_name]()


def get_lmp(iso_name: str = "ERCOT") -> pd.DataFrame:
    """
    Fetch real-time LMP prices for a given ISO.
    Returns sample data if dry_run is enabled in config/settings.yml.
    """
    dry_run = app_config["ingestion"]["dry_run"]
    limit = app_config["ingestion"]["default_row_limit"]

    if dry_run:
        print(f"[dry_run] Returning sample LMP data for {iso_name}")
        return SAMPLE_LMP

    iso = _get_iso(iso_name)

    if iso_name == "ERCOT":
        df = iso.get_lmp(date="latest")
    else:
        df = iso.get_lmp(date="latest", market="REAL_TIME_5_MIN")

    return df.head(limit)


def get_fuel_mix(iso_name: str = "ERCOT") -> pd.DataFrame:
    """
    Fetch current generation fuel mix for a given ISO.
    Returns sample data if dry_run is enabled in config/settings.yml.
    """
    dry_run = app_config["ingestion"]["dry_run"]
    limit = app_config["ingestion"]["default_row_limit"]

    if dry_run:
        print(f"[dry_run] Returning sample fuel mix data for {iso_name}")
        return SAMPLE_FUEL_MIX

    iso = _get_iso(iso_name)
    df = iso.get_fuel_mix(date="latest")
    return df.head(limit)