-- Create response type enum
DO $$ BEGIN
    CREATE TYPE response_type AS ENUM (
        'income',
        'expense',
        'savings_goal',
        'debt',
        'investment',
        'risk_tolerance',
        'financial_knowledge',
        'spending_habit',
        'emergency_fund',
        'retirement_plan'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Create response value type enum
DO $$ BEGIN
    CREATE TYPE response_value_type AS ENUM (
        'number',
        'text',
        'boolean',
        'date',
        'range',
        'multiple_choice',
        'single_choice'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Create onboarding responses table
CREATE TABLE IF NOT EXISTS onboarding_responses (
    id UUID DEFAULT extensions.uuid_generate_v4() PRIMARY KEY,
    onboarding_id UUID NOT NULL REFERENCES user_onboarding(id) ON DELETE CASCADE,
    response_type response_type NOT NULL,
    response_value_type response_value_type NOT NULL,
    response_value JSONB NOT NULL,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Add indexes
CREATE INDEX IF NOT EXISTS idx_onboarding_responses_onboarding_id 
ON onboarding_responses(onboarding_id);

CREATE INDEX IF NOT EXISTS idx_onboarding_responses_type 
ON onboarding_responses(response_type);

-- Create updated_at trigger
CREATE OR REPLACE FUNCTION update_onboarding_responses_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Drop and recreate the trigger
DROP TRIGGER IF EXISTS update_onboarding_responses_updated_at ON onboarding_responses;
CREATE TRIGGER update_onboarding_responses_updated_at
    BEFORE UPDATE ON onboarding_responses
    FOR EACH ROW
    EXECUTE FUNCTION update_onboarding_responses_updated_at();

-- Enable RLS
ALTER TABLE onboarding_responses ENABLE ROW LEVEL SECURITY;

-- Create RLS policies
CREATE POLICY "Users can view own onboarding responses"
    ON onboarding_responses
    FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM user_onboarding
            WHERE id = onboarding_responses.onboarding_id
            AND user_id = auth.uid()
        )
    );

CREATE POLICY "Users can insert own onboarding responses"
    ON onboarding_responses
    FOR INSERT
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM user_onboarding
            WHERE id = onboarding_responses.onboarding_id
            AND user_id = auth.uid()
        )
    );

CREATE POLICY "Users can update own onboarding responses"
    ON onboarding_responses
    FOR UPDATE
    USING (
        EXISTS (
            SELECT 1 FROM user_onboarding
            WHERE id = onboarding_responses.onboarding_id
            AND user_id = auth.uid()
        )
    )
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM user_onboarding
            WHERE id = onboarding_responses.onboarding_id
            AND user_id = auth.uid()
        )
    );

-- Create analytics view
CREATE OR REPLACE VIEW onboarding_responses_analytics AS
SELECT 
    response_type,
    response_value_type,
    COUNT(*) as response_count,
    COUNT(DISTINCT onboarding_id) as unique_users,
    COUNT(*) * 100.0 / NULLIF((SELECT COUNT(*) FROM onboarding_responses), 0) as percentage
FROM onboarding_responses
GROUP BY response_type, response_value_type;

-- Add comments
COMMENT ON TABLE onboarding_responses IS 'Stores detailed responses from user onboarding process';
COMMENT ON COLUMN onboarding_responses.onboarding_id IS 'References the user_onboarding table';
COMMENT ON COLUMN onboarding_responses.response_type IS 'Category of the response (income, expense, etc.)';
COMMENT ON COLUMN onboarding_responses.response_value_type IS 'Data type of the response value';
COMMENT ON COLUMN onboarding_responses.response_value IS 'The actual response value in JSONB format';
COMMENT ON COLUMN onboarding_responses.metadata IS 'Additional metadata about the response'; 