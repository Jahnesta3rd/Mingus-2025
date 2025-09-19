-- Problem-Solution Analysis Database Schema
-- Enhanced database schema for Job Description to Problem Statement Analysis

-- Job Problem Analysis Table
CREATE TABLE IF NOT EXISTS job_problem_analysis (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_opportunity_id INTEGER,
    user_id VARCHAR(100),
    problem_statement_context TEXT,
    problem_statement_challenge TEXT,
    problem_statement_impact TEXT,
    problem_statement_desired_outcome TEXT,
    problem_statement_timeframe TEXT,
    problem_statement_constraints TEXT,
    industry_context VARCHAR(50),
    company_stage VARCHAR(50),
    confidence_score REAL,
    primary_problems JSON,
    secondary_problems JSON,
    tertiary_problems JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (job_opportunity_id) REFERENCES job_opportunities(id)
);

-- Solution Recommendations Table
CREATE TABLE IF NOT EXISTS solution_recommendations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_analysis_id INTEGER,
    user_id VARCHAR(100),
    recommendation_type VARCHAR(20) CHECK (recommendation_type IN ('skill', 'certification', 'title')),
    recommendation_name VARCHAR(200),
    description TEXT,
    relevance_score INTEGER,
    industry_demand_score INTEGER,
    career_impact_score INTEGER,
    learning_roi_score INTEGER,
    competitive_advantage_score INTEGER,
    total_score INTEGER,
    rank INTEGER,
    reasoning TEXT,
    time_to_acquire VARCHAR(50),
    cost_estimate VARCHAR(100),
    salary_impact VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (job_analysis_id) REFERENCES job_problem_analysis(id)
);

-- Enhanced Job Matches Table
CREATE TABLE IF NOT EXISTS enhanced_job_matches (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_opportunity_id INTEGER,
    user_id VARCHAR(100),
    problem_analysis_id INTEGER,
    solution_analysis_id INTEGER,
    enhanced_score REAL,
    problem_solution_alignment REAL,
    positioning_strategy JSON,
    application_insights JSON,
    success_probability REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (job_opportunity_id) REFERENCES job_opportunities(id),
    FOREIGN KEY (problem_analysis_id) REFERENCES job_problem_analysis(id)
);

-- User Problem-Solution Profiles Table
CREATE TABLE IF NOT EXISTS user_problem_solution_profiles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id VARCHAR(100) UNIQUE,
    current_skills JSON,
    target_skills JSON,
    skill_gaps JSON,
    learning_plan JSON,
    positioning_strategy JSON,
    success_metrics JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Problem-Solution Analytics Table
CREATE TABLE IF NOT EXISTS problem_solution_analytics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id VARCHAR(100),
    analysis_type VARCHAR(50),
    problem_keywords JSON,
    solution_keywords JSON,
    industry_context VARCHAR(50),
    company_stage VARCHAR(50),
    success_rate REAL,
    application_outcomes JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Enhanced Job Opportunities Table (extends existing)
ALTER TABLE job_opportunities ADD COLUMN problem_solution_score REAL DEFAULT 0.0;
ALTER TABLE job_opportunities ADD COLUMN problem_statement TEXT;
ALTER TABLE job_opportunities ADD COLUMN solution_alignment JSON;
ALTER TABLE job_opportunities ADD COLUMN positioning_insights JSON;

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_job_problem_analysis_user_id ON job_problem_analysis(user_id);
CREATE INDEX IF NOT EXISTS idx_job_problem_analysis_industry ON job_problem_analysis(industry_context);
CREATE INDEX IF NOT EXISTS idx_job_problem_analysis_confidence ON job_problem_analysis(confidence_score);

CREATE INDEX IF NOT EXISTS idx_solution_recommendations_user_id ON solution_recommendations(user_id);
CREATE INDEX IF NOT EXISTS idx_solution_recommendations_type ON solution_recommendations(recommendation_type);
CREATE INDEX IF NOT EXISTS idx_solution_recommendations_score ON solution_recommendations(total_score);

CREATE INDEX IF NOT EXISTS idx_enhanced_matches_user_id ON enhanced_job_matches(user_id);
CREATE INDEX IF NOT EXISTS idx_enhanced_matches_score ON enhanced_job_matches(enhanced_score);
CREATE INDEX IF NOT EXISTS idx_enhanced_matches_alignment ON enhanced_job_matches(problem_solution_alignment);

CREATE INDEX IF NOT EXISTS idx_user_profiles_user_id ON user_problem_solution_profiles(user_id);

CREATE INDEX IF NOT EXISTS idx_analytics_user_id ON problem_solution_analytics(user_id);
CREATE INDEX IF NOT EXISTS idx_analytics_type ON problem_solution_analytics(analysis_type);

-- Views for common queries
CREATE VIEW IF NOT EXISTS user_problem_solution_summary AS
SELECT 
    u.user_id,
    u.current_skills,
    u.target_skills,
    COUNT(DISTINCT jpa.id) as total_analyses,
    AVG(jpa.confidence_score) as avg_confidence,
    COUNT(DISTINCT sr.id) as total_recommendations,
    AVG(sr.total_score) as avg_recommendation_score
FROM user_problem_solution_profiles u
LEFT JOIN job_problem_analysis jpa ON u.user_id = jpa.user_id
LEFT JOIN solution_recommendations sr ON u.user_id = sr.user_id
GROUP BY u.user_id;

