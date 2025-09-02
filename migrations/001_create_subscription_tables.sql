-- Migration: Create subscription tables
-- Description: Creates all tables for MINGUS subscription management system

-- Create enum types for PostgreSQL (if using PostgreSQL)
-- For SQLite, we'll use TEXT columns with CHECK constraints

-- Create customers table
CREATE TABLE IF NOT EXISTS customers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL UNIQUE,
    stripe_customer_id VARCHAR(255) NOT NULL UNIQUE,
    email VARCHAR(255) NOT NULL,
    name VARCHAR(255),
    phone VARCHAR(50),
    address TEXT, -- JSON stored as TEXT in SQLite
    tax_exempt VARCHAR(50) DEFAULT 'none',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Create indexes for customers table
CREATE INDEX IF NOT EXISTS idx_customers_stripe_customer_id ON customers(stripe_customer_id);
CREATE INDEX IF NOT EXISTS idx_customers_user_id ON customers(user_id);
CREATE INDEX IF NOT EXISTS idx_customers_email ON customers(email);

-- Create pricing_tiers table
CREATE TABLE IF NOT EXISTS pricing_tiers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tier_type VARCHAR(50) NOT NULL UNIQUE CHECK (tier_type IN ('budget', 'mid_tier', 'professional')),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    monthly_price REAL NOT NULL,
    yearly_price REAL NOT NULL,
    stripe_price_id_monthly VARCHAR(255) UNIQUE,
    stripe_price_id_yearly VARCHAR(255) UNIQUE,
    max_health_checkins_per_month INTEGER DEFAULT 4,
    max_financial_reports_per_month INTEGER DEFAULT 2,
    max_ai_insights_per_month INTEGER DEFAULT 0,
    max_projects INTEGER DEFAULT 1,
    max_team_members INTEGER DEFAULT 1,
    max_storage_gb INTEGER DEFAULT 1,
    max_api_calls_per_month INTEGER DEFAULT 1000,
    advanced_analytics BOOLEAN DEFAULT 0,
    priority_support BOOLEAN DEFAULT 0,
    custom_integrations BOOLEAN DEFAULT 0,
    is_active BOOLEAN DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for pricing_tiers table
CREATE INDEX IF NOT EXISTS idx_pricing_tiers_tier_type ON pricing_tiers(tier_type);
CREATE INDEX IF NOT EXISTS idx_pricing_tiers_is_active ON pricing_tiers(is_active);

-- Create subscriptions table
CREATE TABLE IF NOT EXISTS subscriptions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id INTEGER NOT NULL,
    pricing_tier_id INTEGER NOT NULL,
    stripe_subscription_id VARCHAR(255) NOT NULL UNIQUE,
    status VARCHAR(50) NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'past_due', 'canceled', 'unpaid')),
    current_period_start DATETIME NOT NULL,
    current_period_end DATETIME NOT NULL,
    cancel_at_period_end BOOLEAN DEFAULT 0,
    canceled_at DATETIME,
    trial_start DATETIME,
    trial_end DATETIME,
    billing_cycle VARCHAR(20) NOT NULL DEFAULT 'monthly' CHECK (billing_cycle IN ('monthly', 'annual')),
    amount REAL NOT NULL,
    currency VARCHAR(3) DEFAULT 'USD',
    
    -- Proration and billing features
    proration_behavior VARCHAR(50) DEFAULT 'create_prorations',
    proration_date DATETIME,
    next_billing_date DATETIME,
    
    -- Tax and compliance
    tax_percent REAL DEFAULT 0.0,
    tax_calculation_method VARCHAR(50) DEFAULT 'automatic' CHECK (tax_calculation_method IN ('automatic', 'manual', 'exempt')),
    tax_exempt VARCHAR(50) DEFAULT 'none',
    tax_identification_number VARCHAR(255),
    
    -- Usage-based billing
    usage_type VARCHAR(50) DEFAULT 'licensed' CHECK (usage_type IN ('licensed', 'metered')),
    usage_aggregation VARCHAR(50) DEFAULT 'sum' CHECK (usage_aggregation IN ('sum', 'last_during_period', 'last_ever', 'max')),
    metadata TEXT, -- JSON stored as TEXT in SQLite
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE CASCADE,
    FOREIGN KEY (pricing_tier_id) REFERENCES pricing_tiers(id) ON DELETE RESTRICT
);

