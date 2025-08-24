-- Migration: Create Mid-Tier Feature Tables
-- Description: Creates comprehensive tables for Mid-tier subscription features including
-- standard categorization results, spending insights, savings goals, 6-month cash flow forecasts,
-- feature usage tracking, insight preferences, and goal templates

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create standard_categorization_results table
CREATE TABLE standard_categorization_results (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    transaction_id VARCHAR(255) NOT NULL,
    user_id INTEGER NOT NULL,
    original_category VARCHAR(100) NOT NULL,
    suggested_category VARCHAR(100) NOT NULL,
    confidence_score FLOAT NOT NULL DEFAULT 0.0,
    categorization_method VARCHAR(50) NOT NULL,
    reasoning TEXT,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Create spending_insights table
CREATE TABLE spending_insights (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    insight_id VARCHAR(255) NOT NULL UNIQUE,
    user_id INTEGER NOT NULL,
    insight_type VARCHAR(50) NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    data JSONB NOT NULL,
    impact_score FLOAT NOT NULL DEFAULT 0.0,
    priority VARCHAR(20) NOT NULL DEFAULT 'medium',
    is_actionable BOOLEAN DEFAULT TRUE,
    action_description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    is_dismissed BOOLEAN DEFAULT FALSE,
    dismissed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Create savings_goals table
CREATE TABLE savings_goals (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    goal_id VARCHAR(255) NOT NULL UNIQUE,
    user_id INTEGER NOT NULL,
    goal_name VARCHAR(255) NOT NULL,
    goal_type VARCHAR(50) NOT NULL,
    target_amount FLOAT NOT NULL,
    current_amount FLOAT NOT NULL DEFAULT 0.0,
    target_date TIMESTAMP WITH TIME ZONE NOT NULL,
    monthly_target FLOAT NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'not_started',
    progress_percentage FLOAT NOT NULL DEFAULT 0.0,
    description TEXT,
    color VARCHAR(7) DEFAULT '#4ECDC4',
    icon VARCHAR(50) DEFAULT 'target',
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Create savings_goal_progress table
CREATE TABLE savings_goal_progress (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    goal_id VARCHAR(255) NOT NULL,
    user_id INTEGER NOT NULL,
    previous_amount FLOAT NOT NULL,
    new_amount FLOAT NOT NULL,
    amount_change FLOAT NOT NULL,
    progress_percentage FLOAT NOT NULL,
    status VARCHAR(20) NOT NULL,
    update_reason VARCHAR(255),
    update_source VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    FOREIGN KEY (goal_id) REFERENCES savings_goals(goal_id) ON DELETE CASCADE
);

-- Create cash_flow_forecasts_6month table
CREATE TABLE cash_flow_forecasts_6month (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    forecast_id VARCHAR(255) NOT NULL UNIQUE,
    user_id INTEGER NOT NULL,
    forecast_period INTEGER NOT NULL DEFAULT 6,
    start_date TIMESTAMP WITH TIME ZONE NOT NULL,
    end_date TIMESTAMP WITH TIME ZONE NOT NULL,
    monthly_forecasts JSONB NOT NULL,
    projected_income FLOAT NOT NULL DEFAULT 0.0,
    projected_expenses FLOAT NOT NULL DEFAULT 0.0,
    projected_cash_flow FLOAT NOT NULL DEFAULT 0.0,
    cash_flow_trend VARCHAR(20) NOT NULL DEFAULT 'stable',
    model_version VARCHAR(20) NOT NULL DEFAULT '1.0',
    accuracy_score FLOAT NOT NULL DEFAULT 0.0,
    last_updated TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Create mid_tier_feature_usage table
CREATE TABLE mid_tier_feature_usage (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id INTEGER NOT NULL,
    feature_type VARCHAR(50) NOT NULL,
    usage_count INTEGER NOT NULL DEFAULT 0,
    last_used TIMESTAMP WITH TIME ZONE,
    period_start TIMESTAMP WITH TIME ZONE NOT NULL,
    period_end TIMESTAMP WITH TIME ZONE NOT NULL,
    usage_data JSONB,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Create mid_tier_insight_preferences table
CREATE TABLE mid_tier_insight_preferences (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id INTEGER NOT NULL UNIQUE,
    insight_types_enabled JSONB NOT NULL DEFAULT '[]',
    insight_frequency VARCHAR(20) NOT NULL DEFAULT 'weekly',
    max_insights_per_period INTEGER NOT NULL DEFAULT 10,
    email_notifications BOOLEAN DEFAULT TRUE,
    push_notifications BOOLEAN DEFAULT TRUE,
    in_app_notifications BOOLEAN DEFAULT TRUE,
    min_impact_score FLOAT NOT NULL DEFAULT 0.3,
    priority_filter JSONB,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Create mid_tier_goal_templates table
CREATE TABLE mid_tier_goal_templates (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    template_id VARCHAR(255) NOT NULL UNIQUE,
    goal_type VARCHAR(50) NOT NULL,
    template_name VARCHAR(255) NOT NULL,
    description TEXT,
    default_target_amount FLOAT,
    default_duration_months INTEGER,
    default_monthly_target FLOAT,
    category VARCHAR(100),
    difficulty_level VARCHAR(20),
    estimated_impact VARCHAR(20),
    tips JSONB,
    milestones JSONB,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Create indexes for standard_categorization_results
CREATE INDEX idx_standard_categorization_user_transaction ON standard_categorization_results(user_id, transaction_id);
CREATE INDEX idx_standard_categorization_confidence ON standard_categorization_results(confidence_score, created_at);
CREATE INDEX idx_standard_categorization_method ON standard_categorization_results(categorization_method, created_at);
CREATE INDEX idx_standard_categorization_original_suggested ON standard_categorization_results(original_category, suggested_category);

-- Create indexes for spending_insights
CREATE INDEX idx_spending_insights_user_type ON spending_insights(user_id, insight_type);
CREATE INDEX idx_spending_insights_priority_impact ON spending_insights(priority, impact_score);
CREATE INDEX idx_spending_insights_actionable_active ON spending_insights(is_actionable, is_active);
CREATE INDEX idx_spending_insights_created ON spending_insights(created_at, user_id);

-- Create indexes for savings_goals
CREATE INDEX idx_savings_goals_user_status ON savings_goals(user_id, status);
CREATE INDEX idx_savings_goals_type_status ON savings_goals(goal_type, status);
CREATE INDEX idx_savings_goals_progress ON savings_goals(progress_percentage, user_id);
CREATE INDEX idx_savings_goals_target_date ON savings_goals(target_date, user_id);

-- Create indexes for savings_goal_progress
CREATE INDEX idx_savings_goal_progress_goal_date ON savings_goal_progress(goal_id, created_at);
CREATE INDEX idx_savings_goal_progress_user_date ON savings_goal_progress(user_id, created_at);
CREATE INDEX idx_savings_goal_progress_status ON savings_goal_progress(status, created_at);

-- Create indexes for cash_flow_forecasts_6month
CREATE INDEX idx_cash_flow_forecasts_6month_user_date ON cash_flow_forecasts_6month(user_id, created_at);
CREATE INDEX idx_cash_flow_forecasts_6month_trend ON cash_flow_forecasts_6month(cash_flow_trend, accuracy_score);
CREATE INDEX idx_cash_flow_forecasts_6month_period ON cash_flow_forecasts_6month(forecast_period, user_id);

-- Create indexes for mid_tier_feature_usage
CREATE INDEX idx_mid_tier_feature_usage_user_feature ON mid_tier_feature_usage(user_id, feature_type);
CREATE INDEX idx_mid_tier_feature_usage_period ON mid_tier_feature_usage(period_start, period_end);
CREATE INDEX idx_mid_tier_feature_usage_last_used ON mid_tier_feature_usage(last_used, user_id);

-- Create indexes for mid_tier_insight_preferences
CREATE INDEX idx_mid_tier_insight_preferences_user ON mid_tier_insight_preferences(user_id);

-- Create indexes for mid_tier_goal_templates
CREATE INDEX idx_mid_tier_goal_templates_type ON mid_tier_goal_templates(goal_type, difficulty_level);
CREATE INDEX idx_mid_tier_goal_templates_category ON mid_tier_goal_templates(category, estimated_impact);

-- Create triggers for updated_at columns
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_spending_insights_updated_at BEFORE UPDATE ON spending_insights FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_savings_goals_updated_at BEFORE UPDATE ON savings_goals FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_cash_flow_forecasts_6month_updated_at BEFORE UPDATE ON cash_flow_forecasts_6month FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_mid_tier_feature_usage_updated_at BEFORE UPDATE ON mid_tier_feature_usage FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_mid_tier_insight_preferences_updated_at BEFORE UPDATE ON mid_tier_insight_preferences FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_mid_tier_goal_templates_updated_at BEFORE UPDATE ON mid_tier_goal_templates FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Create views for common queries
CREATE VIEW user_spending_insights_summary AS
SELECT 
    user_id,
    COUNT(*) as total_insights,
    COUNT(CASE WHEN is_active THEN 1 END) as active_insights,
    COUNT(CASE WHEN is_dismissed THEN 1 END) as dismissed_insights,
    AVG(impact_score) as average_impact_score,
    COUNT(CASE WHEN is_actionable THEN 1 END) as actionable_insights
FROM spending_insights
GROUP BY user_id;

CREATE VIEW user_savings_goals_summary AS
SELECT 
    user_id,
    COUNT(*) as total_goals,
    COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed_goals,
    COUNT(CASE WHEN status = 'on_track' THEN 1 END) as on_track_goals,
    COUNT(CASE WHEN status = 'behind' THEN 1 END) as behind_goals,
    SUM(target_amount) as total_target_amount,
    SUM(current_amount) as total_current_amount,
    AVG(progress_percentage) as average_progress
FROM savings_goals
GROUP BY user_id;

CREATE VIEW mid_tier_feature_usage_summary AS
SELECT 
    user_id,
    feature_type,
    SUM(usage_count) as total_usage,
    MAX(last_used) as last_used_date,
    COUNT(*) as usage_periods
FROM mid_tier_feature_usage
GROUP BY user_id, feature_type;

-- Create functions for common operations
CREATE OR REPLACE FUNCTION get_user_mid_tier_features(user_id_param INTEGER)
RETURNS TABLE(
    feature_type VARCHAR(50),
    usage_count BIGINT,
    last_used TIMESTAMP WITH TIME ZONE
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        mfu.feature_type,
        SUM(mfu.usage_count) as usage_count,
        MAX(mfu.last_used) as last_used
    FROM mid_tier_feature_usage mfu
    WHERE mfu.user_id = user_id_param
    GROUP BY mfu.feature_type;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION track_mid_tier_feature_usage(
    user_id_param INTEGER,
    feature_type_param VARCHAR(50),
    usage_count_param INTEGER DEFAULT 1
)
RETURNS VOID AS $$
BEGIN
    INSERT INTO mid_tier_feature_usage (
        user_id, 
        feature_type, 
        usage_count, 
        last_used, 
        period_start, 
        period_end
    ) VALUES (
        user_id_param,
        feature_type_param,
        usage_count_param,
        NOW(),
        DATE_TRUNC('month', NOW()),
        DATE_TRUNC('month', NOW()) + INTERVAL '1 month' - INTERVAL '1 day'
    )
    ON CONFLICT (user_id, feature_type, period_start)
    DO UPDATE SET
        usage_count = mid_tier_feature_usage.usage_count + usage_count_param,
        last_used = NOW(),
        updated_at = NOW();
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION get_user_savings_goals(user_id_param INTEGER)
RETURNS TABLE(
    goal_id VARCHAR(255),
    goal_name VARCHAR(255),
    goal_type VARCHAR(50),
    target_amount FLOAT,
    current_amount FLOAT,
    progress_percentage FLOAT,
    status VARCHAR(20)
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        sg.goal_id,
        sg.goal_name,
        sg.goal_type,
        sg.target_amount,
        sg.current_amount,
        sg.progress_percentage,
        sg.status
    FROM savings_goals sg
    WHERE sg.user_id = user_id_param;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION update_savings_goal_progress(
    goal_id_param VARCHAR(255),
    new_amount_param FLOAT
)
RETURNS VOID AS $$
DECLARE
    current_amount_val FLOAT;
    user_id_val INTEGER;
BEGIN
    -- Get current amount and user_id
    SELECT current_amount, user_id INTO current_amount_val, user_id_val
    FROM savings_goals
    WHERE goal_id = goal_id_param;
    
    -- Insert progress record
    INSERT INTO savings_goal_progress (
        goal_id,
        user_id,
        previous_amount,
        new_amount,
        amount_change,
        progress_percentage,
        status,
        update_source
    ) VALUES (
        goal_id_param,
        user_id_val,
        current_amount_val,
        new_amount_param,
        new_amount_param - current_amount_val,
        (new_amount_param / (SELECT target_amount FROM savings_goals WHERE goal_id = goal_id_param)) * 100,
        'updated',
        'manual'
    );
    
    -- Update goal
    UPDATE savings_goals
    SET 
        current_amount = new_amount_param,
        progress_percentage = (new_amount_param / target_amount) * 100,
        updated_at = NOW()
    WHERE goal_id = goal_id_param;
END;
$$ LANGUAGE plpgsql;

-- Insert default goal templates
INSERT INTO mid_tier_goal_templates (template_id, goal_type, template_name, description, default_target_amount, default_duration_months, default_monthly_target, category, difficulty_level, estimated_impact, tips, milestones) VALUES
('emergency_fund_template', 'emergency_fund', 'Emergency Fund', 'Build a safety net for unexpected expenses', 10000.0, 12, 833.33, 'savings', 'medium', 'high', 
 '["Start with a small goal like $1,000", "Set up automatic transfers", "Use windfalls like tax refunds"]',
 '{"1000": "Initial emergency fund", "3000": "Basic emergency fund", "10000": "Full emergency fund"}'),
('vacation_template', 'vacation', 'Vacation Fund', 'Save for your dream vacation', 5000.0, 10, 500.0, 'lifestyle', 'easy', 'medium',
 '["Research destination costs", "Include travel insurance", "Plan for daily expenses"]',
 '{"1000": "Flight tickets", "2500": "Accommodation", "5000": "Complete vacation"}'),
('down_payment_template', 'down_payment', 'Home Down Payment', 'Save for a home down payment', 50000.0, 60, 833.33, 'investment', 'hard', 'high',
 '["Research home prices in your area", "Aim for 20% down payment", "Consider closing costs"]',
 '{"10000": "Initial savings", "25000": "Halfway there", "50000": "Ready to buy"}'),
('retirement_template', 'retirement', 'Retirement Savings', 'Build your retirement nest egg', 100000.0, 120, 833.33, 'investment', 'hard', 'high',
 '["Start early for compound interest", "Consider employer matching", "Diversify your investments"]',
 '{"10000": "Initial retirement fund", "50000": "Growing nest egg", "100000": "Solid foundation"}'),
('education_template', 'education', 'Education Fund', 'Save for education expenses', 25000.0, 48, 520.83, 'education', 'medium', 'high',
 '["Research education costs", "Consider scholarships and grants", "Plan for additional expenses"]',
 '{"5000": "Initial education fund", "15000": "Growing education fund", "25000": "Ready for education"}');

-- Insert default insight preferences for new users
INSERT INTO mid_tier_insight_preferences (user_id, insight_types_enabled, insight_frequency, max_insights_per_period, min_impact_score, priority_filter) VALUES
(1, '["spending_trend", "category_breakdown", "unusual_spending", "recurring_expenses", "savings_opportunity"]', 'weekly', 10, 0.3, '["high", "medium"]');

-- Create comments for documentation
COMMENT ON TABLE standard_categorization_results IS 'Stores results of standard categorization for Mid-tier users';
COMMENT ON TABLE spending_insights IS 'Stores basic spending insights generated for Mid-tier users';
COMMENT ON TABLE savings_goals IS 'Stores savings goals and progress for Mid-tier users';
COMMENT ON TABLE savings_goal_progress IS 'Tracks history of savings goal progress updates';
COMMENT ON TABLE cash_flow_forecasts_6month IS 'Stores 6-month cash flow forecasts for Mid-tier users';
COMMENT ON TABLE mid_tier_feature_usage IS 'Tracks usage of Mid-tier features by users';
COMMENT ON TABLE mid_tier_insight_preferences IS 'Stores user preferences for Mid-tier insights';
COMMENT ON TABLE mid_tier_goal_templates IS 'Stores templates for creating savings goals'; 