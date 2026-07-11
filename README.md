# GridPace

Real-time grid intelligence dashboard for US ISO/RTO markets.

GridPace monitors live grid conditions across ERCOT, CAISO, and PJM — tracking
LMP prices, generation fuel mix, renewable penetration, and statistical anomalies.
Built with a production-grade data pipeline and an extensible architecture for
agentic narrative generation and historical analog retrieval in future phases.

## Current State

Phase 1 is in progress. The dashboard is running locally with synthetic data.

- LMP price monitoring across 9 ISOs (ERCOT, CAISO, MISO, SPP, NYISO, ISONE, IESO, AESO, PJM)
- PJM requires free API key from apiportal.pjm.com — other ISOs need no key
- Statistical anomaly detection with z-score baselines per ISO
- Generation fuel mix breakdown with donut charts
- Medallion data architecture (bronze, silver, gold) via DuckDB
- Prefect orchestration with parallel ISO fetching
- Streamlit dashboard with tab structure for future analytics

## Quick Start

    git clone https://github.com/snoqDS/gridpace.git
    cd gridpace
    uv sync
    cp .env.example .env       # no API key required for Phase 1
    make seed                  # populate with synthetic data
    make run                   # open dashboard at localhost:8501

See [docs/setup.md](docs/setup.md) for full setup instructions including
live data configuration, and troubleshooting.

## Commands

    make run          # launch dashboard
    make test         # run test suite (79 tests)
    make lint         # run ruff linter
    make seed         # populate DB with 48h synthetic data
    make seed-week    # populate DB with 168h synthetic data (recommended)
    make reseed       # clear and regenerate 48h synthetic data

## Architecture

See [docs/architecture.md](docs/architecture.md) for full architecture
documentation including data flow, key decisions, security model, and
future considerations.

## Data Sources

Phase 1: gridstatus open-source library (pulls directly from ISO public portals, no API key, no limits)
Phase 2+: EIA Grid Monitor, WattTime, Ember API

## Roadmap

- [x] Phase 0: Repo scaffolding
- [ ] Phase 1: Live grid dashboard with anomaly detection (in progress)
- [ ] Phase 2: Agentic narrative layer with LangGraph
- [ ] Phase 3: Historical analog engine with vector search
- [ ] Phase 4: Real-time dispatch support for battery operators
- [ ] Phase 5: Long-term project developer analysis

See [docs/architecture.md](docs/architecture.md) for full phase descriptions.

## Tech Stack

Python 3.11, uv, DuckDB, Prefect, Streamlit, structlog, Ruff, pytest,
GitHub Actions CI. Phase 2+ adds LangGraph, FAISS, sentence-transformers,
Pyomo, MLflow.

## License

Apache 2.0 — see [LICENSE](LICENSE) for details.
Copyright 2026 Philip Regulski

## Contact

- GitHub: [snoqDS](https://github.com/snoqDS)
- LinkedIn: [philregulski](https://www.linkedin.com/in/philregulski/)
