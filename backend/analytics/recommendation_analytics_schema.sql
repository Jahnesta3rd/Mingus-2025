-- =====================================================
-- Recommendation Analytics Database Schema
-- Comprehensive analytics tracking for job recommendation system
-- =====================================================

-- Enable foreign key constraints
PRAGMA foreign_keys = ON;

-- =====================================================
-- 1. USER BEHAVIOR ANALYTICS TABLES
-- =====================================================

-- User sessions and journey tracking
CREATE TABLE IF NOT EXISTS user_sessions (
    session_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    session_start TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    session_end TIMESTAMP,
    session_duration INTEGER, -- in seconds
    device_type TEXT CHECK (device_type IN ('mobile', 'tablet', 'desktop')),
    browser TEXT,
    os TEXT,
    ip_address TEXT,
    user_agent TEXT,
    referrer TEXT,
    exit_page TEXT,
    bounce_rate BOOLEAN DEFAULT FALSE,
    conversion_events INTEGER DEFAULT 0
);

-- Resume upload and processing events
CREATE TABLE IF NOT EXISTS resume_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    event_type TEXT NOT NULL CHECK (event_type IN (
        'upload_started', 'upload_completed', 'upload_failed',
        'parsing_started', 'parsing_completed', 'parsing_failed',
        'validation_started', 'validation_completed', 'validation_failed'
    )),
    file_name TEXT,
    file_size INTEGER,
    file_type TEXT,
    processing_time REAL, -- in seconds
    error_message TEXT,
    success_rate REAL,
    confidence_score REAL,
    extracted_fields TEXT, -- JSON of extracted data
    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES user_sessions (session_id)
);

-- User interaction events
CREATE TABLE IF NOT EXISTS user_interactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    interaction_type TEXT NOT NULL CHECK (interaction_type IN (
        'page_view', 'button_click', 'form_submit', 'scroll_depth',
        'time_on_page', 'recommendation_view', 'recommendation_click',
        'application_start', 'application_complete', 'share', 'bookmark'
    )),
    page_url TEXT,
    element_id TEXT,
    element_text TEXT,
    interaction_data TEXT, -- JSON of additional data
    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES user_sessions (session_id)
);

-- Feature usage tracking
CREATE TABLE IF NOT EXISTS feature_usage (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    feature_name TEXT NOT NULL,
    usage_count INTEGER DEFAULT 1,
    first_used TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_used TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    total_time_spent INTEGER DEFAULT 0, -- in seconds
    success_rate REAL DEFAULT 0.0,
    satisfaction_score INTEGER CHECK (satisfaction_score BETWEEN 1 AND 5),
    UNIQUE(user_id, feature_name)
);

-- =====================================================
-- 2. RECOMMENDATION EFFECTIVENESS TABLES
-- =====================================================

-- Job recommendations tracking
CREATE TABLE IF NOT EXISTS job_recommendations (
    recommendation_id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    job_id TEXT NOT NULL,
    tier TEXT NOT NULL CHECK (tier IN ('conservative', 'optimal', 'stretch')),
    recommendation_score REAL NOT NULL,
    salary_increase_potential REAL,
    success_probability REAL,
    skills_gap_score REAL,
    company_culture_fit REAL,
    career_advancement_potential REAL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES user_sessions (session_id)
);

-- Recommendation engagement tracking
CREATE TABLE IF NOT EXISTS recommendation_engagement (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    recommendation_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    engagement_type TEXT NOT NULL CHECK (engagement_type IN (
        'viewed', 'clicked', 'applied', 'saved', 'shared', 'dismissed'
    )),
    engagement_time REAL, -- time spent viewing in seconds
    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (recommendation_id) REFERENCES job_recommendations (recommendation_id)
);

-- Application outcomes tracking
CREATE TABLE IF NOT EXISTS application_outcomes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    recommendation_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    application_id TEXT UNIQUE,
    application_status TEXT NOT NULL CHECK (application_status IN (
        'started', 'submitted', 'under_review', 'interview_scheduled',
        'interview_completed', 'offer_received', 'offer_accepted',
        'offer_declined', 'rejected', 'withdrawn'
    )),
    application_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    outcome_date TIMESTAMP,
    salary_offered REAL,
    salary_negotiated REAL,
    final_salary REAL,
    interview_rounds INTEGER DEFAULT 0,
    feedback_received TEXT,
    success_factors TEXT, -- JSON of factors that led to success
    FOREIGN KEY (recommendation_id) REFERENCES job_recommendations (recommendation_id)
);

