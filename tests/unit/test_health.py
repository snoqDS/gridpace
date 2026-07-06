"""
Unit tests for GridPace health monitoring modules.
Tests db_health, data_health, and health summary structure.

Scope: health check logic only — uses mocked DB connections.
Health result structure defined in monitoring/health.py.
"""

from unittest.mock import patch


def test_make_result_structure():
    """make_result returns correct HealthResult structure."""
    from gridpace.monitoring.types import make_result
    result = make_result(status="ok", message="test", value=42, details={"key": "val"})
    assert result["status"] == "ok"
    assert result["message"] == "test"
    assert result["value"] == 42
    assert result["details"] == {"key": "val"}


def test_make_result_defaults():
    """make_result fills in defaults for optional fields."""
    from gridpace.monitoring.types import make_result
    result = make_result(status="ok", message="test")
    assert result["value"] is None
    assert result["details"] == {}


def test_get_health_summary_returns_all_keys():
    """get_health_summary returns all expected check keys."""
    from gridpace.monitoring.health import get_health_summary
    summary = get_health_summary()
    expected_keys = {
        "db_connectivity", "db_size", "migrations",
        "last_ingest", "row_counts", "data_gap"
    }
    assert expected_keys.issubset(set(summary.keys()))


def test_get_health_summary_all_have_status():
    """Every health result has a valid status field."""
    from gridpace.monitoring.health import get_health_summary
    summary = get_health_summary()
    valid_statuses = {"ok", "warning", "error"}
    for check, result in summary.items():
        assert result["status"] in valid_statuses, f"{check} has invalid status"


def test_check_db_connectivity_ok():
    """check_db_connectivity returns ok when connection succeeds."""
    from gridpace.monitoring.db_health import check_db_connectivity
    result = check_db_connectivity()
    assert result["status"] == "ok"
    assert result["value"] is True


def test_check_db_connectivity_error():
    """check_db_connectivity returns error when connection fails."""
    from gridpace.monitoring.db_health import check_db_connectivity
    with patch("gridpace.grid.storage.get_connection", side_effect=Exception("connection failed")):
        result = check_db_connectivity()
        assert result["status"] == "error"
        assert result["value"] is False


def test_check_db_size_ok(tmp_path):
    """check_db_size returns ok for small file."""
    from gridpace.monitoring.db_health import check_db_size
    small_file = tmp_path / "test.duckdb"
    small_file.write_bytes(b"x" * 1024)  # 1KB
    with patch("gridpace.monitoring.db_health.Path") as mock_path:
        mock_path.return_value = small_file
        with patch("gridpace.grid.storage.DB_PATH", small_file):
            result = check_db_size()
            assert result["status"] == "ok"


def test_check_db_size_no_file(tmp_path):
    """check_db_size returns warning when file does not exist."""
    from gridpace.monitoring.db_health import check_db_size
    with patch("gridpace.grid.storage.DB_PATH", tmp_path / "nonexistent.duckdb"):
        result = check_db_size()
        assert result["status"] == "warning"


def test_check_last_ingest_no_data():
    """check_last_ingest returns warning when no data exists."""
    from gridpace.monitoring.data_health import check_last_ingest
    with patch("gridpace.grid.storage.get_last_ingested_at", return_value=None):
        result = check_last_ingest()
        assert result["status"] == "warning"
        assert result["value"] is None


def test_check_data_gap_returns_result():
    """check_data_gap returns a valid health result."""
    from gridpace.monitoring.data_health import check_data_gap
    result = check_data_gap()
    assert result["status"] in {"ok", "warning", "error"}
    assert "message" in result
