.PHONY: install lint format test eval run mlflow diagnostics

install:
	uv sync --all-groups

lint:
	uv run ruff check src/ tests/ evals/

format:
	uv run ruff format src/ tests/ evals/

test:
	uv run pytest tests/ -v

eval:
	uv run pytest evals/ -v

run:
	uv run streamlit run src/gridpace/ui/app.py

mlflow:
	uv run mlflow ui

diagnostics:
	uv run python scripts/diagnostics.py

seed:
	uv run python scripts/seed_db.py

reseed:
	uv run python scripts/seed_db.py --force

seed-week:
	uv run python scripts/seed_db.py --hours 168 --force
