-- 008_add_smart_resend_analytics.sql
-- Migration: Add smart resend functionality and analytics tracking

-- Add resend_count column to phone_verification table
ALTER TABLE phone_verification 
ADD COLUMN IF NOT EXISTS resend_count INTEGER DEFAULT 0;

-- Create verification_analytics table for tracking resend patterns
CREATE TABLE IF NOT EXISTS verification_analytics (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES "user"(id) ON DELETE CASCADE,
    event_type VARCHAR(50) NOT NULL, -- 'send_code', 'verify_success', 'verify_failed', 'change_phone', 'resend_request'
    event_data JSONB, -- Store detailed event data
    created_at TIMESTAMPTZ DEFAULT NOW(),
    INDEX idx_verification_analytics_user_id (user_id),
    INDEX idx_verification_analytics_event_type (event_type),
    INDEX idx_verification_analytics_created_at (created_at)
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_phone_verification_resend_count ON phone_verification(resend_count);
CREATE INDEX IF NOT EXISTS idx_phone_verification_user_phone_resend ON phone_verification(user_id, phone_number, resend_count);

-- Add comments for documentation
COMMENT ON COLUMN phone_verification.resend_count IS 'Number of times verification code has been resent for this phone number';
COMMENT ON TABLE verification_analytics IS 'Tracks verification events for analytics and pattern analysis';
COMMENT ON COLUMN verification_analytics.event_type IS 'Type of verification event (send_code, verify_success, verify_failed, change_phone, resend_request)';
COMMENT ON COLUMN verification_analytics.event_data IS 'JSON data containing event-specific information';

-- Create view for resend pattern analysis
CREATE OR REPLACE VIEW verification_resend_patterns AS
SELECT 
    user_id,
    phone_number,
    COUNT(*) as total_verifications,
    MAX(resend_count) as max_resend_count,
    AVG(resend_count) as avg_resend_count,
    COUNT(CASE WHEN status = 'verified' THEN 1 END) as successful_verifications,
    COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed_verifications,
    MIN(created_at) as first_attempt,
    MAX(created_at) as last_attempt
FROM phone_verification 
GROUP BY user_id, phone_number;

-- Create view for analytics summary
CREATE OR REPLACE VIEW verification_analytics_summary AS
SELECT 
    event_type,
    COUNT(*) as event_count,
    DATE_TRUNC('day', created_at) as event_date,
    COUNT(DISTINCT user_id) as unique_users
FROM verification_analytics 
GROUP BY event_type, DATE_TRUNC('day', created_at)
ORDER BY event_date DESC, event_count DESC;

-- Add RLS policies for verification_analytics table
ALTER TABLE verification_analytics ENABLE ROW LEVEL SECURITY;

-- Policy: Users can only see their own analytics
CREATE POLICY "Users can view own verification analytics" ON verification_analytics
    FOR SELECT USING (auth.uid() = user_id);

-- Policy: Service can insert analytics (for backend operations)
CREATE POLICY "Service can insert verification analytics" ON verification_analytics
    FOR INSERT WITH CHECK (true);

-- Update existing phone_verification records to have resend_count = 0
UPDATE phone_verification 
SET resend_count = 0 
WHERE resend_count IS NULL; 