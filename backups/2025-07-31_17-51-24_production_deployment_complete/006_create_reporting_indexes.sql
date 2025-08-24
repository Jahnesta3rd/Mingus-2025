-- Migration: Create Reporting System Indexes
-- Description: Add performance indexes for the reporting system
-- Date: 2025-01-27

-- Performance indexes for communication_metrics table
-- These indexes optimize the reporting queries for better performance

-- Index for date-based queries (most common)
CREATE INDEX IF NOT EXISTS idx_comm_metrics_sent_at 
ON communication_metrics(sent_at);

-- Index for user-specific queries
CREATE INDEX IF NOT EXISTS idx_comm_metrics_user_id 
ON communication_metrics(user_id);

-- Index for channel-based queries
CREATE INDEX IF NOT EXISTS idx_comm_metrics_channel 
ON communication_metrics(channel);

-- Index for message type queries
CREATE INDEX IF NOT EXISTS idx_comm_metrics_message_type 
ON communication_metrics(message_type);

-- Index for status-based queries
CREATE INDEX IF NOT EXISTS idx_comm_metrics_status 
ON communication_metrics(status);

-- Composite indexes for common query patterns

-- User + Date (for user-specific time series)
CREATE INDEX IF NOT EXISTS idx_comm_metrics_user_date 
ON communication_metrics(user_id, sent_at);

-- Channel + Date (for channel performance over time)
CREATE INDEX IF NOT EXISTS idx_comm_metrics_channel_date 
ON communication_metrics(channel, sent_at);

-- Message Type + Date (for message type performance over time)
CREATE INDEX IF NOT EXISTS idx_comm_metrics_type_date 
ON communication_metrics(message_type, sent_at);

-- Status + Date (for delivery rate analysis)
CREATE INDEX IF NOT EXISTS idx_comm_metrics_status_date 
ON communication_metrics(status, sent_at);

-- User + Channel (for user channel preferences)
CREATE INDEX IF NOT EXISTS idx_comm_metrics_user_channel 
ON communication_metrics(user_id, channel);

-- User + Message Type (for user message type analysis)
CREATE INDEX IF NOT EXISTS idx_comm_metrics_user_type 
ON communication_metrics(user_id, message_type);

-- Indexes for engagement tracking
-- These help with open/click/action rate calculations

-- Index for opened messages
CREATE INDEX IF NOT EXISTS idx_comm_metrics_opened_at 
ON communication_metrics(opened_at) 
WHERE opened_at IS NOT NULL;

-- Index for clicked messages
CREATE INDEX IF NOT EXISTS idx_comm_metrics_clicked_at 
ON communication_metrics(clicked_at) 
WHERE clicked_at IS NOT NULL;

-- Index for delivered messages
CREATE INDEX IF NOT EXISTS idx_comm_metrics_delivered_at 
ON communication_metrics(delivered_at) 
WHERE delivered_at IS NOT NULL;

-- Index for action tracking
CREATE INDEX IF NOT EXISTS idx_comm_metrics_action_taken 
ON communication_metrics(action_taken) 
WHERE action_taken IS NOT NULL;

-- Partial indexes for cost analysis
CREATE INDEX IF NOT EXISTS idx_comm_metrics_cost 
ON communication_metrics(cost) 
WHERE cost > 0;

-- Composite indexes for complex reporting queries

-- User + Date + Status (for user delivery rate analysis)
CREATE INDEX IF NOT EXISTS idx_comm_metrics_user_date_status 
ON communication_metrics(user_id, sent_at, status);

-- Channel + Date + Status (for channel delivery rate analysis)
CREATE INDEX IF NOT EXISTS idx_comm_metrics_channel_date_status 
ON communication_metrics(channel, sent_at, status);

-- Message Type + Date + Status (for message type delivery rate analysis)
CREATE INDEX IF NOT EXISTS idx_comm_metrics_type_date_status 
ON communication_metrics(message_type, sent_at, status);

