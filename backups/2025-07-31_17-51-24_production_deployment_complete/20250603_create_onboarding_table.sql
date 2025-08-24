-- Create enum types for onboarding responses
CREATE TYPE financial_challenge_type AS ENUM (
    'budgeting',
    'debt',
    'savings',
    'investing',
    'income',
    'spending',
    'planning'
);

CREATE TYPE stress_handling_type AS ENUM (
    'mindfulness',
    'exercise',
    'social',
    'professional',
    'avoidance',
    'planning'
);

CREATE TYPE motivation_type AS ENUM (
    'goals',
    'family',
    'freedom',
    'security',
    'growth',
    'impact'
);

-- Create the user onboarding table
CREATE TABLE user_onboarding (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    financial_challenge financial_challenge_type NOT NULL,
    stress_handling stress_handling_type NOT NULL,
    motivation motivation_type NOT NULL,
    responses JSONB DEFAULT '{}',
    preferences JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc', NOW()),
    completed_at TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc', NOW()),
    UNIQUE(user_id)
);

-- Add onboarding_completed column to users table if it doesn't exist
ALTER TABLE users 
ADD COLUMN IF NOT EXISTS onboarding_completed BOOLEAN DEFAULT FALSE;

-- Create index for faster lookups
CREATE INDEX idx_user_onboarding_user_id ON user_onboarding(user_id);
CREATE INDEX idx_user_onboarding_completed_at ON user_onboarding(completed_at);

-- Create function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = TIMEZONE('utc', NOW());
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create trigger for updated_at
CREATE TRIGGER update_user_onboarding_updated_at
    BEFORE UPDATE ON user_onboarding
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Create RLS policies
ALTER TABLE user_onboarding ENABLE ROW LEVEL SECURITY;

-- Policy for users to read their own onboarding data
CREATE POLICY "Users can view own onboarding data"
    ON user_onboarding
    FOR SELECT
    TO authenticated
    USING (auth.uid() = user_id);

-- Policy for users to insert their own onboarding data
CREATE POLICY "Users can insert own onboarding data"
    ON user_onboarding
    FOR INSERT
    TO authenticated
    WITH CHECK (auth.uid() = user_id);

-- Policy for users to update their own onboarding data
CREATE POLICY "Users can update own onboarding data"
    ON user_onboarding
    FOR UPDATE
    TO authenticated
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

-- Create view for onboarding analytics (accessible by service role)
CREATE VIEW onboarding_analytics AS
SELECT 
    financial_challenge,
    COUNT(*) as count,
    COUNT(*) * 100.0 / (SELECT COUNT(*) FROM user_onboarding) as percentage
FROM user_onboarding
GROUP BY financial_challenge;

COMMENT ON TABLE user_onboarding IS 'Stores user onboarding responses and preferences';
COMMENT ON COLUMN user_onboarding.user_id IS 'References the auth.users table';
COMMENT ON COLUMN user_onboarding.responses IS 'Additional structured responses collected during onboarding';
COMMENT ON COLUMN user_onboarding.preferences IS 'User preferences and settings from onboarding'; 