-- Migration: Create Analytics Tables
-- Description: Creates tables for tracking user events, meme analytics, and engagement metrics

-- Create user_events table
CREATE TABLE user_events (
    id VARCHAR(36) PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    event_type VARCHAR(50) NOT NULL,
    event_data TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
    session_id VARCHAR(100),
    source VARCHAR(50),
    user_agent TEXT,
    ip_address VARCHAR(45)
);

-- Create analytics_events table
CREATE TABLE analytics_events (
    id VARCHAR(36) PRIMARY KEY,
    event_type VARCHAR(50) NOT NULL,
    event_data TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
    severity VARCHAR(20) DEFAULT 'info',
    source VARCHAR(50),
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL
);

-- Create meme_analytics table
CREATE TABLE meme_analytics (
    id VARCHAR(36) PRIMARY KEY,
    meme_id VARCHAR(36) NOT NULL REFERENCES memes(id) ON DELETE CASCADE,
    date DATETIME NOT NULL,
    views INTEGER DEFAULT 0,
    likes INTEGER DEFAULT 0,
    shares INTEGER DEFAULT 0,
    skips INTEGER DEFAULT 0,
    opt_outs INTEGER DEFAULT 0,
    engagement_rate INTEGER DEFAULT 0,
    skip_rate INTEGER DEFAULT 0,
    opt_out_rate INTEGER DEFAULT 0,
    age_group_distribution TEXT,
    income_level_distribution TEXT,
    education_level_distribution TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Create user_meme_analytics table
CREATE TABLE user_meme_analytics (
    id VARCHAR(36) PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    total_memes_viewed INTEGER DEFAULT 0,
    total_memes_liked INTEGER DEFAULT 0,
    total_memes_shared INTEGER DEFAULT 0,
    total_memes_skipped INTEGER DEFAULT 0,
    favorite_categories TEXT,
    least_favorite_categories TEXT,
    average_view_time_seconds INTEGER DEFAULT 0,
    most_active_time_of_day VARCHAR(10),
    most_active_day_of_week VARCHAR(10),
    total_opt_outs INTEGER DEFAULT 0,
    total_opt_ins INTEGER DEFAULT 0,
    last_opt_out_date DATETIME,
    last_opt_in_date DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for performance
CREATE INDEX idx_user_events_user_id ON user_events(user_id);
CREATE INDEX idx_user_events_event_type ON user_events(event_type);
CREATE INDEX idx_user_events_timestamp ON user_events(timestamp);
CREATE INDEX idx_user_events_user_type_timestamp ON user_events(user_id, event_type, timestamp);
CREATE INDEX idx_user_events_source ON user_events(source);

CREATE INDEX idx_analytics_events_event_type ON analytics_events(event_type);
CREATE INDEX idx_analytics_events_timestamp ON analytics_events(timestamp);
CREATE INDEX idx_analytics_events_severity ON analytics_events(severity);
CREATE INDEX idx_analytics_events_source ON analytics_events(source);
CREATE INDEX idx_analytics_events_user_id ON analytics_events(user_id);

CREATE INDEX idx_meme_analytics_meme_id ON meme_analytics(meme_id);
CREATE INDEX idx_meme_analytics_date ON meme_analytics(date);
CREATE INDEX idx_meme_analytics_engagement_rate ON meme_analytics(engagement_rate);
CREATE INDEX idx_meme_analytics_opt_out_rate ON meme_analytics(opt_out_rate);

CREATE INDEX idx_user_meme_analytics_user_id ON user_meme_analytics(user_id);
CREATE INDEX idx_user_meme_analytics_total_views ON user_meme_analytics(total_memes_viewed);
CREATE INDEX idx_user_meme_analytics_engagement ON user_meme_analytics(total_memes_liked);

-- Create unique constraints
CREATE UNIQUE INDEX uq_meme_analytics_meme_date ON meme_analytics(meme_id, date);
CREATE UNIQUE INDEX uq_user_meme_analytics_user ON user_meme_analytics(user_id);

-- Insert initial analytics records for existing users with meme preferences
INSERT INTO user_meme_analytics (id, user_id, total_opt_outs, total_opt_ins, created_at, updated_at)
SELECT 
    (SELECT hex(randomblob(16))),
    ump.user_id,
    CASE WHEN ump.opt_out_date IS NOT NULL THEN 1 ELSE 0 END,
    CASE WHEN ump.opt_out_date IS NULL AND ump.memes_enabled = 1 THEN 1 ELSE 0 END,
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
FROM user_meme_preferences ump
WHERE NOT EXISTS (
    SELECT 1 FROM user_meme_analytics uma WHERE uma.user_id = ump.user_id
);
