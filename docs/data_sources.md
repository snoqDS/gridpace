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
  Native resolution: 5-minute SCED intervals from GridStatus
  Effective poll interval: Configured in config/settings.yml under
    ingestion.poll_interval_minutes (currently 120 minutes on free tier).
    Native 5-minute resolution requires a paid GridStatus tier.
    See docs/architecture.md Key Decisions for full polling constraint rationale.
  ISOs: Configured in config/settings.yml under isos:
  Key fields: Interval Start, Interval End, Location, Location Type, LMP

Fuel Mix (Generation by Fuel Type)
  Endpoint: iso.get_fuel_mix(date="latest")
  Native resolution: Varies by ISO
  Effective poll interval: Matches ingestion.poll_interval_minutes in config/settings.yml.
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
Planned for Phase 2. Will provide US generation and demand data.

## WattTime
Planned for Phase 4. Will provide marginal carbon emissions by balancing
authority for optimal battery charging windows.

## Ember API
Planned for Phase 2. Will provide historical generation mix and carbon intensity.

## Weather
Planned for Phase 4. Required for cross-variable correlation analysis
(weather vs LMP). Source TBD — candidates include NOAA HRRR and NASA POWER.
