-- =====================================================
-- Mingus Personal Finance App - Meme Analytics Schema
-- SQLite Database Schema for Meme Analytics System
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
    time_spent_seconds INTEGER DEFAULT 0, -- Time spent viewing meme
    user_agent TEXT, -- Browser/device info
    ip_address TEXT, -- For geographic analysis
    referrer TEXT, -- Where user came from
    device_type TEXT CHECK (device_type IN ('mobile', 'tablet', 'desktop')),
    browser TEXT,
    os TEXT,
    screen_resolution TEXT,
    additional_data TEXT, -- JSON for extra event data
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
    skip_rate REAL DEFAULT 0, -- Percentage of skips
    continue_rate REAL DEFAULT 0, -- Percentage of continues
    error_count INTEGER DEFAULT 0,
    load_time_ms REAL DEFAULT 0, -- Average load time
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
    categories_viewed TEXT, -- JSON array of categories
    conversion_to_wellness_check BOOLEAN DEFAULT 0,
    wellness_check_completed_at DATETIME,
    session_quality_score REAL, -- Calculated engagement score
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
    affected_metric TEXT, -- Which metric triggered the alert
    threshold_value REAL, -- The threshold that was exceeded
    actual_value REAL, -- The actual value that triggered the alert
    affected_category TEXT, -- If category-specific
    affected_meme_id INTEGER, -- If meme-specific
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

-- =====================================================
-- 9. TRIGGERS FOR AUTOMATIC UPDATES
-- =====================================================

-- Trigger to update performance metrics when analytics events are inserted
CREATE TRIGGER IF NOT EXISTS update_performance_metrics_after_event
    AFTER INSERT ON meme_analytics_events
    FOR EACH ROW
BEGIN
    -- Update meme performance metrics
    INSERT OR REPLACE INTO meme_performance_metrics (
        meme_id, date, total_views, total_continues, total_skips, 
        total_auto_advances, avg_time_spent_seconds, skip_rate, continue_rate, error_count
    )
    SELECT 
        NEW.meme_id,
        DATE(NEW.event_timestamp),
        COUNT(CASE WHEN event_type = 'view' THEN 1 END),
        COUNT(CASE WHEN event_type = 'continue' THEN 1 END),
        COUNT(CASE WHEN event_type = 'skip' THEN 1 END),
        COUNT(CASE WHEN event_type = 'auto_advance' THEN 1 END),
        AVG(CASE WHEN time_spent_seconds > 0 THEN time_spent_seconds END),
        CASE 
            WHEN COUNT(CASE WHEN event_type IN ('view', 'continue', 'skip', 'auto_advance') THEN 1 END) > 0
            THEN (COUNT(CASE WHEN event_type = 'skip' THEN 1 END) * 100.0) / 
                 COUNT(CASE WHEN event_type IN ('view', 'continue', 'skip', 'auto_advance') THEN 1 END)
            ELSE 0
        END,
        CASE 
            WHEN COUNT(CASE WHEN event_type IN ('view', 'continue', 'skip', 'auto_advance') THEN 1 END) > 0
            THEN (COUNT(CASE WHEN event_type = 'continue' THEN 1 END) * 100.0) / 
                 COUNT(CASE WHEN event_type IN ('view', 'continue', 'skip', 'auto_advance') THEN 1 END)
            ELSE 0
        END,
        COUNT(CASE WHEN event_type = 'error' THEN 1 END)
    FROM meme_analytics_events 
    WHERE meme_id = NEW.meme_id 
    AND DATE(event_timestamp) = DATE(NEW.event_timestamp);
    
    -- Update category performance
    INSERT OR REPLACE INTO category_performance (
        category, date, total_views, total_continues, total_skips,
        avg_time_spent_seconds, skip_rate, continue_rate, unique_users
    )
    SELECT 
        m.category,
        DATE(NEW.event_timestamp),
        COUNT(CASE WHEN mae.event_type = 'view' THEN 1 END),
        COUNT(CASE WHEN mae.event_type = 'continue' THEN 1 END),
        COUNT(CASE WHEN mae.event_type = 'skip' THEN 1 END),
        AVG(CASE WHEN mae.time_spent_seconds > 0 THEN mae.time_spent_seconds END),
        CASE 
            WHEN COUNT(CASE WHEN mae.event_type IN ('view', 'continue', 'skip', 'auto_advance') THEN 1 END) > 0
            THEN (COUNT(CASE WHEN mae.event_type = 'skip' THEN 1 END) * 100.0) / 
                 COUNT(CASE WHEN mae.event_type IN ('view', 'continue', 'skip', 'auto_advance') THEN 1 END)
            ELSE 0
        END,
        CASE 
            WHEN COUNT(CASE WHEN mae.event_type IN ('view', 'continue', 'skip', 'auto_advance') THEN 1 END) > 0
            THEN (COUNT(CASE WHEN mae.event_type = 'continue' THEN 1 END) * 100.0) / 
                 COUNT(CASE WHEN mae.event_type IN ('view', 'continue', 'skip', 'auto_advance') THEN 1 END)
            ELSE 0
        END,
        COUNT(DISTINCT mae.user_id)
    FROM meme_analytics_events mae
    JOIN memes m ON mae.meme_id = m.id
    WHERE m.category = (SELECT category FROM memes WHERE id = NEW.meme_id)
    AND DATE(mae.event_timestamp) = DATE(NEW.event_timestamp);
END;

-- =====================================================
-- 10. SAMPLE DATA FOR TESTING
-- =====================================================

-- Sample user demographics
INSERT OR IGNORE INTO user_demographics (user_id, age_range, gender, income_range, education_level, location_state) VALUES
(1, '25-34', 'female', '50k-75k', 'bachelors', 'CA'),
(2, '35-44', 'male', '75k-100k', 'masters', 'NY'),
(3, '18-24', 'non-binary', 'under_25k', 'some_college', 'TX'),
(4, '45-54', 'female', '100k-150k', 'bachelors', 'FL'),
(5, '25-34', 'male', '50k-75k', 'high_school', 'IL');

-- Sample analytics events
INSERT OR IGNORE INTO meme_analytics_events (user_id, session_id, meme_id, event_type, time_spent_seconds, device_type, browser) VALUES
(1, 'session_001', 1, 'view', 8, 'mobile', 'Chrome'),
(1, 'session_001', 1, 'continue', 8, 'mobile', 'Chrome'),
(2, 'session_002', 2, 'view', 12, 'desktop', 'Firefox'),
(2, 'session_002', 2, 'skip', 12, 'desktop', 'Firefox'),
(3, 'session_003', 3, 'view', 5, 'mobile', 'Safari'),
(3, 'session_003', 3, 'auto_advance', 5, 'mobile', 'Safari');

-- =====================================================
-- SCHEMA CREATION COMPLETE
-- =====================================================
