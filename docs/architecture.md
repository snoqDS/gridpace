# Architecture

## Overview

GridPace is a real time grid intelligence platform built across five phases.

For setup instructions see docs/setup.md.

## Phase 0: Repo Scaffolding (Complete)

Production grade Python project structure with uv, Ruff, pytest, GitHub Actions CI, and Apache 2.0 license.

## Phase 1: Live Grid Dashboard (In Progress)

### Data Flow

Current state:

    GridStatus API
          |
          v
    grid/clients/gridstatus.py       (fetch, dry_run mode available)
          |
          v
    grid/storage.py                  (DuckDB bronze layer)
          |
          v
    grid/transformers/gridstatus.py  (column mapping, normalization, business logic)
          |
          v
    grid/validation.py               (schema contract check)
          |
          v
    grid/storage.py                  (silver and gold transforms)
          |
          v
    grid/flows.py                    (Prefect orchestration, parallel ISO fetching)
          |
          v
    intelligence/detection/anomaly.py (z-score statistical baselines per ISO)
          |
          v
    ui/app.py                        (Streamlit dashboard, 5 tabs, ISO selector,
                                      sidebar health summary)
          |
          ├── ui/components/iso_cards.py    (Live Conditions — price cards, donuts)
          ├── ui/components/price_charts.py (Price Analytics — histogram, CDF, box plots)
          └── ui/components/health_tab.py   (Health tab — 6 monitoring domains)

Target state (full pipeline):

    GridStatus API
          |
          v
    grid/clients/gridstatus.py       (fetch)
          |
          v
    grid/validation.py               (schema contract check)
          |
          v
    grid/storage.py                  (DuckDB bronze layer)
          |
          v
    grid/storage.py                  (silver and gold transforms)
          |
          v
    intelligence/agents/graph.py     (LangGraph narrative agent, Phase 2)
          |
          v
    intelligence/retrieval/          (historical analog search, Phase 3)
          |
          v
    ui/app.py                        (Streamlit dashboard, tabs, ISO cards, donuts,
                                      Price Analytics with histogram/CDF/box plots/spread,
                                      generation mix time series, date range slider)

### Key Decisions

Poll interval set to 5 minutes for local real-time system. Configurable in config/settings.yml.
gridstatus open-source library pulls directly from ISO public portals with no request limits.
dry_run mode returns sample data during development. No live ISO API calls are made.
DuckDB serves as the local analytical warehouse. Dashboard reads from DuckDB, not live API.
Integration tests skipped in CI to avoid live ISO API calls during automated builds.
Run manually to verify live connectivity.

Polling resolution: GridPace uses the gridstatus open-source library (version
0.34.0) which pulls data directly from ISO public portals (CAISO OASIS, ERCOT
public API, PJM Data Miner) with no request limits. This is distinct from the
paid gridstatusio API which has a 250 request/month free tier limit. The local
real-time system polls every 5 minutes, matching native ISO SCED resolution.
Price spikes lasting 5 minutes or longer are detectable at this resolution.

API quota management: gridstatus open-source library requires no quota
tracking. If migrating to gridstatusio paid API (250 requests/month free
tier), add usage monitoring to scripts/diagnostics.py and alert thresholds
to config/settings.yml. See docs/data_sources.md for API comparison.

Pipeline orchestration: Prefect @flow and @task decorators wrap existing pipeline
functions. Tasks retry twice on failure with 30-second delays. ISOs fetch in
parallel via task futures. structlog handles all logging throughout the pipeline.
Tasks tested via .fn() which bypasses Prefect context and calls the underlying
Python function directly.

Anomaly detection: Statistical z-score baselines computed per ISO from gold layer
history. Requires minimum 5 data points before producing a status. Returns grey
status when insufficient history exists. Five status levels: grey, green, yellow,
red, critical. Thresholds configured in config/settings.yml under anomaly.
Designed for sustained anomalies only. At 5-minute polling resolution, spikes
lasting 5 minutes or longer are detectable.

Dashboard analytics: Price Analytics tab provides interactive price distribution
analysis (histogram, CDF, box plots, spread) and generation mix time series.
All charts controlled by a single UTC date range slider. ISO cards display
local time per ISO timezone for operator readability.

Health monitoring: Three-module structure in monitoring/ — types.py defines
HealthResult structure, db_health.py covers connectivity and migrations,
data_health.py covers ingestion and data quality. get_health_summary() in
health.py aggregates all checks. Dashboard sidebar displays live status with
color-coded indicators. Thresholds configured in config/settings.yml under health:

ISO support: Nine ISOs supported (ERCOT, CAISO, MISO, SPP, NYISO, ISONE, IESO,
AESO, PJM). PJM requires a free API key from apiportal.pjm.com due to Data Miner 2
authentication requirements. All other ISOs pull directly from public portals with
no key required. PJM is skipped gracefully when PJM_API_KEY is not set in .env.
See docs/data_sources.md for ISO-specific registration requirements.

