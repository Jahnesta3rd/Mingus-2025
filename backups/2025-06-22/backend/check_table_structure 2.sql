-- First query for income table
SELECT 
    column_name, 
    data_type, 
    is_nullable
FROM 
    information_schema.columns
WHERE 
    table_schema = 'public'
    AND table_name = 'user_income_due_dates'
ORDER BY 
    ordinal_position;

-- Second query for expense table
SELECT 
    column_name, 
    data_type, 
    is_nullable
FROM 
    information_schema.columns
WHERE 
    table_schema = 'public'
    AND table_name = 'user_expense_due_dates'
ORDER BY 
    ordinal_position; 