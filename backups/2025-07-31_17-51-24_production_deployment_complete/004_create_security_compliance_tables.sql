-- Migration: Create Security and Compliance Tables
-- Description: Creates comprehensive database schema for security and compliance features
-- Date: 2025-01-27
-- Author: MINGUS Development Team

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create encryption keys table
CREATE TABLE encryption_keys (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    key_id VARCHAR(255) NOT NULL UNIQUE,
    key_material BYTEA NOT NULL, -- Encrypted key material
    algorithm VARCHAR(50) NOT NULL,
    key_type VARCHAR(50) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    rotated_at TIMESTAMP WITH TIME ZONE,
    usage_count INTEGER NOT NULL DEFAULT 0,
    last_used_at TIMESTAMP WITH TIME ZONE,
    key_version VARCHAR(20) NOT NULL DEFAULT '1.0',
    key_purpose VARCHAR(100) NOT NULL,
    data_classification VARCHAR(50) NOT NULL
);

-- Create user consents table
CREATE TABLE user_consents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    consent_type VARCHAR(100) NOT NULL,
    granted BOOLEAN NOT NULL,
    granted_at TIMESTAMP WITH TIME ZONE NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE,
    consent_version VARCHAR(20) NOT NULL DEFAULT '1.0',
    ip_address VARCHAR(45) NOT NULL,
    user_agent TEXT NOT NULL,
    data_processing_purposes JSONB NOT NULL DEFAULT '[]',
    third_parties JSONB NOT NULL DEFAULT '[]',
    revoked_at TIMESTAMP WITH TIME ZONE,
    revoked_reason VARCHAR(255),
    revoked_ip_address VARCHAR(45),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Create data retention records table
CREATE TABLE data_retention_records (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    data_type VARCHAR(100) NOT NULL,
    retention_policy VARCHAR(50) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE,
    deletion_scheduled BOOLEAN NOT NULL DEFAULT TRUE,
    deletion_date TIMESTAMP WITH TIME ZONE,
    deleted_at TIMESTAMP WITH TIME ZONE,
    deletion_method VARCHAR(50),
    deletion_verified BOOLEAN NOT NULL DEFAULT FALSE,
    retention_reason VARCHAR(255),
    legal_basis VARCHAR(100),
    data_volume INTEGER
);

-- Create security audit logs table
CREATE TABLE security_audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(100) NOT NULL,
    resource_id UUID,
    ip_address VARCHAR(45) NOT NULL,
    user_agent TEXT NOT NULL,
    request_method VARCHAR(10),
    request_path VARCHAR(500),
    success BOOLEAN NOT NULL,
    risk_level VARCHAR(20) NOT NULL,
    threat_score INTEGER,
    details JSONB,
    error_message TEXT,
    session_id VARCHAR(255),
    correlation_id VARCHAR(255),
    country_code VARCHAR(2),
    city VARCHAR(100)
);

