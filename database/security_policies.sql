-- =====================================================
-- SUPABASE ROW LEVEL SECURITY POLICIES
-- Financial Profile Security Implementation
-- =====================================================

-- Enable RLS on all financial tables
ALTER TABLE user_income_due_dates ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_expense_due_dates ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_onboarding_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_income_sources ENABLE ROW LEVEL SECURITY;
ALTER TABLE anonymous_onboarding_responses ENABLE ROW LEVEL SECURITY;

-- =====================================================
-- USER INCOME DUE DATES POLICIES
-- =====================================================

-- Policy: Users can only view their own income records
CREATE POLICY "Users can view own income records" ON user_income_due_dates
    FOR SELECT USING (auth.uid() = user_id);

-- Policy: Users can only insert their own income records
CREATE POLICY "Users can insert own income records" ON user_income_due_dates
    FOR INSERT WITH CHECK (auth.uid() = user_id);

-- Policy: Users can only update their own income records
CREATE POLICY "Users can update own income records" ON user_income_due_dates
    FOR UPDATE USING (auth.uid() = user_id);

-- Policy: Users can only delete their own income records
CREATE POLICY "Users can delete own income records" ON user_income_due_dates
    FOR DELETE USING (auth.uid() = user_id);

-- =====================================================
-- USER EXPENSE DUE DATES POLICIES
-- =====================================================

-- Policy: Users can only view their own expense records
CREATE POLICY "Users can view own expense records" ON user_expense_due_dates
    FOR SELECT USING (auth.uid() = user_id);

-- Policy: Users can only insert their own expense records
CREATE POLICY "Users can insert own expense records" ON user_expense_due_dates
    FOR INSERT WITH CHECK (auth.uid() = user_id);

-- Policy: Users can only update their own expense records
CREATE POLICY "Users can update own expense records" ON user_expense_due_dates
    FOR UPDATE USING (auth.uid() = user_id);

-- Policy: Users can only delete their own expense records
CREATE POLICY "Users can delete own expense records" ON user_expense_due_dates
    FOR DELETE USING (auth.uid() = user_id);

-- =====================================================
-- USER ONBOARDING PROFILES POLICIES
-- =====================================================

-- Policy: Users can only view their own onboarding profile
CREATE POLICY "Users can view own onboarding profile" ON user_onboarding_profiles
    FOR SELECT USING (auth.uid() = user_id);

-- Policy: Users can only insert their own onboarding profile
CREATE POLICY "Users can insert own onboarding profile" ON user_onboarding_profiles
    FOR INSERT WITH CHECK (auth.uid() = user_id);

-- Policy: Users can only update their own onboarding profile
CREATE POLICY "Users can update own onboarding profile" ON user_onboarding_profiles
    FOR UPDATE USING (auth.uid() = user_id);

-- Policy: Users can only delete their own onboarding profile
CREATE POLICY "Users can delete own onboarding profile" ON user_onboarding_profiles
    FOR DELETE USING (auth.uid() = user_id);

-- =====================================================
-- USER INCOME SOURCES POLICIES
-- =====================================================

-- Policy: Users can only view their own income sources
CREATE POLICY "Users can view own income sources" ON user_income_sources
    FOR SELECT USING (auth.uid() = user_id);

-- Policy: Users can only insert their own income sources
CREATE POLICY "Users can insert own income sources" ON user_income_sources
    FOR INSERT WITH CHECK (auth.uid() = user_id);

-- Policy: Users can only update their own income sources
CREATE POLICY "Users can update own income sources" ON user_income_sources
    FOR UPDATE USING (auth.uid() = user_id);

-- Policy: Users can only delete their own income sources
CREATE POLICY "Users can delete own income sources" ON user_income_sources
    FOR DELETE USING (auth.uid() = user_id);

-- =====================================================
-- ANONYMOUS ONBOARDING RESPONSES POLICIES
-- =====================================================

-- Policy: Anonymous users can only view their own responses (by session_id)
CREATE POLICY "Anonymous users can view own responses" ON anonymous_onboarding_responses
    FOR SELECT USING (
        session_id = current_setting('app.session_id', true)::uuid
        OR user_id = auth.uid()
    );

