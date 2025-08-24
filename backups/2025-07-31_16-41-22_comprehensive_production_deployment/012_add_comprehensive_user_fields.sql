-- Migration: Add comprehensive user profile fields
-- Date: 2025-01-27
-- Description: Add extensive user profile fields for enhanced personalization and analytics

-- Create ENUM types for new fields
DO $$ BEGIN
    CREATE TYPE income_frequency_type AS ENUM ('weekly', 'bi-weekly', 'semi-monthly', 'monthly', 'annually');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE credit_score_range_type AS ENUM ('excellent', 'good', 'fair', 'poor', 'very_poor', 'unknown');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE age_range_type AS ENUM ('18-24', '25-34', '35-44', '45-54', '55-64', '65+');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE marital_status_type AS ENUM ('single', 'married', 'partnership', 'divorced', 'widowed', 'prefer_not_to_say');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE years_of_experience_type AS ENUM ('less_than_1', '1-3', '4-7', '8-12', '13-20', '20+');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE risk_tolerance_level_type AS ENUM ('conservative', 'moderate', 'aggressive', 'unsure');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE financial_knowledge_level_type AS ENUM ('beginner', 'intermediate', 'advanced', 'expert');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE health_checkin_frequency_type AS ENUM ('daily', 'weekly', 'monthly', 'on_demand', 'never');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Add new columns to users table
-- Personal Information
ALTER TABLE users ADD COLUMN IF NOT EXISTS first_name VARCHAR(50);
ALTER TABLE users ADD COLUMN IF NOT EXISTS last_name VARCHAR(50);
ALTER TABLE users ADD COLUMN IF NOT EXISTS date_of_birth DATE;
ALTER TABLE users ADD COLUMN IF NOT EXISTS zip_code VARCHAR(10);
ALTER TABLE users ADD COLUMN IF NOT EXISTS phone_number VARCHAR(20);
ALTER TABLE users ADD COLUMN IF NOT EXISTS email_verification_status BOOLEAN DEFAULT FALSE;

-- Financial data
ALTER TABLE users ADD COLUMN IF NOT EXISTS monthly_income DECIMAL(10,2);
ALTER TABLE users ADD COLUMN IF NOT EXISTS income_frequency income_frequency_type;
ALTER TABLE users ADD COLUMN IF NOT EXISTS primary_income_source VARCHAR(100);
ALTER TABLE users ADD COLUMN IF NOT EXISTS current_savings_balance DECIMAL(10,2);
ALTER TABLE users ADD COLUMN IF NOT EXISTS total_debt_amount DECIMAL(10,2);
ALTER TABLE users ADD COLUMN IF NOT EXISTS credit_score_range credit_score_range_type;
ALTER TABLE users ADD COLUMN IF NOT EXISTS employment_status VARCHAR(50);

-- Demographics
ALTER TABLE users ADD COLUMN IF NOT EXISTS age_range age_range_type;
ALTER TABLE users ADD COLUMN IF NOT EXISTS marital_status marital_status_type;
ALTER TABLE users ADD COLUMN IF NOT EXISTS dependents_count INT DEFAULT 0;
ALTER TABLE users ADD COLUMN IF NOT EXISTS household_size INT DEFAULT 1;
ALTER TABLE users ADD COLUMN IF NOT EXISTS education_level VARCHAR(100);
ALTER TABLE users ADD COLUMN IF NOT EXISTS occupation VARCHAR(100);
ALTER TABLE users ADD COLUMN IF NOT EXISTS industry VARCHAR(100);
ALTER TABLE users ADD COLUMN IF NOT EXISTS years_of_experience years_of_experience_type;

-- Goals and preferences
ALTER TABLE users ADD COLUMN IF NOT EXISTS primary_financial_goal VARCHAR(100);
ALTER TABLE users ADD COLUMN IF NOT EXISTS risk_tolerance_level risk_tolerance_level_type;
ALTER TABLE users ADD COLUMN IF NOT EXISTS financial_knowledge_level financial_knowledge_level_type;
ALTER TABLE users ADD COLUMN IF NOT EXISTS preferred_contact_method VARCHAR(50);
ALTER TABLE users ADD COLUMN IF NOT EXISTS notification_preferences JSONB;

