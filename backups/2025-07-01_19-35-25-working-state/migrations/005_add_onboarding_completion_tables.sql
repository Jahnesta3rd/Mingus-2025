-- Migration: Add onboarding completion tables
-- Description: Creates tables for reminder schedules, user preferences, and onboarding completion tracking

-- Create reminder_schedules table
CREATE TABLE IF NOT EXISTS reminder_schedules (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    reminder_type VARCHAR(50) NOT NULL,
    scheduled_date TIMESTAMP NOT NULL,
    frequency VARCHAR(20) DEFAULT 'weekly',
    enabled BOOLEAN DEFAULT TRUE,
    preferences JSONB,
    message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create user_preferences table
CREATE TABLE IF NOT EXISTS user_preferences (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE UNIQUE,
    email_notifications BOOLEAN DEFAULT TRUE,
    push_notifications BOOLEAN DEFAULT TRUE,
    sms_notifications BOOLEAN DEFAULT FALSE,
    reminder_preferences JSONB,
    preferred_communication VARCHAR(20) DEFAULT 'email',
    communication_frequency VARCHAR(20) DEFAULT 'weekly',
    share_anonymized_data BOOLEAN DEFAULT TRUE,
    allow_marketing_emails BOOLEAN DEFAULT TRUE,
    theme_preference VARCHAR(20) DEFAULT 'light',
    language_preference VARCHAR(10) DEFAULT 'en',
    onboarding_completed BOOLEAN DEFAULT FALSE,
    first_checkin_scheduled BOOLEAN DEFAULT FALSE,
    mobile_app_downloaded BOOLEAN DEFAULT FALSE,
    custom_preferences JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create onboarding_completion_events table
CREATE TABLE IF NOT EXISTS onboarding_completion_events (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    event_type VARCHAR(50) NOT NULL, -- 'onboarding_completed', 'first_checkin_scheduled', 'mobile_app_downloaded'
    event_data JSONB,
    completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_reminder_schedules_user_id ON reminder_schedules(user_id);
CREATE INDEX IF NOT EXISTS idx_reminder_schedules_type ON reminder_schedules(reminder_type);
CREATE INDEX IF NOT EXISTS idx_reminder_schedules_scheduled_date ON reminder_schedules(scheduled_date);
CREATE INDEX IF NOT EXISTS idx_reminder_schedules_enabled ON reminder_schedules(enabled);

CREATE INDEX IF NOT EXISTS idx_user_preferences_user_id ON user_preferences(user_id);
CREATE INDEX IF NOT EXISTS idx_user_preferences_onboarding_completed ON user_preferences(onboarding_completed);

CREATE INDEX IF NOT EXISTS idx_onboarding_completion_events_user_id ON onboarding_completion_events(user_id);
CREATE INDEX IF NOT EXISTS idx_onboarding_completion_events_type ON onboarding_completion_events(event_type);
CREATE INDEX IF NOT EXISTS idx_onboarding_completion_events_completed_at ON onboarding_completion_events(completed_at);

-- Add RLS policies for reminder_schedules
ALTER TABLE reminder_schedules ENABLE ROW LEVEL SECURITY;

CREATE POLICY reminder_schedules_select_policy ON reminder_schedules
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY reminder_schedules_insert_policy ON reminder_schedules
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY reminder_schedules_update_policy ON reminder_schedules
    FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY reminder_schedules_delete_policy ON reminder_schedules
    FOR DELETE USING (auth.uid() = user_id);

-- Add RLS policies for user_preferences
ALTER TABLE user_preferences ENABLE ROW LEVEL SECURITY;

CREATE POLICY user_preferences_select_policy ON user_preferences
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY user_preferences_insert_policy ON user_preferences
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY user_preferences_update_policy ON user_preferences
    FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY user_preferences_delete_policy ON user_preferences
    FOR DELETE USING (auth.uid() = user_id);

-- Add RLS policies for onboarding_completion_events
ALTER TABLE onboarding_completion_events ENABLE ROW LEVEL SECURITY;

CREATE POLICY onboarding_completion_events_select_policy ON onboarding_completion_events
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY onboarding_completion_events_insert_policy ON onboarding_completion_events
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY onboarding_completion_events_update_policy ON onboarding_completion_events
    FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY onboarding_completion_events_delete_policy ON onboarding_completion_events
    FOR DELETE USING (auth.uid() = user_id);

-- Add columns to existing users table if they don't exist
DO $$ 
BEGIN
    -- Add onboarding_completed column if it doesn't exist
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'users' AND column_name = 'onboarding_completed') THEN
        ALTER TABLE users ADD COLUMN onboarding_completed BOOLEAN DEFAULT FALSE;
    END IF;
    
    -- Add onboarding_completed_at column if it doesn't exist
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'users' AND column_name = 'onboarding_completed_at') THEN
        ALTER TABLE users ADD COLUMN onboarding_completed_at TIMESTAMP;
    END IF;
    
    -- Add first_checkin_scheduled column if it doesn't exist
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'users' AND column_name = 'first_checkin_scheduled') THEN
        ALTER TABLE users ADD COLUMN first_checkin_scheduled BOOLEAN DEFAULT FALSE;
    END IF;
    
    -- Add mobile_app_downloaded column if it doesn't exist
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'users' AND column_name = 'mobile_app_downloaded') THEN
        ALTER TABLE users ADD COLUMN mobile_app_downloaded BOOLEAN DEFAULT FALSE;
    END IF;
