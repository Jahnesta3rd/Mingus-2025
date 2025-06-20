-- Test data insertion script for Important Dates feature
DO $BODY$
DECLARE
    test_user_id UUID := 'f52e20d1-8ce3-4804-92e5-1e8fd149093f'::uuid;
    date_type_id UUID;
    important_date_id UUID;
BEGIN
    -- Clear existing test data for this user
    DELETE FROM important_dates WHERE user_id = test_user_id;

    -- Insert date types first
    INSERT INTO date_types (type_code, type_name, max_occurrences, requires_names, description) 
    VALUES
        ('CHILD_BIRTHDAY', 'Child''s Birthday', 3, true, 'Birthday celebrations for children'),
        ('WEDDING_ANNIV', 'Wedding Anniversary', 1, true, 'Wedding anniversary celebration'),
        ('ENGAGEMENT_ANNIV', 'Engagement Anniversary', 1, true, 'Engagement anniversary celebration'),
        ('GROUP_TRIP', 'Group Trip', NULL, true, 'Planned group trips and vacations'),
        ('SPOUSE_BIRTHDAY', 'Spouse''s Birthday', 1, true, 'Birthday celebration for spouse'),
        ('PARENT_BIRTHDAY', 'Parent''s Birthday', 4, true, 'Birthday celebrations for parents'),
        ('TAX_REFUND', 'Tax Refund Date', NULL, false, 'Expected tax refund dates'),
        ('FRATERNITY_DUES', 'Fraternity/Sorority Assessment', NULL, false, 'Fraternity or sorority membership dues and assessments')
    ON CONFLICT (type_code) DO NOTHING;

    -- 1. Children's Birthdays
    SELECT id INTO date_type_id FROM date_types WHERE type_code = 'CHILD_BIRTHDAY';
    
    -- First child
    INSERT INTO important_dates 
        (user_id, date_type_id, event_date, amount, description, balance_impact)
    VALUES 
        (test_user_id, date_type_id, '2025-03-15', 300.00, 'First Child Birthday Party', 'expense')
    RETURNING id INTO important_date_id;
    
    INSERT INTO associated_people (important_date_id, full_name, relationship) 
    VALUES (important_date_id, 'John Jr Smith', 'Son');

    -- Second child
    INSERT INTO important_dates 
        (user_id, date_type_id, event_date, amount, description, balance_impact)
    VALUES 
        (test_user_id, date_type_id, '2025-07-22', 250.00, 'Second Child Birthday Party', 'expense')
    RETURNING id INTO important_date_id;
    
    INSERT INTO associated_people (important_date_id, full_name, relationship) 
    VALUES (important_date_id, 'Sarah Smith', 'Daughter');

    -- 2. Wedding Anniversary
    SELECT id INTO date_type_id FROM date_types WHERE type_code = 'WEDDING_ANNIV';
    
    INSERT INTO important_dates 
        (user_id, date_type_id, event_date, amount, description, balance_impact)
    VALUES 
        (test_user_id, date_type_id, '2025-06-15', 1000.00, '15th Wedding Anniversary', 'expense')
    RETURNING id INTO important_date_id;
    
    INSERT INTO associated_people (important_date_id, full_name, relationship) 
    VALUES (important_date_id, 'Mary Smith', 'Spouse');

    -- 3. Parent Birthdays
    SELECT id INTO date_type_id FROM date_types WHERE type_code = 'PARENT_BIRTHDAY';
    
    -- Mother
    INSERT INTO important_dates 
        (user_id, date_type_id, event_date, amount, description, balance_impact)
    VALUES 
        (test_user_id, date_type_id, '2025-04-10', 200.00, 'Mother''s Birthday', 'expense')
    RETURNING id INTO important_date_id;
    
    INSERT INTO associated_people (important_date_id, full_name, relationship) 
    VALUES (important_date_id, 'Helen Johnson', 'Mother');

    -- Father
    INSERT INTO important_dates 
        (user_id, date_type_id, event_date, amount, description, balance_impact)
    VALUES 
        (test_user_id, date_type_id, '2025-09-28', 200.00, 'Father''s Birthday', 'expense')
    RETURNING id INTO important_date_id;
    
    INSERT INTO associated_people (important_date_id, full_name, relationship) 
    VALUES (important_date_id, 'Robert Johnson', 'Father');

    -- 4. Group Trip
    SELECT id INTO date_type_id FROM date_types WHERE type_code = 'GROUP_TRIP';
    
    INSERT INTO important_dates 
        (user_id, date_type_id, event_date, amount, description, balance_impact)
    VALUES 
        (test_user_id, date_type_id, '2025-08-01', 2500.00, 'Annual Family Vacation', 'expense')
    RETURNING id INTO important_date_id;
    
    INSERT INTO associated_people (important_date_id, full_name, relationship) 
    VALUES 
        (important_date_id, 'Mary Smith', 'Spouse'),
        (important_date_id, 'John Jr Smith', 'Son'),
        (important_date_id, 'Sarah Smith', 'Daughter');

    -- 5. Tax Refund
    SELECT id INTO date_type_id FROM date_types WHERE type_code = 'TAX_REFUND';
    
    INSERT INTO important_dates 
        (user_id, date_type_id, event_date, amount, description, balance_impact)
    VALUES 
        (test_user_id, date_type_id, '2025-04-15', 3500.00, 'Expected Tax Refund 2024', 'income');

    -- 6. Fraternity Dues
    SELECT id INTO date_type_id FROM date_types WHERE type_code = 'FRATERNITY_DUES';
    
    INSERT INTO important_dates 
        (user_id, date_type_id, event_date, amount, description, balance_impact)
    VALUES 
        (test_user_id, date_type_id, '2025-01-15', 500.00, 'Annual Fraternity Membership Dues', 'expense');

    RAISE NOTICE 'Test data insertion completed successfully';
END;
$BODY$ LANGUAGE plpgsql;