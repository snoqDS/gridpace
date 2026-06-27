# API Outage Runbook

## GridStatus API Outage

Symptoms: Pipeline fails with connection error, no new bronze data.

Steps:
1. Check GridStatus status page: https://gridstatus.io
2. Set dry_run: true in config/settings.yml to keep pipeline running with sample data
3. Monitor GridStatus Twitter/status for restoration
4. When restored, set dry_run: false and run: uv run python -m gridpace.grid.flows
5. Run make reseed if data gap is significant