-- Create indexes for subscriptions table
CREATE INDEX IF NOT EXISTS idx_subscriptions_stripe_subscription_id ON subscriptions(stripe_subscription_id);
CREATE INDEX IF NOT EXISTS idx_subscriptions_customer_id ON subscriptions(customer_id);
CREATE INDEX IF NOT EXISTS idx_subscriptions_status ON subscriptions(status);
CREATE INDEX IF NOT EXISTS idx_subscriptions_current_period_end ON subscriptions(current_period_end);

-- Create payment_methods table
CREATE TABLE IF NOT EXISTS payment_methods (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id INTEGER NOT NULL,
    stripe_payment_method_id VARCHAR(255) NOT NULL UNIQUE,
    type VARCHAR(50) NOT NULL,
    brand VARCHAR(50),
    last4 VARCHAR(4),
    exp_month INTEGER,
    exp_year INTEGER,
    country VARCHAR(2),
    fingerprint VARCHAR(255),
    billing_details TEXT, -- JSON stored as TEXT in SQLite
    is_default BOOLEAN DEFAULT 0,
    is_active BOOLEAN DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE CASCADE
);

-- Create indexes for payment_methods table
CREATE INDEX IF NOT EXISTS idx_payment_methods_stripe_payment_method_id ON payment_methods(stripe_payment_method_id);
CREATE INDEX IF NOT EXISTS idx_payment_methods_customer_id ON payment_methods(customer_id);
CREATE INDEX IF NOT EXISTS idx_payment_methods_is_default ON payment_methods(is_default);
CREATE INDEX IF NOT EXISTS idx_payment_methods_is_active ON payment_methods(is_active);

-- Create billing_history table
CREATE TABLE IF NOT EXISTS billing_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id INTEGER NOT NULL,
    subscription_id INTEGER,
    stripe_invoice_id VARCHAR(255) NOT NULL UNIQUE,
    stripe_payment_intent_id VARCHAR(255),
    invoice_number VARCHAR(255),
    amount_due REAL NOT NULL,
    amount_paid REAL NOT NULL,
    currency VARCHAR(3) DEFAULT 'USD',
    status VARCHAR(50) NOT NULL CHECK (status IN ('succeeded', 'pending', 'failed', 'canceled', 'refunded')),
    paid BOOLEAN DEFAULT 0,
    invoice_date DATETIME NOT NULL,
    due_date DATETIME,
    paid_date DATETIME,
    description TEXT,
    metadata TEXT, -- JSON stored as TEXT in SQLite
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE CASCADE,
    FOREIGN KEY (subscription_id) REFERENCES subscriptions(id) ON DELETE SET NULL
);

-- Create indexes for billing_history table
CREATE INDEX IF NOT EXISTS idx_billing_history_stripe_invoice_id ON billing_history(stripe_invoice_id);
CREATE INDEX IF NOT EXISTS idx_billing_history_customer_id ON billing_history(customer_id);
CREATE INDEX IF NOT EXISTS idx_billing_history_subscription_id ON billing_history(subscription_id);
CREATE INDEX IF NOT EXISTS idx_billing_history_status ON billing_history(status);
CREATE INDEX IF NOT EXISTS idx_billing_history_invoice_date ON billing_history(invoice_date);

-- Create subscription_usage table
CREATE TABLE IF NOT EXISTS subscription_usage (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    subscription_id INTEGER NOT NULL,
    usage_date DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    projects_created INTEGER DEFAULT 0,
    team_members_added INTEGER DEFAULT 0,
    storage_used_mb INTEGER DEFAULT 0,
    api_calls_made INTEGER DEFAULT 0,
    login_count INTEGER DEFAULT 0,
    feature_usage TEXT, -- JSON stored as TEXT in SQLite
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (subscription_id) REFERENCES subscriptions(id) ON DELETE CASCADE
);

-- Create indexes for subscription_usage table
CREATE INDEX IF NOT EXISTS idx_subscription_usage_subscription_id ON subscription_usage(subscription_id);
CREATE INDEX IF NOT EXISTS idx_subscription_usage_usage_date ON subscription_usage(usage_date);

