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
    ui/app.py                        (Streamlit dashboard, tabs, ISO cards, donuts)

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
    ui/app.py                        (Streamlit dashboard)

### Key Decisions

Poll interval set to 120 minutes on free tier. Configurable in config/settings.yml.
dry_run mode returns sample data during development. No API quota consumed.
DuckDB serves as the local analytical warehouse. Dashboard reads from DuckDB, not live API.
Integration tests skipped in CI to preserve API quota. Run manually to verify live connectivity.

Polling resolution: GridStatus free tier allows 250 API requests per month.
To stay within this limit, the pipeline polls every 120 minutes by default,
configurable in config/settings.yml. Price spikes typically last 5 to 30
minutes and will not be captured at this resolution. Anomaly detection is
designed for sustained conditions only, not transient price spikes.
Production deployment with a paid GridStatus tier would enable 5-minute
polling and real-time spike detection. This is a documented constraint,
not a design flaw.

Pipeline orchestration: Prefect @flow and @task decorators wrap existing pipeline
functions. Tasks retry twice on failure with 30-second delays. ISOs fetch in
parallel via task futures. structlog handles all logging throughout the pipeline.
Tasks tested via .fn() which bypasses Prefect context and calls the underlying
Python function directly.

Anomaly detection: Statistical z-score baselines computed per ISO from gold layer
history. Requires minimum 5 data points before producing a status. Returns grey
status when insufficient history exists. Five status levels: grey, green, yellow,
red, critical. Thresholds configured in config/settings.yml under anomaly.
Designed for sustained anomalies only as 2-hour polling resolution cannot detect
transient price spikes.

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
Requires a paid GridStatus tier for node-level LMP and 5-minute resolution.

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
    Data ingestion         gridstatus, httpx, requests
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
    test_ui.py         display layer, cache behavior, schema validation
    test_flows.py      Prefect task behavior with mocked dependencies
    test_storage.py    DuckDB read/write with isolated temp databases
    test_transformers.py   pure data transformation functions
    test_validation.py     contract enforcement logic

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
