"""
Unit tests for size-based retention and archive functions.
Tests layer size checks, retention policy, and Parquet export.
"""

from pathlib import Path
from unittest.mock import patch


def test_get_layer_sizes_returns_dict(initialized_db, monkeypatch):
    """get_layer_sizes returns dict with bronze, silver, gold keys."""
    monkeypatch.setattr("gridpace.grid.storage.DB_PATH", initialized_db)
    from gridpace.grid.storage import get_layer_sizes
    sizes = get_layer_sizes()
    assert "bronze" in sizes
    assert "silver" in sizes
    assert "gold" in sizes


def test_get_layer_sizes_has_rows_key(initialized_db, monkeypatch):
    """get_layer_sizes result has rows key per layer."""
    monkeypatch.setattr("gridpace.grid.storage.DB_PATH", initialized_db)
    from gridpace.grid.storage import get_layer_sizes
    sizes = get_layer_sizes()
    for layer in ["bronze", "silver", "gold"]:
        assert "rows" in sizes[layer]
        assert "db_total_gb" in sizes[layer]


def test_apply_size_based_retention_no_action(initialized_db, monkeypatch):
    """apply_size_based_retention takes no action when DB is small."""
    monkeypatch.setattr("gridpace.grid.storage.DB_PATH", initialized_db)
    from gridpace.grid.storage import apply_size_based_retention
    result = apply_size_based_retention()
    assert "actions" in result
    assert "db_size_gb" in result
    assert result["actions"] == {}


def test_apply_size_based_retention_warning(initialized_db, monkeypatch, tmp_path):
    """apply_size_based_retention logs warning when approaching cap."""
    monkeypatch.setattr("gridpace.grid.storage.DB_PATH", initialized_db)
    mock_cfg = {
        "storage": {
            "bronze_warning_gb": 0.000001,
            "bronze_cap_gb": 5.0,
            "archive_dir": str(tmp_path / "archive"),
        },
        "ingestion": {"poll_interval_minutes": 5},
        "retention": {"bronze_days": 90},
    }
    with patch("gridpace.grid.storage.app_config", mock_cfg):
        from gridpace.grid.storage import apply_size_based_retention
        result = apply_size_based_retention()
        assert "warning" in result["actions"]


def test_export_bronze_to_parquet(initialized_db, monkeypatch, sample_lmp_df, tmp_path):
    """export_bronze_to_parquet creates a Parquet file."""
    monkeypatch.setattr("gridpace.grid.storage.DB_PATH", initialized_db)
    mock_cfg = {
        "storage": {"archive_dir": str(tmp_path / "archive")},
        "ingestion": {"poll_interval_minutes": 5},
        "retention": {"bronze_days": 90},
    }
    with patch("gridpace.grid.storage.app_config", mock_cfg):
        from datetime import UTC, datetime

        from gridpace.grid.storage import export_bronze_to_parquet, write_bronze_lmp
        write_bronze_lmp(sample_lmp_df, "ERCOT")
        cutoff = datetime.now(UTC)
        output = export_bronze_to_parquet("lmp", cutoff)
        assert Path(output).exists()
        assert str(output).endswith(".parquet")
