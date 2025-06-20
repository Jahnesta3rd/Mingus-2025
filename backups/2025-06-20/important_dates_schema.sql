-- Drop existing tables if they exist
DROP TABLE IF EXISTS associated_people CASCADE;
DROP TABLE IF EXISTS important_dates CASCADE;
DROP TABLE IF EXISTS date_types CASCADE;

-- Create date_types lookup table
CREATE TABLE date_types (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    type_code VARCHAR(50) NOT NULL UNIQUE,
    type_name VARCHAR(100) NOT NULL,
    max_occurrences INTEGER,
    requires_names BOOLEAN DEFAULT false,
    description TEXT,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- Create important_dates table
CREATE TABLE important_dates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    date_type_id UUID NOT NULL REFERENCES date_types(id),
    event_date DATE NOT NULL,
    amount DECIMAL(10,2),
    description TEXT,
    is_recurring BOOLEAN DEFAULT true,
    reminder_days INTEGER[] DEFAULT ARRAY[7, 3, 1], -- Days before to send reminder
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'completed', 'cancelled')),
    balance_impact VARCHAR(20) DEFAULT 'expense' CHECK (balance_impact IN ('expense', 'income', 'neutral')),
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),
    CONSTRAINT valid_reminder_days CHECK (array_length(reminder_days, 1) <= 5) -- Max 5 reminder days
);

-- Create associated_people table
CREATE TABLE associated_people (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    important_date_id UUID NOT NULL REFERENCES important_dates(id) ON DELETE CASCADE,
    full_name VARCHAR(100) NOT NULL,
    relationship VARCHAR(50),
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- Create indexes
CREATE INDEX idx_important_dates_user ON important_dates(user_id);
CREATE INDEX idx_important_dates_type ON important_dates(date_type_id);
CREATE INDEX idx_important_dates_date ON important_dates(event_date);
CREATE INDEX idx_associated_people_date ON associated_people(important_date_id);
CREATE INDEX idx_date_types_code ON date_types(type_code);

-- Create trigger function for updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers
CREATE TRIGGER update_important_dates_updated_at
    BEFORE UPDATE ON important_dates
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_associated_people_updated_at
    BEFORE UPDATE ON associated_people
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_date_types_updated_at
    BEFORE UPDATE ON date_types
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Enable Row Level Security
ALTER TABLE important_dates ENABLE ROW LEVEL SECURITY;
ALTER TABLE associated_people ENABLE ROW LEVEL SECURITY;
ALTER TABLE date_types ENABLE ROW LEVEL SECURITY;

-- Create RLS Policies
CREATE POLICY "Users can view their own important dates"
    ON important_dates FOR SELECT
    TO authenticated
    USING (auth.uid() = user_id);

CREATE POLICY "Users can manage their own important dates"
    ON important_dates FOR ALL
    TO authenticated
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can view associated people for their dates"
    ON associated_people FOR SELECT
    TO authenticated
    USING (EXISTS (
        SELECT 1 FROM important_dates 
        WHERE important_dates.id = associated_people.important_date_id 
        AND important_dates.user_id = auth.uid()
    ));

CREATE POLICY "Users can manage associated people for their dates"
    ON associated_people FOR ALL
    TO authenticated
    USING (EXISTS (
        SELECT 1 FROM important_dates 
        WHERE important_dates.id = associated_people.important_date_id 
        AND important_dates.user_id = auth.uid()
    ))
    WITH CHECK (EXISTS (
        SELECT 1 FROM important_dates 
        WHERE important_dates.id = associated_people.important_date_id 
        AND important_dates.user_id = auth.uid()
    ));

CREATE POLICY "Everyone can view date types"
    ON date_types FOR SELECT
    TO authenticated
    USING (true);

-- Insert sample date types
INSERT INTO date_types (type_code, type_name, max_occurrences, requires_names, description) VALUES
    ('CHILD_BIRTHDAY', 'Child''s Birthday', 3, true, 'Birthday celebrations for children'),
    ('WEDDING_ANNIV', 'Wedding Anniversary', 1, true, 'Wedding anniversary celebration'),
    ('ENGAGEMENT_ANNIV', 'Engagement Anniversary', 1, true, 'Engagement anniversary celebration'),
    ('GROUP_TRIP', 'Group Trip', NULL, true, 'Planned group trips and vacations'),
    ('SPOUSE_BIRTHDAY', 'Spouse''s Birthday', 1, true, 'Birthday celebration for spouse'),
    ('PARENT_BIRTHDAY', 'Parent''s Birthday', 4, true, 'Birthday celebrations for parents'),
    ('TAX_REFUND', 'Tax Refund Date', NULL, false, 'Expected tax refund dates'),
    ('FRATERNITY_DUES', 'Fraternity/Sorority Assessment', NULL, false, 'Fraternity or sorority membership dues and assessments');

-- Insert sample data for a test user
DO $$
DECLARE
    test_user_id UUID;
    wedding_date_id UUID;
    child_bday_id UUID;
    tax_refund_id UUID;
    date_type_id UUID;
BEGIN
    -- Get a test user ID (replace with actual user ID in production)
    SELECT id INTO test_user_id FROM auth.users LIMIT 1;
    
    -- Get date type IDs
    SELECT id INTO wedding_date_id FROM date_types WHERE type_code = 'WEDDING_ANNIV';
    SELECT id INTO child_bday_id FROM date_types WHERE type_code = 'CHILD_BIRTHDAY';
    SELECT id INTO tax_refund_id FROM date_types WHERE type_code = 'TAX_REFUND';
    
    -- Insert wedding anniversary
    INSERT INTO important_dates (
        user_id, date_type_id, event_date, amount, description, balance_impact
    ) VALUES (
        test_user_id,
        wedding_date_id,
        '2025-06-15',
        1500.00,
        '10th Wedding Anniversary Celebration',
        'expense'
    ) RETURNING id INTO date_type_id;
    
    -- Insert associated people for wedding
    INSERT INTO associated_people (important_date_id, full_name, relationship) VALUES
    (date_type_id, 'Jane Smith', 'Spouse');
    
    -- Insert child's birthday
    INSERT INTO important_dates (
        user_id, date_type_id, event_date, amount, description, balance_impact
    ) VALUES (
        test_user_id,
        child_bday_id,
        '2025-08-20',
        500.00,
        'Birthday Party - Sweet 16',
        'expense'
    ) RETURNING id INTO date_type_id;
    
    -- Insert associated people for birthday
    INSERT INTO associated_people (important_date_id, full_name, relationship) VALUES
    (date_type_id, 'Emily Smith', 'Daughter');
    
    -- Insert tax refund
    INSERT INTO important_dates (
        user_id, date_type_id, event_date, amount, description, balance_impact
    ) VALUES (
        test_user_id,
        tax_refund_id,
        '2025-04-15',
        2500.00,
        'Expected Tax Refund 2024',
        'income'
    );
END $$; 