-- Create migrations table directly
CREATE TABLE IF NOT EXISTS migrations (
    id SERIAL PRIMARY KEY,
    migration_name VARCHAR(255) NOT NULL UNIQUE,
    executed_at TIMESTAMPTZ DEFAULT NOW()
);

-- Disable RLS for migrations table since it's an admin table
ALTER TABLE migrations DISABLE ROW LEVEL SECURITY;

-- Grant permissions to service role
GRANT ALL ON migrations TO postgres;

-- Create sequence if it doesn't exist
CREATE SEQUENCE IF NOT EXISTS migrations_id_seq;

-- Grant usage on sequence
GRANT USAGE, SELECT ON SEQUENCE migrations_id_seq TO postgres;

-- Function to check if a migration has been run
CREATE OR REPLACE FUNCTION has_migration_run(migration_name text)
RETURNS boolean
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    migration_exists boolean;
BEGIN
    SELECT EXISTS(
        SELECT 1 FROM migrations WHERE migrations.migration_name = $1
    ) INTO migration_exists;
    RETURN migration_exists;
END;
$$;

-- Function to mark a migration as complete
CREATE OR REPLACE FUNCTION mark_migration_complete(migration_name text)
RETURNS void
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
    INSERT INTO migrations (migration_name)
    VALUES ($1);
END;
$$;

-- Function to run a migration
CREATE OR REPLACE PROCEDURE run_migration(
    migration_name text,
    migration_sql text
)
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
    -- Execute the migration SQL
    EXECUTE migration_sql;
    
    -- Record the migration
    INSERT INTO migrations (migration_name)
    VALUES (migration_name);
    
    COMMIT;
EXCEPTION WHEN OTHERS THEN
    ROLLBACK;
    RAISE EXCEPTION 'Error running migration %: %', migration_name, SQLERRM;
END;
$$;

-- Grant permissions
GRANT SELECT, INSERT ON migrations TO authenticated;
GRANT EXECUTE ON PROCEDURE run_migration(text, text) TO authenticated; 