-- Create tax_calculations table
CREATE TABLE IF NOT EXISTS tax_calculations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id INTEGER NOT NULL,
    subscription_id INTEGER,
    invoice_id INTEGER,
    tax_rate REAL NOT NULL DEFAULT 0.0,
    tax_amount REAL NOT NULL DEFAULT 0.0,
    taxable_amount REAL NOT NULL DEFAULT 0.0,
    tax_jurisdiction VARCHAR(255),
    tax_registration_number VARCHAR(255),
    calculation_method VARCHAR(50) DEFAULT 'automatic' CHECK (calculation_method IN ('automatic', 'manual', 'exempt')),
    is_exempt BOOLEAN DEFAULT 0,
    exemption_reason VARCHAR(255),
    stripe_tax_calculation_id VARCHAR(255) UNIQUE,
    metadata TEXT, -- JSON stored as TEXT in SQLite
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE CASCADE,
    FOREIGN KEY (subscription_id) REFERENCES subscriptions(id) ON DELETE SET NULL,
    FOREIGN KEY (invoice_id) REFERENCES billing_history(id) ON DELETE SET NULL
);

-- Create indexes for tax_calculations table
CREATE INDEX IF NOT EXISTS idx_tax_calculations_customer_id ON tax_calculations(customer_id);
CREATE INDEX IF NOT EXISTS idx_tax_calculations_subscription_id ON tax_calculations(subscription_id);
CREATE INDEX IF NOT EXISTS idx_tax_calculations_invoice_id ON tax_calculations(invoice_id);
CREATE INDEX IF NOT EXISTS idx_tax_calculations_stripe_id ON tax_calculations(stripe_tax_calculation_id);

-- Create refunds table
CREATE TABLE IF NOT EXISTS refunds (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id INTEGER NOT NULL,
    invoice_id INTEGER NOT NULL,
    stripe_refund_id VARCHAR(255) NOT NULL UNIQUE,
    amount REAL NOT NULL,
    currency VARCHAR(3) DEFAULT 'USD',
    reason VARCHAR(255),
    status VARCHAR(50) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'processing', 'succeeded', 'failed', 'canceled')),
    processing_fee REAL DEFAULT 0.0,
    failure_reason VARCHAR(255),
    failure_balance_transaction VARCHAR(255),
    metadata TEXT, -- JSON stored as TEXT in SQLite
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE CASCADE,
    FOREIGN KEY (invoice_id) REFERENCES billing_history(id) ON DELETE CASCADE
);

-- Create indexes for refunds table
CREATE INDEX IF NOT EXISTS idx_refunds_customer_id ON refunds(customer_id);
CREATE INDEX IF NOT EXISTS idx_refunds_invoice_id ON refunds(invoice_id);
CREATE INDEX IF NOT EXISTS idx_refunds_stripe_refund_id ON refunds(stripe_refund_id);
CREATE INDEX IF NOT EXISTS idx_refunds_status ON refunds(status);

-- Create credits table
CREATE TABLE IF NOT EXISTS credits (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id INTEGER NOT NULL,
    amount REAL NOT NULL,
    currency VARCHAR(3) DEFAULT 'USD',
    credit_type VARCHAR(50) NOT NULL CHECK (credit_type IN ('refund', 'promotional', 'adjustment', 'overpayment')),
    description TEXT,
    original_amount REAL NOT NULL,
    remaining_amount REAL NOT NULL,
    is_used BOOLEAN DEFAULT 0,
    expires_at DATETIME,
    stripe_credit_note_id VARCHAR(255) UNIQUE,
    metadata TEXT, -- JSON stored as TEXT in SQLite
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE CASCADE
);

-- Create indexes for credits table
CREATE INDEX IF NOT EXISTS idx_credits_customer_id ON credits(customer_id);
CREATE INDEX IF NOT EXISTS idx_credits_credit_type ON credits(credit_type);
CREATE INDEX IF NOT EXISTS idx_credits_is_used ON credits(is_used);
CREATE INDEX IF NOT EXISTS idx_credits_expires_at ON credits(expires_at);
CREATE INDEX IF NOT EXISTS idx_credits_stripe_credit_note_id ON credits(stripe_credit_note_id);

