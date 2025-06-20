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

-- Grant execute permission
GRANT EXECUTE ON FUNCTION exec_sql(text) TO authenticated; 