-- User satisfaction and feedback
CREATE TABLE IF NOT EXISTS user_feedback (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    session_id TEXT,
    feedback_type TEXT NOT NULL CHECK (feedback_type IN (
        'recommendation_quality', 'system_performance', 'user_experience',
        'feature_request', 'bug_report', 'general_feedback'
    )),
    rating INTEGER CHECK (rating BETWEEN 1 AND 5),
    feedback_text TEXT,
    recommendation_id TEXT,
    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (recommendation_id) REFERENCES job_recommendations (recommendation_id)
);

-- =====================================================
-- 3. SYSTEM PERFORMANCE MONITORING TABLES
-- =====================================================

-- API performance tracking
CREATE TABLE IF NOT EXISTS api_performance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    endpoint TEXT NOT NULL,
    method TEXT NOT NULL,
    response_time REAL NOT NULL, -- in milliseconds
    status_code INTEGER NOT NULL,
    request_size INTEGER,
    response_size INTEGER,
    user_id TEXT,
    session_id TEXT,
    error_message TEXT,
    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Processing time tracking
CREATE TABLE IF NOT EXISTS processing_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    process_name TEXT NOT NULL,
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP NOT NULL,
    duration REAL NOT NULL, -- in seconds
    memory_usage INTEGER, -- in MB
    cpu_usage REAL, -- percentage
    success BOOLEAN NOT NULL,
    error_message TEXT,
    metadata TEXT, -- JSON of additional metrics
    FOREIGN KEY (session_id) REFERENCES user_sessions (session_id)
);

-- System resource monitoring
CREATE TABLE IF NOT EXISTS system_resources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    cpu_usage REAL NOT NULL,
    memory_usage REAL NOT NULL,
    disk_usage REAL NOT NULL,
    active_connections INTEGER NOT NULL,
    queue_length INTEGER NOT NULL,
    error_rate REAL NOT NULL,
    response_time_avg REAL NOT NULL
);

-- Error tracking
CREATE TABLE IF NOT EXISTS error_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    error_type TEXT NOT NULL,
    error_message TEXT NOT NULL,
    stack_trace TEXT,
    user_id TEXT,
    session_id TEXT,
    endpoint TEXT,
    severity TEXT NOT NULL CHECK (severity IN ('low', 'medium', 'high', 'critical')),
    resolved BOOLEAN DEFAULT FALSE,
    resolved_at TIMESTAMP,
    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- 4. BUSINESS IMPACT METRICS TABLES
-- =====================================================

-- User income tracking
CREATE TABLE IF NOT EXISTS income_tracking (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    current_salary REAL NOT NULL,
    target_salary REAL,
    salary_increase REAL,
    increase_percentage REAL,
    tracking_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    source TEXT, -- 'self_reported', 'linkedin', 'application_outcome'
    verified BOOLEAN DEFAULT FALSE
);

-- Career advancement tracking
CREATE TABLE IF NOT EXISTS career_advancement (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    advancement_type TEXT NOT NULL CHECK (advancement_type IN (
        'promotion', 'salary_increase', 'role_change', 'skill_development',
        'certification', 'education', 'networking', 'mentorship'
    )),
    advancement_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    previous_role TEXT,
    new_role TEXT,
    salary_change REAL,
    skill_improvements TEXT, -- JSON of skills developed
    recommendation_correlation TEXT, -- JSON linking to recommendations
    success_factors TEXT -- JSON of factors that contributed
);

-- User retention and engagement
CREATE TABLE IF NOT EXISTS user_retention (
    user_id TEXT PRIMARY KEY,
    registration_date TIMESTAMP NOT NULL,
    last_activity TIMESTAMP NOT NULL,
    total_sessions INTEGER DEFAULT 0,
    total_time_spent INTEGER DEFAULT 0, -- in seconds
    recommendations_received INTEGER DEFAULT 0,
    applications_submitted INTEGER DEFAULT 0,
    successful_outcomes INTEGER DEFAULT 0,
    satisfaction_avg REAL,
    churn_risk_score REAL,
    engagement_score REAL,
    lifetime_value REAL
);

