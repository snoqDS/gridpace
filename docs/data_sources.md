# Data Sources

## GridStatus

Real time grid operations data across North American ISOs.

Website: https://gridstatus.io
License: Commercial API, free tier available
Attribution: Required per ToS Section 4.4 "Powered by Grid Status"

Note: ISO list is configured in config/settings.yml. 
Add or remove ISOs there without updating this file.

### API Reference

GridStatus Python library: https://github.com/gridstatus/gridstatus
GridStatus API docs: https://docs.gridstatus.io
GridStatus ToS: https://www.gridstatus.io/terms

Methods used:
  iso.get_lmp(date="latest") — real time LMP prices
  iso.get_fuel_mix(date="latest") — current generation fuel mix

Schema contracts defined in:
  src/gridpace/grid/contracts/gridstatus.yml

### Datasets Used

LMP (Locational Marginal Prices)
  Endpoint: iso.get_lmp(date="latest")
  Frequency: 5 minute SCED intervals
  ISOs: Configured in config/settings.yml under isos:
  Key fields: Interval Start, Interval End, Location, Location Type, LMP

Fuel Mix (Generation by Fuel Type)
  Endpoint: iso.get_fuel_mix(date="latest")
  Frequency: Varies by ISO
  ISOs: Configured in config/settings.yml under isos:
  Key fields: time, natural_gas, wind, solar, coal, nuclear

### API Limits (Free Tier)

  250 requests per month
  500,000 rows per month
  Poll interval: 120 minutes (configurable in config/settings.yml)

### Notes

  dry_run mode returns sample data without hitting the API
  Integration tests are skipped in CI to preserve quota
  Run integration tests manually: uv run pytest tests/integration/ -v

## EIA Grid Monitor
Planned for Phase 1.

## WattTime
Planned for Phase 1.

## Ember API
Planned for Phase 1.

## Weather
TBD.
