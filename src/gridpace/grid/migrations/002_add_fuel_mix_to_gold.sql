-- Migration 002: Add fuel mix columns to gold.iso_summary
-- Enables dashboard to show fuel breakdown without querying silver directly

ALTER TABLE gold.iso_summary ADD COLUMN IF NOT EXISTS natural_gas DOUBLE;
ALTER TABLE gold.iso_summary ADD COLUMN IF NOT EXISTS wind DOUBLE;
ALTER TABLE gold.iso_summary ADD COLUMN IF NOT EXISTS solar DOUBLE;
ALTER TABLE gold.iso_summary ADD COLUMN IF NOT EXISTS coal DOUBLE;
ALTER TABLE gold.iso_summary ADD COLUMN IF NOT EXISTS nuclear DOUBLE;
ALTER TABLE gold.iso_summary ADD COLUMN IF NOT EXISTS other DOUBLE;
