-- =====================================================
-- Migration 006: Add media_type for video/audio support
-- Run AFTER 001, 004, 005.
-- Allows memes to be image, video, or audio; frontend
-- uses this to render <img>, <video>, or <audio>.
-- =====================================================

-- Add column; default 'image' for existing rows
ALTER TABLE memes ADD COLUMN media_type TEXT DEFAULT 'image';

-- Optional: constrain to known values (SQLite allows any value without CHECK in older versions)
-- UPDATE memes SET media_type = 'image' WHERE media_type IS NULL OR media_type = '';
