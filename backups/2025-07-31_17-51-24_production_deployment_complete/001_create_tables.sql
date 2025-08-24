-- Create the important_dates table
CREATE TABLE IF NOT EXISTS important_dates (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID NOT NULL,
    date_type_id UUID NOT NULL,
    event_date DATE NOT NULL,
    amount DECIMAL(10,2),
    description TEXT,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),
    CONSTRAINT future_date CHECK (event_date > CURRENT_DATE)
); 