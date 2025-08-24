-- First, drop existing tables (if they exist) with CASCADE to handle dependencies
DROP TABLE IF EXISTS public.daily_cashflow CASCADE;
DROP TABLE IF EXISTS public.user_income_due_dates CASCADE;
DROP TABLE IF EXISTS public.user_expense_due_dates CASCADE;

-- Create user_income_due_dates table with correct auth schema reference
CREATE TABLE public.user_income_due_dates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    income_type VARCHAR(50) NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    frequency VARCHAR(50) NOT NULL,
    preferred_day INTEGER,
    start_date DATE NOT NULL,
    due_date INTEGER,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),
    CONSTRAINT valid_income_type CHECK (income_type IN ('salary', 'rental', 'freelance', 'other')),
    CONSTRAINT valid_frequency CHECK (frequency IN ('weekly', 'bi-weekly', 'monthly', 'quarterly', 'annually'))
);

-- Create user_expense_due_dates table with correct auth schema reference
CREATE TABLE public.user_expense_due_dates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    expense_type VARCHAR(50) NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    frequency VARCHAR(50) NOT NULL,
    preferred_day INTEGER,
    start_date DATE NOT NULL,
    due_date INTEGER,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),
    CONSTRAINT valid_expense_type CHECK (expense_type IN ('rent', 'utilities', 'car_payment', 'insurance', 'other')),
    CONSTRAINT valid_frequency CHECK (frequency IN ('weekly', 'bi-weekly', 'monthly', 'quarterly', 'annually'))
);

-- Create daily_cashflow table with correct auth schema reference
CREATE TABLE public.daily_cashflow (
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
    updated_at TIMESTAMPTZ DEFAULT now(),
    CONSTRAINT valid_balance_status CHECK (balance_status IN ('healthy', 'warning', 'danger')),
    CONSTRAINT unique_user_date UNIQUE (user_id, forecast_date)
);

-- Create indexes for better performance
CREATE INDEX idx_income_user_id ON public.user_income_due_dates(user_id);
CREATE INDEX idx_expense_user_id ON public.user_expense_due_dates(user_id);
CREATE INDEX idx_cashflow_user_id ON public.daily_cashflow(user_id);
CREATE INDEX idx_cashflow_date ON public.daily_cashflow(forecast_date);

-- Grant necessary permissions
GRANT ALL ON public.user_income_due_dates TO postgres, anon, authenticated, service_role;
GRANT ALL ON public.user_expense_due_dates TO postgres, anon, authenticated, service_role;
GRANT ALL ON public.daily_cashflow TO postgres, anon, authenticated, service_role;

-- Enable RLS
ALTER TABLE public.user_income_due_dates ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.user_expense_due_dates ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.daily_cashflow ENABLE ROW LEVEL SECURITY;

-- Create development policies (allow all operations)
DROP POLICY IF EXISTS "Enable all operations for development" ON public.user_income_due_dates;
CREATE POLICY "Enable all operations for development"
ON public.user_income_due_dates FOR ALL
USING (true)
WITH CHECK (true);

DROP POLICY IF EXISTS "Enable all operations for development" ON public.user_expense_due_dates;
CREATE POLICY "Enable all operations for development"
ON public.user_expense_due_dates FOR ALL
USING (true)
WITH CHECK (true);

DROP POLICY IF EXISTS "Enable all operations for development" ON public.daily_cashflow;
CREATE POLICY "Enable all operations for development"
ON public.daily_cashflow FOR ALL
USING (true)
WITH CHECK (true); 