-- Policy: Anonymous users can insert responses
CREATE POLICY "Anonymous users can insert responses" ON anonymous_onboarding_responses
    FOR INSERT WITH CHECK (
        session_id IS NOT NULL
        OR user_id = auth.uid()
    );

-- Policy: Users can update their own responses
CREATE POLICY "Users can update own responses" ON anonymous_onboarding_responses
    FOR UPDATE USING (user_id = auth.uid());

-- Policy: Users can delete their own responses
CREATE POLICY "Users can delete own responses" ON anonymous_onboarding_responses
    FOR DELETE USING (user_id = auth.uid());

-- =====================================================
-- AUDIT LOGGING FUNCTION
-- =====================================================

-- Create audit log table for financial data access
CREATE TABLE IF NOT EXISTS financial_audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id),
    table_name TEXT NOT NULL,
    operation TEXT NOT NULL, -- SELECT, INSERT, UPDATE, DELETE
    record_id UUID,
    ip_address INET,
    user_agent TEXT,
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    session_id UUID
);

-- Enable RLS on audit log
ALTER TABLE financial_audit_log ENABLE ROW LEVEL SECURITY;

-- Policy: Only authenticated users can view their own audit logs
CREATE POLICY "Users can view own audit logs" ON financial_audit_log
    FOR SELECT USING (auth.uid() = user_id);

