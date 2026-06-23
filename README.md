# GridPace

Real-time grid intelligence with historical context.

GridPace monitors ISO/RTO grid conditions across major US markets, detects stress events and anomalies, generates plain-English situation reports via an agentic reasoning loop, and finds similar historical events using vector search over a time-series event database.

## Features

- Real-time grid monitoring across multiple ISOs (ERCOT, CAISO, PJM)
- Price spike and reserve margin stress detection
- Renewable penetration analysis vs seasonal baselines
- Agentic narrative generation explaining current grid conditions
- Historical analog retrieval using vector similarity search
- Medallion data architecture (bronze, silver, gold)
- Streamlit dashboard with live updates
- Structured logging and health monitoring

## Data Sources

- GridStatus — real-time LMP prices, generation mix, reserve margins
- EIA Grid Monitor — generation and demand data
- WattTime — marginal carbon emissions by balancing authority
- Ember API — historical generation mix and carbon intensity
- Weather: TBD

## Tech Stack

- Python 3.11, uv
- LangGraph — agentic reasoning and multi-step planning
- DuckDB — bronze/silver/gold analytical warehouse
- FAISS + sentence-transformers — vector search for historical analogs
- Streamlit — live dashboard
- Pyomo + HiGHS — dispatch optimization
- MLflow — experiment tracking
- Ruff, pytest, GitHub Actions CI

## Installation

Clone the repository:

    git clone https://github.com/snoqDS/gridpace.git
    cd gridpace

Install uv if not already installed:

    curl -LsSf https://astral.sh/uv/install.sh | sh

Install dependencies:

    uv sync

Copy the environment file and add your API keys:

    cp .env.example .env

See [docs/setup.md](docs/setup.md) for detailed setup instructions including API key signup and first run walkthrough.

Run the dashboard:

    make run

## Quick Start

    # Run the dashboard
    make run

    # Run tests
    make test

    # Run LLM evals
    make eval

    # Run linter
    make lint

    # Format code
    make format

    # Launch MLflow tracking UI
    make mlflow

    # Run system diagnostics
    make diagnostics

    # Live demo: <Phase 1 — coming soon>

## Roadmap

- [x] Phase 0: Production-grade repo scaffolding
- [ ] Phase 1: Live grid dashboard with real-time ISO data
- [ ] Phase 2: Agentic narrative layer with LangGraph
- [ ] Phase 3: Historical analog engine with vector search

## License

Apache 2.0 — see [LICENSE](LICENSE) for details.

Copyright 2026 Philip Regulski

## Contact

- GitHub: [snoqDS](https://github.com/snoqDS)
- LinkedIn: [philregulski](https://www.linkedin.com/in/philregulski/)


