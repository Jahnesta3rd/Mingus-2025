-- Drop all existing policies
DROP POLICY IF EXISTS "No access for unauthenticated users" ON important_dates;
DROP POLICY IF EXISTS "Users can view their own important dates" ON important_dates;
DROP POLICY IF EXISTS "Users can insert their own important dates" ON important_dates;
DROP POLICY IF EXISTS "Users can update their own important dates" ON important_dates;
DROP POLICY IF EXISTS "Users can delete their own important dates" ON important_dates;
DROP POLICY IF EXISTS "Enable all operations for development" ON important_dates;
DROP POLICY IF EXISTS "default_deny_policy" ON important_dates;
DROP POLICY IF EXISTS "auth_select_policy" ON important_dates;
DROP POLICY IF EXISTS "auth_insert_policy" ON important_dates;
DROP POLICY IF EXISTS "auth_update_policy" ON important_dates;
DROP POLICY IF EXISTS "auth_delete_policy" ON important_dates;

-- Revoke all permissions
REVOKE ALL ON important_dates FROM public;
REVOKE ALL ON important_dates FROM anon;
REVOKE ALL ON important_dates FROM authenticated;

-- Grant only necessary permissions to authenticated users
GRANT SELECT, INSERT, UPDATE, DELETE ON important_dates TO authenticated;

-- Enable RLS
ALTER TABLE important_dates ENABLE ROW LEVEL SECURITY;

-- Create restrictive default policy
CREATE POLICY default_deny_policy ON important_dates
    FOR ALL
    TO public
    USING (false);

-- Create authenticated user policies
CREATE POLICY auth_select_policy ON important_dates
    FOR SELECT
    TO authenticated
    USING (auth.uid() = user_id);

CREATE POLICY auth_insert_policy ON important_dates
    FOR INSERT
    TO authenticated
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY auth_update_policy ON important_dates
    FOR UPDATE
    TO authenticated
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY auth_delete_policy ON important_dates
    FOR DELETE
    TO authenticated
    USING (auth.uid() = user_id); 