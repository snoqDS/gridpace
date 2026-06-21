"""
Lightweight database migration runner for GridPace.
Tracks applied migrations in a _migrations table.
Runs numbered SQL files from src/gridpace/grid/migrations/ in order.

Usage:
    from gridpace.grid.migrator import run_migrations
    run_migrations()

Adding a new migration:
    1. Create a new SQL file in src/gridpace/grid/migrations/
    2. Name it NNN_description.sql where NNN is the next number
    3. Run run_migrations() -- it will apply only the new file
"""

from pathlib import Path

import duckdb

from gridpace.config import ROOT

MIGRATIONS_DIR = Path(__file__).parent / "migrations"
DB_PATH = ROOT / "data" / "gridpace.duckdb"


def get_connection() -> duckdb.DuckDBPyConnection:
    """Return a connection to the GridPace DuckDB database."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    return duckdb.connect(str(DB_PATH))


def _ensure_migrations_table(conn: duckdb.DuckDBPyConnection) -> None:
    """Create the _migrations tracking table if it does not exist."""
    conn.execute("""
        CREATE TABLE IF NOT EXISTS _migrations (
            id          VARCHAR PRIMARY KEY,
            applied_at  TIMESTAMPTZ DEFAULT now()
        )
    """)


def _get_applied_migrations(conn: duckdb.DuckDBPyConnection) -> set:
    """Return set of migration IDs that have already been applied."""
    result = conn.execute("SELECT id FROM _migrations").fetchall()
    return {row[0] for row in result}


def _get_pending_migrations(applied: set) -> list:
    """Return sorted list of migration files not yet applied."""
    all_files = sorted(MIGRATIONS_DIR.glob("*.sql"))
    return [f for f in all_files if f.name not in applied]


def run_migrations() -> None:
    """
    Run all pending migrations in order.
    Safe to call on every app startup.
    """
    conn = get_connection()
    _ensure_migrations_table(conn)

    applied = _get_applied_migrations(conn)
    pending = _get_pending_migrations(applied)

    if not pending:
        print("Database is up to date. No migrations to run.")
        conn.close()
        return

    for migration_file in pending:
        print(f"Applying migration: {migration_file.name}")
        sql = migration_file.read_text()
        conn.execute(sql)
        conn.execute(
            "INSERT INTO _migrations (id) VALUES (?)",
            [migration_file.name]
        )
        print(f"Applied: {migration_file.name}")

    conn.close()
    print(f"Migrations complete. {len(pending)} migration(s) applied.")


if __name__ == "__main__":
    run_migrations()
