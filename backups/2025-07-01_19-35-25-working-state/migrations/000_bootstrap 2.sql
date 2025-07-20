-- Create initial bootstrap function
CREATE OR REPLACE FUNCTION exec_bootstrap(bootstrap_query text)
RETURNS void
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
    EXECUTE bootstrap_query;
END;
$$;

-- Grant execute permission
GRANT EXECUTE ON FUNCTION exec_bootstrap(text) TO authenticated;

-- Create DDL execution function using bootstrap
SELECT exec_bootstrap($DDL$
CREATE OR REPLACE FUNCTION exec_ddl(ddl_query text)
RETURNS text
LANGUAGE plpgsql
SECURITY DEFINER
AS $FUNC$
BEGIN
    EXECUTE ddl_query;
    RETURN 'OK';
EXCEPTION WHEN OTHERS THEN
    RAISE EXCEPTION 'Error executing DDL: % - %', SQLERRM, ddl_query;
END;
$FUNC$;
$DDL$);

-- Grant execute permission to DDL function
GRANT EXECUTE ON FUNCTION exec_ddl(text) TO authenticated; 