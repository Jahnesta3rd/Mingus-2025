-- Migration: Create Bank Account Models
-- Description: Creates comprehensive bank account data models for MINGUS
-- Date: 2025-01-27

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create enum types
CREATE TYPE account_type_enum AS ENUM (
    'checking', 'savings', 'credit', 'loan', 'investment', 'mortgage', 
    'business', 'money_market', 'certificate_of_deposit', 'prepaid', 'other'
);

CREATE TYPE account_status_enum AS ENUM (
    'active', 'pending_verification', 'verified', 'suspended', 'disconnected', 
    'maintenance', 'error', 'archived', 'closed'
);

CREATE TYPE sync_status_enum AS ENUM (
    'pending', 'in_progress', 'success', 'failed', 'partial', 'rate_limited', 'maintenance'
);

CREATE TYPE balance_type_enum AS ENUM (
    'current', 'available', 'pending', 'overdraft', 'credit_limit', 'payment_due', 'last_payment'
);

CREATE TYPE notification_frequency_enum AS ENUM (
    'immediate', 'hourly', 'daily', 'weekly', 'monthly', 'never'
);

-- Create bank_accounts table
CREATE TABLE bank_accounts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    plaid_connection_id UUID NOT NULL REFERENCES plaid_connections(id) ON DELETE CASCADE,
    
    -- Account identification
    account_id VARCHAR(255) NOT NULL,
    name VARCHAR(255) NOT NULL,
    mask VARCHAR(10),
    
    -- Account type and classification
    type VARCHAR(50) NOT NULL CHECK (type IN ('depository', 'credit', 'loan', 'investment', 'other')),
    subtype VARCHAR(50),
    account_type VARCHAR(50) NOT NULL,
    
    -- Account status
    status VARCHAR(50) NOT NULL DEFAULT 'active',
    verification_status VARCHAR(50) NOT NULL DEFAULT 'pending',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    
    -- Financial information
    current_balance NUMERIC(15, 2),
    available_balance NUMERIC(15, 2),
    credit_limit NUMERIC(15, 2),
    payment_due NUMERIC(15, 2),
    last_payment_amount NUMERIC(15, 2),
    last_payment_date TIMESTAMP WITH TIME ZONE,
    
    -- Currency and limits
    iso_currency_code VARCHAR(3) NOT NULL DEFAULT 'USD',
    unofficial_currency_code VARCHAR(10),
    
    -- Account details
    interest_rate FLOAT,
    apr FLOAT,
    minimum_balance NUMERIC(15, 2),
    monthly_fee NUMERIC(15, 2),
    
    -- Account metadata
    account_number VARCHAR(50),
    routing_number VARCHAR(20),
    account_holder_name VARCHAR(255),
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    last_sync_at TIMESTAMP WITH TIME ZONE,
    last_balance_update TIMESTAMP WITH TIME ZONE,
    
    -- Additional data
    metadata JSONB,
    tags JSONB,
    notes TEXT,
    
    -- Constraints
    CONSTRAINT uq_bank_account_connection UNIQUE (plaid_connection_id, account_id)
);

-- Create plaid_connections table (enhanced version)
CREATE TABLE plaid_connections (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Plaid identifiers
    access_token TEXT NOT NULL,
    item_id VARCHAR(255) NOT NULL UNIQUE,
    institution_id VARCHAR(255) NOT NULL,
    
    -- Connection information
    institution_name VARCHAR(255) NOT NULL,
    institution_logo VARCHAR(500),
    institution_primary_color VARCHAR(7),
    institution_url VARCHAR(500),
    
    -- Connection status
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    requires_reauth BOOLEAN NOT NULL DEFAULT FALSE,
    last_error VARCHAR(255),
    last_error_at TIMESTAMP WITH TIME ZONE,
    error_count INTEGER NOT NULL DEFAULT 0,
    
    -- Maintenance and sync
    maintenance_until TIMESTAMP WITH TIME ZONE,
    last_sync_at TIMESTAMP WITH TIME ZONE,
    next_sync_at TIMESTAMP WITH TIME ZONE,
    sync_frequency VARCHAR(50) NOT NULL DEFAULT 'daily',
    
    -- Connection metadata
    link_token VARCHAR(255),
    link_token_expires_at TIMESTAMP WITH TIME ZONE,
    reconnection_attempted_at TIMESTAMP WITH TIME ZONE,
    retry_count INTEGER NOT NULL DEFAULT 0,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    
    -- Additional data
    metadata JSONB,
    settings JSONB,
    
    -- Constraints
    CONSTRAINT chk_sync_frequency CHECK (sync_frequency IN ('real_time', 'hourly', 'daily', 'weekly', 'manual'))
);

