-- Risk Analytics Database Schema
-- This schema extends the existing analytics system with risk-based career protection tracking

-- Risk assessments table
CREATE TABLE IF NOT EXISTS risk_assessments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    assessment_type TEXT NOT NULL, -- 'ai_risk', 'layoff_risk', 'income_risk'
    overall_risk REAL NOT NULL, -- 0.0 to 1.0
    risk_triggers TEXT NOT NULL, -- JSON array of risk factors
    risk_breakdown TEXT NOT NULL, -- JSON object with detailed risk analysis
    timeline_urgency TEXT NOT NULL, -- 'immediate', '3_months', '6_months', '1_year'
    assessment_timestamp DATETIME NOT NULL,
    confidence_score REAL NOT NULL, -- 0.0 to 1.0
    risk_factors TEXT NOT NULL, -- JSON object with factor scores
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_risk_assessments_user_id (user_id),
    INDEX idx_risk_assessments_type (assessment_type),
    INDEX idx_risk_assessments_risk_level (overall_risk),
    INDEX idx_risk_assessments_timestamp (assessment_timestamp)
);

-- Risk recommendations table
CREATE TABLE IF NOT EXISTS risk_recommendations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    trigger_type TEXT NOT NULL, -- 'risk_assessment', 'threshold_breach', 'manual_trigger'
    risk_score REAL NOT NULL,
    recommendations_generated INTEGER NOT NULL,
    recommendation_tiers TEXT NOT NULL, -- JSON array of tiers
    emergency_unlock_granted BOOLEAN NOT NULL,
    timeline_urgency TEXT NOT NULL,
    intervention_timestamp DATETIME NOT NULL,
    success_probability REAL NOT NULL, -- 0.0 to 1.0
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_risk_recommendations_user_id (user_id),
    INDEX idx_risk_recommendations_trigger (trigger_type),
    INDEX idx_risk_recommendations_risk_score (risk_score),
    INDEX idx_risk_recommendations_timestamp (intervention_timestamp)
);

-- Risk outcomes table
CREATE TABLE IF NOT EXISTS risk_outcomes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    predicted_risk_score REAL NOT NULL,
    predicted_timeline TEXT NOT NULL,
    actual_outcome TEXT NOT NULL, -- 'laid_off', 'job_saved', 'proactive_switch', etc.
    outcome_timeline_days INTEGER NOT NULL,
    prediction_accuracy REAL NOT NULL, -- 0.0 to 1.0
    outcome_timestamp DATETIME NOT NULL,
    outcome_details TEXT NOT NULL, -- JSON object with detailed outcome data
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_risk_outcomes_user_id (user_id),
    INDEX idx_risk_outcomes_accuracy (prediction_accuracy),
    INDEX idx_risk_outcomes_outcome (actual_outcome),
    INDEX idx_risk_outcomes_timestamp (outcome_timestamp)
);

-- Risk journey flow table
CREATE TABLE IF NOT EXISTS risk_journey_flow (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    session_id TEXT NOT NULL,
    flow_step TEXT NOT NULL, -- 'risk_detected', 'assessment_completed', 'recommendation_generated', etc.
    step_timestamp DATETIME NOT NULL,
    step_data TEXT NOT NULL, -- JSON object with step-specific data
    time_to_next_step INTEGER, -- seconds to next step
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_risk_journey_user_id (user_id),
    INDEX idx_risk_journey_session (session_id),
    INDEX idx_risk_journey_step (flow_step),
    INDEX idx_risk_journey_timestamp (step_timestamp)
);

-- Risk A/B test results table
CREATE TABLE IF NOT EXISTS risk_ab_test_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    test_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    variant_id TEXT NOT NULL,
    risk_threshold REAL NOT NULL,
    recommendation_timing TEXT NOT NULL, -- 'immediate', 'delayed_24h', 'delayed_48h'
    user_response TEXT NOT NULL, -- 'pending', 'accepted', 'rejected', 'ignored'
    outcome_achieved TEXT, -- 'success', 'failure', 'partial'
    test_timestamp DATETIME NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_risk_ab_test_id (test_id),
    INDEX idx_risk_ab_user_id (user_id),
    INDEX idx_risk_ab_variant (variant_id),
    INDEX idx_risk_ab_timestamp (test_timestamp)
);