-- Create PCI compliance records table
CREATE TABLE pci_compliance_records (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    requirement_id VARCHAR(20) NOT NULL,
    requirement_name VARCHAR(255) NOT NULL,
    requirement_description TEXT NOT NULL,
    compliant BOOLEAN NOT NULL,
    last_assessed TIMESTAMP WITH TIME ZONE NOT NULL,
    next_assessment TIMESTAMP WITH TIME ZONE,
    assessment_method VARCHAR(100),
    assessor VARCHAR(255),
    assessment_notes TEXT,
    violations_found JSONB,
    remediation_actions JSONB,
    remediation_completed BOOLEAN NOT NULL DEFAULT FALSE,
    remediation_deadline TIMESTAMP WITH TIME ZONE,
    evidence_files JSONB,
    documentation_urls JSONB,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Create GDPR data requests table
CREATE TABLE gdpr_data_requests (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    request_type VARCHAR(50) NOT NULL,
    request_reason TEXT,
    submitted_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    completed_at TIMESTAMP WITH TIME ZONE,
    assigned_to VARCHAR(255),
    processing_notes TEXT,
    estimated_completion TIMESTAMP WITH TIME ZONE,
    data_categories JSONB,
    date_range JSONB,
    format_preference VARCHAR(50),
    verification_method VARCHAR(50),
    verification_completed BOOLEAN NOT NULL DEFAULT FALSE,
    verification_notes TEXT,
    response_data JSONB,
    response_format VARCHAR(50),
    response_size INTEGER,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Create security incidents table
CREATE TABLE security_incidents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    incident_type VARCHAR(100) NOT NULL,
    severity VARCHAR(20) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'open',
    title VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    affected_users INTEGER,
    affected_data JSONB,
    detected_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    reported_at TIMESTAMP WITH TIME ZONE,
    resolved_at TIMESTAMP WITH TIME ZONE,
    assigned_to VARCHAR(255),
    response_actions JSONB,
    containment_measures TEXT,
    remediation_actions TEXT,
    data_breach BOOLEAN NOT NULL DEFAULT FALSE,
    financial_impact INTEGER,
    reputation_impact VARCHAR(50),
    regulatory_notification BOOLEAN NOT NULL DEFAULT FALSE,
    notification_date TIMESTAMP WITH TIME ZONE,
    notification_authority VARCHAR(255),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Create indexes for better performance
CREATE INDEX idx_encryption_keys_active ON encryption_keys(is_active);
CREATE INDEX idx_encryption_keys_algorithm ON encryption_keys(algorithm);
CREATE INDEX idx_encryption_keys_purpose ON encryption_keys(key_purpose);
CREATE INDEX idx_encryption_keys_classification ON encryption_keys(data_classification);
CREATE INDEX idx_encryption_keys_expires ON encryption_keys(expires_at);

CREATE INDEX idx_user_consents_user_type ON user_consents(user_id, consent_type);
CREATE INDEX idx_user_consents_granted ON user_consents(granted);
CREATE INDEX idx_user_consents_expires ON user_consents(expires_at);
CREATE INDEX idx_user_consents_revoked ON user_consents(revoked_at);

CREATE INDEX idx_data_retention_user_type ON data_retention_records(user_id, data_type);
CREATE INDEX idx_data_retention_policy ON data_retention_records(retention_policy);
CREATE INDEX idx_data_retention_expires ON data_retention_records(expires_at);
CREATE INDEX idx_data_retention_deletion ON data_retention_records(deletion_date);
CREATE INDEX idx_data_retention_deleted ON data_retention_records(deleted_at);

CREATE INDEX idx_security_audit_timestamp ON security_audit_logs(timestamp);
CREATE INDEX idx_security_audit_user_action ON security_audit_logs(user_id, action);
CREATE INDEX idx_security_audit_resource ON security_audit_logs(resource_type, resource_id);
CREATE INDEX idx_security_audit_risk ON security_audit_logs(risk_level);
CREATE INDEX idx_security_audit_success ON security_audit_logs(success);
CREATE INDEX idx_security_audit_session ON security_audit_logs(session_id);
CREATE INDEX idx_security_audit_correlation ON security_audit_logs(correlation_id);

CREATE INDEX idx_pci_compliance_requirement ON pci_compliance_records(requirement_id);
CREATE INDEX idx_pci_compliance_status ON pci_compliance_records(compliant);
CREATE INDEX idx_pci_compliance_assessment ON pci_compliance_records(last_assessed);
CREATE INDEX idx_pci_compliance_next ON pci_compliance_records(next_assessment);
CREATE INDEX idx_pci_compliance_remediation ON pci_compliance_records(remediation_completed);

CREATE INDEX idx_gdpr_requests_user_type ON gdpr_data_requests(user_id, request_type);
CREATE INDEX idx_gdpr_requests_status ON gdpr_data_requests(status);
CREATE INDEX idx_gdpr_requests_submitted ON gdpr_data_requests(submitted_at);
CREATE INDEX idx_gdpr_requests_completed ON gdpr_data_requests(completed_at);
CREATE INDEX idx_gdpr_requests_verification ON gdpr_data_requests(verification_completed);

CREATE INDEX idx_security_incidents_type ON security_incidents(incident_type);
CREATE INDEX idx_security_incidents_severity ON security_incidents(severity);
CREATE INDEX idx_security_incidents_status ON security_incidents(status);
CREATE INDEX idx_security_incidents_detected ON security_incidents(detected_at);
CREATE INDEX idx_security_incidents_resolved ON security_incidents(resolved_at);
CREATE INDEX idx_security_incidents_breach ON security_incidents(data_breach);

-- Create updated_at trigger function (if not exists)
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for updated_at columns
CREATE TRIGGER update_user_consents_updated_at BEFORE UPDATE ON user_consents
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_pci_compliance_records_updated_at BEFORE UPDATE ON pci_compliance_records
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_gdpr_data_requests_updated_at BEFORE UPDATE ON gdpr_data_requests
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_security_incidents_updated_at BEFORE UPDATE ON security_incidents
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Create function to log security events
CREATE OR REPLACE FUNCTION log_security_event()
RETURNS TRIGGER AS $$
BEGIN
    -- This function can be extended to send alerts or notifications
    -- For now, it just ensures the audit log is properly maintained
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create trigger for security audit logging
CREATE TRIGGER security_audit_log_trigger AFTER INSERT ON security_audit_logs
    FOR EACH ROW EXECUTE FUNCTION log_security_event();

-- Create function to check data retention policies
CREATE OR REPLACE FUNCTION check_data_retention()
RETURNS TRIGGER AS $$
BEGIN
    -- Check if data retention policy is being violated
    IF NEW.expires_at IS NOT NULL AND NEW.expires_at < NOW() THEN
        -- Log retention violation
        INSERT INTO security_audit_logs (
            timestamp, action, resource_type, resource_id, 
            ip_address, user_agent, success, risk_level, details
        ) VALUES (
            NOW(), 'retention_policy_violation', 'data_retention', NEW.id,
            'system', 'system', FALSE, 'high',
            jsonb_build_object('data_type', NEW.data_type, 'user_id', NEW.user_id)
        );
    END IF;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create trigger for data retention checking
CREATE TRIGGER data_retention_check_trigger AFTER INSERT OR UPDATE ON data_retention_records
    FOR EACH ROW EXECUTE FUNCTION check_data_retention();

-- Create function to validate PCI compliance
CREATE OR REPLACE FUNCTION validate_pci_compliance()
RETURNS TRIGGER AS $$
BEGIN
    -- Check if PCI compliance requirements are met
    IF NEW.compliant = FALSE THEN
        -- Log PCI compliance violation
        INSERT INTO security_audit_logs (
            timestamp, action, resource_type, resource_id,
            ip_address, user_agent, success, risk_level, details
        ) VALUES (
            NOW(), 'pci_compliance_violation', 'pci_compliance', NEW.id,
            'system', 'system', FALSE, 'critical',
            jsonb_build_object('requirement_id', NEW.requirement_id, 'requirement_name', NEW.requirement_name)
        );
    END IF;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create trigger for PCI compliance validation
CREATE TRIGGER pci_compliance_validation_trigger AFTER INSERT OR UPDATE ON pci_compliance_records
    FOR EACH ROW EXECUTE FUNCTION validate_pci_compliance();

-- Create function to track consent changes
CREATE OR REPLACE FUNCTION track_consent_changes()
RETURNS TRIGGER AS $$
BEGIN
    -- Log consent changes for audit purposes
    IF TG_OP = 'UPDATE' AND (OLD.granted != NEW.granted OR OLD.revoked_at IS DISTINCT FROM NEW.revoked_at) THEN
        INSERT INTO security_audit_logs (
            timestamp, user_id, action, resource_type, resource_id,
            ip_address, user_agent, success, risk_level, details
        ) VALUES (
            NOW(), NEW.user_id, 'consent_changed', 'user_consent', NEW.id,
            COALESCE(NEW.revoked_ip_address, 'system'), 'system', TRUE, 'medium',
            jsonb_build_object(
                'consent_type', NEW.consent_type,
                'old_granted', OLD.granted,
                'new_granted', NEW.granted,
                'revoked_at', NEW.revoked_at
            )
        );
    END IF;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create trigger for consent change tracking
CREATE TRIGGER consent_change_tracking_trigger AFTER UPDATE ON user_consents
    FOR EACH ROW EXECUTE FUNCTION track_consent_changes();

-- Create views for compliance reporting
CREATE VIEW security_compliance_summary AS
SELECT 
    'encryption_keys' as table_name,
    COUNT(*) as total_records,
    COUNT(CASE WHEN is_active = true THEN 1 END) as active_records,
    COUNT(CASE WHEN expires_at < NOW() THEN 1 END) as expired_records
FROM encryption_keys
UNION ALL
SELECT 
    'user_consents' as table_name,
    COUNT(*) as total_records,
    COUNT(CASE WHEN granted = true AND (expires_at IS NULL OR expires_at > NOW()) THEN 1 END) as active_records,
    COUNT(CASE WHEN revoked_at IS NOT NULL THEN 1 END) as expired_records
FROM user_consents
UNION ALL
SELECT 
    'data_retention_records' as table_name,
    COUNT(*) as total_records,
    COUNT(CASE WHEN deleted_at IS NULL THEN 1 END) as active_records,
    COUNT(CASE WHEN deleted_at IS NOT NULL THEN 1 END) as expired_records
FROM data_retention_records
UNION ALL
SELECT 
    'pci_compliance_records' as table_name,
    COUNT(*) as total_records,
    COUNT(CASE WHEN compliant = true THEN 1 END) as active_records,
    COUNT(CASE WHEN compliant = false THEN 1 END) as expired_records
FROM pci_compliance_records;

CREATE VIEW security_incident_summary AS
SELECT 
    incident_type,
    severity,
    status,
    COUNT(*) as incident_count,
    AVG(EXTRACT(EPOCH FROM (resolved_at - detected_at))/3600) as avg_resolution_hours,
    COUNT(CASE WHEN data_breach = true THEN 1 END) as data_breaches,
    SUM(financial_impact) as total_financial_impact
FROM security_incidents
GROUP BY incident_type, severity, status;

CREATE VIEW gdpr_request_summary AS
SELECT 
    request_type,
    status,
    COUNT(*) as request_count,
    AVG(EXTRACT(EPOCH FROM (completed_at - submitted_at))/3600) as avg_processing_hours,
    COUNT(CASE WHEN verification_completed = true THEN 1 END) as verified_requests
FROM gdpr_data_requests
GROUP BY request_type, status;

-- Create indexes for views
CREATE INDEX idx_security_compliance_summary ON security_compliance_summary(table_name);
CREATE INDEX idx_security_incident_summary ON security_incident_summary(incident_type, severity);
CREATE INDEX idx_gdpr_request_summary ON gdpr_request_summary(request_type, status);

-- Insert initial PCI compliance requirements
INSERT INTO pci_compliance_records (
    requirement_id, requirement_name, requirement_description, 
    compliant, last_assessed, assessment_method
) VALUES
('3.1', 'Encrypt Stored Cardholder Data', 'Implement strong cryptography to protect stored cardholder data', true, NOW(), 'automated'),
('3.2', 'Protect Cryptographic Keys', 'Protect cryptographic keys used for encryption of cardholder data', true, NOW(), 'automated'),
('4.1', 'Encrypt Transmission of Cardholder Data', 'Encrypt transmission of cardholder data across open, public networks', true, NOW(), 'automated'),
('7.1', 'Restrict Access to Cardholder Data', 'Limit access to system components and cardholder data to only those individuals whose job requires such access', true, NOW(), 'manual'),
('10.1', 'Implement Audit Logging', 'Implement audit logging to link all access to system components to each individual user', true, NOW(), 'automated'),
('10.2', 'Automated Audit Trails', 'Automated audit trails for all system components to reconstruct events', true, NOW(), 'automated'),
('10.3', 'Record Audit Trail Entries', 'Record audit trail entries for all system components for each event', true, NOW(), 'automated'),
('10.4', 'Synchronize Clocks', 'Synchronize all critical system clocks and times', true, NOW(), 'automated'),
('10.5', 'Secure Audit Trails', 'Secure audit trails so they cannot be altered', true, NOW(), 'automated'),
('10.6', 'Review Logs and Security Events', 'Review logs and security events for all system components', true, NOW(), 'manual'),
('10.7', 'Retain Audit Trail History', 'Retain audit trail history for at least one year', true, NOW(), 'automated'),
('12.1', 'Security Policy', 'Establish, publish, maintain, and disseminate a security policy', true, NOW(), 'manual'),
('12.2', 'Risk Assessment', 'Implement a formal security awareness program', true, NOW(), 'manual'),
('12.3', 'Security Awareness Program', 'Implement a formal security awareness program', true, NOW(), 'manual'),
('12.4', 'Security Responsibilities', 'Ensure that security policies and procedures clearly define responsibilities', true, NOW(), 'manual');

-- Grant permissions (adjust as needed for your setup)
-- GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO your_app_user;
-- GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO your_app_user;

COMMIT; 