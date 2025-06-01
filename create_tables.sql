-- Create users table
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create user_income_due_dates table
CREATE TABLE IF NOT EXISTS user_income_due_dates (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id),
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
CREATE TABLE IF NOT EXISTS user_expense_due_dates (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id),
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
CREATE TABLE IF NOT EXISTS daily_cashflow (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id),
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
CREATE INDEX IF NOT EXISTS idx_income_user_id ON user_income_due_dates(user_id);
CREATE INDEX IF NOT EXISTS idx_expense_user_id ON user_expense_due_dates(user_id);
CREATE INDEX IF NOT EXISTS idx_cashflow_user_id ON daily_cashflow(user_id);
CREATE INDEX IF NOT EXISTS idx_cashflow_date ON daily_cashflow(forecast_date);

-- Create trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Add triggers to all tables
CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_user_income_due_dates_updated_at
    BEFORE UPDATE ON user_income_due_dates
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_user_expense_due_dates_updated_at
    BEFORE UPDATE ON user_expense_due_dates
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_daily_cashflow_updated_at
    BEFORE UPDATE ON daily_cashflow
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column(); 