-- Risk A/B tests table
CREATE TABLE IF NOT EXISTS risk_ab_tests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    test_id TEXT UNIQUE NOT NULL,
    test_name TEXT NOT NULL,
    test_type TEXT NOT NULL, -- 'risk_threshold', 'recommendation_timing', 'communication_style'
    description TEXT NOT NULL,
    hypothesis TEXT NOT NULL,
    risk_threshold_variants TEXT NOT NULL, -- JSON array of threshold values
    recommendation_timing_variants TEXT NOT NULL, -- JSON array of timing options
    success_metrics TEXT NOT NULL, -- JSON array of metrics to track
    status TEXT NOT NULL, -- 'active', 'paused', 'completed', 'cancelled'
    start_date DATETIME NOT NULL,
    end_date DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_risk_ab_tests_test_id (test_id),
    INDEX idx_risk_ab_tests_status (status),
    INDEX idx_risk_ab_tests_type (test_type)
);

-- Career protection outcomes table
CREATE TABLE IF NOT EXISTS career_protection_outcomes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    outcome_type TEXT NOT NULL, -- 'laid_off', 'job_saved', 'proactive_switch', 'promotion_received'
    risk_prediction_accuracy REAL NOT NULL,
    time_to_outcome_days INTEGER NOT NULL,
    salary_impact REAL, -- positive or negative salary change
    career_advancement_score REAL NOT NULL, -- 0.0 to 1.0
    skills_improvement_score REAL NOT NULL, -- 0.0 to 1.0
    network_expansion_score REAL NOT NULL, -- 0.0 to 1.0
    outcome_timestamp DATETIME NOT NULL,
    success_factors TEXT NOT NULL, -- JSON object with factors that led to success
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_career_protection_user_id (user_id),
    INDEX idx_career_protection_outcome (outcome_type),
    INDEX idx_career_protection_accuracy (risk_prediction_accuracy),
    INDEX idx_career_protection_timestamp (outcome_timestamp)
);

-- Early warning effectiveness table
CREATE TABLE IF NOT EXISTS early_warning_effectiveness (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    warning_timestamp DATETIME NOT NULL,
    warning_accuracy REAL NOT NULL, -- 0.0 to 1.0
    advance_notice_days INTEGER NOT NULL,
    user_response_time_hours INTEGER, -- hours from warning to user action
    proactive_action_taken BOOLEAN NOT NULL,
    outcome_improvement REAL, -- improvement in outcome due to early warning
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_early_warning_user_id (user_id),
    INDEX idx_early_warning_accuracy (warning_accuracy),
    INDEX idx_early_warning_timestamp (warning_timestamp),
    INDEX idx_early_warning_proactive (proactive_action_taken)
);

-- Risk communication effectiveness table
CREATE TABLE IF NOT EXISTS risk_communication_effectiveness (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    communication_type TEXT NOT NULL, -- 'email', 'in_app', 'push_notification', 'sms'
    message_clarity_score REAL NOT NULL, -- 0.0 to 1.0
    user_understanding_score REAL NOT NULL, -- 0.0 to 1.0
    action_taken BOOLEAN NOT NULL,
    time_to_action_hours INTEGER, -- hours from communication to action
    communication_timestamp DATETIME NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_risk_comm_user_id (user_id),
    INDEX idx_risk_comm_type (communication_type),
    INDEX idx_risk_comm_clarity (message_clarity_score),
    INDEX idx_risk_comm_action (action_taken),
    INDEX idx_risk_comm_timestamp (communication_timestamp)
);

-- Risk threshold optimization table
CREATE TABLE IF NOT EXISTS risk_threshold_optimization (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    original_threshold REAL NOT NULL,
    optimized_threshold REAL NOT NULL,
    improvement_percentage REAL NOT NULL,
    test_duration_days INTEGER NOT NULL,
    test_results TEXT NOT NULL, -- JSON object with detailed test results
    optimization_timestamp DATETIME NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_risk_threshold_user_id (user_id),
    INDEX idx_risk_threshold_improvement (improvement_percentage),
    INDEX idx_risk_threshold_timestamp (optimization_timestamp)
);

-- Risk alert fatigue tracking table
CREATE TABLE IF NOT EXISTS risk_alert_fatigue (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    alert_frequency_per_week REAL NOT NULL,
    user_response_rate REAL NOT NULL, -- 0.0 to 1.0
    fatigue_score REAL NOT NULL, -- 0.0 to 1.0 (higher = more fatigued)
    optimal_frequency REAL NOT NULL, -- calculated optimal frequency
    last_alert_timestamp DATETIME NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_alert_fatigue_user_id (user_id),
    INDEX idx_alert_fatigue_score (fatigue_score),
    INDEX idx_alert_fatigue_timestamp (last_alert_timestamp)
);