-- Goal achievement tracking
CREATE TABLE IF NOT EXISTS goal_achievement (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    goal_type TEXT NOT NULL CHECK (goal_type IN (
        'salary_increase', 'career_change', 'skill_development',
        'promotion', 'work_life_balance', 'job_satisfaction'
    )),
    goal_value TEXT NOT NULL, -- specific goal description
    target_date DATE,
    achieved_date DATE,
    achievement_percentage REAL,
    recommendation_contribution REAL, -- how much recommendations helped
    success_factors TEXT, -- JSON of contributing factors
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- 5. A/B TESTING FRAMEWORK TABLES
-- =====================================================

-- A/B test definitions
CREATE TABLE IF NOT EXISTS ab_tests (
    test_id TEXT PRIMARY KEY,
    test_name TEXT NOT NULL,
    description TEXT,
    hypothesis TEXT,
    start_date TIMESTAMP NOT NULL,
    end_date TIMESTAMP,
    status TEXT NOT NULL CHECK (status IN ('draft', 'active', 'paused', 'completed', 'cancelled')),
    target_metric TEXT NOT NULL,
    success_threshold REAL,
    minimum_sample_size INTEGER,
    created_by TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- A/B test variants
CREATE TABLE IF NOT EXISTS ab_test_variants (
    variant_id TEXT PRIMARY KEY,
    test_id TEXT NOT NULL,
    variant_name TEXT NOT NULL,
    variant_description TEXT,
    configuration TEXT NOT NULL, -- JSON of variant configuration
    traffic_percentage REAL NOT NULL CHECK (traffic_percentage BETWEEN 0 AND 100),
    is_control BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (test_id) REFERENCES ab_tests (test_id)
);

-- A/B test assignments
CREATE TABLE IF NOT EXISTS ab_test_assignments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    test_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    variant_id TEXT NOT NULL,
    assigned_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    conversion_events TEXT, -- JSON of conversion events
    UNIQUE(test_id, user_id),
    FOREIGN KEY (test_id) REFERENCES ab_tests (test_id),
    FOREIGN KEY (variant_id) REFERENCES ab_test_variants (variant_id)
);

-- A/B test results
CREATE TABLE IF NOT EXISTS ab_test_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    test_id TEXT NOT NULL,
    variant_id TEXT NOT NULL,
    metric_name TEXT NOT NULL,
    metric_value REAL NOT NULL,
    sample_size INTEGER NOT NULL,
    confidence_interval_lower REAL,
    confidence_interval_upper REAL,
    statistical_significance REAL,
    calculated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (test_id) REFERENCES ab_tests (test_id),
    FOREIGN KEY (variant_id) REFERENCES ab_test_variants (variant_id)
);

-- =====================================================
-- 6. DASHBOARD AND REPORTING TABLES
-- =====================================================

-- Daily analytics summary
CREATE TABLE IF NOT EXISTS daily_analytics_summary (
    date DATE PRIMARY KEY,
    total_users INTEGER NOT NULL DEFAULT 0,
    new_users INTEGER NOT NULL DEFAULT 0,
    active_users INTEGER NOT NULL DEFAULT 0,
    total_sessions INTEGER NOT NULL DEFAULT 0,
    resume_uploads INTEGER NOT NULL DEFAULT 0,
    recommendations_generated INTEGER NOT NULL DEFAULT 0,
    applications_started INTEGER NOT NULL DEFAULT 0,
    applications_completed INTEGER NOT NULL DEFAULT 0,
    successful_outcomes INTEGER NOT NULL DEFAULT 0,
    avg_session_duration REAL NOT NULL DEFAULT 0,
    conversion_rate REAL NOT NULL DEFAULT 0,
    satisfaction_avg REAL NOT NULL DEFAULT 0,
    error_rate REAL NOT NULL DEFAULT 0,
    avg_response_time REAL NOT NULL DEFAULT 0
);

-- Real-time metrics cache
CREATE TABLE IF NOT EXISTS real_time_metrics (
    metric_name TEXT PRIMARY KEY,
    metric_value REAL NOT NULL,
    last_updated TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    metadata TEXT -- JSON of additional metric data
);

-- Alert definitions
CREATE TABLE IF NOT EXISTS alert_definitions (
    alert_id TEXT PRIMARY KEY,
    alert_name TEXT NOT NULL,
    metric_name TEXT NOT NULL,
    threshold_value REAL NOT NULL,
    comparison_operator TEXT NOT NULL CHECK (comparison_operator IN ('>', '<', '>=', '<=', '=', '!=')),
    severity TEXT NOT NULL CHECK (severity IN ('low', 'medium', 'high', 'critical')),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Alert history
CREATE TABLE IF NOT EXISTS alert_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    alert_id TEXT NOT NULL,
    triggered_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    metric_value REAL NOT NULL,
    threshold_value REAL NOT NULL,
    resolved_at TIMESTAMP,
    acknowledged_by TEXT,
    FOREIGN KEY (alert_id) REFERENCES alert_definitions (alert_id)
);

-- =====================================================
-- 7. INDEXES FOR PERFORMANCE
-- =====================================================

-- User sessions indexes
CREATE INDEX IF NOT EXISTS idx_user_sessions_user_id ON user_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_user_sessions_start ON user_sessions(session_start);
CREATE INDEX IF NOT EXISTS idx_user_sessions_device ON user_sessions(device_type);

