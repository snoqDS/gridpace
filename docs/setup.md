# Setup Guide

This guide walks through setting up GridPace from scratch on a local machine.

## Prerequisites

- Python 3.11 or higher
- uv package manager
- Git
- A modern Mac, Linux, or Windows (WSL) machine

### Install uv

    curl -LsSf https://astral.sh/uv/install.sh | sh

Verify:

    uv --version

## Clone and Install

    git clone https://github.com/snoqDS/gridpace.git
    cd gridpace
    uv sync

This creates a virtual environment at .venv/ and installs all dependencies.
Nothing is installed to your system Python.

Verify installation:

    uv run python -c "import gridpace; print('OK')"

## API Keys

GridPace uses several free data APIs. Sign up for each before running the pipeline.

### GridStatus (required)

Real-time ISO grid data. Free tier provides 250 requests per month.

1. Sign up at https://gridstatus.io
2. Copy your API key from the dashboard

## Configure Environment

Copy the example environment file:

    cp .env.example .env

Open .env and fill in your API keys:

    GRIDSTATUS_API_KEY=your_key_here

GridStatus is the only key required for Phase 1. Additional keys will be added
as new data sources are integrated in later phases.

## Initialize the Database

Run database migrations to create the bronze, silver, and gold schemas:

    uv run python -c "from gridpace.grid.migrator import run_migrations; run_migrations()"

You should see output confirming each migration was applied.

After initializing, seed synthetic data for development:

    make seed

This generates 48 hours of synthetic LMP and fuel mix data per ISO, enabling
anomaly detection baselines and dashboard testing without consuming API quota.

To force reseed (clears existing data and regenerates):

    make reseed

## Run the Pipeline

### Dry Run (no API calls, uses sample data)

Verify the full pipeline works before using real API quota:

    uv run python -m gridpace.grid.flows

This runs the complete pipeline using sample data. No API requests are made.
Check that it completes without errors.

### Live Run (uses real API data)

To fetch real grid data, set dry_run to false in config/settings.yml:

    ingestion:
      dry_run: false

Then run the pipeline:

    uv run python -m gridpace.grid.flows

Set dry_run back to true after verifying live data is working.

## Seed Development Data

The seed script populates DuckDB with synthetic historical data for development
and testing. This enables anomaly detection baselines and dashboard testing
without consuming GridStatus API quota.

Seed parameters are configured in config/settings.yml under seed:

    seed:
      default_hours: 48
      lmp_params:
        ERCOT:
          mean: 35.0
          std: 12.0
      ...

Adjust these values to tune the synthetic data for your testing needs.

## Launch the Dashboard

    make run

This opens the GridPace dashboard at http://localhost:8501

The dashboard reads from DuckDB and shows:
- Current LMP prices per ISO with anomaly status indicators
- Fuel mix breakdown per ISO
- Renewable energy penetration
- Last updated timestamp and data window

## Run Tests

Run the full test suite:

    make test

Run linting:

    make lint

Expected output: 75 tests passing, 2 skipped (integration tests).

LLM evals are available in Phase 2 and beyond:

    make eval

## Development Workflow

The recommended workflow for making changes:

1. Create a feature branch:

    git checkout -b feat/your-feature-name

2. Make your changes.

3. Run lint and fix any issues:

    make lint

4. Run the full test suite:

    make test

5. Add tests for any new features or changed behavior.

6. If you changed the pipeline schema, run migrations and reseed:

    make reseed

7. Update CHANGELOG.md with what changed.

8. Update docs/architecture.md if architecture or key decisions changed.

9. Update docs/setup.md if setup steps changed.

10. Commit using Conventional Commits format:

    git commit -m "feat: description of change"

11. Push and verify CI is green:

    git push origin main

## Troubleshooting

### Database errors on first run

If you see schema errors, run migrations first:

    uv run python -c "from gridpace.grid.migrator import run_migrations; run_migrations()"

### Dashboard shows no data

Run the seed script first to populate the database:

    make seed

Or run the pipeline to fetch live data:

    uv run python -m gridpace.grid.flows

### API quota exceeded

GridStatus free tier allows 250 requests per month. If you exceed this:
- Set dry_run: true in config/settings.yml
- Wait until the next month for quota to reset
- Consider upgrading to a paid GridStatus tier

### Running integration tests

Integration tests hit live APIs and are skipped by default. Run manually:

    uv run pytest tests/integration/ -v
