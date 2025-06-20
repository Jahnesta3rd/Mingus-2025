-- Drop existing function if it exists
DROP FUNCTION IF EXISTS exec_sql(text);

-- Create function to execute arbitrary SQL
CREATE OR REPLACE FUNCTION exec_sql(query text)
RETURNS SETOF json
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    result json;
BEGIN
    FOR result IN EXECUTE query
    LOOP
        RETURN NEXT result;
    END LOOP;
    RETURN;
END;
$$;

-- Create DDL execution function
CREATE OR REPLACE FUNCTION exec_ddl(ddl_query text)
RETURNS text
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
    EXECUTE ddl_query;
    RETURN 'OK';
EXCEPTION WHEN OTHERS THEN
    RAISE EXCEPTION 'Error executing DDL: % - %', SQLERRM, ddl_query;
END;
$$;

-- Grant execute permissions
GRANT EXECUTE ON FUNCTION exec_sql(text) TO authenticated;
GRANT EXECUTE ON FUNCTION exec_ddl(text) TO authenticated; 