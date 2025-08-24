-- =============================================================================
-- MINGUS Personal Finance Application - Unified PostgreSQL Schema
-- =============================================================================
-- 
-- This schema consolidates all MINGUS databases into a unified PostgreSQL
-- database designed for African American professionals seeking financial wellness.
--
-- Features:
-- - UUID primary keys for security and scalability
-- - JSONB for flexible data storage
-- - Proper foreign key relationships
-- - Timestamps with timezone awareness
-- - Decimal types for financial precision
-- - Comprehensive constraints and indexes
-- - Subscription and billing management
-- - Feature access control
-- - Health and career tracking
-- - Analytics and performance monitoring
--
-- Author: MINGUS Development Team
-- Date: January 2025
-- Version: 1.0
-- =============================================================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- =============================================================================
-- USER MANAGEMENT TABLES
-- =============================================================================

-- Core users table
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT true,
    is_verified BOOLEAN DEFAULT false,
    email_verification_token UUID,
    password_reset_token UUID,
    password_reset_expires_at TIMESTAMP WITH TIME ZONE,
    last_login_at TIMESTAMP WITH TIME ZONE,
    login_attempts INTEGER DEFAULT 0,
    locked_until TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- User profiles with enhanced demographic data
CREATE TABLE user_profiles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    date_of_birth DATE,
    gender VARCHAR(20),
    phone_number VARCHAR(20),
    address_line_1 VARCHAR(255),
    address_line_2 VARCHAR(255),
    city VARCHAR(100),
    state VARCHAR(50),
    zip_code VARCHAR(10) NOT NULL,
    country VARCHAR(100) DEFAULT 'USA',
    timezone VARCHAR(50) DEFAULT 'America/New_York',
    dependents INTEGER DEFAULT 0,
    marital_status VARCHAR(20),
    household_size INTEGER DEFAULT 1,
    annual_income DECIMAL(12,2),
    income_source VARCHAR(100),
    employment_status VARCHAR(50),
    education_level VARCHAR(50),
    occupation VARCHAR(100),
    industry VARCHAR(100),
    years_of_experience INTEGER,
    company_name VARCHAR(255),
    company_size VARCHAR(50),
    job_title VARCHAR(100),
    naics_code VARCHAR(10),
    risk_tolerance VARCHAR(20) DEFAULT 'moderate',
    financial_goals JSONB,
    preferences JSONB,
    profile_completion_percentage INTEGER DEFAULT 0,
    onboarding_completed BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Onboarding progress tracking
CREATE TABLE onboarding_progress (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    step_name VARCHAR(100) NOT NULL,
    step_order INTEGER NOT NULL,
    is_completed BOOLEAN DEFAULT false,
    completed_at TIMESTAMP WITH TIME ZONE,
    step_data JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, step_name)
);

-- =============================================================================
-- SUBSCRIPTION AND BILLING SYSTEM
-- =============================================================================

-- Subscription plans
CREATE TABLE subscription_plans (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL,
    description TEXT,
    price DECIMAL(10,2) NOT NULL,
    billing_cycle VARCHAR(20) NOT NULL, -- monthly, yearly
    features JSONB NOT NULL,
    limits JSONB, -- usage limits for features
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- User subscriptions
CREATE TABLE subscriptions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    plan_id UUID NOT NULL REFERENCES subscription_plans(id),
    stripe_subscription_id VARCHAR(255) UNIQUE,
    stripe_customer_id VARCHAR(255),
    status VARCHAR(50) NOT NULL, -- active, canceled, past_due, unpaid
    current_period_start TIMESTAMP WITH TIME ZONE,
    current_period_end TIMESTAMP WITH TIME ZONE,
    cancel_at_period_end BOOLEAN DEFAULT false,
    canceled_at TIMESTAMP WITH TIME ZONE,
    trial_start TIMESTAMP WITH TIME ZONE,
    trial_end TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Feature access control
CREATE TABLE feature_access (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    feature_name VARCHAR(100) NOT NULL,
    is_enabled BOOLEAN DEFAULT true,
    usage_count INTEGER DEFAULT 0,
    usage_limit INTEGER,
    last_used_at TIMESTAMP WITH TIME ZONE,
    expires_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, feature_name)
);

