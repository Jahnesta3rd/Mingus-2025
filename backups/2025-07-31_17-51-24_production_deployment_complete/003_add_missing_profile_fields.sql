-- Migration: Add Missing Profile Fields for Enhanced Onboarding
-- Date: 2025-01-27
-- Description: Add missing fields to user_profiles table to support detailed user onboarding

-- Add basic information fields
ALTER TABLE user_profiles ADD COLUMN first_name VARCHAR(100);
ALTER TABLE user_profiles ADD COLUMN last_name VARCHAR(100);
ALTER TABLE user_profiles ADD COLUMN gender VARCHAR(50);

-- Add location and household fields
ALTER TABLE user_profiles ADD COLUMN zip_code VARCHAR(10);
ALTER TABLE user_profiles ADD COLUMN dependents VARCHAR(50);
ALTER TABLE user_profiles ADD COLUMN relationship_status VARCHAR(50);

-- Add employment fields
ALTER TABLE user_profiles ADD COLUMN industry VARCHAR(100);
ALTER TABLE user_profiles ADD COLUMN job_title VARCHAR(100);
ALTER TABLE user_profiles ADD COLUMN naics_code VARCHAR(10);

-- Add indexes for better performance
CREATE INDEX IF NOT EXISTS idx_user_profiles_first_name ON user_profiles(first_name);
CREATE INDEX IF NOT EXISTS idx_user_profiles_last_name ON user_profiles(last_name);
CREATE INDEX IF NOT EXISTS idx_user_profiles_industry ON user_profiles(industry);
CREATE INDEX IF NOT EXISTS idx_user_profiles_employment_status ON user_profiles(employment_status);

-- migrations/006_add_progress_tracking.sql
CREATE TABLE IF NOT EXISTS onboarding_progress_saves (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    step_name VARCHAR(100) NOT NULL,
    step_data JSONB NOT NULL,
    saved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    synced_at TIMESTAMP,
    is_conflict BOOLEAN DEFAULT FALSE,
    conflict_resolved_at TIMESTAMP,
    device_id VARCHAR(255),
    session_id VARCHAR(255)
);

CREATE INDEX idx_progress_saves_user_step ON onboarding_progress_saves(user_id, step_name);
CREATE INDEX idx_progress_saves_synced ON onboarding_progress_saves(synced_at) WHERE synced_at IS NULL;

-- migrations/007_add_analytics_tables.sql
CREATE TABLE IF NOT EXISTS onboarding_analytics_events (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    event_name VARCHAR(100) NOT NULL,
    properties JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    session_id VARCHAR(255),
    device_id VARCHAR(255)
);

CREATE TABLE IF NOT EXISTS onboarding_feedback (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    step_name VARCHAR(100) NOT NULL,
    rating INTEGER CHECK (rating BETWEEN 1 AND 5),
    feedback_text TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS onboarding_dropoffs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    step_name VARCHAR(100) NOT NULL,
    dropoff_reason VARCHAR(255),
    time_spent_seconds INTEGER,
    session_duration_seconds INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create analytics views
CREATE OR REPLACE VIEW onboarding_dropoff_analysis AS
SELECT 
    step_name,
    COUNT(*) as dropoff_count,
    AVG(time_spent_seconds) as avg_time_spent,
    AVG(session_duration_seconds) as avg_session_duration,
    COUNT(*) * 100.0 / NULLIF((SELECT COUNT(*) FROM onboarding_analytics_events WHERE event_name = 'onboarding_started'), 0) as dropoff_rate
FROM onboarding_dropoffs
GROUP BY step_name
ORDER BY dropoff_count DESC;

-- migrations/008_add_referral_system.sql
CREATE TABLE IF NOT EXISTS referral_codes (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    code VARCHAR(20) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    usage_count INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS referral_invites (
    id SERIAL PRIMARY KEY,
    referrer_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    email VARCHAR(255) NOT NULL,
    message TEXT,
    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    opened_at TIMESTAMP,
    clicked_at TIMESTAMP,
    converted_at TIMESTAMP,
    converted_user_id INTEGER REFERENCES users(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS referral_rewards (
    id SERIAL PRIMARY KEY,
    referrer_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    referred_user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    reward_type VARCHAR(50) NOT NULL, -- 'premium_access', 'credits', 'badge'
    reward_value DECIMAL(10,2),
    awarded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_claimed BOOLEAN DEFAULT FALSE
);

-- Create indexes
CREATE INDEX idx_referral_codes_user ON referral_codes(user_id);
CREATE INDEX idx_referral_codes_code ON referral_codes(code);
CREATE INDEX idx_referral_invites_referrer ON referral_invites(referrer_id);
CREATE INDEX idx_referral_invites_email ON referral_invites(email);
CREATE INDEX idx_referral_rewards_referrer ON referral_rewards(referrer_id);

-- Create referral statistics view
CREATE OR REPLACE VIEW referral_stats AS
SELECT 
    u.id as user_id,
    u.name as user_name,
    COUNT(DISTINCT ri.id) as invites_sent,
    COUNT(DISTINCT CASE WHEN ri.converted_at IS NOT NULL THEN ri.id END) as invites_converted,
    COUNT(DISTINCT rr.id) as rewards_earned,
    COALESCE(SUM(rr.reward_value), 0) as total_reward_value
FROM users u
LEFT JOIN referral_invites ri ON u.id = ri.referrer_id
LEFT JOIN referral_rewards rr ON u.id = rr.referrer_id
GROUP BY u.id, u.name; 