"""
Database health checks for GridPace.
Covers connectivity, file size, and migration status.

All functions return HealthResult dicts — see monitoring/health.py for structure.
Thresholds configured in config/settings.yml under health:
    db_size_warning_gb — warn when DB file exceeds this size
    db_size_error_gb   — error when DB file exceeds this size
"""

from pathlib import Path

from gridpace.config import app_config
from gridpace.monitoring.logger import get_logger
from gridpace.monitoring.types import HealthResult, make_result

log = get_logger(__name__)

# Thresholds loaded from config — never hardcode here
_health_cfg = app_config.get("health", {})
DB_SIZE_WARNING_GB = _health_cfg.get("db_size_warning_gb", 1.0)
DB_SIZE_ERROR_GB = _health_cfg.get("db_size_error_gb", 2.0)

log = get_logger(__name__)


def check_db_connectivity() -> HealthResult:
    """
    Check DuckDB connectivity.
    Attempts to connect and run a simple query.
    """
    try:
        from gridpace.grid.storage import get_connection
        conn = get_connection()
        conn.execute("SELECT 1").fetchone()
        conn.close()
        log.info("db_connectivity_ok")
        return make_result(
            status="ok",
            message="DuckDB connection successful",
            value=True,
        )
    except Exception as e:
        log.warning("db_connectivity_failed", error=str(e))
        return make_result(
            status="error",
            message=f"DuckDB connection failed: {e}",
            value=False,
        )


def check_db_size() -> HealthResult:
    """
    Check DuckDB file size on disk.
    """
    try:
        from gridpace.grid.storage import DB_PATH
        path = Path(DB_PATH)

        if not path.exists():
            return make_result(
                status="warning",
                message="DuckDB file does not exist yet",
                value=0,
            )

        size_bytes = path.stat().st_size
        size_mb = round(size_bytes / 1024 / 1024, 1)
        size_gb = round(size_bytes / 1024 / 1024 / 1024, 2)

        if size_gb >= DB_SIZE_ERROR_GB:
            status = "error"
            message = f"DB size critical: {size_gb}GB — consider aging off data"
        elif size_gb >= DB_SIZE_WARNING_GB:
            status = "warning"
            message = f"DB size elevated: {size_gb}GB"
        else:
            status = "ok"
            message = f"DB size: {size_mb}MB"

        log.info("db_size_checked", size_mb=size_mb)
        return make_result(
            status=status,
            message=message,
            value=size_mb,
            details={"size_bytes": size_bytes, "size_gb": size_gb},
        )
    except Exception as e:
        log.warning("db_size_check_failed", error=str(e))
        return make_result(
            status="error",
            message=f"DB size check failed: {e}",
            value=None,
        )


def check_migrations() -> HealthResult:
    """
    Check that all migrations have been applied.
    Compares applied migrations against available SQL files.
    """
    try:
        from gridpace.grid.migrator import (
            MIGRATIONS_DIR,
            _ensure_migrations_table,
            _get_applied_migrations,
            _get_pending_migrations,
        )
        from gridpace.grid.storage import get_connection

        conn = get_connection()
        _ensure_migrations_table(conn)
        applied = _get_applied_migrations(conn)
        pending = _get_pending_migrations(applied)
        conn.close()

        total = len(list(MIGRATIONS_DIR.glob("*.sql")))

        if pending:
            return make_result(
                status="warning",
                message=f"{len(pending)} pending migration(s) — run migrations",
                value=len(applied),
                details={"pending": [m.name for m in pending], "total": total},
            )

        return make_result(
            status="ok",
            message=f"All {total} migration(s) applied",
            value=total,
            details={"applied": list(applied)},
        )
    except Exception as e:
        log.warning("migrations_check_failed", error=str(e))
        return make_result(
            status="error",
            message=f"Migration check failed: {e}",
            value=None,
        )
