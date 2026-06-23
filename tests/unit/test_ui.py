"""
Unit tests for Streamlit UI components.
Uses streamlit testing utilities to test without a running server.
"""

import pandas as pd
import pytest


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


def test_load_iso_summary_returns_none_on_empty_db():
    """load_iso_summary returns None gracefully when DB has no data."""
    from unittest.mock import patch
    with patch("gridpace.grid.storage.get_connection") as mock_conn:
        mock_conn.side_effect = Exception("No database")
        from gridpace.ui.app import load_iso_summary
        load_iso_summary.clear()
        result = load_iso_summary()
        assert result is None