-- Create transaction_syncs table
CREATE TABLE transaction_syncs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    bank_account_id UUID NOT NULL REFERENCES bank_accounts(id) ON DELETE CASCADE,
    plaid_connection_id UUID NOT NULL REFERENCES plaid_connections(id) ON DELETE CASCADE,
    
    -- Sync information
    sync_type VARCHAR(50) NOT NULL CHECK (sync_type IN ('initial', 'incremental', 'full', 'manual', 'scheduled')),
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    
    -- Timing information
    started_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    duration FLOAT,
    
    -- Sync results
    records_processed INTEGER NOT NULL DEFAULT 0,
    records_failed INTEGER NOT NULL DEFAULT 0,
    records_added INTEGER NOT NULL DEFAULT 0,
    records_updated INTEGER NOT NULL DEFAULT 0,
    records_deleted INTEGER NOT NULL DEFAULT 0,
    
    -- Error handling
    error_message TEXT,
    error_code VARCHAR(100),
    retry_count INTEGER NOT NULL DEFAULT 0,
    retry_after TIMESTAMP WITH TIME ZONE,
    
    -- Sync context
    context JSONB,
    metadata JSONB,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT chk_sync_status CHECK (status IN ('pending', 'in_progress', 'success', 'failed', 'partial', 'rate_limited', 'maintenance'))
);

-- Create account_balances table
CREATE TABLE account_balances (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    bank_account_id UUID NOT NULL REFERENCES bank_accounts(id) ON DELETE CASCADE,
    
    -- Balance information
    balance_type VARCHAR(50) NOT NULL,
    amount NUMERIC(15, 2) NOT NULL,
    currency VARCHAR(3) NOT NULL DEFAULT 'USD',
    
    -- Balance metadata
    as_of_date TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    is_current BOOLEAN NOT NULL DEFAULT TRUE,
    source VARCHAR(50) NOT NULL DEFAULT 'plaid',
    
    -- Historical tracking
    previous_amount NUMERIC(15, 2),
    change_amount NUMERIC(15, 2),
    change_percentage FLOAT,
    
    -- Additional data
    metadata JSONB,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT chk_balance_type CHECK (balance_type IN ('current', 'available', 'pending', 'overdraft', 'credit_limit', 'payment_due', 'last_payment')),
    CONSTRAINT chk_currency_length CHECK (char_length(currency) = 3)
);

-- Create banking_preferences table
CREATE TABLE banking_preferences (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    bank_account_id UUID REFERENCES bank_accounts(id) ON DELETE CASCADE,
    
    -- Sync preferences
    sync_frequency VARCHAR(50) NOT NULL DEFAULT 'daily',
    auto_sync BOOLEAN NOT NULL DEFAULT TRUE,
    sync_on_login BOOLEAN NOT NULL DEFAULT TRUE,
    
    -- Notification preferences
    balance_alerts BOOLEAN NOT NULL DEFAULT TRUE,
    balance_threshold NUMERIC(15, 2),
    low_balance_alert BOOLEAN NOT NULL DEFAULT TRUE,
    low_balance_threshold NUMERIC(15, 2),
    
    -- Transaction notifications
    transaction_notifications BOOLEAN NOT NULL DEFAULT TRUE,
    large_transaction_threshold NUMERIC(15, 2),
    unusual_activity_alerts BOOLEAN NOT NULL DEFAULT TRUE,
    
    -- Notification channels
    email_notifications BOOLEAN NOT NULL DEFAULT TRUE,
    push_notifications BOOLEAN NOT NULL DEFAULT TRUE,
    sms_notifications BOOLEAN NOT NULL DEFAULT FALSE,
    in_app_notifications BOOLEAN NOT NULL DEFAULT TRUE,
    
    -- Notification frequency
    notification_frequency VARCHAR(50) NOT NULL DEFAULT 'daily',
    
    -- Privacy and security
    share_analytics BOOLEAN NOT NULL DEFAULT TRUE,
    share_aggregated_data BOOLEAN NOT NULL DEFAULT TRUE,
    allow_marketing_emails BOOLEAN NOT NULL DEFAULT FALSE,
    
    -- Display preferences
    default_currency VARCHAR(3) NOT NULL DEFAULT 'USD',
    date_format VARCHAR(20) NOT NULL DEFAULT 'MM/DD/YYYY',
    time_format VARCHAR(10) NOT NULL DEFAULT '12h',
    show_balances BOOLEAN NOT NULL DEFAULT TRUE,
    show_transaction_details BOOLEAN NOT NULL DEFAULT TRUE,
    
    -- Account-specific settings
    account_alias VARCHAR(100),
    account_color VARCHAR(7),
    account_icon VARCHAR(50),
    hide_account BOOLEAN NOT NULL DEFAULT FALSE,
    
    -- Additional preferences
    metadata JSONB,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT uq_banking_preferences_user_account UNIQUE (user_id, bank_account_id),
    CONSTRAINT chk_preferences_sync_frequency CHECK (sync_frequency IN ('real_time', 'hourly', 'daily', 'weekly', 'manual')),
    CONSTRAINT chk_notification_frequency CHECK (notification_frequency IN ('immediate', 'hourly', 'daily', 'weekly', 'monthly', 'never')),
    CONSTRAINT chk_preferences_currency_length CHECK (char_length(default_currency) = 3)
);

