-- =====================================================
-- MIGRATION: Create Assessment System Tables
-- =====================================================
-- Description: Comprehensive assessment functionality for AI job risk, relationship impact, tax impact, and income comparison assessments
-- Revision: 016_create_assessment_system_tables
-- Date: 2025-01-XX
-- Author: MINGUS Development Team

-- =====================================================
-- ENABLE REQUIRED EXTENSIONS
-- =====================================================

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =====================================================
-- CREATE ENUM TYPES
-- =====================================================

-- Assessment type enum
DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'assessment_type') THEN
        CREATE TYPE assessment_type AS ENUM (
            'ai_job_risk',
            'relationship_impact', 
            'tax_impact',
            'income_comparison'
        );
    END IF;
END $$;

-- Risk level enum
DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'risk_level_type') THEN
        CREATE TYPE risk_level_type AS ENUM (
            'low',
            'medium',
            'high',
            'critical'
        );
    END IF;
END $$;

-- =====================================================
-- CREATE ASSESSMENTS TABLE
-- =====================================================

-- Core assessments table - stores assessment templates and configurations
CREATE TABLE IF NOT EXISTS assessments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    type assessment_type NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    questions_json JSONB NOT NULL DEFAULT '[]',
    scoring_config JSONB NOT NULL DEFAULT '{}',
    version VARCHAR(20) DEFAULT '1.0',
    estimated_duration_minutes INTEGER DEFAULT 10,
    is_active BOOLEAN DEFAULT true,
    requires_authentication BOOLEAN DEFAULT false,
    allow_anonymous BOOLEAN DEFAULT true,
    max_attempts_per_user INTEGER DEFAULT 3,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT valid_questions_json CHECK (jsonb_typeof(questions_json) = 'array'),
    CONSTRAINT valid_scoring_config CHECK (jsonb_typeof(scoring_config) = 'object'),
    CONSTRAINT valid_duration CHECK (estimated_duration_minutes > 0 AND estimated_duration_minutes <= 120),
    CONSTRAINT valid_max_attempts CHECK (max_attempts_per_user > 0 AND max_attempts_per_user <= 10)
);

-- =====================================================
-- CREATE USER_ASSESSMENTS TABLE
-- =====================================================

-- User assessment responses table - stores individual assessment attempts
CREATE TABLE IF NOT EXISTS user_assessments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    assessment_id UUID NOT NULL REFERENCES assessments(id) ON DELETE CASCADE,
    responses_json JSONB NOT NULL DEFAULT '{}',
    score INTEGER CHECK (score >= 0 AND score <= 100),
    risk_level risk_level_type,
    completed_at TIMESTAMP WITH TIME ZONE,
    
    -- Anonymous user fields
    email VARCHAR(255),
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    location VARCHAR(255),
    job_title VARCHAR(255),
    industry VARCHAR(255),
    
    -- Metadata
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    time_spent_seconds INTEGER DEFAULT 0,
    ip_address INET,
    user_agent TEXT,
    session_id UUID,
    assessment_version VARCHAR(20),
    
    -- Status tracking
    is_complete BOOLEAN DEFAULT false,
    is_valid BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT valid_responses_json CHECK (jsonb_typeof(responses_json) = 'object'),
    CONSTRAINT valid_anonymous_user CHECK (
        (user_id IS NOT NULL) OR 
        (email IS NOT NULL AND first_name IS NOT NULL)
    ),
    CONSTRAINT valid_completion CHECK (
        (is_complete = true AND completed_at IS NOT NULL) OR
        (is_complete = false AND completed_at IS NULL)
    ),
    CONSTRAINT valid_time_spent CHECK (time_spent_seconds >= 0),
    CONSTRAINT valid_score_range CHECK (score IS NULL OR (score >= 0 AND score <= 100))
);

-- =====================================================
-- CREATE ASSESSMENT_RESULTS TABLE
-- =====================================================

