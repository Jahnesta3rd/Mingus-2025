-- Create exec_sql function for schema management
CREATE OR REPLACE FUNCTION exec_sql(sql text) RETURNS void AS $$
BEGIN
    EXECUTE sql;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Drop existing indexes if they exist
DROP INDEX IF EXISTS idx_anonymous_onboarding_session_id;
DROP INDEX IF EXISTS idx_anonymous_onboarding_created_at;
DROP INDEX IF EXISTS idx_anonymous_onboarding_converted;
DROP INDEX IF EXISTS idx_user_onboarding_user_id;
DROP INDEX IF EXISTS idx_user_onboarding_created_at;
DROP INDEX IF EXISTS idx_personalization_analytics_session;
DROP INDEX IF EXISTS idx_personalization_analytics_timestamp;
DROP INDEX IF EXISTS idx_users_email;

-- Drop existing enum types if they exist
DO $$ BEGIN
    IF EXISTS (SELECT 1 FROM pg_type WHERE typname = 'financial_challenge_type') THEN
        DROP TYPE financial_challenge_type CASCADE;
    END IF;
    IF EXISTS (SELECT 1 FROM pg_type WHERE typname = 'stress_handling_type') THEN
        DROP TYPE stress_handling_type CASCADE;
    END IF;
    IF EXISTS (SELECT 1 FROM pg_type WHERE typname = 'motivation_type') THEN
        DROP TYPE motivation_type CASCADE;
    END IF;
    IF EXISTS (SELECT 1 FROM pg_type WHERE typname = 'income_range_type') THEN
        DROP TYPE income_range_type CASCADE;
    END IF;
END $$;

-- Create enum types
CREATE TYPE financial_challenge_type AS ENUM (
    'emergency_savings',
    'multiple_income',
    'debt',
    'major_expenses'
);

CREATE TYPE stress_handling_type AS ENUM (
    'talk_to_people',
    'exercise',
    'avoid_thinking',
    'research_plan'
);

CREATE TYPE motivation_type AS ENUM (
    'family_goals',
    'personal_growth',
    'community_impact',
    'financial_freedom'
);

CREATE TYPE income_range_type AS ENUM (
    'under_25k',
    '25k_50k',
    '50k_75k',
    '75k_100k',
    '100k_150k',
    '150k_200k',
    'over_200k'
);

-- Drop existing tables if they exist
DROP TABLE IF EXISTS anonymous_onboarding_responses CASCADE;
DROP TABLE IF EXISTS user_onboarding_profiles CASCADE;
DROP TABLE IF EXISTS personalization_analytics CASCADE;
DROP TABLE IF EXISTS users CASCADE;

-- Create users table
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email TEXT NOT NULL UNIQUE,
    full_name TEXT NOT NULL,
    income_range income_range_type NOT NULL,
    session_id UUID,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ,
    CONSTRAINT valid_email CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$')
);

-- Create anonymous onboarding responses table
CREATE TABLE IF NOT EXISTS anonymous_onboarding_responses (
    id SERIAL PRIMARY KEY,
    session_id UUID NOT NULL,
    financial_challenge financial_challenge_type NOT NULL,
    stress_handling stress_handling_type[] NOT NULL,
    motivation motivation_type[] NOT NULL,
    monthly_income DECIMAL(12,2) NOT NULL CHECK (monthly_income >= 0),
    monthly_expenses DECIMAL(12,2) NOT NULL CHECK (monthly_expenses >= 0),
    savings_goal DECIMAL(12,2) NOT NULL CHECK (savings_goal >= 0),
    risk_tolerance INTEGER NOT NULL CHECK (risk_tolerance BETWEEN 1 AND 10),
    financial_knowledge INTEGER NOT NULL CHECK (financial_knowledge BETWEEN 1 AND 10),
    preferred_contact_method TEXT NOT NULL CHECK (preferred_contact_method IN ('email', 'sms', 'both')),
    contact_info TEXT NOT NULL,
    ip_address TEXT NOT NULL,
    user_agent TEXT NOT NULL,
    referrer TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    converted_to_signup BOOLEAN DEFAULT FALSE,
    conversion_date TIMESTAMPTZ,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    CONSTRAINT valid_expenses CHECK (monthly_expenses <= monthly_income * 2),
    CONSTRAINT valid_savings_goal CHECK (savings_goal <= monthly_income * 120)
);

-- Create user onboarding profiles table
CREATE TABLE IF NOT EXISTS user_onboarding_profiles (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    financial_challenge financial_challenge_type NOT NULL,
    stress_handling stress_handling_type[] NOT NULL,
    motivation motivation_type[] NOT NULL,
    monthly_income DECIMAL(12,2) NOT NULL CHECK (monthly_income >= 0),
    monthly_expenses DECIMAL(12,2) NOT NULL CHECK (monthly_expenses >= 0),
    savings_goal DECIMAL(12,2) NOT NULL CHECK (savings_goal >= 0),
    risk_tolerance INTEGER NOT NULL CHECK (risk_tolerance BETWEEN 1 AND 10),
    financial_knowledge INTEGER NOT NULL CHECK (financial_knowledge BETWEEN 1 AND 10),
    preferred_contact_method TEXT NOT NULL CHECK (preferred_contact_method IN ('email', 'sms', 'both')),
    contact_info TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ,
    CONSTRAINT valid_expenses CHECK (monthly_expenses <= monthly_income * 2),
    CONSTRAINT valid_savings_goal CHECK (savings_goal <= monthly_income * 120)
);

-- Create personalization analytics table
CREATE TABLE IF NOT EXISTS personalization_analytics (
    id SERIAL PRIMARY KEY,
    session_id UUID NOT NULL,
    financial_challenge financial_challenge_type NOT NULL,
    motivation motivation_type NOT NULL,
    converted BOOLEAN NOT NULL DEFAULT FALSE,
    timestamp TIMESTAMPTZ DEFAULT NOW()
);

-- Drop existing trigger function if it exists
DROP FUNCTION IF EXISTS update_updated_at_column() CASCADE;

-- Create trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for updated_at columns
CREATE TRIGGER update_user_onboarding_profiles_updated_at
    BEFORE UPDATE ON user_onboarding_profiles
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_anonymous_onboarding_session_id ON anonymous_onboarding_responses(session_id);
CREATE INDEX IF NOT EXISTS idx_anonymous_onboarding_created_at ON anonymous_onboarding_responses(created_at);
CREATE INDEX IF NOT EXISTS idx_anonymous_onboarding_converted ON anonymous_onboarding_responses(converted_to_signup);
CREATE INDEX IF NOT EXISTS idx_user_onboarding_user_id ON user_onboarding_profiles(user_id);
CREATE INDEX IF NOT EXISTS idx_user_onboarding_created_at ON user_onboarding_profiles(created_at);
CREATE INDEX IF NOT EXISTS idx_personalization_analytics_session ON personalization_analytics(session_id);
CREATE INDEX IF NOT EXISTS idx_personalization_analytics_timestamp ON personalization_analytics(timestamp);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email); 