"""
GridPace health monitoring main entry point.
Imports from db_health.py and data_health.py and exposes a unified summary.

Health result structure defined in monitoring/types.py.
All check functions return HealthResult dicts.

Dashboard usage:
    from gridpace.monitoring.health import get_health_summary
    summary = get_health_summary()
    for check_name, result in summary.items():
        # result["status"] drives color coding
        # result["message"] drives display text
"""

from gridpace.monitoring.data_health import (
    check_data_gap,
    check_last_ingest,
    check_row_counts,
)
from gridpace.monitoring.db_health import (
    check_db_connectivity,
    check_db_size,
    check_migrations,
)
from gridpace.monitoring.types import HealthResult


def get_health_summary() -> dict[str, HealthResult]:
    """
    Run all health checks and return a unified summary.
    Called by the dashboard sidebar to display system health.

    Returns:
        dict mapping check name to HealthResult
    """
    return {
        "db_connectivity": check_db_connectivity(),
        "db_size": check_db_size(),
        "migrations": check_migrations(),
        "last_ingest": check_last_ingest(),
        "row_counts": check_row_counts(),
        "data_gap": check_data_gap(),
    }