ISO selector: Dashboard sidebar provides ON/OFF checkboxes for all 9 supported
ISOs. Default selection is ERCOT, CAISO, MISO, ISONE. All charts and cards
filter dynamically. Selected ISOs stored in Streamlit session_state.

Storage management: Size-based retention complements time-based retention.
apply_size_based_retention() checks total DB file size against configurable
caps in config/settings.yml under storage: When bronze cap is exceeded,
oldest 50% of bronze data exports to data/archive/bronze/ as Parquet before
deletion. Silver and gold are smaller and managed by time-based retention only.
Cloudflare R2 upload path documented as future production archive destination.

Health monitoring UI: Sidebar shows traffic light status and affected domain
names only. Full details in Health tab covering Data Freshness, Data Quality,
Storage, Pipeline Health, System, and ISO Coverage. Domain-level sidebar keeps
cognitive load low while Health tab provides operator-grade detail.

## Phase 2: Agentic Narrative Layer (Planned)

LangGraph state machine with observe, diagnose, explain, and publish nodes.
Tools call GridStatus, WattTime, and Ember APIs.
Narrative generation via configurable LLM provider (Ollama, HuggingFace, or Anthropic).
Produces plain-English situation reports explaining current grid conditions
to operators and market participants.

## Phase 3: Historical Analog Engine (Planned)

FAISS vector store over historical grid events with sentence transformer embeddings.
Retrieval augmented generation over a time series event database.
Historical events sourced from EIA, GridStatus history, and Catalyst Cooperative PUDL.
Enables contextual comparisons such as identifying that current conditions
resemble a prior event where prices spiked significantly within hours.

## Phase 4: Real-Time Dispatch Support (Planned)

Designed for battery storage operators making short-term dispatch decisions.
Node-level LMP requires specifying specific pricing nodes in gridstatus queries.
5-minute resolution is already available via the open-source library.

    Node-level LMP at key pricing hubs (ERCOT HB_NORTH/SOUTH/WEST/HOUSTON,
    CAISO SP15/NP15/ZP26, PJM Western/Eastern Hub)
    Day-ahead vs real-time price spread
    4-hour ahead renewable generation forecast
    Ancillary services prices (ERCOT ECRS, CAISO REGUP/REGDN)
    Reserve margin alerts
    Marginal carbon emissions via WattTime integration
    Negative price detection for optimal battery charging windows

## Phase 5: Long-Term Project Developer Analysis (Planned)

Designed for developers and investors evaluating storage and renewable projects.

    Merchant revenue stacking analysis
    Capacity factor projections by technology and region
    IRA incentive optimization (ITC, PTC, storage adder)
    Interconnection queue analysis
    Multi-year price forecasting

## Tech Stack

    Layer                  Technology
    --------------------   ---------------------------
    Package manager        uv
    Language               Python 3.11
    Data ingestion         gridstatus 0.34.0 (open-source, 9 ISOs, no request limits)
    Storage                DuckDB (bronze/silver/gold)
    Scheduling             Prefect (pipeline orchestration)
    Agent framework        LangGraph 1.0 (Phase 2)
    Vector store           FAISS + sentence-transformers (Phase 3)
    LLM providers          Ollama, HuggingFace, Anthropic (Phase 2)
    Dashboard              Streamlit
    Optimization           Pyomo + HiGHS
    Logging                structlog
    Linting                Ruff
    Testing                pytest
    CI/CD                  GitHub Actions

## Configuration

All secrets loaded from .env via pydantic-settings.
Static config (ISOs, poll interval, dry_run) in config/settings.yml.
LLM provider switchable via LLM_PROVIDER in .env.

## Database Migrations

GridPace uses a custom lightweight migration runner rather than Alembic or Flyway.

Rationale: DuckDB's SQLAlchemy support has known rough edges making Alembic unreliable.
A simple custom runner gives full control with zero compatibility issues.

How it works:

    1. On startup, migrator.py checks for a _migrations tracking table
    2. Creates it if it does not exist
    3. Scans src/gridpace/grid/migrations/ for numbered SQL files in order
    4. Runs any file not already recorded in _migrations
    5. Records each applied migration with a timestamp
    6. Safe to call on every app startup — fully idempotent

Adding a new migration:

    1. Create a new SQL file in src/gridpace/grid/migrations/
    2. Name it NNN_description.sql where NNN is the next number
    3. Run the migrator — it applies only the new file

In a team environment with a standard relational database, Alembic would be
the preferred choice for schema versioning and auto-generation from models.

## Testing Strategy