-- User + Date + Channel (for user channel performance over time)
CREATE INDEX IF NOT EXISTS idx_comm_metrics_user_date_channel 
ON communication_metrics(user_id, sent_at, channel);

-- Indexes for time-based aggregations
-- These help with date_trunc and date functions

-- Index for daily aggregations
CREATE INDEX IF NOT EXISTS idx_comm_metrics_date_daily 
ON communication_metrics(DATE(sent_at));

-- Index for weekly aggregations (if using date_trunc)
CREATE INDEX IF NOT EXISTS idx_comm_metrics_date_weekly 
ON communication_metrics(DATE_TRUNC('week', sent_at));

-- Index for monthly aggregations (if using date_trunc)
CREATE INDEX IF NOT EXISTS idx_comm_metrics_date_monthly 
ON communication_metrics(DATE_TRUNC('month', sent_at));

-- Indexes for user engagement analysis
-- These help with user segmentation queries

-- Index for users with opened messages
CREATE INDEX IF NOT EXISTS idx_comm_metrics_user_opened 
ON communication_metrics(user_id) 
WHERE opened_at IS NOT NULL;

-- Index for users with clicked messages
CREATE INDEX IF NOT EXISTS idx_comm_metrics_user_clicked 
ON communication_metrics(user_id) 
WHERE clicked_at IS NOT NULL;

-- Index for users with actions
CREATE INDEX IF NOT EXISTS idx_comm_metrics_user_action 
ON communication_metrics(user_id) 
WHERE action_taken IS NOT NULL;

-- Indexes for cost analysis
-- These help with cost tracking and ROI analysis

-- Index for cost by user
CREATE INDEX IF NOT EXISTS idx_comm_metrics_user_cost 
ON communication_metrics(user_id, cost);

-- Index for cost by channel
CREATE INDEX IF NOT EXISTS idx_comm_metrics_channel_cost 
ON communication_metrics(channel, cost);

-- Index for cost by message type
CREATE INDEX IF NOT EXISTS idx_comm_metrics_type_cost 
ON communication_metrics(message_type, cost);

-- Index for cost by date
CREATE INDEX IF NOT EXISTS idx_comm_metrics_date_cost 
ON communication_metrics(sent_at, cost);

-- Function to update communication metrics statistics
-- This function helps maintain aggregated statistics for faster reporting

CREATE OR REPLACE FUNCTION update_communication_metrics_stats()
RETURNS TRIGGER AS $$
BEGIN
    -- This function can be used to maintain materialized views or summary tables
    -- for faster reporting queries
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to update statistics when communication metrics change
CREATE TRIGGER trigger_update_comm_metrics_stats
    AFTER INSERT OR UPDATE OR DELETE ON communication_metrics
    FOR EACH ROW
    EXECUTE FUNCTION update_communication_metrics_stats();

-- Create a summary table for daily metrics (optional, for very large datasets)
-- This table can be populated by a scheduled job for faster daily reporting

