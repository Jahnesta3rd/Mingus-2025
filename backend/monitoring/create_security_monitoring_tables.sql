-- Security Monitoring Database Tables
-- This script creates the necessary tables for comprehensive security performance monitoring

-- Security Performance Metrics Table
CREATE TABLE IF NOT EXISTS security_performance_metrics (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    operation_type VARCHAR(100) NOT NULL,
    duration_ms DECIMAL(10,3) NOT NULL,
    success BOOLEAN NOT NULL DEFAULT true,
    error_message TEXT,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Encryption Performance Metrics Table
CREATE TABLE IF NOT EXISTS encryption_performance_metrics (
    id SERIAL PRIMARY KEY,
    algorithm VARCHAR(50) NOT NULL,
    key_size INTEGER NOT NULL,
    operation VARCHAR(20) NOT NULL CHECK (operation IN ('encrypt', 'decrypt')),
    data_size_bytes BIGINT NOT NULL,
    duration_ms DECIMAL(10,3) NOT NULL,
    success BOOLEAN NOT NULL DEFAULT true,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Audit Log Performance Metrics Table
CREATE TABLE IF NOT EXISTS audit_log_performance_metrics (
    id SERIAL PRIMARY KEY,
    operation_type VARCHAR(100) NOT NULL,
    duration_ms DECIMAL(10,3) NOT NULL,
    log_size_bytes BIGINT NOT NULL,
    success BOOLEAN NOT NULL DEFAULT true,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    batch_size INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Key Rotation Performance Metrics Table
CREATE TABLE IF NOT EXISTS key_rotation_performance_metrics (
    id SERIAL PRIMARY KEY,
    key_type VARCHAR(50) NOT NULL,
    old_key_id VARCHAR(100) NOT NULL,
    new_key_id VARCHAR(100) NOT NULL,
    duration_ms DECIMAL(10,3) NOT NULL,
    success BOOLEAN NOT NULL DEFAULT true,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    affected_entities INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_security_performance_timestamp ON security_performance_metrics(timestamp);
CREATE INDEX IF NOT EXISTS idx_security_performance_operation_type ON security_performance_metrics(operation_type);
CREATE INDEX IF NOT EXISTS idx_security_performance_success ON security_performance_metrics(success);

CREATE INDEX IF NOT EXISTS idx_encryption_performance_timestamp ON encryption_performance_metrics(timestamp);
CREATE INDEX IF NOT EXISTS idx_encryption_performance_algorithm ON encryption_performance_metrics(algorithm);
CREATE INDEX IF NOT EXISTS idx_encryption_performance_operation ON encryption_performance_metrics(operation);

CREATE INDEX IF NOT EXISTS idx_audit_log_performance_timestamp ON audit_log_performance_metrics(timestamp);
CREATE INDEX IF NOT EXISTS idx_audit_log_performance_operation_type ON audit_log_performance_metrics(operation_type);

CREATE INDEX IF NOT EXISTS idx_key_rotation_performance_timestamp ON key_rotation_performance_metrics(timestamp);
CREATE INDEX IF NOT EXISTS idx_key_rotation_performance_key_type ON key_rotation_performance_metrics(key_type);

-- Create partitioned tables for better performance with large datasets
-- Security Performance Metrics Partitioning (by month)
CREATE TABLE IF NOT EXISTS security_performance_metrics_y2024m01 PARTITION OF security_performance_metrics
    FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');

CREATE TABLE IF NOT EXISTS security_performance_metrics_y2024m02 PARTITION OF security_performance_metrics
    FOR VALUES FROM ('2024-02-01') TO ('2024-03-01');

-- Add more partitions as needed for future months

-- Create views for common queries
CREATE OR REPLACE VIEW security_performance_summary AS
SELECT 
    DATE_TRUNC('hour', timestamp) as hour_bucket,
    operation_type,
    COUNT(*) as total_operations,
    AVG(duration_ms) as avg_duration_ms,
    MAX(duration_ms) as max_duration_ms,
    MIN(duration_ms) as min_duration_ms,
    SUM(CASE WHEN success THEN 1 ELSE 0 END) as successful_operations,
    SUM(CASE WHEN NOT success THEN 1 ELSE 0 END) as failed_operations,
    (SUM(CASE WHEN success THEN 1 ELSE 0 END)::DECIMAL / COUNT(*) * 100) as success_rate_percent
FROM security_performance_metrics
WHERE timestamp >= NOW() - INTERVAL '24 hours'
GROUP BY DATE_TRUNC('hour', timestamp), operation_type
ORDER BY hour_bucket DESC, operation_type;

CREATE OR REPLACE VIEW encryption_performance_summary AS
SELECT 
    DATE_TRUNC('hour', timestamp) as hour_bucket,
    algorithm,
    key_size,
    operation,
    COUNT(*) as total_operations,
    AVG(duration_ms) as avg_duration_ms,
    MAX(duration_ms) as max_duration_ms,
    AVG(data_size_bytes) as avg_data_size_bytes,
    SUM(CASE WHEN success THEN 1 ELSE 0 END) as successful_operations,
    (SUM(CASE WHEN success THEN 1 ELSE 0 END)::DECIMAL / COUNT(*) * 100) as success_rate_percent
FROM encryption_performance_metrics
WHERE timestamp >= NOW() - INTERVAL '24 hours'
GROUP BY DATE_TRUNC('hour', timestamp), algorithm, key_size, operation
ORDER BY hour_bucket DESC, algorithm, key_size, operation;

CREATE OR REPLACE VIEW audit_log_performance_summary AS
SELECT 
    DATE_TRUNC('hour', timestamp) as hour_bucket,
    operation_type,
    COUNT(*) as total_operations,
    AVG(duration_ms) as avg_duration_ms,
    MAX(duration_ms) as max_duration_ms,
    AVG(log_size_bytes) as avg_log_size_bytes,
    SUM(CASE WHEN success THEN 1 ELSE 0 END) as successful_operations,
    SUM(CASE WHEN NOT success THEN 1 ELSE 0 END) as failed_operations,
    (SUM(CASE WHEN success THEN 1 ELSE 0 END)::DECIMAL / COUNT(*) * 100) as success_rate_percent
FROM audit_log_performance_metrics
WHERE timestamp >= NOW() - INTERVAL '24 hours'
GROUP BY DATE_TRUNC('hour', timestamp), operation_type
ORDER BY hour_bucket DESC, operation_type;

-- Create function to automatically create monthly partitions
CREATE OR REPLACE FUNCTION create_monthly_partition(table_name TEXT, year_month TEXT)
RETURNS VOID AS $$
DECLARE
    partition_name TEXT;
    start_date DATE;
    end_date DATE;
BEGIN
    -- Parse year_month (format: 'YYYY-MM')
    start_date := TO_DATE(year_month || '-01', 'YYYY-MM-DD');
    end_date := start_date + INTERVAL '1 month';
    
    -- Create partition name
    partition_name := table_name || '_y' || REPLACE(year_month, '-', 'm');
    
    -- Create partition if it doesn't exist
    EXECUTE format('CREATE TABLE IF NOT EXISTS %I PARTITION OF %I FOR VALUES FROM (%L) TO (%L)',
                   partition_name, table_name, start_date, end_date);
    
    RAISE NOTICE 'Created partition % for table %', partition_name, table_name;
END;
$$ LANGUAGE plpgsql;

-- Create function to clean up old metrics data
CREATE OR REPLACE FUNCTION cleanup_old_security_metrics(days_to_keep INTEGER DEFAULT 30)
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER := 0;
    cutoff_date TIMESTAMP WITH TIME ZONE;
BEGIN
    cutoff_date := NOW() - (days_to_keep || ' days')::INTERVAL;
    
    -- Clean up security performance metrics
    DELETE FROM security_performance_metrics WHERE timestamp < cutoff_date;
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    
    -- Clean up encryption metrics
    DELETE FROM encryption_performance_metrics WHERE timestamp < cutoff_date;
    
    -- Clean up audit log metrics
    DELETE FROM audit_log_performance_metrics WHERE timestamp < cutoff_date;
    
    -- Clean up key rotation metrics
    DELETE FROM key_rotation_performance_metrics WHERE timestamp < cutoff_date;
    
    RAISE NOTICE 'Cleaned up security metrics older than % days', days_to_keep;
    
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Grant necessary permissions
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO mingus_user;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO mingus_user;

-- Create a scheduled job to clean up old data (if using pg_cron extension)
-- SELECT cron.schedule('cleanup-security-metrics', '0 2 * * *', 'SELECT cleanup_old_security_metrics(30);');

-- Insert sample data for testing (optional)
INSERT INTO security_performance_metrics (timestamp, operation_type, duration_ms, success, metadata) VALUES
(NOW() - INTERVAL '1 hour', 'user_authentication', 45.2, true, '{"user_id": "test123", "ip": "192.168.1.1"}'),
(NOW() - INTERVAL '30 minutes', 'password_validation', 12.8, true, '{"user_id": "test123"}'),
(NOW() - INTERVAL '15 minutes', 'session_creation', 23.1, true, '{"user_id": "test123", "session_id": "sess_abc123"}');

INSERT INTO encryption_performance_metrics (algorithm, key_size, operation, data_size_bytes, duration_ms, success, timestamp) VALUES
('AES-256', 256, 'encrypt', 1024, 15.3, true, NOW() - INTERVAL '1 hour'),
('AES-256', 256, 'decrypt', 1024, 12.7, true, NOW() - INTERVAL '1 hour'),
('RSA-2048', 2048, 'encrypt', 256, 45.2, true, NOW() - INTERVAL '30 minutes');

INSERT INTO audit_log_performance_metrics (operation_type, duration_ms, log_size_bytes, success, timestamp, batch_size) VALUES
('user_login', 8.5, 512, true, NOW() - INTERVAL '1 hour', 1),
('data_access', 12.3, 1024, true, NOW() - INTERVAL '30 minutes', 5),
('security_event', 15.7, 2048, true, NOW() - INTERVAL '15 minutes', 1);

-- Create a summary table for real-time monitoring
CREATE TABLE IF NOT EXISTS security_monitoring_summary (
    id SERIAL PRIMARY KEY,
    metric_type VARCHAR(50) NOT NULL,
    metric_value JSONB NOT NULL,
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Insert initial summary data
INSERT INTO security_monitoring_summary (metric_type, metric_value) VALUES
('system_health_score', '{"score": 100, "status": "healthy"}'),
('pci_compliance_status', '{"status": "compliant", "last_check": null}'),
('encryption_performance', '{"avg_duration_ms": 0, "success_rate": 100}'),
('audit_log_performance', '{"avg_duration_ms": 0, "success_rate": 100}');

-- Create index on summary table
CREATE INDEX IF NOT EXISTS idx_security_monitoring_summary_metric_type ON security_monitoring_summary(metric_type);
CREATE INDEX IF NOT EXISTS idx_security_monitoring_summary_last_updated ON security_monitoring_summary(last_updated);
