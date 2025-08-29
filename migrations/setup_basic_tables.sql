-- Setup basic tables for MINGUS application
-- This creates the essential tables needed for the questionnaire functionality

-- Create users table
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255),
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE,
    email_verified BOOLEAN DEFAULT FALSE,
    phone VARCHAR(20),
    phone_verified BOOLEAN DEFAULT FALSE,
    date_of_birth DATE,
    gender VARCHAR(20),
    occupation VARCHAR(100),
    company VARCHAR(100),
    industry VARCHAR(100),
    annual_income DECIMAL(12,2),
    financial_goals TEXT[],
    risk_tolerance VARCHAR(20),
    investment_experience VARCHAR(20),
    emergency_fund_amount DECIMAL(12,2),
    total_debt DECIMAL(12,2),
    monthly_expenses DECIMAL(12,2),
    savings_rate DECIMAL(5,2),
    credit_score INTEGER,
    financial_stress_level INTEGER,
    preferred_communication_method VARCHAR(20),
    notification_preferences JSONB,
    timezone VARCHAR(50) DEFAULT 'UTC',
    locale VARCHAR(10) DEFAULT 'en-US',
    last_login TIMESTAMP WITH TIME ZONE,
    login_count INTEGER DEFAULT 0,
    failed_login_attempts INTEGER DEFAULT 0,
    account_locked BOOLEAN DEFAULT FALSE,
    account_locked_until TIMESTAMP WITH TIME ZONE,
    password_reset_token VARCHAR(255),
    password_reset_expires TIMESTAMP WITH TIME ZONE,
    email_verification_token VARCHAR(255),
    email_verification_expires TIMESTAMP WITH TIME ZONE,
    profile_completion_percentage INTEGER DEFAULT 0,
    onboarding_completed BOOLEAN DEFAULT FALSE,
    subscription_tier VARCHAR(20) DEFAULT 'free',
    subscription_status VARCHAR(20) DEFAULT 'active',
    subscription_start_date TIMESTAMP WITH TIME ZONE,
    subscription_end_date TIMESTAMP WITH TIME ZONE,
    trial_end_date TIMESTAMP WITH TIME ZONE,
    payment_method_id VARCHAR(255),
    billing_address JSONB,
    marketing_consent BOOLEAN DEFAULT FALSE,
    terms_accepted BOOLEAN DEFAULT FALSE,
    privacy_policy_accepted BOOLEAN DEFAULT FALSE,
    data_processing_consent BOOLEAN DEFAULT FALSE,
    source VARCHAR(100),
    utm_source VARCHAR(100),
    utm_medium VARCHAR(100),
    utm_campaign VARCHAR(100),
    utm_term VARCHAR(100),
    utm_content VARCHAR(100),
    referrer VARCHAR(255),
    device_info JSONB,
    ip_address INET,
    user_agent TEXT,
    notes TEXT,
    tags TEXT[],
    metadata JSONB
);

-- Create indexes for users table
CREATE INDEX IF NOT EXISTS idx_users_email ON users (email);
CREATE INDEX IF NOT EXISTS idx_users_created_at ON users (created_at DESC);
CREATE INDEX IF NOT EXISTS idx_users_subscription_tier ON users (subscription_tier);
CREATE INDEX IF NOT EXISTS idx_users_subscription_status ON users (subscription_status);
CREATE INDEX IF NOT EXISTS idx_users_is_active ON users (is_active);
CREATE INDEX IF NOT EXISTS idx_users_email_verified ON users (email_verified);

-- Create questionnaire_submissions table
CREATE TABLE IF NOT EXISTS questionnaire_submissions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) NOT NULL,
    
    -- Questionnaire data
    answers JSONB NOT NULL,  -- Store the question answers
    total_score INTEGER NOT NULL,
    wellness_level VARCHAR(100) NOT NULL,  -- LOW, MODERATE, HIGH
    wellness_description TEXT,
    
    -- User journey tracking
    has_signed_up BOOLEAN DEFAULT FALSE,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    
    -- Marketing data
    source VARCHAR(100) DEFAULT 'financial_questionnaire',
    utm_source VARCHAR(100),
    utm_medium VARCHAR(100),
    utm_campaign VARCHAR(100),
    
    -- Timestamps
    submitted_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    signed_up_at TIMESTAMP WITH TIME ZONE,
    
    -- Constraints
    CONSTRAINT questionnaire_submissions_email_unique UNIQUE (email)
);

-- Create indexes for questionnaire_submissions table
CREATE INDEX IF NOT EXISTS idx_questionnaire_submissions_email ON questionnaire_submissions (email);
CREATE INDEX IF NOT EXISTS idx_questionnaire_submissions_submitted_at ON questionnaire_submissions (submitted_at DESC);
CREATE INDEX IF NOT EXISTS idx_questionnaire_submissions_has_signed_up ON questionnaire_submissions (has_signed_up);
CREATE INDEX IF NOT EXISTS idx_questionnaire_submissions_source ON questionnaire_submissions (source);
CREATE INDEX IF NOT EXISTS idx_questionnaire_submissions_user_id ON questionnaire_submissions (user_id) WHERE user_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_questionnaire_submissions_wellness_level ON questionnaire_submissions (wellness_level);

-- Create relationship_questionnaire_submissions table
CREATE TABLE IF NOT EXISTS relationship_questionnaire_submissions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) NOT NULL,

    -- Questionnaire data
    answers JSONB NOT NULL,  -- Store the question answers
    total_score INTEGER NOT NULL,
    connection_level VARCHAR(100) NOT NULL,  -- LOW, MODERATE, HIGH
    connection_description TEXT,

    -- User journey tracking
    has_signed_up BOOLEAN DEFAULT FALSE,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,

    -- Marketing data
    source VARCHAR(100) DEFAULT 'relationship_questionnaire',
    utm_source VARCHAR(100),
    utm_medium VARCHAR(100),
    utm_campaign VARCHAR(100),

    -- Timestamps
    submitted_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    signed_up_at TIMESTAMP WITH TIME ZONE,

    -- Constraints
    CONSTRAINT relationship_questionnaire_submissions_email_unique UNIQUE (email)
);

-- Create indexes for relationship_questionnaire_submissions table
CREATE INDEX IF NOT EXISTS idx_relationship_questionnaire_submissions_email ON relationship_questionnaire_submissions (email);
CREATE INDEX IF NOT EXISTS idx_relationship_questionnaire_submissions_submitted_at ON relationship_questionnaire_submissions (submitted_at DESC);
CREATE INDEX IF NOT EXISTS idx_relationship_questionnaire_submissions_has_signed_up ON relationship_questionnaire_submissions (has_signed_up);
CREATE INDEX IF NOT EXISTS idx_relationship_questionnaire_submissions_source ON relationship_questionnaire_submissions (source);
CREATE INDEX IF NOT EXISTS idx_relationship_questionnaire_submissions_user_id ON relationship_questionnaire_submissions (user_id) WHERE user_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_relationship_questionnaire_submissions_connection_level ON relationship_questionnaire_submissions (connection_level);

-- Add comments
COMMENT ON TABLE users IS 'Main users table for MINGUS application';
COMMENT ON TABLE questionnaire_submissions IS 'Store financial questionnaire submissions with email addresses for follow-up';
COMMENT ON TABLE relationship_questionnaire_submissions IS 'Store relationship questionnaire submissions with email addresses for follow-up';