END $$;

-- Create indexes for new user columns
CREATE INDEX IF NOT EXISTS idx_users_onboarding_completed ON users(onboarding_completed);
CREATE INDEX IF NOT EXISTS idx_users_onboarding_completed_at ON users(onboarding_completed_at);
CREATE INDEX IF NOT EXISTS idx_users_first_checkin_scheduled ON users(first_checkin_scheduled);
CREATE INDEX IF NOT EXISTS idx_users_mobile_app_downloaded ON users(mobile_app_downloaded);

-- Insert default preferences for existing users
INSERT INTO user_preferences (user_id, email_notifications, push_notifications, sms_notifications, reminder_preferences, preferred_communication, communication_frequency, share_anonymized_data, allow_marketing_emails, theme_preference, language_preference, onboarding_completed, first_checkin_scheduled, mobile_app_downloaded, custom_preferences)
SELECT 
    u.id,
    TRUE,
    TRUE,
    FALSE,
    '{"enabled": true, "frequency": "weekly", "day": "wednesday", "time": "10:00", "email": true, "push": true}'::jsonb,
    'email',
    'weekly',
    TRUE,
    TRUE,
    'light',
    'en',
    COALESCE(u.onboarding_completed, FALSE),
    COALESCE(u.first_checkin_scheduled, FALSE),
    COALESCE(u.mobile_app_downloaded, FALSE),
    '{}'::jsonb
FROM users u
WHERE NOT EXISTS (
    SELECT 1 FROM user_preferences up WHERE up.user_id = u.id
);

-- Create function to update user onboarding status
CREATE OR REPLACE FUNCTION update_user_onboarding_status(
    p_user_id INTEGER,
    p_onboarding_completed BOOLEAN DEFAULT NULL,
    p_first_checkin_scheduled BOOLEAN DEFAULT NULL,
    p_mobile_app_downloaded BOOLEAN DEFAULT NULL
) RETURNS VOID AS $$
BEGIN
    UPDATE users 
    SET 
        onboarding_completed = COALESCE(p_onboarding_completed, onboarding_completed),
        onboarding_completed_at = CASE 
            WHEN p_onboarding_completed = TRUE AND onboarding_completed_at IS NULL 
            THEN CURRENT_TIMESTAMP 
            ELSE onboarding_completed_at 
        END,
        first_checkin_scheduled = COALESCE(p_first_checkin_scheduled, first_checkin_scheduled),
        mobile_app_downloaded = COALESCE(p_mobile_app_downloaded, mobile_app_downloaded),
        updated_at = CURRENT_TIMESTAMP
    WHERE id = p_user_id;
    
    -- Also update user_preferences table
    UPDATE user_preferences 
    SET 
        onboarding_completed = COALESCE(p_onboarding_completed, onboarding_completed),
        first_checkin_scheduled = COALESCE(p_first_checkin_scheduled, first_checkin_scheduled),
        mobile_app_downloaded = COALESCE(p_mobile_app_downloaded, mobile_app_downloaded),
        updated_at = CURRENT_TIMESTAMP
    WHERE user_id = p_user_id;
END;
$$ LANGUAGE plpgsql;

