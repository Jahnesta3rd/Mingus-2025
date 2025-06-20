-- Drop existing tables
DROP TABLE IF EXISTS daily_cashflow CASCADE;
DROP TABLE IF EXISTS user_income_due_dates CASCADE;
DROP TABLE IF EXISTS user_expense_due_dates CASCADE;

-- Create user_income_due_dates table
CREATE TABLE user_income_due_dates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    income_type VARCHAR(50) NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    frequency VARCHAR(50) NOT NULL,
    preferred_day INTEGER,
    start_date DATE NOT NULL,
    due_date INTEGER,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- Create user_expense_due_dates table
CREATE TABLE user_expense_due_dates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    expense_type VARCHAR(50) NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    frequency VARCHAR(50) NOT NULL,
    preferred_day INTEGER,
    start_date DATE NOT NULL,
    due_date INTEGER,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- Create daily_cashflow table
CREATE TABLE daily_cashflow (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    forecast_date DATE NOT NULL,
    opening_balance DECIMAL(10,2) NOT NULL,
    income DECIMAL(10,2) NOT NULL DEFAULT 0,
    expenses DECIMAL(10,2) NOT NULL DEFAULT 0,
    closing_balance DECIMAL(10,2) NOT NULL,
    net_change DECIMAL(10,2) NOT NULL,
    balance_status VARCHAR(20) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- Create indexes
CREATE INDEX idx_income_user_id ON user_income_due_dates(user_id);
CREATE INDEX idx_expense_user_id ON user_expense_due_dates(user_id);
CREATE INDEX idx_cashflow_user_id ON daily_cashflow(user_id);
CREATE INDEX idx_cashflow_date ON daily_cashflow(forecast_date);

-- Grant permissions
GRANT ALL ON user_income_due_dates TO authenticated;
GRANT ALL ON user_expense_due_dates TO authenticated;
GRANT ALL ON daily_cashflow TO authenticated;

-- Enable RLS
ALTER TABLE user_income_due_dates ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_expense_due_dates ENABLE ROW LEVEL SECURITY;
ALTER TABLE daily_cashflow ENABLE ROW LEVEL SECURITY;

-- Create RLS policies
CREATE POLICY "Users can manage their own income schedules"
ON user_income_due_dates FOR ALL
TO authenticated
USING (auth.uid() = user_id)
WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can manage their own expense schedules"
ON user_expense_due_dates FOR ALL
TO authenticated
USING (auth.uid() = user_id)
WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can manage their own cashflow"
ON daily_cashflow FOR ALL
TO authenticated
USING (auth.uid() = user_id)
WITH CHECK (auth.uid() = user_id); 