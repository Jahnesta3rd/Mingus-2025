-- Migration: Create Communication Analytics Tables
-- Date: 2025-01-27
-- Description: Adds comprehensive communication analytics system for tracking effectiveness

-- Create enum types for analytics
CREATE TYPE metric_type AS ENUM (
    'delivery_rate', 'open_rate', 'click_rate', 'response_rate', 
    'engagement_rate', 'cost_per_engagement', 'conversion_rate', 'retention_rate'
);

CREATE TYPE channel_type AS ENUM ('sms', 'email', 'push', 'in_app');

CREATE TYPE user_segment AS ENUM (
    'new_user', 'engaged', 'at_risk', 'premium', 'enterprise', 'inactive'
);

CREATE TYPE financial_outcome AS ENUM (
    'late_fee_avoided', 'bill_paid_on_time', 'savings_goal_achieved',
    'subscription_upgraded', 'career_advancement', 'budget_improved', 'emergency_fund_built'
);

-- Create communication_metrics table
CREATE TABLE communication_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Metric identification
    metric_type metric_type NOT NULL,
    channel channel_type NOT NULL,
    alert_type VARCHAR(50),
    user_segment user_segment,
    
    -- Time dimensions
    date TIMESTAMP WITH TIME ZONE NOT NULL,
    hour INTEGER, -- 0-23
    day_of_week INTEGER, -- 0-6 (Monday=0)
    week_of_year INTEGER,
    month INTEGER,
    quarter INTEGER,
    year INTEGER NOT NULL,
    
    -- Metric values
    total_sent INTEGER DEFAULT 0,
    total_delivered INTEGER DEFAULT 0,
    total_opened INTEGER DEFAULT 0,
    total_clicked INTEGER DEFAULT 0,
    total_responded INTEGER DEFAULT 0,
    total_converted INTEGER DEFAULT 0,
    
    -- Calculated rates
    delivery_rate FLOAT DEFAULT 0.0, -- percentage
    open_rate FLOAT DEFAULT 0.0, -- percentage
    click_rate FLOAT DEFAULT 0.0, -- percentage
    response_rate FLOAT DEFAULT 0.0, -- percentage
    conversion_rate FLOAT DEFAULT 0.0, -- percentage
    engagement_rate FLOAT DEFAULT 0.0, -- percentage
    
    -- Cost metrics
    total_cost NUMERIC(10, 4) DEFAULT 0.0,
    cost_per_message NUMERIC(10, 4) DEFAULT 0.0,
    cost_per_engagement NUMERIC(10, 4) DEFAULT 0.0,
    cost_per_conversion NUMERIC(10, 4) DEFAULT 0.0,
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create user_engagement_analytics table
CREATE TABLE user_engagement_analytics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Engagement metrics
    total_messages_received INTEGER DEFAULT 0,
    total_messages_engaged INTEGER DEFAULT 0,
    total_messages_ignored INTEGER DEFAULT 0,
    
    -- Channel-specific engagement
    sms_engagement_count INTEGER DEFAULT 0,
    email_engagement_count INTEGER DEFAULT 0,
    push_engagement_count INTEGER DEFAULT 0,
    in_app_engagement_count INTEGER DEFAULT 0,
    
    -- Time-based engagement patterns
    engagement_by_hour JSONB, -- {hour: engagement_count}
    engagement_by_day JSONB, -- {day: engagement_count}
    engagement_by_month JSONB, -- {month: engagement_count}
    
    -- Message type effectiveness
    alert_type_engagement JSONB, -- {alert_type: {engaged, total, rate}}
    
    -- Response time analysis
    avg_response_time_minutes FLOAT DEFAULT 0.0,
    response_time_distribution JSONB, -- {time_range: count}
    
    -- Engagement trends
    engagement_trend VARCHAR(20) DEFAULT 'stable', -- increasing, decreasing, stable
    engagement_score FLOAT DEFAULT 0.0, -- 0-100 scale
    
    -- Frequency analysis
    optimal_frequency VARCHAR(20), -- daily, weekly, monthly
    current_frequency VARCHAR(20),
    frequency_effectiveness FLOAT DEFAULT 0.0, -- 0-100 scale
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create financial_impact_metrics table
CREATE TABLE financial_impact_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Financial outcomes
    outcome_type financial_outcome NOT NULL,
    outcome_value NUMERIC(12, 2), -- Dollar amount
    outcome_date TIMESTAMP WITH TIME ZONE NOT NULL,
    
    -- Communication correlation
    communication_channel channel_type,
    alert_type VARCHAR(50),
    message_id VARCHAR(100),
    
    -- Time correlation
    days_since_last_communication INTEGER,
    communication_frequency_before_outcome VARCHAR(20),
    
    -- Engagement correlation
    user_engaged_with_communication BOOLEAN DEFAULT FALSE,
    engagement_level VARCHAR(20), -- low, medium, high
    
    -- Attribution
    attributed_to_communication BOOLEAN DEFAULT FALSE,
    attribution_confidence FLOAT DEFAULT 0.0, -- 0-100 scale
    attribution_reason TEXT,
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create ab_test_results table
CREATE TABLE ab_test_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Test identification
    test_name VARCHAR(100) NOT NULL,
    test_variant VARCHAR(50) NOT NULL, -- A, B, C, etc.
    test_type VARCHAR(50) NOT NULL, -- content, timing, frequency, channel
    
    -- Test parameters
    target_audience JSONB, -- {segment, criteria}
    test_duration_days INTEGER NOT NULL,
    start_date TIMESTAMP WITH TIME ZONE NOT NULL,
    end_date TIMESTAMP WITH TIME ZONE NOT NULL,
    
    -- Sample sizes
    total_users INTEGER DEFAULT 0,
    total_messages_sent INTEGER DEFAULT 0,
    total_engagements INTEGER DEFAULT 0,
    
    -- Performance metrics
    delivery_rate FLOAT DEFAULT 0.0,
    open_rate FLOAT DEFAULT 0.0,
    click_rate FLOAT DEFAULT 0.0,
    response_rate FLOAT DEFAULT 0.0,
    conversion_rate FLOAT DEFAULT 0.0,
    engagement_rate FLOAT DEFAULT 0.0,
    
    -- Financial impact
    total_revenue_impact NUMERIC(12, 2) DEFAULT 0.0,
    cost_per_conversion NUMERIC(10, 4) DEFAULT 0.0,
    roi FLOAT DEFAULT 0.0, -- Return on investment percentage
    
    -- Statistical significance
    confidence_level FLOAT DEFAULT 0.0, -- 0-100 scale
    p_value FLOAT DEFAULT 0.0,
    is_statistically_significant BOOLEAN DEFAULT FALSE,
    
    -- Test status
    is_winner BOOLEAN DEFAULT FALSE,
    test_status VARCHAR(20) DEFAULT 'running', -- running, completed, paused
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create communication_queue_status table
CREATE TABLE communication_queue_status (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Queue identification
    queue_name VARCHAR(50) NOT NULL, -- sms_critical, email_reports, etc.
    channel channel_type NOT NULL,
    
    -- Queue metrics
    queue_depth INTEGER DEFAULT 0,
    messages_processed INTEGER DEFAULT 0,
    messages_failed INTEGER DEFAULT 0,
    messages_pending INTEGER DEFAULT 0,
    
    -- Performance metrics
    avg_processing_time_seconds FLOAT DEFAULT 0.0,
    max_processing_time_seconds FLOAT DEFAULT 0.0,
    throughput_messages_per_minute FLOAT DEFAULT 0.0,
    
    -- Error tracking
    error_rate FLOAT DEFAULT 0.0, -- percentage
    last_error_message TEXT,
    last_error_time TIMESTAMP WITH TIME ZONE,
    
    -- Health status
    is_healthy BOOLEAN DEFAULT TRUE,
    health_score FLOAT DEFAULT 100.0, -- 0-100 scale
    last_health_check TIMESTAMP WITH TIME ZONE,
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create analytics_alerts table
CREATE TABLE analytics_alerts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Alert identification
    alert_type VARCHAR(50) NOT NULL, -- low_delivery_rate, high_opt_out, cost_threshold
    alert_severity VARCHAR(20) NOT NULL, -- low, medium, high, critical
    alert_status VARCHAR(20) DEFAULT 'active', -- active, acknowledged, resolved
    
    -- Alert conditions
    metric_name VARCHAR(50) NOT NULL,
    threshold_value FLOAT NOT NULL,
    current_value FLOAT NOT NULL,
    comparison_operator VARCHAR(10) NOT NULL, -- <, >, <=, >=, ==
    
    -- Context
    channel channel_type,
    alert_type_filter VARCHAR(50),
    user_segment user_segment,
    time_period VARCHAR(20), -- last_hour, last_day, last_week
    
    -- Alert details
    alert_message TEXT NOT NULL,
    alert_description TEXT,
    recommended_action TEXT,
    
    -- Notification
    notified_users JSONB, -- List of user IDs notified
    notification_sent_at TIMESTAMP WITH TIME ZONE,
    
    -- Resolution
    resolved_by VARCHAR(36),
    resolved_at TIMESTAMP WITH TIME ZONE,
    resolution_notes TEXT,
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create analytics_reports table
CREATE TABLE analytics_reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Report identification
    report_type VARCHAR(50) NOT NULL, -- weekly_performance, monthly_engagement, quarterly_impact
    report_period VARCHAR(20) NOT NULL, -- weekly, monthly, quarterly, yearly
    report_date TIMESTAMP WITH TIME ZONE NOT NULL,
    
    -- Report scope
    channels_included JSONB, -- List of channels
    user_segments_included JSONB, -- List of segments
    alert_types_included JSONB, -- List of alert types
    
    -- Report metrics
    total_messages_sent INTEGER DEFAULT 0,
    total_engagements INTEGER DEFAULT 0,
    total_conversions INTEGER DEFAULT 0,
    total_revenue_impact NUMERIC(12, 2) DEFAULT 0.0,
    total_cost NUMERIC(10, 4) DEFAULT 0.0,
    
    -- Performance summary
    avg_delivery_rate FLOAT DEFAULT 0.0,
    avg_engagement_rate FLOAT DEFAULT 0.0,
    avg_conversion_rate FLOAT DEFAULT 0.0,
    avg_cost_per_engagement NUMERIC(10, 4) DEFAULT 0.0,
    overall_roi FLOAT DEFAULT 0.0,
    
    -- Key insights
    top_performing_channel VARCHAR(20),
    top_performing_alert_type VARCHAR(50),
    most_engaged_segment VARCHAR(20),
    key_insights JSONB, -- List of insights
    
    -- Report content
    report_data JSONB, -- Full report data
    report_url VARCHAR(500), -- Link to generated report
    
    -- Distribution
    recipients JSONB, -- List of recipient emails
    sent_at TIMESTAMP WITH TIME ZONE,
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by VARCHAR(36)
);