-- Create indexes for bank_accounts table
CREATE INDEX idx_bank_accounts_user_id ON bank_accounts(user_id);
CREATE INDEX idx_bank_accounts_plaid_connection_id ON bank_accounts(plaid_connection_id);
CREATE INDEX idx_bank_accounts_account_id ON bank_accounts(account_id);
CREATE INDEX idx_bank_accounts_status ON bank_accounts(status);
CREATE INDEX idx_bank_accounts_type ON bank_accounts(type);
CREATE INDEX idx_bank_accounts_is_active ON bank_accounts(is_active);
CREATE INDEX idx_bank_accounts_last_sync_at ON bank_accounts(last_sync_at);
CREATE INDEX idx_bank_accounts_verification_status ON bank_accounts(verification_status);
CREATE INDEX idx_bank_accounts_iso_currency_code ON bank_accounts(iso_currency_code);

-- Create indexes for plaid_connections table
CREATE INDEX idx_plaid_connections_user_id ON plaid_connections(user_id);
CREATE INDEX idx_plaid_connections_item_id ON plaid_connections(item_id);
CREATE INDEX idx_plaid_connections_institution_id ON plaid_connections(institution_id);
CREATE INDEX idx_plaid_connections_is_active ON plaid_connections(is_active);
CREATE INDEX idx_plaid_connections_last_sync_at ON plaid_connections(last_sync_at);
CREATE INDEX idx_plaid_connections_requires_reauth ON plaid_connections(requires_reauth);
CREATE INDEX idx_plaid_connections_sync_frequency ON plaid_connections(sync_frequency);
CREATE INDEX idx_plaid_connections_error_count ON plaid_connections(error_count);

-- Create indexes for transaction_syncs table
CREATE INDEX idx_transaction_syncs_bank_account_id ON transaction_syncs(bank_account_id);
CREATE INDEX idx_transaction_syncs_plaid_connection_id ON transaction_syncs(plaid_connection_id);
CREATE INDEX idx_transaction_syncs_status ON transaction_syncs(status);
CREATE INDEX idx_transaction_syncs_started_at ON transaction_syncs(started_at);
CREATE INDEX idx_transaction_syncs_completed_at ON transaction_syncs(completed_at);
CREATE INDEX idx_transaction_syncs_sync_type ON transaction_syncs(sync_type);
CREATE INDEX idx_transaction_syncs_retry_count ON transaction_syncs(retry_count);

-- Create indexes for account_balances table
CREATE INDEX idx_account_balances_bank_account_id ON account_balances(bank_account_id);
CREATE INDEX idx_account_balances_balance_type ON account_balances(balance_type);
CREATE INDEX idx_account_balances_as_of_date ON account_balances(as_of_date);
CREATE INDEX idx_account_balances_is_current ON account_balances(is_current);
CREATE INDEX idx_account_balances_source ON account_balances(source);
CREATE INDEX idx_account_balances_currency ON account_balances(currency);

-- Create indexes for banking_preferences table
CREATE INDEX idx_banking_preferences_user_id ON banking_preferences(user_id);
CREATE INDEX idx_banking_preferences_bank_account_id ON banking_preferences(bank_account_id);
CREATE INDEX idx_banking_preferences_sync_frequency ON banking_preferences(sync_frequency);
CREATE INDEX idx_banking_preferences_notification_frequency ON banking_preferences(notification_frequency);
CREATE INDEX idx_banking_preferences_email_notifications ON banking_preferences(email_notifications);
CREATE INDEX idx_banking_preferences_push_notifications ON banking_preferences(push_notifications);

