-- 010_add_security_audit_logging_sqlite.sql
-- Migration: Add security audit logging and enhanced security features (SQLite version)

-- Create verification_audit_log table for security event tracking
CREATE TABLE IF NOT EXISTS verification_audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    ip_address TEXT NOT NULL,
    user_agent TEXT,
    phone_number TEXT,
    event_type TEXT NOT NULL, -- 'send_code', 'verify_success', 'verify_failed', 'rate_limit_exceeded', 'suspicious_activity', 'sim_swap_detected', 'captcha_failed'
    event_details TEXT, -- JSON data containing event details
    risk_score REAL DEFAULT 0.0, -- Risk score from 0.0 to 1.0
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for security audit log
CREATE INDEX IF NOT EXISTS idx_verification_audit_user_id ON verification_audit_log(user_id);
CREATE INDEX IF NOT EXISTS idx_verification_audit_ip_address ON verification_audit_log(ip_address);
CREATE INDEX IF NOT EXISTS idx_verification_audit_event_type ON verification_audit_log(event_type);
CREATE INDEX IF NOT EXISTS idx_verification_audit_created_at ON verification_audit_log(created_at);
CREATE INDEX IF NOT EXISTS idx_verification_audit_risk_score ON verification_audit_log(risk_score);
CREATE INDEX IF NOT EXISTS idx_verification_audit_user_ip ON verification_audit_log(user_id, ip_address);

-- Add security-related columns to phone_verification table
ALTER TABLE phone_verification ADD COLUMN salt TEXT; -- Salt for code hashing
ALTER TABLE phone_verification ADD COLUMN ip_address TEXT; -- IP address of request
ALTER TABLE phone_verification ADD COLUMN user_agent TEXT; -- User agent of request
ALTER TABLE phone_verification ADD COLUMN captcha_verified INTEGER DEFAULT 0; -- CAPTCHA verification status (0/1 for SQLite)
ALTER TABLE phone_verification ADD COLUMN risk_score REAL DEFAULT 0.0; -- Risk score for this verification

-- Create indexes for new security columns
CREATE INDEX IF NOT EXISTS idx_phone_verification_ip_address ON phone_verification(ip_address);
CREATE INDEX IF NOT EXISTS idx_phone_verification_risk_score ON phone_verification(risk_score);
CREATE INDEX IF NOT EXISTS idx_phone_verification_captcha_verified ON phone_verification(captcha_verified);

-- Create view for suspicious IP addresses (simplified for SQLite)
CREATE VIEW IF NOT EXISTS suspicious_ips AS
SELECT 
    ip_address,
    COUNT(*) as total_events,
    COUNT(CASE WHEN event_type = 'verify_failed' THEN 1 END) as failed_attempts,
    COUNT(CASE WHEN event_type = 'rate_limit_exceeded' THEN 1 END) as rate_limit_violations,
    AVG(risk_score) as avg_risk_score,
    MAX(created_at) as last_activity
FROM verification_audit_log 
WHERE created_at >= datetime('now', '-24 hours')
GROUP BY ip_address
HAVING COUNT(*) > 10 OR AVG(risk_score) > 0.6
ORDER BY avg_risk_score DESC;

-- Create view for user security summary
CREATE VIEW IF NOT EXISTS user_security_summary AS
SELECT 
    user_id,
    COUNT(*) as total_verifications,
    COUNT(CASE WHEN status = 'verified' THEN 1 END) as successful_verifications,
    COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed_verifications,
    COUNT(DISTINCT ip_address) as unique_ips,
    COUNT(DISTINCT phone_number) as unique_phones,
    MAX(created_at) as last_verification,
    AVG(risk_score) as avg_risk_score
FROM phone_verification 
GROUP BY user_id;

-- Update existing records to have default values for new columns
UPDATE phone_verification SET salt = '' WHERE salt IS NULL;
UPDATE phone_verification SET captcha_verified = 0 WHERE captcha_verified IS NULL;
UPDATE phone_verification SET risk_score = 0.0 WHERE risk_score IS NULL; 