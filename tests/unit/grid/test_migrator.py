"""
Unit tests for database migration runner.
Uses temporary DuckDB database to avoid touching production data.
"""

import duckdb

from gridpace.grid.migrator import MIGRATIONS_DIR
from tests.conftest import EXPECTED_SCHEMAS


def test_migrations_table_created(temp_db):
    """Migration runner creates _migrations tracking table."""
    from gridpace.grid.migrator import _ensure_migrations_table

    conn = duckdb.connect(str(temp_db))
    _ensure_migrations_table(conn)
    result = conn.execute(
        "SELECT COUNT(*) FROM information_schema.tables WHERE table_name = '_migrations'"
    ).fetchone()[0]
    conn.close()
    assert result == 1


def test_first_migration_applied(temp_db):
    """First migration creates bronze, silver and gold schemas."""
    from gridpace.grid.migrator import (
        _ensure_migrations_table,
        _get_applied_migrations,
        _get_pending_migrations,
    )

    conn = duckdb.connect(str(temp_db))
    _ensure_migrations_table(conn)
    applied = _get_applied_migrations(conn)
    pending = _get_pending_migrations(applied)

    for migration_file in pending:
        sql = migration_file.read_text()
        conn.execute(sql)
        conn.execute(
            "INSERT INTO _migrations (id) VALUES (?)",
            [migration_file.name]
        )

    schemas = conn.execute(
        "SELECT schema_name FROM information_schema.schemata"
    ).fetchall()
    schema_names = {s[0] for s in schemas}
    conn.close()
    assert EXPECTED_SCHEMAS.issubset(schema_names)


def test_migrations_idempotent(temp_db):
    """Running migrations twice does not duplicate entries."""
    from gridpace.grid.migrator import (
        _ensure_migrations_table,
        _get_applied_migrations,
        _get_pending_migrations,
    )

    conn = duckdb.connect(str(temp_db))
    _ensure_migrations_table(conn)

    for _ in range(2):
        applied = _get_applied_migrations(conn)
        pending = _get_pending_migrations(applied)
        for migration_file in pending:
            sql = migration_file.read_text()
            conn.execute(sql)
            conn.execute(
                "INSERT INTO _migrations (id) VALUES (?)",
                [migration_file.name]
            )

    count = conn.execute("SELECT COUNT(*) FROM _migrations").fetchone()[0]
    conn.close()
    expected = len(list(MIGRATIONS_DIR.glob("*.sql")))
    assert count == expected


def test_migration_recorded(temp_db):
    """First applied migration is recorded in _migrations table."""
    from gridpace.grid.migrator import (
        _ensure_migrations_table,
        _get_applied_migrations,
        _get_pending_migrations,
    )

    conn = duckdb.connect(str(temp_db))
    _ensure_migrations_table(conn)
    applied = _get_applied_migrations(conn)
    pending = _get_pending_migrations(applied)

    for migration_file in pending:
        sql = migration_file.read_text()
        conn.execute(sql)
        conn.execute(
            "INSERT INTO _migrations (id) VALUES (?)",
            [migration_file.name]
        )

    result = conn.execute(
        "SELECT id FROM _migrations ORDER BY applied_at LIMIT 1"
    ).fetchone()[0]
    conn.close()

    # First migration should be the lowest numbered file
    first_migration = sorted(MIGRATIONS_DIR.glob("*.sql"))[0].name
    assert result == first_migration
