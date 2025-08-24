-- =============================================================================
-- MIGRATION: Add Real-time Salary Data Tables
-- =============================================================================
-- 
-- This migration extends the MINGUS PostgreSQL schema with new tables for
-- real-time salary data integration, market data, and confidence scoring.
--
-- Tables Added:
-- - salary_benchmarks: Core salary data from multiple sources
-- - market_data: Job market and economic indicators
-- - confidence_scores: Data quality and reliability metrics
--
-- Integration Points:
-- - Extends existing PostgreSQL schema with new tables
-- - Integrates with existing Redis caching system
-- - Uses existing Celery worker configuration
-- - Maintains UUID primary keys and JSONB flexibility
--
-- Author: MINGUS Development Team
-- Date: January 2025
-- Version: 1.0
-- =============================================================================

-- =============================================================================
-- SALARY BENCHMARKS TABLE
-- =============================================================================

CREATE TABLE salary_benchmarks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    location VARCHAR(255) NOT NULL, -- City, State or Metro area
    occupation VARCHAR(255) NOT NULL, -- Job title or SOC code
    industry VARCHAR(255), -- Industry classification
    experience_level VARCHAR(50), -- Entry, Mid, Senior, Executive
    education_level VARCHAR(50), -- High School, Bachelor's, Master's, PhD
    
    -- Salary data from multiple sources
    median_salary DECIMAL(12,2) NOT NULL,
    mean_salary DECIMAL(12,2),
    percentile_25 DECIMAL(12,2),
    percentile_75 DECIMAL(12,2),
    percentile_90 DECIMAL(12,2),
    
    -- Sample and confidence data
    sample_size INTEGER,
    confidence_interval_lower DECIMAL(12,2),
    confidence_interval_upper DECIMAL(12,2),
    
    -- Data source information
    data_source VARCHAR(50) NOT NULL, -- BLS, Census, Indeed, etc.
    source_confidence_score DECIMAL(3,2) DEFAULT 0.0, -- 0.00 to 1.00
    data_freshness_days INTEGER, -- Days since last update
    
    -- Metadata and tracking
    year INTEGER NOT NULL,
    quarter INTEGER, -- Q1, Q2, Q3, Q4
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    cache_key VARCHAR(255), -- Redis cache key for quick lookups
    metadata JSONB, -- Additional source-specific data
    
    -- Indexes for performance
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Composite unique constraint
    UNIQUE(location, occupation, industry, experience_level, education_level, year, quarter, data_source)
);

-- =============================================================================
-- MARKET DATA TABLE
-- =============================================================================

CREATE TABLE market_data (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    location VARCHAR(255) NOT NULL, -- Geographic area
    occupation VARCHAR(255), -- Optional: specific occupation
    industry VARCHAR(255), -- Optional: specific industry
    
    -- Job market indicators
    job_count INTEGER, -- Number of active job postings
    job_growth_rate DECIMAL(5,2), -- Annual growth percentage
    unemployment_rate DECIMAL(5,2), -- Local unemployment rate
    labor_force_participation DECIMAL(5,2), -- Labor force participation rate
    
    -- Economic indicators
    cost_of_living_index DECIMAL(8,2), -- Relative to national average (100)
    housing_cost_index DECIMAL(8,2),
    transportation_cost_index DECIMAL(8,2),
    healthcare_cost_index DECIMAL(8,2),
    
    -- Demand and supply metrics
    demand_score DECIMAL(3,2) DEFAULT 0.0, -- 0.00 to 1.00
    supply_score DECIMAL(3,2) DEFAULT 0.0, -- 0.00 to 1.00
    market_balance_score DECIMAL(3,2) DEFAULT 0.0, -- Demand vs Supply ratio
    
    -- Remote work and flexibility
    remote_work_percentage DECIMAL(5,2), -- % of jobs offering remote work
    hybrid_work_percentage DECIMAL(5,2), -- % of jobs offering hybrid work
    
    -- Data source and quality
    data_source VARCHAR(50) NOT NULL, -- BLS, FRED, Indeed, etc.
    source_confidence_score DECIMAL(3,2) DEFAULT 0.0,
    data_freshness_days INTEGER,
    
    -- Temporal data
    year INTEGER NOT NULL,
    month INTEGER, -- 1-12
    quarter INTEGER, -- 1-4
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    cache_key VARCHAR(255),
    metadata JSONB,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Composite unique constraint
    UNIQUE(location, occupation, industry, year, month, quarter, data_source)
);

-- =============================================================================
-- CONFIDENCE SCORES TABLE
-- =============================================================================

