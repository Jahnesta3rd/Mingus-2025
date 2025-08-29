-- Migration: Create questionnaire_submissions table
-- Description: Stores questionnaire submissions with email addresses for follow-up

-- Create questionnaire_submissions table
CREATE TABLE IF NOT EXISTS questionnaire_submissions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) NOT NULL,
    
    -- Questionnaire data
    answers JSONB NOT NULL,  -- Store the 5 question answers
    total_score INTEGER NOT NULL,
    wellness_level VARCHAR(100) NOT NULL,
    wellness_description TEXT,
    
    -- User journey tracking
    has_signed_up BOOLEAN DEFAULT FALSE,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    
    -- Marketing data
    source VARCHAR(100) DEFAULT 'financial_wellness_questionnaire',
    utm_source VARCHAR(100),
    utm_medium VARCHAR(100),
    utm_campaign VARCHAR(100),
    
    -- Timestamps
    submitted_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    signed_up_at TIMESTAMP WITH TIME ZONE,
    
    -- Constraints
    CONSTRAINT questionnaire_submissions_email_unique UNIQUE (email)
);

-- Add comments
COMMENT ON TABLE questionnaire_submissions IS 'Store questionnaire submissions with email addresses for follow-up';
COMMENT ON COLUMN questionnaire_submissions.id IS 'Unique identifier for the submission';
COMMENT ON COLUMN questionnaire_submissions.email IS 'Email address of the person who took the assessment';
COMMENT ON COLUMN questionnaire_submissions.answers IS 'JSON object containing the 5 question answers';
COMMENT ON COLUMN questionnaire_submissions.total_score IS 'Calculated wellness score (0-100)';
COMMENT ON COLUMN questionnaire_submissions.wellness_level IS 'Text description of wellness level (e.g., "Excellent Financial Wellness")';
COMMENT ON COLUMN questionnaire_submissions.wellness_description IS 'Detailed description of the wellness level';
COMMENT ON COLUMN questionnaire_submissions.has_signed_up IS 'Whether the user has signed up for a MINGUS account';
COMMENT ON COLUMN questionnaire_submissions.user_id IS 'User ID if the person has signed up';
COMMENT ON COLUMN questionnaire_submissions.source IS 'Source of the questionnaire (e.g., "financial_wellness_questionnaire")';
COMMENT ON COLUMN questionnaire_submissions.utm_source IS 'UTM source parameter for tracking';
COMMENT ON COLUMN questionnaire_submissions.utm_medium IS 'UTM medium parameter for tracking';
COMMENT ON COLUMN questionnaire_submissions.utm_campaign IS 'UTM campaign parameter for tracking';
COMMENT ON COLUMN questionnaire_submissions.submitted_at IS 'When the questionnaire was submitted';
COMMENT ON COLUMN questionnaire_submissions.signed_up_at IS 'When the user signed up (if applicable)';

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_questionnaire_submissions_email ON questionnaire_submissions (email);
CREATE INDEX IF NOT EXISTS idx_questionnaire_submissions_submitted_at ON questionnaire_submissions (submitted_at DESC);
CREATE INDEX IF NOT EXISTS idx_questionnaire_submissions_has_signed_up ON questionnaire_submissions (has_signed_up);
CREATE INDEX IF NOT EXISTS idx_questionnaire_submissions_source ON questionnaire_submissions (source);
CREATE INDEX IF NOT EXISTS idx_questionnaire_submissions_user_id ON questionnaire_submissions (user_id) WHERE user_id IS NOT NULL;

-- Add RLS (Row Level Security) policies if using Supabase
-- Note: These are commented out as they may not be needed for this use case
/*
ALTER TABLE questionnaire_submissions ENABLE ROW LEVEL SECURITY;

-- Policy for users to view their own submissions
CREATE POLICY "Users can view their own questionnaire submissions" ON questionnaire_submissions
    FOR SELECT USING (auth.uid() = user_id);

-- Policy for inserting new submissions (no user_id required)
CREATE POLICY "Anyone can insert questionnaire submissions" ON questionnaire_submissions
    FOR INSERT WITH CHECK (true);

-- Policy for updating submissions (only if user_id matches)
CREATE POLICY "Users can update their own questionnaire submissions" ON questionnaire_submissions
    FOR UPDATE USING (auth.uid() = user_id);
*/
