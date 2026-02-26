-- =====================================================
-- Migration 004: Day-of-week and theme for memes (testing)
-- Adds optional columns so each day can have a dedicated theme/meme.
-- 0 = Monday, 6 = Sunday (Python weekday() convention).
-- =====================================================

-- Add optional columns (nullable so existing memes are unchanged)
ALTER TABLE memes ADD COLUMN day_of_week INTEGER;  -- 0=Mon .. 6=Sun
ALTER TABLE memes ADD COLUMN theme TEXT;           -- e.g. 'Monday Motivation', 'Tuesday Hustle'

-- Index for "today's meme" lookups
CREATE INDEX IF NOT EXISTS idx_memes_day_of_week ON memes(day_of_week) WHERE day_of_week IS NOT NULL;
