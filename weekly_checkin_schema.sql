-- =====================================================
-- Mingus Personal Finance App - Weekly Check-in Schema
-- SQLite Database Schema for Weekly Check-in System
-- =====================================================

-- Enable foreign key constraints
PRAGMA foreign_keys = ON;

-- =====================================================
-- 1. WEEKLY CHECK-IN TABLE
-- =====================================================
CREATE TABLE IF NOT EXISTS weekly_checkins (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    session_id TEXT,
    check_in_date DATE NOT NULL,
    week_start_date DATE NOT NULL,
    
    -- Health & Wellness Data
    physical_activity INTEGER DEFAULT 0, -- workouts this week
    relationship_satisfaction INTEGER CHECK (relationship_satisfaction BETWEEN 1 AND 10), -- 1-10 scale
    meditation_minutes INTEGER DEFAULT 0, -- total minutes
    stress_spending DECIMAL(10,2) DEFAULT 0.0, -- dollars spent when stressed
    
    -- Vehicle & Transportation Data
    vehicle_expenses DECIMAL(10,2) DEFAULT 0.0, -- unexpected vehicle costs this week
    transportation_stress INTEGER CHECK (transportation_stress BETWEEN 1 AND 5), -- 1-5 scale
    commute_satisfaction INTEGER CHECK (commute_satisfaction BETWEEN 1 AND 5), -- 1-5 scale
    vehicle_decisions TEXT, -- financial decisions made this week
    
    -- Metadata
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    -- Ensure one check-in per user per week
    UNIQUE(user_id, week_start_date)
);

-- =====================================================
-- 2. WEEKLY CHECK-IN ANALYTICS TABLE
-- =====================================================
CREATE TABLE IF NOT EXISTS weekly_checkin_analytics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    analysis_date DATE NOT NULL,
    
    -- Health Analytics
    avg_physical_activity REAL,
    avg_relationship_satisfaction REAL,
    avg_meditation_minutes REAL,
    avg_stress_spending REAL,
    health_trend TEXT, -- 'improving', 'stable', 'declining'
    
    -- Vehicle Analytics
    avg_vehicle_expenses REAL,
    avg_transportation_stress REAL,
    avg_commute_satisfaction REAL,
    vehicle_expense_trend TEXT, -- 'increasing', 'stable', 'decreasing'
    transportation_stress_trend TEXT, -- 'improving', 'stable', 'worsening'
    
    -- Combined Insights
    overall_wellness_score REAL, -- calculated score 1-10
    financial_stress_level TEXT, -- 'low', 'medium', 'high'
    recommendations TEXT, -- JSON array of recommendations
    
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, analysis_date)
);

-- =====================================================
-- 3. WEEKLY CHECK-IN INSIGHTS TABLE
-- =====================================================
CREATE TABLE IF NOT EXISTS weekly_checkin_insights (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    insight_type TEXT NOT NULL CHECK (insight_type IN (
        'health_improvement',
        'health_decline',
        'vehicle_cost_spike',
        'transportation_stress',
        'commute_satisfaction',
        'financial_decision',
        'wellness_correlation'
    )),
    insight_data TEXT NOT NULL, -- JSON data
    priority TEXT NOT NULL CHECK (priority IN ('low', 'medium', 'high', 'critical')),
    is_actionable BOOLEAN DEFAULT 1,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    expires_at DATETIME
);

-- =====================================================
-- 4. INDEXES FOR PERFORMANCE
-- =====================================================

-- Indexes for weekly_checkins table
CREATE INDEX IF NOT EXISTS idx_weekly_checkins_user_id ON weekly_checkins(user_id);
CREATE INDEX IF NOT EXISTS idx_weekly_checkins_date ON weekly_checkins(check_in_date);
CREATE INDEX IF NOT EXISTS idx_weekly_checkins_week_start ON weekly_checkins(week_start_date);
CREATE INDEX IF NOT EXISTS idx_weekly_checkins_user_week ON weekly_checkins(user_id, week_start_date);

