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

def test_sample_lmp_has_synthetic_market():
    """SAMPLE_LMP has Market=SYNTHETIC for synthetic data detection."""
    df = get_lmp("ERCOT")
    assert "Market" in df.columns
    assert (df["Market"] == "SYNTHETIC").all()


def test_get_iso_all_supported_isos():
    """All 9 supported ISOs are in ISO_CLASSES."""
    from gridpace.grid.clients.gridstatus import ISO_CLASSES
    expected = {"ERCOT", "CAISO", "PJM", "MISO", "SPP", "NYISO", "ISONE", "IESO", "AESO"}
    assert expected.issubset(set(ISO_CLASSES.keys()))


def test_get_iso_pjm_raises_without_key():
    """_get_iso raises RuntimeError for PJM when PJM_API_KEY not set."""
    with patch("gridpace.grid.clients.gridstatus.os.getenv", return_value=None):
        with pytest.raises(RuntimeError, match="PJM_API_KEY"):
            _get_iso("PJM")


def test_get_lmp_returns_none_when_iso_skipped():
    """get_lmp returns None when ISO raises RuntimeError (e.g. PJM without key)."""
    mock_config = {
        "ingestion": {"dry_run": False, "default_row_limit": 10},
        "isos": ["PJM"],
    }
    with patch("gridpace.grid.clients.gridstatus.app_config", mock_config):
        with patch("gridpace.grid.clients.gridstatus.os.getenv", return_value=None):
            result = get_lmp("PJM")
            assert result is None


def test_get_fuel_mix_returns_none_when_iso_skipped():
    """get_fuel_mix returns None when ISO raises RuntimeError."""
    mock_config = {
        "ingestion": {"dry_run": False, "default_row_limit": 10},
        "isos": ["PJM"],
    }
    with patch("gridpace.grid.clients.gridstatus.app_config", mock_config):
        with patch("gridpace.grid.clients.gridstatus.os.getenv", return_value=None):
            result = get_fuel_mix("PJM")
            assert result is None
