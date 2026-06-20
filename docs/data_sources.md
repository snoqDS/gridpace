# Data Sources

## GridStatus

Real time grid operations data across North American ISOs.

Website: https://gridstatus.io
License: Commercial API, free tier available
Attribution: Required per ToS Section 4.4 "Powered by Grid Status"

Note: ISO list is configured in config/settings.yml. 
Add or remove ISOs there without updating this file.

### Datasets Used

LMP (Locational Marginal Prices)
  Endpoint: iso.get_lmp(date="latest")
  Frequency: 5 minute SCED intervals
  ISOs: Configured in config/settings.yml under isos:
  Key fields: Interval Start, Interval End, Location, Location Type, LMP

Fuel Mix (Generation by Fuel Type)
  Endpoint: iso.get_fuel_mix(date="latest")
  Frequency: Varies by ISO
  ISOs: ERCOT, CAISO, PJM
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

Coming in Session 2.

## WattTime

Coming in Session 2.

## Ember API

Coming in Session 2.

## Weather

TBD.
