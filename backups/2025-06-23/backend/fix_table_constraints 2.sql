-- First, drop the existing unique constraint on forecast_date
ALTER TABLE daily_cashflow
DROP CONSTRAINT IF EXISTS daily_cashflow_date_key;

-- Create a composite unique constraint on user_id and forecast_date
ALTER TABLE daily_cashflow
ADD CONSTRAINT daily_cashflow_user_date_key UNIQUE (user_id, forecast_date);

-- Make sure we have the correct indexes for performance
CREATE INDEX IF NOT EXISTS idx_daily_cashflow_user_date 
ON daily_cashflow(user_id, forecast_date);

-- Verify the table structure
SELECT 
    c.conname AS constraint_name,
    c.contype AS constraint_type,
    pg_get_constraintdef(c.oid) AS constraint_definition
FROM pg_constraint c
JOIN pg_namespace n ON n.oid = c.connamespace
WHERE n.nspname = 'public' 
AND c.conrelid = 'daily_cashflow'::regclass; 