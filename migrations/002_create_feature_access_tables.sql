-- Migration: Create Feature Access Tables
-- Description: Adds tables for feature access control, usage tracking, and trial management

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create feature_usage table for tracking monthly usage
CREATE TABLE IF NOT EXISTS feature_usage (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    feature_name VARCHAR(100) NOT NULL,
    usage_month DATE NOT NULL, -- First day of the month
    usage_count INTEGER DEFAULT 0,
    last_used_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Ensure one record per user per feature per month
    UNIQUE(user_id, feature_name, usage_month)
);

-- Create indexes for feature_usage table
CREATE INDEX IF NOT EXISTS idx_feature_usage_user_id ON feature_usage(user_id);
CREATE INDEX IF NOT EXISTS idx_feature_usage_feature_name ON feature_usage(feature_name);
CREATE INDEX IF NOT EXISTS idx_feature_usage_month ON feature_usage(usage_month);
CREATE INDEX IF NOT EXISTS idx_feature_usage_user_feature ON feature_usage(user_id, feature_name);

-- Create feature_trials table for managing trial periods
CREATE TABLE IF NOT EXISTS feature_trials (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    feature_name VARCHAR(100) NOT NULL,
    trial_start_date TIMESTAMP WITH TIME ZONE NOT NULL,
    trial_end_date TIMESTAMP WITH TIME ZONE NOT NULL,
    is_active BOOLEAN DEFAULT true,
    trial_used BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Ensure one trial per user per feature
    UNIQUE(user_id, feature_name)
);

-- Create indexes for feature_trials table
CREATE INDEX IF NOT EXISTS idx_feature_trials_user_id ON feature_trials(user_id);
CREATE INDEX IF NOT EXISTS idx_feature_trials_feature_name ON feature_trials(feature_name);
CREATE INDEX IF NOT EXISTS idx_feature_trials_active ON feature_trials(is_active);
CREATE INDEX IF NOT EXISTS idx_feature_trials_dates ON feature_trials(trial_start_date, trial_end_date);

-- Create feature_access_logs table for audit trail
CREATE TABLE IF NOT EXISTS feature_access_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    feature_name VARCHAR(100) NOT NULL,
    access_granted BOOLEAN NOT NULL,
    access_reason VARCHAR(100) NOT NULL, -- 'access_granted', 'upgrade_required', 'usage_limit_exceeded', etc.
    current_tier VARCHAR(50),
    required_tier VARCHAR(50),
    current_usage JSONB, -- Store current usage as JSON
    usage_limits JSONB, -- Store usage limits as JSON
    ip_address INET,
    user_agent TEXT,
    endpoint VARCHAR(255),
    metadata JSONB, -- Additional context
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for feature_access_logs table
CREATE INDEX IF NOT EXISTS idx_feature_access_logs_user_id ON feature_access_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_feature_access_logs_feature_name ON feature_access_logs(feature_name);
CREATE INDEX IF NOT EXISTS idx_feature_access_logs_access_granted ON feature_access_logs(access_granted);
CREATE INDEX IF NOT EXISTS idx_feature_access_logs_created_at ON feature_access_logs(created_at);

-- Create upgrade_prompts table for tracking upgrade interactions
CREATE TABLE IF NOT EXISTS upgrade_prompts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    feature_name VARCHAR(100) NOT NULL,
    prompt_type VARCHAR(50) NOT NULL, -- 'upgrade_required', 'usage_limit', 'trial_ending'
    current_tier VARCHAR(50) NOT NULL,
    target_tier VARCHAR(50) NOT NULL,
    prompt_shown_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    user_action VARCHAR(50), -- 'upgraded', 'started_trial', 'dismissed', 'learned_more'
    action_taken_at TIMESTAMP WITH TIME ZONE,
    conversion_successful BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for upgrade_prompts table
CREATE INDEX IF NOT EXISTS idx_upgrade_prompts_user_id ON upgrade_prompts(user_id);
CREATE INDEX IF NOT EXISTS idx_upgrade_prompts_feature_name ON upgrade_prompts(feature_name);
CREATE INDEX IF NOT EXISTS idx_upgrade_prompts_prompt_type ON upgrade_prompts(prompt_type);
CREATE INDEX IF NOT EXISTS idx_upgrade_prompts_conversion ON upgrade_prompts(conversion_successful);