-- Resume events indexes
CREATE INDEX IF NOT EXISTS idx_resume_events_session ON resume_events(session_id);
CREATE INDEX IF NOT EXISTS idx_resume_events_type ON resume_events(event_type);
CREATE INDEX IF NOT EXISTS idx_resume_events_timestamp ON resume_events(timestamp);

-- User interactions indexes
CREATE INDEX IF NOT EXISTS idx_user_interactions_session ON user_interactions(session_id);
CREATE INDEX IF NOT EXISTS idx_user_interactions_type ON user_interactions(interaction_type);
CREATE INDEX IF NOT EXISTS idx_user_interactions_timestamp ON user_interactions(timestamp);

-- Recommendation indexes
CREATE INDEX IF NOT EXISTS idx_job_recommendations_user ON job_recommendations(user_id);
CREATE INDEX IF NOT EXISTS idx_job_recommendations_tier ON job_recommendations(tier);
CREATE INDEX IF NOT EXISTS idx_job_recommendations_created ON job_recommendations(created_at);

-- Engagement indexes
CREATE INDEX IF NOT EXISTS idx_recommendation_engagement_rec ON recommendation_engagement(recommendation_id);
CREATE INDEX IF NOT EXISTS idx_recommendation_engagement_type ON recommendation_engagement(engagement_type);

-- Application outcomes indexes
CREATE INDEX IF NOT EXISTS idx_application_outcomes_rec ON application_outcomes(recommendation_id);
CREATE INDEX IF NOT EXISTS idx_application_outcomes_status ON application_outcomes(application_status);
CREATE INDEX IF NOT EXISTS idx_application_outcomes_date ON application_outcomes(application_date);

-- Performance indexes
CREATE INDEX IF NOT EXISTS idx_api_performance_endpoint ON api_performance(endpoint);
CREATE INDEX IF NOT EXISTS idx_api_performance_timestamp ON api_performance(timestamp);
CREATE INDEX IF NOT EXISTS idx_processing_metrics_session ON processing_metrics(session_id);
CREATE INDEX IF NOT EXISTS idx_processing_metrics_process ON processing_metrics(process_name);

-- Business impact indexes
CREATE INDEX IF NOT EXISTS idx_income_tracking_user ON income_tracking(user_id);
CREATE INDEX IF NOT EXISTS idx_career_advancement_user ON career_advancement(user_id);
CREATE INDEX IF NOT EXISTS idx_goal_achievement_user ON goal_achievement(user_id);

-- A/B testing indexes
CREATE INDEX IF NOT EXISTS idx_ab_test_assignments_user ON ab_test_assignments(user_id);
CREATE INDEX IF NOT EXISTS idx_ab_test_assignments_test ON ab_test_assignments(test_id);
CREATE INDEX IF NOT EXISTS idx_ab_test_results_test ON ab_test_results(test_id);

-- Dashboard indexes
CREATE INDEX IF NOT EXISTS idx_daily_analytics_date ON daily_analytics_summary(date);
CREATE INDEX IF NOT EXISTS idx_alert_history_alert ON alert_history(alert_id);
CREATE INDEX IF NOT EXISTS idx_alert_history_triggered ON alert_history(triggered_at);

-- =====================================================
-- 8. VIEWS FOR COMMON QUERIES
-- =====================================================

-- User success metrics view
CREATE VIEW IF NOT EXISTS user_success_metrics AS
SELECT 
    u.user_id,
    u.registration_date,
    u.last_activity,
    u.total_sessions,
    u.total_time_spent,
    u.recommendations_received,
    u.applications_submitted,
    u.successful_outcomes,
    u.satisfaction_avg,
    u.engagement_score,
    COALESCE(i.current_salary, 0) as current_salary,
    COALESCE(i.salary_increase, 0) as salary_increase,
    COALESCE(i.increase_percentage, 0) as salary_increase_percentage
FROM user_retention u
LEFT JOIN (
    SELECT user_id, current_salary, salary_increase, increase_percentage,
           ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY tracking_date DESC) as rn
    FROM income_tracking
) i ON u.user_id = i.user_id AND i.rn = 1;

-- Recommendation effectiveness view
CREATE VIEW IF NOT EXISTS recommendation_effectiveness AS
SELECT 
    jr.tier,
    COUNT(*) as total_recommendations,
    COUNT(re.engagement_id) as total_engagements,
    COUNT(ao.application_id) as applications_started,
    COUNT(CASE WHEN ao.application_status IN ('offer_received', 'offer_accepted') THEN 1 END) as successful_applications,
    AVG(jr.recommendation_score) as avg_recommendation_score,
    AVG(jr.salary_increase_potential) as avg_salary_potential,
    AVG(ao.final_salary) as avg_final_salary,
    COUNT(CASE WHEN ao.application_status = 'offer_accepted' THEN 1 END) * 100.0 / COUNT(ao.application_id) as success_rate