-- Create user_segment_performance table
CREATE TABLE user_segment_performance (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Segment identification
    user_segment user_segment NOT NULL,
    date TIMESTAMP WITH TIME ZONE NOT NULL,
    
    -- Segment metrics
    total_users INTEGER DEFAULT 0,
    active_users INTEGER DEFAULT 0,
    new_users INTEGER DEFAULT 0,
    churned_users INTEGER DEFAULT 0,
    
    -- Communication metrics
    messages_sent INTEGER DEFAULT 0,
    messages_delivered INTEGER DEFAULT 0,
    messages_engaged INTEGER DEFAULT 0,
    
    -- Engagement rates
    delivery_rate FLOAT DEFAULT 0.0,
    engagement_rate FLOAT DEFAULT 0.0,
    retention_rate FLOAT DEFAULT 0.0,
    
    -- Financial metrics
    avg_revenue_per_user NUMERIC(10, 2) DEFAULT 0.0,
    total_revenue NUMERIC(12, 2) DEFAULT 0.0,
    conversion_rate FLOAT DEFAULT 0.0,
    
    -- Channel performance
    channel_performance JSONB, -- {channel: {metrics}}
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX idx_communication_metrics_date ON communication_metrics(date);
CREATE INDEX idx_communication_metrics_channel ON communication_metrics(channel);
CREATE INDEX idx_communication_metrics_alert_type ON communication_metrics(alert_type);
CREATE INDEX idx_communication_metrics_user_segment ON communication_metrics(user_segment);
CREATE INDEX idx_communication_metrics_metric_type ON communication_metrics(metric_type);

CREATE INDEX idx_user_engagement_analytics_user_id ON user_engagement_analytics(user_id);
CREATE INDEX idx_user_engagement_analytics_engagement_score ON user_engagement_analytics(engagement_score);

CREATE INDEX idx_financial_impact_metrics_user_id ON financial_impact_metrics(user_id);
CREATE INDEX idx_financial_impact_metrics_outcome_type ON financial_impact_metrics(outcome_type);
CREATE INDEX idx_financial_impact_metrics_outcome_date ON financial_impact_metrics(outcome_date);

CREATE INDEX idx_ab_test_results_test_name ON ab_test_results(test_name);
CREATE INDEX idx_ab_test_results_test_status ON ab_test_results(test_status);
CREATE INDEX idx_ab_test_results_start_date ON ab_test_results(start_date);

CREATE INDEX idx_communication_queue_status_queue_name ON communication_queue_status(queue_name);
CREATE INDEX idx_communication_queue_status_is_healthy ON communication_queue_status(is_healthy);

CREATE INDEX idx_analytics_alerts_alert_type ON analytics_alerts(alert_type);
CREATE INDEX idx_analytics_alerts_alert_severity ON analytics_alerts(alert_severity);
CREATE INDEX idx_analytics_alerts_alert_status ON analytics_alerts(alert_status);
CREATE INDEX idx_analytics_alerts_created_at ON analytics_alerts(created_at);

CREATE INDEX idx_analytics_reports_report_type ON analytics_reports(report_type);
CREATE INDEX idx_analytics_reports_report_date ON analytics_reports(report_date);

CREATE INDEX idx_user_segment_performance_segment ON user_segment_performance(user_segment);
CREATE INDEX idx_user_segment_performance_date ON user_segment_performance(date);

-- Create triggers for updated_at timestamps
CREATE TRIGGER update_communication_metrics_updated_at 
    BEFORE UPDATE ON communication_metrics 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_user_engagement_analytics_updated_at 
    BEFORE UPDATE ON user_engagement_analytics 
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

CREATE TRIGGER update_user_segment_performance_updated_at 
    BEFORE UPDATE ON user_segment_performance 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insert default queue status records
INSERT INTO communication_queue_status (
    queue_name, channel, queue_depth, messages_processed, 
    messages_failed, messages_pending, is_healthy, health_score
) VALUES 
    ('sms_critical', 'sms', 0, 0, 0, 0, TRUE, 100.0),
    ('sms_daily', 'sms', 0, 0, 0, 0, TRUE, 100.0),
    ('email_reports', 'email', 0, 0, 0, 0, TRUE, 100.0),
    ('email_education', 'email', 0, 0, 0, 0, TRUE, 100.0),
    ('communication', 'email', 0, 0, 0, 0, TRUE, 100.0),
    ('alerts', 'sms', 0, 0, 0, 0, TRUE, 100.0),
    ('batch', 'email', 0, 0, 0, 0, TRUE, 100.0),
    ('fallback', 'sms', 0, 0, 0, 0, TRUE, 100.0),
    ('monitoring', 'email', 0, 0, 0, 0, TRUE, 100.0),
    ('followup', 'email', 0, 0, 0, 0, TRUE, 100.0),
    ('analytics', 'email', 0, 0, 0, 0, TRUE, 100.0),
    ('optimization', 'email', 0, 0, 0, 0, TRUE, 100.0);

-- Insert default alert thresholds
INSERT INTO analytics_alerts (
    alert_type, alert_severity, metric_name, threshold_value, 
    current_value, comparison_operator, alert_message, alert_description
) VALUES 
    ('low_delivery_rate', 'high', 'delivery_rate', 85.0, 0.0, '<', 
     'Low delivery rate detected', 'Delivery rate has fallen below 85% threshold'),
    ('high_opt_out_rate', 'medium', 'opt_out_rate', 5.0, 0.0, '>', 
     'High opt-out rate detected', 'Opt-out rate has exceeded 5% threshold'),
    ('cost_threshold_breach', 'critical', 'cost_per_engagement', 2.0, 0.0, '>', 
     'Cost threshold breached', 'Cost per engagement has exceeded $2.00 threshold'),
    ('queue_depth_alert', 'medium', 'queue_depth', 1000, 0, '>', 
     'High queue depth detected', 'Message queue depth has exceeded 1000 messages'),
    ('error_rate_alert', 'high', 'error_rate', 10.0, 0.0, '>', 
     'High error rate detected', 'Communication error rate has exceeded 10% threshold'); 