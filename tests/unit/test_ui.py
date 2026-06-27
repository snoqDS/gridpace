"""
Unit tests for Streamlit UI components and dashboard data loaders.
Tests display logic, cache behavior, and schema validation.

Scope: UI layer only — color mapping, status constants, cache error handling.
Anomaly detection logic is tested in tests/unit/test_anomaly.py.
Migration schema tests live here since they validate what the dashboard depends on.
"""

from unittest.mock import patch

import pandas as pd
import pytest

from gridpace.config import app_config


@pytest.fixture
def sample_iso_summary():
    """Sample gold ISO summary DataFrame for UI testing."""
    return pd.DataFrame({
        "iso": ["ERCOT", "CAISO", "PJM"],
        "window_start": pd.date_range("2026-01-01", periods=3, freq="h", tz="UTC"),
        "window_end": pd.date_range("2026-01-01 01:00", periods=3, freq="h", tz="UTC"),
        "avg_lmp": [25.1, 45.2, 78.9],
        "max_lmp": [30.0, 55.0, 95.0],
        "min_lmp": [20.0, 35.0, 60.0],
        "renewable_pct": [35.0, 42.0, 28.0],
        "natural_gas": [45.0, 35.0, 35.0],
        "wind": [25.0, 15.0, 10.0],
        "solar": [10.0, 25.0, 5.0],
        "coal": [15.0, 2.0, 25.0],
        "nuclear": [5.0, 8.0, 25.0],
        "other": [0.0, 0.0, 0.0],
        "computed_at": pd.date_range("2026-01-01", periods=3, freq="h", tz="UTC"),
    })


def test_lmp_color_normal():
    """LMP below normal_max returns normal."""
    from gridpace.ui.components.iso_cards import lmp_color
    assert lmp_color(25.0) == "normal"


def test_lmp_color_elevated():
    """LMP between normal_max and elevated_max returns off."""
    from gridpace.ui.components.iso_cards import lmp_color
    assert lmp_color(75.0) == "off"


def test_lmp_color_high():
    """LMP above elevated_max returns inverse."""
    from gridpace.ui.components.iso_cards import lmp_color
    assert lmp_color(150.0) == "inverse"


def test_lmp_color_at_boundary():
    """LMP exactly at normal_max boundary."""
    from gridpace.ui.components.iso_cards import lmp_color
    assert lmp_color(50.0) == "off"


def test_status_emoji_has_all_levels():
    """STATUS_EMOJI contains all five status levels."""
    from gridpace.ui.components.iso_cards import STATUS_EMOJI
    assert set(STATUS_EMOJI.keys()) == {"grey", "green", "yellow", "red", "critical"}


def test_status_label_has_all_levels():
    """STATUS_LABEL contains all five status levels."""
    from gridpace.ui.components.iso_cards import STATUS_LABEL
    assert set(STATUS_LABEL.keys()) == {"grey", "green", "yellow", "red", "critical"}


def test_load_iso_summary_returns_none_on_empty_db():
    """load_iso_summary returns None gracefully when DB has no data."""
    with patch("gridpace.grid.storage.get_connection") as mock_conn:
        mock_conn.side_effect = Exception("No database")
        from gridpace.ui.app import load_iso_summary
        load_iso_summary.clear()
        result = load_iso_summary()
        assert result is None


def test_load_anomaly_results_returns_empty_dict_on_error():
    """load_anomaly_results returns empty dict on error."""
    with patch("gridpace.grid.storage.get_connection") as mock_conn:
        mock_conn.side_effect = Exception("No database")
        from gridpace.ui.app import load_anomaly_results
        load_anomaly_results.clear()
        result = load_anomaly_results()
        assert result == {}


def test_load_anomaly_results_returns_dict():
    """load_anomaly_results returns a dict."""
    from gridpace.ui.app import load_anomaly_results
    load_anomaly_results.clear()
    result = load_anomaly_results()
    assert isinstance(result, dict)


def test_migration_002_adds_fuel_columns():
    """Migration 002 adds fuel mix columns to gold schema."""

    import duckdb

    from gridpace.grid.migrator import MIGRATIONS_DIR

    conn = duckdb.connect(":memory:")

    # Apply all migrations
    for migration_file in sorted(MIGRATIONS_DIR.glob("*.sql")):
        conn.execute(migration_file.read_text())

    # Check fuel columns exist in gold.iso_summary
    cols = conn.execute("""
        SELECT column_name FROM information_schema.columns
        WHERE table_schema = 'gold' AND table_name = 'iso_summary'
    """).fetchall()
    col_names = {c[0] for c in cols}

    expected_fuel_cols = {"natural_gas", "wind", "solar", "coal", "nuclear", "other"}
    assert expected_fuel_cols.issubset(col_names)
    conn.close()

def test_iso_timezones_covers_configured_isos():
    """All configured ISOs have a timezone entry."""
    from gridpace.ui.components.iso_cards import ISO_TIMEZONES
    isos = app_config["isos"]
    for iso in isos:
        assert iso in ISO_TIMEZONES, f"ISO {iso} missing from ISO_TIMEZONES"


def test_get_iso_color_known_iso():
    """Known ISO returns a color string."""
    from gridpace.ui.components.price_charts import _get_iso_color
    color = _get_iso_color("ERCOT")
    assert color.startswith("#")


def test_get_iso_color_unknown_iso():
    """Unknown ISO returns fallback grey color."""
    from gridpace.ui.components.price_charts import _get_iso_color
    color = _get_iso_color("UNKNOWN_ISO")
    assert color == "#adb5bd"


def test_load_iso_summary_history_returns_none_on_error():
    """load_iso_summary_history returns None gracefully on error."""
    with patch("gridpace.grid.storage.get_connection") as mock_conn:
        mock_conn.side_effect = Exception("No database")
        from gridpace.ui.app import load_iso_summary_history
        load_iso_summary_history.clear()
        result = load_iso_summary_history()
        assert result is None
