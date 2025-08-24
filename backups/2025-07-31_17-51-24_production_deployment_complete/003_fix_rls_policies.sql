-- Drop all existing policies first
DROP POLICY IF EXISTS "Enable all operations for development" ON important_dates;
DROP POLICY IF EXISTS "Users can view their own important dates" ON important_dates;
DROP POLICY IF EXISTS "Users can manage their own important dates" ON important_dates;

-- Revoke all permissions and regrant only what's needed
REVOKE ALL ON important_dates FROM anon;
REVOKE ALL ON important_dates FROM authenticated;

-- Grant necessary permissions to authenticated users
GRANT SELECT, INSERT, UPDATE, DELETE ON important_dates TO authenticated;

-- Create proper RLS policies
CREATE POLICY "No access for unauthenticated users"
    ON important_dates FOR ALL
    TO anon
    USING (false)
    WITH CHECK (false);

CREATE POLICY "Users can view their own important dates"
    ON important_dates FOR SELECT
    TO authenticated
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own important dates"
    ON important_dates FOR INSERT
    TO authenticated
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own important dates"
    ON important_dates FOR UPDATE
    TO authenticated
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can delete their own important dates"
    ON important_dates FOR DELETE
    TO authenticated
    USING (auth.uid() = user_id); 