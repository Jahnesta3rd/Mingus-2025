-- Migration: Create Communication Preferences and Consent Management Tables
-- Date: 2025-01-27
-- Description: Adds comprehensive communication preference and consent management system

-- Create enum types
CREATE TYPE communication_channel AS ENUM ('sms', 'email', 'push', 'in_app');
CREATE TYPE alert_type AS ENUM (
    'critical_financial', 'daily_checkin', 'weekly_report', 'monthly_analysis',
    'career_insights', 'wellness_tips', 'bill_reminders', 'budget_alerts',
    'spending_patterns', 'emergency_fund', 'subscription_updates', 'marketing_content'
);
CREATE TYPE frequency_type AS ENUM ('immediate', 'daily', 'weekly', 'monthly', 'quarterly', 'never');
CREATE TYPE consent_status AS ENUM ('pending', 'granted', 'denied', 'revoked', 'expired');

-- Create communication_preferences table
CREATE TABLE communication_preferences (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Channel preferences
    sms_enabled BOOLEAN DEFAULT TRUE,
    email_enabled BOOLEAN DEFAULT TRUE,
    push_enabled BOOLEAN DEFAULT FALSE,
    in_app_enabled BOOLEAN DEFAULT TRUE,
    
    -- Frequency preferences
    critical_frequency frequency_type DEFAULT 'immediate',
    daily_frequency frequency_type DEFAULT 'daily',
    weekly_frequency frequency_type DEFAULT 'weekly',
    monthly_frequency frequency_type DEFAULT 'monthly',
    
    -- Content type preferences
    financial_alerts_enabled BOOLEAN DEFAULT TRUE,
    career_content_enabled BOOLEAN DEFAULT TRUE,
    wellness_content_enabled BOOLEAN DEFAULT TRUE,
    marketing_content_enabled BOOLEAN DEFAULT FALSE,
    
    -- Delivery timing preferences
    preferred_sms_time VARCHAR(5) DEFAULT '09:00',
    preferred_email_time VARCHAR(5) DEFAULT '18:00',
    timezone VARCHAR(50) DEFAULT 'UTC',
    
    -- Smart defaults
    auto_adjust_frequency BOOLEAN DEFAULT TRUE,
    engagement_based_optimization BOOLEAN DEFAULT TRUE,
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(user_id)
);

-- Create consent_records table
CREATE TABLE consent_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    preferences_id UUID NOT NULL REFERENCES communication_preferences(id) ON DELETE CASCADE,
    
    -- Consent details
    consent_type VARCHAR(50) NOT NULL, -- 'sms', 'email', 'marketing'
    consent_status consent_status DEFAULT 'pending',
    
    -- TCPA compliance fields
    phone_number VARCHAR(20),
    ip_address VARCHAR(45),
    user_agent TEXT,
    consent_source VARCHAR(100) NOT NULL, -- 'web_form', 'mobile_app', 'api'
    
    -- GDPR compliance fields
    legal_basis VARCHAR(50), -- 'consent', 'legitimate_interest', 'contract'
    purpose TEXT,
    data_retention_period INTEGER, -- days
    
    -- Consent lifecycle
    granted_at TIMESTAMP WITH TIME ZONE,
    revoked_at TIMESTAMP WITH TIME ZONE,
    expires_at TIMESTAMP WITH TIME ZONE,
    
    -- Verification
    verified_at TIMESTAMP WITH TIME ZONE,
    verification_method VARCHAR(50), -- 'sms_code', 'email_link', 'manual'
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create alert_type_preferences table
CREATE TABLE alert_type_preferences (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    preferences_id UUID NOT NULL REFERENCES communication_preferences(id) ON DELETE CASCADE,
    
    -- Alert type and channel preferences
    alert_type alert_type NOT NULL,
    sms_enabled BOOLEAN DEFAULT TRUE,
    email_enabled BOOLEAN DEFAULT TRUE,
    push_enabled BOOLEAN DEFAULT FALSE,
    in_app_enabled BOOLEAN DEFAULT TRUE,
    
    -- Frequency for this specific alert type
    frequency frequency_type NOT NULL,
    
    -- Priority and timing
    priority INTEGER DEFAULT 5, -- 1-10 scale
    preferred_time VARCHAR(5), -- HH:MM format
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(user_id, alert_type)
);