-- Indexes for analytics table
CREATE INDEX IF NOT EXISTS idx_weekly_analytics_user_id ON weekly_checkin_analytics(user_id);
CREATE INDEX IF NOT EXISTS idx_weekly_analytics_date ON weekly_checkin_analytics(analysis_date);
CREATE INDEX IF NOT EXISTS idx_weekly_analytics_user_date ON weekly_checkin_analytics(user_id, analysis_date);

-- Indexes for insights table
CREATE INDEX IF NOT EXISTS idx_weekly_insights_user_id ON weekly_checkin_insights(user_id);
CREATE INDEX IF NOT EXISTS idx_weekly_insights_type ON weekly_checkin_insights(insight_type);
CREATE INDEX IF NOT EXISTS idx_weekly_insights_priority ON weekly_checkin_insights(priority);
CREATE INDEX IF NOT EXISTS idx_weekly_insights_expires ON weekly_checkin_insights(expires_at);

-- =====================================================
-- 5. TRIGGERS FOR AUTOMATIC TIMESTAMP UPDATES
-- =====================================================

-- Trigger to update updated_at timestamp on weekly_checkins table
CREATE TRIGGER IF NOT EXISTS update_weekly_checkins_timestamp 
    AFTER UPDATE ON weekly_checkins
    FOR EACH ROW
BEGIN
    UPDATE weekly_checkins SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- =====================================================
-- 6. USEFUL QUERIES FOR THE APPLICATION
-- =====================================================

-- Query to get latest check-in for a user
-- SELECT * FROM weekly_checkins WHERE user_id = ? ORDER BY check_in_date DESC LIMIT 1;

-- Query to get check-in history for analytics
-- SELECT * FROM weekly_checkins WHERE user_id = ? AND check_in_date >= ? ORDER BY check_in_date;

-- Query to get weekly averages for a user
-- SELECT 
--     AVG(physical_activity) as avg_physical_activity,
--     AVG(relationship_satisfaction) as avg_relationship_satisfaction,
--     AVG(meditation_minutes) as avg_meditation_minutes,
--     AVG(stress_spending) as avg_stress_spending,
--     AVG(vehicle_expenses) as avg_vehicle_expenses,
--     AVG(transportation_stress) as avg_transportation_stress,
--     AVG(commute_satisfaction) as avg_commute_satisfaction
-- FROM weekly_checkins 
-- WHERE user_id = ? AND check_in_date >= ?;

-- Query to detect trends
-- SELECT 
--     week_start_date,
--     vehicle_expenses,
--     LAG(vehicle_expenses) OVER (ORDER BY week_start_date) as prev_vehicle_expenses,
--     vehicle_expenses - LAG(vehicle_expenses) OVER (ORDER BY week_start_date) as expense_change
-- FROM weekly_checkins 
-- WHERE user_id = ? 
-- ORDER BY week_start_date;

-- =====================================================
-- 7. SAMPLE DATA (for testing)
-- =====================================================

-- Sample weekly check-in data
INSERT INTO weekly_checkins (
    user_id, 
    check_in_date, 
    week_start_date,
    physical_activity, 
    relationship_satisfaction, 
    meditation_minutes, 
    stress_spending,
    vehicle_expenses,
    transportation_stress,
    commute_satisfaction,
    vehicle_decisions
) VALUES
('user_123', '2025-01-15', '2025-01-13', 3, 8, 45, 120.00, 0.00, 2, 4, 'No major vehicle decisions this week'),
('user_123', '2025-01-22', '2025-01-20', 4, 7, 60, 80.00, 150.00, 3, 3, 'Got new tires, researched insurance options'),
('user_123', '2025-01-29', '2025-01-27', 2, 9, 30, 200.00, 75.00, 1, 5, 'Scheduled routine maintenance, found cheaper gas station');

-- =====================================================
-- SCHEMA CREATION COMPLETE
-- =====================================================
