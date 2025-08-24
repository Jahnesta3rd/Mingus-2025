-- Migration: Enhance Communication Preferences System
-- Date: 2025-01-27
-- Description: Enhances communication preferences system with new fields and tables

-- Create enum types for user segments
CREATE TYPE user_segment AS ENUM (
    'new_user', 'premium_subscriber', 'at_risk_user', 'high_engagement', 'inactive'
);

-- Add new columns to communication_preferences table
ALTER TABLE communication_preferences 
ADD COLUMN preferred_sms_time TIME DEFAULT '09:00:00',
ADD COLUMN preferred_email_day INTEGER DEFAULT 1,
ADD COLUMN alert_types_sms JSONB DEFAULT '{
    "critical_financial": true,
    "bill_reminders": true,
    "budget_alerts": true,
    "emergency_fund": true,
    "daily_checkin": false,
    "weekly_report": false,
    "monthly_analysis": false,
    "career_insights": false,
    "wellness_tips": false,
    "spending_patterns": false,
    "subscription_updates": false,
    "marketing_content": false
}',
ADD COLUMN alert_types_email JSONB DEFAULT '{
    "critical_financial": true,
    "bill_reminders": true,
    "budget_alerts": true,
    "emergency_fund": true,
    "daily_checkin": true,
    "weekly_report": true,
    "monthly_analysis": true,
    "career_insights": true,
    "wellness_tips": true,
    "spending_patterns": true,
    "subscription_updates": true,
    "marketing_content": false
}',
ADD COLUMN frequency_preference frequency_type DEFAULT 'weekly',
ADD COLUMN user_segment user_segment DEFAULT 'new_user';

-- Update existing preferred_sms_time and preferred_email_time columns
ALTER TABLE communication_preferences 
ALTER COLUMN preferred_sms_time TYPE TIME USING preferred_sms_time::time,
ALTER COLUMN preferred_email_time TYPE TIME USING preferred_email_time::time;

-- Create sms_consent table for TCPA compliance
CREATE TABLE sms_consent (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Phone number verification
    phone_number VARCHAR(20) NOT NULL,
    phone_verified BOOLEAN DEFAULT FALSE,
    verification_code VARCHAR(10),
    verification_expires_at TIMESTAMP WITH TIME ZONE,
    
    -- TCPA compliance fields
    consent_granted BOOLEAN DEFAULT FALSE,
    consent_granted_at TIMESTAMP WITH TIME ZONE,
    consent_source VARCHAR(100) NOT NULL, -- 'web_form', 'mobile_app', 'api', 'sms_reply'
    ip_address VARCHAR(45),
    user_agent TEXT,
    
    -- Opt-out tracking
    opted_out BOOLEAN DEFAULT FALSE,
    opted_out_at TIMESTAMP WITH TIME ZONE,
    opt_out_reason VARCHAR(200),
    opt_out_method VARCHAR(50), -- 'sms_stop', 'web_form', 'api'
    
    -- Re-engagement
    re_engaged BOOLEAN DEFAULT FALSE,
    re_engaged_at TIMESTAMP WITH TIME ZONE,
    re_engagement_method VARCHAR(50),
    
    -- Compliance tracking
    last_message_sent_at TIMESTAMP WITH TIME ZONE,
    messages_sent_count INTEGER DEFAULT 0,
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(user_id)
);

-- Create indexes for sms_consent
CREATE INDEX idx_sms_consent_user_id ON sms_consent(user_id);
CREATE INDEX idx_sms_consent_phone_number ON sms_consent(phone_number);
CREATE INDEX idx_sms_consent_consent_granted ON sms_consent(consent_granted);
CREATE INDEX idx_sms_consent_opted_out ON sms_consent(opted_out);

-- Rename communication_delivery_logs to delivery_logs
ALTER TABLE communication_delivery_logs RENAME TO delivery_logs;

-- Rename opt_out_records to opt_out_history
ALTER TABLE opt_out_records RENAME TO opt_out_history;

-- Add new columns to opt_out_history
ALTER TABLE opt_out_history 
ADD COLUMN ip_address VARCHAR(45),
ADD COLUMN user_agent TEXT;

-- Update user_segment column in communication_policies
ALTER TABLE communication_policies 
ALTER COLUMN user_segment TYPE user_segment USING user_segment::user_segment;

-- Create function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for updated_at
CREATE TRIGGER update_sms_consent_updated_at 
    BEFORE UPDATE ON sms_consent 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Create function to set default preferences for new users