-- Health and wellness
ALTER TABLE users ADD COLUMN IF NOT EXISTS health_checkin_frequency health_checkin_frequency_type;
ALTER TABLE users ADD COLUMN IF NOT EXISTS stress_level_baseline INT CHECK (stress_level_baseline >= 1 AND stress_level_baseline <= 10);
ALTER TABLE users ADD COLUMN IF NOT EXISTS wellness_goals JSONB;

-- Compliance and preferences
ALTER TABLE users ADD COLUMN IF NOT EXISTS gdpr_consent_status BOOLEAN DEFAULT FALSE;
ALTER TABLE users ADD COLUMN IF NOT EXISTS data_sharing_preferences VARCHAR(100);
ALTER TABLE users ADD COLUMN IF NOT EXISTS profile_completion_percentage DECIMAL(5,2) DEFAULT 0.00;
ALTER TABLE users ADD COLUMN IF NOT EXISTS onboarding_step INT DEFAULT 1;

-- Add constraints for data validation
ALTER TABLE users ADD CONSTRAINT IF NOT EXISTS valid_phone_number 
    CHECK (phone_number IS NULL OR phone_number ~ '^\+?[1-9]\d{1,14}$');

ALTER TABLE users ADD CONSTRAINT IF NOT EXISTS valid_zip_code 
    CHECK (zip_code IS NULL OR zip_code ~ '^\d{5}(-\d{4})?$');

ALTER TABLE users ADD CONSTRAINT IF NOT EXISTS valid_dependents_count 
    CHECK (dependents_count >= 0 AND dependents_count <= 20);

ALTER TABLE users ADD CONSTRAINT IF NOT EXISTS valid_household_size 
    CHECK (household_size >= 1 AND household_size <= 20);

ALTER TABLE users ADD CONSTRAINT IF NOT EXISTS valid_profile_completion 
    CHECK (profile_completion_percentage >= 0.00 AND profile_completion_percentage <= 100.00);

ALTER TABLE users ADD CONSTRAINT IF NOT EXISTS valid_onboarding_step 
    CHECK (onboarding_step >= 1 AND onboarding_step <= 10);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_users_first_name ON users(first_name);
CREATE INDEX IF NOT EXISTS idx_users_last_name ON users(last_name);
CREATE INDEX IF NOT EXISTS idx_users_zip_code ON users(zip_code);
CREATE INDEX IF NOT EXISTS idx_users_phone_number ON users(phone_number);
CREATE INDEX IF NOT EXISTS idx_users_email_verification ON users(email_verification_status);
CREATE INDEX IF NOT EXISTS idx_users_monthly_income ON users(monthly_income);
CREATE INDEX IF NOT EXISTS idx_users_credit_score ON users(credit_score_range);
CREATE INDEX IF NOT EXISTS idx_users_age_range ON users(age_range);
CREATE INDEX IF NOT EXISTS idx_users_marital_status ON users(marital_status);
CREATE INDEX IF NOT EXISTS idx_users_employment_status ON users(employment_status);
CREATE INDEX IF NOT EXISTS idx_users_risk_tolerance ON users(risk_tolerance_level);
CREATE INDEX IF NOT EXISTS idx_users_financial_knowledge ON users(financial_knowledge_level);
CREATE INDEX IF NOT EXISTS idx_users_profile_completion ON users(profile_completion_percentage);
CREATE INDEX IF NOT EXISTS idx_users_onboarding_step ON users(onboarding_step);
CREATE INDEX IF NOT EXISTS idx_users_gdpr_consent ON users(gdpr_consent_status);

