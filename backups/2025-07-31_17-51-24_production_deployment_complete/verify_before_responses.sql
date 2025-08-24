-- Check if user_onboarding table exists
SELECT EXISTS (
    SELECT FROM information_schema.tables 
    WHERE table_schema = 'public' 
    AND table_name = 'user_onboarding'
) as user_onboarding_exists;

-- If it exists, check its structure
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_schema = 'public'
AND table_name = 'user_onboarding'
ORDER BY ordinal_position; 