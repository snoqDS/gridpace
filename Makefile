.PHONY: install lint format test eval run mlflow diagnostics diagnostics-full seed reseed seed-week backfill backfill-history

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

diagnostics-full:
	uv run python scripts/diagnostics.py --security

seed:
	uv run python scripts/seed_db.py

reseed:
	uv run python scripts/seed_db.py --force

seed-week:
	uv run python scripts/seed_db.py --hours 168 --force

backfill:
	uv run python scripts/backfill_events.py --gold

backfill-history:
	uv run python scripts/backfill_events.py --history --days 30
