-- =====================================================
-- Migration 005: Unify meme categories (6 -> 8 allowed)
-- Canonical 7 from meme_selector + going_out for legacy.
-- Run AFTER 001 and 004. Recreates memes so CHECK allows
-- faith, work_life, health, housing, transportation,
-- relationships, family, going_out.
-- =====================================================

PRAGMA foreign_keys = OFF;

-- Create replacement table with expanded category CHECK
CREATE TABLE IF NOT EXISTS memes_new (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    image_url TEXT NOT NULL,
    category TEXT NOT NULL CHECK (category IN (
        'faith',
        'work_life',
        'health',
        'housing',
        'transportation',
        'relationships',
        'family',
        'going_out'
    )),
    caption TEXT NOT NULL,
    alt_text TEXT NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT 1,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    day_of_week INTEGER,
    theme TEXT
);

-- Copy data: map old 6-category values to unified set.
-- Uses only columns that exist in 001 (no day_of_week/theme in SELECT) so this works before or after 004.
INSERT INTO memes_new (
    id, image_url, category, caption, alt_text, is_active,
    created_at, updated_at
)
SELECT
    id,
    image_url,
    CASE category
        WHEN 'friendships' THEN 'relationships'
        WHEN 'children' THEN 'family'
        ELSE category
    END,
    caption,
    alt_text,
    is_active,
    created_at,
    updated_at
FROM memes;

DROP TABLE memes;
ALTER TABLE memes_new RENAME TO memes;

-- Recreate indexes
CREATE INDEX IF NOT EXISTS idx_memes_category ON memes(category);
CREATE INDEX IF NOT EXISTS idx_memes_active ON memes(is_active);
CREATE INDEX IF NOT EXISTS idx_memes_category_active ON memes(category, is_active);
CREATE INDEX IF NOT EXISTS idx_memes_created_at ON memes(created_at);
CREATE INDEX IF NOT EXISTS idx_memes_day_of_week ON memes(day_of_week) WHERE day_of_week IS NOT NULL;

-- Recreate timestamp trigger
CREATE TRIGGER IF NOT EXISTS update_memes_timestamp
    AFTER UPDATE ON memes
    FOR EACH ROW
BEGIN
    UPDATE memes SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

PRAGMA foreign_keys = ON;