-- Create composite indexes for better query performance
CREATE INDEX idx_bank_accounts_user_status ON bank_accounts(user_id, status);
CREATE INDEX idx_bank_accounts_user_active ON bank_accounts(user_id, is_active);
CREATE INDEX idx_plaid_connections_user_active ON plaid_connections(user_id, is_active);
CREATE INDEX idx_transaction_syncs_account_status ON transaction_syncs(bank_account_id, status);
CREATE INDEX idx_account_balances_account_current ON account_balances(bank_account_id, is_current);
CREATE INDEX idx_banking_preferences_user_account ON banking_preferences(user_id, bank_account_id);

-- Create functions for automatic timestamp updates
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for updated_at columns
CREATE TRIGGER update_bank_accounts_updated_at BEFORE UPDATE ON bank_accounts
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_plaid_connections_updated_at BEFORE UPDATE ON plaid_connections
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_transaction_syncs_updated_at BEFORE UPDATE ON transaction_syncs
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_account_balances_updated_at BEFORE UPDATE ON account_balances
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_banking_preferences_updated_at BEFORE UPDATE ON banking_preferences
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Create function to calculate balance change
CREATE OR REPLACE FUNCTION calculate_balance_change()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.previous_amount IS NULL AND OLD.amount IS NOT NULL THEN
        NEW.previous_amount = OLD.amount;
        NEW.change_amount = NEW.amount - OLD.amount;
        
        IF OLD.amount != 0 THEN
            NEW.change_percentage = (NEW.change_amount / OLD.amount) * 100;
        ELSE
            NEW.change_percentage = CASE WHEN NEW.amount > 0 THEN 100.0 ELSE 0.0 END;
        END IF;
    END IF;
    
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create trigger for balance change calculation
CREATE TRIGGER calculate_balance_change_trigger BEFORE UPDATE ON account_balances
    FOR EACH ROW EXECUTE FUNCTION calculate_balance_change();

-- Create function to update account last_sync_at
CREATE OR REPLACE FUNCTION update_account_last_sync()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.status = 'success' AND NEW.completed_at IS NOT NULL THEN
        UPDATE bank_accounts 
        SET last_sync_at = NEW.completed_at,
            updated_at = NOW()
        WHERE id = NEW.bank_account_id;
    END IF;
    
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create trigger for updating account last_sync_at
CREATE TRIGGER update_account_last_sync_trigger AFTER UPDATE ON transaction_syncs
    FOR EACH ROW EXECUTE FUNCTION update_account_last_sync();

-- Create function to update connection last_sync_at
CREATE OR REPLACE FUNCTION update_connection_last_sync()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.status = 'success' AND NEW.completed_at IS NOT NULL THEN
        UPDATE plaid_connections 
        SET last_sync_at = NEW.completed_at,
            updated_at = NOW()
        WHERE id = NEW.plaid_connection_id;
    END IF;
    
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create trigger for updating connection last_sync_at
CREATE TRIGGER update_connection_last_sync_trigger AFTER UPDATE ON transaction_syncs
    FOR EACH ROW EXECUTE FUNCTION update_connection_last_sync();

-- Create function to set current balance to false for old balances
CREATE OR REPLACE FUNCTION set_old_balances_inactive()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.is_current = TRUE THEN
        UPDATE account_balances 
        SET is_current = FALSE
        WHERE bank_account_id = NEW.bank_account_id 
          AND balance_type = NEW.balance_type 
          AND id != NEW.id;
    END IF;
    
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create trigger for setting old balances inactive
CREATE TRIGGER set_old_balances_inactive_trigger BEFORE INSERT OR UPDATE ON account_balances
    FOR EACH ROW EXECUTE FUNCTION set_old_balances_inactive();

-- Create views for common queries

-- View for active bank accounts with latest balances
CREATE VIEW active_bank_accounts AS
SELECT 
    ba.id,
    ba.user_id,
    ba.plaid_connection_id,
    ba.account_id,
    ba.name,
    ba.mask,
    ba.type,
    ba.subtype,
    ba.account_type,
    ba.status,
    ba.verification_status,
    ba.current_balance,
    ba.available_balance,
    ba.credit_limit,
    ba.iso_currency_code,
    ba.last_sync_at,
    pc.institution_name,
    pc.institution_logo,
    pc.sync_frequency,
    pc.is_active as connection_active,
    ab.amount as latest_balance,
    ab.as_of_date as balance_date
FROM bank_accounts ba
JOIN plaid_connections pc ON ba.plaid_connection_id = pc.id
LEFT JOIN account_balances ab ON ba.id = ab.bank_account_id AND ab.is_current = TRUE
WHERE ba.is_active = TRUE AND pc.is_active = TRUE;

