-- =====================================================
-- ENCRYPTED FINANCIAL TABLES CREATION
-- Comprehensive setup for secure financial data storage
-- =====================================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- =====================================================
-- ENCRYPTED FINANCIAL PROFILES TABLE
-- =====================================================

CREATE TABLE IF NOT EXISTS encrypted_financial_profiles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    
    -- Encrypted sensitive fields
    monthly_income TEXT, -- Encrypted with field-level encryption
    current_savings TEXT, -- Encrypted
    current_debt TEXT, -- Encrypted
    emergency_fund TEXT, -- Encrypted
    savings_goal TEXT, -- Encrypted
    debt_payoff_goal TEXT, -- Encrypted
    investment_goal TEXT, -- Encrypted
    
    -- Non-sensitive fields
    income_frequency VARCHAR(50),
    primary_income_source VARCHAR(100),
    secondary_income_source VARCHAR(100),
    risk_tolerance VARCHAR(50),
    investment_experience VARCHAR(50),
    budgeting_experience VARCHAR(50),
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_complete BOOLEAN DEFAULT FALSE,
    
    -- Constraints
    CONSTRAINT valid_income_frequency CHECK (
        income_frequency IN ('weekly', 'bi-weekly', 'semi-monthly', 'monthly', 'quarterly', 'annually')
    ),
    CONSTRAINT valid_risk_tolerance CHECK (
        risk_tolerance IN ('conservative', 'moderate', 'aggressive')
    )
);

-- =====================================================
-- ENCRYPTED INCOME SOURCES TABLE
-- =====================================================

CREATE TABLE IF NOT EXISTS encrypted_income_sources (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    
    -- Encrypted sensitive fields
    amount TEXT NOT NULL, -- Encrypted
    
    -- Non-sensitive fields
    source_name VARCHAR(100) NOT NULL,
    frequency VARCHAR(50) NOT NULL,
    start_date TIMESTAMP,
    end_date TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT valid_frequency CHECK (
        frequency IN ('weekly', 'bi-weekly', 'semi-monthly', 'monthly', 'quarterly', 'annually')
    )
);

-- =====================================================
-- ENCRYPTED DEBT ACCOUNTS TABLE
-- =====================================================

CREATE TABLE IF NOT EXISTS encrypted_debt_accounts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    
    -- Encrypted sensitive fields
    balance TEXT NOT NULL, -- Encrypted
    minimum_payment TEXT, -- Encrypted
    
    -- Non-sensitive fields
    account_name VARCHAR(100) NOT NULL,
    interest_rate DECIMAL(5,4),
    account_type VARCHAR(50) NOT NULL,
    due_date INTEGER,
    is_active BOOLEAN DEFAULT TRUE,
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT valid_account_type CHECK (
        account_type IN ('credit_card', 'student_loan', 'mortgage', 'car_loan', 'personal_loan', 'other')
    ),
    CONSTRAINT valid_due_date CHECK (due_date BETWEEN 1 AND 31)
);

-- =====================================================
-- FINANCIAL AUDIT LOGS TABLE
-- =====================================================

CREATE TABLE IF NOT EXISTS financial_audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    table_name VARCHAR(100) NOT NULL,
    record_id UUID NOT NULL,
    action_type VARCHAR(50) NOT NULL,
    field_name VARCHAR(100),
    old_value TEXT,
    new_value TEXT,
    ip_address INET,
    user_agent TEXT,
    request_id UUID,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT valid_action_type CHECK (
        action_type IN ('CREATE', 'READ', 'UPDATE', 'DELETE', 'FIELD_UPDATE')
    )
);

-- =====================================================
-- ENCRYPTED CHILD SUPPORT TABLE
-- =====================================================

CREATE TABLE IF NOT EXISTS encrypted_child_support (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    
    -- Encrypted sensitive fields
    amount TEXT, -- Encrypted
    
    -- Non-sensitive fields
    frequency VARCHAR(50),
    next_pay_date DATE,
    is_active BOOLEAN DEFAULT TRUE,
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT valid_frequency CHECK (
        frequency IN ('weekly', 'bi-weekly', 'semi-monthly', 'monthly')
    )
);

-- =====================================================
-- INDEXES FOR PERFORMANCE
-- =====================================================

-- User-based indexes for RLS performance
CREATE INDEX IF NOT EXISTS idx_encrypted_financial_profiles_user_id 
ON encrypted_financial_profiles(user_id);

CREATE INDEX IF NOT EXISTS idx_encrypted_income_sources_user_id 
ON encrypted_income_sources(user_id);

CREATE INDEX IF NOT EXISTS idx_encrypted_debt_accounts_user_id 
ON encrypted_debt_accounts(user_id);

CREATE INDEX IF NOT EXISTS idx_encrypted_child_support_user_id 
ON encrypted_child_support(user_id);

CREATE INDEX IF NOT EXISTS idx_financial_audit_logs_user_id 
ON financial_audit_logs(user_id);

-- Audit log indexes
CREATE INDEX IF NOT EXISTS idx_financial_audit_logs_timestamp 
ON financial_audit_logs(timestamp);

CREATE INDEX IF NOT EXISTS idx_financial_audit_logs_table_record 
ON financial_audit_logs(table_name, record_id);

-- =====================================================
-- TRIGGERS FOR UPDATED_AT TIMESTAMPS
-- =====================================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for all tables with updated_at
CREATE TRIGGER update_encrypted_financial_profiles_updated_at
    BEFORE UPDATE ON encrypted_financial_profiles
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_encrypted_income_sources_updated_at
    BEFORE UPDATE ON encrypted_income_sources
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_encrypted_debt_accounts_updated_at
    BEFORE UPDATE ON encrypted_debt_accounts
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_encrypted_child_support_updated_at
    BEFORE UPDATE ON encrypted_child_support
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- =====================================================
-- ROW LEVEL SECURITY (RLS) POLICIES
-- =====================================================