-- Billing history
CREATE TABLE billing_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    subscription_id UUID REFERENCES subscriptions(id),
    stripe_invoice_id VARCHAR(255) UNIQUE,
    amount DECIMAL(10,2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'USD',
    status VARCHAR(50) NOT NULL, -- paid, unpaid, void, pending
    billing_date TIMESTAMP WITH TIME ZONE NOT NULL,
    due_date TIMESTAMP WITH TIME ZONE,
    paid_at TIMESTAMP WITH TIME ZONE,
    description TEXT,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =============================================================================
-- FINANCIAL DATA TABLES
-- =============================================================================

-- Encrypted financial profiles
CREATE TABLE encrypted_financial_profiles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    profile_name VARCHAR(100) NOT NULL,
    profile_type VARCHAR(50) NOT NULL, -- checking, savings, credit, investment
    institution_name VARCHAR(255),
    account_number_encrypted TEXT, -- encrypted with pgcrypto
    routing_number_encrypted TEXT,
    account_balance DECIMAL(15,2),
    credit_limit DECIMAL(15,2),
    interest_rate DECIMAL(5,4),
    last_sync_at TIMESTAMP WITH TIME ZONE,
    sync_status VARCHAR(50) DEFAULT 'pending',
    is_active BOOLEAN DEFAULT true,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Income due dates tracking
CREATE TABLE user_income_due_dates (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    income_source VARCHAR(100) NOT NULL,
    expected_amount DECIMAL(12,2) NOT NULL,
    due_date DATE NOT NULL,
    frequency VARCHAR(20) NOT NULL, -- weekly, biweekly, monthly, quarterly, yearly
    is_recurring BOOLEAN DEFAULT true,
    last_received_date DATE,
    last_received_amount DECIMAL(12,2),
    status VARCHAR(50) DEFAULT 'pending', -- pending, received, overdue
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Expense due dates tracking
CREATE TABLE user_expense_due_dates (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    expense_name VARCHAR(255) NOT NULL,
    expense_category VARCHAR(100),
    expected_amount DECIMAL(12,2) NOT NULL,
    due_date DATE NOT NULL,
    frequency VARCHAR(20) NOT NULL, -- weekly, biweekly, monthly, quarterly, yearly
    is_recurring BOOLEAN DEFAULT true,
    is_essential BOOLEAN DEFAULT true,
    last_paid_date DATE,
    last_paid_amount DECIMAL(12,2),
    status VARCHAR(50) DEFAULT 'pending', -- pending, paid, overdue
    auto_pay_enabled BOOLEAN DEFAULT false,
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Financial transactions
CREATE TABLE financial_transactions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    financial_profile_id UUID REFERENCES encrypted_financial_profiles(id),
    transaction_type VARCHAR(50) NOT NULL, -- income, expense, transfer
    amount DECIMAL(12,2) NOT NULL,
    description TEXT,
    category VARCHAR(100),
    merchant_name VARCHAR(255),
    transaction_date DATE NOT NULL,
    posted_date DATE,
    reference_number VARCHAR(255),
    status VARCHAR(50) DEFAULT 'pending', -- pending, completed, failed, disputed
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =============================================================================
-- HEALTH TRACKING TABLES
-- =============================================================================

-- User health check-ins
CREATE TABLE user_health_checkins (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    checkin_date DATE NOT NULL,
    mood_score INTEGER CHECK (mood_score >= 1 AND mood_score <= 10),
    stress_level INTEGER CHECK (stress_level >= 1 AND stress_level <= 10),
    sleep_hours DECIMAL(3,1),
    exercise_minutes INTEGER,
    water_intake_oz INTEGER,
    medication_taken BOOLEAN DEFAULT false,
    symptoms JSONB,
    wellness_activities JSONB,
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Health spending correlations
CREATE TABLE health_spending_correlations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    correlation_date DATE NOT NULL,
    health_metric VARCHAR(100) NOT NULL, -- mood, stress, sleep, exercise
    health_score DECIMAL(5,2),
    spending_amount DECIMAL(12,2),
    spending_category VARCHAR(100),
    correlation_strength DECIMAL(3,2), -- -1.0 to 1.0
    confidence_interval_lower DECIMAL(3,2),
    confidence_interval_upper DECIMAL(3,2),
    p_value DECIMAL(10,8),
    is_significant BOOLEAN DEFAULT false,
    analysis_period VARCHAR(20), -- daily, weekly, monthly
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Health goals and tracking
CREATE TABLE health_goals (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    goal_name VARCHAR(255) NOT NULL,
    goal_type VARCHAR(50) NOT NULL, -- mood, stress, sleep, exercise, nutrition
    target_value DECIMAL(10,2),
    current_value DECIMAL(10,2),
    unit VARCHAR(50),
    target_date DATE,
    is_completed BOOLEAN DEFAULT false,
    completion_date DATE,
    progress_percentage INTEGER DEFAULT 0,
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =============================================================================
-- CAREER DATA TABLES
-- =============================================================================

-- Job security analysis
CREATE TABLE job_security_analysis (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    analysis_date DATE NOT NULL,
    industry_risk_score DECIMAL(3,2), -- 0.0 to 1.0
    company_risk_score DECIMAL(3,2),
    personal_risk_score DECIMAL(3,2),
    overall_risk_score DECIMAL(3,2),
    risk_factors JSONB,
    mitigation_strategies JSONB,
    market_conditions JSONB,
    salary_comparison JSONB,
    career_opportunities JSONB,
    recommendations JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Career milestones and goals
CREATE TABLE career_milestones (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    milestone_name VARCHAR(255) NOT NULL,
    milestone_type VARCHAR(50) NOT NULL, -- promotion, raise, certification, education
    target_date DATE,
    target_salary DECIMAL(12,2),
    current_salary DECIMAL(12,2),
    is_completed BOOLEAN DEFAULT false,
    completion_date DATE,
    progress_percentage INTEGER DEFAULT 0,
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Income projections
CREATE TABLE income_projections (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    projection_date DATE NOT NULL,
    current_income DECIMAL(12,2) NOT NULL,
    projected_income_1_year DECIMAL(12,2),
    projected_income_3_years DECIMAL(12,2),
    projected_income_5_years DECIMAL(12,2),
    growth_rate DECIMAL(5,2),
    factors JSONB,
    confidence_level DECIMAL(3,2),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =============================================================================
-- ANALYTICS TABLES
-- =============================================================================

-- User analytics
CREATE TABLE user_analytics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    event_date DATE NOT NULL,
    event_type VARCHAR(100) NOT NULL,
    event_data JSONB,
    session_duration INTEGER, -- in seconds
    page_views INTEGER,
    features_used JSONB,
    engagement_score DECIMAL(3,2),
    retention_score DECIMAL(3,2),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Performance metrics
CREATE TABLE performance_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    metric_date DATE NOT NULL,
    metric_name VARCHAR(100) NOT NULL,
    metric_value DECIMAL(15,2),
    metric_unit VARCHAR(50),
    category VARCHAR(100),
    subcategory VARCHAR(100),
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Feature usage tracking
CREATE TABLE feature_usage (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    feature_name VARCHAR(100) NOT NULL,
    usage_date DATE NOT NULL,
    usage_count INTEGER DEFAULT 1,
    usage_duration INTEGER, -- in seconds
    success_rate DECIMAL(3,2),
    error_count INTEGER DEFAULT 0,
    performance_metrics JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- User feedback and satisfaction
CREATE TABLE user_feedback (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    feedback_date DATE NOT NULL,
    feedback_type VARCHAR(50) NOT NULL, -- feature, support, general
    rating INTEGER CHECK (rating >= 1 AND rating <= 5),
    feedback_text TEXT,
    category VARCHAR(100),
    status VARCHAR(50) DEFAULT 'open', -- open, in_progress, resolved, closed
    priority VARCHAR(20) DEFAULT 'medium', -- low, medium, high, critical
    assigned_to UUID,
    resolution_notes TEXT,
    resolved_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =============================================================================
-- SYSTEM MANAGEMENT TABLES
-- =============================================================================

-- System alerts
CREATE TABLE system_alerts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    alert_type VARCHAR(50) NOT NULL, -- security, performance, maintenance, user
    severity VARCHAR(20) NOT NULL, -- low, medium, high, critical
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    is_read BOOLEAN DEFAULT false,
    read_at TIMESTAMP WITH TIME ZONE,
    action_required BOOLEAN DEFAULT false,
    action_taken BOOLEAN DEFAULT false,
    action_notes TEXT,
    expires_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Important dates and reminders
CREATE TABLE important_dates (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    date_name VARCHAR(255) NOT NULL,
    date_type VARCHAR(50) NOT NULL, -- financial, health, career, personal
    date_value DATE NOT NULL,
    reminder_days INTEGER DEFAULT 7, -- days before to send reminder
    is_recurring BOOLEAN DEFAULT false,
    recurrence_pattern VARCHAR(100), -- yearly, monthly, weekly
    description TEXT,
    is_active BOOLEAN DEFAULT true,
    last_reminder_sent TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Notification preferences
CREATE TABLE notification_preferences (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    notification_type VARCHAR(50) NOT NULL,
    email_enabled BOOLEAN DEFAULT true,
    sms_enabled BOOLEAN DEFAULT false,
    push_enabled BOOLEAN DEFAULT true,
    frequency VARCHAR(20) DEFAULT 'immediate', -- immediate, daily, weekly
    quiet_hours_start TIME,
    quiet_hours_end TIME,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, notification_type)
);

-- =============================================================================
-- INDEXES FOR PERFORMANCE
-- =============================================================================

-- User indexes
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_created_at ON users(created_at);
CREATE INDEX idx_users_is_active ON users(is_active);

-- User profile indexes
CREATE INDEX idx_user_profiles_user_id ON user_profiles(user_id);
CREATE INDEX idx_user_profiles_zip_code ON user_profiles(zip_code);
CREATE INDEX idx_user_profiles_annual_income ON user_profiles(annual_income);
CREATE INDEX idx_user_profiles_industry ON user_profiles(industry);

-- Subscription indexes
CREATE INDEX idx_subscriptions_user_id ON subscriptions(user_id);
CREATE INDEX idx_subscriptions_status ON subscriptions(status);
CREATE INDEX idx_subscriptions_stripe_subscription_id ON subscriptions(stripe_subscription_id);

-- Feature access indexes
CREATE INDEX idx_feature_access_user_id ON feature_access(user_id);
CREATE INDEX idx_feature_access_feature_name ON feature_access(feature_name);

-- Financial data indexes
CREATE INDEX idx_encrypted_financial_profiles_user_id ON encrypted_financial_profiles(user_id);
CREATE INDEX idx_user_income_due_dates_user_id ON user_income_due_dates(user_id);
CREATE INDEX idx_user_income_due_dates_due_date ON user_income_due_dates(due_date);
CREATE INDEX idx_user_expense_due_dates_user_id ON user_expense_due_dates(user_id);
CREATE INDEX idx_user_expense_due_dates_due_date ON user_expense_due_dates(due_date);

-- Health tracking indexes
CREATE INDEX idx_user_health_checkins_user_id ON user_health_checkins(user_id);
CREATE INDEX idx_user_health_checkins_checkin_date ON user_health_checkins(checkin_date);
CREATE INDEX idx_health_spending_correlations_user_id ON health_spending_correlations(user_id);

-- Career data indexes
CREATE INDEX idx_job_security_analysis_user_id ON job_security_analysis(user_id);
CREATE INDEX idx_career_milestones_user_id ON career_milestones(user_id);

-- Analytics indexes
CREATE INDEX idx_user_analytics_user_id ON user_analytics(user_id);
CREATE INDEX idx_user_analytics_event_date ON user_analytics(event_date);
CREATE INDEX idx_performance_metrics_metric_date ON performance_metrics(metric_date);

-- System management indexes
CREATE INDEX idx_system_alerts_user_id ON system_alerts(user_id);
CREATE INDEX idx_system_alerts_severity ON system_alerts(severity);
CREATE INDEX idx_important_dates_user_id ON important_dates(user_id);
CREATE INDEX idx_important_dates_date_value ON important_dates(date_value);

-- JSONB indexes for better query performance
CREATE INDEX idx_user_profiles_financial_goals ON user_profiles USING GIN (financial_goals);
CREATE INDEX idx_user_profiles_preferences ON user_profiles USING GIN (preferences);
CREATE INDEX idx_encrypted_financial_profiles_metadata ON encrypted_financial_profiles USING GIN (metadata);
CREATE INDEX idx_user_analytics_event_data ON user_analytics USING GIN (event_data);

-- =============================================================================
-- CONSTRAINTS AND VALIDATIONS
-- =============================================================================

-- Add check constraints
ALTER TABLE user_profiles ADD CONSTRAINT chk_annual_income_positive CHECK (annual_income >= 0);
ALTER TABLE user_profiles ADD CONSTRAINT chk_dependents_non_negative CHECK (dependents >= 0);
ALTER TABLE user_profiles ADD CONSTRAINT chk_household_size_positive CHECK (household_size > 0);
ALTER TABLE user_profiles ADD CONSTRAINT chk_years_experience_non_negative CHECK (years_of_experience >= 0);

ALTER TABLE user_income_due_dates ADD CONSTRAINT chk_expected_amount_positive CHECK (expected_amount > 0);
ALTER TABLE user_expense_due_dates ADD CONSTRAINT chk_expected_amount_positive CHECK (expected_amount > 0);

ALTER TABLE financial_transactions ADD CONSTRAINT chk_amount_non_zero CHECK (amount != 0);

ALTER TABLE user_health_checkins ADD CONSTRAINT chk_sleep_hours_reasonable CHECK (sleep_hours >= 0 AND sleep_hours <= 24);
ALTER TABLE user_health_checkins ADD CONSTRAINT chk_exercise_minutes_non_negative CHECK (exercise_minutes >= 0);

-- =============================================================================
-- TRIGGERS FOR AUTOMATIC UPDATES
-- =============================================================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply updated_at triggers to relevant tables
CREATE TRIGGER update_user_profiles_updated_at BEFORE UPDATE ON user_profiles FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_subscriptions_updated_at BEFORE UPDATE ON subscriptions FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_feature_access_updated_at BEFORE UPDATE ON feature_access FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_encrypted_financial_profiles_updated_at BEFORE UPDATE ON encrypted_financial_profiles FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_user_health_checkins_updated_at BEFORE UPDATE ON user_health_checkins FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_career_milestones_updated_at BEFORE UPDATE ON career_milestones FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_user_feedback_updated_at BEFORE UPDATE ON user_feedback FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_system_alerts_updated_at BEFORE UPDATE ON system_alerts FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_important_dates_updated_at BEFORE UPDATE ON important_dates FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_notification_preferences_updated_at BEFORE UPDATE ON notification_preferences FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- =============================================================================
-- INITIAL DATA INSERTS
-- =============================================================================

-- Insert default subscription plans
INSERT INTO subscription_plans (name, description, price, billing_cycle, features, limits) VALUES
('Budget', 'Essential features for basic financial wellness', 10.00, 'monthly', 
 '{"health_checkins": 4, "financial_reports": 2, "ai_insights": 0, "career_analysis": false, "team_management": false}', 
 '{"health_checkins_per_month": 4, "financial_reports_per_month": 2}'),
('Mid-tier', 'Enhanced features for growing professionals', 20.00, 'monthly',
 '{"health_checkins": 12, "financial_reports": 6, "ai_insights": 10, "career_analysis": true, "team_management": false}',
 '{"health_checkins_per_month": 12, "financial_reports_per_month": 6, "ai_insights_per_month": 10}'),
('Professional', 'Complete financial wellness platform', 50.00, 'monthly',
 '{"health_checkins": -1, "financial_reports": -1, "ai_insights": -1, "career_analysis": true, "team_management": true}',
 '{"health_checkins_per_month": -1, "financial_reports_per_month": -1, "ai_insights_per_month": -1}');

-- =============================================================================
-- COMMENTS FOR DOCUMENTATION
-- =============================================================================

COMMENT ON TABLE users IS 'Core user accounts with authentication and security features';
COMMENT ON TABLE user_profiles IS 'Enhanced user profiles with demographic and financial information';
COMMENT ON TABLE subscriptions IS 'User subscription management with Stripe integration';
COMMENT ON TABLE feature_access IS 'Feature access control with usage limits and tracking';
COMMENT ON TABLE encrypted_financial_profiles IS 'Encrypted financial account information';
COMMENT ON TABLE user_health_checkins IS 'Daily health and wellness tracking';
COMMENT ON TABLE health_spending_correlations IS 'Statistical analysis of health-spending relationships';
COMMENT ON TABLE job_security_analysis IS 'Career risk assessment and job security analysis';
COMMENT ON TABLE user_analytics IS 'User behavior and engagement analytics';
COMMENT ON TABLE system_alerts IS 'System-wide alerts and notifications';
COMMENT ON TABLE important_dates IS 'Important dates and reminders for users';

COMMENT ON COLUMN users.id IS 'UUID primary key for security and scalability';
COMMENT ON COLUMN user_profiles.zip_code IS 'Required for demographic analysis and local insights';
COMMENT ON COLUMN user_profiles.dependents IS 'Number of dependents for financial planning';
COMMENT ON COLUMN user_profiles.naics_code IS 'North American Industry Classification System code';
COMMENT ON COLUMN subscriptions.stripe_subscription_id IS 'Stripe subscription ID for billing management';
COMMENT ON COLUMN feature_access.usage_limit IS 'Monthly usage limit (-1 for unlimited)';
COMMENT ON COLUMN encrypted_financial_profiles.account_number_encrypted IS 'Encrypted account number using pgcrypto';
COMMENT ON COLUMN health_spending_correlations.correlation_strength IS 'Pearson correlation coefficient (-1.0 to 1.0)';

-- =============================================================================
-- SCHEMA COMPLETION
-- =============================================================================

-- Verify schema creation
SELECT 'MINGUS Unified PostgreSQL Schema created successfully!' as status; 