CREATE VIEW IF NOT EXISTS top_solution_recommendations AS
SELECT 
    recommendation_type,
    recommendation_name,
    AVG(total_score) as avg_score,
    COUNT(*) as recommendation_count,
    AVG(relevance_score) as avg_relevance,
    AVG(industry_demand_score) as avg_industry_demand
FROM solution_recommendations
WHERE total_score >= 70
GROUP BY recommendation_type, recommendation_name
ORDER BY avg_score DESC;

CREATE VIEW IF NOT EXISTS enhanced_match_performance AS
SELECT 
    ejm.user_id,
    COUNT(*) as total_matches,
    AVG(ejm.enhanced_score) as avg_enhanced_score,
    AVG(ejm.problem_solution_alignment) as avg_alignment,
    AVG(ejm.success_probability) as avg_success_probability,
    COUNT(CASE WHEN ejm.enhanced_score >= 80 THEN 1 END) as high_score_matches
FROM enhanced_job_matches ejm
GROUP BY ejm.user_id;

-- Triggers for data consistency
CREATE TRIGGER IF NOT EXISTS update_job_problem_analysis_timestamp
    AFTER UPDATE ON job_problem_analysis
    BEGIN
        UPDATE job_problem_analysis SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
    END;

CREATE TRIGGER IF NOT EXISTS update_user_profiles_timestamp
    AFTER UPDATE ON user_problem_solution_profiles
    BEGIN
        UPDATE user_problem_solution_profiles SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
    END;

-- Sample data insertion functions
CREATE TRIGGER IF NOT EXISTS create_user_problem_solution_profile
    AFTER INSERT ON user_problem_solution_profiles
    WHEN NEW.current_skills IS NULL
    BEGIN
        UPDATE user_problem_solution_profiles 
        SET current_skills = '[]',
            target_skills = '[]',
            skill_gaps = '[]',
            learning_plan = '{}',
            positioning_strategy = '{}',
            success_metrics = '{}'
        WHERE id = NEW.id;
    END;

-- Performance optimization views
CREATE VIEW IF NOT EXISTS problem_solution_insights AS
SELECT 
    jpa.industry_context,
    jpa.company_stage,
    AVG(jpa.confidence_score) as avg_confidence,
    COUNT(DISTINCT jpa.id) as analysis_count,
    COUNT(DISTINCT sr.id) as recommendation_count,
    AVG(sr.total_score) as avg_recommendation_score
FROM job_problem_analysis jpa
LEFT JOIN solution_recommendations sr ON jpa.id = sr.job_analysis_id
GROUP BY jpa.industry_context, jpa.company_stage;

-- User success tracking view
CREATE VIEW IF NOT EXISTS user_success_tracking AS
SELECT 
    u.user_id,
    u.current_skills,
    COUNT(DISTINCT ejm.id) as total_enhanced_matches,
    AVG(ejm.enhanced_score) as avg_enhanced_score,
    AVG(ejm.success_probability) as avg_success_probability,
    COUNT(DISTINCT jpa.id) as total_problem_analyses,
    AVG(jpa.confidence_score) as avg_problem_confidence
FROM user_problem_solution_profiles u
LEFT JOIN enhanced_job_matches ejm ON u.user_id = ejm.user_id
LEFT JOIN job_problem_analysis jpa ON u.user_id = jpa.user_id
GROUP BY u.user_id;

-- Industry-specific problem patterns view
CREATE VIEW IF NOT EXISTS industry_problem_patterns AS
SELECT 
    industry_context,
    JSON_EXTRACT(primary_problems, '$[*].indicators') as common_indicators,
    COUNT(*) as pattern_frequency,
    AVG(confidence_score) as avg_confidence
FROM job_problem_analysis
WHERE primary_problems IS NOT NULL
GROUP BY industry_context;

-- Solution effectiveness tracking view
CREATE VIEW IF NOT EXISTS solution_effectiveness AS
SELECT 
    sr.recommendation_type,
    sr.recommendation_name,
    AVG(sr.total_score) as avg_score,
    COUNT(*) as usage_count,
    AVG(sr.relevance_score) as avg_relevance,
    AVG(sr.industry_demand_score) as avg_industry_demand,
    AVG(sr.career_impact_score) as avg_career_impact
FROM solution_recommendations sr
GROUP BY sr.recommendation_type, sr.recommendation_name
HAVING COUNT(*) >= 5  -- Only include solutions with sufficient data
ORDER BY avg_score DESC;

-- Career positioning success metrics view
CREATE VIEW IF NOT EXISTS career_positioning_metrics AS
SELECT 
    ejm.user_id,
    COUNT(*) as total_applications,
    AVG(ejm.enhanced_score) as avg_application_score,
    AVG(ejm.problem_solution_alignment) as avg_positioning_alignment,
    COUNT(CASE WHEN ejm.enhanced_score >= 85 THEN 1 END) as high_quality_matches,
    COUNT(CASE WHEN ejm.problem_solution_alignment >= 80 THEN 1 END) as strong_positioning_matches
FROM enhanced_job_matches ejm
GROUP BY ejm.user_id;

-- Problem-solution learning recommendations view
CREATE VIEW IF NOT EXISTS learning_recommendations AS
SELECT 
    sr.user_id,
    sr.recommendation_type,
    sr.recommendation_name,
    sr.total_score,
    sr.time_to_acquire,
    sr.cost_estimate,
    sr.salary_impact,
    ROW_NUMBER() OVER (PARTITION BY sr.user_id, sr.recommendation_type ORDER BY sr.total_score DESC) as rank
FROM solution_recommendations sr
WHERE sr.total_score >= 70
ORDER BY sr.user_id, sr.recommendation_type, sr.total_score DESC;
