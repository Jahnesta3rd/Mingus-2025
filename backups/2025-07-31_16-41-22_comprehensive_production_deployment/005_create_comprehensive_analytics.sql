-- Migration: Create Comprehensive Analytics System
-- Description: Creates all analytics tables with proper relationships and indexes
-- Date: 2025-01-27

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create enum types for analytics
CREATE TYPE metric_type AS ENUM (
    'delivery_rate',
    'open_rate', 
    'click_rate',
    'response_rate',
    'engagement_rate',
    'cost_per_engagement',
    'conversion_rate',
    'retention_rate'
);

CREATE TYPE channel_type AS ENUM (
    'sms',
    'email',
    'push',
    'in_app'
);

CREATE TYPE user_segment AS ENUM (
    'new_user',
    'engaged',
    'at_risk',
    'premium',
    'enterprise',
    'inactive'
);

CREATE TYPE financial_outcome AS ENUM (
    'late_fee_avoided',
    'bill_paid_on_time',
    'savings_goal_achieved',
    'subscription_upgraded',
    'career_advancement',
    'budget_improved',
    'emergency_fund_built'
);

-- Create communication_metrics table (updated structure)
CREATE TABLE communication_metrics (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    message_type VARCHAR(50),     -- "low_balance", "weekly_checkin"
    channel VARCHAR(10),          -- "sms" or "email"
    status VARCHAR(20),           -- "sent", "delivered", "failed"
    cost FLOAT,                   -- Cost in dollars
    sent_at TIMESTAMP DEFAULT NOW(),
    delivered_at TIMESTAMP,
    opened_at TIMESTAMP,
    clicked_at TIMESTAMP,
    action_taken VARCHAR(100)     -- "viewed_forecast", "updated_budget"
);

