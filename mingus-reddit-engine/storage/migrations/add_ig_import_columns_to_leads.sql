-- IGL-01: Add Instagram import columns to leads
-- Run manually: psql $DATABASE_URL -f storage/migrations/add_ig_import_columns_to_leads.sql
-- Safe to re-run: uses IF NOT EXISTS

ALTER TABLE leads ADD COLUMN IF NOT EXISTS source TEXT DEFAULT 'reddit';
ALTER TABLE leads ADD COLUMN IF NOT EXISTS ig_handle TEXT;

CREATE INDEX IF NOT EXISTS idx_leads_ig_handle ON leads(ig_handle);