-- Assessment results table - stores detailed analysis and recommendations
CREATE TABLE IF NOT EXISTS assessment_results (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_assessment_id UUID NOT NULL REFERENCES user_assessments(id) ON DELETE CASCADE,
    
    -- Analysis results
    insights_json JSONB NOT NULL DEFAULT '{}',
    recommendations_json JSONB NOT NULL DEFAULT '{}',
    
    -- AI-specific scores (for AI job risk assessment)
    automation_score INTEGER CHECK (automation_score >= 0 AND automation_score <= 100),
    augmentation_score INTEGER CHECK (augmentation_score >= 0 AND augmentation_score <= 100),
    
    -- Financial impact calculations
    cost_projections JSONB DEFAULT '{}',
    risk_factors JSONB DEFAULT '[]',
    mitigation_strategies JSONB DEFAULT '[]',
    
    -- Relationship impact analysis (for relationship impact assessment)
    relationship_stress_score INTEGER CHECK (relationship_stress_score >= 0 AND relationship_stress_score <= 100),
    financial_harmony_score INTEGER CHECK (financial_harmony_score >= 0 AND financial_harmony_score <= 100),
    
    -- Tax impact analysis (for tax impact assessment)
    tax_efficiency_score INTEGER CHECK (tax_efficiency_score >= 0 AND tax_efficiency_score <= 100),
    potential_savings DECIMAL(12,2),
    tax_optimization_opportunities JSONB DEFAULT '[]',
    
    -- Income comparison analysis (for income comparison assessment)
    market_position_score INTEGER CHECK (market_position_score >= 0 AND market_position_score <= 100),
    salary_benchmark_data JSONB DEFAULT '{}',
    negotiation_leverage_points JSONB DEFAULT '[]',
    
    -- Metadata
    analysis_version VARCHAR(20) DEFAULT '1.0',
    processing_time_ms INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT valid_insights_json CHECK (jsonb_typeof(insights_json) = 'object'),
    CONSTRAINT valid_recommendations_json CHECK (jsonb_typeof(recommendations_json) = 'object'),
    CONSTRAINT valid_cost_projections CHECK (jsonb_typeof(cost_projections) = 'object'),
    CONSTRAINT valid_risk_factors CHECK (jsonb_typeof(risk_factors) = 'array'),
    CONSTRAINT valid_mitigation_strategies CHECK (jsonb_typeof(mitigation_strategies) = 'array'),
    CONSTRAINT valid_tax_optimization CHECK (jsonb_typeof(tax_optimization_opportunities) = 'array'),
    CONSTRAINT valid_salary_benchmark CHECK (jsonb_typeof(salary_benchmark_data) = 'object'),
    CONSTRAINT valid_negotiation_points CHECK (jsonb_typeof(negotiation_leverage_points) = 'array'),
    CONSTRAINT valid_potential_savings CHECK (potential_savings IS NULL OR potential_savings >= 0),
    CONSTRAINT valid_processing_time CHECK (processing_time_ms IS NULL OR processing_time_ms >= 0)
);

-- =====================================================
-- CREATE INDEXES FOR PERFORMANCE
-- =====================================================

-- Assessments table indexes
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_assessments_type ON assessments(type);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_assessments_active ON assessments(is_active) WHERE is_active = true;
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_assessments_version ON assessments(version);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_assessments_created_at ON assessments(created_at);

-- User assessments table indexes
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_user_assessments_user_id ON user_assessments(user_id);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_user_assessments_assessment_id ON user_assessments(assessment_id);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_user_assessments_email ON user_assessments(email);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_user_assessments_completed_at ON user_assessments(completed_at);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_user_assessments_risk_level ON user_assessments(risk_level);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_user_assessments_score ON user_assessments(score);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_user_assessments_session_id ON user_assessments(session_id);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_user_assessments_started_at ON user_assessments(started_at);

-- Composite indexes for common queries
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_user_assessments_user_complete ON user_assessments(user_id, is_complete) WHERE user_id IS NOT NULL;
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_user_assessments_assessment_complete ON user_assessments(assessment_id, is_complete);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_user_assessments_email_complete ON user_assessments(email, is_complete) WHERE email IS NOT NULL;

-- Assessment results table indexes
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_assessment_results_user_assessment_id ON assessment_results(user_assessment_id);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_assessment_results_automation_score ON assessment_results(automation_score);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_assessment_results_augmentation_score ON assessment_results(augmentation_score);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_assessment_results_relationship_stress ON assessment_results(relationship_stress_score);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_assessment_results_financial_harmony ON assessment_results(financial_harmony_score);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_assessment_results_tax_efficiency ON assessment_results(tax_efficiency_score);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_assessment_results_market_position ON assessment_results(market_position_score);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_assessment_results_created_at ON assessment_results(created_at);

-- =====================================================
-- CREATE TRIGGERS FOR UPDATED_AT TIMESTAMPS
-- =====================================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers for updated_at columns
CREATE TRIGGER update_assessments_updated_at 
    BEFORE UPDATE ON assessments 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_user_assessments_updated_at 
    BEFORE UPDATE ON user_assessments 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_assessment_results_updated_at 
    BEFORE UPDATE ON assessment_results 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- =====================================================