FROM job_recommendations jr
LEFT JOIN recommendation_engagement re ON jr.recommendation_id = re.recommendation_id
LEFT JOIN application_outcomes ao ON jr.recommendation_id = ao.recommendation_id
GROUP BY jr.tier;

-- System performance summary view
CREATE VIEW IF NOT EXISTS system_performance_summary AS
SELECT 
    DATE(timestamp) as date,
    COUNT(*) as total_requests,
    AVG(response_time) as avg_response_time,
    COUNT(CASE WHEN status_code >= 400 THEN 1 END) * 100.0 / COUNT(*) as error_rate,
    AVG(request_size) as avg_request_size,
    AVG(response_size) as avg_response_size
FROM api_performance
GROUP BY DATE(timestamp)
ORDER BY date DESC;

-- =====================================================
-- 9. TRIGGERS FOR AUTOMATIC UPDATES
-- =====================================================

-- Update user retention on new session
CREATE TRIGGER IF NOT EXISTS update_user_retention_on_session
AFTER INSERT ON user_sessions
BEGIN
    INSERT OR REPLACE INTO user_retention (
        user_id, registration_date, last_activity, total_sessions
    ) VALUES (
        NEW.user_id,
        COALESCE((SELECT registration_date FROM user_retention WHERE user_id = NEW.user_id), NEW.session_start),
        NEW.session_start,
        COALESCE((SELECT total_sessions FROM user_retention WHERE user_id = NEW.user_id), 0) + 1
    );
END;

-- Update daily analytics summary
CREATE TRIGGER IF NOT EXISTS update_daily_analytics_on_session
AFTER INSERT ON user_sessions
BEGIN
    INSERT OR REPLACE INTO daily_analytics_summary (
        date, total_users, active_users, total_sessions
    ) VALUES (
        DATE(NEW.session_start),
        (SELECT COUNT(DISTINCT user_id) FROM user_sessions WHERE DATE(session_start) = DATE(NEW.session_start)),
        (SELECT COUNT(DISTINCT user_id) FROM user_sessions WHERE DATE(session_start) = DATE(NEW.session_start)),
        (SELECT COUNT(*) FROM user_sessions WHERE DATE(session_start) = DATE(NEW.session_start))
    );
END;

-- =====================================================
-- 10. INITIAL DATA AND CONFIGURATION
-- =====================================================

-- Insert default alert definitions
INSERT OR IGNORE INTO alert_definitions (alert_id, alert_name, metric_name, threshold_value, comparison_operator, severity) VALUES
('high_error_rate', 'High Error Rate', 'error_rate', 5.0, '>', 'high'),
('slow_response_time', 'Slow Response Time', 'avg_response_time', 2000.0, '>', 'medium'),
('low_conversion_rate', 'Low Conversion Rate', 'conversion_rate', 10.0, '<', 'medium'),
('high_bounce_rate', 'High Bounce Rate', 'bounce_rate', 70.0, '>', 'medium'),
('system_overload', 'System Overload', 'cpu_usage', 90.0, '>', 'critical');

-- =====================================================
-- 11. RISK-BASED CAREER PROTECTION TABLES
-- =====================================================

-- User risk assessment tracking
CREATE TABLE IF NOT EXISTS user_risk_assessments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    assessment_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    risk_level TEXT NOT NULL CHECK (risk_level IN ('low', 'medium', 'high', 'critical')),
    risk_score REAL NOT NULL CHECK (risk_score BETWEEN 0 AND 100),
    risk_factors TEXT NOT NULL, -- JSON of identified risk factors
    industry_risk_score REAL,
    company_risk_score REAL,
    role_risk_score REAL,
    market_risk_score REAL,
    personal_risk_score REAL,
    assessment_confidence REAL,
    next_assessment_date TIMESTAMP,
    intervention_triggered BOOLEAN DEFAULT FALSE,
    intervention_date TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES user_retention (user_id)
);

-- Risk intervention tracking
CREATE TABLE IF NOT EXISTS risk_interventions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    risk_assessment_id INTEGER NOT NULL,
    intervention_type TEXT NOT NULL CHECK (intervention_type IN (
        'early_warning', 'job_search_acceleration', 'skill_development',
        'network_expansion', 'emergency_unlock', 'career_coaching',
        'resume_optimization', 'interview_prep'
    )),
    intervention_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    intervention_status TEXT NOT NULL CHECK (intervention_status IN (
        'triggered', 'in_progress', 'completed', 'cancelled', 'expired'
    )),
    intervention_data TEXT, -- JSON of intervention details
    success_metrics TEXT, -- JSON of success tracking
    completion_date TIMESTAMP,
    effectiveness_score REAL,
    user_response TEXT, -- JSON of user feedback
    FOREIGN KEY (user_id) REFERENCES user_retention (user_id),
    FOREIGN KEY (risk_assessment_id) REFERENCES user_risk_assessments (id)
);

