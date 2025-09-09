-- =====================================================
-- Migration 002: Analytics Schema
-- Adds comprehensive analytics tracking tables
-- =====================================================

-- Enable foreign key constraints
PRAGMA foreign_keys = ON;

-- =====================================================
-- 1. MEME ANALYTICS EVENTS TABLE
-- =====================================================
CREATE TABLE IF NOT EXISTS meme_analytics_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    session_id TEXT NOT NULL,
    meme_id INTEGER NOT NULL,
    event_type TEXT NOT NULL CHECK (event_type IN (
        'view', 
        'continue', 
        'skip', 
        'auto_advance',
        'mood_selected',
        'error'
    )),
    event_timestamp DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    time_spent_seconds INTEGER DEFAULT 0,
    user_agent TEXT,
    ip_address TEXT,
    referrer TEXT,
    device_type TEXT CHECK (device_type IN ('mobile', 'tablet', 'desktop')),
    browser TEXT,
    os TEXT,
    screen_resolution TEXT,
    additional_data TEXT,
    FOREIGN KEY (meme_id) REFERENCES memes(id) ON DELETE CASCADE
);

-- =====================================================
-- 2. USER DEMOGRAPHICS TABLE
-- =====================================================
CREATE TABLE IF NOT EXISTS user_demographics (
    user_id INTEGER PRIMARY KEY,
    age_range TEXT CHECK (age_range IN ('18-24', '25-34', '35-44', '45-54', '55-64', '65+')),
    gender TEXT CHECK (gender IN ('male', 'female', 'non-binary', 'prefer_not_to_say')),
    income_range TEXT CHECK (income_range IN ('under_25k', '25k-50k', '50k-75k', '75k-100k', '100k-150k', '150k+')),
    education_level TEXT CHECK (education_level IN ('high_school', 'some_college', 'bachelors', 'masters', 'doctorate')),
    location_state TEXT,
    location_country TEXT DEFAULT 'US',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- 3. MEME PERFORMANCE METRICS TABLE
-- =====================================================
CREATE TABLE IF NOT EXISTS meme_performance_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    meme_id INTEGER NOT NULL,
    date DATE NOT NULL,
    total_views INTEGER DEFAULT 0,
    total_continues INTEGER DEFAULT 0,
    total_skips INTEGER DEFAULT 0,
    total_auto_advances INTEGER DEFAULT 0,
    avg_time_spent_seconds REAL DEFAULT 0,
    skip_rate REAL DEFAULT 0,
    continue_rate REAL DEFAULT 0,
    error_count INTEGER DEFAULT 0,
    load_time_ms REAL DEFAULT 0,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (meme_id) REFERENCES memes(id) ON DELETE CASCADE,
    UNIQUE(meme_id, date)
);

-- =====================================================
-- 4. CATEGORY PERFORMANCE TABLE
-- =====================================================
CREATE TABLE IF NOT EXISTS category_performance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category TEXT NOT NULL,
    date DATE NOT NULL,
    total_views INTEGER DEFAULT 0,
    total_continues INTEGER DEFAULT 0,
    total_skips INTEGER DEFAULT 0,
    avg_time_spent_seconds REAL DEFAULT 0,
    skip_rate REAL DEFAULT 0,
    continue_rate REAL DEFAULT 0,
    unique_users INTEGER DEFAULT 0,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(category, date)
);

-- =====================================================
-- 5. USER ENGAGEMENT SESSIONS TABLE
-- =====================================================
CREATE TABLE IF NOT EXISTS user_engagement_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    session_id TEXT NOT NULL,
    session_start DATETIME NOT NULL,
    session_end DATETIME,
    total_memes_viewed INTEGER DEFAULT 0,
    total_time_spent_seconds INTEGER DEFAULT 0,
    memes_continued INTEGER DEFAULT 0,
    memes_skipped INTEGER DEFAULT 0,
    categories_viewed TEXT,
    conversion_to_wellness_check BOOLEAN DEFAULT 0,
    wellness_check_completed_at DATETIME,
    session_quality_score REAL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- 6. ANALYTICS ALERTS TABLE