-- Enable RLS on all tables
ALTER TABLE encrypted_financial_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE encrypted_income_sources ENABLE ROW LEVEL SECURITY;
ALTER TABLE encrypted_debt_accounts ENABLE ROW LEVEL SECURITY;
ALTER TABLE encrypted_child_support ENABLE ROW LEVEL SECURITY;
ALTER TABLE financial_audit_logs ENABLE ROW LEVEL SECURITY;

-- =====================================================
-- ENCRYPTED FINANCIAL PROFILES POLICIES
-- =====================================================

-- Users can only view their own financial profiles
CREATE POLICY "Users can view own financial profiles" ON encrypted_financial_profiles
    FOR SELECT USING (auth.uid() = user_id);

-- Users can only insert their own financial profiles
CREATE POLICY "Users can insert own financial profiles" ON encrypted_financial_profiles
    FOR INSERT WITH CHECK (auth.uid() = user_id);

-- Users can only update their own financial profiles
CREATE POLICY "Users can update own financial profiles" ON encrypted_financial_profiles
    FOR UPDATE USING (auth.uid() = user_id);

-- Users can only delete their own financial profiles
CREATE POLICY "Users can delete own financial profiles" ON encrypted_financial_profiles
    FOR DELETE USING (auth.uid() = user_id);

-- =====================================================
-- ENCRYPTED INCOME SOURCES POLICIES
-- =====================================================

-- Users can only view their own income sources
CREATE POLICY "Users can view own income sources" ON encrypted_income_sources
    FOR SELECT USING (auth.uid() = user_id);

-- Users can only insert their own income sources
CREATE POLICY "Users can insert own income sources" ON encrypted_income_sources
    FOR INSERT WITH CHECK (auth.uid() = user_id);

-- Users can only update their own income sources
CREATE POLICY "Users can update own income sources" ON encrypted_income_sources
    FOR UPDATE USING (auth.uid() = user_id);

-- Users can only delete their own income sources
CREATE POLICY "Users can delete own income sources" ON encrypted_income_sources
    FOR DELETE USING (auth.uid() = user_id);

-- =====================================================
-- ENCRYPTED DEBT ACCOUNTS POLICIES
-- =====================================================

-- Users can only view their own debt accounts
CREATE POLICY "Users can view own debt accounts" ON encrypted_debt_accounts
    FOR SELECT USING (auth.uid() = user_id);

-- Users can only insert their own debt accounts
CREATE POLICY "Users can insert own debt accounts" ON encrypted_debt_accounts
    FOR INSERT WITH CHECK (auth.uid() = user_id);

-- Users can only update their own debt accounts
CREATE POLICY "Users can update own debt accounts" ON encrypted_debt_accounts
    FOR UPDATE USING (auth.uid() = user_id);

-- Users can only delete their own debt accounts
CREATE POLICY "Users can delete own debt accounts" ON encrypted_debt_accounts
    FOR DELETE USING (auth.uid() = user_id);

-- =====================================================
-- ENCRYPTED CHILD SUPPORT POLICIES
-- =====================================================

-- Users can only view their own child support records
CREATE POLICY "Users can view own child support" ON encrypted_child_support
    FOR SELECT USING (auth.uid() = user_id);

-- Users can only insert their own child support records
CREATE POLICY "Users can insert own child support" ON encrypted_child_support
    FOR INSERT WITH CHECK (auth.uid() = user_id);

-- Users can only update their own child support records
CREATE POLICY "Users can update own child support" ON encrypted_child_support
    FOR UPDATE USING (auth.uid() = user_id);

-- Users can only delete their own child support records
CREATE POLICY "Users can delete own child support" ON encrypted_child_support
    FOR DELETE USING (auth.uid() = user_id);

-- =====================================================
-- FINANCIAL AUDIT LOGS POLICIES
-- =====================================================

-- Users can only view their own audit logs
CREATE POLICY "Users can view own audit logs" ON financial_audit_logs
    FOR SELECT USING (auth.uid() = user_id);

-- System can insert audit logs for any user
CREATE POLICY "System can insert audit logs" ON financial_audit_logs
    FOR INSERT WITH CHECK (true);

-- =====================================================
-- COMMENTS FOR DOCUMENTATION
-- =====================================================

COMMENT ON TABLE encrypted_financial_profiles IS 'Stores encrypted financial profile data with field-level encryption for sensitive information';
COMMENT ON TABLE encrypted_income_sources IS 'Stores encrypted income source information with field-level encryption for amounts';
COMMENT ON TABLE encrypted_debt_accounts IS 'Stores encrypted debt account information with field-level encryption for balances and payments';
COMMENT ON TABLE encrypted_child_support IS 'Stores encrypted child support information with field-level encryption for amounts';
COMMENT ON TABLE financial_audit_logs IS 'Audit trail for all financial data access and modifications';

COMMENT ON COLUMN encrypted_financial_profiles.monthly_income IS 'Encrypted monthly income amount';
COMMENT ON COLUMN encrypted_financial_profiles.current_savings IS 'Encrypted current savings amount';
COMMENT ON COLUMN encrypted_financial_profiles.current_debt IS 'Encrypted current debt amount';
COMMENT ON COLUMN encrypted_income_sources.amount IS 'Encrypted income amount';
COMMENT ON COLUMN encrypted_debt_accounts.balance IS 'Encrypted debt balance';
COMMENT ON COLUMN encrypted_debt_accounts.minimum_payment IS 'Encrypted minimum payment amount';
COMMENT ON COLUMN encrypted_child_support.amount IS 'Encrypted child support amount';
