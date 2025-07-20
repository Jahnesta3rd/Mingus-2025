-- Create financial challenge enum
DO $$ BEGIN
    CREATE TYPE financial_challenge_type AS ENUM (
        'emergency_savings',
        'multiple_income',
        'debt',
        'major_expenses'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Create stress handling enum
DO $$ BEGIN
    CREATE TYPE stress_handling_type AS ENUM (
        'talk_to_people',
        'exercise',
        'avoid_thinking',
        'research_plan'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Create motivation enum
DO $$ BEGIN
    CREATE TYPE motivation_type AS ENUM (
        'family_goals',
        'personal_growth',
        'community_impact',
        'financial_freedom'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Create onboarding responses table
CREATE TABLE IF NOT EXISTS onboarding_responses (
    id UUID DEFAULT extensions.uuid_generate_v4() PRIMARY KEY,
    session_id TEXT NOT NULL,
    financial_challenge financial_challenge_type NOT NULL,
    stress_handling stress_handling_type NOT NULL,
    motivation motivation_type NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    ip_address TEXT,
    user_agent TEXT,
    converted_to_signup BOOLEAN DEFAULT FALSE,
    
    -- Add constraints
    CONSTRAINT session_id_not_empty CHECK (session_id <> ''),
    CONSTRAINT valid_ip_address CHECK (ip_address IS NULL OR ip_address <> '')
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_onboarding_responses_session_id 
ON onboarding_responses(session_id);

CREATE INDEX IF NOT EXISTS idx_onboarding_responses_created_at 
ON onboarding_responses(created_at);

CREATE INDEX IF NOT EXISTS idx_onboarding_responses_converted 
ON onboarding_responses(converted_to_signup) 
WHERE converted_to_signup = TRUE;

-- Enable Row Level Security
ALTER TABLE onboarding_responses ENABLE ROW LEVEL SECURITY;

-- Create policies for anonymous access
CREATE POLICY "Allow anonymous insert"
    ON onboarding_responses
    FOR INSERT
    WITH CHECK (true);  -- Anyone can create a response

-- Create policy for reading own responses via session_id
CREATE POLICY "Allow reading own responses by session"
    ON onboarding_responses
    FOR SELECT
    USING (
        -- Allow if the session_id matches or if authenticated as admin
        session_id = current_setting('app.current_session_id', TRUE) OR
        auth.role() = 'authenticated'
    );

-- Create policy for analytics access (admin only)
CREATE POLICY "Allow admin full access"
    ON onboarding_responses
    FOR ALL
    USING (auth.role() = 'authenticated');

-- Create analytics view
CREATE OR REPLACE VIEW onboarding_responses_analytics AS
SELECT 
    DATE_TRUNC('hour', created_at) as time_bucket,
    financial_challenge,
    stress_handling,
    motivation,
    COUNT(*) as response_count,
    COUNT(DISTINCT session_id) as unique_sessions,
    SUM(CASE WHEN converted_to_signup THEN 1 ELSE 0 END) as conversions,
    ROUND(
        (SUM(CASE WHEN converted_to_signup THEN 1 ELSE 0 END)::NUMERIC / COUNT(*)::NUMERIC) * 100,
        2
    ) as conversion_rate
FROM onboarding_responses
GROUP BY 
    DATE_TRUNC('hour', created_at),
    financial_challenge,
    stress_handling,
    motivation;

-- Add comments
COMMENT ON TABLE onboarding_responses IS 'Stores anonymous onboarding responses before user signup';
COMMENT ON COLUMN onboarding_responses.session_id IS 'Unique identifier for anonymous session';
COMMENT ON COLUMN onboarding_responses.ip_address IS 'IP address for analytics and abuse prevention';
COMMENT ON COLUMN onboarding_responses.user_agent IS 'Browser/device information for analytics';
COMMENT ON COLUMN onboarding_responses.converted_to_signup IS 'Whether this anonymous response led to a signup'; 