-- IGL-04: Add no_reply column to leads
-- Run: psql $DATABASE_URL -f storage/migrations/add_no_reply_to_leads.sql

ALTER TABLE leads ADD COLUMN IF NOT EXISTS
  no_reply BOOLEAN DEFAULT FALSE;

CREATE INDEX IF NOT EXISTS idx_leads_no_reply
  ON leads(no_reply) WHERE no_reply = true;
