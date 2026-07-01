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
  Native resolution: 5-minute SCED intervals from ISO public portals
  Effective poll interval: Configured in config/settings.yml under
    ingestion.poll_interval_minutes (default 5 minutes).
    gridstatus open-source library has no request limits — pulls directly
    from CAISO OASIS, ERCOT public API, and PJM Data Miner.
  ISOs: Configured in config/settings.yml under isos:
  Key fields: Interval Start, Interval End, Location, Location Type, LMP

Fuel Mix (Generation by Fuel Type)
  Endpoint: iso.get_fuel_mix(date="latest")
  Native resolution: 5-minute intervals for most ISOs, varies by market
  Effective poll interval: Configured in config/settings.yml under
    ingestion.poll_interval_minutes (default 5 minutes).  ISOs: Configured in config/settings.yml under isos:
  Key fields: time, natural_gas, wind, solar, coal, nuclear

### API Limits

  gridstatus open-source library pulls directly from ISO public portals.
  No request limits apply — this is not the paid gridstatusio API.
  Poll interval: 5 minutes for local real-time system (configurable in
  config/settings.yml under ingestion.poll_interval_minutes).
  Native ISO resolution: 5-minute SCED intervals for LMP data.

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
