-- Migration: Create Plaid Integration Tables
-- Description: Creates comprehensive database schema for Plaid integration
-- Date: 2025-01-27
-- Author: MINGUS Development Team

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create Plaid connections table
CREATE TABLE plaid_connections (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    item_id VARCHAR(255) NOT NULL UNIQUE,
    access_token TEXT NOT NULL, -- In production, this should be encrypted
    institution_id VARCHAR(255) NOT NULL,
    institution_name VARCHAR(255) NOT NULL,
    products JSONB NOT NULL DEFAULT '[]',
    webhook_url VARCHAR(500),
    error_code VARCHAR(100),
    error_message TEXT,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    last_sync_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Create Plaid accounts table
CREATE TABLE plaid_accounts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    connection_id UUID NOT NULL REFERENCES plaid_connections(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    plaid_account_id VARCHAR(255) NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL,
    mask VARCHAR(10),
    official_name VARCHAR(255),
    type VARCHAR(50) NOT NULL,
    subtype VARCHAR(50),
    current_balance DECIMAL(15,2),
    available_balance DECIMAL(15,2),
    iso_currency_code VARCHAR(3),
    unofficial_currency_code VARCHAR(10),
    limit DECIMAL(15,2),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    last_balance_update TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Create Plaid transactions table
CREATE TABLE plaid_transactions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    connection_id UUID NOT NULL REFERENCES plaid_connections(id) ON DELETE CASCADE,
    account_id UUID NOT NULL REFERENCES plaid_accounts(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    plaid_transaction_id VARCHAR(255) NOT NULL UNIQUE,
    pending_transaction_id VARCHAR(255),
    name VARCHAR(500) NOT NULL,
    amount DECIMAL(15,2) NOT NULL,
    date VARCHAR(10) NOT NULL, -- YYYY-MM-DD format
    datetime VARCHAR(30), -- ISO 8601 format
    authorized_date VARCHAR(10),
    authorized_datetime VARCHAR(30),
    merchant_name VARCHAR(255),
    logo_url VARCHAR(500),
    website VARCHAR(500),
    category JSONB NOT NULL DEFAULT '[]',
    category_id VARCHAR(50) NOT NULL,
    personal_finance_category JSONB,
    pending BOOLEAN NOT NULL DEFAULT FALSE,
    payment_channel VARCHAR(50) NOT NULL,
    transaction_type VARCHAR(50) NOT NULL,
    transaction_code VARCHAR(50),
    location JSONB,
    payment_meta JSONB,
    iso_currency_code VARCHAR(3),
    unofficial_currency_code VARCHAR(10),
    account_owner VARCHAR(255),
    check_number VARCHAR(50),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Create Plaid institutions table
CREATE TABLE plaid_institutions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    plaid_institution_id VARCHAR(255) NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL,
    logo VARCHAR(500),
    primary_color VARCHAR(7), -- Hex color code
    url VARCHAR(500),
    products JSONB NOT NULL DEFAULT '[]',
    routing_numbers JSONB,
    oauth BOOLEAN NOT NULL DEFAULT FALSE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Create Plaid sync logs table
CREATE TABLE plaid_sync_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    connection_id UUID NOT NULL REFERENCES plaid_connections(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    sync_type VARCHAR(50) NOT NULL, -- transactions, accounts, identity, etc.
    status VARCHAR(20) NOT NULL, -- in_progress, success, error
    started_at TIMESTAMP WITH TIME ZONE NOT NULL,
    completed_at TIMESTAMP WITH TIME ZONE,
    duration_seconds DECIMAL(10,3),
    items_processed INTEGER NOT NULL DEFAULT 0,
    items_added INTEGER NOT NULL DEFAULT 0,
    items_updated INTEGER NOT NULL DEFAULT 0,
    items_failed INTEGER NOT NULL DEFAULT 0,
    error_message TEXT,
    error_code VARCHAR(100),
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Create Plaid identities table
CREATE TABLE plaid_identities (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    connection_id UUID NOT NULL REFERENCES plaid_connections(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    names JSONB NOT NULL DEFAULT '[]', -- List of names
    phone_numbers JSONB NOT NULL DEFAULT '[]', -- List of phone numbers with metadata
    emails JSONB NOT NULL DEFAULT '[]', -- List of emails with metadata
    addresses JSONB NOT NULL DEFAULT '[]', -- List of addresses with metadata
    account_ids JSONB NOT NULL DEFAULT '[]', -- List of account IDs this identity is associated with
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Create indexes for better performance
CREATE INDEX idx_plaid_connections_user_active ON plaid_connections(user_id, is_active);
CREATE INDEX idx_plaid_connections_institution ON plaid_connections(institution_id);
CREATE INDEX idx_plaid_connections_last_sync ON plaid_connections(last_sync_at);

CREATE INDEX idx_plaid_accounts_connection_active ON plaid_accounts(connection_id, is_active);
CREATE INDEX idx_plaid_accounts_user_active ON plaid_accounts(user_id, is_active);
CREATE INDEX idx_plaid_accounts_type ON plaid_accounts(type);
CREATE INDEX idx_plaid_accounts_balance_update ON plaid_accounts(last_balance_update);

CREATE INDEX idx_plaid_transactions_connection ON plaid_transactions(connection_id);
CREATE INDEX idx_plaid_transactions_account ON plaid_transactions(account_id);
CREATE INDEX idx_plaid_transactions_user ON plaid_transactions(user_id);
CREATE INDEX idx_plaid_transactions_date ON plaid_transactions(date);
CREATE INDEX idx_plaid_transactions_amount ON plaid_transactions(amount);
CREATE INDEX idx_plaid_transactions_category ON plaid_transactions(category_id);
CREATE INDEX idx_plaid_transactions_pending ON plaid_transactions(pending);
CREATE INDEX idx_plaid_transactions_active ON plaid_transactions(is_active);

CREATE INDEX idx_plaid_institutions_active ON plaid_institutions(is_active);
CREATE INDEX idx_plaid_institutions_name ON plaid_institutions(name);

CREATE INDEX idx_plaid_sync_logs_connection ON plaid_sync_logs(connection_id);
CREATE INDEX idx_plaid_sync_logs_user ON plaid_sync_logs(user_id);
CREATE INDEX idx_plaid_sync_logs_status ON plaid_sync_logs(status);
CREATE INDEX idx_plaid_sync_logs_started ON plaid_sync_logs(started_at);
CREATE INDEX idx_plaid_sync_logs_type ON plaid_sync_logs(sync_type);

CREATE INDEX idx_plaid_identities_connection ON plaid_identities(connection_id);
CREATE INDEX idx_plaid_identities_user ON plaid_identities(user_id);
CREATE INDEX idx_plaid_identities_active ON plaid_identities(is_active);

-- Create updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for updated_at columns
CREATE TRIGGER update_plaid_connections_updated_at BEFORE UPDATE ON plaid_connections
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_plaid_accounts_updated_at BEFORE UPDATE ON plaid_accounts
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_plaid_transactions_updated_at BEFORE UPDATE ON plaid_transactions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_plaid_institutions_updated_at BEFORE UPDATE ON plaid_institutions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_plaid_identities_updated_at BEFORE UPDATE ON plaid_identities
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Create function to calculate sync duration
CREATE OR REPLACE FUNCTION calculate_sync_duration()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.completed_at IS NOT NULL AND NEW.started_at IS NOT NULL THEN
        NEW.duration_seconds = EXTRACT(EPOCH FROM (NEW.completed_at - NEW.started_at));
    END IF;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create trigger for sync duration calculation
CREATE TRIGGER calculate_plaid_sync_duration BEFORE UPDATE ON plaid_sync_logs
    FOR EACH ROW EXECUTE FUNCTION calculate_sync_duration();

-- Create function to update account balance
CREATE OR REPLACE FUNCTION update_account_balance()
RETURNS TRIGGER AS $$
BEGIN
    NEW.last_balance_update = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create trigger for account balance updates
CREATE TRIGGER update_plaid_account_balance BEFORE UPDATE ON plaid_accounts
    FOR EACH ROW EXECUTE FUNCTION update_account_balance();

-- Create function to validate transaction amount
CREATE OR REPLACE FUNCTION validate_transaction_amount()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.amount IS NOT NULL AND NEW.amount < 0 THEN
        -- Allow negative amounts for credit transactions
        RETURN NEW;
    END IF;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create trigger for transaction amount validation
CREATE TRIGGER validate_plaid_transaction_amount BEFORE INSERT OR UPDATE ON plaid_transactions
    FOR EACH ROW EXECUTE FUNCTION validate_transaction_amount();

-- Create function to log sync activities
CREATE OR REPLACE FUNCTION log_plaid_sync_activity()
RETURNS TRIGGER AS $$
BEGIN
    -- Log sync activity to audit table (if exists)
    -- This can be extended to log to external monitoring systems
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create trigger for sync activity logging
CREATE TRIGGER log_plaid_sync_activity_trigger AFTER INSERT OR UPDATE ON plaid_sync_logs
    FOR EACH ROW EXECUTE FUNCTION log_plaid_sync_activity();

-- Create views for common queries
CREATE VIEW plaid_connection_summary AS
SELECT 
    pc.id as connection_id,
    pc.user_id,
    pc.institution_name,
    pc.is_active,
    pc.last_sync_at,
    COUNT(pa.id) as account_count,
    COUNT(pt.id) as transaction_count,
    SUM(pa.current_balance) as total_balance
FROM plaid_connections pc
LEFT JOIN plaid_accounts pa ON pc.id = pa.connection_id AND pa.is_active = true
LEFT JOIN plaid_transactions pt ON pc.id = pt.connection_id AND pt.is_active = true
GROUP BY pc.id, pc.user_id, pc.institution_name, pc.is_active, pc.last_sync_at;

CREATE VIEW plaid_account_summary AS
SELECT 
    pa.id as account_id,
    pa.connection_id,
    pa.user_id,
    pa.name,
    pa.type,
    pa.subtype,
    pa.current_balance,
    pa.available_balance,
    pa.iso_currency_code,
    pa.last_balance_update,
    COUNT(pt.id) as transaction_count,
    SUM(CASE WHEN pt.pending = true THEN 1 ELSE 0 END) as pending_transactions
FROM plaid_accounts pa
LEFT JOIN plaid_transactions pt ON pa.id = pt.account_id AND pt.is_active = true
WHERE pa.is_active = true
GROUP BY pa.id, pa.connection_id, pa.user_id, pa.name, pa.type, pa.subtype, 
         pa.current_balance, pa.available_balance, pa.iso_currency_code, pa.last_balance_update;

-- Create indexes for views
CREATE INDEX idx_plaid_connection_summary_user ON plaid_connection_summary(user_id);
CREATE INDEX idx_plaid_account_summary_user ON plaid_account_summary(user_id);
CREATE INDEX idx_plaid_account_summary_connection ON plaid_account_summary(connection_id);

-- Grant permissions (adjust as needed for your setup)
-- GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO your_app_user;
-- GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO your_app_user;

-- Insert sample data for testing (optional)
-- INSERT INTO plaid_institutions (plaid_institution_id, name, products, is_active) VALUES
-- ('ins_109508', 'Chase', '["auth", "transactions", "identity"]', true),
-- ('ins_109509', 'Bank of America', '["auth", "transactions", "identity"]', true),
-- ('ins_109510', 'Wells Fargo', '["auth", "transactions", "identity"]', true);

COMMIT; 