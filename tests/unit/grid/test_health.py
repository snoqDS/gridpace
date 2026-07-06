"""
Health checks requiring database fixtures.
Tests that need initialized_db live here to access grid conftest fixtures.
"""



def test_check_migrations_ok(initialized_db, monkeypatch):
    """check_migrations returns ok when all migrations applied."""
    monkeypatch.setattr("gridpace.grid.storage.DB_PATH", initialized_db)
    from gridpace.monitoring.db_health import check_migrations
    result = check_migrations()
    assert result["status"] == "ok"
    assert result["value"] >= 2


def test_check_row_counts_ok(initialized_db, monkeypatch, sample_lmp_df, sample_fuel_mix_df):
    """check_row_counts returns ok when all layers populated."""
    monkeypatch.setattr("gridpace.grid.storage.DB_PATH", initialized_db)
    from gridpace.grid.storage import (
        compute_gold_iso_summary,
        transform_to_silver_fuel_mix,
        transform_to_silver_lmp,
        write_bronze_fuel_mix,
        write_bronze_lmp,
    )
    write_bronze_lmp(sample_lmp_df, "ERCOT")
    write_bronze_fuel_mix(sample_fuel_mix_df, "ERCOT")
    transform_to_silver_lmp()
    transform_to_silver_fuel_mix()
    compute_gold_iso_summary()
    from gridpace.monitoring.data_health import check_row_counts
    result = check_row_counts()
    assert result["status"] == "ok"