CREATE TABLE confidence_scores (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    data_type VARCHAR(50) NOT NULL, -- 'salary', 'market', 'cost_of_living'
    location VARCHAR(255) NOT NULL,
    occupation VARCHAR(255), -- Optional
    industry VARCHAR(255), -- Optional
    
    -- Confidence scoring components
    sample_size_score DECIMAL(3,2) DEFAULT 0.0, -- Based on sample size
    data_freshness_score DECIMAL(3,2) DEFAULT 0.0, -- Based on data age
    source_reliability_score DECIMAL(3,2) DEFAULT 0.0, -- Based on source reputation
    methodology_score DECIMAL(3,2) DEFAULT 0.0, -- Based on data collection method
    consistency_score DECIMAL(3,2) DEFAULT 0.0, -- Based on cross-source consistency
    
    -- Composite scores
    overall_confidence_score DECIMAL(3,2) DEFAULT 0.0, -- Weighted average
    data_quality_score DECIMAL(3,2) DEFAULT 0.0, -- Overall data quality
    reliability_score DECIMAL(3,2) DEFAULT 0.0, -- How reliable is this data
    
    -- Scoring metadata
    scoring_methodology JSONB, -- Details on how scores were calculated
    contributing_sources JSONB, -- List of data sources used
    last_calculated TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Temporal tracking
    year INTEGER NOT NULL,
    quarter INTEGER,
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    cache_key VARCHAR(255),
    metadata JSONB,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Composite unique constraint
    UNIQUE(data_type, location, occupation, industry, year, quarter)
);

-- =============================================================================
-- SALARY DATA CACHE TRACKING TABLE
-- =============================================================================

