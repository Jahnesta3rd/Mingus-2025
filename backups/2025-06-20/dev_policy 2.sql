-- Drop existing policies
DROP POLICY IF EXISTS "Users can view their own income schedules" ON user_income_due_dates;
DROP POLICY IF EXISTS "Users can insert their own income schedules" ON user_income_due_dates;
DROP POLICY IF EXISTS "Users can update their own income schedules" ON user_income_due_dates;
DROP POLICY IF EXISTS "Users can delete their own income schedules" ON user_income_due_dates;

DROP POLICY IF EXISTS "Users can view their own expense schedules" ON user_expense_due_dates;
DROP POLICY IF EXISTS "Users can insert their own expense schedules" ON user_expense_due_dates;
DROP POLICY IF EXISTS "Users can update their own expense schedules" ON user_expense_due_dates;
DROP POLICY IF EXISTS "Users can delete their own expense schedules" ON user_expense_due_dates;

DROP POLICY IF EXISTS "Users can view their own cashflow" ON daily_cashflow;
DROP POLICY IF EXISTS "Users can insert their own cashflow" ON daily_cashflow;
DROP POLICY IF EXISTS "Users can update their own cashflow" ON daily_cashflow;
DROP POLICY IF EXISTS "Users can delete their own cashflow" ON daily_cashflow;

-- Create permissive policies for development
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