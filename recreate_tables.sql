-- Drop existing tables and types
DROP TABLE IF EXISTS daily_cashflow CASCADE;
DROP TABLE IF EXISTS user_income_due_dates CASCADE;
DROP TABLE IF EXISTS user_expense_due_dates CASCADE;

-- Create user_income_due_dates table
CREATE TABLE user_income_due_dates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id),
    income_type VARCHAR(50) NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    frequency VARCHAR(50) NOT NULL,
    preferred_day INTEGER,
    start_date DATE NOT NULL,
    due_date INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT valid_income_type CHECK (income_type IN ('salary', 'rental', 'freelance', 'other')),
    CONSTRAINT valid_frequency CHECK (frequency IN ('weekly', 'bi-weekly', 'monthly', 'quarterly', 'annually'))
);

-- Create user_expense_due_dates table
CREATE TABLE user_expense_due_dates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id),
    expense_type VARCHAR(50) NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    frequency VARCHAR(50) NOT NULL,
    preferred_day INTEGER,
    start_date DATE NOT NULL,
    due_date INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT valid_expense_type CHECK (expense_type IN ('rent', 'utilities', 'car_payment', 'insurance', 'other')),
    CONSTRAINT valid_frequency CHECK (frequency IN ('weekly', 'bi-weekly', 'monthly', 'quarterly', 'annually'))
);

-- Create daily_cashflow table
CREATE TABLE daily_cashflow (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id),
    forecast_date DATE NOT NULL,
    opening_balance DECIMAL(10,2) NOT NULL,
    income DECIMAL(10,2) NOT NULL DEFAULT 0,
    expenses DECIMAL(10,2) NOT NULL DEFAULT 0,
    closing_balance DECIMAL(10,2) NOT NULL,
    net_change DECIMAL(10,2) NOT NULL,
    balance_status VARCHAR(20) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT valid_balance_status CHECK (balance_status IN ('healthy', 'warning', 'danger')),
    CONSTRAINT unique_user_date UNIQUE (user_id, forecast_date)
);

-- Create indexes for better performance
CREATE INDEX idx_income_user_id ON user_income_due_dates(user_id);
CREATE INDEX idx_expense_user_id ON user_expense_due_dates(user_id);
CREATE INDEX idx_cashflow_user_id ON daily_cashflow(user_id);
CREATE INDEX idx_cashflow_date ON daily_cashflow(forecast_date);

-- Grant permissions
GRANT ALL ON user_income_due_dates TO postgres, anon, authenticated;
GRANT ALL ON user_expense_due_dates TO postgres, anon, authenticated;
GRANT ALL ON daily_cashflow TO postgres, anon, authenticated;

-- Enable RLS
ALTER TABLE user_income_due_dates ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_expense_due_dates ENABLE ROW LEVEL SECURITY;
ALTER TABLE daily_cashflow ENABLE ROW LEVEL SECURITY;

-- Create development policies (allow all operations)
CREATE POLICY "Enable all operations for development"
ON user_income_due_dates FOR ALL
USING (true)
WITH CHECK (true);

CREATE POLICY "Enable all operations for development"
ON user_expense_due_dates FOR ALL
USING (true)
WITH CHECK (true);

CREATE POLICY "Enable all operations for development"
ON daily_cashflow FOR ALL
USING (true)
WITH CHECK (true); 