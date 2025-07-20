-- Grant permissions for user_income_due_dates
GRANT SELECT, INSERT, UPDATE, DELETE ON user_income_due_dates TO anon;
GRANT SELECT, INSERT, UPDATE, DELETE ON user_income_due_dates TO authenticated;

-- Grant permissions for user_expense_due_dates
GRANT SELECT, INSERT, UPDATE, DELETE ON user_expense_due_dates TO anon;
GRANT SELECT, INSERT, UPDATE, DELETE ON user_expense_due_dates TO authenticated;

-- Grant permissions for daily_cashflow
GRANT SELECT, INSERT, UPDATE, DELETE ON daily_cashflow TO anon;
GRANT SELECT, INSERT, UPDATE, DELETE ON daily_cashflow TO authenticated;

-- Enable RLS on the tables
ALTER TABLE user_income_due_dates ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_expense_due_dates ENABLE ROW LEVEL SECURITY;
ALTER TABLE daily_cashflow ENABLE ROW LEVEL SECURITY;

-- Create RLS policies for user_income_due_dates
CREATE POLICY "Users can view their own income schedules"
ON user_income_due_dates FOR SELECT
USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own income schedules"
ON user_income_due_dates FOR INSERT
WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own income schedules"
ON user_income_due_dates FOR UPDATE
USING (auth.uid() = user_id)
WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can delete their own income schedules"
ON user_income_due_dates FOR DELETE
USING (auth.uid() = user_id);

-- Create RLS policies for user_expense_due_dates
CREATE POLICY "Users can view their own expense schedules"
ON user_expense_due_dates FOR SELECT
USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own expense schedules"
ON user_expense_due_dates FOR INSERT
WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own expense schedules"
ON user_expense_due_dates FOR UPDATE
USING (auth.uid() = user_id)
WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can delete their own expense schedules"
ON user_expense_due_dates FOR DELETE
USING (auth.uid() = user_id);

-- Create RLS policies for daily_cashflow
CREATE POLICY "Users can view their own cashflow"
ON daily_cashflow FOR SELECT
USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own cashflow"
ON daily_cashflow FOR INSERT
WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own cashflow"
ON daily_cashflow FOR UPDATE
USING (auth.uid() = user_id)
WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can delete their own cashflow"
ON daily_cashflow FOR DELETE
USING (auth.uid() = user_id); 