-- INSERT DEFAULT ASSESSMENT TEMPLATES
-- =====================================================

-- AI Job Risk Assessment Template
INSERT INTO assessments (type, title, description, questions_json, scoring_config, version, estimated_duration_minutes) 
VALUES (
    'ai_job_risk',
    'AI Job Risk Assessment',
    'Evaluate your job''s vulnerability to AI automation and get personalized recommendations for career resilience.',
    '[
        {
            "id": "ai_1",
            "question": "How much of your work involves repetitive, rule-based tasks?",
            "type": "scale",
            "options": [
                {"value": 1, "label": "Very little (0-20%)"},
                {"value": 2, "label": "Some (21-40%)"},
                {"value": 3, "label": "Moderate (41-60%)"},
                {"value": 4, "label": "Significant (61-80%)"},
                {"value": 5, "label": "Mostly (81-100%)"}
            ],
            "weight": 0.25
        },
        {
            "id": "ai_2", 
            "question": "How much does your role require creative problem-solving and innovation?",
            "type": "scale",
            "options": [
                {"value": 1, "label": "Very little"},
                {"value": 2, "label": "Some"},
                {"value": 3, "label": "Moderate"},
                {"value": 4, "label": "Significant"},
                {"value": 5, "label": "Extensive"}
            ],
            "weight": 0.20
        },
        {
            "id": "ai_3",
            "question": "How much human interaction and emotional intelligence does your job require?",
            "type": "scale", 
            "options": [
                {"value": 1, "label": "Minimal"},
                {"value": 2, "label": "Some"},
                {"value": 3, "label": "Moderate"},
                {"value": 4, "label": "Significant"},
                {"value": 5, "label": "Extensive"}
            ],
            "weight": 0.20
        },
        {
            "id": "ai_4",
            "question": "How quickly is AI/automation being adopted in your industry?",
            "type": "scale",
            "options": [
                {"value": 1, "label": "Very slow"},
                {"value": 2, "label": "Slow"},
                {"value": 3, "label": "Moderate"},
                {"value": 4, "label": "Fast"},
                {"value": 5, "label": "Very fast"}
            ],
            "weight": 0.15
        },
        {
            "id": "ai_5",
            "question": "How much specialized knowledge or expertise does your role require?",
            "type": "scale",
            "options": [
                {"value": 1, "label": "Basic"},
                {"value": 2, "label": "Some"},
                {"value": 3, "label": "Moderate"},
                {"value": 4, "label": "High"},
                {"value": 5, "label": "Expert"}
            ],
            "weight": 0.20
        }
    ]'::jsonb,
    '{
        "automation_risk_formula": "SUM(question_value * weight) * 20",
        "augmentation_potential_formula": "100 - automation_risk_score",
        "risk_thresholds": {
            "low": {"max": 30, "label": "Low Risk"},
            "medium": {"min": 31, "max": 60, "label": "Medium Risk"},
            "high": {"min": 61, "max": 80, "label": "High Risk"},
            "critical": {"min": 81, "max": 100, "label": "Critical Risk"}
        }
    }'::jsonb,
    '1.0',
    5
) ON CONFLICT DO NOTHING;

