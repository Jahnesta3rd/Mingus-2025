-- First, clean up any existing data that would violate constraints
DELETE FROM important_dates WHERE event_date < CURRENT_DATE;
UPDATE important_dates SET status = NULL WHERE status NOT IN ('pending', 'confirmed', 'cancelled');
UPDATE important_dates SET balance_impact = 'expense' WHERE balance_impact NOT IN ('income', 'expense');

-- Drop existing constraints if they exist
DO $$ 
BEGIN
    ALTER TABLE important_dates DROP CONSTRAINT IF EXISTS check_future_date;
    ALTER TABLE important_dates DROP CONSTRAINT IF EXISTS check_status;
    ALTER TABLE important_dates DROP CONSTRAINT IF EXISTS check_balance_impact;
EXCEPTION WHEN OTHERS THEN NULL;
END $$;

-- Drop existing trigger if it exists
DROP TRIGGER IF EXISTS enforce_future_date ON important_dates;
DROP FUNCTION IF EXISTS check_future_date();

-- Add check constraints to important_dates table
ALTER TABLE important_dates
    ADD CONSTRAINT check_future_date 
        CHECK (event_date >= CURRENT_DATE),
    ADD CONSTRAINT check_status 
        CHECK (status IS NULL OR status IN ('pending', 'confirmed', 'cancelled')),
    ADD CONSTRAINT check_balance_impact 
        CHECK (balance_impact IN ('income', 'expense'));

-- Add trigger to enforce future dates on insert/update
CREATE OR REPLACE FUNCTION check_future_date()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.event_date < CURRENT_DATE THEN
        RAISE EXCEPTION 'Event date must be in the future';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER enforce_future_date
    BEFORE INSERT OR UPDATE ON important_dates
    FOR EACH ROW
    EXECUTE FUNCTION check_future_date(); 