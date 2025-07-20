-- Begin transaction
BEGIN;

-- Rename 'forecast_date' back to 'date'
ALTER TABLE daily_cashflow 
    RENAME COLUMN forecast_date TO "date";

-- Rename 'balance_status' back to 'status_color'
ALTER TABLE daily_cashflow 
    RENAME COLUMN balance_status TO status_color;

-- Commit the changes
COMMIT;

-- Verify the rollback
SELECT 
    column_name, 
    data_type 
FROM 
    information_schema.columns 
WHERE 
    table_name = 'daily_cashflow' 
ORDER BY 
    ordinal_position; 