-- Create composite indexes for common queries
CREATE INDEX IF NOT EXISTS idx_users_name_search ON users(first_name, last_name);
CREATE INDEX IF NOT EXISTS idx_users_demographics ON users(age_range, marital_status, employment_status);
CREATE INDEX IF NOT EXISTS idx_users_financial_profile ON users(monthly_income, credit_score_range, risk_tolerance_level);

-- Add comments for documentation
COMMENT ON COLUMN users.first_name IS 'User first name for personalization';
COMMENT ON COLUMN users.last_name IS 'User last name for personalization';
COMMENT ON COLUMN users.date_of_birth IS 'User date of birth for age calculations and compliance';
COMMENT ON COLUMN users.zip_code IS 'User zip code for location-based services';
COMMENT ON COLUMN users.phone_number IS 'User phone number for SMS notifications';
COMMENT ON COLUMN users.email_verification_status IS 'Whether user email has been verified';
COMMENT ON COLUMN users.monthly_income IS 'User monthly income for financial planning';
COMMENT ON COLUMN users.income_frequency IS 'How often user receives income';
COMMENT ON COLUMN users.primary_income_source IS 'Main source of user income';
COMMENT ON COLUMN users.current_savings_balance IS 'Current savings account balance';
COMMENT ON COLUMN users.total_debt_amount IS 'Total outstanding debt amount';
COMMENT ON COLUMN users.credit_score_range IS 'User credit score range for risk assessment';
COMMENT ON COLUMN users.employment_status IS 'Current employment status';
COMMENT ON COLUMN users.age_range IS 'User age range for demographic analysis';
COMMENT ON COLUMN users.marital_status IS 'User marital status for financial planning';
COMMENT ON COLUMN users.dependents_count IS 'Number of dependents for financial planning';
COMMENT ON COLUMN users.household_size IS 'Total household size';
COMMENT ON COLUMN users.education_level IS 'Highest education level achieved';
COMMENT ON COLUMN users.occupation IS 'Current job title/occupation';
COMMENT ON COLUMN users.industry IS 'Industry of employment';
COMMENT ON COLUMN users.years_of_experience IS 'Years of work experience';
COMMENT ON COLUMN users.primary_financial_goal IS 'Main financial goal for planning';
COMMENT ON COLUMN users.risk_tolerance_level IS 'User risk tolerance for investment recommendations';
COMMENT ON COLUMN users.financial_knowledge_level IS 'User financial knowledge level';
COMMENT ON COLUMN users.preferred_contact_method IS 'Preferred method of contact';
COMMENT ON COLUMN users.notification_preferences IS 'JSON object storing notification preferences';
COMMENT ON COLUMN users.health_checkin_frequency IS 'How often user wants health check-ins';
COMMENT ON COLUMN users.stress_level_baseline IS 'Baseline stress level (1-10 scale)';
COMMENT ON COLUMN users.wellness_goals IS 'JSON object storing wellness goals';
COMMENT ON COLUMN users.gdpr_consent_status IS 'Whether user has given GDPR consent';
COMMENT ON COLUMN users.data_sharing_preferences IS 'User data sharing preferences';
COMMENT ON COLUMN users.profile_completion_percentage IS 'Percentage of profile completion';
COMMENT ON COLUMN users.onboarding_step IS 'Current step in onboarding process';

-- Create a function to calculate profile completion percentage
CREATE OR REPLACE FUNCTION calculate_profile_completion_percentage(user_uuid UUID)
RETURNS DECIMAL(5,2)
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    total_fields INTEGER := 25; -- Total number of profile fields
    filled_fields INTEGER := 0;
    user_record RECORD;
