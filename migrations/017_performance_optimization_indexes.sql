-- =============================================================================
-- PERFORMANCE OPTIMIZATION MIGRATION
-- Comprehensive database optimization for AI Calculator
-- =============================================================================

-- Migration: 017_performance_optimization_indexes
-- Description: Add performance indexes for fast job title lookups, assessment submissions, and analytics queries
-- Target: <2 second load time, <500ms assessment submission, 99.9% uptime

-- =============================================================================
-- 1. JOB TITLE LOOKUP OPTIMIZATION
-- =============================================================================

-- Full-text search index for job titles (PostgreSQL)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_ai_job_assessments_job_title_fts 
ON ai_job_assessments USING gin(to_tsvector('english', job_title));

-- Trigram index for fuzzy job title matching
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_ai_job_assessments_job_title_trgm 
ON ai_job_assessments USING gin(job_title gin_trgm_ops);

-- Composite index for industry + job title lookups
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_ai_job_assessments_industry_job_title 
ON ai_job_assessments(industry, job_title);

-- Partial index for active job titles only
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_ai_job_assessments_active_job_titles 
ON ai_job_assessments(job_title) WHERE completed_at IS NOT NULL;

-- =============================================================================
-- 2. ASSESSMENT SUBMISSION OPTIMIZATION
-- =============================================================================

-- Fast email-based lookups for anonymous users
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_ai_job_assessments_email_completed 
ON ai_job_assessments(email, completed_at DESC);

-- Risk level and score filtering
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_ai_job_assessments_risk_level_score 
ON ai_job_assessments(overall_risk_level, automation_score DESC, augmentation_score DESC);

-- Session tracking for user journey analysis
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_ai_job_assessments_session_tracking 
ON ai_job_assessments(session_id, created_at) WHERE session_id IS NOT NULL;

-- Lead source conversion tracking
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_ai_job_assessments_lead_source_conversion 
ON ai_job_assessments(lead_source, completed_at, overall_risk_level);

-- =============================================================================
-- 3. ANALYTICS QUERY OPTIMIZATION
-- =============================================================================

-- Time-series analytics for trend analysis
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_ai_job_assessments_time_series 
ON ai_job_assessments(created_at, overall_risk_level, industry);

-- Geographic analytics (if location data is available)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_ai_job_assessments_location_analytics 
ON ai_job_assessments(location, created_at) WHERE location IS NOT NULL;

-- Experience level and automation correlation
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_ai_job_assessments_experience_automation 
ON ai_job_assessments(experience_level, automation_score, industry);

-- Team size and AI usage correlation
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_ai_job_assessments_team_ai_correlation 
ON ai_job_assessments(team_size, ai_usage_frequency, automation_score);

-- =============================================================================
-- 4. READ REPLICA OPTIMIZATION (for analytics queries)
-- =============================================================================

-- Materialized view for frequently accessed analytics
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_assessment_analytics AS
SELECT 
    DATE_TRUNC('day', created_at) as date,
    overall_risk_level,
    industry,
    experience_level,
    AVG(automation_score) as avg_automation_score,
    AVG(augmentation_score) as avg_augmentation_score,
    COUNT(*) as assessment_count,
    COUNT(DISTINCT email) as unique_users
FROM ai_job_assessments 
WHERE completed_at IS NOT NULL
GROUP BY 1, 2, 3, 4;

-- Index on materialized view
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_mv_assessment_analytics_date_risk 
ON mv_assessment_analytics(date DESC, overall_risk_level);

-- Refresh function for materialized view
CREATE OR REPLACE FUNCTION refresh_assessment_analytics()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_assessment_analytics;
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- 5. CACHE-OPTIMIZED QUERIES
-- =============================================================================

-- Function to get cached job risk data
CREATE OR REPLACE FUNCTION get_cached_job_risk(
    p_job_title TEXT,
    p_industry TEXT,
    p_experience_level TEXT
) RETURNS TABLE(
    automation_score INTEGER,
    augmentation_score INTEGER,
    risk_level TEXT,
    confidence DECIMAL
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        AVG(automation_score)::INTEGER,
        AVG(augmentation_score)::INTEGER,
        MODE() WITHIN GROUP (ORDER BY overall_risk_level) as risk_level,
        COUNT(*)::DECIMAL / (SELECT COUNT(*) FROM ai_job_assessments WHERE job_title ILIKE '%' || p_job_title || '%') as confidence
    FROM ai_job_assessments 
    WHERE job_title ILIKE '%' || p_job_title || '%'
    AND industry = p_industry
    AND experience_level = p_experience_level
    AND completed_at >= NOW() - INTERVAL '30 days';
END;
$$ LANGUAGE plpgsql STABLE;

-- =============================================================================
-- 6. CONNECTION POOLING OPTIMIZATION
-- =============================================================================

-- Function to get connection pool statistics
CREATE OR REPLACE FUNCTION get_connection_pool_stats()
RETURNS TABLE(
    pool_name TEXT,
    active_connections INTEGER,
    idle_connections INTEGER,
    total_connections INTEGER
) AS $$
BEGIN
    -- This would be implemented based on your connection pooling solution
    -- For now, return placeholder data
    RETURN QUERY
    SELECT 
        'main_pool'::TEXT,
        5::INTEGER,
        15::INTEGER,
        20::INTEGER;
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- 7. PERFORMANCE MONITORING
-- =============================================================================

-- Table for performance metrics
CREATE TABLE IF NOT EXISTS performance_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    metric_name VARCHAR(100) NOT NULL,
    metric_value DECIMAL NOT NULL,
    metric_unit VARCHAR(20),
    recorded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    context JSONB
);

