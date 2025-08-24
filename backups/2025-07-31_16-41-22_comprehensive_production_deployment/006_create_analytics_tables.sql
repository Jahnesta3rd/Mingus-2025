-- Migration: Create Analytics Tables for Transaction Processing
-- Description: Creates comprehensive analytics tables for storing transaction insights,
-- spending patterns, budget alerts, anomaly detections, and financial insights

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create transaction_insights table
CREATE TABLE transaction_insights (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    transaction_id VARCHAR(255) NOT NULL,
    user_id INTEGER NOT NULL,
    account_id VARCHAR(255) NOT NULL,
    
    -- Analysis results
    category VARCHAR(100) NOT NULL,
    confidence FLOAT NOT NULL,
    transaction_type VARCHAR(50) NOT NULL,
    merchant_name VARCHAR(255),
    
    -- Flags
    is_recurring BOOLEAN DEFAULT FALSE,
    is_subscription BOOLEAN DEFAULT FALSE,
    is_anomaly BOOLEAN DEFAULT FALSE,
    
    -- Risk and scoring
    risk_score FLOAT DEFAULT 0.0,
    fraud_score FLOAT DEFAULT 0.0,
    
    -- Additional data
    insights TEXT,
    tags TEXT,
    metadata JSONB,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Create spending_categories table
CREATE TABLE spending_categories (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id INTEGER NOT NULL,
    category_name VARCHAR(100) NOT NULL,
    
    -- Spending statistics
    total_amount FLOAT NOT NULL DEFAULT 0.0,
    transaction_count INTEGER NOT NULL DEFAULT 0,
    average_amount FLOAT NOT NULL DEFAULT 0.0,
    
    -- Trend analysis
    trend_direction VARCHAR(20),
    percentage_change FLOAT,
    trend_period VARCHAR(20),
    
    -- Budget information
    budget_limit FLOAT,
    budget_used FLOAT DEFAULT 0.0,
    budget_percentage FLOAT,
    
    -- Analysis period
    period_start TIMESTAMP WITH TIME ZONE NOT NULL,
    period_end TIMESTAMP WITH TIME ZONE NOT NULL,
    
    -- Recommendations
    recommendations TEXT,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Create budget_alerts table
CREATE TABLE budget_alerts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id INTEGER NOT NULL,
    category_name VARCHAR(100) NOT NULL,
    
    -- Alert details
    alert_type VARCHAR(50) NOT NULL,
    alert_level VARCHAR(20) NOT NULL,
    
    -- Spending information
    current_spending FLOAT NOT NULL,
    budget_limit FLOAT NOT NULL,
    percentage_used FLOAT NOT NULL,
    
    -- Time information
    days_remaining INTEGER,
    alert_date TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    
    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    is_dismissed BOOLEAN DEFAULT FALSE,
    dismissed_at TIMESTAMP WITH TIME ZONE,
    dismissed_by INTEGER,
    
    -- Recommendations
    recommendations TEXT,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Create spending_patterns table
CREATE TABLE spending_patterns (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id INTEGER NOT NULL,
    pattern_type VARCHAR(50) NOT NULL,
    
    -- Pattern details
    category_name VARCHAR(100),
    merchant_name VARCHAR(255),
    
    -- Pattern characteristics
    frequency INTEGER NOT NULL,
    average_amount FLOAT NOT NULL,
    total_amount FLOAT NOT NULL,
    
    -- Timing information
    day_of_week INTEGER,
    day_of_month INTEGER,
    month_of_year INTEGER,
    hour_of_day INTEGER,
    
    -- Confidence and reliability
    confidence_score FLOAT NOT NULL DEFAULT 0.0,
    reliability_score FLOAT NOT NULL DEFAULT 0.0,
    
    -- Pattern metadata
    first_occurrence TIMESTAMP WITH TIME ZONE NOT NULL,
    last_occurrence TIMESTAMP WITH TIME ZONE NOT NULL,
    next_predicted TIMESTAMP WITH TIME ZONE,
    
    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    is_recurring BOOLEAN DEFAULT FALSE,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Create anomaly_detections table
CREATE TABLE anomaly_detections (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id INTEGER NOT NULL,
    transaction_id VARCHAR(255) NOT NULL,
    
    -- Anomaly details
    anomaly_type VARCHAR(50) NOT NULL,
    severity VARCHAR(20) NOT NULL,
    confidence FLOAT NOT NULL DEFAULT 0.0,
    
    -- Anomaly characteristics
    expected_value FLOAT,
    actual_value FLOAT NOT NULL,
    deviation_percentage FLOAT,
    
    -- Context information
    category_name VARCHAR(100),
    merchant_name VARCHAR(255),
    location VARCHAR(255),
    
    -- Analysis details
    detection_method VARCHAR(50) NOT NULL,
    algorithm_version VARCHAR(20),
    
    -- Status
    is_confirmed BOOLEAN DEFAULT FALSE,
    is_false_positive BOOLEAN DEFAULT FALSE,
    user_feedback VARCHAR(50),
    
    -- Timestamps
    detected_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Create subscription_analyses table
CREATE TABLE subscription_analyses (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id INTEGER NOT NULL,
    
    -- Subscription details
    merchant_name VARCHAR(255) NOT NULL,
    subscription_name VARCHAR(255),
    
    -- Financial information
    monthly_cost FLOAT NOT NULL,
    annual_cost FLOAT NOT NULL,
    total_spent FLOAT NOT NULL DEFAULT 0.0,
    
    -- Usage information
    transaction_count INTEGER NOT NULL DEFAULT 0,
    first_transaction TIMESTAMP WITH TIME ZONE NOT NULL,
    last_transaction TIMESTAMP WITH TIME ZONE NOT NULL,
    next_expected TIMESTAMP WITH TIME ZONE,
    
    -- Subscription characteristics
    billing_cycle VARCHAR(20),
    category VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE,
    
    -- Analysis results
    usage_score FLOAT,
    cost_score FLOAT,
    recommendation VARCHAR(50),
    
    -- User feedback
    user_rating INTEGER,
    user_notes TEXT,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Create financial_insights table
CREATE TABLE financial_insights (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id INTEGER NOT NULL,
    
    -- Insight details
    insight_type VARCHAR(50) NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    
    -- Insight data
    data JSONB,
    metrics JSONB,
    
    -- Impact and priority
    impact_score FLOAT NOT NULL DEFAULT 0.0,
    priority VARCHAR(20) NOT NULL DEFAULT 'medium',
    
    -- Actionability
    is_actionable BOOLEAN DEFAULT TRUE,
    action_type VARCHAR(50),
    action_description TEXT,
    
    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    is_dismissed BOOLEAN DEFAULT FALSE,
    dismissed_at TIMESTAMP WITH TIME ZONE,
    
    -- Timestamps
    generated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Create analytics_reports table
CREATE TABLE analytics_reports (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id INTEGER NOT NULL,
    
    -- Report details
    report_type VARCHAR(50) NOT NULL,
    report_name VARCHAR(255) NOT NULL,
    description TEXT,
    
    -- Report period
    period_start TIMESTAMP WITH TIME ZONE NOT NULL,
    period_end TIMESTAMP WITH TIME ZONE NOT NULL,
    
    -- Report data
    data JSONB NOT NULL,
    summary JSONB,
    charts JSONB,
    
    -- Report status
    status VARCHAR(20) NOT NULL DEFAULT 'generated',
    generated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    delivered_at TIMESTAMP WITH TIME ZONE,
    viewed_at TIMESTAMP WITH TIME ZONE,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Create indexes for transaction_insights
CREATE INDEX idx_transaction_insights_user_date ON transaction_insights(user_id, created_at);
CREATE INDEX idx_transaction_insights_category ON transaction_insights(category, created_at);
CREATE INDEX idx_transaction_insights_type ON transaction_insights(transaction_type, created_at);
CREATE INDEX idx_transaction_insights_recurring ON transaction_insights(is_recurring, created_at);
CREATE INDEX idx_transaction_insights_subscription ON transaction_insights(is_subscription, created_at);
CREATE INDEX idx_transaction_insights_transaction_id ON transaction_insights(transaction_id);
CREATE INDEX idx_transaction_insights_account_id ON transaction_insights(account_id);

-- Create indexes for spending_categories
CREATE INDEX idx_spending_categories_user_period ON spending_categories(user_id, period_start, period_end);
CREATE INDEX idx_spending_categories_category_period ON spending_categories(category_name, period_start, period_end);
CREATE INDEX idx_spending_categories_budget ON spending_categories(user_id, budget_percentage);
CREATE INDEX idx_spending_categories_user_category ON spending_categories(user_id, category_name);

-- Create indexes for budget_alerts
CREATE INDEX idx_budget_alerts_user_active ON budget_alerts(user_id, is_active);
CREATE INDEX idx_budget_alerts_category_active ON budget_alerts(category_name, is_active);
CREATE INDEX idx_budget_alerts_level_date ON budget_alerts(alert_level, alert_date);
CREATE INDEX idx_budget_alerts_percentage ON budget_alerts(percentage_used, alert_date);
CREATE INDEX idx_budget_alerts_dismissed ON budget_alerts(is_dismissed, alert_date);

-- Create indexes for spending_patterns
CREATE INDEX idx_spending_patterns_user_type ON spending_patterns(user_id, pattern_type);
CREATE INDEX idx_spending_patterns_category ON spending_patterns(category_name, is_active);
CREATE INDEX idx_spending_patterns_recurring ON spending_patterns(is_recurring, is_active);
CREATE INDEX idx_spending_patterns_timing ON spending_patterns(day_of_week, hour_of_day);
CREATE INDEX idx_spending_patterns_merchant ON spending_patterns(merchant_name, is_active);

-- Create indexes for anomaly_detections
CREATE INDEX idx_anomaly_detections_user_severity ON anomaly_detections(user_id, severity);
CREATE INDEX idx_anomaly_detections_type_severity ON anomaly_detections(anomaly_type, severity);
CREATE INDEX idx_anomaly_detections_confirmed ON anomaly_detections(is_confirmed, detected_at);
CREATE INDEX idx_anomaly_detections_feedback ON anomaly_detections(user_feedback, detected_at);
CREATE INDEX idx_anomaly_detections_transaction_id ON anomaly_detections(transaction_id);

-- Create indexes for subscription_analyses
CREATE INDEX idx_subscription_analyses_user_active ON subscription_analyses(user_id, is_active);
CREATE INDEX idx_subscription_analyses_merchant ON subscription_analyses(merchant_name, is_active);
CREATE INDEX idx_subscription_analyses_cost ON subscription_analyses(monthly_cost, is_active);
CREATE INDEX idx_subscription_analyses_recommendation ON subscription_analyses(recommendation, is_active);
CREATE INDEX idx_subscription_analyses_category ON subscription_analyses(category, is_active);

-- Create indexes for financial_insights
CREATE INDEX idx_financial_insights_user_type ON financial_insights(user_id, insight_type);
CREATE INDEX idx_financial_insights_priority ON financial_insights(priority, impact_score);
CREATE INDEX idx_financial_insights_actionable ON financial_insights(is_actionable, is_active);
CREATE INDEX idx_financial_insights_generated ON financial_insights(generated_at, is_active);
CREATE INDEX idx_financial_insights_dismissed ON financial_insights(is_dismissed, generated_at);

-- Create indexes for analytics_reports
CREATE INDEX idx_analytics_reports_user_type ON analytics_reports(user_id, report_type);
CREATE INDEX idx_analytics_reports_period ON analytics_reports(period_start, period_end);
CREATE INDEX idx_analytics_reports_status ON analytics_reports(status, generated_at);
CREATE INDEX idx_analytics_reports_user_status ON analytics_reports(user_id, status);

-- Create triggers for updated_at timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply updated_at triggers to all tables
CREATE TRIGGER update_transaction_insights_updated_at 
    BEFORE UPDATE ON transaction_insights 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_spending_categories_updated_at 
    BEFORE UPDATE ON spending_categories 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_budget_alerts_updated_at 
    BEFORE UPDATE ON budget_alerts 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_spending_patterns_updated_at 
    BEFORE UPDATE ON spending_patterns 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_anomaly_detections_updated_at 
    BEFORE UPDATE ON anomaly_detections 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_subscription_analyses_updated_at 
    BEFORE UPDATE ON subscription_analyses 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_financial_insights_updated_at 
    BEFORE UPDATE ON financial_insights 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_analytics_reports_updated_at 
    BEFORE UPDATE ON analytics_reports 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Create views for common analytics queries

-- View for user spending summary
CREATE VIEW user_spending_summary AS
SELECT 
    user_id,
    COUNT(*) as total_transactions,
    SUM(CASE WHEN transaction_type = 'expense' THEN ABS(amount) ELSE 0 END) as total_expenses,
    SUM(CASE WHEN transaction_type = 'income' THEN amount ELSE 0 END) as total_income,
    AVG(CASE WHEN transaction_type = 'expense' THEN ABS(amount) ELSE NULL END) as avg_expense,
    AVG(CASE WHEN transaction_type = 'income' THEN amount ELSE NULL END) as avg_income
FROM transaction_insights
GROUP BY user_id;

-- View for category spending breakdown
CREATE VIEW category_spending_breakdown AS
SELECT 
    user_id,
    category,
    COUNT(*) as transaction_count,
    SUM(CASE WHEN transaction_type = 'expense' THEN ABS(amount) ELSE 0 END) as total_spent,
    AVG(CASE WHEN transaction_type = 'expense' THEN ABS(amount) ELSE NULL END) as avg_amount
FROM transaction_insights
WHERE transaction_type = 'expense'
GROUP BY user_id, category;

-- View for active budget alerts
CREATE VIEW active_budget_alerts AS
SELECT 
    ba.*,
    sc.category_name,
    sc.budget_limit,
    sc.budget_used
FROM budget_alerts ba
JOIN spending_categories sc ON ba.user_id = sc.user_id AND ba.category_name = sc.category_name
WHERE ba.is_active = TRUE AND ba.is_dismissed = FALSE;

-- View for subscription summary
CREATE VIEW subscription_summary AS
SELECT 
    user_id,
    COUNT(*) as total_subscriptions,
    SUM(monthly_cost) as total_monthly_cost,
    SUM(annual_cost) as total_annual_cost,
    AVG(usage_score) as avg_usage_score,
    COUNT(CASE WHEN recommendation = 'cancel' THEN 1 END) as recommended_cancellations
FROM subscription_analyses
WHERE is_active = TRUE
GROUP BY user_id;

-- Create functions for analytics operations

-- Function to calculate spending trends
CREATE OR REPLACE FUNCTION calculate_spending_trend(
    p_user_id INTEGER,
    p_category VARCHAR(100),
    p_period_days INTEGER DEFAULT 30
)
RETURNS TABLE(
    trend_direction VARCHAR(20),
    percentage_change FLOAT,
    current_period_amount FLOAT,
    previous_period_amount FLOAT
) AS $$
BEGIN
    RETURN QUERY
    WITH current_period AS (
        SELECT COALESCE(SUM(ABS(amount)), 0) as amount
        FROM transaction_insights
        WHERE user_id = p_user_id 
          AND category = p_category 
          AND transaction_type = 'expense'
          AND created_at >= NOW() - INTERVAL '1 day' * p_period_days
    ),
    previous_period AS (
        SELECT COALESCE(SUM(ABS(amount)), 0) as amount
        FROM transaction_insights
        WHERE user_id = p_user_id 
          AND category = p_category 
          AND transaction_type = 'expense'
          AND created_at >= NOW() - INTERVAL '1 day' * (p_period_days * 2)
          AND created_at < NOW() - INTERVAL '1 day' * p_period_days
    )
    SELECT 
        CASE 
            WHEN cp.amount > pp.amount THEN 'increasing'
            WHEN cp.amount < pp.amount THEN 'decreasing'
            ELSE 'stable'
        END as trend_direction,
        CASE 
            WHEN pp.amount > 0 THEN ((cp.amount - pp.amount) / pp.amount) * 100
            ELSE 0
        END as percentage_change,
        cp.amount as current_period_amount,
        pp.amount as previous_period_amount
    FROM current_period cp, previous_period pp;
END;
$$ LANGUAGE plpgsql;

-- Function to generate budget alerts
CREATE OR REPLACE FUNCTION generate_budget_alerts(p_user_id INTEGER)
RETURNS INTEGER AS $$
DECLARE
    alert_count INTEGER := 0;
    rec RECORD;
BEGIN
    FOR rec IN 
        SELECT 
            sc.category_name,
            sc.total_amount as current_spending,
            sc.budget_limit,
            (sc.total_amount / sc.budget_limit) * 100 as percentage_used
        FROM spending_categories sc
        WHERE sc.user_id = p_user_id 
          AND sc.budget_limit IS NOT NULL
          AND sc.period_end >= NOW() - INTERVAL '1 day'
    LOOP
        -- Check if alert already exists
        IF NOT EXISTS (
            SELECT 1 FROM budget_alerts 
            WHERE user_id = p_user_id 
              AND category_name = rec.category_name
              AND is_active = TRUE
              AND is_dismissed = FALSE
        ) THEN
            -- Generate alert based on percentage used
            IF rec.percentage_used >= 100 THEN
                INSERT INTO budget_alerts (
                    user_id, category_name, alert_type, alert_level,
                    current_spending, budget_limit, percentage_used
                ) VALUES (
                    p_user_id, rec.category_name, 'over_budget', 'critical',
                    rec.current_spending, rec.budget_limit, rec.percentage_used
                );
                alert_count := alert_count + 1;
            ELSIF rec.percentage_used >= 80 THEN
                INSERT INTO budget_alerts (
                    user_id, category_name, alert_type, alert_level,
                    current_spending, budget_limit, percentage_used
                ) VALUES (
                    p_user_id, rec.category_name, 'warning', 'high',
                    rec.current_spending, rec.budget_limit, rec.percentage_used
                );
                alert_count := alert_count + 1;
            ELSIF rec.percentage_used >= 60 THEN
                INSERT INTO budget_alerts (
                    user_id, category_name, alert_type, alert_level,
                    current_spending, budget_limit, percentage_used
                ) VALUES (
                    p_user_id, rec.category_name, 'warning', 'medium',
                    rec.current_spending, rec.budget_limit, rec.percentage_used
                );
                alert_count := alert_count + 1;
            END IF;
        END IF;
    END LOOP;
    
    RETURN alert_count;
END;
$$ LANGUAGE plpgsql;

-- Function to clean up old analytics data
CREATE OR REPLACE FUNCTION cleanup_old_analytics_data(p_days_to_keep INTEGER DEFAULT 365)
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER := 0;
BEGIN
    -- Clean up old transaction insights
    DELETE FROM transaction_insights 
    WHERE created_at < NOW() - INTERVAL '1 day' * p_days_to_keep;
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    
    -- Clean up old anomaly detections
    DELETE FROM anomaly_detections 
    WHERE created_at < NOW() - INTERVAL '1 day' * p_days_to_keep;
    
    -- Clean up old financial insights (keep dismissed ones for shorter period)
    DELETE FROM financial_insights 
    WHERE created_at < NOW() - INTERVAL '1 day' * (p_days_to_keep / 2)
      AND is_dismissed = TRUE;
    
    -- Clean up old analytics reports
    DELETE FROM analytics_reports 
    WHERE created_at < NOW() - INTERVAL '1 day' * p_days_to_keep
      AND status = 'viewed';
    
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Insert migration record
INSERT INTO migrations (version, name, applied_at) 
VALUES ('006', 'Create Analytics Tables for Transaction Processing', NOW()); 