-- View for sync statistics
CREATE VIEW sync_statistics AS
SELECT 
    ba.id as bank_account_id,
    ba.name as account_name,
    pc.institution_name,
    COUNT(ts.id) as total_syncs,
    COUNT(CASE WHEN ts.status = 'success' THEN 1 END) as successful_syncs,
    COUNT(CASE WHEN ts.status = 'failed' THEN 1 END) as failed_syncs,
    AVG(ts.duration) as avg_sync_duration,
    MAX(ts.completed_at) as last_sync_at,
    SUM(ts.records_processed) as total_records_processed,
    SUM(ts.records_failed) as total_records_failed
FROM bank_accounts ba
JOIN plaid_connections pc ON ba.plaid_connection_id = pc.id
LEFT JOIN transaction_syncs ts ON ba.id = ts.bank_account_id
GROUP BY ba.id, ba.name, pc.institution_name;

-- View for user account summary
CREATE VIEW user_account_summary AS
SELECT 
    u.id as user_id,
    u.email,
    COUNT(ba.id) as total_accounts,
    COUNT(CASE WHEN ba.status = 'active' THEN 1 END) as active_accounts,
    COUNT(CASE WHEN ba.status = 'error' THEN 1 END) as error_accounts,
    COUNT(DISTINCT pc.institution_id) as unique_institutions,
    SUM(ab.amount) as total_balance,
    MAX(ba.last_sync_at) as last_sync_at
FROM users u
LEFT JOIN bank_accounts ba ON u.id = ba.user_id
LEFT JOIN plaid_connections pc ON ba.plaid_connection_id = pc.id
LEFT JOIN account_balances ab ON ba.id = ab.bank_account_id AND ab.is_current = TRUE
GROUP BY u.id, u.email;

-- Insert initial data for testing (optional)
-- This can be removed in production

-- Insert sample banking preferences for existing users
INSERT INTO banking_preferences (user_id, sync_frequency, notification_frequency)
SELECT 
    u.id,
    'daily',
    'daily'
FROM users u
WHERE NOT EXISTS (
    SELECT 1 FROM banking_preferences bp WHERE bp.user_id = u.id
);

-- Create comments for documentation
COMMENT ON TABLE bank_accounts IS 'Stores bank account details and institution information';
COMMENT ON TABLE plaid_connections IS 'Enhanced Plaid connection model with additional functionality';
COMMENT ON TABLE transaction_syncs IS 'Tracks transaction synchronization history and last updates';
COMMENT ON TABLE account_balances IS 'Stores current balances and historical balance data';
COMMENT ON TABLE banking_preferences IS 'User settings and notification preferences for banking';

COMMENT ON COLUMN bank_accounts.account_id IS 'Plaid account identifier';
COMMENT ON COLUMN bank_accounts.mask IS 'Last 4 digits of account number';
COMMENT ON COLUMN bank_accounts.current_balance IS 'Current account balance';
COMMENT ON COLUMN bank_accounts.available_balance IS 'Available balance (may differ from current)';
COMMENT ON COLUMN bank_accounts.credit_limit IS 'Credit limit for credit accounts';
COMMENT ON COLUMN bank_accounts.metadata IS 'Additional account metadata in JSON format';

COMMENT ON COLUMN plaid_connections.access_token IS 'Encrypted Plaid access token';
COMMENT ON COLUMN plaid_connections.item_id IS 'Plaid item identifier (unique)';
COMMENT ON COLUMN plaid_connections.sync_frequency IS 'How often to sync this connection';
COMMENT ON COLUMN plaid_connections.error_count IS 'Number of consecutive sync errors';

COMMENT ON COLUMN transaction_syncs.sync_type IS 'Type of sync operation performed';
COMMENT ON COLUMN transaction_syncs.records_processed IS 'Total records processed in this sync';
COMMENT ON COLUMN transaction_syncs.records_failed IS 'Number of records that failed to sync';
COMMENT ON COLUMN transaction_syncs.duration IS 'Sync duration in seconds';

COMMENT ON COLUMN account_balances.balance_type IS 'Type of balance (current, available, etc.)';
COMMENT ON COLUMN account_balances.is_current IS 'Whether this is the most recent balance';
COMMENT ON COLUMN account_balances.source IS 'Source of balance data (plaid, manual, calculated)';

COMMENT ON COLUMN banking_preferences.sync_frequency IS 'How often to sync accounts';
COMMENT ON COLUMN banking_preferences.balance_threshold IS 'Threshold for balance change notifications';
COMMENT ON COLUMN banking_preferences.notification_frequency IS 'How often to send notifications';
COMMENT ON COLUMN banking_preferences.account_alias IS 'User-defined account nickname'; 