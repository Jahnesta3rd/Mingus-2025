-- =====================================================
-- Migration 001: Initial Meme Schema
-- Creates the base meme tables and indexes
-- =====================================================

-- Enable foreign key constraints
PRAGMA foreign_keys = ON;

-- =====================================================
-- 1. MEMES TABLE
-- =====================================================
CREATE TABLE IF NOT EXISTS memes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    image_url TEXT NOT NULL,
    category TEXT NOT NULL CHECK (category IN (
        'faith', 
        'work_life', 
        'friendships', 
        'children', 
        'relationships', 
        'going_out'
    )),
    caption TEXT NOT NULL,
    alt_text TEXT NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT 1,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- 2. USER MEME HISTORY TABLE
-- =====================================================
CREATE TABLE IF NOT EXISTS user_meme_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    meme_id INTEGER NOT NULL,
    viewed_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (meme_id) REFERENCES memes(id) ON DELETE CASCADE,
    UNIQUE(user_id, meme_id)
);

-- =====================================================
-- 3. USER MOOD DATA TABLE
-- =====================================================
CREATE TABLE IF NOT EXISTS user_mood_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    session_id TEXT NOT NULL,
    meme_id INTEGER NOT NULL,
    mood_score INTEGER NOT NULL CHECK (mood_score BETWEEN 1 AND 5),
    mood_label TEXT NOT NULL CHECK (mood_label IN ('excited', 'happy', 'neutral', 'sad', 'angry')),
    timestamp DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    meme_category TEXT NOT NULL,
    spending_context TEXT DEFAULT 'before_budget_check',
    FOREIGN KEY (meme_id) REFERENCES memes(id) ON DELETE CASCADE
);

-- =====================================================
-- 4. INDEXES FOR PERFORMANCE
-- =====================================================

-- Indexes for memes table
CREATE INDEX IF NOT EXISTS idx_memes_category ON memes(category);
CREATE INDEX IF NOT EXISTS idx_memes_active ON memes(is_active);
CREATE INDEX IF NOT EXISTS idx_memes_category_active ON memes(category, is_active);
CREATE INDEX IF NOT EXISTS idx_memes_created_at ON memes(created_at);

-- Indexes for mood data table
CREATE INDEX IF NOT EXISTS idx_user_mood_data_user_id ON user_mood_data(user_id);
CREATE INDEX IF NOT EXISTS idx_user_mood_data_timestamp ON user_mood_data(timestamp);
CREATE INDEX IF NOT EXISTS idx_user_mood_data_mood_score ON user_mood_data(mood_score);
CREATE INDEX IF NOT EXISTS idx_user_mood_data_user_timestamp ON user_mood_data(user_id, timestamp);

-- Indexes for user_meme_history table
CREATE INDEX IF NOT EXISTS idx_user_meme_history_user_id ON user_meme_history(user_id);
CREATE INDEX IF NOT EXISTS idx_user_meme_history_meme_id ON user_meme_history(meme_id);
CREATE INDEX IF NOT EXISTS idx_user_meme_history_viewed_at ON user_meme_history(viewed_at);
CREATE INDEX IF NOT EXISTS idx_user_meme_history_user_viewed ON user_meme_history(user_id, viewed_at);

-- =====================================================
-- 5. TRIGGERS FOR AUTOMATIC TIMESTAMP UPDATES
-- =====================================================

-- Trigger to update updated_at timestamp on memes table
CREATE TRIGGER IF NOT EXISTS update_memes_timestamp 
    AFTER UPDATE ON memes
    FOR EACH ROW
BEGIN
    UPDATE memes SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;
