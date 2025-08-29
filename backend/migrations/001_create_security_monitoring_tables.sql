-- Security Monitoring Database Tables
-- Creates tables for comprehensive security monitoring system

-- Security Events Table
CREATE TABLE IF NOT EXISTS security_events (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    event_type VARCHAR(50) NOT NULL,
    user_identifier VARCHAR(255) NOT NULL,
    severity VARCHAR(20) NOT NULL,
    ip_address INET,
    user_agent TEXT,
    endpoint VARCHAR(255),
    method VARCHAR(10),
    details JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for security_events
CREATE INDEX IF NOT EXISTS idx_security_events_timestamp ON security_events (timestamp);
CREATE INDEX IF NOT EXISTS idx_security_events_event_type ON security_events (event_type);
CREATE INDEX IF NOT EXISTS idx_security_events_user_identifier ON security_events (user_identifier);
CREATE INDEX IF NOT EXISTS idx_security_events_severity ON security_events (severity);
CREATE INDEX IF NOT EXISTS idx_security_events_ip_address ON security_events (ip_address);
CREATE INDEX IF NOT EXISTS idx_security_events_created_at ON security_events (created_at);

-- Security Alerts Table
CREATE TABLE IF NOT EXISTS security_alerts (
    id SERIAL PRIMARY KEY,
    alert_type VARCHAR(50) NOT NULL,
    event_type VARCHAR(50) NOT NULL,
    count INTEGER NOT NULL,
    timeframe INTEGER NOT NULL,
    alert_details JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for security_alerts
CREATE INDEX IF NOT EXISTS idx_security_alerts_alert_type ON security_alerts (alert_type);
CREATE INDEX IF NOT EXISTS idx_security_alerts_event_type ON security_alerts (event_type);
CREATE INDEX IF NOT EXISTS idx_security_alerts_created_at ON security_alerts (created_at);

-- Assessment Anomalies Table
CREATE TABLE IF NOT EXISTS assessment_anomalies (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    assessment_type VARCHAR(100) NOT NULL,
    anomaly_type VARCHAR(100) NOT NULL,
    severity VARCHAR(20) NOT NULL,
    details JSONB,
    detected_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for assessment_anomalies
CREATE INDEX IF NOT EXISTS idx_assessment_anomalies_user_id ON assessment_anomalies (user_id);
CREATE INDEX IF NOT EXISTS idx_assessment_anomalies_assessment_type ON assessment_anomalies (assessment_type);
CREATE INDEX IF NOT EXISTS idx_assessment_anomalies_anomaly_type ON assessment_anomalies (anomaly_type);
CREATE INDEX IF NOT EXISTS idx_assessment_anomalies_severity ON assessment_anomalies (severity);
CREATE INDEX IF NOT EXISTS idx_assessment_anomalies_detected_at ON assessment_anomalies (detected_at);

-- Security Metrics Table
CREATE TABLE IF NOT EXISTS security_metrics (
    id SERIAL PRIMARY KEY,
    metric_name VARCHAR(100) NOT NULL,
    metric_value NUMERIC,
    metric_unit VARCHAR(20),
    time_period VARCHAR(20) NOT NULL,
    recorded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for security_metrics
CREATE INDEX IF NOT EXISTS idx_security_metrics_metric_name ON security_metrics (metric_name);
CREATE INDEX IF NOT EXISTS idx_security_metrics_time_period ON security_metrics (time_period);
CREATE INDEX IF NOT EXISTS idx_security_metrics_recorded_at ON security_metrics (recorded_at);

-- Blocked IPs Table
CREATE TABLE IF NOT EXISTS blocked_ips (
    id SERIAL PRIMARY KEY,
    ip_address INET NOT NULL,
    reason VARCHAR(255) NOT NULL,
    blocked_until TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE,
    UNIQUE(ip_address)
);

-- Create indexes for blocked_ips
CREATE INDEX IF NOT EXISTS idx_blocked_ips_ip_address ON blocked_ips (ip_address);
CREATE INDEX IF NOT EXISTS idx_blocked_ips_blocked_until ON blocked_ips (blocked_until);
CREATE INDEX IF NOT EXISTS idx_blocked_ips_is_active ON blocked_ips (is_active);

-- Security Audit Log Table
CREATE TABLE IF NOT EXISTS security_audit_log (
    id SERIAL PRIMARY KEY,
    table_name VARCHAR(100) NOT NULL,
    operation VARCHAR(10) NOT NULL,
    record_id INTEGER,
    old_data JSONB,
    new_data JSONB,
    changed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for security_audit_log
CREATE INDEX IF NOT EXISTS idx_security_audit_log_table_name ON security_audit_log (table_name);
CREATE INDEX IF NOT EXISTS idx_security_audit_log_operation ON security_audit_log (operation);
CREATE INDEX IF NOT EXISTS idx_security_audit_log_changed_at ON security_audit_log (changed_at);

-- Security Dashboard Views
CREATE OR REPLACE VIEW security_events_summary AS
SELECT 
    DATE_TRUNC('hour', timestamp) as hour,
    event_type,
    severity,
    COUNT(*) as event_count,
    COUNT(DISTINCT user_identifier) as unique_users,
    COUNT(DISTINCT ip_address) as unique_ips
FROM security_events
WHERE timestamp >= NOW() - INTERVAL '24 hours'
GROUP BY DATE_TRUNC('hour', timestamp), event_type, severity
ORDER BY hour DESC, event_count DESC;

CREATE OR REPLACE VIEW security_alerts_summary AS
SELECT 
    DATE_TRUNC('hour', created_at) as hour,
    alert_type,
    event_type,
    COUNT(*) as alert_count,
    AVG(count) as avg_event_count
FROM security_alerts
WHERE created_at >= NOW() - INTERVAL '24 hours'
GROUP BY DATE_TRUNC('hour', created_at), alert_type, event_type
ORDER BY hour DESC, alert_count DESC;

CREATE OR REPLACE VIEW assessment_anomalies_summary AS
SELECT 
    DATE_TRUNC('day', detected_at) as day,
    assessment_type,
    anomaly_type,
    severity,
    COUNT(*) as anomaly_count,
    COUNT(DISTINCT user_id) as affected_users
FROM assessment_anomalies
WHERE detected_at >= NOW() - INTERVAL '7 days'
GROUP BY DATE_TRUNC('day', detected_at), assessment_type, anomaly_type, severity
ORDER BY day DESC, anomaly_count DESC;

-- Security Retention Policy Function
CREATE OR REPLACE FUNCTION cleanup_old_security_events()
RETURNS void AS $$
BEGIN
    DELETE FROM security_events 
    WHERE timestamp < NOW() - INTERVAL '90 days';
    
    DELETE FROM security_alerts 
    WHERE created_at < NOW() - INTERVAL '90 days';
    
    DELETE FROM assessment_anomalies 
    WHERE detected_at < NOW() - INTERVAL '90 days';
    
    DELETE FROM security_metrics 
    WHERE recorded_at < NOW() - INTERVAL '90 days';
END;
$$ LANGUAGE plpgsql;

-- Security Event Triggers
CREATE OR REPLACE FUNCTION log_security_event_trigger()
RETURNS TRIGGER AS $$
BEGIN
    -- Log to separate audit table for compliance
    INSERT INTO security_audit_log (
        table_name,
        operation,
        record_id,
        old_data,
        new_data,
        changed_at
    ) VALUES (
        'security_events',
        TG_OP,
        NEW.id,
        CASE WHEN TG_OP = 'UPDATE' THEN row_to_json(OLD) ELSE NULL END,
        CASE WHEN TG_OP IN ('INSERT', 'UPDATE') THEN row_to_json(NEW) ELSE NULL END,
        NOW()
    );
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER security_events_audit_trigger
    AFTER INSERT OR UPDATE OR DELETE ON security_events
    FOR EACH ROW EXECUTE FUNCTION log_security_event_trigger();

-- Insert initial security metrics
INSERT INTO security_metrics (metric_name, metric_value, metric_unit, time_period) VALUES
('total_security_events', 0, 'count', 'all_time'),
('failed_login_attempts', 0, 'count', 'last_24h'),
('injection_attempts', 0, 'count', 'last_24h'),
('assessment_anomalies', 0, 'count', 'last_24h'),
('blocked_ips', 0, 'count', 'current');

-- Create composite indexes for performance
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_security_events_composite 
ON security_events (event_type, severity, timestamp);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_security_alerts_composite 
ON security_alerts (alert_type, created_at);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_assessment_anomalies_composite 
ON assessment_anomalies (user_id, assessment_type, detected_at);
