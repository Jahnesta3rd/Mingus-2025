-- 1. Check if enums exist and their values
SELECT '1. ENUM TYPES:' as section;
SELECT t.typname as enum_type, 
       array_agg(e.enumlabel ORDER BY e.enumsortorder) as possible_values
FROM pg_type t
JOIN pg_enum e ON t.oid = e.enumtypid
WHERE t.typname IN ('response_type', 'response_value_type')
GROUP BY t.typname;

-- 2. Check table structure
SELECT '2. TABLE STRUCTURE:' as section;
SELECT column_name, 
       data_type, 
       udt_name,
       column_default,
       is_nullable
FROM information_schema.columns
WHERE table_schema = 'public' 
AND table_name = 'onboarding_responses'
ORDER BY ordinal_position;

-- 3. Check indexes
SELECT '3. INDEXES:' as section;
SELECT indexname,
       indexdef
FROM pg_indexes
WHERE schemaname = 'public'
AND tablename = 'onboarding_responses';

-- 4. Check RLS status
SELECT '4. RLS STATUS:' as section;
SELECT tablename,
       rowsecurity as rls_enabled
FROM pg_tables
WHERE schemaname = 'public'
AND tablename = 'onboarding_responses';

-- 5. Check RLS policies
SELECT '5. RLS POLICIES:' as section;
SELECT policyname,
       permissive,
       cmd,
       qual
FROM pg_policies
WHERE schemaname = 'public'
AND tablename = 'onboarding_responses';

-- 6. Check triggers
SELECT '6. TRIGGERS:' as section;
SELECT trigger_name,
       event_manipulation,
       event_object_table,
       action_statement
FROM information_schema.triggers
WHERE event_object_schema = 'public'
AND event_object_table = 'onboarding_responses';

-- 7. Check analytics view
SELECT '7. ANALYTICS VIEW:' as section;
SELECT schemaname,
       viewname,
       definition
FROM pg_views
WHERE schemaname = 'public'
AND viewname = 'onboarding_responses_analytics'; 