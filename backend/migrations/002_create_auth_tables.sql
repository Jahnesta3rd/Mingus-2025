-- Migration: Create Authentication Tables
-- Description: Add tables for email verification and password reset tokens
-- Date: 2025-01-XX
-- Author: MINGUS Development Team

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create auth_tokens table for password reset and other authentication tokens
CREATE TABLE IF NOT EXISTS auth_tokens (
    id SERIAL PRIMARY KEY,
    token_hash VARCHAR(255) NOT NULL UNIQUE,
    user_id INTEGER NOT NULL,
    token_type VARCHAR(50) NOT NULL CHECK (token_type IN ('email_verification', 'password_reset')),
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    used_at TIMESTAMP WITH TIME ZONE NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    ip_address INET NULL,
    user_agent TEXT NULL,
    
    -- Foreign key constraints
    CONSTRAINT fk_auth_tokens_user_id FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    
    -- Indexes for performance
    CONSTRAINT idx_auth_tokens_user_type UNIQUE (user_id, token_type),
    CONSTRAINT idx_auth_tokens_expires UNIQUE (expires_at),
    CONSTRAINT idx_auth_tokens_hash UNIQUE (token_hash)
);

-- Create indexes for auth_tokens table
CREATE INDEX IF NOT EXISTS idx_auth_tokens_user_id ON auth_tokens(user_id);
CREATE INDEX IF NOT EXISTS idx_auth_tokens_token_type ON auth_tokens(token_type);
CREATE INDEX IF NOT EXISTS idx_auth_tokens_expires_at ON auth_tokens(expires_at);
CREATE INDEX IF NOT EXISTS idx_auth_tokens_used_at ON auth_tokens(used_at);
CREATE INDEX IF NOT EXISTS idx_auth_tokens_ip_address ON auth_tokens(ip_address);

-- Create email_verifications table for email verification tracking
CREATE TABLE IF NOT EXISTS email_verifications (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL UNIQUE,
    email VARCHAR(255) NOT NULL,
    verification_token_hash VARCHAR(255) NOT NULL UNIQUE,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    verified_at TIMESTAMP WITH TIME ZONE NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    resend_count INTEGER DEFAULT 0,
    last_resend_at TIMESTAMP WITH TIME ZONE NULL,
    
    -- Foreign key constraints
    CONSTRAINT fk_email_verifications_user_id FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    
    -- Check constraints
    CONSTRAINT chk_email_verifications_resend_count CHECK (resend_count >= 0),
    CONSTRAINT chk_email_verifications_expires_at CHECK (expires_at > created_at)
);

-- Create indexes for email_verifications table
CREATE INDEX IF NOT EXISTS idx_email_verifications_user_id ON email_verifications(user_id);
CREATE INDEX IF NOT EXISTS idx_email_verifications_email ON email_verifications(email);
CREATE INDEX IF NOT EXISTS idx_email_verifications_token_hash ON email_verifications(verification_token_hash);
CREATE INDEX IF NOT EXISTS idx_email_verifications_expires_at ON email_verifications(expires_at);
CREATE INDEX IF NOT EXISTS idx_email_verifications_verified_at ON email_verifications(verified_at);

-- Add email_verified column to users table if it doesn't exist
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'users' AND column_name = 'email_verified'
    ) THEN
        ALTER TABLE users ADD COLUMN email_verified BOOLEAN DEFAULT FALSE;
    END IF;
END $$;

-- Create index on email_verified column
CREATE INDEX IF NOT EXISTS idx_users_email_verified ON users(email_verified);

-- Create audit log table for authentication events
CREATE TABLE IF NOT EXISTS auth_audit_log (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NULL,
    event_type VARCHAR(100) NOT NULL,
    event_data JSONB NULL,
    ip_address INET NULL,
    user_agent TEXT NULL,
    success BOOLEAN NOT NULL,
    error_message TEXT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Foreign key constraints
    CONSTRAINT fk_auth_audit_log_user_id FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
);

-- Create indexes for auth_audit_log table
CREATE INDEX IF NOT EXISTS idx_auth_audit_log_user_id ON auth_audit_log(user_id);
CREATE INDEX IF NOT EXISTS idx_auth_audit_log_event_type ON auth_audit_log(event_type);
CREATE INDEX IF NOT EXISTS idx_auth_audit_log_success ON auth_audit_log(success);
CREATE INDEX IF NOT EXISTS idx_auth_audit_log_created_at ON auth_audit_log(created_at);
CREATE INDEX IF NOT EXISTS idx_auth_audit_log_ip_address ON auth_audit_log(ip_address);

