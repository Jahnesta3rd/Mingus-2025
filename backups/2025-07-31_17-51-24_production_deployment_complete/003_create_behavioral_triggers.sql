-- Migration: Create Behavioral Trigger System Tables
-- Date: 2025-01-27
-- Description: Adds intelligent behavioral trigger system for contextual communications

-- Create enum types for behavioral triggers
CREATE TYPE trigger_type AS ENUM (
    'financial_behavior', 'health_wellness', 'career_advancement', 
    'life_event', 'engagement', 'predictive'
);

CREATE TYPE trigger_category AS ENUM (
    'spending_spike', 'income_drop', 'savings_stall', 'milestone_reached',
    'low_exercise_high_spending', 'high_stress_financial', 'relationship_change',
    'job_opportunity', 'skill_gap', 'salary_below_market',
    'birthday_approaching', 'lease_renewal', 'student_loan_grace_ending',
    'app_usage_decline', 'feature_unused', 'premium_upgrade_opportunity'
);

CREATE TYPE trigger_status AS ENUM ('active', 'inactive', 'paused', 'testing');

CREATE TYPE trigger_priority AS ENUM ('critical', 'high', 'medium', 'low');

-- Create behavioral_triggers table
CREATE TABLE behavioral_triggers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Trigger identification
    trigger_name VARCHAR(100) NOT NULL,
    trigger_type trigger_type NOT NULL,
    trigger_category trigger_category NOT NULL,
    
    -- Trigger configuration
    trigger_conditions JSONB NOT NULL, -- Complex conditions for trigger detection
    trigger_thresholds JSONB, -- Threshold values for triggers
    trigger_frequency VARCHAR(20) DEFAULT 'once', -- once, daily, weekly, monthly
    
    -- Communication configuration
    sms_template VARCHAR(200),
    email_template VARCHAR(200),
    communication_delay_minutes INTEGER DEFAULT 0, -- Delay before sending
    
    -- Priority and status
    priority trigger_priority DEFAULT 'medium',
    status trigger_status DEFAULT 'active',
    
    -- Targeting
    target_user_segments JSONB, -- List of user segments
    target_user_tiers JSONB, -- List of user tiers
    exclusion_conditions JSONB, -- Conditions to exclude users
    
    -- Machine learning configuration
    ml_model_enabled BOOLEAN DEFAULT FALSE,
    ml_model_name VARCHAR(100),
    ml_confidence_threshold FLOAT DEFAULT 0.7, -- Minimum confidence for ML triggers
    
    -- Effectiveness tracking
    success_rate FLOAT DEFAULT 0.0, -- Historical success rate
    engagement_rate FLOAT DEFAULT 0.0, -- Historical engagement rate
    conversion_rate FLOAT DEFAULT 0.0, -- Historical conversion rate
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by VARCHAR(36)
);