-- Risk dashboard metrics table (for caching dashboard data)
CREATE TABLE IF NOT EXISTS risk_dashboard_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    metric_name TEXT NOT NULL,
    metric_value REAL NOT NULL,
    metric_data TEXT NOT NULL, -- JSON object with detailed metric data
    calculation_timestamp DATETIME NOT NULL,
    expires_at DATETIME NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_dashboard_metric_name (metric_name),
    INDEX idx_dashboard_timestamp (calculation_timestamp),
    INDEX idx_dashboard_expires (expires_at)
);

-- Risk model performance table
CREATE TABLE IF NOT EXISTS risk_model_performance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    model_version TEXT NOT NULL,
    accuracy_score REAL NOT NULL,
    precision_score REAL NOT NULL,
    recall_score REAL NOT NULL,
    f1_score REAL NOT NULL,
    test_data_size INTEGER NOT NULL,
    training_timestamp DATETIME NOT NULL,
    performance_timestamp DATETIME NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_model_performance_version (model_version),
    INDEX idx_model_performance_accuracy (accuracy_score),
    INDEX idx_model_performance_timestamp (performance_timestamp)
);

-- Risk user segments table
CREATE TABLE IF NOT EXISTS risk_user_segments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    segment_name TEXT NOT NULL, -- 'high_risk_high_engagement', 'low_risk_low_engagement', etc.
    risk_profile TEXT NOT NULL, -- JSON object with risk characteristics
    engagement_level TEXT NOT NULL, -- 'high', 'medium', 'low'
    segment_timestamp DATETIME NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_user_segments_user_id (user_id),
    INDEX idx_user_segments_segment (segment_name),
    INDEX idx_user_segments_engagement (engagement_level),
    INDEX idx_user_segments_timestamp (segment_timestamp)
);

-- Risk triggered recommendations table (specific extension)
CREATE TABLE IF NOT EXISTS risk_triggered_recommendations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    risk_assessment_id INTEGER NOT NULL,
    recommendation_id INTEGER NOT NULL,
    trigger_risk_score REAL NOT NULL,
    trigger_timestamp DATETIME NOT NULL,
    recommendation_tier TEXT NOT NULL, -- 'optimal', 'safe', 'stretch'
    success_probability REAL NOT NULL,
    application_generated BOOLEAN DEFAULT FALSE,
    application_timestamp DATETIME,
    outcome_achieved TEXT, -- 'success', 'failure', 'pending'
    outcome_timestamp DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (risk_assessment_id) REFERENCES risk_assessments(id),
    FOREIGN KEY (recommendation_id) REFERENCES recommendations(id),
    INDEX idx_risk_triggered_risk_assessment (risk_assessment_id),
    INDEX idx_risk_triggered_recommendation (recommendation_id),
    INDEX idx_risk_triggered_risk_score (trigger_risk_score),
    INDEX idx_risk_triggered_timestamp (trigger_timestamp)
);

-- Risk prediction accuracy table (specific extension)
CREATE TABLE IF NOT EXISTS risk_prediction_accuracy (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    prediction_id TEXT NOT NULL,
    predicted_risk_score REAL NOT NULL,
    predicted_timeline_days INTEGER NOT NULL,
    predicted_outcome TEXT NOT NULL,
    actual_risk_score REAL,
    actual_timeline_days INTEGER,
    actual_outcome TEXT,
    accuracy_score REAL NOT NULL, -- 0.0 to 1.0
    prediction_timestamp DATETIME NOT NULL,
    validation_timestamp DATETIME,
    model_version TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_prediction_accuracy_user_id (user_id),
    INDEX idx_prediction_accuracy_prediction_id (prediction_id),
    INDEX idx_prediction_accuracy_score (accuracy_score),
    INDEX idx_prediction_accuracy_timestamp (prediction_timestamp)
);

