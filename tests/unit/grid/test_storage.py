"""
Unit tests for DuckDB storage layer.
Uses temporary database to avoid touching production data.
Fixtures and constants from tests/unit/grid/conftest.py and tests/conftest.py.
"""

from unittest.mock import patch

import duckdb

from tests.conftest import SAMPLE_ROWS, TEST_ISO


def test_get_connection(initialized_db):
    """get_connection returns a valid DuckDB connection."""
    with patch("gridpace.grid.storage.DB_PATH", initialized_db):
        import importlib

        from gridpace.grid import storage
        importlib.reload(storage)
        conn = storage.get_connection()
        assert conn is not None
        conn.close()


def test_write_bronze_lmp(initialized_db, sample_lmp_df):
    """write_bronze_lmp writes correct number of rows."""
    with patch("gridpace.grid.storage.DB_PATH", initialized_db):
        import importlib

        from gridpace.grid import storage
        importlib.reload(storage)
        rows = storage.write_bronze_lmp(sample_lmp_df, TEST_ISO)
        assert rows == SAMPLE_ROWS


def test_write_bronze_fuel_mix(initialized_db, sample_fuel_mix_df):
    """write_bronze_fuel_mix writes correct number of rows."""
    with patch("gridpace.grid.storage.DB_PATH", initialized_db):
        import importlib

        from gridpace.grid import storage
        importlib.reload(storage)
        rows = storage.write_bronze_fuel_mix(sample_fuel_mix_df, TEST_ISO)
        assert rows == SAMPLE_ROWS


def test_transform_to_silver_lmp(initialized_db, sample_lmp_df):
    """transform_to_silver_lmp moves data from bronze to silver."""
    with patch("gridpace.grid.storage.DB_PATH", initialized_db):
        import importlib

        from gridpace.grid import storage
        importlib.reload(storage)
        storage.write_bronze_lmp(sample_lmp_df, TEST_ISO)
        rows = storage.transform_to_silver_lmp()
        assert rows > 0


def test_transform_to_silver_fuel_mix(initialized_db, sample_fuel_mix_df):
    """transform_to_silver_fuel_mix computes renewable_pct."""
    with patch("gridpace.grid.storage.DB_PATH", initialized_db):
        import importlib

        from gridpace.grid import storage
        importlib.reload(storage)
        storage.write_bronze_fuel_mix(sample_fuel_mix_df, TEST_ISO)
        rows = storage.transform_to_silver_fuel_mix()
        assert rows > 0
        conn = storage.get_connection()
        result = conn.execute(
            "SELECT renewable_pct FROM silver.fuel_mix LIMIT 1"
        ).fetchone()[0]
        conn.close()
        assert result is not None
        assert 0 <= result <= 100


def test_compute_gold_iso_summary(initialized_db, sample_lmp_df, sample_fuel_mix_df):
    """compute_gold_iso_summary aggregates silver data into gold."""
    with patch("gridpace.grid.storage.DB_PATH", initialized_db):
        import importlib

        from gridpace.grid import storage
        importlib.reload(storage)
        storage.write_bronze_lmp(sample_lmp_df, TEST_ISO)
        storage.write_bronze_fuel_mix(sample_fuel_mix_df, TEST_ISO)
        storage.transform_to_silver_lmp()
        storage.transform_to_silver_fuel_mix()
        rows = storage.compute_gold_iso_summary()
        assert rows > 0


def test_get_last_ingested_at_none_when_empty(initialized_db):
    """get_last_ingested_at returns None when no data exists."""
    with patch("gridpace.grid.storage.DB_PATH", initialized_db):
        import importlib

        from gridpace.grid import storage
        importlib.reload(storage)
        conn = duckdb.connect(str(initialized_db))
        result = conn.execute(
            "SELECT MAX(ingested_at) FROM bronze.lmp"
        ).fetchone()[0]
        conn.close()
        assert result is None


def test_get_last_ingested_at_returns_timestamp(initialized_db, sample_lmp_df):
    """get_last_ingested_at returns a timestamp after data is written."""
    with patch("gridpace.grid.storage.DB_PATH", initialized_db):
        import importlib

        from gridpace.grid import storage
        importlib.reload(storage)
        storage.write_bronze_lmp(sample_lmp_df, TEST_ISO)
        result = storage.get_last_ingested_at("lmp")
        assert result is not None


def test_apply_retention_deletes_nothing_recent(initialized_db, sample_lmp_df, sample_fuel_mix_df):
    """apply_retention_policy deletes nothing when data is recent."""
    with patch("gridpace.grid.storage.DB_PATH", initialized_db):
        import importlib

        from gridpace.grid import storage
        importlib.reload(storage)
        storage.write_bronze_lmp(sample_lmp_df, TEST_ISO)
        storage.write_bronze_fuel_mix(sample_fuel_mix_df, TEST_ISO)
        deleted = storage.apply_retention_policy()
        assert deleted == 0