-- Create proration_calculations table
CREATE TABLE IF NOT EXISTS proration_calculations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    subscription_id INTEGER NOT NULL,
    proration_date DATETIME NOT NULL,
    old_amount REAL NOT NULL,
    new_amount REAL NOT NULL,
    proration_amount REAL NOT NULL,
    currency VARCHAR(3) DEFAULT 'USD',
    calculation_method VARCHAR(50) DEFAULT 'exact_day' CHECK (calculation_method IN ('exact_day', 'exact_time', 'exact_month')),
    proration_behavior VARCHAR(50) DEFAULT 'create_prorations',
    usage_until_proration REAL DEFAULT 0.0,
    usage_after_proration REAL DEFAULT 0.0,
    stripe_proration_id VARCHAR(255) UNIQUE,
    metadata TEXT, -- JSON stored as TEXT in SQLite
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (subscription_id) REFERENCES subscriptions(id) ON DELETE CASCADE
);

-- Create indexes for proration_calculations table
CREATE INDEX IF NOT EXISTS idx_proration_calculations_subscription_id ON proration_calculations(subscription_id);
CREATE INDEX IF NOT EXISTS idx_proration_calculations_proration_date ON proration_calculations(proration_date);
CREATE INDEX IF NOT EXISTS idx_proration_calculations_stripe_proration_id ON proration_calculations(stripe_proration_id);

-- Create feature_usage table
CREATE TABLE IF NOT EXISTS feature_usage (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    subscription_id INTEGER NOT NULL,
    usage_month INTEGER NOT NULL CHECK (usage_month >= 1 AND usage_month <= 12),
    usage_year INTEGER NOT NULL,
    health_checkins_used INTEGER DEFAULT 0,
    financial_reports_used INTEGER DEFAULT 0,
    ai_insights_used INTEGER DEFAULT 0,
    projects_created INTEGER DEFAULT 0,
    team_members_added INTEGER DEFAULT 0,
    storage_used_mb INTEGER DEFAULT 0,
    api_calls_made INTEGER DEFAULT 0,
    last_usage_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    is_reset BOOLEAN DEFAULT 0,
    metadata TEXT, -- JSON stored as TEXT in SQLite
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (subscription_id) REFERENCES subscriptions(id) ON DELETE CASCADE,
    UNIQUE(subscription_id, usage_month, usage_year)
);

-- Create indexes for feature_usage table
CREATE INDEX IF NOT EXISTS idx_feature_usage_subscription_id ON feature_usage(subscription_id);
CREATE INDEX IF NOT EXISTS idx_feature_usage_period ON feature_usage(usage_month, usage_year);
CREATE INDEX IF NOT EXISTS idx_feature_usage_last_usage_date ON feature_usage(last_usage_date);

-- Create audit_logs table
CREATE TABLE IF NOT EXISTS audit_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_type VARCHAR(100) NOT NULL CHECK (event_type IN (
        'subscription_created', 'subscription_updated', 'subscription_canceled', 'subscription_reactivated',
        'subscription_tier_changed', 'subscription_billing_changed', 'payment_succeeded', 'payment_failed',
        'payment_refunded', 'payment_disputed', 'payment_method_added', 'payment_method_removed',
        'payment_method_updated', 'feature_used', 'feature_limit_reached', 'feature_access_denied',
        'usage_reset', 'tax_calculation', 'compliance_check', 'data_export', 'privacy_request',
        'gdpr_request', 'system_maintenance', 'security_event', 'error_occurred'
    )),
    severity VARCHAR(20) NOT NULL DEFAULT 'info' CHECK (severity IN ('info', 'warning', 'error', 'critical')),
    event_timestamp DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    user_id INTEGER,
    customer_id INTEGER,
    session_id VARCHAR(255),
    ip_address VARCHAR(45),
    user_agent TEXT,
    subscription_id INTEGER,
    invoice_id INTEGER,
    payment_method_id INTEGER,
    feature_usage_id INTEGER,
    event_description TEXT NOT NULL,
    old_values TEXT, -- JSON stored as TEXT in SQLite
    new_values TEXT, -- JSON stored as TEXT in SQLite
    changed_fields TEXT, -- JSON stored as TEXT in SQLite
    compliance_impact BOOLEAN DEFAULT 0,
    security_impact BOOLEAN DEFAULT 0,
    data_classification VARCHAR(50) DEFAULT 'internal',
    stripe_event_id VARCHAR(255),
    external_reference VARCHAR(255),
    metadata TEXT, -- JSON stored as TEXT in SQLite
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL,
    FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE SET NULL,
    FOREIGN KEY (subscription_id) REFERENCES subscriptions(id) ON DELETE SET NULL,
    FOREIGN KEY (invoice_id) REFERENCES billing_history(id) ON DELETE SET NULL,
    FOREIGN KEY (payment_method_id) REFERENCES payment_methods(id) ON DELETE SET NULL,
    FOREIGN KEY (feature_usage_id) REFERENCES feature_usage(id) ON DELETE SET NULL
);