-- Create function to automatically clean up expired tokens
CREATE OR REPLACE FUNCTION cleanup_expired_auth_tokens()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER := 0;
BEGIN
    -- Delete expired auth tokens
    DELETE FROM auth_tokens 
    WHERE expires_at < NOW();
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    
    -- Delete expired email verifications
    DELETE FROM email_verifications 
    WHERE expires_at < NOW() AND verified_at IS NULL;
    
    GET DIAGNOSTICS deleted_count = deleted_count + ROW_COUNT;
    
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Create function to log authentication events
CREATE OR REPLACE FUNCTION log_auth_event(
    p_user_id INTEGER,
    p_event_type VARCHAR(100),
    p_event_data JSONB DEFAULT NULL,
    p_ip_address INET DEFAULT NULL,
    p_user_agent TEXT DEFAULT NULL,
    p_success BOOLEAN DEFAULT TRUE,
    p_error_message TEXT DEFAULT NULL
)
RETURNS VOID AS $$
BEGIN
    INSERT INTO auth_audit_log (
        user_id, event_type, event_data, ip_address, user_agent, 
        success, error_message, created_at
    ) VALUES (
        p_user_id, p_event_type, p_event_data, p_ip_address, p_user_agent,
        p_success, p_error_message, NOW()
    );
END;
$$ LANGUAGE plpgsql;

-- Create function to get user verification status
CREATE OR REPLACE FUNCTION get_user_verification_status(p_user_id INTEGER)
RETURNS JSONB AS $$
DECLARE
    result JSONB;
    user_record RECORD;
    verification_record RECORD;
BEGIN
    -- Get user information
    SELECT id, email, email_verified, created_at
    INTO user_record
    FROM users
    WHERE id = p_user_id;
    
    IF NOT FOUND THEN
        RETURN jsonb_build_object('error', 'User not found');
    END IF;
    
    -- Get verification information
    SELECT id, expires_at, verified_at, resend_count, last_resend_at
    INTO verification_record
    FROM email_verifications
    WHERE user_id = p_user_id;
    
    -- Build result
    result := jsonb_build_object(
        'user_id', user_record.id,
        'email', user_record.email,
        'email_verified', user_record.email_verified,
        'verification_status', CASE 
            WHEN verification_record.id IS NOT NULL THEN
                jsonb_build_object(
                    'has_verification', true,
                    'is_expired', verification_record.expires_at < NOW(),
                    'can_resend', verification_record.last_resend_at IS NULL 
                        OR verification_record.last_resend_at < NOW() - INTERVAL '5 minutes',
                    'resend_count', verification_record.resend_count,
                    'max_resend_attempts', 5
                )
            ELSE
                jsonb_build_object(
                    'has_verification', false,
                    'is_expired', null,
                    'can_resend', null,
                    'resend_count', 0,
                    'max_resend_attempts', 5
                )
        END
    );
    
    RETURN result;
END;
$$ LANGUAGE plpgsql;

-- Create function to validate password strength
CREATE OR REPLACE FUNCTION validate_password_strength(p_password TEXT)
RETURNS JSONB AS $$
DECLARE
    result JSONB;
    has_length BOOLEAN;
    has_letter BOOLEAN;
    has_number BOOLEAN;
    has_special BOOLEAN;
BEGIN
    -- Check password requirements
    has_length := length(p_password) >= 8;
    has_letter := p_password ~ '[a-zA-Z]';
    has_number := p_password ~ '\d';
    has_special := p_password ~ '[!@#$%^&*(),.?":{}|<>]';
    
    -- Build result
    result := jsonb_build_object(
        'valid', has_length AND has_letter AND has_number AND has_special,
        'requirements', jsonb_build_object(
            'length', has_length,
            'letter', has_letter,
            'number', has_number,
            'special', has_special
        ),
        'message', CASE 
            WHEN has_length AND has_letter AND has_number AND has_special THEN
                'Password meets all requirements'
            WHEN NOT has_length THEN
                'Password must be at least 8 characters long'
            WHEN NOT has_letter THEN
                'Password must contain at least one letter'
            WHEN NOT has_number THEN
                'Password must contain at least one number'
            WHEN NOT has_special THEN
                'Password must contain at least one special character'
            ELSE
                'Password does not meet requirements'
        END
    );
    
    RETURN result;
END;
$$ LANGUAGE plpgsql;

-- Grant permissions to application user (adjust as needed)
-- GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO mingus_app;
-- GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO mingus_app;

-- Insert initial data if needed
-- This can be used to set up default configurations or test data

-- Create a scheduled job to clean up expired tokens (if using pg_cron)
-- SELECT cron.schedule('cleanup-expired-tokens', '0 2 * * *', 'SELECT cleanup_expired_auth_tokens();');

-- Add comments for documentation
COMMENT ON TABLE auth_tokens IS 'Stores authentication tokens for password reset and other auth operations';
COMMENT ON TABLE email_verifications IS 'Tracks email verification status and tokens for users';
COMMENT ON TABLE auth_audit_log IS 'Audit log for all authentication events and security monitoring';
COMMENT ON FUNCTION cleanup_expired_auth_tokens() IS 'Automatically removes expired authentication tokens';
COMMENT ON FUNCTION log_auth_event() IS 'Logs authentication events for security monitoring';
COMMENT ON FUNCTION get_user_verification_status() IS 'Returns comprehensive verification status for a user';
COMMENT ON FUNCTION validate_password_strength() IS 'Validates password strength against security requirements';