BEGIN
    SELECT * INTO user_record FROM users WHERE id = user_uuid;
    
    -- Count filled fields
    IF user_record.first_name IS NOT NULL AND user_record.first_name != '' THEN filled_fields := filled_fields + 1; END IF;
    IF user_record.last_name IS NOT NULL AND user_record.last_name != '' THEN filled_fields := filled_fields + 1; END IF;
    IF user_record.date_of_birth IS NOT NULL THEN filled_fields := filled_fields + 1; END IF;
    IF user_record.zip_code IS NOT NULL AND user_record.zip_code != '' THEN filled_fields := filled_fields + 1; END IF;
    IF user_record.phone_number IS NOT NULL AND user_record.phone_number != '' THEN filled_fields := filled_fields + 1; END IF;
    IF user_record.monthly_income IS NOT NULL THEN filled_fields := filled_fields + 1; END IF;
    IF user_record.income_frequency IS NOT NULL THEN filled_fields := filled_fields + 1; END IF;
    IF user_record.primary_income_source IS NOT NULL AND user_record.primary_income_source != '' THEN filled_fields := filled_fields + 1; END IF;
    IF user_record.current_savings_balance IS NOT NULL THEN filled_fields := filled_fields + 1; END IF;
    IF user_record.total_debt_amount IS NOT NULL THEN filled_fields := filled_fields + 1; END IF;
    IF user_record.credit_score_range IS NOT NULL THEN filled_fields := filled_fields + 1; END IF;
    IF user_record.employment_status IS NOT NULL AND user_record.employment_status != '' THEN filled_fields := filled_fields + 1; END IF;
    IF user_record.age_range IS NOT NULL THEN filled_fields := filled_fields + 1; END IF;
    IF user_record.marital_status IS NOT NULL THEN filled_fields := filled_fields + 1; END IF;
    IF user_record.education_level IS NOT NULL AND user_record.education_level != '' THEN filled_fields := filled_fields + 1; END IF;
    IF user_record.occupation IS NOT NULL AND user_record.occupation != '' THEN filled_fields := filled_fields + 1; END IF;
    IF user_record.industry IS NOT NULL AND user_record.industry != '' THEN filled_fields := filled_fields + 1; END IF;
    IF user_record.years_of_experience IS NOT NULL THEN filled_fields := filled_fields + 1; END IF;
    IF user_record.primary_financial_goal IS NOT NULL AND user_record.primary_financial_goal != '' THEN filled_fields := filled_fields + 1; END IF;
    IF user_record.risk_tolerance_level IS NOT NULL THEN filled_fields := filled_fields + 1; END IF;
    IF user_record.financial_knowledge_level IS NOT NULL THEN filled_fields := filled_fields + 1; END IF;
    IF user_record.preferred_contact_method IS NOT NULL AND user_record.preferred_contact_method != '' THEN filled_fields := filled_fields + 1; END IF;
    IF user_record.health_checkin_frequency IS NOT NULL THEN filled_fields := filled_fields + 1; END IF;
    IF user_record.stress_level_baseline IS NOT NULL THEN filled_fields := filled_fields + 1; END IF;
    IF user_record.gdpr_consent_status IS NOT NULL THEN filled_fields := filled_fields + 1; END IF;
    
    RETURN ROUND((filled_fields::DECIMAL / total_fields) * 100, 2);
END;
$$;

-- Create a trigger to automatically update profile completion percentage
CREATE OR REPLACE FUNCTION update_profile_completion_trigger()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    NEW.profile_completion_percentage = calculate_profile_completion_percentage(NEW.id);
    RETURN NEW;
END;
$$;

-- Create trigger to update profile completion on user updates
DROP TRIGGER IF EXISTS trigger_update_profile_completion ON users;
CREATE TRIGGER trigger_update_profile_completion
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_profile_completion_trigger();

-- Grant necessary permissions
GRANT EXECUTE ON FUNCTION calculate_profile_completion_percentage(UUID) TO authenticated;
GRANT EXECUTE ON FUNCTION update_profile_completion_trigger() TO authenticated;

-- Insert migration record
INSERT INTO migration_log (migration_name, applied_at, description)
VALUES ('012_add_comprehensive_user_fields', NOW(), 'Added comprehensive user profile fields including personal info, financial data, demographics, goals, health/wellness, and compliance fields')
ON CONFLICT (migration_name) DO NOTHING; 