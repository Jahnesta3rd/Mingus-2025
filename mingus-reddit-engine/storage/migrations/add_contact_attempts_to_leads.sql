-- Add multi-attempt contact tracking to leads (Option B: child table + denormalized count)
-- Run: psql $DATABASE_URL -f storage/migrations/add_contact_attempts_to_leads.sql
--
-- Data-additive only: adds columns and a new table; does not modify or drop
-- existing columns (source, ig_handle, responded, response_got_dm, no_reply,
-- pipeline_stage, ingested_at, updated_at).
--
-- Safety checks (run after migration):
--   SELECT column_name, data_type, column_default
--   FROM information_schema.columns
--   WHERE table_schema = 'public' AND table_name = 'leads'
--     AND column_name IN (
--       'contact_attempt_count', 'attempt_1_at', 'attempt_2_at',
--       'attempt_3_at', 'requeued_at'
--     )
--   ORDER BY column_name;
--
--   SELECT COUNT(*) AS backfilled_leads
--   FROM leads
--   WHERE contact_attempt_count > 0;
--
--   SELECT * FROM lead_contact_attempts LIMIT 0;

-- ---------------------------------------------------------------------------
-- Step 1: Denormalized attempt columns on leads
-- ---------------------------------------------------------------------------

ALTER TABLE leads ADD COLUMN IF NOT EXISTS contact_attempt_count INTEGER DEFAULT 0;
ALTER TABLE leads ADD COLUMN IF NOT EXISTS attempt_1_at TIMESTAMP;
ALTER TABLE leads ADD COLUMN IF NOT EXISTS attempt_2_at TIMESTAMP;
ALTER TABLE leads ADD COLUMN IF NOT EXISTS attempt_3_at TIMESTAMP;
ALTER TABLE leads ADD COLUMN IF NOT EXISTS requeued_at TIMESTAMP;

ALTER TABLE leads DROP CONSTRAINT IF EXISTS chk_leads_contact_attempt_count;
ALTER TABLE leads ADD CONSTRAINT chk_leads_contact_attempt_count
  CHECK (contact_attempt_count >= 0 AND contact_attempt_count <= 3);

CREATE INDEX IF NOT EXISTS idx_leads_contact_attempt_count
  ON leads(contact_attempt_count)
  WHERE contact_attempt_count > 0;

-- ---------------------------------------------------------------------------
-- Step 2: Child table for full audit trail
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS lead_contact_attempts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lead_id UUID NOT NULL REFERENCES leads(id) ON DELETE CASCADE,
    attempt_number INTEGER NOT NULL
      CHECK (attempt_number >= 1 AND attempt_number <= 3),
    channel TEXT NOT NULL DEFAULT 'instagram_dm',
    attempted_at TIMESTAMP NOT NULL DEFAULT NOW(),
    notes TEXT,
    logged_by TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_lead_contact_attempts_lead_attempt
      UNIQUE (lead_id, attempt_number)
);

CREATE INDEX IF NOT EXISTS idx_lead_contact_attempts_lead_attempted
  ON lead_contact_attempts(lead_id, attempted_at DESC);

CREATE INDEX IF NOT EXISTS idx_lead_contact_attempts_attempted_at
  ON lead_contact_attempts(attempted_at DESC);

-- ---------------------------------------------------------------------------
-- Step 3: Backfill existing responded leads as attempt 1
-- ---------------------------------------------------------------------------

UPDATE leads
SET
  contact_attempt_count = 1,
  attempt_1_at = COALESCE(updated_at, ingested_at, NOW())
WHERE responded = TRUE
  AND COALESCE(contact_attempt_count, 0) = 0;

INSERT INTO lead_contact_attempts (
    lead_id,
    attempt_number,
    channel,
    attempted_at,
    notes,
    logged_by
)
SELECT
    l.id,
    1,
    CASE
        WHEN l.source = 'instagram' THEN 'instagram_dm'
        ELSE 'reddit_comment'
    END,
    COALESCE(l.attempt_1_at, l.updated_at, l.ingested_at, NOW()),
    'Backfilled from responded = TRUE',
    'migration_backfill'
FROM leads l
WHERE l.responded = TRUE
  AND l.contact_attempt_count = 1
  AND NOT EXISTS (
      SELECT 1
      FROM lead_contact_attempts a
      WHERE a.lead_id = l.id
        AND a.attempt_number = 1
  );

-- ---------------------------------------------------------------------------
-- Rollback (manual — run only if reverting this migration)
-- ---------------------------------------------------------------------------
-- DROP TABLE IF EXISTS lead_contact_attempts;
-- ALTER TABLE leads DROP CONSTRAINT IF EXISTS chk_leads_contact_attempt_count;
-- DROP INDEX IF EXISTS idx_leads_contact_attempt_count;
-- ALTER TABLE leads DROP COLUMN IF EXISTS requeued_at;
-- ALTER TABLE leads DROP COLUMN IF EXISTS attempt_3_at;
-- ALTER TABLE leads DROP COLUMN IF EXISTS attempt_2_at;
-- ALTER TABLE leads DROP COLUMN IF EXISTS attempt_1_at;
-- ALTER TABLE leads DROP COLUMN IF EXISTS contact_attempt_count;