-- Create indexes for audit_logs table
CREATE INDEX IF NOT EXISTS idx_audit_logs_event_type ON audit_logs(event_type);
CREATE INDEX IF NOT EXISTS idx_audit_logs_event_timestamp ON audit_logs(event_timestamp);
CREATE INDEX IF NOT EXISTS idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_customer_id ON audit_logs(customer_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_subscription_id ON audit_logs(subscription_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_severity ON audit_logs(severity);
CREATE INDEX IF NOT EXISTS idx_audit_logs_compliance_impact ON audit_logs(compliance_impact);
CREATE INDEX IF NOT EXISTS idx_audit_logs_security_impact ON audit_logs(security_impact);

-- Create compliance_records table
CREATE TABLE IF NOT EXISTS compliance_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    compliance_type VARCHAR(100) NOT NULL,
    requirement_id VARCHAR(255),
    requirement_description TEXT,
    customer_id INTEGER,
    subscription_id INTEGER,
    user_id INTEGER,
    status VARCHAR(50) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'compliant', 'non_compliant', 'exempt')),
    compliance_date DATETIME,
    next_review_date DATETIME,
    evidence_description TEXT,
    evidence_files TEXT, -- JSON stored as TEXT in SQLite
    auditor_notes TEXT,
    risk_level VARCHAR(20) DEFAULT 'low' CHECK (risk_level IN ('low', 'medium', 'high', 'critical')),
    risk_description TEXT,
    mitigation_actions TEXT, -- JSON stored as TEXT in SQLite
    external_audit_id VARCHAR(255),
    regulatory_reference VARCHAR(255),
    metadata TEXT, -- JSON stored as TEXT in SQLite
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE SET NULL,
    FOREIGN KEY (subscription_id) REFERENCES subscriptions(id) ON DELETE SET NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
);

-- Create indexes for compliance_records table
CREATE INDEX IF NOT EXISTS idx_compliance_records_compliance_type ON compliance_records(compliance_type);
CREATE INDEX IF NOT EXISTS idx_compliance_records_status ON compliance_records(status);
CREATE INDEX IF NOT EXISTS idx_compliance_records_customer_id ON compliance_records(customer_id);
CREATE INDEX IF NOT EXISTS idx_compliance_records_next_review_date ON compliance_records(next_review_date);
CREATE INDEX IF NOT EXISTS idx_compliance_records_risk_level ON compliance_records(risk_level);

-- Create security_events table
CREATE TABLE IF NOT EXISTS security_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_type VARCHAR(100) NOT NULL,
    severity VARCHAR(20) NOT NULL DEFAULT 'info' CHECK (severity IN ('info', 'warning', 'error', 'critical')),
    event_timestamp DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    user_id INTEGER,
    customer_id INTEGER,
    session_id VARCHAR(255),
    ip_address VARCHAR(45),
    user_agent TEXT,
    location_data TEXT, -- JSON stored as TEXT in SQLite
    threat_level VARCHAR(20) DEFAULT 'low' CHECK (threat_level IN ('low', 'medium', 'high', 'critical')),
    attack_vector VARCHAR(100),
    indicators TEXT, -- JSON stored as TEXT in SQLite
    response_actions TEXT, -- JSON stored as TEXT in SQLite
    investigation_status VARCHAR(50) DEFAULT 'open' CHECK (investigation_status IN ('open', 'investigating', 'resolved', 'closed')),
    investigator_id INTEGER,
    investigation_notes TEXT,
    resolution_date DATETIME,
    security_tool_id VARCHAR(255),
    external_threat_id VARCHAR(255),
    metadata TEXT, -- JSON stored as TEXT in SQLite
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL,
    FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE SET NULL,
    FOREIGN KEY (investigator_id) REFERENCES users(id) ON DELETE SET NULL
);

