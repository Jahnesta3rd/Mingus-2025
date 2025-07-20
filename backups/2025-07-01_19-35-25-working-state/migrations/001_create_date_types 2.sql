-- Drop existing trigger and function if they exist
DROP TRIGGER IF EXISTS update_date_types_updated_at ON date_types;
DROP FUNCTION IF EXISTS update_date_types_updated_at();

-- Create date_types table if it doesn't exist
CREATE TABLE IF NOT EXISTS date_types (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    type_code VARCHAR(50) NOT NULL UNIQUE,
    type_name VARCHAR(100) NOT NULL,
    max_occurrences INTEGER,
    requires_names BOOLEAN DEFAULT false,
    description TEXT,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- Create updated_at trigger
CREATE OR REPLACE FUNCTION update_date_types_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_date_types_updated_at
    BEFORE UPDATE ON date_types
    FOR EACH ROW
    EXECUTE FUNCTION update_date_types_updated_at();

-- Insert or update base date types
INSERT INTO date_types (
    type_code,
    type_name,
    max_occurrences,
    requires_names,
    description
) VALUES 
    ('CHILD_BIRTHDAY', 'Child''s Birthday', 3, true, 'Birthday celebrations for children'),
    ('WEDDING_ANNIV', 'Wedding Anniversary', 1, true, 'Wedding anniversary celebration'),
    ('ENGAGEMENT_ANNIV', 'Engagement Anniversary', 1, true, 'Engagement anniversary celebration'),
    ('GROUP_TRIP', 'Group Trip', NULL, true, 'Planned group trips and vacations'),
    ('SPOUSE_BIRTHDAY', 'Spouse''s Birthday', 1, true, 'Birthday celebration for spouse'),
    ('PARENT_BIRTHDAY', 'Parent''s Birthday', 4, true, 'Birthday celebrations for parents'),
    ('TAX_REFUND', 'Tax Refund Date', NULL, false, 'Expected tax refund dates'),
    ('FRATERNITY_DUES', 'Fraternity/Sorority Assessment', NULL, false, 'Fraternity or sorority membership dues and assessments')
ON CONFLICT (type_code) DO UPDATE SET
    type_name = EXCLUDED.type_name,
    max_occurrences = EXCLUDED.max_occurrences,
    requires_names = EXCLUDED.requires_names,
    description = EXCLUDED.description;

-- Set up permissions
GRANT SELECT ON date_types TO authenticated;
REVOKE INSERT, UPDATE, DELETE ON date_types FROM authenticated;
GRANT ALL ON date_types TO postgres;

-- Disable RLS for date_types since it's a reference table
ALTER TABLE date_types DISABLE ROW LEVEL SECURITY; 