-- Career protection outcomes
CREATE TABLE IF NOT EXISTS career_protection_outcomes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    risk_assessment_id INTEGER NOT NULL,
    intervention_id INTEGER,
    outcome_type TEXT NOT NULL CHECK (outcome_type IN (
        'successful_transition', 'unemployment_prevented', 'salary_increased',
        'job_security_improved', 'career_advancement', 'skill_development',
        'network_expansion', 'early_warning_success', 'intervention_success'
    )),
    outcome_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    outcome_details TEXT NOT NULL, -- JSON of outcome details
    salary_change REAL,
    job_security_improvement REAL,
    time_to_new_role INTEGER, -- days
    satisfaction_score INTEGER CHECK (satisfaction_score BETWEEN 1 AND 5),
    would_recommend BOOLEAN,
    success_factors TEXT, -- JSON of contributing factors
    verification_status TEXT CHECK (verification_status IN ('unverified', 'pending', 'verified', 'rejected')),
    verified_date TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES user_retention (user_id),
    FOREIGN KEY (risk_assessment_id) REFERENCES user_risk_assessments (id),
    FOREIGN KEY (intervention_id) REFERENCES risk_interventions (id)
);

-- Risk trend forecasting data
CREATE TABLE IF NOT EXISTS risk_forecasts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    forecast_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    forecast_type TEXT NOT NULL CHECK (forecast_type IN (
        'industry_risk', 'market_risk', 'company_risk', 'role_risk', 'user_risk'
    )),
    target_entity TEXT NOT NULL, -- industry, company, role, or user_id
    forecast_horizon_days INTEGER NOT NULL,
    risk_probability REAL NOT NULL CHECK (risk_probability BETWEEN 0 AND 1),
    confidence_level REAL NOT NULL CHECK (confidence_level BETWEEN 0 AND 1),
    forecast_data TEXT NOT NULL, -- JSON of forecast details
    actual_outcome TEXT, -- JSON of actual results when available
    accuracy_score REAL,
    model_version TEXT,
    created_by TEXT DEFAULT 'system'
);

-- Risk success stories
CREATE TABLE IF NOT EXISTS risk_success_stories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    story_type TEXT NOT NULL CHECK (story_type IN (
        'early_transition', 'unemployment_avoided', 'salary_increased',
        'career_advancement', 'skill_development', 'network_expansion'
    )),
    story_title TEXT NOT NULL,
    story_description TEXT NOT NULL,
    original_risk_factors TEXT NOT NULL, -- JSON
    intervention_timeline TEXT NOT NULL, -- JSON
    outcome_details TEXT NOT NULL, -- JSON
    user_satisfaction INTEGER CHECK (user_satisfaction BETWEEN 1 AND 5),
    would_recommend BOOLEAN,
    testimonial_text TEXT,
    approval_status TEXT CHECK (approval_status IN ('pending', 'approved', 'rejected')) DEFAULT 'pending',
    created_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    approved_date TIMESTAMP,
    featured BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (user_id) REFERENCES user_retention (user_id)
);

-- Risk analytics aggregations
CREATE TABLE IF NOT EXISTS risk_analytics_aggregations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    aggregation_date DATE NOT NULL,
    metric_name TEXT NOT NULL,
    metric_value REAL NOT NULL,
    metric_category TEXT NOT NULL,
    breakdown_data TEXT, -- JSON of detailed breakdown
    confidence_interval_lower REAL,
    confidence_interval_upper REAL,
    sample_size INTEGER,
    last_updated TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(aggregation_date, metric_name, metric_category)
);

-- Risk dashboard alerts
CREATE TABLE IF NOT EXISTS risk_dashboard_alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    alert_type TEXT NOT NULL CHECK (alert_type IN (
        'protection_rate_decline', 'risk_pattern_change', 'intervention_ineffectiveness',
        'forecast_accuracy_drop', 'resource_shortage', 'system_overload'
    )),
    alert_title TEXT NOT NULL,
    alert_description TEXT NOT NULL,
    severity TEXT NOT NULL CHECK (severity IN ('low', 'medium', 'high', 'critical')),
    alert_data TEXT, -- JSON of alert details
    triggered_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP,
    acknowledged_by TEXT,
    resolution_notes TEXT,
    is_active BOOLEAN DEFAULT TRUE
);