-- Create trigger_events table
CREATE TABLE trigger_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    trigger_id UUID NOT NULL REFERENCES behavioral_triggers(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Event details
    event_type VARCHAR(50) NOT NULL, -- 'triggered', 'sent', 'engaged', 'converted'
    event_data JSONB, -- Data that caused the trigger
    
    -- Trigger detection
    detection_method VARCHAR(50) NOT NULL, -- 'rule_based', 'ml_model', 'hybrid'
    confidence_score FLOAT DEFAULT 1.0, -- ML confidence score
    trigger_conditions_met JSONB, -- Which conditions were met
    
    -- Communication details
    sms_sent BOOLEAN DEFAULT FALSE,
    email_sent BOOLEAN DEFAULT FALSE,
    sms_message_id VARCHAR(100),
    email_message_id VARCHAR(100),
    
    -- User response
    user_engaged BOOLEAN DEFAULT FALSE,
    engagement_type VARCHAR(50), -- 'sms_click', 'email_open', 'email_click', 'app_action'
    engagement_time_minutes INTEGER, -- Time to engagement
    
    -- Conversion tracking
    conversion_achieved BOOLEAN DEFAULT FALSE,
    conversion_type VARCHAR(50), -- 'goal_set', 'action_taken', 'purchase', 'upgrade'
    conversion_value NUMERIC(10, 2), -- Dollar value of conversion
    
    -- Timing
    triggered_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    sent_at TIMESTAMP WITH TIME ZONE,
    engaged_at TIMESTAMP WITH TIME ZONE,
    converted_at TIMESTAMP WITH TIME ZONE,
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create trigger_effectiveness table
CREATE TABLE trigger_effectiveness (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    trigger_id UUID NOT NULL REFERENCES behavioral_triggers(id) ON DELETE CASCADE,
    
    -- Time period
    period_start TIMESTAMP WITH TIME ZONE NOT NULL,
    period_end TIMESTAMP WITH TIME ZONE NOT NULL,
    period_type VARCHAR(20) NOT NULL, -- 'daily', 'weekly', 'monthly'
    
    -- Effectiveness metrics
    total_triggers INTEGER DEFAULT 0,
    total_sent INTEGER DEFAULT 0,
    total_engaged INTEGER DEFAULT 0,
    total_converted INTEGER DEFAULT 0,
    
    -- Rates
    send_rate FLOAT DEFAULT 0.0, -- percentage of triggers that were sent
    engagement_rate FLOAT DEFAULT 0.0, -- percentage of sent that were engaged
    conversion_rate FLOAT DEFAULT 0.0, -- percentage of engaged that converted
    
    -- Financial impact
    total_conversion_value NUMERIC(12, 2) DEFAULT 0.0,
    avg_conversion_value NUMERIC(10, 2) DEFAULT 0.0,
    roi FLOAT DEFAULT 0.0, -- Return on investment
    
    -- Cost metrics
    total_cost NUMERIC(10, 4) DEFAULT 0.0,
    cost_per_trigger NUMERIC(10, 4) DEFAULT 0.0,
    cost_per_conversion NUMERIC(10, 4) DEFAULT 0.0,
    
    -- User segment breakdown
    segment_breakdown JSONB, -- {segment: {metrics}}
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create user_behavior_patterns table
CREATE TABLE user_behavior_patterns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Pattern identification
    pattern_type VARCHAR(50) NOT NULL, -- 'spending', 'income', 'savings', 'health', 'career'
    pattern_name VARCHAR(100) NOT NULL, -- 'weekly_spending_cycle', 'monthly_income_pattern'
    
    -- Pattern data
    pattern_data JSONB NOT NULL, -- Historical pattern data
    pattern_confidence FLOAT DEFAULT 0.0, -- Confidence in pattern detection
    pattern_last_updated TIMESTAMP WITH TIME ZONE NOT NULL,
    
    -- Pattern characteristics
    baseline_value FLOAT, -- Baseline for comparison
    variance_threshold FLOAT, -- Threshold for anomaly detection
    trend_direction VARCHAR(20), -- 'increasing', 'decreasing', 'stable'
    
    -- Usage tracking
    times_used_for_triggers INTEGER DEFAULT 0,
    last_used_for_trigger TIMESTAMP WITH TIME ZONE,
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create ml_models table
CREATE TABLE ml_models (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Model identification
    model_name VARCHAR(100) NOT NULL,
    model_type VARCHAR(50) NOT NULL, -- 'classification', 'regression', 'clustering'
    model_version VARCHAR(20) NOT NULL,
    
    -- Model configuration
    model_config JSONB NOT NULL, -- Model hyperparameters and configuration
    feature_columns JSONB NOT NULL, -- List of input features
    target_column VARCHAR(50) NOT NULL, -- Target variable
    
    -- Model performance
    accuracy_score FLOAT DEFAULT 0.0,
    precision_score FLOAT DEFAULT 0.0,
    recall_score FLOAT DEFAULT 0.0,
    f1_score FLOAT DEFAULT 0.0,
    
    -- Training information
    training_data_size INTEGER DEFAULT 0,
    training_date TIMESTAMP WITH TIME ZONE NOT NULL,
    training_duration_minutes INTEGER,
    
    -- Model status
    is_active BOOLEAN DEFAULT FALSE,
    is_production BOOLEAN DEFAULT FALSE,
    
    -- Model artifacts
    model_file_path VARCHAR(500), -- Path to saved model
    model_metadata JSONB, -- Additional model metadata
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by VARCHAR(36)
);

-- Create trigger_templates table
CREATE TABLE trigger_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Template identification
    template_name VARCHAR(100) NOT NULL,
    template_type VARCHAR(20) NOT NULL, -- 'sms', 'email', 'push'
    trigger_category trigger_category NOT NULL,
    
    -- Template content
    subject_line VARCHAR(200), -- For emails
    message_content TEXT NOT NULL,
    personalization_variables JSONB, -- Available variables for personalization
    
    -- Template configuration
    character_limit INTEGER, -- For SMS
    call_to_action VARCHAR(100),
    urgency_level VARCHAR(20) DEFAULT 'normal', -- low, normal, high, urgent
    
    -- A/B testing
    is_ab_test_enabled BOOLEAN DEFAULT FALSE,
    ab_test_variants JSONB, -- Different versions for testing
    
    -- Effectiveness
    avg_engagement_rate FLOAT DEFAULT 0.0,
    avg_conversion_rate FLOAT DEFAULT 0.0,
    total_uses INTEGER DEFAULT 0,
    
    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    is_default BOOLEAN DEFAULT FALSE, -- Default template for category
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by VARCHAR(36)
);

-- Create trigger_schedules table
CREATE TABLE trigger_schedules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    trigger_id UUID NOT NULL REFERENCES behavioral_triggers(id) ON DELETE CASCADE,
    
    -- Schedule configuration
    schedule_type VARCHAR(20) NOT NULL, -- 'immediate', 'delayed', 'recurring', 'optimal_time'
    delay_minutes INTEGER DEFAULT 0, -- Delay before sending
    
    -- Time-based scheduling
    optimal_hours JSONB, -- [9, 10, 11, 18, 19, 20] - preferred hours
    optimal_days JSONB, -- [0, 1, 2, 3, 4, 5, 6] - preferred days (0=Monday)
    timezone_aware BOOLEAN DEFAULT TRUE,
    
    -- Frequency limits
    max_triggers_per_day INTEGER DEFAULT 3,
    max_triggers_per_week INTEGER DEFAULT 10,
    max_triggers_per_month INTEGER DEFAULT 30,
    
    -- Cooldown periods
    cooldown_hours INTEGER DEFAULT 24, -- Hours between same trigger
    cooldown_days INTEGER DEFAULT 7, -- Days between same trigger category
    
    -- User-specific scheduling
    respect_user_preferences BOOLEAN DEFAULT TRUE, -- Respect user's preferred times
    adaptive_scheduling BOOLEAN DEFAULT TRUE, -- Learn from user engagement patterns
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX idx_behavioral_triggers_type ON behavioral_triggers(trigger_type);
CREATE INDEX idx_behavioral_triggers_category ON behavioral_triggers(trigger_category);
CREATE INDEX idx_behavioral_triggers_status ON behavioral_triggers(status);
CREATE INDEX idx_behavioral_triggers_priority ON behavioral_triggers(priority);

CREATE INDEX idx_trigger_events_user_id ON trigger_events(user_id);
CREATE INDEX idx_trigger_events_trigger_id ON trigger_events(trigger_id);
CREATE INDEX idx_trigger_events_event_type ON trigger_events(event_type);
CREATE INDEX idx_trigger_events_triggered_at ON trigger_events(triggered_at);
CREATE INDEX idx_trigger_events_user_engaged ON trigger_events(user_engaged);
CREATE INDEX idx_trigger_events_conversion_achieved ON trigger_events(conversion_achieved);

CREATE INDEX idx_trigger_effectiveness_trigger_id ON trigger_effectiveness(trigger_id);
CREATE INDEX idx_trigger_effectiveness_period ON trigger_effectiveness(period_start, period_end);

CREATE INDEX idx_user_behavior_patterns_user_id ON user_behavior_patterns(user_id);
CREATE INDEX idx_user_behavior_patterns_type ON user_behavior_patterns(pattern_type);
CREATE INDEX idx_user_behavior_patterns_confidence ON user_behavior_patterns(pattern_confidence);

CREATE INDEX idx_ml_models_name ON ml_models(model_name);
CREATE INDEX idx_ml_models_type ON ml_models(model_type);
CREATE INDEX idx_ml_models_active ON ml_models(is_active);
CREATE INDEX idx_ml_models_production ON ml_models(is_production);

CREATE INDEX idx_trigger_templates_category ON trigger_templates(trigger_category);
CREATE INDEX idx_trigger_templates_type ON trigger_templates(template_type);
CREATE INDEX idx_trigger_templates_active ON trigger_templates(is_active);

CREATE INDEX idx_trigger_schedules_trigger_id ON trigger_schedules(trigger_id);

-- Create triggers for updated_at timestamps
CREATE TRIGGER update_behavioral_triggers_updated_at 
    BEFORE UPDATE ON behavioral_triggers 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_user_behavior_patterns_updated_at 
    BEFORE UPDATE ON user_behavior_patterns 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_ml_models_updated_at 
    BEFORE UPDATE ON ml_models 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_trigger_templates_updated_at 
    BEFORE UPDATE ON trigger_templates 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_trigger_schedules_updated_at 
    BEFORE UPDATE ON trigger_schedules 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insert default trigger templates
INSERT INTO trigger_templates (
    template_name, template_type, trigger_category, subject_line, message_content, 
    personalization_variables, character_limit, call_to_action, urgency_level, is_default
) VALUES 
    -- Financial behavior triggers
    ('Spending Spike SMS', 'sms', 'spending_spike', NULL, 
     'Hi {{user_name}}, we noticed your spending is {{percentage}}% higher than usual this week. Want to review your budget? Reply YES for insights.',
     '["user_name", "percentage"]', 160, 'Reply YES', 'high', TRUE),
    
    ('Spending Spike Email', 'email', 'spending_spike', 'Spending Alert: {{percentage}}% Increase Detected',
     'Hi {{user_name}},\n\nWe noticed your spending this week is {{percentage}}% higher than your usual pattern. This could impact your savings goals.\n\nKey insights:\n- Top spending categories: {{top_categories}}\n- Potential savings: ${{potential_savings}}\n- Impact on goals: {{goal_impact}}\n\nWould you like us to help you adjust your budget?',
     '["user_name", "percentage", "top_categories", "potential_savings", "goal_impact"]', NULL, 'Review Budget', 'high', TRUE),
    
    ('Income Drop SMS', 'sms', 'income_drop', NULL,
     'Hi {{user_name}}, we noticed a change in your income pattern. Need help adjusting your budget? Reply HELP for guidance.',
     '["user_name"]', 160, 'Reply HELP', 'high', TRUE),
    
    ('Savings Stall SMS', 'sms', 'savings_stall', NULL,
     'Hi {{user_name}}, your savings goal progress has stalled. Want to get back on track? Reply SAVE for personalized tips.',
     '["user_name"]', 160, 'Reply SAVE', 'medium', TRUE),
    
    ('Milestone Reached SMS', 'sms', 'milestone_reached', NULL,
     '🎉 Congrats {{user_name}}! You''ve reached your {{milestone_name}} goal! You''re {{percentage}}% of the way to your next milestone.',
     '["user_name", "milestone_name", "percentage"]', 160, 'View Progress', 'normal', TRUE),
    
    -- Health/wellness triggers
    ('Low Exercise High Spending SMS', 'sms', 'low_exercise_high_spending', NULL,
     'Hi {{user_name}}, we noticed you''ve been less active but spending more. This pattern often indicates stress. Need help finding balance?',
     '["user_name"]', 160, 'Get Tips', 'medium', TRUE),
    
    ('High Stress Financial SMS', 'sms', 'high_stress_financial', NULL,
     'Hi {{user_name}}, stress can impact financial decisions. Take a moment to breathe. We''re here to help you make confident choices.',
     '["user_name"]', 160, 'Get Support', 'high', TRUE),
    
    -- Career triggers
    ('Job Opportunity SMS', 'sms', 'job_opportunity', NULL,
     'Hi {{user_name}}, {{job_count}} new opportunities in {{field}} match your profile. Want to explore? Reply JOBS for details.',
     '["user_name", "job_count", "field"]', 160, 'Reply JOBS', 'high', TRUE),
    
    ('Skill Gap SMS', 'sms', 'skill_gap', NULL,
     'Hi {{user_name}}, developing {{skill_name}} could boost your earning potential by {{percentage}}%. Ready to invest in yourself?',
     '["user_name", "skill_name", "percentage"]', 160, 'Learn More', 'medium', TRUE),
    
    -- Life event triggers
    ('Birthday Approaching SMS', 'sms', 'birthday_approaching', NULL,
     'Hi {{user_name}}, your birthday is in {{days}} days! Want to treat yourself without breaking the bank? Reply BIRTHDAY for budget-friendly ideas.',
     '["user_name", "days"]', 160, 'Reply BIRTHDAY', 'normal', TRUE),
    
    ('Lease Renewal SMS', 'sms', 'lease_renewal', NULL,
     'Hi {{user_name}}, your lease expires in {{days}} days. Want to compare your options? Reply LEASE for a cost analysis.',
     '["user_name", "days"]', 160, 'Reply LEASE', 'high', TRUE),
    
    -- Engagement triggers
    ('App Usage Decline SMS', 'sms', 'app_usage_decline', NULL,
     'Hi {{user_name}}, we miss you! You haven''t checked your finances in {{days}} days. Want to see what you''ve been missing?',
     '["user_name", "days"]', 160, 'Check Now', 'medium', TRUE),
    
    ('Feature Unused SMS', 'sms', 'feature_unused', NULL,
     'Hi {{user_name}}, you haven''t tried {{feature_name}} yet. It could save you ${{potential_savings}}/month. Want to learn more?',
     '["user_name", "feature_name", "potential_savings"]', 160, 'Learn More', 'normal', TRUE),
    
    ('Premium Upgrade SMS', 'sms', 'premium_upgrade_opportunity', NULL,
     'Hi {{user_name}}, upgrade to Premium and unlock {{benefit_count}} exclusive features. Save {{percentage}}% on your first month!',
     '["user_name", "benefit_count", "percentage"]', 160, 'Upgrade Now', 'medium', TRUE);

-- Insert default behavioral triggers
INSERT INTO behavioral_triggers (
    trigger_name, trigger_type, trigger_category, trigger_conditions, trigger_thresholds,
    sms_template, email_template, priority, status
) VALUES 
    ('Spending Spike Detection', 'financial_behavior', 'spending_spike',
     '{"condition": "spending_increase", "timeframe": "7d", "comparison": "baseline"}',
     '{"percentage_increase": 20, "minimum_amount": 100}',
     'Spending Spike SMS', 'Spending Spike Email', 'high', 'active'),
    
    ('Income Drop Detection', 'financial_behavior', 'income_drop',
     '{"condition": "income_decrease", "timeframe": "30d", "comparison": "average"}',
     '{"percentage_decrease": 15, "minimum_amount": 500}',
     'Income Drop SMS', NULL, 'critical', 'active'),
    
    ('Savings Goal Stall', 'financial_behavior', 'savings_stall',
     '{"condition": "savings_no_progress", "timeframe": "14d", "goal_type": "all"}',
     '{"stall_days": 14, "minimum_goal_amount": 100}',
     'Savings Stall SMS', NULL, 'medium', 'active'),
    
    ('Financial Milestone Reached', 'financial_behavior', 'milestone_reached',
     '{"condition": "goal_achieved", "milestone_types": ["savings", "debt_payoff", "investment"]}',
     '{"celebration_threshold": 100}',
     'Milestone Reached SMS', NULL, 'medium', 'active'),
    
    ('Low Exercise High Spending', 'health_wellness', 'low_exercise_high_spending',
     '{"condition": "correlation", "health_metric": "exercise", "financial_metric": "spending"}',
     '{"exercise_threshold": "low", "spending_threshold": "high"}',
     'Low Exercise High Spending SMS', NULL, 'medium', 'active'),
    
    ('High Stress Financial Decision', 'health_wellness', 'high_stress_financial',
     '{"condition": "stress_indicator", "financial_action": "large_purchase"}',
     '{"stress_level": "high", "purchase_amount": 1000}',
     'High Stress Financial SMS', NULL, 'high', 'active'),
    
    ('Job Market Opportunity', 'career_advancement', 'job_opportunity',
     '{"condition": "job_market_scan", "user_field": "current_field", "salary_range": "user_range"}',
     '{"opportunity_count": 3, "salary_increase": 10}',
     'Job Opportunity SMS', NULL, 'high', 'active'),
    
    ('Skill Gap Identified', 'career_advancement', 'skill_gap',
     '{"condition": "skill_analysis", "market_demand": "high", "user_gap": "identified"}',
     '{"skill_demand": "high", "salary_impact": 15}',
     'Skill Gap SMS', NULL, 'medium', 'active'),
    
    ('Birthday Approaching', 'life_event', 'birthday_approaching',
     '{"condition": "birthday_reminder", "days_until": "7"}',
     '{"reminder_days": 7}',
     'Birthday Approaching SMS', NULL, 'low', 'active'),
    
    ('Lease Renewal Period', 'life_event', 'lease_renewal',
     '{"condition": "lease_expiry", "days_until": "30"}',
     '{"reminder_days": 30}',
     'Lease Renewal SMS', NULL, 'high', 'active'),
    
    ('App Usage Decline', 'engagement', 'app_usage_decline',
     '{"condition": "app_inactivity", "days_inactive": "7"}',
     '{"inactivity_days": 7}',
     'App Usage Decline SMS', NULL, 'medium', 'active'),
    
    ('Feature Unused', 'engagement', 'feature_unused',
     '{"condition": "feature_unused", "days_since_signup": "30"}',
     '{"unused_days": 30}',
     'Feature Unused SMS', NULL, 'low', 'active'),
    
    ('Premium Upgrade Opportunity', 'engagement', 'premium_upgrade_opportunity',
     '{"condition": "premium_eligible", "usage_frequency": "high", "feature_usage": "multiple"}',
     '{"usage_threshold": "high", "feature_count": 3}',
     'Premium Upgrade SMS', NULL, 'medium', 'active'); 