# Changelog

All notable changes to GridPace are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [Unreleased]

## [0.1.0] - 2026-06-19

### Added
- Phase 0: Production grade repo scaffolding
- Full src layout with grid/ and intelligence/ domains
- Medallion data architecture (bronze, silver, gold)
- pydantic-settings config with LLM provider switching
- Makefile with install, lint, format, test, eval, run, mlflow, diagnostics targets
- GitHub Actions CI and deploy workflow stubs
- Apache 2.0 license
- README and CONTRIBUTING guide

## [0.2.0] - 2026-06-20

### Added
- Phase 1: GridStatus client
- grid/clients/gridstatus.py with get_lmp() and get_fuel_mix()
- dry_run mode for development without burning API quota
- config/settings.yml with poll interval and ISO list
- Mock based unit tests for GridStatus client (8 tests)
- Integration test stubs for live API (skipped in CI)
- docs/data_sources.md documenting GridStatus API usage and limits

## [0.3.0] - 2026-06-20

### Added
- Phase 1: DuckDB storage layer with medallion architecture
- grid/migrator.py custom lightweight migration runner
- grid/migrations/001_create_bronze_silver_gold.sql first migration
- bronze, silver, and gold schemas with full table definitions
- write_bronze_lmp() and write_bronze_fuel_mix() ingestion functions
- transform_to_silver_lmp() and transform_to_silver_fuel_mix() with renewable_pct computation
- compute_gold_iso_summary() hourly aggregation to gold layer
- get_last_ingested_at() and check_data_gap() for operational monitoring
- apply_retention_policy() with 90 day bronze retention
- data/archive/ folder structure for Parquet archive path
- 13 new unit tests for migrator and storage (24 total passing)
- Prefect selected for future pipeline orchestration (replaces APScheduler)

### Changed
- data/ folder restructured to data/archive/bronze/silver/gold
- config/settings.yml updated with retention.bronze_days setting

## [0.4.0] - 2026-06-21

### Added
- Phase 1: Data contracts, transformers, and validation layer
- grid/contracts/gridstatus.yml schema contract with column maps and silver column definitions
- grid/transformers/ package replacing normalizer.py
- grid/transformers/utils.py shared transformation utilities
- grid/transformers/gridstatus.py source specific transforms for LMP and fuel mix
- grid/validation.py contract enforcement between bronze and silver layers
- renewable_pct computed in transformer layer not storage layer
- market defaulting to UNKNOWN in transformer layer
- Single source of truth for silver columns in contract YAML
- 18 new tests for transformers and validation (42 total passing)

### Changed
- Pipeline is now bronze to transformer to validation to silver
- Business logic moved from storage.py to transformer layer
- Silver column definitions centralized in gridstatus.yml
- DuckDB combined DataFrame registered before SQL execution

## [0.5.0] - 2026-06-22

### Added
- Phase 1: Prefect orchestration and structured logging
- monitoring/logger.py with structlog JSON structured logging
- grid/flows.py with @flow and @task decorators for full pipeline orchestration
- Parallel ISO fetching via Prefect task futures
- Replaced all print() statements with structlog throughout codebase
- DO_NOT_TRACK and PREFECT_SERVER_ANALYTICS_ENABLED env vars to disable telemetry
- 9 new tests for flows and logger (51 total passing)

### Changed
- Pipeline now orchestrated via Prefect with retry logic on fetch tasks
- All logging standardized to structlog JSON format

## [0.6.0] - 2026-06-23

### Added
- Phase 1: Streamlit dashboard with live ISO price cards
- ui/app.py dashboard skeleton with sidebar, main content, and footer
- ui/components/iso_cards.py LMP price cards per ISO
- GridStatus attribution footer per ToS Section 4.4
- LMP price thresholds moved to config/settings.yml
- dashboard cache_ttl_seconds and refresh_interval_seconds in config
- make run launches dashboard at localhost:8501
- 5 new UI tests, 56 total passing

### Changed
- config/settings.yml updated with dashboard and thresholds sections

## [0.7.0] - 2026-06-24

### Added
- Phase 1: Anomaly detection, generation mix charts, seed script
- intelligence/detection/anomaly.py with z-score statistical baselines per ISO
- Five status levels (grey/green/yellow/red/critical) driven by config thresholds
- scripts/seed_db.py contract-driven synthetic data generator
- Migration 002 adds fuel mix columns to gold.iso_summary
- Donut charts per ISO showing fuel mix breakdown
- Tab structure in dashboard (Live Conditions, Price Analytics, Nodal Analysis, Correlations)
- 48-hour min/max range in ISO cards
- Cache auto-invalidation on schema mismatch
- 19 new tests (75 total passing)