-- =====================================================
-- 12. RISK-BASED INDEXES
-- =====================================================

-- Risk assessment indexes
CREATE INDEX IF NOT EXISTS idx_user_risk_assessments_user ON user_risk_assessments(user_id);
CREATE INDEX IF NOT EXISTS idx_user_risk_assessments_date ON user_risk_assessments(assessment_date);
CREATE INDEX IF NOT EXISTS idx_user_risk_assessments_level ON user_risk_assessments(risk_level);
CREATE INDEX IF NOT EXISTS idx_user_risk_assessments_score ON user_risk_assessments(risk_score);

-- Risk intervention indexes
CREATE INDEX IF NOT EXISTS idx_risk_interventions_user ON risk_interventions(user_id);
CREATE INDEX IF NOT EXISTS idx_risk_interventions_assessment ON risk_interventions(risk_assessment_id);
CREATE INDEX IF NOT EXISTS idx_risk_interventions_type ON risk_interventions(intervention_type);
CREATE INDEX IF NOT EXISTS idx_risk_interventions_status ON risk_interventions(intervention_status);

-- Career protection outcome indexes
CREATE INDEX IF NOT EXISTS idx_career_protection_user ON career_protection_outcomes(user_id);
CREATE INDEX IF NOT EXISTS idx_career_protection_assessment ON career_protection_outcomes(risk_assessment_id);
CREATE INDEX IF NOT EXISTS idx_career_protection_type ON career_protection_outcomes(outcome_type);
CREATE INDEX IF NOT EXISTS idx_career_protection_date ON career_protection_outcomes(outcome_date);

-- Risk forecast indexes
CREATE INDEX IF NOT EXISTS idx_risk_forecasts_type ON risk_forecasts(forecast_type);
CREATE INDEX IF NOT EXISTS idx_risk_forecasts_entity ON risk_forecasts(target_entity);
CREATE INDEX IF NOT EXISTS idx_risk_forecasts_date ON risk_forecasts(forecast_date);

-- Risk success story indexes
CREATE INDEX IF NOT EXISTS idx_risk_success_stories_user ON risk_success_stories(user_id);
CREATE INDEX IF NOT EXISTS idx_risk_success_stories_type ON risk_success_stories(story_type);
CREATE INDEX IF NOT EXISTS idx_risk_success_stories_approval ON risk_success_stories(approval_status);
CREATE INDEX IF NOT EXISTS idx_risk_success_stories_featured ON risk_success_stories(featured);

-- Risk analytics aggregation indexes
CREATE INDEX IF NOT EXISTS idx_risk_analytics_date ON risk_analytics_aggregations(aggregation_date);
CREATE INDEX IF NOT EXISTS idx_risk_analytics_metric ON risk_analytics_aggregations(metric_name);
CREATE INDEX IF NOT EXISTS idx_risk_analytics_category ON risk_analytics_aggregations(metric_category);

-- Risk dashboard alert indexes
CREATE INDEX IF NOT EXISTS idx_risk_dashboard_alerts_type ON risk_dashboard_alerts(alert_type);
CREATE INDEX IF NOT EXISTS idx_risk_dashboard_alerts_severity ON risk_dashboard_alerts(severity);
CREATE INDEX IF NOT EXISTS idx_risk_dashboard_alerts_active ON risk_dashboard_alerts(is_active);

-- =====================================================
-- 13. RISK-BASED VIEWS
-- =====================================================

-- Career protection effectiveness view
CREATE VIEW IF NOT EXISTS career_protection_effectiveness AS
SELECT 
    DATE(ura.assessment_date) as assessment_date,
    COUNT(*) as total_assessments,
    COUNT(CASE WHEN ura.risk_level IN ('high', 'critical') THEN 1 END) as high_risk_users,
    COUNT(cpo.id) as successful_outcomes,
    COUNT(CASE WHEN cpo.outcome_type = 'successful_transition' THEN 1 END) as successful_transitions,
    COUNT(CASE WHEN cpo.outcome_type = 'unemployment_prevented' THEN 1 END) as unemployment_prevented,
    COUNT(CASE WHEN cpo.outcome_type = 'salary_increased' THEN 1 END) as salary_increases,
    AVG(cpo.salary_change) as avg_salary_change,
    AVG(cpo.time_to_new_role) as avg_time_to_new_role,
    COUNT(CASE WHEN cpo.satisfaction_score >= 4 THEN 1 END) * 100.0 / COUNT(cpo.id) as satisfaction_rate