-- Create indexes for security_events table
CREATE INDEX IF NOT EXISTS idx_security_events_event_type ON security_events(event_type);
CREATE INDEX IF NOT EXISTS idx_security_events_event_timestamp ON security_events(event_timestamp);
CREATE INDEX IF NOT EXISTS idx_security_events_user_id ON security_events(user_id);
CREATE INDEX IF NOT EXISTS idx_security_events_customer_id ON security_events(customer_id);
CREATE INDEX IF NOT EXISTS idx_security_events_severity ON security_events(severity);
CREATE INDEX IF NOT EXISTS idx_security_events_threat_level ON security_events(threat_level);
CREATE INDEX IF NOT EXISTS idx_security_events_investigation_status ON security_events(investigation_status);

-- Insert default pricing tiers
INSERT INTO pricing_tiers (tier_type, name, description, monthly_price, yearly_price, max_health_checkins_per_month, max_financial_reports_per_month, max_ai_insights_per_month, max_projects, max_team_members, max_storage_gb, max_api_calls_per_month, advanced_analytics, priority_support, custom_integrations, is_active, created_at, updated_at) VALUES
('budget', 'Budget Tier', 'Perfect for individuals getting started with personal finance management', 15.00, 144.00, 4, 2, 0, 1, 1, 1, 1000, 0, 0, 0, 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
('mid_tier', 'Mid-Tier', 'Ideal for serious users who want advanced financial insights and career protection', 35.00, 336.00, 12, 10, 50, 3, 2, 5, 5000, 1, 1, 0, 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
('professional', 'Professional Tier', 'Comprehensive solution for professionals, teams, and businesses', 100.00, 960.00, -1, -1, -1, -1, 10, 50, 10000, 1, 1, 1, 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP);

-- Create triggers for updated_at timestamps
CREATE TRIGGER IF NOT EXISTS update_customers_updated_at 
    AFTER UPDATE ON customers
    BEGIN
        UPDATE customers SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
    END;

CREATE TRIGGER IF NOT EXISTS update_pricing_tiers_updated_at 
    AFTER UPDATE ON pricing_tiers
    BEGIN
        UPDATE pricing_tiers SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
    END;

CREATE TRIGGER IF NOT EXISTS update_subscriptions_updated_at 
    AFTER UPDATE ON subscriptions
    BEGIN
        UPDATE subscriptions SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
    END;

CREATE TRIGGER IF NOT EXISTS update_payment_methods_updated_at 
    AFTER UPDATE ON payment_methods
    BEGIN
        UPDATE payment_methods SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
    END;

CREATE TRIGGER IF NOT EXISTS update_billing_history_updated_at 
    AFTER UPDATE ON billing_history
    BEGIN
        UPDATE billing_history SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
    END;

CREATE TRIGGER IF NOT EXISTS update_subscription_usage_updated_at 
    AFTER UPDATE ON subscription_usage
    BEGIN
        UPDATE subscription_usage SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
    END;

CREATE TRIGGER IF NOT EXISTS update_tax_calculations_updated_at 
    AFTER UPDATE ON tax_calculations
    BEGIN
        UPDATE tax_calculations SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
    END;

CREATE TRIGGER IF NOT EXISTS update_refunds_updated_at 
    AFTER UPDATE ON refunds
    BEGIN
        UPDATE refunds SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
    END;

CREATE TRIGGER IF NOT EXISTS update_credits_updated_at 
    AFTER UPDATE ON credits
    BEGIN
        UPDATE credits SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
    END;

CREATE TRIGGER IF NOT EXISTS update_proration_calculations_updated_at 
    AFTER UPDATE ON proration_calculations
    BEGIN
        UPDATE proration_calculations SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
    END;

CREATE TRIGGER IF NOT EXISTS update_feature_usage_updated_at 
    AFTER UPDATE ON feature_usage
    BEGIN
        UPDATE feature_usage SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
    END;

CREATE TRIGGER IF NOT EXISTS update_compliance_records_updated_at 
    AFTER UPDATE ON compliance_records
    BEGIN
        UPDATE compliance_records SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
    END;

CREATE TRIGGER IF NOT EXISTS update_security_events_updated_at 
    AFTER UPDATE ON security_events
    BEGIN
        UPDATE security_events SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
    END; 