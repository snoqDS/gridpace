# Contributing to GridPace

Thank you for your interest in contributing. This document outlines the process for contributing to this project.

## Getting Started

1. Fork the repository on GitHub
2. Clone your fork locally:

    git clone https://github.com/YOUR_USERNAME/gridpace.git
    cd gridpace

3. Install dependencies:

    uv sync

4. Copy the environment file and add your API keys:

    cp .env.example .env

5. Create a feature branch:

    git checkout -b feat/your-feature-name

## Branch Naming

- `feat/` for new features
- `fix/` for bug fixes
- `chore/` for maintenance tasks
- `docs/` for documentation updates

## Commit Messages

Follow Conventional Commits format:

- `feat: add CAISO client to grid ingestion layer`
- `fix: correct DuckDB silver schema migration`
- `chore: update dependencies`
- `docs: expand architecture documentation`

## Code Style

This project uses Ruff for linting and formatting. Before committing:

    make lint
    make format

## Running Tests

    uv run pytest tests/ -v

All tests must pass before submitting a pull request.

Unit tests use mocked dependencies and temporary databases.
Integration tests hit live APIs and are skipped in CI by default.
Run integration tests manually only when verifying live API connectivity:

    uv run pytest tests/integration/ -v

## Test Structure

Shared constants and fixtures live in conftest.py files:

    tests/conftest.py               shared constants for all tests
    tests/unit/grid/conftest.py     shared fixtures for grid unit tests

When adding new tests:
    Use constants from tests/conftest.py rather than hardcoding values
    Add domain specific fixtures to the nearest conftest.py
    Never hardcode ISO names, row counts, or migration filenames in tests

## Running Evals

LLM evals are separate from unit tests and live in evals/:

    make eval

## Pull Request Process

1. Ensure all tests pass
2. Ensure ruff check passes with no errors
3. Update README.md if your change affects usage or installation
4. Submit your pull request against the `main` branch
5. Describe what your change does and why

## Adding a New Data Source Client

1. Create a new client under `src/gridpace/grid/clients/`
2. Follow the existing pattern in `src/gridpace/grid/clients/gridstatus.py`
3. Add a corresponding contract under `src/gridpace/grid/contracts/`
4. Add unit tests under `tests/unit/grid/`
5. Document the data source in `docs/data_sources.md`

## Adding a New Agent Tool

1. Add the tool function to `src/gridpace/intelligence/agents/tools.py`
2. Register it in `src/gridpace/intelligence/agents/graph.py`
3. Add corresponding evals in `evals/test_agent_evals.py`

## Reporting Issues

Open an issue on GitHub with:
- A clear description of the problem
- Steps to reproduce
- Expected vs actual behavior
- Python version and OS

## License

By contributing, you agree that your contributions will be licensed under the Apache 2.0 license.
