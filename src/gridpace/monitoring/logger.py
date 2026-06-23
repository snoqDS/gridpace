"""
Structured logging for GridPace using structlog.
Provides a single configured logger instance for the entire application.

Usage:
    from gridpace.monitoring.logger import get_logger
    log = get_logger(__name__)
    log.info("fetch_complete", iso="ERCOT", rows=5)

Output (JSON):
    {
        "timestamp": "2026-06-21T10:00:00Z",
        "level": "info",
        "logger": "gridpace.grid.flows",
        "event": "fetch_complete",
        "iso": "ERCOT",
        "rows": 5
    }
"""

import logging
import sys

import structlog


def configure_logging(log_level: str = "INFO") -> None:
    """
    Configure structlog for the application.
    Call once at application startup.

    Args:
        log_level: logging level string e.g. 'INFO', 'DEBUG', 'WARNING'
    """
    # Configure standard library logging as the backend
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, log_level.upper(), logging.INFO),
    )

    structlog.configure(
        processors=[
            # Add log level to event dict
            structlog.stdlib.add_log_level,
            # Add logger name
            structlog.stdlib.add_logger_name,
            # Add timestamp in ISO format
            structlog.processors.TimeStamper(fmt="iso"),
            # Add caller info in debug mode
            structlog.processors.CallsiteParameterAdder(
                [
                    structlog.processors.CallsiteParameter.FILENAME,
                    structlog.processors.CallsiteParameter.LINENO,
                ]
            ),
            # Render to JSON for machine parsing
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """
    Get a configured logger for a module.

    Args:
        name: module name, typically __name__

    Returns:
        Configured structlog BoundLogger
    """
    return structlog.get_logger(name)


# Configure logging on import with default settings
# Can be reconfigured by calling configure_logging() with different settings
configure_logging()