### Changed
- load_iso_summary() queries 48h min/max from gold history
- ISO cards show anomaly status indicators with z-scores
- Migrator tests now dynamic — no hardcoded migration counts or names
- MIGRATION_001 constant removed from test conftest

## [0.8.0] - 2026-06-24

### Added
- pip-audit dependency vulnerability scanning in CI
- docs/security.md vulnerability tracking log with severity levels
- Security audit step in GitHub Actions CI pipeline

### Changed
- Removed mlflow 1.27.0 (73 CVEs, pandas>=3 conflict) — will re-add in Phase 3
- Updated langsmith 0.8.17 → 0.9.2 (1 CVE resolved)
- Updated pydantic-settings 2.14.1 → 2.14.2 (1 CVE resolved)
- docs/architecture.md references security.md

## [0.9.0] - 2026-06-27

### Added
- Price Analytics tab with interactive date range slider (UTC)
- LMP price histogram with grouped bars per ISO
- Cumulative distribution function (CDF) chart overlaid per ISO
- Box plots per ISO showing median, IQR, whiskers, outliers
- Price spread chart (Q0.75 minus Q0.25) per ISO with metrics
- Generation mix time series stacked bar charts per ISO
- ISO timezone mapping for local time display on cards
- seed-week Makefile target for 168 hours of synthetic data
- load_iso_summary_history() for full history with fuel columns
- 4 new tests (79 total passing)

### Changed
- ISO cards show local time window per ISO timezone
- Min/Max labels include lookback hours for clarity
- Current LMP and Renewable labeled as latest hour
- All Price Analytics charts controlled by single date range slider
- load_iso_history() and load_iso_summary_history() fetch all available history
- seed default_hours updated to 168 in config/settings.yml

## [0.10.0] - 2026-07-06

### Added
- monitoring/health.py unified health summary entry point
- monitoring/db_health.py DB connectivity, file size, migration checks
- monitoring/data_health.py last ingest, row counts, data gap checks
- monitoring/types.py HealthResult TypedDict and make_result helper
- System Health section in dashboard sidebar with color-coded status
- health thresholds in config/settings.yml
- 12 new health tests (91 total passing)

### Changed
- poll_interval_minutes updated from 120 to 5 in config/settings.yml
- Dashboard caption and footer read poll interval from config
- docs updated to reflect gridstatus open-source library and 5-phase roadmap

## [0.11.0] - 2026-07-11

### Added
- 9 ISO support: ERCOT, CAISO, MISO, SPP, NYISO, ISONE, IESO, AESO, PJM
- PJM graceful degradation when PJM_API_KEY not set
- ISO_CLASSES mapping in gridstatus client with per-ISO constructor kwargs
- SAMPLE_LMP now includes Market=SYNTHETIC for synthetic data detection
- PJM_API_KEY added to .env.example with registration instructions
- docs/data_sources.md ISO-specific requirements section
- seed config updated with lmp_params and fuel_mix for all 9 ISOs
- 5 new client tests, 96 total passing

### Changed
- GRIDSTATUS_API_KEY removed from .env.example — open-source library needs no key
- flows.py skips None results from fetch tasks gracefully
- docs updated to reflect 9 ISO support throughout

## [0.12.0] - 2026-07-11

### Added
- ISO selector UI in sidebar with ON/OFF checkboxes for all 9 ISOs
- Default selection: ERCOT, CAISO, MISO, ISONE
- All tabs (Live Conditions, Price Analytics) filter dynamically by selected ISOs
- session_state stores selected ISO list for cross-tab consistency

## [0.13.0] - 2026-07-12

### Added
- storage.py get_layer_sizes() — row counts and DB file size per layer
- storage.py export_bronze_to_parquet() — export aged-off bronze to local Parquet
- storage.py apply_size_based_retention() — size-based age-off with Parquet export
- flows.py size_retention_task() — runs size check on every pipeline execution
- scripts/backfill_events.py — gold NULL backfill and historical data backfill
- make backfill and make backfill-history Makefile targets
- data/archive/bronze|silver|gold directories with .gitkeep
- config/settings.yml storage section with size caps and archive path
- 5 new retention tests, 103 total passing

### Changed
- apply_retention_policy() now complemented by size-based retention
- Path imported in storage.py for archive path handling

## [0.14.0] - 2026-07-12

### Added
- Health tab in dashboard with 6 monitoring domains:
  Data Freshness, Data Quality, Storage, Pipeline Health, System, ISO Coverage
- Sidebar System Health shows affected domain names not just count
- Data summary caption on Price Analytics tab (date range, rows, ISOs)
- health_tab.py component module

### Changed
- Sidebar health section simplified to domain-level summary
- Full health details moved to Health tab