-- Relationship Impact Assessment Template
INSERT INTO assessments (type, title, description, questions_json, scoring_config, version, estimated_duration_minutes)
VALUES (
    'relationship_impact',
    'Relationship & Money Impact Assessment',
    'Understand how your relationships affect your financial decisions and get strategies for financial harmony.',
    '[
        {
            "id": "rel_1",
            "question": "How often do you make financial decisions based on your partner''s or family''s wants?",
            "type": "scale",
            "options": [
                {"value": 1, "label": "Never"},
                {"value": 2, "label": "Rarely"},
                {"value": 3, "label": "Sometimes"},
                {"value": 4, "label": "Often"},
                {"value": 5, "label": "Always"}
            ],
            "weight": 0.20
        },
        {
            "id": "rel_2",
            "question": "How much stress do financial discussions cause in your relationships?",
            "type": "scale",
            "options": [
                {"value": 1, "label": "No stress"},
                {"value": 2, "label": "Minimal"},
                {"value": 3, "label": "Moderate"},
                {"value": 4, "label": "High"},
                {"value": 5, "label": "Extreme"}
            ],
            "weight": 0.25
        },
        {
            "id": "rel_3",
            "question": "How often do you spend money to avoid relationship conflicts?",
            "type": "scale",
            "options": [
                {"value": 1, "label": "Never"},
                {"value": 2, "label": "Rarely"},
                {"value": 3, "label": "Sometimes"},
                {"value": 4, "label": "Often"},
                {"value": 5, "label": "Always"}
            ],
            "weight": 0.20
        },
        {
            "id": "rel_4",
            "question": "How well do you and your partner/family communicate about money?",
            "type": "scale",
            "options": [
                {"value": 5, "label": "Excellent"},
                {"value": 4, "label": "Good"},
                {"value": 3, "label": "Fair"},
                {"value": 2, "label": "Poor"},
                {"value": 1, "label": "Very poor"}
            ],
            "weight": 0.20
        },
        {
            "id": "rel_5",
            "question": "How much do your emotions influence your spending decisions?",
            "type": "scale",
            "options": [
                {"value": 1, "label": "Not at all"},
                {"value": 2, "label": "Minimally"},
                {"value": 3, "label": "Moderately"},
                {"value": 4, "label": "Significantly"},
                {"value": 5, "label": "Completely"}
            ],
            "weight": 0.15
        }
    ]'::jsonb,
    '{
        "relationship_stress_formula": "SUM(question_value * weight) * 20",
        "financial_harmony_formula": "100 - relationship_stress_score",
        "stress_thresholds": {
            "low": {"max": 30, "label": "Low Stress"},
            "medium": {"min": 31, "max": 60, "label": "Medium Stress"},
            "high": {"min": 61, "max": 80, "label": "High Stress"},
            "critical": {"min": 81, "max": 100, "label": "Critical Stress"}
        }
    }'::jsonb,
    '1.0',
    5
) ON CONFLICT DO NOTHING;

-- Tax Impact Assessment Template
INSERT INTO assessments (type, title, description, questions_json, scoring_config, version, estimated_duration_minutes)
VALUES (
    'tax_impact',
    'Tax Efficiency Assessment',
    'Evaluate your current tax situation and discover opportunities for optimization and savings.',
    '[
        {
            "id": "tax_1",
            "question": "How much do you currently contribute to tax-advantaged accounts (401k, IRA, HSA)?",
            "type": "scale",
            "options": [
                {"value": 1, "label": "Nothing"},
                {"value": 2, "label": "Less than 5% of income"},
                {"value": 3, "label": "5-10% of income"},
                {"value": 4, "label": "10-15% of income"},
                {"value": 5, "label": "More than 15% of income"}
            ],
            "weight": 0.25
        },
        {
            "id": "tax_2",
            "question": "How familiar are you with tax deductions and credits available to you?",
            "type": "scale",
            "options": [
                {"value": 1, "label": "Not familiar at all"},
                {"value": 2, "label": "Somewhat familiar"},
                {"value": 3, "label": "Moderately familiar"},
                {"value": 4, "label": "Very familiar"},
                {"value": 5, "label": "Expert level"}
            ],
            "weight": 0.20
        },
        {
            "id": "tax_3",
            "question": "Do you have a side business or freelance income?",
            "type": "scale",
            "options": [
                {"value": 1, "label": "No"},
                {"value": 2, "label": "Occasional"},
                {"value": 3, "label": "Regular side income"},
                {"value": 4, "label": "Significant side business"},
                {"value": 5, "label": "Multiple income streams"}
            ],
            "weight": 0.20
        },
        {
            "id": "tax_4",
            "question": "How much do you spend on work-related expenses that might be deductible?",
            "type": "scale",
            "options": [
                {"value": 1, "label": "Nothing"},
                {"value": 2, "label": "Less than $1,000/year"},
                {"value": 3, "label": "$1,000-$5,000/year"},
                {"value": 4, "label": "$5,000-$10,000/year"},
                {"value": 5, "label": "More than $10,000/year"}
            ],
            "weight": 0.20
        },
        {
            "id": "tax_5",
            "question": "How often do you review and optimize your tax strategy?",
            "type": "scale",
            "options": [
                {"value": 1, "label": "Never"},
                {"value": 2, "label": "Only at tax time"},
                {"value": 3, "label": "Quarterly"},
                {"value": 4, "label": "Monthly"},
                {"value": 5, "label": "Continuously"}
            ],
            "weight": 0.15
        }
    ]'::jsonb,
    '{
        "tax_efficiency_formula": "SUM(question_value * weight) * 20",
        "potential_savings_formula": "(100 - tax_efficiency_score) * 0.01 * annual_income",
        "efficiency_thresholds": {
            "low": {"max": 30, "label": "Low Efficiency"},
            "medium": {"min": 31, "max": 60, "label": "Medium Efficiency"},
            "high": {"min": 61, "max": 80, "label": "High Efficiency"},
            "excellent": {"min": 81, "max": 100, "label": "Excellent Efficiency"}
        }
    }'::jsonb,
    '1.0',
    5
) ON CONFLICT DO NOTHING;

