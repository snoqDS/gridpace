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
  ISOs: Configured in config/settings.yml under isos:
  Key fields: Interval Start, Interval End, Location, Location Type, LMP

Fuel Mix (Generation by Fuel Type)
  Endpoint: iso.get_fuel_mix(date="latest")
  Native resolution: 5-minute intervals for most ISOs, varies by market
  Effective poll interval: Configured in config/settings.yml under
    ingestion.poll_interval_minutes (default 5 minutes).
  ISOs: Configured in config/settings.yml under isos:
  Key fields: time, natural_gas, wind, solar, coal, nuclear

### API Limits

  gridstatus open-source library pulls directly from ISO public portals.
  No request limits apply — this is not the paid gridstatusio API.
  Poll interval: 5 minutes for local real-time system (configurable in
  config/settings.yml under ingestion.poll_interval_minutes).
  Native ISO resolution: 5-minute SCED intervals for LMP data.

### ISO-Specific Requirements

  Most ISOs require no API key — gridstatus pulls directly from public portals.
  PJM is the exception:

  PJM Data Miner 2 API:
    Registration: https://apiportal.pjm.com
    Cost: Free
    Note: Requires a PJM member account. Non-member accounts (e.g. gmail.com)
    have significantly limited access. If you are not a PJM member, PJM data
    will be skipped in the live pipeline but works in dry_run mode.
    Set PJM_API_KEY in .env once registered.
    See .env.example for setup instructions.

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

### Notes

  dry_run mode returns sample data without hitting the API.
  Integration tests are skipped in CI to avoid live ISO API calls during automated builds.

  Run integration tests manually: uv run pytest tests/integration/ -v

  API quota tracking: not required — gridstatus open-source library pulls
  directly from ISO public portals with no request limits. If switching to
  the paid gridstatusio API, add quota tracking to scripts/diagnostics.py
  and monitor usage at https://api.gridstatus.io/v1/api_usage.
  See docs/architecture.md Key Decisions for full rationale.