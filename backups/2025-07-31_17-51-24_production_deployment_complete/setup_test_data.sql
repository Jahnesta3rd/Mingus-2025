-- Insert a test user if it doesn't exist
INSERT INTO auth.users (id, email)
VALUES 
    ('6f2a5f8a-df01-47b6-9827-50217ebc65c5', 'test@example.com')
ON CONFLICT (id) DO NOTHING;

-- Insert some test income records
INSERT INTO user_income_due_dates 
    (id, user_id, description, payment_amount, frequency, start_date)
VALUES
    (gen_random_uuid(), '6f2a5f8a-df01-47b6-9827-50217ebc65c5', 'salary', 5000.00, 'bi-weekly', CURRENT_DATE),
    (gen_random_uuid(), '6f2a5f8a-df01-47b6-9827-50217ebc65c5', 'rental', 2000.00, 'monthly', CURRENT_DATE)
ON CONFLICT DO NOTHING;

-- Insert some test expense records
INSERT INTO user_expense_due_dates
    (id, user_id, expense_type, due_date)
VALUES
    (gen_random_uuid(), '6f2a5f8a-df01-47b6-9827-50217ebc65c5', 'rent', 1),
    (gen_random_uuid(), '6f2a5f8a-df01-47b6-9827-50217ebc65c5', 'utilities', 15),
    (gen_random_uuid(), '6f2a5f8a-df01-47b6-9827-50217ebc65c5', 'car_payment', 5)
ON CONFLICT DO NOTHING; 