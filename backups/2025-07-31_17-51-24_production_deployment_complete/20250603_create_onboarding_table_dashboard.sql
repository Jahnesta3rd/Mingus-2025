-- Create enum types for onboarding responses
DO $$ BEGIN
    CREATE TYPE financial_challenge_type AS ENUM (
        'budgeting',
        'debt',
        'savings',
        'investing',
        'income',
        'spending',
        'planning'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE stress_handling_type AS ENUM (
        'mindfulness',
        'exercise',
        'social',
        'professional',
        'avoidance',
        'planning'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE motivation_type AS ENUM (
        'goals',
        'family',
        'freedom',
        'security',
        'growth',
        'impact'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Create the user onboarding table if it doesn't exist
CREATE TABLE IF NOT EXISTS user_onboarding (
    id UUID DEFAULT extensions.uuid_generate_v4() PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    financial_challenge financial_challenge_type NOT NULL,
    stress_handling stress_handling_type NOT NULL,
    motivation motivation_type NOT NULL,
    responses JSONB DEFAULT '{}',
    preferences JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Add unique constraint if it doesn't exist
DO $$ BEGIN
    ALTER TABLE user_onboarding ADD CONSTRAINT user_onboarding_user_id_key UNIQUE (user_id);
EXCEPTION
    WHEN duplicate_table THEN null;
END $$;

-- Create indexes if they don't exist
DO $$ BEGIN
    CREATE INDEX IF NOT EXISTS idx_user_onboarding_user_id ON user_onboarding(user_id);
    CREATE INDEX IF NOT EXISTS idx_user_onboarding_completed_at ON user_onboarding(completed_at);
EXCEPTION
    WHEN duplicate_table THEN null;
END $$;

-- Create or replace the updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Drop and recreate the trigger
DROP TRIGGER IF EXISTS update_user_onboarding_updated_at ON user_onboarding;
CREATE TRIGGER update_user_onboarding_updated_at
    BEFORE UPDATE ON user_onboarding
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Enable RLS
ALTER TABLE user_onboarding ENABLE ROW LEVEL SECURITY;

-- Drop existing policies if they exist
DROP POLICY IF EXISTS "Users can view own onboarding data" ON user_onboarding;
DROP POLICY IF EXISTS "Users can insert own onboarding data" ON user_onboarding;
DROP POLICY IF EXISTS "Users can update own onboarding data" ON user_onboarding;

-- Create RLS policies
CREATE POLICY "Users can view own onboarding data"
    ON user_onboarding
    FOR SELECT
    TO authenticated
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own onboarding data"
    ON user_onboarding
    FOR INSERT
    TO authenticated
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own onboarding data"
    ON user_onboarding
    FOR UPDATE
    TO authenticated
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

-- Create analytics view if it doesn't exist
CREATE OR REPLACE VIEW onboarding_analytics AS
SELECT 
    financial_challenge,
    COUNT(*) as count,
    COUNT(*) * 100.0 / NULLIF((SELECT COUNT(*) FROM user_onboarding), 0) as percentage
FROM user_onboarding
GROUP BY financial_challenge;

-- Add comments
COMMENT ON TABLE user_onboarding IS 'Stores user onboarding responses and preferences';
COMMENT ON COLUMN user_onboarding.user_id IS 'References the auth.users table';
COMMENT ON COLUMN user_onboarding.responses IS 'Additional structured responses collected during onboarding';
COMMENT ON COLUMN user_onboarding.preferences IS 'User preferences and settings from onboarding';
COMMENT ON COLUMN user_onboarding.completed_at IS 'Timestamp when the user completed onboarding. NULL indicates incomplete onboarding'; 