-- Income Comparison Assessment Template
INSERT INTO assessments (type, title, description, questions_json, scoring_config, version, estimated_duration_minutes)
VALUES (
    'income_comparison',
    'Income & Market Position Assessment',
    'Compare your compensation to market standards and identify opportunities for salary growth.',
    '[
        {
            "id": "income_1",
            "question": "How long have you been in your current role?",
            "type": "scale",
            "options": [
                {"value": 5, "label": "Less than 1 year"},
                {"value": 4, "label": "1-2 years"},
                {"value": 3, "label": "3-5 years"},
                {"value": 2, "label": "6-10 years"},
                {"value": 1, "label": "More than 10 years"}
            ],
            "weight": 0.20
        },
        {
            "id": "income_2",
            "question": "How much have you grown your skills and responsibilities in the past year?",
            "type": "scale",
            "options": [
                {"value": 1, "label": "No growth"},
                {"value": 2, "label": "Minimal growth"},
                {"value": 3, "label": "Moderate growth"},
                {"value": 4, "label": "Significant growth"},
                {"value": 5, "label": "Exceptional growth"}
            ],
            "weight": 0.25
        },
        {
            "id": "income_3",
            "question": "How competitive is your current salary compared to similar roles in your area?",
            "type": "scale",
            "options": [
                {"value": 1, "label": "Below market"},
                {"value": 2, "label": "Slightly below"},
                {"value": 3, "label": "At market"},
                {"value": 4, "label": "Above market"},
                {"value": 5, "label": "Well above market"}
            ],
            "weight": 0.25
        },
        {
            "id": "income_4",
            "question": "How confident are you in negotiating your compensation?",
            "type": "scale",
            "options": [
                {"value": 1, "label": "Not confident"},
                {"value": 2, "label": "Somewhat confident"},
                {"value": 3, "label": "Moderately confident"},
                {"value": 4, "label": "Very confident"},
                {"value": 5, "label": "Extremely confident"}
            ],
            "weight": 0.15
        },
        {
            "id": "income_5",
            "question": "How much do you know about salary ranges for your role and experience level?",
            "type": "scale",
            "options": [
                {"value": 1, "label": "Very little"},
                {"value": 2, "label": "Some knowledge"},
                {"value": 3, "label": "Good knowledge"},
                {"value": 4, "label": "Very knowledgeable"},
                {"value": 5, "label": "Expert knowledge"}
            ],
            "weight": 0.15
        }
    ]'::jsonb,
    '{
        "market_position_formula": "SUM(question_value * weight) * 20",
        "negotiation_leverage_formula": "market_position_score * 0.8 + confidence_score * 0.2",
        "position_thresholds": {
            "low": {"max": 30, "label": "Low Position"},
            "medium": {"min": 31, "max": 60, "label": "Medium Position"},
            "high": {"min": 61, "max": 80, "label": "High Position"},
            "excellent": {"min": 81, "max": 100, "label": "Excellent Position"}
        }
    }'::jsonb,
    '1.0',
    5
) ON CONFLICT DO NOTHING;

-- =====================================================
-- CREATE VIEWS FOR COMMON QUERIES
-- =====================================================

-- View for assessment completion statistics
CREATE OR REPLACE VIEW assessment_completion_stats AS
SELECT 
    a.type,
    a.title,
    COUNT(ua.id) as total_attempts,
    COUNT(CASE WHEN ua.is_complete = true THEN 1 END) as completed_attempts,
    ROUND(
        COUNT(CASE WHEN ua.is_complete = true THEN 1 END) * 100.0 / COUNT(ua.id), 
        2
    ) as completion_rate,
    AVG(ua.score) as average_score,
    AVG(ua.time_spent_seconds) as average_time_seconds,
    COUNT(CASE WHEN ua.risk_level = 'low' THEN 1 END) as low_risk_count,
    COUNT(CASE WHEN ua.risk_level = 'medium' THEN 1 END) as medium_risk_count,
    COUNT(CASE WHEN ua.risk_level = 'high' THEN 1 END) as high_risk_count,
    COUNT(CASE WHEN ua.risk_level = 'critical' THEN 1 END) as critical_risk_count
