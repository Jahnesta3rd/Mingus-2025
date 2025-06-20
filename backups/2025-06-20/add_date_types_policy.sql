-- Drop existing policies for date_types
DROP POLICY IF EXISTS "Everyone can view date types" ON date_types;
DROP POLICY IF EXISTS "Enable all operations for testing" ON date_types;

-- Create a permissive policy for testing that allows all operations
CREATE POLICY "Enable all operations for testing"
    ON date_types FOR ALL
    TO authenticated
    USING (true)
    WITH CHECK (true); 