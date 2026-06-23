"""
Unit tests for Prefect flow tasks.
Tests task behavior using .fn() to bypass Prefect context requirements.
DB-dependent tests use initialized_db fixture from conftest.py.
"""

from unittest.mock import patch

import pandas as pd

from tests.conftest import SAMPLE_ROWS, TEST_ISO


def test_fetch_lmp_task_returns_dataframe():
    """fetch_lmp_task returns a DataFrame."""
    from gridpace.grid.flows import fetch_lmp_task
    result = fetch_lmp_task.fn(TEST_ISO)
    assert isinstance(result, pd.DataFrame)
    assert len(result) > 0


def test_fetch_fuel_mix_task_returns_dataframe():
    """fetch_fuel_mix_task returns a DataFrame."""
    from gridpace.grid.flows import fetch_fuel_mix_task
    result = fetch_fuel_mix_task.fn(TEST_ISO)
    assert isinstance(result, pd.DataFrame)
    assert len(result) > 0


def test_write_bronze_task_lmp(initialized_db, monkeypatch, sample_lmp_df):
    """write_bronze_task writes LMP data to bronze."""
    monkeypatch.setattr("gridpace.grid.storage.DB_PATH", initialized_db)
    from gridpace.grid.flows import write_bronze_task
    rows = write_bronze_task.fn(sample_lmp_df, TEST_ISO, "lmp")
    assert rows == SAMPLE_ROWS


def test_write_bronze_task_fuel_mix(initialized_db, monkeypatch, sample_fuel_mix_df):
    """write_bronze_task writes fuel mix data to bronze."""
    monkeypatch.setattr("gridpace.grid.storage.DB_PATH", initialized_db)
    from gridpace.grid.flows import write_bronze_task
    rows = write_bronze_task.fn(sample_fuel_mix_df, TEST_ISO, "fuel_mix")
    assert rows == SAMPLE_ROWS


def test_gap_check_task_returns_dict():
    """gap_check_task returns a dict with expected keys."""
    from gridpace.grid.flows import gap_check_task
    with patch("gridpace.grid.storage.get_last_ingested_at", return_value=None):
        result = gap_check_task.fn()
        assert isinstance(result, dict)
        assert "has_gap" in result
        assert "message" in result