FROM assessments a
LEFT JOIN user_assessments ua ON a.id = ua.assessment_id
WHERE a.is_active = true
GROUP BY a.id, a.type, a.title;

-- View for user assessment history
CREATE OR REPLACE VIEW user_assessment_history AS
SELECT 
    ua.id,
    ua.user_id,
    ua.email,
    ua.first_name,
    ua.last_name,
    a.type as assessment_type,
    a.title as assessment_title,
    ua.score,
    ua.risk_level,
    ua.completed_at,
    ua.time_spent_seconds,
    ar.insights_json,
    ar.recommendations_json
FROM user_assessments ua
JOIN assessments a ON ua.assessment_id = a.id
LEFT JOIN assessment_results ar ON ua.id = ar.user_assessment_id
WHERE ua.is_complete = true
ORDER BY ua.completed_at DESC;

-- =====================================================
-- CREATE FUNCTIONS FOR ASSESSMENT PROCESSING
-- =====================================================

-- Function to calculate assessment score based on responses and scoring config
CREATE OR REPLACE FUNCTION calculate_assessment_score(
    p_responses_json JSONB,
    p_scoring_config JSONB
)
RETURNS INTEGER AS $$
DECLARE
    total_score DECIMAL := 0;
    question_value INTEGER;
    question_weight DECIMAL;
    question JSONB;
BEGIN
    -- Loop through each question in the responses
    FOR question IN SELECT * FROM jsonb_array_elements(p_responses_json)
    LOOP
        -- Extract question value and weight
        question_value := (question->>'value')::INTEGER;
        question_weight := (question->>'weight')::DECIMAL;
        
        -- Add weighted score
        total_score := total_score + (question_value * question_weight);
    END LOOP;
    
    -- Apply scoring formula if specified
    IF p_scoring_config ? 'score_formula' THEN
        -- This would be a more complex calculation based on the formula
        -- For now, we'll use a simple weighted average
        total_score := total_score * 20; -- Scale to 0-100
    END IF;
    
    RETURN LEAST(GREATEST(total_score::INTEGER, 0), 100);
END;
$$ LANGUAGE plpgsql;

-- Function to determine risk level based on score
CREATE OR REPLACE FUNCTION determine_risk_level(
    p_score INTEGER,
    p_assessment_type assessment_type
)
RETURNS risk_level_type AS $$
BEGIN
    CASE p_assessment_type
        WHEN 'ai_job_risk' THEN
            IF p_score <= 30 THEN RETURN 'low';
            ELSIF p_score <= 60 THEN RETURN 'medium';
            ELSIF p_score <= 80 THEN RETURN 'high';
            ELSE RETURN 'critical';
            END IF;
        WHEN 'relationship_impact' THEN
            IF p_score <= 30 THEN RETURN 'low';
            ELSIF p_score <= 60 THEN RETURN 'medium';
            ELSIF p_score <= 80 THEN RETURN 'high';
            ELSE RETURN 'critical';
            END IF;
        WHEN 'tax_impact' THEN
            IF p_score >= 70 THEN RETURN 'low';
            ELSIF p_score >= 40 THEN RETURN 'medium';
            ELSIF p_score >= 20 THEN RETURN 'high';
            ELSE RETURN 'critical';
            END IF;
        WHEN 'income_comparison' THEN
            IF p_score >= 70 THEN RETURN 'low';
            ELSIF p_score >= 40 THEN RETURN 'medium';
            ELSIF p_score >= 20 THEN RETURN 'high';
            ELSE RETURN 'critical';
            END IF;
        ELSE
            RETURN 'medium';
    END CASE;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- MIGRATION COMPLETION
-- =====================================================

-- Log migration completion
DO $$
BEGIN
    RAISE NOTICE 'Migration 016_create_assessment_system_tables completed successfully';
    RAISE NOTICE 'Created tables: assessments, user_assessments, assessment_results';
    RAISE NOTICE 'Created indexes: 15 performance indexes';
    RAISE NOTICE 'Created views: assessment_completion_stats, user_assessment_history';
    RAISE NOTICE 'Created functions: calculate_assessment_score, determine_risk_level';
    RAISE NOTICE 'Inserted default assessment templates: 4 assessment types';
END $$;
