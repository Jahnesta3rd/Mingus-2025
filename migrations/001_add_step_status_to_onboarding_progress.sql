-- Migration: Add step_status column to onboarding_progress table
-- Date: 2025-01-27
-- Description: Adds step_status column for granular step tracking in onboarding progress

-- Add step_status column to onboarding_progress table
ALTER TABLE onboarding_progress 
ADD COLUMN step_status TEXT;

-- Add comment to document the column
COMMENT ON COLUMN onboarding_progress.step_status IS 'JSON string storing step completion status for granular progress tracking';

-- Update existing records to have empty step_status (will be populated by application logic)
UPDATE onboarding_progress 
SET step_status = '{}' 
WHERE step_status IS NULL; 