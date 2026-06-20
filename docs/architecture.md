# Architecture

## Overview

GridPace is a real time grid intelligence platform built in four phases.

## Phase 0: Repo Scaffolding (Complete)

Production grade Python project structure with uv, Ruff, pytest, GitHub Actions CI, and Apache 2.0 license.

## Phase 1: Live Grid Dashboard (In Progress)

### Data Flow

    GridStatus API
          |
          v
    grid/clients/gridstatus.py   (fetch)
          |
          v
    grid/validation.py           (schema contract check)
          |
          v
    grid/storage.py              (DuckDB bronze layer)
          |
          v
    grid/storage.py              (silver and gold transforms)
          |
          v
    ui/app.py                    (Streamlit dashboard)

### Key Decisions

Poll interval set to 120 minutes on free tier. Configurable in config/settings.yml.
dry_run mode returns sample data during development. No API quota consumed.
DuckDB serves as the local analytical warehouse. Dashboard reads from DuckDB, not live API.
Integration tests skipped in CI to preserve API quota. Run manually to verify live connectivity.

## Phase 2: Agentic Narrative Layer (Planned)

LangGraph state machine with observe, diagnose, explain, and publish nodes.
Tools call GridStatus, WattTime, and Ember APIs.
Narrative generation via configurable LLM provider (Ollama, HuggingFace, or Anthropic).

## Phase 3: Historical Analog Engine (Planned)

FAISS vector store over historical grid events with sentence transformer embeddings.
Retrieval augmented generation over time series event database.
Historical events sourced from EIA, GridStatus history, and Catalyst Cooperative PUDL.

## Tech Stack

    Layer              Technology
    ----------------   ---------------------------
    Package manager    uv
    Language           Python 3.11
    Data ingestion     gridstatus, httpx, requests
    Storage            DuckDB (bronze/silver/gold)
    Scheduling         APScheduler
    Agent framework    LangGraph 1.0
    Vector store       FAISS + sentence-transformers
    LLM providers      Ollama, HuggingFace, Anthropic
    Dashboard          Streamlit
    Optimization       Pyomo + HiGHS
    Experiment tracking MLflow
    Logging            structlog
    Linting            Ruff
    Testing            pytest
    CI/CD              GitHub Actions

## Configuration

All secrets loaded from .env via pydantic-settings.
Static config (ISOs, poll interval, dry_run) in config/settings.yml.
LLM provider switchable via LLM_PROVIDER in .env.
