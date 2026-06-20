"""
Integration tests for GridStatus live API.
These tests make real API calls and burn quota.

INTENTIONALLY SKIPPED in CI/CD pipeline.
Run manually only when verifying live API connectivity:

    uv run pytest tests/integration/ -v -m integration

In a production system with higher API tier, remove the skip
decorator and add to CI pipeline as a scheduled nightly job.
"""

import pandas as pd
import pytest

# Mark all tests in this file as integration tests
# These are skipped in standard CI runs
pytestmark = pytest.mark.skip(reason="Integration tests skipped in CI — run manually to verify live API")


def test_live_ercot_lmp():
    """Fetch live LMP data from ERCOT API."""
    from unittest.mock import patch

    from gridpace.grid.clients.gridstatus import get_lmp

    live_config = {
        "ingestion": {
            "dry_run": False,
            "default_row_limit": 5,
        },
        "isos": ["ERCOT", "CAISO", "PJM"],
    }

    with patch("gridpace.grid.clients.gridstatus.app_config", live_config):
        df = get_lmp("ERCOT")

    assert isinstance(df, pd.DataFrame)
    assert len(df) > 0
    assert "LMP" in df.columns or "lmp" in df.columns.str.lower().tolist()


def test_live_ercot_fuel_mix():
    """Fetch live fuel mix data from ERCOT API."""
    from unittest.mock import patch

    from gridpace.grid.clients.gridstatus import get_fuel_mix

    live_config = {
        "ingestion": {
            "dry_run": False,
            "default_row_limit": 5,
        },
        "isos": ["ERCOT", "CAISO", "PJM"],
    }

    with patch("gridpace.grid.clients.gridstatus.app_config", live_config):
        df = get_fuel_mix("ERCOT")

    assert isinstance(df, pd.DataFrame)
    assert len(df) > 0