CREATE OR REPLACE FUNCTION create_default_communication_preferences()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO communication_preferences (
        id, user_id, sms_enabled, email_enabled, push_enabled, in_app_enabled,
        preferred_sms_time, preferred_email_day, alert_types_sms, alert_types_email,
        frequency_preference, financial_alerts_enabled, career_content_enabled,
        wellness_content_enabled, marketing_content_enabled, preferred_email_time,
        timezone, user_segment, auto_adjust_frequency, engagement_based_optimization
    ) VALUES (
        gen_random_uuid(), NEW.id, TRUE, TRUE, FALSE, TRUE,
        '09:00:00', 1, 
        '{"critical_financial": true, "bill_reminders": true, "budget_alerts": true, "emergency_fund": true, "daily_checkin": false, "weekly_report": false, "monthly_analysis": false, "career_insights": false, "wellness_tips": false, "spending_patterns": false, "subscription_updates": false, "marketing_content": false}',
        '{"critical_financial": true, "bill_reminders": true, "budget_alerts": true, "emergency_fund": true, "daily_checkin": true, "weekly_report": true, "monthly_analysis": true, "career_insights": true, "wellness_tips": true, "spending_patterns": true, "subscription_updates": true, "marketing_content": false}',
        'weekly', TRUE, TRUE, TRUE, FALSE, '18:00:00', 'UTC', 'new_user', TRUE, TRUE
    );
    
    -- Create engagement metrics
    INSERT INTO user_engagement_metrics (
        id, user_id, total_messages_sent, total_messages_opened, total_messages_clicked,
        total_messages_responded, sms_engagement_rate, email_engagement_rate, push_engagement_rate,
        alert_type_engagement, optimal_send_times, current_frequency, engagement_trend
    ) VALUES (
        gen_random_uuid(), NEW.id, 0, 0, 0, 0, 0, 0, 0, '{}', '{}', 'weekly', 'stable'
    );
    
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create trigger for new users
CREATE TRIGGER create_user_communication_preferences
    AFTER INSERT ON users
    FOR EACH ROW EXECUTE FUNCTION create_default_communication_preferences();

-- Create function to handle SMS STOP requests
CREATE OR REPLACE FUNCTION handle_sms_stop_request(phone_number_param VARCHAR(20))
RETURNS BOOLEAN AS $$
DECLARE
    user_record RECORD;
    sms_consent_record RECORD;
BEGIN
    -- Find user by phone number
    SELECT u.id INTO user_record
    FROM users u
    WHERE u.phone_number = phone_number_param;
    
    IF NOT FOUND THEN
        RETURN FALSE;
    END IF;
    
    -- Find SMS consent record
    SELECT * INTO sms_consent_record
    FROM sms_consent
    WHERE user_id = user_record.id;
    
    -- Update SMS consent
    IF FOUND THEN
        UPDATE sms_consent 
        SET opted_out = TRUE, 
            opted_out_at = NOW(),
            opt_out_reason = 'SMS STOP request',
            opt_out_method = 'sms_stop'
        WHERE user_id = user_record.id;
    END IF;
    
    -- Create opt-out history record
    INSERT INTO opt_out_history (
        id, user_id, channel, alert_type, reason, method, source, opted_out_at
    ) VALUES (
        gen_random_uuid(), user_record.id, 'sms', NULL, 'SMS STOP request', 'sms_stop', 'sms', NOW()
    );
    
    -- Update communication preferences
    UPDATE communication_preferences 
    SET sms_enabled = FALSE,
        updated_at = NOW()
    WHERE user_id = user_record.id;
    
    RETURN TRUE;
END;
$$ language 'plpgsql';

-- Create function to get optimal send time
CREATE OR REPLACE FUNCTION get_optimal_send_time(
    user_id_param INTEGER,
    channel_param communication_channel
)
RETURNS TIMESTAMP WITH TIME ZONE AS $$
DECLARE
    user_prefs RECORD;
    optimal_time TIMESTAMP WITH TIME ZONE;
    current_time TIMESTAMP WITH TIME ZONE;
BEGIN
    -- Get user preferences
    SELECT * INTO user_prefs
    FROM communication_preferences
    WHERE user_id = user_id_param;
    
    IF NOT FOUND THEN
        RETURN NULL;
    END IF;
    
    current_time = NOW();
    
    IF channel_param = 'sms' THEN
        -- Use preferred SMS time
        optimal_time = current_time::date + user_prefs.preferred_sms_time;
        
        -- If optimal time has passed today, schedule for tomorrow
        IF optimal_time <= current_time THEN
            optimal_time = optimal_time + INTERVAL '1 day';
        END IF;
        
    ELSIF channel_param = 'email' THEN
        -- Use preferred email day and time
        optimal_time = current_time::date + user_prefs.preferred_email_time;
        
        -- Calculate days until preferred day
        WHILE EXTRACT(DOW FROM optimal_time) != user_prefs.preferred_email_day LOOP
            optimal_time = optimal_time + INTERVAL '1 day';
        END LOOP;
        
        -- If optimal time has passed this week, schedule for next week
        IF optimal_time <= current_time THEN
            optimal_time = optimal_time + INTERVAL '7 days';
        END IF;
    END IF;
    
    RETURN optimal_time;
