-- First, drop any existing policies
DROP POLICY IF EXISTS "Everyone can view date types" ON date_types;
DROP POLICY IF EXISTS "Enable all operations for testing" ON date_types;

-- Disable RLS for date_types since it's a reference table
ALTER TABLE date_types DISABLE ROW LEVEL SECURITY;

-- Grant read-only access to authenticated users
GRANT SELECT ON date_types TO authenticated;

-- Revoke insert/update/delete from authenticated users
REVOKE INSERT, UPDATE, DELETE ON date_types FROM authenticated;

-- Only database owners/admins can modify the table
GRANT ALL ON date_types TO postgres; 