GridPace uses a three-layer test structure:

    tests/
    ├── conftest.py              # shared constants and config for all tests
    ├── unit/
    │   ├── grid/
    │   │   └── conftest.py     # shared fixtures for grid unit tests
    │   └── ...
    └── integration/
        └── ...

Shared constants live in tests/conftest.py:
    TEST_ISO, SAMPLE_ROWS, EXPECTED_SCHEMAS

Test scope boundaries:
    test_anomaly.py    statistical detection logic only, no UI or DB dependencies
    test_ui.py         display layer, cache behavior, schema validation, health tab imports
    test_flows.py      Prefect task behavior with mocked dependencies
    test_storage.py          DuckDB read/write with isolated temp databases
    test_storage_retention.py size-based retention, Parquet export, layer sizes
    test_transformers.py   pure data transformation functions
    test_validation.py     contract enforcement logic
    test_health.py (grid/) — health checks requiring initialized DB fixtures
    test_health.py (unit/) — health check logic with mocked dependencies

Flow tasks tested via .fn() to bypass Prefect context requirements.
Integration tests skipped in CI and run manually to verify live API connectivity.

Shared fixtures live in tests/unit/grid/conftest.py:
    temp_db, initialized_db, sample_lmp_df, sample_fuel_mix_df

pytest loads conftest.py files automatically. No imports needed in test files
for fixtures. Constants are imported explicitly from tests.conftest.

Adding a new test domain (e.g. intelligence, monitoring):
    1. Create tests/unit/<domain>/conftest.py with domain specific fixtures
    2. Add domain specific constants to tests/conftest.py if shared
    3. Write test files in tests/unit/<domain>/

Unit tests use mocked dependencies and temporary databases.
Integration tests hit live APIs and are skipped in CI by default.
Run integration tests manually: uv run pytest tests/integration/ -v

## Security

See docs/security.md for the full vulnerability tracking log and dependency
update policy. pip-audit runs in CI on every push.

### API Key Management

All secrets loaded from .env via pydantic-settings. Never committed to Git.
detect-secrets runs as a pre-commit hook to block accidental key commits.
See .env.example for required keys.

### Dependency Scanning

pip-audit runs in CI on every push to check for known CVEs in dependencies.
Build fails if any vulnerability is found. See docs/security.md for the
vulnerability tracking log and remediation policy.

### Agent Security Model (Phase 2)

GridPace agents operate under two security constraints by design:

Level 1: Tool allowlisting
    LangGraph enforces that agents can only call explicitly registered tools.
    No arbitrary function execution is possible.

Level 2: Read-only external calls
    All agent tools fetch data only. No tools write, post, delete, or modify
    external systems. Low attack surface by design.

Level 3: No code execution tools
    GridPace agents do not have access to a Python REPL or shell execution tool.
    This eliminates the primary risk vector in agentic systems.

Prompt injection risk is mitigated by structured tool outputs rather than
passing raw external text directly to the LLM reasoning loop.

## Future Considerations

Scale out storage: DuckDB handles gigabytes easily on a single machine.
When bronze data exceeds 90 days, aged off data exports to S3 as Parquet files.
DuckDB reads S3 Parquet natively so historical queries require no code changes.
DynamoDB was explicitly ruled out as it is designed for transactional workloads,
not the analytical time series queries GridPace requires.

Pipeline orchestration: Prefect handles scheduled data collection with retries,
observability, and a monitoring dashboard. Prefect Cloud free tier enables
always-on collection independent of local machine uptime.

Schema versioning: Migrate to Alembic when the schema stabilizes and if the
database backend changes to PostgreSQL or another SQLAlchemy compatible database.

Auto generated documentation: Generate docs from code using Sphinx or mkdocs
rather than maintaining markdown files manually.

Infrastructure as code: Cloud resources and deployment configuration should be
defined in code using Terraform or Pulumi for reproducible environment setup
across dev, staging, and production.

Production deployment: Before any production deployment, fill in the Dockerfile
and docker-compose.yml placeholders. Production deployments should run in
isolated containers with explicit network rules. A dedicated Prefect worker
running on a cloud VM ensures always-on data collection independent of local
machine uptime. See docs/security.md for the security model that governs
production deployments.

MLflow: Planned for Phase 3 experiment tracking. Removed from Phase 1
dependencies due to incompatibility with pandas>=3. Will be re-added when
pandas compatibility is resolved.

Storage management: Configurable size caps per medallion layer (bronze, silver, gold)
with both time-based and size-based age-off triggers. Aged-off bronze exports to
Parquet for archival. Dashboard sidebar shows DB size per layer with alerts at cap.

Deployment modes: Local real-time system polls every 5 minutes with full 9-ISO
coverage. Public demo deployment uses Streamlit Community Cloud with seeded
historical data. Production always-on path uses Cloudflare R2 (10GB free) plus
GCP e2-micro VM for the pipeline worker.
