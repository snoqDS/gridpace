"""
Unit tests for GridStatus transformers.
Tests column mapping, timestamp normalization, type coercion,
renewable_pct computation, and silver schema filtering.
"""

import pandas as pd
import pytest

from tests.conftest import TEST_ISO


@pytest.fixture
def raw_lmp_df():
    """Raw LMP DataFrame mimicking GridStatus API output."""
    return pd.DataFrame({
        "time": pd.date_range("2026-01-01", periods=3, freq="h"),
        "iso": [TEST_ISO] * 3,
        "lmp": [25.1, 30.4, 28.9],
        "energy": [24.0, 29.0, 27.5],
        "congestion": [1.1, 1.4, 1.4],
    })


@pytest.fixture
def raw_fuel_mix_df():
    """Raw fuel mix DataFrame mimicking GridStatus API output."""
    return pd.DataFrame({
        "time": pd.date_range("2026-01-01", periods=3, freq="h"),
        "iso": [TEST_ISO] * 3,
        "natural_gas": [45.0, 42.0, 40.0],
        "wind": [25.0, 28.0, 30.0],
        "solar": [10.0, 12.0, 15.0],
        "coal": [15.0, 13.0, 10.0],
        "nuclear": [5.0, 5.0, 5.0],
        "other": [0.0, 0.0, 0.0],
    })


def test_transform_lmp_returns_dataframe(raw_lmp_df):
    """transform_lmp returns a DataFrame."""
    from gridpace.grid.transformers.gridstatus import transform_lmp
    result = transform_lmp(raw_lmp_df, TEST_ISO)
    assert isinstance(result, pd.DataFrame)


def test_transform_lmp_has_iso_column(raw_lmp_df):
    """transform_lmp output has iso column."""
    from gridpace.grid.transformers.gridstatus import transform_lmp
    result = transform_lmp(raw_lmp_df, TEST_ISO)
    assert "iso" in result.columns
    assert (result["iso"] == TEST_ISO).all()


def test_transform_lmp_timestamp_is_utc(raw_lmp_df):
    """transform_lmp normalizes interval_start to UTC."""
    from gridpace.grid.transformers.gridstatus import transform_lmp
    result = transform_lmp(raw_lmp_df, TEST_ISO)
    assert "interval_start" in result.columns
    assert str(result["interval_start"].dtype) == "datetime64[us, UTC]"


def test_transform_lmp_lmp_is_numeric(raw_lmp_df):
    """transform_lmp coerces lmp to float."""
    from gridpace.grid.transformers.gridstatus import transform_lmp
    result = transform_lmp(raw_lmp_df, TEST_ISO)
    assert pd.api.types.is_float_dtype(result["lmp"])


def test_transform_lmp_market_defaulted(raw_lmp_df):
    """transform_lmp defaults missing market to UNKNOWN."""
    from gridpace.grid.transformers.gridstatus import transform_lmp
    result = transform_lmp(raw_lmp_df, TEST_ISO)
    assert "market" in result.columns
    assert (result["market"] == "UNKNOWN").all()


def test_transform_lmp_drops_extra_columns(raw_lmp_df):
    """transform_lmp drops columns not in silver schema."""
    from gridpace.grid.transformers.gridstatus import transform_lmp
    result = transform_lmp(raw_lmp_df, TEST_ISO)
    assert "energy" not in result.columns
    assert "congestion" not in result.columns


def test_transform_fuel_mix_returns_dataframe(raw_fuel_mix_df):
    """transform_fuel_mix returns a DataFrame."""
    from gridpace.grid.transformers.gridstatus import transform_fuel_mix
    result = transform_fuel_mix(raw_fuel_mix_df, TEST_ISO)
    assert isinstance(result, pd.DataFrame)


def test_transform_fuel_mix_computes_renewable_pct(raw_fuel_mix_df):
    """transform_fuel_mix computes renewable_pct correctly."""
    from gridpace.grid.transformers.gridstatus import transform_fuel_mix
    result = transform_fuel_mix(raw_fuel_mix_df, TEST_ISO)
    assert "renewable_pct" in result.columns
    assert (result["renewable_pct"] >= 0).all()
    assert (result["renewable_pct"] <= 100).all()


def test_transform_fuel_mix_timestamp_is_utc(raw_fuel_mix_df):
    """transform_fuel_mix normalizes time to UTC."""
    from gridpace.grid.transformers.gridstatus import transform_fuel_mix
    result = transform_fuel_mix(raw_fuel_mix_df, TEST_ISO)
    assert str(result["time"].dtype) == "datetime64[us, UTC]"


def test_transform_fuel_mix_numeric_columns(raw_fuel_mix_df):
    """transform_fuel_mix coerces generation columns to float."""
    from gridpace.grid.transformers.gridstatus import transform_fuel_mix
    result = transform_fuel_mix(raw_fuel_mix_df, TEST_ISO)
    for col in ["natural_gas", "wind", "solar", "coal", "nuclear"]:
        assert pd.api.types.is_float_dtype(result[col])