-- Function to log financial data access
CREATE OR REPLACE FUNCTION log_financial_access(
    p_table_name TEXT,
    p_operation TEXT,
    p_record_id UUID DEFAULT NULL
)
RETURNS VOID AS $$
BEGIN
    INSERT INTO financial_audit_log (
        user_id,
        table_name,
        operation,
        record_id,
        ip_address,
        user_agent,
        session_id
    ) VALUES (
        auth.uid(),
        p_table_name,
        p_operation,
        p_record_id,
        inet_client_addr(),
        current_setting('request.headers', true)::json->>'user-agent',
        current_setting('app.session_id', true)::uuid
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- =====================================================
-- TRIGGERS FOR AUTOMATIC AUDIT LOGGING
-- =====================================================

-- Trigger function for user_income_due_dates
CREATE OR REPLACE FUNCTION audit_income_due_dates()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        PERFORM log_financial_access('user_income_due_dates', 'INSERT', NEW.id);
        RETURN NEW;
    ELSIF TG_OP = 'UPDATE' THEN
        PERFORM log_financial_access('user_income_due_dates', 'UPDATE', NEW.id);
        RETURN NEW;
    ELSIF TG_OP = 'DELETE' THEN
        PERFORM log_financial_access('user_income_due_dates', 'DELETE', OLD.id);
        RETURN OLD;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Create triggers
CREATE TRIGGER audit_income_due_dates_trigger
    AFTER INSERT OR UPDATE OR DELETE ON user_income_due_dates
    FOR EACH ROW EXECUTE FUNCTION audit_income_due_dates();

-- Trigger function for user_expense_due_dates
CREATE OR REPLACE FUNCTION audit_expense_due_dates()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        PERFORM log_financial_access('user_expense_due_dates', 'INSERT', NEW.id);
        RETURN NEW;
    ELSIF TG_OP = 'UPDATE' THEN
        PERFORM log_financial_access('user_expense_due_dates', 'UPDATE', NEW.id);
        RETURN NEW;
    ELSIF TG_OP = 'DELETE' THEN
        PERFORM log_financial_access('user_expense_due_dates', 'DELETE', OLD.id);
        RETURN OLD;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Create triggers
CREATE TRIGGER audit_expense_due_dates_trigger
    AFTER INSERT OR UPDATE OR DELETE ON user_expense_due_dates
    FOR EACH ROW EXECUTE FUNCTION audit_expense_due_dates();

-- Trigger function for user_onboarding_profiles
CREATE OR REPLACE FUNCTION audit_onboarding_profiles()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        PERFORM log_financial_access('user_onboarding_profiles', 'INSERT', NEW.id);
        RETURN NEW;
    ELSIF TG_OP = 'UPDATE' THEN
        PERFORM log_financial_access('user_onboarding_profiles', 'UPDATE', NEW.id);
        RETURN NEW;
    ELSIF TG_OP = 'DELETE' THEN
        PERFORM log_financial_access('user_onboarding_profiles', 'DELETE', OLD.id);
        RETURN OLD;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Create triggers
CREATE TRIGGER audit_onboarding_profiles_trigger
    AFTER INSERT OR UPDATE OR DELETE ON user_onboarding_profiles
    FOR EACH ROW EXECUTE FUNCTION audit_onboarding_profiles();

-- =====================================================
-- DATA VALIDATION CONSTRAINTS
-- =====================================================

-- Add validation constraints to user_income_due_dates
ALTER TABLE user_income_due_dates 
ADD CONSTRAINT valid_income_amount 
CHECK (amount > 0 AND amount <= 1000000); -- Max $1M per income source

ALTER TABLE user_income_due_dates 
ADD CONSTRAINT valid_income_frequency 
CHECK (frequency IN ('weekly', 'bi-weekly', 'monthly', 'quarterly', 'annually'));

-- Add validation constraints to user_expense_due_dates
ALTER TABLE user_expense_due_dates 
ADD CONSTRAINT valid_expense_amount 
CHECK (amount > 0 AND amount <= 100000); -- Max $100K per expense

ALTER TABLE user_expense_due_dates 
ADD CONSTRAINT valid_expense_frequency 
CHECK (frequency IN ('weekly', 'bi-weekly', 'monthly', 'quarterly', 'annually'));

-- Add validation constraints to user_onboarding_profiles
ALTER TABLE user_onboarding_profiles 
ADD CONSTRAINT valid_monthly_income 
CHECK (monthly_income >= 0 AND monthly_income <= 1000000); -- Max $1M monthly

ALTER TABLE user_onboarding_profiles 
ADD CONSTRAINT valid_monthly_expenses 
CHECK (monthly_expenses >= 0 AND monthly_expenses <= 500000); -- Max $500K monthly

ALTER TABLE user_onboarding_profiles 
ADD CONSTRAINT valid_savings_goal 
CHECK (savings_goal >= 0 AND savings_goal <= 10000000); -- Max $10M savings goal

-- =====================================================
-- INDEXES FOR PERFORMANCE AND SECURITY
-- =====================================================

-- Create indexes for better query performance with RLS
CREATE INDEX IF NOT EXISTS idx_income_due_dates_user_id ON user_income_due_dates(user_id);
CREATE INDEX IF NOT EXISTS idx_expense_due_dates_user_id ON user_expense_due_dates(user_id);
CREATE INDEX IF NOT EXISTS idx_onboarding_profiles_user_id ON user_onboarding_profiles(user_id);
CREATE INDEX IF NOT EXISTS idx_income_sources_user_id ON user_income_sources(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_log_user_id ON financial_audit_log(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_log_timestamp ON financial_audit_log(timestamp);

-- =====================================================
-- SECURITY VIEWS FOR REPORTING
-- =====================================================

-- Create a secure view for financial summaries (only accessible by the user)
CREATE OR REPLACE VIEW user_financial_summary AS
SELECT 
    u.id as user_id,
    u.email,
    COALESCE(SUM(uid.amount), 0) as total_monthly_income,
    COALESCE(SUM(ued.amount), 0) as total_monthly_expenses,
    uop.current_savings,
    uop.current_debt,
    uop.savings_goal
FROM auth.users u
LEFT JOIN user_income_due_dates uid ON u.id = uid.user_id
LEFT JOIN user_expense_due_dates ued ON u.id = ued.user_id
LEFT JOIN user_onboarding_profiles uop ON u.id = uop.user_id
GROUP BY u.id, u.email, uop.current_savings, uop.current_debt, uop.savings_goal;

-- Enable RLS on the view
ALTER VIEW user_financial_summary SET (security_invoker = true);

-- Grant access to authenticated users
GRANT SELECT ON user_financial_summary TO authenticated; 