-- Create function to get user onboarding progress
CREATE OR REPLACE FUNCTION get_user_onboarding_progress(p_user_id INTEGER)
RETURNS TABLE(
    onboarding_completed BOOLEAN,
    first_checkin_scheduled BOOLEAN,
    mobile_app_downloaded BOOLEAN,
    profile_completion_percentage INTEGER,
    goals_count INTEGER,
    preferences_configured BOOLEAN
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        u.onboarding_completed,
        u.first_checkin_scheduled,
        u.mobile_app_downloaded,
        CASE 
            WHEN u.name IS NOT NULL AND u.email IS NOT NULL AND u.phone IS NOT NULL 
            THEN 100
            WHEN u.name IS NOT NULL AND u.email IS NOT NULL 
            THEN 67
            WHEN u.name IS NOT NULL OR u.email IS NOT NULL 
            THEN 33
            ELSE 0
        END as profile_completion_percentage,
        COALESCE(ug.goals_count, 0) as goals_count,
        up.id IS NOT NULL as preferences_configured
    FROM users u
    LEFT JOIN (
        SELECT user_id, COUNT(*) as goals_count 
        FROM user_goals 
        WHERE user_id = p_user_id 
        GROUP BY user_id
    ) ug ON ug.user_id = u.id
    LEFT JOIN user_preferences up ON up.user_id = u.id
    WHERE u.id = p_user_id;
END;
$$ LANGUAGE plpgsql;

-- Create function to schedule first check-in
CREATE OR REPLACE FUNCTION schedule_first_checkin(
    p_user_id INTEGER,
    p_frequency VARCHAR(20) DEFAULT 'weekly',
    p_day VARCHAR(20) DEFAULT 'wednesday',
    p_time VARCHAR(5) DEFAULT '10:00'
) RETURNS TIMESTAMP AS $$
DECLARE
    v_scheduled_date TIMESTAMP;
    v_day_number INTEGER;
BEGIN
    -- Map day names to numbers (0=Monday, 6=Sunday)
    v_day_number := CASE p_day
        WHEN 'monday' THEN 0
        WHEN 'tuesday' THEN 1
        WHEN 'wednesday' THEN 2
        WHEN 'thursday' THEN 3
        WHEN 'friday' THEN 4
        WHEN 'saturday' THEN 5
        WHEN 'sunday' THEN 6
        ELSE 2 -- Default to Wednesday
    END;
    
    -- Calculate next occurrence of the target day
    v_scheduled_date := CURRENT_DATE + 
        (v_day_number - EXTRACT(DOW FROM CURRENT_DATE) + 7) % 7 + 
        INTERVAL p_time;
    
    -- Insert reminder schedule
    INSERT INTO reminder_schedules (
        user_id, 
        reminder_type, 
        scheduled_date, 
        frequency, 
        enabled, 
        preferences
    ) VALUES (
        p_user_id,
        'first_checkin',
        v_scheduled_date,
        p_frequency,
        TRUE,
        jsonb_build_object(
            'enabled', TRUE,
            'frequency', p_frequency,
            'day', p_day,
            'time', p_time,
            'email', TRUE,
            'push', TRUE
        )
    );
    
    -- Update user status
    PERFORM update_user_onboarding_status(p_user_id, NULL, TRUE, NULL);
    
    RETURN v_scheduled_date;
END;
$$ LANGUAGE plpgsql;

-- Create view for community statistics
CREATE OR REPLACE VIEW community_stats AS
SELECT 
    COUNT(*) as total_members,
    COUNT(CASE WHEN last_login >= CURRENT_DATE - INTERVAL '7 days' THEN 1 END) as active_this_week,
    COUNT(CASE WHEN onboarding_completed = TRUE THEN 1 END) as completed_onboarding,
    COUNT(CASE WHEN first_checkin_scheduled = TRUE THEN 1 END) as scheduled_checkins,
    COUNT(CASE WHEN mobile_app_downloaded = TRUE THEN 1 END) as mobile_users,
    ROUND(AVG(CASE WHEN onboarding_completed = TRUE THEN 1 ELSE 0 END) * 100, 1) as onboarding_completion_rate
FROM users;

-- Grant necessary permissions
GRANT SELECT, INSERT, UPDATE, DELETE ON reminder_schedules TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON user_preferences TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON onboarding_completion_events TO authenticated;
GRANT SELECT ON community_stats TO authenticated;
GRANT EXECUTE ON FUNCTION update_user_onboarding_status TO authenticated;
GRANT EXECUTE ON FUNCTION get_user_onboarding_progress TO authenticated;
GRANT EXECUTE ON FUNCTION schedule_first_checkin TO authenticated; 