"""
Unit tests for anomaly detection logic.
Tests statistical baseline computation, z-score calculation, and status mapping.

Scope: pure detection logic only — no UI, no database, no Streamlit.
UI display of anomaly results is tested in tests/unit/test_ui.py.
"""

import pandas as pd
import pytest

from tests.conftest import TEST_ISO


@pytest.fixture
def sample_history_df():
    """Sample gold ISO summary history with enough data points for baseline."""
    return pd.DataFrame({
        "iso": [TEST_ISO] * 10,
        "window_start": pd.date_range("2026-01-01", periods=10, freq="h", tz="UTC"),
        "avg_lmp": [30.0, 32.0, 28.0, 35.0, 31.0, 33.0, 29.0, 34.0, 30.0, 32.0],
    })


@pytest.fixture
def sample_current_df():
    """Sample gold ISO summary current snapshot."""
    return pd.DataFrame({
        "iso": [TEST_ISO],
        "window_start": pd.date_range("2026-01-01 10:00", periods=1, freq="h", tz="UTC"),
        "avg_lmp": [31.0],
    })


def test_compute_iso_baseline_returns_dict(sample_history_df):
    """compute_iso_baseline returns a dict with expected keys."""
    from gridpace.intelligence.detection.anomaly import compute_iso_baseline
    result = compute_iso_baseline(sample_history_df, TEST_ISO)
    assert result is not None
    assert "mean" in result
    assert "std" in result
    assert "count" in result
    assert "q25" in result
    assert "q75" in result
    assert "spread" in result


def test_compute_iso_baseline_correct_values(sample_history_df):
    """compute_iso_baseline computes correct mean and count."""
    from gridpace.intelligence.detection.anomaly import compute_iso_baseline
    result = compute_iso_baseline(sample_history_df, TEST_ISO)
    assert result["count"] == 10
    assert abs(result["mean"] - 31.4) < 0.1


def test_compute_iso_baseline_returns_none_insufficient_data():
    """compute_iso_baseline returns None when data points below minimum."""
    from gridpace.intelligence.detection.anomaly import compute_iso_baseline
    df = pd.DataFrame({
        "iso": [TEST_ISO] * 2,
        "avg_lmp": [30.0, 32.0],
    })
    result = compute_iso_baseline(df, TEST_ISO)
    assert result is None


def test_compute_z_score_normal():
    """compute_z_score returns zero for value at mean."""
    from gridpace.intelligence.detection.anomaly import compute_z_score
    baseline = {"mean": 30.0, "std": 5.0}
    assert compute_z_score(30.0, baseline) == 0.0


def test_compute_z_score_positive():
    """compute_z_score returns positive for value above mean."""
    from gridpace.intelligence.detection.anomaly import compute_z_score
    baseline = {"mean": 30.0, "std": 5.0}
    assert compute_z_score(40.0, baseline) == 2.0


def test_compute_z_score_zero_std():
    """compute_z_score returns None when std is zero."""
    from gridpace.intelligence.detection.anomaly import compute_z_score
    baseline = {"mean": 30.0, "std": 0.0}
    assert compute_z_score(30.0, baseline) is None


def test_get_anomaly_status_grey():
    """get_anomaly_status returns grey for None z_score."""
    from gridpace.intelligence.detection.anomaly import get_anomaly_status
    assert get_anomaly_status(None) == "grey"


def test_get_anomaly_status_green():
    """get_anomaly_status returns green for low z_score."""
    from gridpace.intelligence.detection.anomaly import get_anomaly_status
    assert get_anomaly_status(0.5) == "green"


def test_get_anomaly_status_yellow():
    """get_anomaly_status returns yellow for moderate z_score."""
    from gridpace.intelligence.detection.anomaly import get_anomaly_status
    assert get_anomaly_status(1.5) == "yellow"


def test_get_anomaly_status_red():
    """get_anomaly_status returns red for high z_score."""
    from gridpace.intelligence.detection.anomaly import get_anomaly_status
    assert get_anomaly_status(2.5) == "red"


def test_get_anomaly_status_critical():
    """get_anomaly_status returns critical for extreme z_score."""
    from gridpace.intelligence.detection.anomaly import get_anomaly_status
    assert get_anomaly_status(3.5) == "critical"


def test_detect_anomalies_returns_dict(sample_history_df, sample_current_df):
    """detect_anomalies returns dict keyed by ISO."""
    from gridpace.intelligence.detection.anomaly import detect_anomalies
    result = detect_anomalies(sample_history_df, sample_current_df)
    assert isinstance(result, dict)
    assert TEST_ISO in result


def test_detect_anomalies_has_expected_keys(sample_history_df, sample_current_df):
    """detect_anomalies result has expected keys per ISO."""
    from gridpace.intelligence.detection.anomaly import detect_anomalies
    result = detect_anomalies(sample_history_df, sample_current_df)
    iso_result = result[TEST_ISO]
    assert "status" in iso_result
    assert "z_score" in iso_result
    assert "current_lmp" in iso_result


def test_detect_anomalies_grey_when_insufficient_data(sample_current_df):
    """detect_anomalies returns grey status when history is too short."""
    from gridpace.intelligence.detection.anomaly import detect_anomalies
    tiny_history = pd.DataFrame({
        "iso": [TEST_ISO] * 2,
        "avg_lmp": [30.0, 32.0],
        "window_start": pd.date_range("2026-01-01", periods=2, freq="h", tz="UTC"),
    })
    result = detect_anomalies(tiny_history, sample_current_df)
    assert result[TEST_ISO]["status"] == "grey"
