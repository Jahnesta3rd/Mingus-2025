-- User Income Due Dates table
CREATE TABLE IF NOT EXISTS user_income_due_dates (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL,
    income_type TEXT NOT NULL,
    amount NUMERIC NOT NULL,
    frequency TEXT NOT NULL,
    preferred_day INTEGER,  -- 0=Monday through 6=Sunday
    start_date DATE NOT NULL,
    due_date INTEGER,  -- Day of month for monthly payments
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- User Expense Due Dates table
CREATE TABLE IF NOT EXISTS user_expense_due_dates (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL,
    expense_type TEXT NOT NULL,
    amount NUMERIC NOT NULL,
    frequency TEXT NOT NULL,
    preferred_day INTEGER,  -- 0=Monday through 6=Sunday
    start_date DATE NOT NULL,
    due_date INTEGER,  -- Day of month for monthly payments
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Add indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_income_user_id ON user_income_due_dates(user_id);
CREATE INDEX IF NOT EXISTS idx_expense_user_id ON user_expense_due_dates(user_id); 