-- Create communication_delivery_logs table
CREATE TABLE communication_delivery_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    preferences_id UUID NOT NULL REFERENCES communication_preferences(id) ON DELETE CASCADE,
    
    -- Delivery details
    alert_type alert_type NOT NULL,
    channel communication_channel NOT NULL,
    message_id VARCHAR(100), -- External service message ID
    
    -- Content and timing
    subject TEXT,
    content_preview TEXT,
    scheduled_at TIMESTAMP WITH TIME ZONE,
    sent_at TIMESTAMP WITH TIME ZONE,
    delivered_at TIMESTAMP WITH TIME ZONE,
    
    -- Delivery status
    status VARCHAR(50) DEFAULT 'pending', -- pending, sent, delivered, failed, bounced
    error_message TEXT,
    
    -- User engagement
    opened_at TIMESTAMP WITH TIME ZONE,
    clicked_at TIMESTAMP WITH TIME ZONE,
    responded_at TIMESTAMP WITH TIME ZONE,
    
    -- Compliance tracking
    consent_verified BOOLEAN DEFAULT FALSE,
    compliance_checks_passed BOOLEAN DEFAULT TRUE,
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create opt_out_records table
CREATE TABLE opt_out_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Opt-out details
    channel communication_channel NOT NULL,
    alert_type alert_type, -- null means all types
    reason VARCHAR(200),
    
    -- Opt-out method
    method VARCHAR(50) NOT NULL, -- 'sms_stop', 'email_unsubscribe', 'web_form', 'api'
    source VARCHAR(100), -- 'sms', 'email', 'web', 'mobile_app'
    
    -- Timing
    opted_out_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE, -- for temporary opt-outs
    
    -- Re-engagement
    re_engaged_at TIMESTAMP WITH TIME ZONE,
    re_engagement_method VARCHAR(50),
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create user_engagement_metrics table
CREATE TABLE user_engagement_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Engagement metrics
    total_messages_sent INTEGER DEFAULT 0,
    total_messages_opened INTEGER DEFAULT 0,
    total_messages_clicked INTEGER DEFAULT 0,
    total_messages_responded INTEGER DEFAULT 0,
    
    -- Channel-specific metrics
    sms_engagement_rate INTEGER DEFAULT 0, -- percentage
    email_engagement_rate INTEGER DEFAULT 0, -- percentage
    push_engagement_rate INTEGER DEFAULT 0, -- percentage
    
    -- Alert type engagement
    alert_type_engagement JSONB, -- {alert_type: engagement_rate}
    
    -- Timing preferences
    optimal_send_times JSONB, -- {day_of_week: {hour: engagement_rate}}
    
    -- Frequency optimization
    current_frequency VARCHAR(50) DEFAULT 'weekly',
    recommended_frequency VARCHAR(50),
    frequency_adjustment_reason TEXT,
    
    -- Last engagement
    last_engagement_at TIMESTAMP WITH TIME ZONE,
    engagement_trend VARCHAR(20) DEFAULT 'stable', -- increasing, decreasing, stable
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(user_id)
);