END;
$$ language 'plpgsql';

-- Create function to check consent for message type
CREATE OR REPLACE FUNCTION check_consent_for_message_type(
    user_id_param INTEGER,
    message_type_param VARCHAR(50),
    channel_param communication_channel
)
RETURNS BOOLEAN AS $$
DECLARE
    user_prefs RECORD;
    sms_consent_record RECORD;
    email_consent_record RECORD;
    opt_out_record RECORD;
BEGIN
    -- Get user preferences
    SELECT * INTO user_prefs
    FROM communication_preferences
    WHERE user_id = user_id_param;
    
    IF NOT FOUND THEN
        RETURN FALSE;
    END IF;
    
    -- Check channel-specific consent
    IF channel_param = 'sms' THEN
        IF NOT user_prefs.sms_enabled THEN
            RETURN FALSE;
        END IF;
        
        -- Check SMS consent
        SELECT * INTO sms_consent_record
        FROM sms_consent
        WHERE user_id = user_id_param 
          AND consent_granted = TRUE 
          AND opted_out = FALSE;
        
        IF NOT FOUND THEN
            RETURN FALSE;
        END IF;
        
        -- Check alert type preference
        IF user_prefs.alert_types_sms ? message_type_param THEN
            IF NOT user_prefs.alert_types_sms->message_type_param THEN
                RETURN FALSE;
            END IF;
        END IF;
        
    ELSIF channel_param = 'email' THEN
        IF NOT user_prefs.email_enabled THEN
            RETURN FALSE;
        END IF;
        
        -- Check email consent
        SELECT * INTO email_consent_record
        FROM consent_records
        WHERE user_id = user_id_param 
          AND consent_type = 'email' 
          AND consent_status = 'granted';
        
        IF NOT FOUND THEN
            RETURN FALSE;
        END IF;
        
        -- Check alert type preference
        IF user_prefs.alert_types_email ? message_type_param THEN
            IF NOT user_prefs.alert_types_email->message_type_param THEN
                RETURN FALSE;
            END IF;
        END IF;
    END IF;
    
    -- Check opt-out history
    SELECT * INTO opt_out_record
    FROM opt_out_history
    WHERE user_id = user_id_param 
      AND channel = channel_param
      AND (alert_type IS NULL OR alert_type::text = message_type_param)
      AND opted_out_at >= NOW() - INTERVAL '30 days';
    
    IF FOUND THEN
        RETURN FALSE;
    END IF;
    
    RETURN TRUE;
END;
$$ language 'plpgsql';

-- Create indexes for performance
CREATE INDEX idx_delivery_logs_user_id ON delivery_logs(user_id);
CREATE INDEX idx_delivery_logs_alert_type ON delivery_logs(alert_type);
CREATE INDEX idx_delivery_logs_channel ON delivery_logs(channel);
CREATE INDEX idx_delivery_logs_sent_at ON delivery_logs(sent_at);

CREATE INDEX idx_opt_out_history_user_id ON opt_out_history(user_id);
CREATE INDEX idx_opt_out_history_channel ON opt_out_history(channel);
CREATE INDEX idx_opt_out_history_opted_out_at ON opt_out_history(opted_out_at);

CREATE INDEX idx_communication_preferences_user_segment ON communication_preferences(user_segment);
CREATE INDEX idx_communication_preferences_sms_enabled ON communication_preferences(sms_enabled);
CREATE INDEX idx_communication_preferences_email_enabled ON communication_preferences(email_enabled);

-- Create view for communication preferences summary
CREATE VIEW communication_preferences_summary AS
SELECT 
    u.id as user_id,
    u.email,
    u.full_name,
    u.phone_number,
    cp.sms_enabled,
    cp.email_enabled,
    cp.user_segment,
    cp.frequency_preference,
    sc.consent_granted as sms_consent_granted,
    sc.phone_verified as sms_phone_verified,
    sc.opted_out as sms_opted_out,
    cr.consent_status as email_consent_status,
    uem.total_messages_sent,
    uem.sms_engagement_rate,
    uem.email_engagement_rate
FROM users u
LEFT JOIN communication_preferences cp ON u.id = cp.user_id
LEFT JOIN sms_consent sc ON u.id = sc.user_id
LEFT JOIN consent_records cr ON u.id = cr.user_id AND cr.consent_type = 'email'
LEFT JOIN user_engagement_metrics uem ON u.id = uem.user_id;

