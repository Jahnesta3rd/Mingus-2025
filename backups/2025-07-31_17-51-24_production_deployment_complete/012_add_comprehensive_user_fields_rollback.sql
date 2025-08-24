-- Rollback Migration: Remove comprehensive user profile fields
-- Date: 2025-01-27
-- Description: Rollback for migration 012_add_comprehensive_user_fields

-- Drop triggers first
DROP TRIGGER IF EXISTS trigger_update_profile_completion ON users;

-- Drop functions
DROP FUNCTION IF EXISTS update_profile_completion_trigger();
DROP FUNCTION IF EXISTS calculate_profile_completion_percentage(UUID);

-- Remove columns from users table
-- Personal Information
ALTER TABLE users DROP COLUMN IF EXISTS first_name;
ALTER TABLE users DROP COLUMN IF EXISTS last_name;
ALTER TABLE users DROP COLUMN IF EXISTS date_of_birth;
ALTER TABLE users DROP COLUMN IF EXISTS zip_code;
ALTER TABLE users DROP COLUMN IF EXISTS phone_number;
ALTER TABLE users DROP COLUMN IF EXISTS email_verification_status;

-- Financial data
ALTER TABLE users DROP COLUMN IF EXISTS monthly_income;
ALTER TABLE users DROP COLUMN IF EXISTS income_frequency;
ALTER TABLE users DROP COLUMN IF EXISTS primary_income_source;
ALTER TABLE users DROP COLUMN IF EXISTS current_savings_balance;
ALTER TABLE users DROP COLUMN IF EXISTS total_debt_amount;
ALTER TABLE users DROP COLUMN IF EXISTS credit_score_range;
ALTER TABLE users DROP COLUMN IF EXISTS employment_status;

-- Demographics
ALTER TABLE users DROP COLUMN IF EXISTS age_range;
ALTER TABLE users DROP COLUMN IF EXISTS marital_status;
ALTER TABLE users DROP COLUMN IF EXISTS dependents_count;
ALTER TABLE users DROP COLUMN IF EXISTS household_size;
ALTER TABLE users DROP COLUMN IF EXISTS education_level;
ALTER TABLE users DROP COLUMN IF EXISTS occupation;
ALTER TABLE users DROP COLUMN IF EXISTS industry;
ALTER TABLE users DROP COLUMN IF EXISTS years_of_experience;

-- Goals and preferences
ALTER TABLE users DROP COLUMN IF EXISTS primary_financial_goal;
ALTER TABLE users DROP COLUMN IF EXISTS risk_tolerance_level;
ALTER TABLE users DROP COLUMN IF EXISTS financial_knowledge_level;
ALTER TABLE users DROP COLUMN IF EXISTS preferred_contact_method;
ALTER TABLE users DROP COLUMN IF EXISTS notification_preferences;

-- Health and wellness
ALTER TABLE users DROP COLUMN IF EXISTS health_checkin_frequency;
ALTER TABLE users DROP COLUMN IF EXISTS stress_level_baseline;
ALTER TABLE users DROP COLUMN IF EXISTS wellness_goals;

-- Compliance and preferences
ALTER TABLE users DROP COLUMN IF EXISTS gdpr_consent_status;
ALTER TABLE users DROP COLUMN IF EXISTS data_sharing_preferences;
ALTER TABLE users DROP COLUMN IF EXISTS profile_completion_percentage;
ALTER TABLE users DROP COLUMN IF EXISTS onboarding_step;

-- Drop constraints (they will be automatically dropped with columns, but explicit for safety)
ALTER TABLE users DROP CONSTRAINT IF EXISTS valid_phone_number;
ALTER TABLE users DROP CONSTRAINT IF EXISTS valid_zip_code;
ALTER TABLE users DROP CONSTRAINT IF EXISTS valid_dependents_count;
ALTER TABLE users DROP CONSTRAINT IF EXISTS valid_household_size;
ALTER TABLE users DROP CONSTRAINT IF EXISTS valid_profile_completion;
ALTER TABLE users DROP CONSTRAINT IF EXISTS valid_onboarding_step;

-- Drop indexes
DROP INDEX IF EXISTS idx_users_first_name;
DROP INDEX IF EXISTS idx_users_last_name;
DROP INDEX IF EXISTS idx_users_zip_code;
DROP INDEX IF EXISTS idx_users_phone_number;
DROP INDEX IF EXISTS idx_users_email_verification;
DROP INDEX IF EXISTS idx_users_monthly_income;
DROP INDEX IF EXISTS idx_users_credit_score;
DROP INDEX IF EXISTS idx_users_age_range;
DROP INDEX IF EXISTS idx_users_marital_status;
DROP INDEX IF EXISTS idx_users_employment_status;
DROP INDEX IF EXISTS idx_users_risk_tolerance;
DROP INDEX IF EXISTS idx_users_financial_knowledge;
DROP INDEX IF EXISTS idx_users_profile_completion;
DROP INDEX IF EXISTS idx_users_onboarding_step;
DROP INDEX IF EXISTS idx_users_gdpr_consent;
DROP INDEX IF EXISTS idx_users_name_search;
DROP INDEX IF EXISTS idx_users_demographics;
DROP INDEX IF EXISTS idx_users_financial_profile;

-- Drop ENUM types (only if they're not used elsewhere)
-- Note: These will only be dropped if they're not used by other tables
DROP TYPE IF EXISTS income_frequency_type;
DROP TYPE IF EXISTS credit_score_range_type;
DROP TYPE IF EXISTS age_range_type;
DROP TYPE IF EXISTS marital_status_type;
DROP TYPE IF EXISTS years_of_experience_type;
DROP TYPE IF EXISTS risk_tolerance_level_type;
DROP TYPE IF EXISTS financial_knowledge_level_type;
DROP TYPE IF EXISTS health_checkin_frequency_type;

-- Insert rollback record
INSERT INTO migration_log (migration_name, applied_at, description)
VALUES ('012_add_comprehensive_user_fields_rollback', NOW(), 'Rollback: Removed comprehensive user profile fields')
ON CONFLICT (migration_name) DO NOTHING; 