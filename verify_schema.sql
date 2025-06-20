-- List all tables in the public schema
SELECT tablename 
FROM pg_tables 
WHERE schemaname = 'public'; 