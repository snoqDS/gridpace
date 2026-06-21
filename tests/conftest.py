"""
Shared test constants and fixtures for GridPace test suite.
pytest loads this file automatically before any tests run.
"""

# ISOs
TEST_ISO = "ERCOT"

# Migration constants
MIGRATION_001 = "001_create_bronze_silver_gold.sql"
EXPECTED_SCHEMAS = {"bronze", "silver", "gold"}

# Sample data sizes — must match fixtures in tests/unit/grid/conftest.py
SAMPLE_ROWS = 3