FROM user_risk_assessments ura
LEFT JOIN career_protection_outcomes cpo ON ura.id = cpo.risk_assessment_id
GROUP BY DATE(ura.assessment_date)
ORDER BY assessment_date DESC;

-- Risk intervention effectiveness view
CREATE VIEW IF NOT EXISTS risk_intervention_effectiveness AS
SELECT 
    ri.intervention_type,
    COUNT(*) as total_interventions,
    COUNT(CASE WHEN ri.intervention_status = 'completed' THEN 1 END) as completed_interventions,
    COUNT(CASE WHEN ri.intervention_status = 'completed' AND ri.effectiveness_score >= 7 THEN 1 END) as effective_interventions,
    AVG(ri.effectiveness_score) as avg_effectiveness_score,
    COUNT(CASE WHEN ri.intervention_status = 'completed' THEN 1 END) * 100.0 / COUNT(*) as completion_rate,
    COUNT(CASE WHEN ri.intervention_status = 'completed' AND ri.effectiveness_score >= 7 THEN 1 END) * 100.0 / 
        COUNT(CASE WHEN ri.intervention_status = 'completed' THEN 1 END) as effectiveness_rate
FROM risk_interventions ri
GROUP BY ri.intervention_type
ORDER BY effectiveness_rate DESC;

-- Risk trend analysis view
CREATE VIEW IF NOT EXISTS risk_trend_analysis AS
SELECT 
    rf.forecast_type,
    rf.target_entity,
    DATE(rf.forecast_date) as forecast_date,
    rf.forecast_horizon_days,
    rf.risk_probability,
    rf.confidence_level,
    rf.accuracy_score,
    CASE 
        WHEN rf.accuracy_score >= 0.8 THEN 'high'
        WHEN rf.accuracy_score >= 0.6 THEN 'medium'
        ELSE 'low'
    END as accuracy_level
FROM risk_forecasts rf
WHERE rf.actual_outcome IS NOT NULL
ORDER BY rf.forecast_date DESC;

-- =====================================================
-- 14. RISK-BASED TRIGGERS
-- =====================================================

-- Update risk analytics aggregations on new outcome
CREATE TRIGGER IF NOT EXISTS update_risk_analytics_on_outcome
AFTER INSERT ON career_protection_outcomes
BEGIN
    -- Update daily protection success rate
    INSERT OR REPLACE INTO risk_analytics_aggregations (
        aggregation_date, metric_name, metric_value, metric_category
    ) VALUES (
        DATE(NEW.outcome_date),
        'daily_protection_success_rate',
        (SELECT COUNT(*) * 100.0 / (SELECT COUNT(*) FROM user_risk_assessments 
         WHERE DATE(assessment_date) = DATE(NEW.outcome_date) AND risk_level IN ('high', 'critical'))
         FROM career_protection_outcomes 
         WHERE DATE(outcome_date) = DATE(NEW.outcome_date) AND outcome_type = 'successful_transition'),
        'protection_metrics'
    );
END;

-- Update intervention effectiveness on completion
CREATE TRIGGER IF NOT EXISTS update_intervention_effectiveness
AFTER UPDATE OF intervention_status ON risk_interventions
WHEN NEW.intervention_status = 'completed'
BEGIN
    -- Calculate effectiveness score based on outcomes
    UPDATE risk_interventions 
    SET effectiveness_score = (
        SELECT COALESCE(AVG(cpo.satisfaction_score) * 2, 0) + 
               CASE WHEN COUNT(cpo.id) > 0 THEN 2 ELSE 0 END +
               CASE WHEN COUNT(CASE WHEN cpo.outcome_type = 'successful_transition' THEN 1 END) > 0 THEN 3 ELSE 0 END
        FROM career_protection_outcomes cpo 
        WHERE cpo.intervention_id = NEW.id
    )
    WHERE id = NEW.id;
END;

-- Insert default real-time metrics
INSERT OR IGNORE INTO real_time_metrics (metric_name, metric_value, last_updated) VALUES
('active_users', 0, CURRENT_TIMESTAMP),
('total_recommendations_today', 0, CURRENT_TIMESTAMP),
('success_rate_today', 0, CURRENT_TIMESTAMP),
('avg_response_time', 0, CURRENT_TIMESTAMP),
('error_rate', 0, CURRENT_TIMESTAMP),
('career_protection_success_rate', 0, CURRENT_TIMESTAMP),
('high_risk_users_count', 0, CURRENT_TIMESTAMP),
('intervention_effectiveness_rate', 0, CURRENT_TIMESTAMP),
('early_warning_accuracy', 0, CURRENT_TIMESTAMP),
('unemployment_prevention_rate', 0, CURRENT_TIMESTAMP);
