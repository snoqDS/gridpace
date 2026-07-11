"""
GridStatus client for fetching real-time grid data.
Supports dry_run mode for development without live API calls.

ISO support:
    No API key required: ERCOT, CAISO, MISO, SPP, NYISO, ISONE, IESO, AESO
    Free key required:   PJM (register at https://apiportal.pjm.com)
                         PJM requires PJM member account — non-member accounts
                         (e.g. gmail.com) have significantly limited access.
                         Set PJM_API_KEY in .env to enable PJM live data.
                         Without key, PJM is skipped in live pipeline but
                         works in dry_run mode.

See docs/data_sources.md for full API details and registration instructions.
"""

import os

import gridstatus
import pandas as pd

from gridpace.config import app_config
from gridpace.monitoring.logger import get_logger

log = get_logger(__name__)

# Sample data for dry_run mode
SAMPLE_LMP = pd.DataFrame({
    "time": pd.date_range("2026-01-01", periods=5, freq="h"),
    "iso": ["ERCOT"] * 5,
    "lmp": [25.1, 30.4, 28.9, 45.2, 22.7],
    "energy": [24.0, 29.0, 27.5, 43.0, 21.5],
    "congestion": [1.1, 1.4, 1.4, 2.2, 1.2],
    "Market": ["SYNTHETIC"] * 5,
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

# ISO class mapping — all supported gridstatus ISOs
# PJM requires PJM_API_KEY env var — skipped gracefully if not set
ISO_CLASSES = {
    "ERCOT": (gridstatus.Ercot, {}),
    "CAISO": (gridstatus.CAISO, {}),
    "MISO":  (gridstatus.MISO, {}),
    "SPP":   (gridstatus.SPP, {}),
    "NYISO": (gridstatus.NYISO, {}),
    "ISONE": (gridstatus.ISONE, {}),
    "IESO":  (gridstatus.IESO, {}),
    "AESO":  (gridstatus.AESO, {}),
    "PJM":   (gridstatus.PJM, {"api_key": os.getenv("PJM_API_KEY")}),
}


def _get_iso(iso_name: str):
    """
    Return a gridstatus ISO object by name.
    Raises ValueError for unsupported ISOs.
    Raises RuntimeError for PJM when PJM_API_KEY is not set.
    """
    if iso_name not in ISO_CLASSES:
        raise ValueError(
            f"Unsupported ISO: {iso_name}. "
            f"Choose from {list(ISO_CLASSES.keys())}"
        )

    iso_class, kwargs = ISO_CLASSES[iso_name]

    if iso_name == "PJM" and not kwargs.get("api_key"):
        raise RuntimeError(
            "PJM_API_KEY not set — PJM requires a free API key from "
            "https://apiportal.pjm.com. Set PJM_API_KEY in .env to enable. "
            "See docs/data_sources.md for registration instructions."
        )

    return iso_class(**kwargs)


def get_lmp(iso_name: str = "ERCOT") -> pd.DataFrame:
    """
    Fetch real-time LMP prices for a given ISO.
    Returns sample data if dry_run is enabled in config/settings.yml.
    Returns None if ISO is unavailable (e.g. PJM without API key).
    """
    dry_run = app_config["ingestion"]["dry_run"]
    limit = app_config["ingestion"]["default_row_limit"]

    if dry_run:
        log.info("dry_run_lmp", iso=iso_name, mode="dry_run")
        return SAMPLE_LMP

    try:
        iso = _get_iso(iso_name)
    except RuntimeError as e:
        log.warning("iso_skipped", iso=iso_name, reason=str(e))
        return None

    if iso_name == "ERCOT":
        df = iso.get_lmp(date="latest")
    else:
        df = iso.get_lmp(date="latest", market="REAL_TIME_5_MIN")

    return df.head(limit)


def get_fuel_mix(iso_name: str = "ERCOT") -> pd.DataFrame:
    """
    Fetch current generation fuel mix for a given ISO.
    Returns sample data if dry_run is enabled in config/settings.yml.
    Returns None if ISO is unavailable (e.g. PJM without API key).
    """
    dry_run = app_config["ingestion"]["dry_run"]
    limit = app_config["ingestion"]["default_row_limit"]

    if dry_run:
        log.info("dry_run_fuel_mix", iso=iso_name, mode="dry_run")
        return SAMPLE_FUEL_MIX

    try:
        iso = _get_iso(iso_name)
    except RuntimeError as e:
        log.warning("iso_skipped", iso=iso_name, reason=str(e))
        return None

    df = iso.get_fuel_mix(date="latest")
    return df.head(limit)
