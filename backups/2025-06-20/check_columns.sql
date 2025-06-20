-- Check columns for user_income_due_dates
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'user_income_due_dates'
ORDER BY ordinal_position;

-- Check columns for user_expense_due_dates
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'user_expense_due_dates'
ORDER BY ordinal_position;

-- Check columns for daily_cashflow
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'daily_cashflow'
ORDER BY ordinal_position; 