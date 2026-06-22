"""
Unit tests for data contract validation.
Tests field existence, nullability, type checking, and contract loading.
"""

import pandas as pd
import pytest

from tests.conftest import TEST_ISO


@pytest.fixture
def valid_lmp_df():
    """Valid normalized LMP DataFrame matching silver schema."""
    return pd.DataFrame({
        "iso": [TEST_ISO] * 3,
        "interval_start": pd.date_range("2026-01-01", periods=3, freq="h", tz="UTC"),
        "lmp": [25.1, 30.4, 28.9],
        "location": [None, None, None],
        "location_type": [None, None, None],
        "market": ["UNKNOWN"] * 3,
    })


@pytest.fixture
def valid_fuel_mix_df():
    """Valid normalized fuel mix DataFrame matching silver schema."""
    return pd.DataFrame({
        "iso": [TEST_ISO] * 3,
        "time": pd.date_range("2026-01-01", periods=3, freq="h", tz="UTC"),
        "natural_gas": [45.0, 42.0, 40.0],
        "wind": [25.0, 28.0, 30.0],
        "solar": [10.0, 12.0, 15.0],
        "coal": [15.0, 13.0, 10.0],
        "nuclear": [5.0, 5.0, 5.0],
        "other": [0.0, 0.0, 0.0],
        "renewable_pct": [35.0, 40.0, 45.0],
    })


def test_valid_lmp_passes(valid_lmp_df):
    """Valid LMP DataFrame passes contract validation."""
    from gridpace.grid.validation import validate_dataframe
    result = validate_dataframe(valid_lmp_df, "gridstatus", "lmp")
    assert result["valid"] is True
    assert result["errors"] == []


def test_valid_fuel_mix_passes(valid_fuel_mix_df):
    """Valid fuel mix DataFrame passes contract validation."""
    from gridpace.grid.validation import validate_dataframe
    result = validate_dataframe(valid_fuel_mix_df, "gridstatus", "fuel_mix")
    assert result["valid"] is True
    assert result["errors"] == []


def test_missing_required_field_fails():
    """Missing required field produces validation error."""
    from gridpace.grid.validation import validate_dataframe
    df = pd.DataFrame({
        "iso": ["ERCOT"] * 3,
        "lmp": [25.1, 30.4, 28.9],
    })
    result = validate_dataframe(df, "gridstatus", "lmp")
    assert result["valid"] is False
    assert any("interval_start" in e for e in result["errors"])


def test_null_in_required_field_fails():
    """Null values in required field produce validation error."""
    from gridpace.grid.validation import validate_dataframe
    df = pd.DataFrame({
        "iso": ["ERCOT", None, "ERCOT"],
        "interval_start": pd.date_range("2026-01-01", periods=3, freq="h", tz="UTC"),
        "lmp": [25.1, 30.4, 28.9],
    })
    result = validate_dataframe(df, "gridstatus", "lmp")
    assert result["valid"] is False
    assert any("iso" in e for e in result["errors"])


def test_missing_optional_field_warns(valid_lmp_df):
    """Missing optional field produces warning not error."""
    from gridpace.grid.validation import validate_dataframe
    df = valid_lmp_df.drop(columns=["location"])
    result = validate_dataframe(df, "gridstatus", "lmp")
    assert result["valid"] is True
    assert any("location" in w for w in result["warnings"])


def test_rows_checked_count(valid_lmp_df):
    """rows_checked matches DataFrame length."""
    from gridpace.grid.validation import validate_dataframe
    result = validate_dataframe(valid_lmp_df, "gridstatus", "lmp")
    assert result["rows_checked"] == len(valid_lmp_df)


def test_invalid_contract_source_raises():
    """Unknown contract source raises FileNotFoundError."""
    from gridpace.grid.validation import validate_dataframe
    df = pd.DataFrame({"iso": ["ERCOT"]})
    with pytest.raises(FileNotFoundError):
        validate_dataframe(df, "nonexistent_source", "lmp")


def test_invalid_dataset_raises():
    """Unknown dataset raises KeyError."""
    from gridpace.grid.validation import validate_dataframe
    df = pd.DataFrame({"iso": ["ERCOT"]})
    with pytest.raises(KeyError):
        validate_dataframe(df, "gridstatus", "nonexistent_dataset")
