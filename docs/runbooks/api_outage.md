# ISO Portal Outage Runbook

## Symptoms

Pipeline fails with connection error. No new bronze data ingested.
Structured logs show fetch errors in grid/flows.py fetch tasks.

## Affected Sources

GridPace pulls directly from ISO public portals via the gridstatus open-source
library. Outages affect one or more of:

    CAISO OASIS:      https://oasis.caiso.com
    ERCOT public API: https://api.ercot.com
    PJM Data Miner:   https://dataminer2.pjm.com
    MISO:             https://api.misoenergy.org
    NYISO:            https://www.nyiso.com/custom-reports
    ISONE:            https://webservices.iso-ne.com
    SPP:              https://marketplace.spp.org
    IESO:             https://ieso.ca/power-data
    AESO:             https://api.aeso.ca

## Steps

1. Identify which ISO portal is down from the error logs
2. Check the affected ISO status page directly
3. Set dry_run: true in config/settings.yml to keep pipeline running with sample data
4. Monitor ISO status page for restoration
5. When restored, set dry_run: false and run:

    uv run python -m gridpace.grid.flows

6. Run make backfill if data gap is significant and historical data is needed
