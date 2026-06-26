-- Add updated_at column to leads for pipeline stage tracking
-- Run: psql $DATABASE_URL -f storage/migrations/add_updated_at_to_leads.sql

ALTER TABLE leads ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT NOW();
CREATE INDEX IF NOT EXISTS idx_leads_updated_at ON leads(updated_at DESC);
