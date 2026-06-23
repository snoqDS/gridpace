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

GridStatus is the only key required for Phase 1. The others are used in later future phases.

## Initialize the Database

Run database migrations to create the bronze, silver, and gold schemas:

    uv run python -c "from gridpace.grid.migrator import run_migrations; run_migrations()"

You should see:

    Applying migration: 001_create_bronze_silver_gold.sql
    Applied: 001_create_bronze_silver_gold.sql
    Migrations complete. 1 migration(s) applied.

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

## Launch the Dashboard

    make run

This opens the GridPace dashboard at http://localhost:8501

The dashboard reads from DuckDB and shows:
- Current LMP prices per ISO
- Renewable energy penetration
- Last updated timestamp
- Data gap status

## Run Tests

Run the full test suite:

    make test

Run linting:

    make lint

Run LLM evals (Phase 2 and beyond):

    make eval

Expected output: 56 tests passing, 2 skipped (integration tests).

## Development Workflow

The recommended workflow for making changes:

1. Create a feature branch:

    git checkout -b feat/your-feature-name

2. Make changes and run tests:

    make lint
    make test

3. Commit using Conventional Commits format:

    git commit -m "feat: add new ISO client"

4. Push and open a pull request against main.

## Troubleshooting

### Database errors on first run

If you see schema errors, run migrations first:

    uv run python -c "from gridpace.grid.migrator import run_migrations; run_migrations()"

### Dashboard shows no data

Run the pipeline first to populate the database:

    uv run python -m gridpace.grid.flows

### API quota exceeded

GridStatus free tier allows 250 requests per month. If you exceed this:
- Set dry_run: true in config/settings.yml
- Wait until the next month for quota to reset
- Consider upgrading to a paid GridStatus tier

### Running integration tests

Integration tests hit live APIs and are skipped by default. Run manually:

    uv run pytest tests/integration/ -v
