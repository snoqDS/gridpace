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
- Phase 1 Session 1: GridStatus client
- grid/clients/gridstatus.py with get_lmp() and get_fuel_mix()
- dry_run mode for development without burning API quota
- config/settings.yml with poll interval and ISO list
- Mock based unit tests for GridStatus client (8 tests)
- Integration test stubs for live API (skipped in CI)
- docs/data_sources.md documenting GridStatus API usage and limits

