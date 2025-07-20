-- Begin transaction
BEGIN;

-- Rename 'date' column to 'forecast_date'
ALTER TABLE daily_cashflow 
    RENAME COLUMN "date" TO forecast_date;

-- Rename 'status_color' column to 'balance_status'
ALTER TABLE daily_cashflow 
    RENAME COLUMN status_color TO balance_status;

-- Commit the changes
COMMIT;

-- If something goes wrong, changes will be automatically rolled back
-- To manually rollback, you can use:
-- ROLLBACK;

-- Verify the changes (run this after the transaction completes)
SELECT 
    column_name, 
    data_type 
FROM 
    information_schema.columns 
WHERE 
    table_name = 'daily_cashflow' 
ORDER BY 
    ordinal_position; 