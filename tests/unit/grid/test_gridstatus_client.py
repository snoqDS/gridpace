"""
Unit tests for GridStatus client.
All tests mock config to force dry_run mode.
No API calls, no quota used.
"""

from unittest.mock import patch

import pandas as pd
import pytest

from gridpace.grid.clients.gridstatus import _get_iso, get_fuel_mix, get_lmp


@pytest.fixture(autouse=True)
def force_dry_run():
    """Force dry_run=True and limit=10 for all tests regardless of settings.yml."""
    mock_config = {
        "ingestion": {
            "dry_run": True,
            "default_row_limit": 10,
        },
        "isos": ["ERCOT", "CAISO", "PJM"],
    }
    with patch("gridpace.grid.clients.gridstatus.app_config", mock_config):
        yield


def test_get_lmp_returns_dataframe():
    """get_lmp returns a DataFrame."""
    df = get_lmp("ERCOT")
    assert isinstance(df, pd.DataFrame)


def test_get_lmp_has_expected_columns():
    """get_lmp sample data has required columns."""
    df = get_lmp("ERCOT")
    for col in ["time", "iso", "lmp", "energy", "congestion"]:
        assert col in df.columns


def test_get_fuel_mix_returns_dataframe():
    """get_fuel_mix returns a DataFrame."""
    df = get_fuel_mix("ERCOT")
    assert isinstance(df, pd.DataFrame)


def test_get_fuel_mix_has_expected_columns():
    """get_fuel_mix sample data has required columns."""
    df = get_fuel_mix("ERCOT")
    for col in ["time", "iso", "natural_gas", "wind", "solar"]:
        assert col in df.columns


def test_get_lmp_returns_rows():
    """get_lmp returns at least one row."""
    df = get_lmp("ERCOT")
    assert len(df) > 0


def test_get_fuel_mix_returns_rows():
    """get_fuel_mix returns at least one row."""
    df = get_fuel_mix("ERCOT")
    assert len(df) > 0


def test_get_iso_invalid_raises():
    """_get_iso raises ValueError for unsupported ISO."""
    with pytest.raises(ValueError):
        _get_iso("INVALID")


def test_get_iso_valid_ercot():
    """_get_iso returns a valid object for ERCOT."""
    iso = _get_iso("ERCOT")
    assert iso is not None