-- =====================================================
CREATE TABLE IF NOT EXISTS analytics_alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    alert_type TEXT NOT NULL CHECK (alert_type IN (
        'high_skip_rate',
        'technical_error',
        'unusual_usage_pattern',
        'performance_degradation',
        'low_engagement'
    )),
    severity TEXT NOT NULL CHECK (severity IN ('low', 'medium', 'high', 'critical')),
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    affected_metric TEXT,
    threshold_value REAL,
    actual_value REAL,
    affected_category TEXT,
    affected_meme_id INTEGER,
    date_range_start DATE,
    date_range_end DATE,
    is_resolved BOOLEAN DEFAULT 0,
    resolved_at DATETIME,
    resolved_by TEXT,
    resolution_notes TEXT,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (affected_meme_id) REFERENCES memes(id) ON DELETE SET NULL
);

-- =====================================================
-- 7. DAILY ANALYTICS SUMMARY TABLE
-- =====================================================
CREATE TABLE IF NOT EXISTS daily_analytics_summary (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date DATE NOT NULL UNIQUE,
    total_users INTEGER DEFAULT 0,
    total_sessions INTEGER DEFAULT 0,
    total_meme_views INTEGER DEFAULT 0,
    total_continues INTEGER DEFAULT 0,
    total_skips INTEGER DEFAULT 0,
    avg_session_duration_seconds REAL DEFAULT 0,
    overall_skip_rate REAL DEFAULT 0,
    overall_continue_rate REAL DEFAULT 0,
    conversion_to_wellness_check_rate REAL DEFAULT 0,
    avg_load_time_ms REAL DEFAULT 0,
    error_rate REAL DEFAULT 0,
    most_popular_category TEXT,
    least_popular_category TEXT,
    new_users INTEGER DEFAULT 0,
    returning_users INTEGER DEFAULT 0,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- 8. INDEXES FOR PERFORMANCE
-- =====================================================

-- Analytics events indexes
CREATE INDEX IF NOT EXISTS idx_analytics_events_user_id ON meme_analytics_events(user_id);
CREATE INDEX IF NOT EXISTS idx_analytics_events_meme_id ON meme_analytics_events(meme_id);
CREATE INDEX IF NOT EXISTS idx_analytics_events_timestamp ON meme_analytics_events(event_timestamp);
CREATE INDEX IF NOT EXISTS idx_analytics_events_type ON meme_analytics_events(event_type);
CREATE INDEX IF NOT EXISTS idx_analytics_events_user_timestamp ON meme_analytics_events(user_id, event_timestamp);
CREATE INDEX IF NOT EXISTS idx_analytics_events_meme_timestamp ON meme_analytics_events(meme_id, event_timestamp);

-- Performance metrics indexes
CREATE INDEX IF NOT EXISTS idx_performance_metrics_meme_id ON meme_performance_metrics(meme_id);
CREATE INDEX IF NOT EXISTS idx_performance_metrics_date ON meme_performance_metrics(date);
CREATE INDEX IF NOT EXISTS idx_performance_metrics_meme_date ON meme_performance_metrics(meme_id, date);

-- Category performance indexes
CREATE INDEX IF NOT EXISTS idx_category_performance_category ON category_performance(category);
CREATE INDEX IF NOT EXISTS idx_category_performance_date ON category_performance(date);
CREATE INDEX IF NOT EXISTS idx_category_performance_category_date ON category_performance(category, date);

-- User engagement indexes
CREATE INDEX IF NOT EXISTS idx_engagement_sessions_user_id ON user_engagement_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_engagement_sessions_session_id ON user_engagement_sessions(session_id);
CREATE INDEX IF NOT EXISTS idx_engagement_sessions_start ON user_engagement_sessions(session_start);

-- Alerts indexes
CREATE INDEX IF NOT EXISTS idx_alerts_type ON analytics_alerts(alert_type);
CREATE INDEX IF NOT EXISTS idx_alerts_severity ON analytics_alerts(severity);
CREATE INDEX IF NOT EXISTS idx_alerts_resolved ON analytics_alerts(is_resolved);
CREATE INDEX IF NOT EXISTS idx_alerts_created ON analytics_alerts(created_at);

-- Daily summary indexes
CREATE INDEX IF NOT EXISTS idx_daily_summary_date ON daily_analytics_summary(date);