-- Index for performance metrics queries
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_performance_metrics_name_time 
ON performance_metrics(metric_name, recorded_at DESC);

-- Function to record performance metrics
CREATE OR REPLACE FUNCTION record_performance_metric(
    p_metric_name TEXT,
    p_metric_value DECIMAL,
    p_metric_unit TEXT DEFAULT NULL,
    p_context JSONB DEFAULT NULL
) RETURNS void AS $$
BEGIN
    INSERT INTO performance_metrics (metric_name, metric_value, metric_unit, context)
    VALUES (p_metric_name, p_metric_value, p_metric_unit, p_context);
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- 8. QUERY OPTIMIZATION HINTS
-- =============================================================================

-- Function to analyze slow queries
CREATE OR REPLACE FUNCTION analyze_slow_queries()
RETURNS TABLE(
    query_text TEXT,
    execution_time DECIMAL,
    calls BIGINT,
    mean_time DECIMAL
) AS $$
BEGIN
    -- This would query pg_stat_statements for slow queries
    -- Requires pg_stat_statements extension
    RETURN QUERY
    SELECT 
        query::TEXT,
        total_time::DECIMAL,
        calls::BIGINT,
        mean_time::DECIMAL
    FROM pg_stat_statements 
    WHERE mean_time > 100  -- Queries taking more than 100ms
    ORDER BY mean_time DESC
    LIMIT 10;
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- 9. AUTOMATIC MAINTENANCE
-- =============================================================================

-- Function to update table statistics
CREATE OR REPLACE FUNCTION update_table_statistics()
RETURNS void AS $$
BEGIN
    ANALYZE ai_job_assessments;
    ANALYZE performance_metrics;
    
    -- Update materialized view
    PERFORM refresh_assessment_analytics();
    
    -- Record maintenance completion
    PERFORM record_performance_metric('maintenance_completed', 1, 'count');
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- 10. MONITORING AND ALERTING
-- =============================================================================

-- Table for system alerts
CREATE TABLE IF NOT EXISTS system_alerts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    alert_type VARCHAR(50) NOT NULL,
    severity VARCHAR(20) NOT NULL CHECK (severity IN ('low', 'medium', 'high', 'critical')),
    message TEXT NOT NULL,
    context JSONB,
    resolved_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index for alert queries
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_system_alerts_type_severity 
ON system_alerts(alert_type, severity, created_at DESC);

-- Function to create performance alerts
CREATE OR REPLACE FUNCTION create_performance_alert(
    p_alert_type TEXT,
    p_severity TEXT,
    p_message TEXT,
    p_context JSONB DEFAULT NULL
) RETURNS void AS $$
BEGIN
    INSERT INTO system_alerts (alert_type, severity, message, context)
    VALUES (p_alert_type, p_severity, p_message, p_context);
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- 11. PERFORMANCE THRESHOLDS
-- =============================================================================

-- Function to check performance thresholds
CREATE OR REPLACE FUNCTION check_performance_thresholds()
RETURNS TABLE(
    threshold_name TEXT,
    current_value DECIMAL,
    threshold_value DECIMAL,
    status TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        'avg_query_time'::TEXT,
        (SELECT AVG(metric_value) FROM performance_metrics WHERE metric_name = 'query_time' AND recorded_at >= NOW() - INTERVAL '1 hour'),
        500::DECIMAL,  -- 500ms threshold
        CASE 
            WHEN (SELECT AVG(metric_value) FROM performance_metrics WHERE metric_name = 'query_time' AND recorded_at >= NOW() - INTERVAL '1 hour') > 500 
            THEN 'exceeded'::TEXT 
            ELSE 'ok'::TEXT 
        END;
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- 12. MIGRATION COMPLETION
-- =============================================================================

-- Record migration completion
INSERT INTO performance_metrics (metric_name, metric_value, metric_unit, context)
VALUES (
    'migration_completed',
    1,
    'count',
    '{"migration": "017_performance_optimization_indexes", "timestamp": "' || NOW() || '"}'
);

-- Log migration completion
DO $$
BEGIN
    RAISE NOTICE 'Performance optimization migration completed successfully';
    RAISE NOTICE 'Added % indexes for job title lookups', (SELECT COUNT(*) FROM pg_indexes WHERE indexname LIKE 'idx_ai_job_assessments_job_title%');
    RAISE NOTICE 'Added % indexes for assessment submissions', (SELECT COUNT(*) FROM pg_indexes WHERE indexname LIKE 'idx_ai_job_assessments_%' AND indexname NOT LIKE '%job_title%');
    RAISE NOTICE 'Created materialized view for analytics optimization';
END $$;
