-- Enable RLS but allow all operations for testing
ALTER TABLE daily_cashflow ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_income_due_dates ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_expense_due_dates ENABLE ROW LEVEL SECURITY;

-- Create permissive policies for development
CREATE POLICY "Enable all operations for development"
ON daily_cashflow
FOR ALL
USING (true)
WITH CHECK (true);

CREATE POLICY "Enable all operations for development"
ON user_income_due_dates
FOR ALL
USING (true)
WITH CHECK (true);

CREATE POLICY "Enable all operations for development"
ON user_expense_due_dates
FOR ALL
USING (true)
WITH CHECK (true); 