-- =============================================================================
-- AI Job Impact Calculator - PostgreSQL Database Schema
-- =============================================================================
-- 
-- This schema creates tables for the AI Job Impact Calculator lead magnet
-- that assesses how AI might affect a user's job and career prospects.
--
-- Features:
-- - UUID primary keys for security and scalability
-- - JSONB for flexible data storage of tasks and concerns
-- - Proper foreign key relationships
-- - Timestamps with timezone awareness
-- - Comprehensive constraints and indexes
-- - Conversion tracking for lead generation
--
-- Author: MINGUS Development Team
-- Date: January 2025
-- Version: 1.0
-- =============================================================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- =============================================================================
-- AI JOB ASSESSMENT TABLES
-- =============================================================================

-- Main table for AI job impact assessments
CREATE TABLE ai_job_assessments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL, -- Nullable for anonymous assessments
    job_title VARCHAR(255) NOT NULL,
    industry VARCHAR(100) NOT NULL,
    experience_level VARCHAR(20) NOT NULL CHECK (experience_level IN ('entry', 'mid', 'senior', 'executive')),
    tasks_array JSONB NOT NULL DEFAULT '[]', -- Selected daily tasks
    remote_work_frequency VARCHAR(20) NOT NULL CHECK (remote_work_frequency IN ('never', 'rarely', 'sometimes', 'often', 'always')),
    ai_usage_frequency VARCHAR(20) NOT NULL CHECK (ai_usage_frequency IN ('never', 'rarely', 'sometimes', 'often', 'always')),
    team_size VARCHAR(20) NOT NULL CHECK (team_size IN ('1-5', '6-10', '11-25', '26-50', '50+')),
    tech_skills_level VARCHAR(20) NOT NULL CHECK (tech_skills_level IN ('basic', 'intermediate', 'advanced', 'expert')),
    concerns_array JSONB NOT NULL DEFAULT '[]', -- AI-related concerns
    first_name VARCHAR(100) NOT NULL,
    email VARCHAR(255) NOT NULL,
    location VARCHAR(100),
    automation_score INTEGER NOT NULL CHECK (automation_score >= 0 AND automation_score <= 100),
    augmentation_score INTEGER NOT NULL CHECK (augmentation_score >= 0 AND augmentation_score <= 100),
    overall_risk_level VARCHAR(20) NOT NULL CHECK (overall_risk_level IN ('low', 'medium', 'high')),
    assessment_type VARCHAR(50) DEFAULT 'ai_job_risk',
    completed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Additional fields for lead generation
    lead_source VARCHAR(100) DEFAULT 'ai_job_calculator',
    utm_source VARCHAR(100),
    utm_medium VARCHAR(100),
    utm_campaign VARCHAR(100),
    utm_term VARCHAR(100),
    utm_content VARCHAR(100),
    
    -- Email and communication preferences
    email_verified BOOLEAN DEFAULT FALSE,
    email_verification_token VARCHAR(255),
    email_verification_expires TIMESTAMP WITH TIME ZONE,
    communication_preferences JSONB DEFAULT '{
        "marketing_emails": true,
        "career_insights": true,
        "ai_updates": true,
        "frequency": "weekly"
    }',
    
    -- Assessment metadata
    assessment_duration_seconds INTEGER,
    questions_answered INTEGER DEFAULT 0,
    total_questions INTEGER DEFAULT 15,
    completion_percentage DECIMAL(5,2) DEFAULT 0,
    
    -- Risk analysis details
    risk_factors JSONB DEFAULT '{}',
    mitigation_strategies JSONB DEFAULT '[]',
    recommended_skills JSONB DEFAULT '[]',
    career_advice JSONB DEFAULT '{}',
    
    -- Timestamps
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Static reference data for AI job risk calculations
CREATE TABLE ai_job_risk_data (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_keyword VARCHAR(100) NOT NULL UNIQUE,
    automation_base_score INTEGER NOT NULL CHECK (automation_base_score >= 0 AND automation_base_score <= 100),
    augmentation_base_score INTEGER NOT NULL CHECK (augmentation_base_score >= 0 AND augmentation_base_score <= 100),
    risk_category VARCHAR(20) NOT NULL CHECK (risk_category IN ('low', 'medium', 'high')),
    industry_modifiers JSONB NOT NULL DEFAULT '{}', -- Industry-specific risk adjustments
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Conversion tracking for AI calculator assessments
CREATE TABLE ai_calculator_conversions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    assessment_id UUID NOT NULL REFERENCES ai_job_assessments(id) ON DELETE CASCADE,
    conversion_type VARCHAR(50) NOT NULL CHECK (conversion_type IN ('email_signup', 'paid_upgrade', 'consultation_booking', 'course_enrollment')),
    conversion_value DECIMAL(10,2) DEFAULT 0,
    converted_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Conversion details
    conversion_source VARCHAR(100),
    conversion_medium VARCHAR(100),
    conversion_campaign VARCHAR(100),
    conversion_revenue DECIMAL(10,2) DEFAULT 0,
    
    -- User journey tracking
    touchpoints_before_conversion INTEGER DEFAULT 0,
    days_to_conversion INTEGER DEFAULT 0,
    conversion_funnel_stage VARCHAR(50),
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =============================================================================
-- INDEXES FOR PERFORMANCE
-- =============================================================================

-- Indexes for ai_job_assessments table
CREATE INDEX idx_ai_job_assessments_email ON ai_job_assessments(email);
CREATE INDEX idx_ai_job_assessments_job_title ON ai_job_assessments(job_title);
CREATE INDEX idx_ai_job_assessments_industry ON ai_job_assessments(industry);
CREATE INDEX idx_ai_job_assessments_completed_at ON ai_job_assessments(completed_at);
CREATE INDEX idx_ai_job_assessments_risk_level ON ai_job_assessments(overall_risk_level);
CREATE INDEX idx_ai_job_assessments_automation_score ON ai_job_assessments(automation_score);
CREATE INDEX idx_ai_job_assessments_augmentation_score ON ai_job_assessments(augmentation_score);
CREATE INDEX idx_ai_job_assessments_user_id ON ai_job_assessments(user_id);
CREATE INDEX idx_ai_job_assessments_lead_source ON ai_job_assessments(lead_source);
CREATE INDEX idx_ai_job_assessments_created_at ON ai_job_assessments(created_at);

-- Indexes for ai_job_risk_data table
CREATE INDEX idx_ai_job_risk_data_job_keyword ON ai_job_risk_data(job_keyword);
CREATE INDEX idx_ai_job_risk_data_risk_category ON ai_job_risk_data(risk_category);
CREATE INDEX idx_ai_job_risk_data_automation_score ON ai_job_risk_data(automation_base_score);
CREATE INDEX idx_ai_job_risk_data_augmentation_score ON ai_job_risk_data(augmentation_base_score);

-- Indexes for ai_calculator_conversions table
CREATE INDEX idx_ai_calculator_conversions_assessment_id ON ai_calculator_conversions(assessment_id);
CREATE INDEX idx_ai_calculator_conversions_conversion_type ON ai_calculator_conversions(conversion_type);
CREATE INDEX idx_ai_calculator_conversions_converted_at ON ai_calculator_conversions(converted_at);
CREATE INDEX idx_ai_calculator_conversions_conversion_value ON ai_calculator_conversions(conversion_value);

-- =============================================================================
-- SAMPLE DATA FOR AI JOB RISK REFERENCE
-- =============================================================================

-- Insert sample job risk data
INSERT INTO ai_job_risk_data (job_keyword, automation_base_score, augmentation_base_score, risk_category, industry_modifiers) VALUES
-- High Automation Risk Jobs
('data_entry', 85, 15, 'high', '{"finance": 90, "healthcare": 80, "retail": 85}'),
('bookkeeping', 75, 25, 'high', '{"finance": 80, "accounting": 75, "small_business": 70}'),
('customer_service', 70, 30, 'high', '{"retail": 75, "telecommunications": 70, "banking": 65}'),
('telemarketing', 80, 20, 'high', '{"sales": 85, "marketing": 80, "insurance": 75}'),
('assembly_line', 90, 10, 'high', '{"manufacturing": 95, "automotive": 90, "electronics": 85}'),

-- Medium Automation Risk Jobs
('content_writing', 45, 55, 'medium', '{"marketing": 40, "publishing": 50, "advertising": 45}'),
('graphic_design', 40, 60, 'medium', '{"design": 35, "marketing": 45, "publishing": 40}'),
('project_management', 30, 70, 'medium', '{"technology": 25, "construction": 35, "consulting": 30}'),
('sales_representative', 35, 65, 'medium', '{"retail": 40, "technology": 30, "pharmaceuticals": 35}'),
('human_resources', 50, 50, 'medium', '{"corporate": 45, "healthcare": 55, "technology": 50}'),

-- Low Automation Risk Jobs
('software_engineer', 20, 80, 'low', '{"technology": 15, "finance": 25, "healthcare": 20}'),
('data_scientist', 15, 85, 'low', '{"technology": 10, "finance": 20, "healthcare": 15}'),
('product_manager', 25, 75, 'low', '{"technology": 20, "ecommerce": 30, "finance": 25}'),
('user_experience_designer', 20, 80, 'low', '{"technology": 15, "design": 20, "ecommerce": 25}'),
('business_analyst', 30, 70, 'low', '{"consulting": 25, "finance": 35, "technology": 30}'),
('marketing_manager', 35, 65, 'low', '{"marketing": 30, "technology": 40, "retail": 35}'),
('financial_advisor', 25, 75, 'low', '{"finance": 20, "insurance": 30, "wealth_management": 25}'),
('healthcare_provider', 15, 85, 'low', '{"healthcare": 10, "pharmaceuticals": 20, "research": 15}'),
('legal_professional', 20, 80, 'low', '{"legal": 15, "corporate": 25, "government": 20}'),
('research_scientist', 10, 90, 'low', '{"research": 5, "academia": 15, "pharmaceuticals": 10}');

-- =============================================================================
-- TRIGGERS AND FUNCTIONS
-- =============================================================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers to automatically update updated_at
CREATE TRIGGER update_ai_job_assessments_updated_at 
    BEFORE UPDATE ON ai_job_assessments 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_ai_job_risk_data_updated_at 
    BEFORE UPDATE ON ai_job_risk_data 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Function to calculate completion percentage
CREATE OR REPLACE FUNCTION calculate_completion_percentage()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.questions_answered > 0 AND NEW.total_questions > 0 THEN
        NEW.completion_percentage = (NEW.questions_answered::DECIMAL / NEW.total_questions::DECIMAL) * 100;
    END IF;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger to calculate completion percentage
CREATE TRIGGER calculate_ai_assessment_completion 
    BEFORE INSERT OR UPDATE ON ai_job_assessments 
    FOR EACH ROW EXECUTE FUNCTION calculate_completion_percentage();

-- =============================================================================
-- VIEWS FOR ANALYTICS
-- =============================================================================

-- View for AI job risk analytics
CREATE VIEW ai_job_risk_analytics AS
SELECT 
    industry,
    overall_risk_level,
    COUNT(*) as assessment_count,
    AVG(automation_score) as avg_automation_score,
    AVG(augmentation_score) as avg_augmentation_score,
    AVG(completion_percentage) as avg_completion_percentage,
    COUNT(CASE WHEN email_verified = true THEN 1 END) as verified_emails,
    COUNT(CASE WHEN converted_at IS NOT NULL THEN 1 END) as conversions
FROM ai_job_assessments
GROUP BY industry, overall_risk_level
ORDER BY industry, overall_risk_level;

-- View for conversion funnel analysis
CREATE VIEW ai_calculator_conversion_funnel AS
SELECT 
    conversion_type,
    COUNT(*) as conversion_count,
    AVG(conversion_value) as avg_conversion_value,
    SUM(conversion_value) as total_conversion_value,
    AVG(days_to_conversion) as avg_days_to_conversion
FROM ai_calculator_conversions
GROUP BY conversion_type
ORDER BY total_conversion_value DESC;

-- =============================================================================
-- COMMENTS
-- =============================================================================

COMMENT ON TABLE ai_job_assessments IS 'Stores AI job impact assessment results and user information';
COMMENT ON TABLE ai_job_risk_data IS 'Reference data for job automation and augmentation risk calculations';
COMMENT ON TABLE ai_calculator_conversions IS 'Tracks conversions from AI job impact calculator assessments';

COMMENT ON COLUMN ai_job_assessments.tasks_array IS 'JSON array of selected daily tasks that could be automated';
COMMENT ON COLUMN ai_job_assessments.concerns_array IS 'JSON array of AI-related concerns expressed by user';
COMMENT ON COLUMN ai_job_assessments.risk_factors IS 'JSON object containing identified risk factors for the job';
COMMENT ON COLUMN ai_job_assessments.mitigation_strategies IS 'JSON array of recommended mitigation strategies';
COMMENT ON COLUMN ai_job_assessments.recommended_skills IS 'JSON array of skills recommended to stay competitive';
COMMENT ON COLUMN ai_job_assessments.career_advice IS 'JSON object containing personalized career advice';

COMMENT ON COLUMN ai_job_risk_data.industry_modifiers IS 'JSON object with industry-specific risk adjustments';
COMMENT ON COLUMN ai_calculator_conversions.conversion_value IS 'Monetary value of the conversion event';
