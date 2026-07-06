"""
Shared types for GridPace health monitoring.
Import HealthResult and make_result from here — never from health.py.
This avoids circular imports between health.py and check modules.
"""

from typing import Any, TypedDict


class HealthResult(TypedDict):
    """Standard structure for all health check results."""
    status: str   # "ok", "warning", or "error"
    message: str  # human readable description
    value: Any    # the measured value
    details: dict # optional extra context


def make_result(
    status: str,
    message: str,
    value: Any = None,
    details: dict = None,
) -> HealthResult:
    """
    Helper to build a consistent HealthResult dict.
    Use this in all health check functions.

    Args:
        status: "ok", "warning", or "error"
        message: human readable description
        value: the measured value
        details: optional extra context

    Returns:
        HealthResult dict
    """
    return {
        "status": status,
        "message": message,
        "value": value,
        "details": details or {},
    }
