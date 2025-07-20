-- Migration: Add Profile Fields for Enhanced Onboarding
-- Date: 2025-01-27
-- Description: Add comprehensive profile fields to support detailed user onboarding

-- Add basic information fields
ALTER TABLE user_onboarding_profiles 
ADD COLUMN IF NOT EXISTS first_name VARCHAR(100),
ADD COLUMN IF NOT EXISTS last_name VARCHAR(100),
ADD COLUMN IF NOT EXISTS age_range VARCHAR(50),
ADD COLUMN IF NOT EXISTS gender VARCHAR(50);

-- Add location and household fields
ALTER TABLE user_onboarding_profiles 
ADD COLUMN IF NOT EXISTS zip_code VARCHAR(10),
ADD COLUMN IF NOT EXISTS location_state VARCHAR(50),
ADD COLUMN IF NOT EXISTS location_city VARCHAR(100),
ADD COLUMN IF NOT EXISTS household_size VARCHAR(10),
ADD COLUMN IF NOT EXISTS dependents VARCHAR(50),
ADD COLUMN IF NOT EXISTS relationship_status VARCHAR(50);

-- Add employment and income fields
ALTER TABLE user_onboarding_profiles 
ADD COLUMN IF NOT EXISTS income_frequency VARCHAR(50) DEFAULT 'monthly',
ADD COLUMN IF NOT EXISTS primary_income_source VARCHAR(100),
ADD COLUMN IF NOT EXISTS employment_status VARCHAR(50),
ADD COLUMN IF NOT EXISTS industry VARCHAR(100),
ADD COLUMN IF NOT EXISTS job_title VARCHAR(100),
ADD COLUMN IF NOT EXISTS naics_code VARCHAR(10);

-- Add financial status fields
ALTER TABLE user_onboarding_profiles 
ADD COLUMN IF NOT EXISTS current_savings DECIMAL(12,2),
ADD COLUMN IF NOT EXISTS current_debt DECIMAL(12,2),
ADD COLUMN IF NOT EXISTS credit_score_range VARCHAR(50);

-- Add constraints for data validation
ALTER TABLE user_onboarding_profiles 
ADD CONSTRAINT IF NOT EXISTS valid_zip_code 
CHECK (zip_code ~ '^\d{5}(-\d{4})?$'),
ADD CONSTRAINT IF NOT EXISTS valid_age_range 
CHECK (age_range IN ('18-24', '25-34', '35-44', '45-54', '55-64', '65+')),
ADD CONSTRAINT IF NOT EXISTS valid_gender 
CHECK (gender IN ('male', 'female', 'non_binary', 'other', '')),
ADD CONSTRAINT IF NOT EXISTS valid_household_size 
CHECK (household_size IN ('1', '2', '3', '4', '5+')),
ADD CONSTRAINT IF NOT EXISTS valid_relationship_status 
CHECK (relationship_status IN ('single', 'married', 'domestic_partnership', 'divorced', 'widowed')),
ADD CONSTRAINT IF NOT EXISTS valid_employment_status 
CHECK (employment_status IN ('employed', 'self_employed', 'unemployed', 'student', 'retired', 'other')),
ADD CONSTRAINT IF NOT EXISTS valid_income_frequency 
CHECK (income_frequency IN ('weekly', 'bi-weekly', 'semi-monthly', 'monthly', 'quarterly', 'annually')),
ADD CONSTRAINT IF NOT EXISTS valid_credit_score_range 
CHECK (credit_score_range IN ('excellent', 'good', 'fair', 'poor', 'unknown'));

-- Add indexes for better performance
CREATE INDEX IF NOT EXISTS idx_user_profiles_first_name ON user_onboarding_profiles(first_name);
CREATE INDEX IF NOT EXISTS idx_user_profiles_last_name ON user_onboarding_profiles(last_name);
CREATE INDEX IF NOT EXISTS idx_user_profiles_age_range ON user_onboarding_profiles(age_range);
CREATE INDEX IF NOT EXISTS idx_user_profiles_location_state ON user_onboarding_profiles(location_state);
CREATE INDEX IF NOT EXISTS idx_user_profiles_industry ON user_onboarding_profiles(industry);
CREATE INDEX IF NOT EXISTS idx_user_profiles_employment_status ON user_onboarding_profiles(employment_status);

-- Add comments for documentation
COMMENT ON COLUMN user_onboarding_profiles.first_name IS 'User first name';
COMMENT ON COLUMN user_onboarding_profiles.last_name IS 'User last name';
COMMENT ON COLUMN user_onboarding_profiles.age_range IS 'User age range category';
COMMENT ON COLUMN user_onboarding_profiles.gender IS 'User gender identity';
COMMENT ON COLUMN user_onboarding_profiles.zip_code IS 'User zip code (5 or 9 digit format)';
COMMENT ON COLUMN user_onboarding_profiles.location_state IS 'User state of residence';
COMMENT ON COLUMN user_onboarding_profiles.location_city IS 'User city of residence';
COMMENT ON COLUMN user_onboarding_profiles.household_size IS 'Number of people in household';
COMMENT ON COLUMN user_onboarding_profiles.dependents IS 'Number of dependents';
COMMENT ON COLUMN user_onboarding_profiles.relationship_status IS 'User relationship status';
COMMENT ON COLUMN user_onboarding_profiles.income_frequency IS 'Frequency of income payments';
COMMENT ON COLUMN user_onboarding_profiles.primary_income_source IS 'Primary source of income';
COMMENT ON COLUMN user_onboarding_profiles.employment_status IS 'Current employment status';
COMMENT ON COLUMN user_onboarding_profiles.industry IS 'Industry of employment';
COMMENT ON COLUMN user_onboarding_profiles.job_title IS 'Job title or position';
COMMENT ON COLUMN user_onboarding_profiles.naics_code IS 'NAICS industry classification code';
COMMENT ON COLUMN user_onboarding_profiles.current_savings IS 'Current savings amount';
COMMENT ON COLUMN user_onboarding_profiles.current_debt IS 'Current debt amount';
COMMENT ON COLUMN user_onboarding_profiles.credit_score_range IS 'Credit score range category'; 