-- Career protection outcomes table (specific extension)
CREATE TABLE IF NOT EXISTS career_protection_outcomes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    risk_assessment_id INTEGER NOT NULL,
    outcome_type TEXT NOT NULL, -- 'proactive_switch', 'job_saved', 'laid_off', 'promotion'
    transition_success BOOLEAN NOT NULL,
    salary_protection_amount REAL,
    salary_improvement_percentage REAL,
    time_to_transition_days INTEGER,
    advance_notice_days INTEGER, -- How much advance warning was given
    risk_mitigation_effectiveness REAL, -- 0.0 to 1.0
    outcome_timestamp DATETIME NOT NULL,
    success_factors TEXT NOT NULL, -- JSON array of success factors
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (risk_assessment_id) REFERENCES risk_assessments(id),
    INDEX idx_career_protection_user_id (user_id),
    INDEX idx_career_protection_outcome (outcome_type),
    INDEX idx_career_protection_success (transition_success),
    INDEX idx_career_protection_timestamp (outcome_timestamp)
);

-- Risk A/B test results table (specific extension)
CREATE TABLE IF NOT EXISTS risk_ab_test_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    test_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    variant_id TEXT NOT NULL,
    risk_threshold REAL NOT NULL,
    recommendation_timing TEXT NOT NULL, -- 'immediate', 'delayed_24h', 'delayed_48h'
    user_response TEXT NOT NULL, -- 'pending', 'accepted', 'rejected', 'ignored'
    application_generated BOOLEAN DEFAULT FALSE,
    outcome_achieved TEXT, -- 'success', 'failure', 'partial'
    conversion_time_hours INTEGER,
    test_timestamp DATETIME NOT NULL,
    outcome_timestamp DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_risk_ab_test_id (test_id),
    INDEX idx_risk_ab_user_id (user_id),
    INDEX idx_risk_ab_variant (variant_id),
    INDEX idx_risk_ab_timestamp (test_timestamp)
);

-- Risk A/B test configurations table
CREATE TABLE IF NOT EXISTS risk_ab_test_configs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    test_id TEXT UNIQUE NOT NULL,
    test_name TEXT NOT NULL,
    test_type TEXT NOT NULL,
    description TEXT NOT NULL,
    hypothesis TEXT NOT NULL,
    variants_config TEXT NOT NULL,
    success_criteria TEXT NOT NULL,
    target_participants INTEGER NOT NULL,
    test_duration_days INTEGER NOT NULL,
    minimum_risk_users_per_variant INTEGER NOT NULL,
    risk_score_range TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'draft',
    start_date DATETIME,
    end_date DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_risk_ab_configs_test_id (test_id),
    INDEX idx_risk_ab_configs_type (test_type),
    INDEX idx_risk_ab_configs_status (status)
);

-- Risk A/B test participants table
CREATE TABLE IF NOT EXISTS risk_ab_test_participants (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    test_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    variant_id TEXT NOT NULL,
    risk_score REAL NOT NULL,
    risk_level TEXT NOT NULL,
    assigned_at DATETIME NOT NULL,
    last_activity DATETIME,
    conversion_events TEXT,
    outcome_data TEXT,
    
    UNIQUE(test_id, user_id),
    INDEX idx_risk_participants_test_id (test_id),
    INDEX idx_risk_participants_user_id (user_id),
    INDEX idx_risk_participants_variant (variant_id),
    INDEX idx_risk_participants_risk_score (risk_score)
);

-- Risk A/B test outcomes table
CREATE TABLE IF NOT EXISTS risk_ab_test_outcomes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    test_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    variant_id TEXT NOT NULL,
    outcome_type TEXT NOT NULL,
    outcome_value REAL NOT NULL,
    outcome_timestamp DATETIME NOT NULL,
    success_metrics TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_risk_outcomes_test_id (test_id),
    INDEX idx_risk_outcomes_user_id (user_id),
    INDEX idx_risk_outcomes_variant (variant_id),
    INDEX idx_risk_outcomes_type (outcome_type)
);

-- Risk optimization history table
CREATE TABLE IF NOT EXISTS risk_optimization_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    test_id TEXT NOT NULL,
    optimization_type TEXT NOT NULL,
    original_value REAL NOT NULL,
    optimized_value REAL NOT NULL,
    improvement_percentage REAL NOT NULL,
    confidence_level REAL NOT NULL,
    optimization_timestamp DATETIME NOT NULL,
    test_results TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_risk_optimization_test_id (test_id),
    INDEX idx_risk_optimization_type (optimization_type),
    INDEX idx_risk_optimization_timestamp (optimization_timestamp)
);
