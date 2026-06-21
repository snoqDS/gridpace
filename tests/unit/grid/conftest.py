"""
Shared fixtures for grid unit tests.
pytest loads this automatically for all tests in tests/unit/grid/.
"""

import duckdb
import pandas as pd
import pytest


@pytest.fixture
def temp_db(tmp_path):
    """Provide a temporary DuckDB database path for each test."""
    return tmp_path / "test.duckdb"


@pytest.fixture
def initialized_db(temp_db, monkeypatch):
    """Provide a fully migrated temporary database."""
    monkeypatch.setattr("gridpace.grid.storage.DB_PATH", temp_db)
    monkeypatch.setattr("gridpace.grid.migrator.DB_PATH", temp_db)

    from gridpace.grid.migrator import (
        _ensure_migrations_table,
        _get_applied_migrations,
        _get_pending_migrations,
    )
    import duckdb
    conn = duckdb.connect(str(temp_db))
    _ensure_migrations_table(conn)
    applied = _get_applied_migrations(conn)
    pending = _get_pending_migrations(applied)
    for migration_file in pending:
        sql = migration_file.read_text()
        conn.execute(sql)
        conn.execute(
            "INSERT INTO _migrations (id) VALUES (?)",
            [migration_file.name]
        )
    conn.close()
    return temp_db


@pytest.fixture
def sample_lmp_df():
    """Sample LMP DataFrame matching dry_run output. 3 rows."""
    return pd.DataFrame({
        "time": pd.date_range("2026-01-01", periods=3, freq="h"),
        "iso": ["ERCOT"] * 3,
        "lmp": [25.1, 30.4, 28.9],
        "energy": [24.0, 29.0, 27.5],
        "congestion": [1.1, 1.4, 1.4],
    })


@pytest.fixture
def sample_fuel_mix_df():
    """Sample fuel mix DataFrame matching dry_run output. 3 rows."""
    return pd.DataFrame({
        "time": pd.date_range("2026-01-01", periods=3, freq="h"),
        "iso": ["ERCOT"] * 3,
        "natural_gas": [45.0, 42.0, 40.0],
        "wind": [25.0, 28.0, 30.0],
        "solar": [10.0, 12.0, 15.0],
        "coal": [15.0, 13.0, 10.0],
        "nuclear": [5.0, 5.0, 5.0],
    })