-- Create view for compliance reporting
CREATE VIEW compliance_report AS
SELECT 
    u.id as user_id,
    u.email,
    u.full_name,
    u.phone_number,
    cp.user_segment,
    sc.consent_granted as sms_consent_granted,
    sc.consent_granted_at as sms_consent_granted_at,
    sc.phone_verified as sms_phone_verified,
    sc.opted_out as sms_opted_out,
    sc.opted_out_at as sms_opted_out_at,
    cr.consent_status as email_consent_status,
    cr.granted_at as email_consent_granted_at,
    cr.revoked_at as email_consent_revoked_at,
    COUNT(dl.id) as total_deliveries,
    COUNT(CASE WHEN dl.status = 'delivered' THEN 1 END) as successful_deliveries,
    COUNT(CASE WHEN dl.status = 'failed' THEN 1 END) as failed_deliveries,
    MAX(dl.sent_at) as last_message_sent
FROM users u
LEFT JOIN communication_preferences cp ON u.id = cp.user_id
LEFT JOIN sms_consent sc ON u.id = sc.user_id
LEFT JOIN consent_records cr ON u.id = cr.user_id AND cr.consent_type = 'email'
LEFT JOIN delivery_logs dl ON u.id = dl.user_id
GROUP BY u.id, u.email, u.full_name, u.phone_number, cp.user_segment,
         sc.consent_granted, sc.consent_granted_at, sc.phone_verified, sc.opted_out, sc.opted_out_at,
         cr.consent_status, cr.granted_at, cr.revoked_at;

-- Insert default communication policies
INSERT INTO communication_policies (
    id, policy_name, policy_type, user_segment, default_channel, default_frequency,
    max_messages_per_day, max_messages_per_week, marketing_content_allowed,
    require_double_optin, consent_retention_days, auto_optout_inactive_days,
    quiet_hours_start, quiet_hours_end, timezone_aware, is_active, priority
) VALUES 
(gen_random_uuid(), 'New User Default', 'default', 'new_user', 'email', 'weekly', 3, 10, FALSE, TRUE, 2555, 365, '22:00', '08:00', TRUE, TRUE, 1),
(gen_random_uuid(), 'Premium Subscriber', 'tier_based', 'premium_subscriber', 'email', 'daily', 10, 50, TRUE, FALSE, 2555, 730, '23:00', '07:00', TRUE, TRUE, 2),
(gen_random_uuid(), 'At-Risk User', 'default', 'at_risk_user', 'sms', 'daily', 5, 20, FALSE, TRUE, 2555, 180, '21:00', '09:00', TRUE, TRUE, 3),
(gen_random_uuid(), 'High Engagement', 'default', 'high_engagement', 'email', 'daily', 8, 40, TRUE, FALSE, 2555, 1095, '22:00', '08:00', TRUE, TRUE, 4);

-- Update existing users with default preferences if they don't have any
INSERT INTO communication_preferences (
    id, user_id, sms_enabled, email_enabled, push_enabled, in_app_enabled,
    preferred_sms_time, preferred_email_day, alert_types_sms, alert_types_email,
    frequency_preference, financial_alerts_enabled, career_content_enabled,
    wellness_content_enabled, marketing_content_enabled, preferred_email_time,
    timezone, user_segment, auto_adjust_frequency, engagement_based_optimization
)
SELECT 
    gen_random_uuid(), u.id, TRUE, TRUE, FALSE, TRUE,
    '09:00:00', 1, 
    '{"critical_financial": true, "bill_reminders": true, "budget_alerts": true, "emergency_fund": true, "daily_checkin": false, "weekly_report": false, "monthly_analysis": false, "career_insights": false, "wellness_tips": false, "spending_patterns": false, "subscription_updates": false, "marketing_content": false}',
    '{"critical_financial": true, "bill_reminders": true, "budget_alerts": true, "emergency_fund": true, "daily_checkin": true, "weekly_report": true, "monthly_analysis": true, "career_insights": true, "wellness_tips": true, "spending_patterns": true, "subscription_updates": true, "marketing_content": false}',
    'weekly', TRUE, TRUE, TRUE, FALSE, '18:00:00', 'UTC', 'new_user', TRUE, TRUE
FROM users u
WHERE NOT EXISTS (
    SELECT 1 FROM communication_preferences cp WHERE cp.user_id = u.id
);

-- Create engagement metrics for existing users who don't have them
INSERT INTO user_engagement_metrics (
    id, user_id, total_messages_sent, total_messages_opened, total_messages_clicked,
    total_messages_responded, sms_engagement_rate, email_engagement_rate, push_engagement_rate,
    alert_type_engagement, optimal_send_times, current_frequency, engagement_trend
)
SELECT 
    gen_random_uuid(), u.id, 0, 0, 0, 0, 0, 0, 0, '{}', '{}', 'weekly', 'stable'
FROM users u
WHERE NOT EXISTS (
    SELECT 1 FROM user_engagement_metrics uem WHERE uem.user_id = u.id
); 