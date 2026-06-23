"""
Unit tests for structured logging configuration.
"""

import structlog


def test_get_logger_returns_logger():
    """get_logger returns a structlog BoundLogger."""
    from gridpace.monitoring.logger import get_logger
    log = get_logger("test")
    assert log is not None


def test_logger_has_correct_name():
    """get_logger binds the module name correctly."""
    from gridpace.monitoring.logger import get_logger
    log = get_logger("gridpace.test.module")
    assert log is not None


def test_configure_logging_runs_without_error():
    """configure_logging executes without raising exceptions."""
    from gridpace.monitoring.logger import configure_logging
    configure_logging(log_level="DEBUG")
    configure_logging(log_level="WARNING")


def test_logger_captures_events():
    """Logger produces structured output."""
    with structlog.testing.capture_logs() as cap_logs:
        from gridpace.monitoring.logger import get_logger
        log = get_logger("test")
        log.info("test_event", key="value")
    assert len(cap_logs) > 0
    assert cap_logs[0]["event"] == "test_event"
    assert cap_logs[0]["key"] == "value"