CREATE TABLE IF NOT EXISTS daily_communication_summary (
    summary_date DATE PRIMARY KEY,
    total_messages INTEGER DEFAULT 0,
    delivered_messages INTEGER DEFAULT 0,
    opened_messages INTEGER DEFAULT 0,
    clicked_messages INTEGER DEFAULT 0,
    action_messages INTEGER DEFAULT 0,
    total_cost DECIMAL(10,2) DEFAULT 0.00,
    sms_messages INTEGER DEFAULT 0,
    email_messages INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index for the summary table
CREATE INDEX IF NOT EXISTS idx_daily_summary_date 
ON daily_communication_summary(summary_date);

-- Function to populate daily summary table
CREATE OR REPLACE FUNCTION populate_daily_summary(target_date DATE DEFAULT CURRENT_DATE)
RETURNS VOID AS $$
BEGIN
    INSERT INTO daily_communication_summary (
        summary_date,
        total_messages,
        delivered_messages,
        opened_messages,
        clicked_messages,
        action_messages,
        total_cost,
        sms_messages,
        email_messages,
        updated_at
    )
    SELECT 
        DATE(sent_at) as summary_date,
        COUNT(*) as total_messages,
        COUNT(CASE WHEN status = 'delivered' THEN 1 END) as delivered_messages,
        COUNT(CASE WHEN opened_at IS NOT NULL THEN 1 END) as opened_messages,
        COUNT(CASE WHEN clicked_at IS NOT NULL THEN 1 END) as clicked_messages,
        COUNT(CASE WHEN action_taken IS NOT NULL THEN 1 END) as action_messages,
        COALESCE(SUM(cost), 0.00) as total_cost,
        COUNT(CASE WHEN channel = 'sms' THEN 1 END) as sms_messages,
        COUNT(CASE WHEN channel = 'email' THEN 1 END) as email_messages,
        NOW() as updated_at
    FROM communication_metrics
    WHERE DATE(sent_at) = target_date
    GROUP BY DATE(sent_at)
    ON CONFLICT (summary_date) 
    DO UPDATE SET
        total_messages = EXCLUDED.total_messages,
        delivered_messages = EXCLUDED.delivered_messages,
        opened_messages = EXCLUDED.opened_messages,
        clicked_messages = EXCLUDED.clicked_messages,
        action_messages = EXCLUDED.action_messages,
        total_cost = EXCLUDED.total_cost,
        sms_messages = EXCLUDED.sms_messages,
        email_messages = EXCLUDED.email_messages,
        updated_at = NOW();
END;
$$ LANGUAGE plpgsql;

-- Create a view for easy access to user engagement metrics
CREATE OR REPLACE VIEW user_engagement_summary AS
SELECT 
    user_id,
    COUNT(*) as total_messages,
    COUNT(CASE WHEN status = 'delivered' THEN 1 END) as delivered_messages,
    COUNT(CASE WHEN opened_at IS NOT NULL THEN 1 END) as opened_messages,
    COUNT(CASE WHEN clicked_at IS NOT NULL THEN 1 END) as clicked_messages,
    COUNT(CASE WHEN action_taken IS NOT NULL THEN 1 END) as action_messages,
    COALESCE(SUM(cost), 0.00) as total_cost,
    COUNT(CASE WHEN channel = 'sms' THEN 1 END) as sms_messages,
    COUNT(CASE WHEN channel = 'email' THEN 1 END) as email_messages,
    CASE 
        WHEN COUNT(*) > 0 THEN 
            ROUND((COUNT(CASE WHEN status = 'delivered' THEN 1 END)::DECIMAL / COUNT(*)) * 100, 2)
        ELSE 0 
    END as delivery_rate,
    CASE 
        WHEN COUNT(*) > 0 THEN 
            ROUND((COUNT(CASE WHEN opened_at IS NOT NULL THEN 1 END)::DECIMAL / COUNT(*)) * 100, 2)
        ELSE 0 
    END as open_rate,
    CASE 
        WHEN COUNT(*) > 0 THEN 
            ROUND((COUNT(CASE WHEN clicked_at IS NOT NULL THEN 1 END)::DECIMAL / COUNT(*)) * 100, 2)
        ELSE 0 
    END as click_rate,
    CASE 
        WHEN COUNT(*) > 0 THEN 
            ROUND((COUNT(CASE WHEN action_taken IS NOT NULL THEN 1 END)::DECIMAL / COUNT(*)) * 100, 2)
        ELSE 0 
    END as action_rate,
    MAX(sent_at) as last_communication_date
FROM communication_metrics
GROUP BY user_id;

-- Create a view for channel performance summary
CREATE OR REPLACE VIEW channel_performance_summary AS
SELECT 
    channel,
    COUNT(*) as total_messages,
    COUNT(CASE WHEN status = 'delivered' THEN 1 END) as delivered_messages,
    COUNT(CASE WHEN opened_at IS NOT NULL THEN 1 END) as opened_messages,
    COUNT(CASE WHEN clicked_at IS NOT NULL THEN 1 END) as clicked_messages,
    COUNT(CASE WHEN action_taken IS NOT NULL THEN 1 END) as action_messages,
    COALESCE(SUM(cost), 0.00) as total_cost,
    CASE 
        WHEN COUNT(*) > 0 THEN 
            ROUND((COUNT(CASE WHEN status = 'delivered' THEN 1 END)::DECIMAL / COUNT(*)) * 100, 2)
        ELSE 0 
    END as delivery_rate,
    CASE 
        WHEN COUNT(*) > 0 THEN 
            ROUND((COUNT(CASE WHEN opened_at IS NOT NULL THEN 1 END)::DECIMAL / COUNT(*)) * 100, 2)
        ELSE 0 
    END as open_rate,
    CASE 
        WHEN COUNT(*) > 0 THEN 
            ROUND((COUNT(CASE WHEN clicked_at IS NOT NULL THEN 1 END)::DECIMAL / COUNT(*)) * 100, 2)
        ELSE 0 
    END as click_rate,
    CASE 
        WHEN COUNT(*) > 0 THEN 
            ROUND((COUNT(CASE WHEN action_taken IS NOT NULL THEN 1 END)::DECIMAL / COUNT(*)) * 100, 2)
        ELSE 0 
    END as action_rate,
    CASE 
        WHEN COUNT(*) > 0 THEN 
            ROUND(COALESCE(SUM(cost), 0.00) / COUNT(*), 4)
        ELSE 0 
    END as avg_cost_per_message
FROM communication_metrics
GROUP BY channel;

-- Create a view for message type performance summary
CREATE OR REPLACE VIEW message_type_performance_summary AS
SELECT 
    message_type,
    COUNT(*) as total_messages,
    COUNT(CASE WHEN status = 'delivered' THEN 1 END) as delivered_messages,
    COUNT(CASE WHEN opened_at IS NOT NULL THEN 1 END) as opened_messages,
    COUNT(CASE WHEN clicked_at IS NOT NULL THEN 1 END) as clicked_messages,
    COUNT(CASE WHEN action_taken IS NOT NULL THEN 1 END) as action_messages,
    COALESCE(SUM(cost), 0.00) as total_cost,
    CASE 
        WHEN COUNT(*) > 0 THEN 
            ROUND((COUNT(CASE WHEN status = 'delivered' THEN 1 END)::DECIMAL / COUNT(*)) * 100, 2)
        ELSE 0 
    END as delivery_rate,
    CASE 
        WHEN COUNT(*) > 0 THEN 
            ROUND((COUNT(CASE WHEN opened_at IS NOT NULL THEN 1 END)::DECIMAL / COUNT(*)) * 100, 2)
        ELSE 0 
    END as open_rate,
    CASE 
        WHEN COUNT(*) > 0 THEN 
            ROUND((COUNT(CASE WHEN clicked_at IS NOT NULL THEN 1 END)::DECIMAL / COUNT(*)) * 100, 2)
        ELSE 0 
    END as click_rate,
    CASE 
        WHEN COUNT(*) > 0 THEN 
            ROUND((COUNT(CASE WHEN action_taken IS NOT NULL THEN 1 END)::DECIMAL / COUNT(*)) * 100, 2)
        ELSE 0 
    END as action_rate,
    CASE 
        WHEN COUNT(*) > 0 THEN 
            ROUND(COALESCE(SUM(cost), 0.00) / COUNT(*), 4)
        ELSE 0 
    END as avg_cost_per_message
FROM communication_metrics
GROUP BY message_type;

-- Grant permissions for the views
GRANT SELECT ON user_engagement_summary TO PUBLIC;
GRANT SELECT ON channel_performance_summary TO PUBLIC;
GRANT SELECT ON message_type_performance_summary TO PUBLIC;

-- Log the migration completion
INSERT INTO migration_log (migration_name, applied_at, description)
VALUES (
    '006_create_reporting_indexes',
    NOW(),
    'Created performance indexes and views for the reporting system'
); 