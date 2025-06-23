-- Enable RLS on the tables
ALTER TABLE daily_cashflow ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_income_due_dates ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_expense_due_dates ENABLE ROW LEVEL SECURITY;

-- Create policies for daily_cashflow
CREATE POLICY "Enable insert for authenticated users only"
ON daily_cashflow
FOR INSERT
TO authenticated
WITH CHECK (true);

CREATE POLICY "Enable read access for users to own cashflow"
ON daily_cashflow
FOR SELECT
USING (auth.uid() = user_id);

-- Create policies for income dates
CREATE POLICY "Enable insert for authenticated users only"
ON user_income_due_dates
FOR INSERT
TO authenticated
WITH CHECK (true);

CREATE POLICY "Enable read access for users to own income dates"
ON user_income_due_dates
FOR SELECT
USING (auth.uid() = user_id);

-- Create policies for expense dates
CREATE POLICY "Enable insert for authenticated users only"
ON user_expense_due_dates
FOR INSERT
TO authenticated
WITH CHECK (true);

CREATE POLICY "Enable read access for users to own expense dates"
ON user_expense_due_dates
FOR SELECT
USING (auth.uid() = user_id); 