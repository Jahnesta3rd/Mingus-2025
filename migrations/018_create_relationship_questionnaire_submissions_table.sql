-- Migration: Create relationship_questionnaire_submissions table
-- Description: Stores relationship questionnaire submissions with email addresses for follow-up

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

-- Add comments
COMMENT ON TABLE relationship_questionnaire_submissions IS 'Store relationship questionnaire submissions with email addresses for follow-up';
COMMENT ON COLUMN relationship_questionnaire_submissions.id IS 'Unique identifier for the submission';
COMMENT ON COLUMN relationship_questionnaire_submissions.email IS 'Email address of the person who took the assessment';
COMMENT ON COLUMN relationship_questionnaire_submissions.answers IS 'JSON object containing the question answers';
COMMENT ON COLUMN relationship_questionnaire_submissions.total_score IS 'Calculated connection score (0-20)';
COMMENT ON COLUMN relationship_questionnaire_submissions.connection_level IS 'Text description of connection level (LOW, MODERATE, HIGH)';
COMMENT ON COLUMN relationship_questionnaire_submissions.connection_description IS 'Detailed description of the connection level';
COMMENT ON COLUMN relationship_questionnaire_submissions.has_signed_up IS 'Whether the user has signed up for a MINGUS account';
COMMENT ON COLUMN relationship_questionnaire_submissions.user_id IS 'User ID if the person has signed up';
COMMENT ON COLUMN relationship_questionnaire_submissions.source IS 'Source of the questionnaire (e.g., "relationship_questionnaire")';
COMMENT ON COLUMN relationship_questionnaire_submissions.utm_source IS 'UTM source parameter for tracking';
COMMENT ON COLUMN relationship_questionnaire_submissions.utm_medium IS 'UTM medium parameter for tracking';
COMMENT ON COLUMN relationship_questionnaire_submissions.utm_campaign IS 'UTM campaign parameter for tracking';
COMMENT ON COLUMN relationship_questionnaire_submissions.submitted_at IS 'When the questionnaire was submitted';
COMMENT ON COLUMN relationship_questionnaire_submissions.signed_up_at IS 'When the user signed up (if applicable)';

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_relationship_questionnaire_submissions_email ON relationship_questionnaire_submissions (email);
CREATE INDEX IF NOT EXISTS idx_relationship_questionnaire_submissions_submitted_at ON relationship_questionnaire_submissions (submitted_at DESC);
CREATE INDEX IF NOT EXISTS idx_relationship_questionnaire_submissions_has_signed_up ON relationship_questionnaire_submissions (has_signed_up);
CREATE INDEX IF NOT EXISTS idx_relationship_questionnaire_submissions_source ON relationship_questionnaire_submissions (source);
CREATE INDEX IF NOT EXISTS idx_relationship_questionnaire_submissions_user_id ON relationship_questionnaire_submissions (user_id) WHERE user_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_relationship_questionnaire_submissions_connection_level ON relationship_questionnaire_submissions (connection_level);