-- Create user_engagement_metrics table
CREATE TABLE user_engagement_metrics (
    id VARCHAR(36) PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    total_messages_received INTEGER DEFAULT 0,
    total_messages_engaged INTEGER DEFAULT 0,
    total_messages_ignored INTEGER DEFAULT 0,
    sms_engagement_count INTEGER DEFAULT 0,
    email_engagement_count INTEGER DEFAULT 0,
    push_engagement_count INTEGER DEFAULT 0,
    in_app_engagement_count INTEGER DEFAULT 0,
    engagement_by_hour JSONB,
    engagement_by_day JSONB,
    engagement_by_month JSONB,
    alert_type_engagement JSONB,
    avg_response_time_minutes FLOAT DEFAULT 0.0,
    response_time_distribution JSONB,
    engagement_trend VARCHAR(20) DEFAULT 'stable',
    engagement_score FLOAT DEFAULT 0.0,
    optimal_frequency VARCHAR(20),
    current_frequency VARCHAR(20),
    frequency_effectiveness FLOAT DEFAULT 0.0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create channel_effectiveness table
CREATE TABLE channel_effectiveness (
    id VARCHAR(36) PRIMARY KEY DEFAULT uuid_generate_v4(),
    channel channel_type NOT NULL,
    alert_type VARCHAR(50),
    user_segment user_segment,
    date DATE NOT NULL,
    period_type VARCHAR(20) NOT NULL,
    messages_sent INTEGER DEFAULT 0,
    messages_delivered INTEGER DEFAULT 0,
    messages_opened INTEGER DEFAULT 0,
    messages_clicked INTEGER DEFAULT 0,
    messages_responded INTEGER DEFAULT 0,
    messages_converted INTEGER DEFAULT 0,
    delivery_rate FLOAT DEFAULT 0.0,
    open_rate FLOAT DEFAULT 0.0,
    click_rate FLOAT DEFAULT 0.0,
    response_rate FLOAT DEFAULT 0.0,
    conversion_rate FLOAT DEFAULT 0.0,
    engagement_rate FLOAT DEFAULT 0.0,
    total_cost NUMERIC(10, 4) DEFAULT 0.0,
    cost_per_message NUMERIC(10, 4) DEFAULT 0.0,
    cost_per_engagement NUMERIC(10, 4) DEFAULT 0.0,
    cost_per_conversion NUMERIC(10, 4) DEFAULT 0.0,
    revenue_generated NUMERIC(12, 2) DEFAULT 0.0,
    roi_percentage FLOAT DEFAULT 0.0,
    profit_margin FLOAT DEFAULT 0.0,
    avg_response_time_minutes FLOAT DEFAULT 0.0,
    opt_out_rate FLOAT DEFAULT 0.0,
    re_engagement_rate FLOAT DEFAULT 0.0,
    vs_other_channels JSONB,
    market_benchmark FLOAT DEFAULT 0.0,
    performance_score FLOAT DEFAULT 0.0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create financial_impact_metrics table
CREATE TABLE financial_impact_metrics (
    id VARCHAR(36) PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    outcome_type financial_outcome NOT NULL,
    outcome_value NUMERIC(12, 2),
    outcome_date TIMESTAMP NOT NULL,
    communication_channel channel_type,
    alert_type VARCHAR(50),
    message_id VARCHAR(100),
    days_since_last_communication INTEGER,
    communication_frequency_before_outcome VARCHAR(20),
    user_engaged_with_communication BOOLEAN DEFAULT FALSE,
    engagement_level VARCHAR(20),
    attributed_to_communication BOOLEAN DEFAULT FALSE,
    attribution_confidence FLOAT DEFAULT 0.0,
    attribution_reason TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create cost_tracking table
CREATE TABLE cost_tracking (
    id VARCHAR(36) PRIMARY KEY DEFAULT uuid_generate_v4(),
    channel channel_type NOT NULL,
    alert_type VARCHAR(50),
    user_segment user_segment,
    date DATE NOT NULL,
    period_type VARCHAR(20) NOT NULL,
    sms_cost NUMERIC(10, 4) DEFAULT 0.0,
    email_cost NUMERIC(10, 4) DEFAULT 0.0,
    push_cost NUMERIC(10, 4) DEFAULT 0.0,
    in_app_cost NUMERIC(10, 4) DEFAULT 0.0,
    twilio_cost NUMERIC(10, 4) DEFAULT 0.0,
    resend_cost NUMERIC(10, 4) DEFAULT 0.0,
    other_provider_cost NUMERIC(10, 4) DEFAULT 0.0,
    server_cost NUMERIC(10, 4) DEFAULT 0.0,
    storage_cost NUMERIC(10, 4) DEFAULT 0.0,
    bandwidth_cost NUMERIC(10, 4) DEFAULT 0.0,
    development_cost NUMERIC(10, 4) DEFAULT 0.0,
    maintenance_cost NUMERIC(10, 4) DEFAULT 0.0,
    support_cost NUMERIC(10, 4) DEFAULT 0.0,
    total_cost NUMERIC(12, 4) DEFAULT 0.0,
    total_messages INTEGER DEFAULT 0,
    cost_per_message NUMERIC(10, 4) DEFAULT 0.0,
    budget_allocation NUMERIC(12, 4) DEFAULT 0.0,
    budget_utilization FLOAT DEFAULT 0.0,
    budget_variance NUMERIC(12, 4) DEFAULT 0.0,
    cost_per_engagement NUMERIC(10, 4) DEFAULT 0.0,
    cost_per_conversion NUMERIC(10, 4) DEFAULT 0.0,
    cost_efficiency_score FLOAT DEFAULT 0.0,
    cost_trend VARCHAR(20) DEFAULT 'stable',
    cost_forecast NUMERIC(12, 4) DEFAULT 0.0,
    cost_threshold_exceeded BOOLEAN DEFAULT FALSE,
    budget_alert_triggered BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create ab_test_results table
CREATE TABLE ab_test_results (
    id VARCHAR(36) PRIMARY KEY DEFAULT uuid_generate_v4(),
    test_name VARCHAR(100) NOT NULL,
    test_variant VARCHAR(50) NOT NULL,
    test_type VARCHAR(50) NOT NULL,
    target_audience JSONB,
    test_duration_days INTEGER NOT NULL,
    start_date TIMESTAMP NOT NULL,
    end_date TIMESTAMP NOT NULL,
    total_users INTEGER DEFAULT 0,
    total_messages_sent INTEGER DEFAULT 0,
    total_engagements INTEGER DEFAULT 0,
    delivery_rate FLOAT DEFAULT 0.0,
    open_rate FLOAT DEFAULT 0.0,
    click_rate FLOAT DEFAULT 0.0,
    response_rate FLOAT DEFAULT 0.0,
    conversion_rate FLOAT DEFAULT 0.0,
    engagement_rate FLOAT DEFAULT 0.0,
    total_revenue_impact NUMERIC(12, 2) DEFAULT 0.0,
    cost_per_conversion NUMERIC(10, 4) DEFAULT 0.0,
    roi FLOAT DEFAULT 0.0,
    confidence_level FLOAT DEFAULT 0.0,
    p_value FLOAT DEFAULT 0.0,
    is_statistically_significant BOOLEAN DEFAULT FALSE,
    is_winner BOOLEAN DEFAULT FALSE,
    test_status VARCHAR(20) DEFAULT 'running',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create communication_queue_status table
CREATE TABLE communication_queue_status (
    id VARCHAR(36) PRIMARY KEY DEFAULT uuid_generate_v4(),
    queue_name VARCHAR(50) NOT NULL,
    channel channel_type NOT NULL,
    queue_depth INTEGER DEFAULT 0,
    messages_processed INTEGER DEFAULT 0,
    messages_failed INTEGER DEFAULT 0,
    messages_pending INTEGER DEFAULT 0,
    avg_processing_time_seconds FLOAT DEFAULT 0.0,
    max_processing_time_seconds FLOAT DEFAULT 0.0,
    throughput_messages_per_minute FLOAT DEFAULT 0.0,
    error_rate FLOAT DEFAULT 0.0,
    last_error_message TEXT,
    last_error_time TIMESTAMP,
    is_healthy BOOLEAN DEFAULT TRUE,
    health_score FLOAT DEFAULT 100.0,
    last_health_check TIMESTAMP,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create analytics_alerts table
CREATE TABLE analytics_alerts (
    id VARCHAR(36) PRIMARY KEY DEFAULT uuid_generate_v4(),
    alert_type VARCHAR(50) NOT NULL,
    alert_severity VARCHAR(20) NOT NULL,
    alert_status VARCHAR(20) DEFAULT 'active',
    metric_name VARCHAR(50) NOT NULL,
    threshold_value FLOAT NOT NULL,
    current_value FLOAT NOT NULL,
    comparison_operator VARCHAR(10) NOT NULL,
    channel channel_type,
    alert_type_filter VARCHAR(50),
    user_segment user_segment,
    time_period VARCHAR(20),
    alert_message TEXT NOT NULL,
    alert_description TEXT,
    recommended_action TEXT,
    notified_users JSONB,
    notification_sent_at TIMESTAMP,
    resolved_by VARCHAR(36),
    resolved_at TIMESTAMP,
    resolution_notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create analytics_reports table
CREATE TABLE analytics_reports (
    id VARCHAR(36) PRIMARY KEY DEFAULT uuid_generate_v4(),
    report_type VARCHAR(50) NOT NULL,
    report_period VARCHAR(20) NOT NULL,
    report_date TIMESTAMP NOT NULL,
    channels_included JSONB,
    user_segments_included JSONB,
    alert_types_included JSONB,
    total_messages_sent INTEGER DEFAULT 0,
    total_engagements INTEGER DEFAULT 0,
    total_conversions INTEGER DEFAULT 0,
    total_revenue_impact NUMERIC(12, 2) DEFAULT 0.0,
    total_cost NUMERIC(10, 4) DEFAULT 0.0,
    avg_delivery_rate FLOAT DEFAULT 0.0,
    avg_engagement_rate FLOAT DEFAULT 0.0,
    avg_conversion_rate FLOAT DEFAULT 0.0,
    avg_cost_per_engagement NUMERIC(10, 4) DEFAULT 0.0,
    overall_roi FLOAT DEFAULT 0.0,
    top_performing_channel VARCHAR(20),
    top_performing_alert_type VARCHAR(50),
    most_engaged_segment VARCHAR(20),
    key_insights JSONB,
    report_data JSONB,
    report_url VARCHAR(500),
    recipients JSONB,
    sent_at TIMESTAMP,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by VARCHAR(36)
);

-- Create user_segment_performance table
CREATE TABLE user_segment_performance (
    id VARCHAR(36) PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_segment user_segment NOT NULL,
    date DATE NOT NULL,
    total_users INTEGER DEFAULT 0,
    active_users INTEGER DEFAULT 0,
    new_users INTEGER DEFAULT 0,
    churned_users INTEGER DEFAULT 0,
    messages_sent INTEGER DEFAULT 0,
    messages_delivered INTEGER DEFAULT 0,
    messages_engaged INTEGER DEFAULT 0,
    delivery_rate FLOAT DEFAULT 0.0,
    engagement_rate FLOAT DEFAULT 0.0,
    retention_rate FLOAT DEFAULT 0.0,
    avg_revenue_per_user NUMERIC(10, 2) DEFAULT 0.0,
    total_revenue NUMERIC(12, 2) DEFAULT 0.0,
    conversion_rate FLOAT DEFAULT 0.0,
    channel_performance JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX idx_comm_metrics_user_id ON communication_metrics(user_id);
CREATE INDEX idx_comm_metrics_message_type ON communication_metrics(message_type);
CREATE INDEX idx_comm_metrics_channel ON communication_metrics(channel);
CREATE INDEX idx_comm_metrics_status ON communication_metrics(status);
CREATE INDEX idx_comm_metrics_sent_at ON communication_metrics(sent_at);

CREATE INDEX idx_user_engagement_user_id ON user_engagement_metrics(user_id);
CREATE INDEX idx_user_engagement_score ON user_engagement_metrics(engagement_score);
CREATE INDEX idx_user_engagement_trend ON user_engagement_metrics(engagement_trend);

CREATE INDEX idx_channel_effectiveness_date_channel ON channel_effectiveness(date, channel);
CREATE INDEX idx_channel_effectiveness_alert_type ON channel_effectiveness(alert_type);
CREATE INDEX idx_channel_effectiveness_user_segment ON channel_effectiveness(user_segment);
CREATE INDEX idx_channel_effectiveness_performance ON channel_effectiveness(performance_score);

CREATE INDEX idx_financial_impact_user_id ON financial_impact_metrics(user_id);
CREATE INDEX idx_financial_impact_outcome_type ON financial_impact_metrics(outcome_type);
CREATE INDEX idx_financial_impact_outcome_date ON financial_impact_metrics(outcome_date);
CREATE INDEX idx_financial_impact_attribution ON financial_impact_metrics(attributed_to_communication);

CREATE INDEX idx_cost_tracking_date_channel ON cost_tracking(date, channel);
CREATE INDEX idx_cost_tracking_total_cost ON cost_tracking(total_cost);
CREATE INDEX idx_cost_tracking_budget_utilization ON cost_tracking(budget_utilization);
CREATE INDEX idx_cost_tracking_cost_efficiency ON cost_tracking(cost_efficiency_score);

CREATE INDEX idx_ab_test_results_test_name ON ab_test_results(test_name);
CREATE INDEX idx_ab_test_results_test_status ON ab_test_results(test_status);
CREATE INDEX idx_ab_test_results_is_winner ON ab_test_results(is_winner);

CREATE INDEX idx_queue_status_queue_name ON communication_queue_status(queue_name);
CREATE INDEX idx_queue_status_channel ON communication_queue_status(channel);
CREATE INDEX idx_queue_status_health ON communication_queue_status(is_healthy);

CREATE INDEX idx_analytics_alerts_alert_type ON analytics_alerts(alert_type);
CREATE INDEX idx_analytics_alerts_severity ON analytics_alerts(alert_severity);
CREATE INDEX idx_analytics_alerts_status ON analytics_alerts(alert_status);
CREATE INDEX idx_analytics_alerts_created_at ON analytics_alerts(created_at);

CREATE INDEX idx_analytics_reports_report_type ON analytics_reports(report_type);
CREATE INDEX idx_analytics_reports_report_date ON analytics_reports(report_date);
CREATE INDEX idx_analytics_reports_period ON analytics_reports(report_period);

CREATE INDEX idx_user_segment_performance_segment_date ON user_segment_performance(user_segment, date);
CREATE INDEX idx_user_segment_performance_engagement_rate ON user_segment_performance(engagement_rate);
CREATE INDEX idx_user_segment_performance_retention_rate ON user_segment_performance(retention_rate);

-- Create triggers for updated_at timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_user_engagement_metrics_updated_at 
    BEFORE UPDATE ON user_engagement_metrics 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_channel_effectiveness_updated_at 
    BEFORE UPDATE ON channel_effectiveness 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_cost_tracking_updated_at 
    BEFORE UPDATE ON cost_tracking 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_ab_test_results_updated_at 
    BEFORE UPDATE ON ab_test_results 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_communication_queue_status_updated_at 
    BEFORE UPDATE ON communication_queue_status 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_analytics_alerts_updated_at 
    BEFORE UPDATE ON analytics_alerts 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_analytics_reports_updated_at 
    BEFORE UPDATE ON analytics_reports 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_user_segment_performance_updated_at 
    BEFORE UPDATE ON user_segment_performance 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insert initial data for testing
INSERT INTO communication_queue_status (id, queue_name, channel, is_healthy, health_score) VALUES
(uuid_generate_v4(), 'sms_critical', 'sms', true, 100.0),
(uuid_generate_v4(), 'sms_daily', 'sms', true, 100.0),
(uuid_generate_v4(), 'email_reports', 'email', true, 100.0),
(uuid_generate_v4(), 'email_education', 'email', true, 100.0);

-- Create view for analytics dashboard
CREATE VIEW analytics_dashboard_view AS
SELECT 
    'communication_metrics' as table_name,
    COUNT(*) as record_count,
    MAX(sent_at) as last_updated
FROM communication_metrics
UNION ALL
SELECT 
    'user_engagement_metrics' as table_name,
    COUNT(*) as record_count,
    MAX(created_at) as last_updated
FROM user_engagement_metrics
UNION ALL
SELECT 
    'channel_effectiveness' as table_name,
    COUNT(*) as record_count,
    MAX(created_at) as last_updated
FROM channel_effectiveness
UNION ALL
SELECT 
    'financial_impact_metrics' as table_name,
    COUNT(*) as record_count,
    MAX(created_at) as last_updated
FROM financial_impact_metrics
UNION ALL
SELECT 
    'cost_tracking' as table_name,
    COUNT(*) as record_count,
    MAX(created_at) as last_updated
FROM cost_tracking;

-- Grant permissions (adjust as needed for your setup)
-- GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO your_app_user;
-- GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO your_app_user;

COMMIT; 