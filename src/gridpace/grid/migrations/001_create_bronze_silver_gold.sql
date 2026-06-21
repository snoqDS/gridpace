-- Migration 001: Create bronze, silver, and gold schemas and tables
-- Applied by: src/gridpace/grid/migrator.py
-- Date: 2026-06-20

CREATE SCHEMA IF NOT EXISTS bronze;
CREATE SCHEMA IF NOT EXISTS silver;
CREATE SCHEMA IF NOT EXISTS gold;

-- Bronze: raw LMP data as received from GridStatus
CREATE TABLE IF NOT EXISTS bronze.lmp (
    ingested_at     TIMESTAMPTZ DEFAULT now(),
    iso             VARCHAR,
    interval_start  TIMESTAMPTZ,
    interval_end    TIMESTAMPTZ,
    location        VARCHAR,
    location_type   VARCHAR,
    lmp             DOUBLE,
    market          VARCHAR,
    raw_json        VARCHAR
);

-- Bronze: raw fuel mix data as received from GridStatus
CREATE TABLE IF NOT EXISTS bronze.fuel_mix (
    ingested_at     TIMESTAMPTZ DEFAULT now(),
    iso             VARCHAR,
    time            TIMESTAMPTZ,
    natural_gas     DOUBLE,
    wind            DOUBLE,
    solar           DOUBLE,
    coal            DOUBLE,
    nuclear         DOUBLE,
    other           DOUBLE,
    raw_json        VARCHAR
);

-- Silver: cleaned and normalized LMP
CREATE TABLE IF NOT EXISTS silver.lmp (
    iso             VARCHAR,
    interval_start  TIMESTAMPTZ,
    location        VARCHAR,
    location_type   VARCHAR,
    lmp             DOUBLE,
    market          VARCHAR,
    processed_at    TIMESTAMPTZ DEFAULT now()
);

-- Silver: cleaned and normalized fuel mix
CREATE TABLE IF NOT EXISTS silver.fuel_mix (
    iso             VARCHAR,
    time            TIMESTAMPTZ,
    natural_gas     DOUBLE,
    wind            DOUBLE,
    solar           DOUBLE,
    coal            DOUBLE,
    nuclear         DOUBLE,
    other           DOUBLE,
    renewable_pct   DOUBLE,
    processed_at    TIMESTAMPTZ DEFAULT now()
);

-- Gold: aggregated ISO summary metrics
CREATE TABLE IF NOT EXISTS gold.iso_summary (
    iso             VARCHAR,
    window_start    TIMESTAMPTZ,
    window_end      TIMESTAMPTZ,
    avg_lmp         DOUBLE,
    max_lmp         DOUBLE,
    min_lmp         DOUBLE,
    renewable_pct   DOUBLE,
    computed_at     TIMESTAMPTZ DEFAULT now()
);