CREATE TABLE salary_data_cache (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    cache_key VARCHAR(255) UNIQUE NOT NULL,
    data_type VARCHAR(50) NOT NULL, -- 'salary', 'market', 'confidence'
    
    -- Cache management
    redis_key VARCHAR(255) NOT NULL, -- Actual Redis key
    ttl_seconds INTEGER DEFAULT 86400, -- Time to live in seconds
    cache_hits INTEGER DEFAULT 0, -- Number of cache hits
    cache_misses INTEGER DEFAULT 0, -- Number of cache misses
    last_accessed TIMESTAMP WITH TIME ZONE,
    
    -- Data metadata
    data_size_bytes INTEGER, -- Size of cached data
    compression_ratio DECIMAL(5,2), -- If data is compressed
    cache_strategy VARCHAR(50) DEFAULT 'standard', -- 'standard', 'aggressive', 'conservative'
    
    -- Performance metrics
    average_response_time_ms INTEGER, -- Average time to retrieve from cache
    hit_rate DECIMAL(5,2), -- Hit rate percentage
    
    -- Management
    is_active BOOLEAN DEFAULT true,
    expires_at TIMESTAMP WITH TIME ZONE,
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =============================================================================
-- INDEXES FOR PERFORMANCE
-- =============================================================================

-- Salary benchmarks indexes
CREATE INDEX idx_salary_benchmarks_location ON salary_benchmarks(location);
CREATE INDEX idx_salary_benchmarks_occupation ON salary_benchmarks(occupation);
CREATE INDEX idx_salary_benchmarks_industry ON salary_benchmarks(industry);
CREATE INDEX idx_salary_benchmarks_year ON salary_benchmarks(year);
CREATE INDEX idx_salary_benchmarks_data_source ON salary_benchmarks(data_source);
CREATE INDEX idx_salary_benchmarks_cache_key ON salary_benchmarks(cache_key);
CREATE INDEX idx_salary_benchmarks_last_updated ON salary_benchmarks(last_updated);
CREATE INDEX idx_salary_benchmarks_median_salary ON salary_benchmarks(median_salary);

-- Market data indexes
CREATE INDEX idx_market_data_location ON market_data(location);
CREATE INDEX idx_market_data_occupation ON market_data(occupation);
CREATE INDEX idx_market_data_industry ON market_data(industry);
CREATE INDEX idx_market_data_year ON market_data(year);
CREATE INDEX idx_market_data_data_source ON market_data(data_source);
CREATE INDEX idx_market_data_cache_key ON market_data(cache_key);
CREATE INDEX idx_market_data_last_updated ON market_data(last_updated);
CREATE INDEX idx_market_data_demand_score ON market_data(demand_score);

-- Confidence scores indexes
CREATE INDEX idx_confidence_scores_data_type ON confidence_scores(data_type);
CREATE INDEX idx_confidence_scores_location ON confidence_scores(location);
CREATE INDEX idx_confidence_scores_overall_confidence ON confidence_scores(overall_confidence_score);
CREATE INDEX idx_confidence_scores_cache_key ON confidence_scores(cache_key);
CREATE INDEX idx_confidence_scores_last_updated ON confidence_scores(last_updated);

-- Cache tracking indexes
CREATE INDEX idx_salary_data_cache_cache_key ON salary_data_cache(cache_key);
CREATE INDEX idx_salary_data_cache_data_type ON salary_data_cache(data_type);
CREATE INDEX idx_salary_data_cache_expires_at ON salary_data_cache(expires_at);
CREATE INDEX idx_salary_data_cache_last_accessed ON salary_data_cache(last_accessed);

-- Composite indexes for common queries
CREATE INDEX idx_salary_benchmarks_location_occupation ON salary_benchmarks(location, occupation);
CREATE INDEX idx_salary_benchmarks_location_industry ON salary_benchmarks(location, industry);
CREATE INDEX idx_market_data_location_occupation ON market_data(location, occupation);
CREATE INDEX idx_confidence_scores_location_data_type ON confidence_scores(location, data_type);

-- JSONB indexes for metadata queries
CREATE INDEX idx_salary_benchmarks_metadata ON salary_benchmarks USING GIN (metadata);
CREATE INDEX idx_market_data_metadata ON market_data USING GIN (metadata);
CREATE INDEX idx_confidence_scores_metadata ON confidence_scores USING GIN (metadata);
CREATE INDEX idx_salary_data_cache_metadata ON salary_data_cache USING GIN (metadata);

-- =============================================================================
-- TRIGGERS FOR UPDATED_AT COLUMNS
-- =============================================================================

-- Trigger function for salary_benchmarks
CREATE TRIGGER update_salary_benchmarks_updated_at 
    BEFORE UPDATE ON salary_benchmarks 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Trigger function for market_data
CREATE TRIGGER update_market_data_updated_at 
    BEFORE UPDATE ON market_data 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Trigger function for confidence_scores
CREATE TRIGGER update_confidence_scores_updated_at 
    BEFORE UPDATE ON confidence_scores 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- =============================================================================
-- VIEWS FOR COMMON QUERIES
-- =============================================================================

-- View for comprehensive salary data with confidence scores
CREATE VIEW salary_data_comprehensive AS
SELECT 
    sb.id,
    sb.location,
    sb.occupation,
    sb.industry,
    sb.experience_level,
    sb.education_level,
    sb.median_salary,
    sb.mean_salary,
    sb.percentile_25,
    sb.percentile_75,
    sb.percentile_90,
    sb.sample_size,
    sb.data_source,
    sb.source_confidence_score,
    sb.year,
    sb.quarter,
    sb.last_updated,
    
    -- Market data
    md.job_count,
    md.job_growth_rate,
    md.unemployment_rate,
    md.demand_score,
    md.cost_of_living_index,
    md.remote_work_percentage,
    
    -- Confidence scores
    cs.overall_confidence_score,
    cs.data_quality_score,
    cs.reliability_score,
    
    -- Cache information
    sdc.cache_hits,
    sdc.cache_misses,
    sdc.hit_rate
    
FROM salary_benchmarks sb
LEFT JOIN market_data md ON 
    sb.location = md.location AND 
    sb.occupation = md.occupation AND 
    sb.industry = md.industry AND 
    sb.year = md.year AND 
    COALESCE(sb.quarter, 0) = COALESCE(md.quarter, 0)
LEFT JOIN confidence_scores cs ON 
    sb.location = cs.location AND 
    sb.occupation = cs.occupation AND 
    sb.industry = cs.industry AND 
    cs.data_type = 'salary' AND
    sb.year = cs.year AND 
    COALESCE(sb.quarter, 0) = COALESCE(cs.quarter, 0)
LEFT JOIN salary_data_cache sdc ON 
    sb.cache_key = sdc.cache_key
WHERE sb.is_active = true;

-- View for market insights
CREATE VIEW market_insights AS
SELECT 
    md.location,
    md.occupation,
    md.industry,
    md.year,
    md.quarter,
    md.job_count,
    md.job_growth_rate,
    md.unemployment_rate,
    md.demand_score,
    md.supply_score,
    md.market_balance_score,
    md.cost_of_living_index,
    md.remote_work_percentage,
    md.hybrid_work_percentage,
    md.data_source,
    md.last_updated,
    
    -- Aggregated salary data
    AVG(sb.median_salary) as avg_median_salary,
    COUNT(sb.id) as salary_data_points,
    
    -- Confidence metrics
    AVG(cs.overall_confidence_score) as avg_confidence_score
    
FROM market_data md
LEFT JOIN salary_benchmarks sb ON 
    md.location = sb.location AND 
    md.occupation = sb.occupation AND 
    md.industry = sb.industry AND 
    md.year = sb.year AND 
    COALESCE(md.quarter, 0) = COALESCE(sb.quarter, 0)
LEFT JOIN confidence_scores cs ON 
    md.location = cs.location AND 
    md.occupation = cs.occupation AND 
    md.industry = cs.industry AND 
    cs.data_type = 'market' AND
    md.year = cs.year AND 
    COALESCE(md.quarter, 0) = COALESCE(cs.quarter, 0)
GROUP BY md.id, md.location, md.occupation, md.industry, md.year, md.quarter,
         md.job_count, md.job_growth_rate, md.unemployment_rate, md.demand_score,
         md.supply_score, md.market_balance_score, md.cost_of_living_index,
         md.remote_work_percentage, md.hybrid_work_percentage, md.data_source, md.last_updated;

-- =============================================================================
-- FUNCTIONS FOR DATA MANAGEMENT
-- =============================================================================

-- Function to calculate confidence scores
CREATE OR REPLACE FUNCTION calculate_confidence_score(
    p_sample_size INTEGER,
    p_data_freshness_days INTEGER,
    p_source_reliability DECIMAL(3,2),
    p_methodology_score DECIMAL(3,2),
    p_consistency_score DECIMAL(3,2)
) RETURNS DECIMAL(3,2) AS $$
DECLARE
    sample_size_score DECIMAL(3,2);
    data_freshness_score DECIMAL(3,2);
    overall_score DECIMAL(3,2);
BEGIN
    -- Calculate sample size score (0-1)
    IF p_sample_size IS NULL OR p_sample_size = 0 THEN
        sample_size_score := 0.0;
    ELSIF p_sample_size >= 10000 THEN
        sample_size_score := 1.0;
    ELSIF p_sample_size >= 1000 THEN
        sample_size_score := 0.8;
    ELSIF p_sample_size >= 100 THEN
        sample_size_score := 0.6;
    ELSIF p_sample_size >= 10 THEN
        sample_size_score := 0.4;
    ELSE
        sample_size_score := 0.2;
    END IF;
    
    -- Calculate data freshness score (0-1)
    IF p_data_freshness_days IS NULL THEN
        data_freshness_score := 0.0;
    ELSIF p_data_freshness_days <= 30 THEN
        data_freshness_score := 1.0;
    ELSIF p_data_freshness_days <= 90 THEN
        data_freshness_score := 0.8;
    ELSIF p_data_freshness_days <= 365 THEN
        data_freshness_score := 0.6;
    ELSIF p_data_freshness_days <= 730 THEN
        data_freshness_score := 0.4;
    ELSE
        data_freshness_score := 0.2;
    END IF;
    
    -- Calculate weighted overall score
    overall_score := (
        sample_size_score * 0.25 +
        data_freshness_score * 0.25 +
        COALESCE(p_source_reliability, 0.5) * 0.2 +
        COALESCE(p_methodology_score, 0.5) * 0.2 +
        COALESCE(p_consistency_score, 0.5) * 0.1
    );
    
    RETURN LEAST(GREATEST(overall_score, 0.0), 1.0);
END;
$$ LANGUAGE plpgsql;

-- Function to generate cache keys
CREATE OR REPLACE FUNCTION generate_cache_key(
    p_data_type VARCHAR(50),
    p_location VARCHAR(255),
    p_occupation VARCHAR(255) DEFAULT NULL,
    p_industry VARCHAR(255) DEFAULT NULL,
    p_year INTEGER DEFAULT NULL,
    p_quarter INTEGER DEFAULT NULL
) RETURNS VARCHAR(255) AS $$
DECLARE
    cache_key VARCHAR(255);
BEGIN
    cache_key := p_data_type || ':' || 
                 LOWER(REPLACE(p_location, ' ', '_')) || ':' ||
                 COALESCE(LOWER(REPLACE(p_occupation, ' ', '_')), 'all') || ':' ||
                 COALESCE(LOWER(REPLACE(p_industry, ' ', '_')), 'all') || ':' ||
                 COALESCE(p_year::VARCHAR, 'all') || ':' ||
                 COALESCE(p_quarter::VARCHAR, 'all');
    
    RETURN cache_key;
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- MIGRATION COMPLETE
-- =============================================================================

-- Log the migration
INSERT INTO system_alerts (
    alert_type,
    severity,
    title,
    message,
    metadata
) VALUES (
    'system_info',
    'info',
    'Salary Data Tables Migration Complete',
    'Successfully added salary_benchmarks, market_data, confidence_scores, and salary_data_cache tables to the database schema.',
    '{"migration_version": "001", "tables_added": ["salary_benchmarks", "market_data", "confidence_scores", "salary_data_cache"], "indexes_created": 25, "views_created": 2, "functions_created": 2}'
); 