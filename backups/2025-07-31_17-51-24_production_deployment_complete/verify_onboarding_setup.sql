-- Check if enum types exist and their values
SELECT '1. ENUM TYPES:' as section;
SELECT t.typname as enum_type, 
       array_agg(e.enumlabel ORDER BY e.enumsortorder) as possible_values
FROM pg_type t
JOIN pg_enum e ON t.oid = e.enumtypid
WHERE t.typname IN ('financial_challenge_type', 'stress_handling_type', 'motivation_type')
GROUP BY t.typname
ORDER BY t.typname;

-- Check table structure
SELECT '2. TABLE STRUCTURE:' as section;
SELECT column_name, 
       data_type, 
       udt_name,
       column_default,
       is_nullable
FROM information_schema.columns
WHERE table_schema = 'public' 
AND table_name = 'user_onboarding'
ORDER BY ordinal_position;

-- Check RLS policies
SELECT '3. RLS POLICIES:' as section;
SELECT policyname, cmd, roles
FROM pg_policies
WHERE schemaname = 'public' 
AND tablename = 'user_onboarding';

-- 4. Check RLS
SELECT '4. RLS STATUS:' as section;
SELECT tablename, rowsecurity as rls_enabled
FROM pg_tables
WHERE schemaname = 'public' AND tablename = 'user_onboarding';

-- 5. Check Foreign Key
SELECT '5. FOREIGN KEY:' as section;
SELECT
    tc.constraint_name,
    kcu.column_name,
    ccu.table_schema AS foreign_table_schema,
    ccu.table_name AS foreign_table_name,
    ccu.column_name AS foreign_column_name
FROM information_schema.table_constraints AS tc
JOIN information_schema.key_column_usage AS kcu
    ON tc.constraint_name = kcu.constraint_name
    AND tc.table_schema = kcu.table_schema
JOIN information_schema.constraint_column_usage AS ccu
    ON ccu.constraint_name = tc.constraint_name
WHERE tc.constraint_type = 'FOREIGN KEY'
AND tc.table_schema = 'public'
AND tc.table_name = 'user_onboarding';

-- 6. Check Indexes
SELECT '6. INDEXES:' as section;
SELECT indexname,
       indexdef
FROM pg_indexes
WHERE schemaname = 'public'
AND tablename = 'user_onboarding';

-- 7. Check Triggers
SELECT '7. TRIGGERS:' as section;
SELECT trigger_name,
       event_manipulation,
       action_statement
FROM information_schema.triggers
WHERE trigger_schema = 'public'
AND event_object_table = 'user_onboarding'; 