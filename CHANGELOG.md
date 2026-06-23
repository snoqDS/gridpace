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