-- Create educational_content_views table for tracking educational content engagement
CREATE TABLE IF NOT EXISTS educational_content_views (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    content_category VARCHAR(100) NOT NULL, -- 'health_wellness', 'financial_planning', etc.
    content_type VARCHAR(50) NOT NULL, -- 'modal', 'page', 'tooltip'
    time_spent_seconds INTEGER,
    content_completed BOOLEAN DEFAULT false,
    user_action VARCHAR(50), -- 'upgraded', 'started_trial', 'dismissed'
    viewed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for educational_content_views table
CREATE INDEX IF NOT EXISTS idx_educational_content_views_user_id ON educational_content_views(user_id);
CREATE INDEX IF NOT EXISTS idx_educational_content_views_category ON educational_content_views(content_category);
CREATE INDEX IF NOT EXISTS idx_educational_content_views_viewed_at ON educational_content_views(viewed_at);

-- Create feature_grace_periods table for managing grace periods
CREATE TABLE IF NOT EXISTS feature_grace_periods (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    subscription_id UUID NOT NULL REFERENCES subscriptions(id) ON DELETE CASCADE,
    grace_period_start TIMESTAMP WITH TIME ZONE NOT NULL,
    grace_period_end TIMESTAMP WITH TIME ZONE NOT NULL,
    grace_period_reason VARCHAR(100) NOT NULL, -- 'payment_failed', 'subscription_expired'
    features_restricted JSONB, -- List of features that are restricted during grace period
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for feature_grace_periods table
CREATE INDEX IF NOT EXISTS idx_feature_grace_periods_user_id ON feature_grace_periods(user_id);
CREATE INDEX IF NOT EXISTS idx_feature_grace_periods_subscription_id ON feature_grace_periods(subscription_id);
CREATE INDEX IF NOT EXISTS idx_feature_grace_periods_active ON feature_grace_periods(is_active);
CREATE INDEX IF NOT EXISTS idx_feature_grace_periods_dates ON feature_grace_periods(grace_period_start, grace_period_end);

-- Add comments for documentation
COMMENT ON TABLE feature_usage IS 'Tracks monthly usage of features by users';
COMMENT ON TABLE feature_trials IS 'Manages trial periods for premium features';
COMMENT ON TABLE feature_access_logs IS 'Audit trail for feature access attempts';
COMMENT ON TABLE upgrade_prompts IS 'Tracks upgrade prompt interactions and conversions';
COMMENT ON TABLE educational_content_views IS 'Tracks user engagement with educational content';
COMMENT ON TABLE feature_grace_periods IS 'Manages grace periods for users with payment issues';

-- Create functions for common operations

-- Function to increment feature usage
CREATE OR REPLACE FUNCTION increment_feature_usage(
    p_user_id UUID,
    p_feature_name VARCHAR(100),
    p_usage_month DATE DEFAULT NULL
)
RETURNS INTEGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_usage_count INTEGER;
    v_month DATE;
BEGIN
    -- Default to current month if not specified
    v_month := COALESCE(p_usage_month, DATE_TRUNC('month', NOW())::DATE);
    
    -- Insert or update usage record
    INSERT INTO feature_usage (user_id, feature_name, usage_month, usage_count, last_used_at)
    VALUES (p_user_id, p_feature_name, v_month, 1, NOW())
    ON CONFLICT (user_id, feature_name, usage_month)
    DO UPDATE SET 
        usage_count = feature_usage.usage_count + 1,
        last_used_at = NOW(),
        updated_at = NOW()
    RETURNING usage_count INTO v_usage_count;
    
    RETURN v_usage_count;
END;
$$;

-- Function to check if user can use feature
CREATE OR REPLACE FUNCTION can_use_feature(
    p_user_id UUID,
    p_feature_name VARCHAR(100),
    p_usage_month DATE DEFAULT NULL
)
RETURNS BOOLEAN
LANGUAGE plpgsql
AS $$
DECLARE
    v_user_tier VARCHAR(50);
    v_feature_limit INTEGER;
    v_current_usage INTEGER;
    v_month DATE;
    v_has_trial BOOLEAN;
    v_trial_active BOOLEAN;
BEGIN
    -- Default to current month if not specified
    v_month := COALESCE(p_usage_month, DATE_TRUNC('month', NOW())::DATE);
    
    -- Get user's current tier
    SELECT tier_type INTO v_user_tier
    FROM subscriptions s
    JOIN pricing_tiers pt ON s.pricing_tier_id = pt.id
    WHERE s.user_id = p_user_id AND s.status = 'active'
    ORDER BY s.created_at DESC
    LIMIT 1;
    
    -- If no subscription, check for trial
    IF v_user_tier IS NULL THEN
        SELECT EXISTS(
            SELECT 1 FROM feature_trials 
            WHERE user_id = p_user_id 
            AND feature_name = p_feature_name 
            AND is_active = true
            AND trial_start_date <= NOW()
            AND trial_end_date >= NOW()
        ) INTO v_trial_active;
        
        RETURN v_trial_active;
    END IF;
    
    -- Get feature limit for user's tier
    SELECT 
        CASE 
            WHEN v_user_tier = 'budget' THEN
                CASE p_feature_name
                    WHEN 'health_checkin' THEN 4
                    WHEN 'financial_reports' THEN 2
                    WHEN 'ai_insights' THEN 0
                    WHEN 'custom_reports' THEN 0
                    WHEN 'career_risk_management' THEN 0
                    WHEN 'data_export' THEN 0
                    WHEN 'api_access' THEN 0
                    ELSE 0
                END
            WHEN v_user_tier = 'mid_tier' THEN
                CASE p_feature_name
                    WHEN 'health_checkin' THEN 12
                    WHEN 'financial_reports' THEN 10
                    WHEN 'ai_insights' THEN 50
                    WHEN 'custom_reports' THEN 5
                    WHEN 'career_risk_management' THEN -1 -- Unlimited
                    WHEN 'data_export' THEN 5
                    WHEN 'api_access' THEN 0
                    ELSE 0
                END
            WHEN v_user_tier = 'professional' THEN
                -1 -- Unlimited for all features
            ELSE
                0
        END INTO v_feature_limit;
    
    -- If unlimited, return true
    IF v_feature_limit = -1 THEN
        RETURN true;
    END IF;
    
    -- If feature not available for tier, return false
    IF v_feature_limit = 0 THEN
        RETURN false;
    END IF;
    
    -- Get current usage
    SELECT COALESCE(usage_count, 0) INTO v_current_usage
    FROM feature_usage
    WHERE user_id = p_user_id 
    AND feature_name = p_feature_name 
    AND usage_month = v_month;
    
    -- Return true if usage is within limit
    RETURN v_current_usage < v_feature_limit;
END;
$$;

-- Function to log feature access attempt
CREATE OR REPLACE FUNCTION log_feature_access(
    p_user_id UUID,
    p_feature_name VARCHAR(100),
    p_access_granted BOOLEAN,
    p_access_reason VARCHAR(100),
    p_current_tier VARCHAR(50) DEFAULT NULL,
    p_required_tier VARCHAR(50) DEFAULT NULL,
    p_current_usage JSONB DEFAULT NULL,
    p_usage_limits JSONB DEFAULT NULL,
    p_ip_address INET DEFAULT NULL,
    p_user_agent TEXT DEFAULT NULL,
    p_endpoint VARCHAR(255) DEFAULT NULL,
    p_metadata JSONB DEFAULT NULL
)
RETURNS UUID
LANGUAGE plpgsql
AS $$
DECLARE
    v_log_id UUID;
BEGIN
    INSERT INTO feature_access_logs (
        user_id, feature_name, access_granted, access_reason,
        current_tier, required_tier, current_usage, usage_limits,
        ip_address, user_agent, endpoint, metadata
    ) VALUES (
        p_user_id, p_feature_name, p_access_granted, p_access_reason,
        p_current_tier, p_required_tier, p_current_usage, p_usage_limits,
        p_ip_address, p_user_agent, p_endpoint, p_metadata
    ) RETURNING id INTO v_log_id;
    
    RETURN v_log_id;
END;
$$;

-- Function to start feature trial
CREATE OR REPLACE FUNCTION start_feature_trial(
    p_user_id UUID,
    p_feature_name VARCHAR(100),
    p_duration_days INTEGER DEFAULT 7
)
RETURNS BOOLEAN
LANGUAGE plpgsql
AS $$
DECLARE
    v_trial_start TIMESTAMP WITH TIME ZONE;
    v_trial_end TIMESTAMP WITH TIME ZONE;
    v_existing_trial BOOLEAN;
BEGIN
    -- Check if user already has a trial for this feature
    SELECT EXISTS(
        SELECT 1 FROM feature_trials 
        WHERE user_id = p_user_id AND feature_name = p_feature_name
    ) INTO v_existing_trial;
    
    IF v_existing_trial THEN
        RETURN false; -- Trial already exists
    END IF;
    
    -- Set trial dates
    v_trial_start := NOW();
    v_trial_end := v_trial_start + (p_duration_days || ' days')::INTERVAL;
    
    -- Insert trial record
    INSERT INTO feature_trials (
        user_id, feature_name, trial_start_date, trial_end_date, is_active
    ) VALUES (
        p_user_id, p_feature_name, v_trial_start, v_trial_end, true
    );
    
    RETURN true;
END;
$$;

-- Create triggers for automatic updates

-- Trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply trigger to relevant tables
CREATE TRIGGER update_feature_usage_updated_at 
    BEFORE UPDATE ON feature_usage 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_feature_trials_updated_at 
    BEFORE UPDATE ON feature_trials 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_feature_grace_periods_updated_at 
    BEFORE UPDATE ON feature_grace_periods 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insert sample data for testing (optional)
-- This can be removed in production

-- Sample feature usage records
INSERT INTO feature_usage (user_id, feature_name, usage_month, usage_count, last_used_at)
SELECT 
    u.id,
    'health_checkin',
    DATE_TRUNC('month', NOW())::DATE,
    FLOOR(RANDOM() * 3) + 1,
    NOW() - (RANDOM() * INTERVAL '30 days')
FROM users u
WHERE u.id IN (SELECT id FROM users LIMIT 10)
ON CONFLICT DO NOTHING;

-- Sample trial records
INSERT INTO feature_trials (user_id, feature_name, trial_start_date, trial_end_date, is_active)
SELECT 
    u.id,
    'ai_insights',
    NOW() - INTERVAL '3 days',
    NOW() + INTERVAL '4 days',
    true
FROM users u
WHERE u.id IN (SELECT id FROM users LIMIT 5)
ON CONFLICT DO NOTHING; 