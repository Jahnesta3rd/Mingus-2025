-- Migration: Add Financial Questionnaire Fields
-- Date: 2025-01-27
-- Description: Add fields to support financial questionnaire functionality

-- Add questionnaire fields to user_profile table
ALTER TABLE user_profile ADD financial_health_score INTEGER DEFAULT 0;
ALTER TABLE user_profile ADD financial_health_level VARCHAR(50);
ALTER TABLE user_profile ADD questionnaire_completed_at TIMESTAMP;
ALTER TABLE user_profile ADD onboarding_type VARCHAR(20) DEFAULT 'detailed';
ALTER TABLE user_profile ADD risk_tolerance INTEGER DEFAULT 3;

-- Add questionnaire responses to onboarding_progress table
ALTER TABLE onboarding_progress ADD questionnaire_responses TEXT;

-- Add indexes for better performance
CREATE INDEX idx_user_profile_onboarding_type ON user_profile(onboarding_type);
CREATE INDEX idx_user_profile_health_score ON user_profile(financial_health_score);

-- Update existing records to have default values
UPDATE user_profile SET onboarding_type = 'detailed' WHERE onboarding_type IS NULL;
UPDATE user_profile SET risk_tolerance = 3 WHERE risk_tolerance IS NULL;
UPDATE user_profile SET financial_health_score = 0 WHERE financial_health_score IS NULL; 