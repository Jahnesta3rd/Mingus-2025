-- Add pipeline_stage column to leads for sales pipeline tracking
-- Run: psql $DATABASE_URL -f storage/migrations/add_pipeline_stage_to_leads.sql

ALTER TABLE leads ADD COLUMN IF NOT EXISTS pipeline_stage TEXT DEFAULT 'prospect';

ALTER TABLE leads DROP CONSTRAINT IF EXISTS chk_leads_pipeline_stage;
ALTER TABLE leads ADD CONSTRAINT chk_leads_pipeline_stage
  CHECK (pipeline_stage IN (
    'prospect',
    'meeting_booked',
    'qualified',
    'offer_made',
    'decision_pending',
    'closed_won',
    'closed_lost'
  ));

CREATE INDEX IF NOT EXISTS idx_leads_pipeline_stage ON leads(pipeline_stage);

DO $$
BEGIN
  IF EXISTS (
    SELECT 1
    FROM information_schema.columns
    WHERE table_schema = 'public'
      AND table_name = 'leads'
      AND column_name = 'updated_at'
  ) THEN
    CREATE INDEX IF NOT EXISTS idx_leads_updated_at ON leads(updated_at DESC);
  END IF;
END $$;
