-- Migration: Create Subscription Tier Tables
-- Description: Creates comprehensive tables for subscription tier features including
-- custom categories, category rules, merchant analysis, cash flow forecasts,
-- AI categorization results, subscription tiers, feature usage, and tier upgrades

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create custom_categories table
CREATE TABLE custom_categories (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    category_id VARCHAR(255) NOT NULL UNIQUE,
    user_id INTEGER NOT NULL,
    category_name VARCHAR(100) NOT NULL,
    parent_category VARCHAR(100),
    color VARCHAR(7) NOT NULL DEFAULT '#000000',
    icon VARCHAR(50) NOT NULL DEFAULT 'default',
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Create category_rules table
CREATE TABLE category_rules (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    rule_id VARCHAR(255) NOT NULL UNIQUE,
    category_id VARCHAR(255) NOT NULL,
    user_id INTEGER NOT NULL,
    category_name VARCHAR(100) NOT NULL,
    rule_type VARCHAR(50) NOT NULL,
    rule_conditions JSONB NOT NULL,
    priority INTEGER NOT NULL DEFAULT 1,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    FOREIGN KEY (category_id) REFERENCES custom_categories(category_id) ON DELETE CASCADE
);

-- Create merchant_analyses table
CREATE TABLE merchant_analyses (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    merchant_id VARCHAR(255) NOT NULL UNIQUE,
    user_id INTEGER NOT NULL,
    merchant_name VARCHAR(255) NOT NULL,
    standardized_name VARCHAR(255) NOT NULL,
    merchant_type VARCHAR(100) NOT NULL,
    category VARCHAR(100) NOT NULL,
    subcategory VARCHAR(100),
    total_transactions INTEGER NOT NULL DEFAULT 0,
    total_amount FLOAT NOT NULL DEFAULT 0.0,
    average_amount FLOAT NOT NULL DEFAULT 0.0,
    first_transaction TIMESTAMP WITH TIME ZONE NOT NULL,
    last_transaction TIMESTAMP WITH TIME ZONE NOT NULL,
    spending_frequency FLOAT NOT NULL DEFAULT 0.0,
    spending_consistency FLOAT NOT NULL DEFAULT 0.0,
    seasonal_patterns JSONB,
    merchant_score FLOAT NOT NULL DEFAULT 0.0,
    risk_level VARCHAR(20) NOT NULL DEFAULT 'low',
    fraud_indicators JSONB,
    business_type VARCHAR(100) NOT NULL,
    location VARCHAR(255),
    website VARCHAR(255),
    phone VARCHAR(50),
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Create cash_flow_forecasts table
CREATE TABLE cash_flow_forecasts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    forecast_id VARCHAR(255) NOT NULL UNIQUE,
    user_id INTEGER NOT NULL,
    forecast_period INTEGER NOT NULL,
    start_date TIMESTAMP WITH TIME ZONE NOT NULL,
    end_date TIMESTAMP WITH TIME ZONE NOT NULL,
    monthly_forecasts JSONB NOT NULL,
    confidence_intervals JSONB,
    projected_income FLOAT NOT NULL DEFAULT 0.0,
    income_growth_rate FLOAT NOT NULL DEFAULT 0.0,
    income_volatility FLOAT NOT NULL DEFAULT 0.0,
    projected_expenses FLOAT NOT NULL DEFAULT 0.0,
    expense_growth_rate FLOAT NOT NULL DEFAULT 0.0,
    expense_volatility FLOAT NOT NULL DEFAULT 0.0,
    projected_cash_flow FLOAT NOT NULL DEFAULT 0.0,
    cash_flow_trend VARCHAR(20) NOT NULL DEFAULT 'stable',
    break_even_date TIMESTAMP WITH TIME ZONE,
    model_version VARCHAR(20) NOT NULL DEFAULT '1.0',
    accuracy_score FLOAT NOT NULL DEFAULT 0.0,
    last_updated TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Create ai_categorization_results table
CREATE TABLE ai_categorization_results (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    transaction_id VARCHAR(255) NOT NULL,
    user_id INTEGER NOT NULL,
    original_category VARCHAR(100) NOT NULL,
    ai_category VARCHAR(100) NOT NULL,
    confidence_score FLOAT NOT NULL DEFAULT 0.0,
    categorization_method VARCHAR(50) NOT NULL,
    reasoning TEXT,
    alternatives JSONB,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Create subscription_tiers table
CREATE TABLE subscription_tiers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id INTEGER NOT NULL UNIQUE,
    tier_type VARCHAR(50) NOT NULL,
    tier_name VARCHAR(100) NOT NULL,
    tier_description TEXT,
    features JSONB NOT NULL,
    limits JSONB NOT NULL,
    subscription_id VARCHAR(255),
    billing_cycle VARCHAR(20),
    next_billing_date TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN DEFAULT TRUE,
    trial_end_date TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Create feature_usage table
CREATE TABLE feature_usage (
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

-- Create tier_upgrades table
CREATE TABLE tier_upgrades (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id INTEGER NOT NULL,
    from_tier VARCHAR(50) NOT NULL,
    to_tier VARCHAR(50) NOT NULL,
    upgrade_reason VARCHAR(255),
    upgrade_date TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    effective_date TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    billing_amount FLOAT,
    billing_currency VARCHAR(3) DEFAULT 'USD',
    is_active BOOLEAN DEFAULT TRUE,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Create indexes for custom_categories
CREATE INDEX idx_custom_categories_user_active ON custom_categories(user_id, is_active);
CREATE INDEX idx_custom_categories_name_user ON custom_categories(category_name, user_id);

-- Create indexes for category_rules
CREATE INDEX idx_category_rules_user_active ON category_rules(user_id, is_active);
CREATE INDEX idx_category_rules_type_priority ON category_rules(rule_type, priority);
CREATE INDEX idx_category_rules_category_user ON category_rules(category_id, user_id);

-- Create indexes for merchant_analyses
CREATE INDEX idx_merchant_analyses_user_merchant ON merchant_analyses(user_id, merchant_name);
CREATE INDEX idx_merchant_analyses_score_risk ON merchant_analyses(merchant_score, risk_level);
CREATE INDEX idx_merchant_analyses_type_category ON merchant_analyses(merchant_type, category);
CREATE INDEX idx_merchant_analyses_updated ON merchant_analyses(updated_at, user_id);

-- Create indexes for cash_flow_forecasts
CREATE INDEX idx_cash_flow_forecasts_user_period ON cash_flow_forecasts(user_id, forecast_period);
CREATE INDEX idx_cash_flow_forecasts_trend_accuracy ON cash_flow_forecasts(cash_flow_trend, accuracy_score);
CREATE INDEX idx_cash_flow_forecasts_updated ON cash_flow_forecasts(last_updated, user_id);
CREATE INDEX idx_cash_flow_forecasts_date_range ON cash_flow_forecasts(start_date, end_date);

-- Create indexes for ai_categorization_results
CREATE INDEX idx_ai_categorization_user_transaction ON ai_categorization_results(user_id, transaction_id);
CREATE INDEX idx_ai_categorization_confidence ON ai_categorization_results(confidence_score, created_at);
CREATE INDEX idx_ai_categorization_method ON ai_categorization_results(categorization_method, created_at);
CREATE INDEX idx_ai_categorization_original_ai ON ai_categorization_results(original_category, ai_category);

-- Create indexes for subscription_tiers
CREATE INDEX idx_subscription_tiers_type_active ON subscription_tiers(tier_type, is_active);
CREATE INDEX idx_subscription_tiers_billing ON subscription_tiers(next_billing_date, is_active);
CREATE INDEX idx_subscription_tiers_trial ON subscription_tiers(trial_end_date, is_active);

-- Create indexes for feature_usage
CREATE INDEX idx_feature_usage_user_feature ON feature_usage(user_id, feature_type);
CREATE INDEX idx_feature_usage_period ON feature_usage(period_start, period_end);
CREATE INDEX idx_feature_usage_last_used ON feature_usage(last_used, user_id);

-- Create indexes for tier_upgrades
CREATE INDEX idx_tier_upgrades_user_date ON tier_upgrades(user_id, upgrade_date);
CREATE INDEX idx_tier_upgrades_from_to ON tier_upgrades(from_tier, to_tier);
CREATE INDEX idx_tier_upgrades_active ON tier_upgrades(is_active, user_id);

-- Create triggers for updated_at columns
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_custom_categories_updated_at BEFORE UPDATE ON custom_categories FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_category_rules_updated_at BEFORE UPDATE ON category_rules FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_merchant_analyses_updated_at BEFORE UPDATE ON merchant_analyses FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_cash_flow_forecasts_updated_at BEFORE UPDATE ON cash_flow_forecasts FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_subscription_tiers_updated_at BEFORE UPDATE ON subscription_tiers FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_feature_usage_updated_at BEFORE UPDATE ON feature_usage FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_tier_upgrades_updated_at BEFORE UPDATE ON tier_upgrades FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Create views for common queries
CREATE VIEW user_custom_categories_summary AS
SELECT 
    user_id,
    COUNT(*) as total_categories,
    COUNT(CASE WHEN is_active THEN 1 END) as active_categories,
    COUNT(CASE WHEN parent_category IS NOT NULL THEN 1 END) as subcategories
FROM custom_categories
GROUP BY user_id;

CREATE VIEW user_feature_usage_summary AS
SELECT 
    user_id,
    feature_type,
    SUM(usage_count) as total_usage,
    MAX(last_used) as last_used_date,
    COUNT(*) as usage_periods
FROM feature_usage
GROUP BY user_id, feature_type;

CREATE VIEW merchant_analysis_summary AS
SELECT 
    user_id,
    COUNT(*) as total_merchants,
    AVG(merchant_score) as average_merchant_score,
    COUNT(CASE WHEN risk_level = 'high' THEN 1 END) as high_risk_merchants,
    COUNT(CASE WHEN risk_level = 'medium' THEN 1 END) as medium_risk_merchants,
    COUNT(CASE WHEN risk_level = 'low' THEN 1 END) as low_risk_merchants
FROM merchant_analyses
GROUP BY user_id;

CREATE VIEW cash_flow_forecast_summary AS
SELECT 
    user_id,
    COUNT(*) as total_forecasts,
    AVG(accuracy_score) as average_accuracy,
    MAX(last_updated) as latest_forecast,
    COUNT(CASE WHEN cash_flow_trend = 'increasing' THEN 1 END) as increasing_trends,
    COUNT(CASE WHEN cash_flow_trend = 'decreasing' THEN 1 END) as decreasing_trends,
    COUNT(CASE WHEN cash_flow_trend = 'stable' THEN 1 END) as stable_trends
FROM cash_flow_forecasts
GROUP BY user_id;

-- Create functions for common operations
CREATE OR REPLACE FUNCTION get_user_tier_features(user_id_param INTEGER)
RETURNS TABLE(
    tier_type VARCHAR(50),
    features JSONB,
    limits JSONB
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        st.tier_type,
        st.features,
        st.limits
    FROM subscription_tiers st
    WHERE st.user_id = user_id_param AND st.is_active = TRUE;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION track_feature_usage(
    user_id_param INTEGER,
    feature_type_param VARCHAR(50),
    usage_count_param INTEGER DEFAULT 1
)
RETURNS VOID AS $$
BEGIN
    INSERT INTO feature_usage (
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
        usage_count = feature_usage.usage_count + usage_count_param,
        last_used = NOW(),
        updated_at = NOW();
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION get_user_custom_categories(user_id_param INTEGER)
RETURNS TABLE(
    category_id VARCHAR(255),
    category_name VARCHAR(100),
    parent_category VARCHAR(100),
    color VARCHAR(7),
    icon VARCHAR(50),
    description TEXT,
    rules_count BIGINT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        cc.category_id,
        cc.category_name,
        cc.parent_category,
        cc.color,
        cc.icon,
        cc.description,
        COUNT(cr.id) as rules_count
    FROM custom_categories cc
    LEFT JOIN category_rules cr ON cc.category_id = cr.category_id AND cr.is_active = TRUE
    WHERE cc.user_id = user_id_param AND cc.is_active = TRUE
    GROUP BY cc.id, cc.category_id, cc.category_name, cc.parent_category, cc.color, cc.icon, cc.description;
END;
$$ LANGUAGE plpgsql;

-- Create function to check feature access
CREATE OR REPLACE FUNCTION check_feature_access(
    user_id_param INTEGER,
    feature_type_param VARCHAR(50)
)
RETURNS BOOLEAN AS $$
DECLARE
    has_access BOOLEAN := FALSE;
BEGIN
    SELECT (features->feature_type_param)::BOOLEAN INTO has_access
    FROM subscription_tiers
    WHERE user_id = user_id_param AND is_active = TRUE;
    
    RETURN COALESCE(has_access, FALSE);
END;
$$ LANGUAGE plpgsql;

-- Insert default subscription tier configurations
INSERT INTO subscription_tiers (user_id, tier_type, tier_name, tier_description, features, limits) VALUES
(1, 'professional', 'Professional', 'Full access to all features', 
 '{"ai_categorization": true, "custom_categories": true, "merchant_analysis": true, "cash_flow_forecasting": true, "basic_analytics": true, "standard_categorization": true}',
 '{"max_custom_categories": -1, "max_category_rules": -1, "forecast_months": 24, "merchant_analysis_depth": "advanced"}')
ON CONFLICT (user_id) DO NOTHING;

-- Create comments for documentation
COMMENT ON TABLE custom_categories IS 'Stores user-defined custom categories for transaction classification';
COMMENT ON TABLE category_rules IS 'Stores rules for automatic categorization of transactions into custom categories';
COMMENT ON TABLE merchant_analyses IS 'Stores detailed analysis of merchant spending patterns and risk assessment';
COMMENT ON TABLE cash_flow_forecasts IS 'Stores cash flow forecasting data and projections';
COMMENT ON TABLE ai_categorization_results IS 'Stores results of AI-powered transaction categorization';
COMMENT ON TABLE subscription_tiers IS 'Stores user subscription tier information and feature access';
COMMENT ON TABLE feature_usage IS 'Tracks usage of subscription tier features by users';
COMMENT ON TABLE tier_upgrades IS 'Tracks history of subscription tier upgrades and changes'; 