-- Create communication_policies table
CREATE TABLE communication_policies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Policy details
    policy_name VARCHAR(100) NOT NULL,
    policy_type VARCHAR(50) NOT NULL, -- 'default', 'tier_based', 'region_based'
    
    -- Target criteria
    user_tier VARCHAR(50), -- 'free', 'premium', 'enterprise'
    region VARCHAR(50),
    user_segment VARCHAR(50), -- 'new_user', 'engaged', 'at_risk'
    
    -- Policy rules
    default_channel communication_channel DEFAULT 'email',
    default_frequency frequency_type DEFAULT 'weekly',
    max_messages_per_day INTEGER DEFAULT 5,
    max_messages_per_week INTEGER DEFAULT 20,
    
    -- Content restrictions
    allowed_alert_types JSONB, -- list of allowed alert types
    marketing_content_allowed BOOLEAN DEFAULT FALSE,
    
    -- Compliance settings
    require_double_optin BOOLEAN DEFAULT TRUE,
    consent_retention_days INTEGER DEFAULT 2555, -- 7 years
    auto_optout_inactive_days INTEGER DEFAULT 365, -- 1 year
    
    -- Timing restrictions
    quiet_hours_start VARCHAR(5) DEFAULT '22:00', -- HH:MM format
    quiet_hours_end VARCHAR(5) DEFAULT '08:00', -- HH:MM format
    timezone_aware BOOLEAN DEFAULT TRUE,
    
    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    priority INTEGER DEFAULT 5, -- 1-10 scale for policy precedence
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by VARCHAR(36),
    updated_by VARCHAR(36)
);

-- Create indexes for performance
CREATE INDEX idx_communication_preferences_user_id ON communication_preferences(user_id);
CREATE INDEX idx_consent_records_user_id ON consent_records(user_id);
CREATE INDEX idx_consent_records_preferences_id ON consent_records(preferences_id);
CREATE INDEX idx_consent_records_status ON consent_records(consent_status);
CREATE INDEX idx_alert_type_preferences_user_id ON alert_type_preferences(user_id);
CREATE INDEX idx_alert_type_preferences_alert_type ON alert_type_preferences(alert_type);
CREATE INDEX idx_communication_delivery_logs_user_id ON communication_delivery_logs(user_id);
CREATE INDEX idx_communication_delivery_logs_status ON communication_delivery_logs(status);
CREATE INDEX idx_communication_delivery_logs_sent_at ON communication_delivery_logs(sent_at);
CREATE INDEX idx_opt_out_records_user_id ON opt_out_records(user_id);
CREATE INDEX idx_opt_out_records_channel ON opt_out_records(channel);
CREATE INDEX idx_user_engagement_metrics_user_id ON user_engagement_metrics(user_id);
CREATE INDEX idx_communication_policies_active ON communication_policies(is_active);
CREATE INDEX idx_communication_policies_priority ON communication_policies(priority);

-- Insert default communication policies
INSERT INTO communication_policies (
    policy_name, policy_type, user_tier, default_channel, default_frequency,
    max_messages_per_day, max_messages_per_week, marketing_content_allowed,
    require_double_optin, priority
) VALUES 
    ('Default Free User Policy', 'default', 'free', 'email', 'weekly', 3, 10, FALSE, TRUE, 5),
    ('Premium User Policy', 'tier_based', 'premium', 'email', 'daily', 5, 20, TRUE, TRUE, 3),
    ('Enterprise User Policy', 'tier_based', 'enterprise', 'email', 'immediate', 10, 50, TRUE, FALSE, 1),
    ('New User Policy', 'default', NULL, 'sms', 'daily', 2, 7, FALSE, TRUE, 4),
    ('At-Risk User Policy', 'default', NULL, 'sms', 'immediate', 3, 15, FALSE, TRUE, 2);

-- Create triggers for updated_at timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_communication_preferences_updated_at 
    BEFORE UPDATE ON communication_preferences 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_consent_records_updated_at 
    BEFORE UPDATE ON consent_records 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_alert_type_preferences_updated_at 
    BEFORE UPDATE ON alert_type_preferences 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_user_engagement_metrics_updated_at 
    BEFORE UPDATE ON user_engagement_metrics 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_communication_policies_updated_at 
    BEFORE UPDATE ON communication_policies 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column(); 