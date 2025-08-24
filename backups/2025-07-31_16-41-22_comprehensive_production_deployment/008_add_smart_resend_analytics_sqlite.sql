-- 008_add_smart_resend_analytics_sqlite.sql
-- Migration: Add smart resend functionality and analytics tracking (SQLite version)

-- Add resend_count column to phone_verification table
ALTER TABLE phone_verification 
ADD COLUMN resend_count INTEGER DEFAULT 0;

-- Create verification_analytics table for tracking resend patterns
CREATE TABLE IF NOT EXISTS verification_analytics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    event_type TEXT NOT NULL, -- 'send_code', 'verify_success', 'verify_failed', 'change_phone', 'resend_request'
    event_data TEXT, -- Store detailed event data as JSON
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_phone_verification_resend_count ON phone_verification(resend_count);
CREATE INDEX IF NOT EXISTS idx_phone_verification_user_phone_resend ON phone_verification(user_id, phone_number, resend_count);
CREATE INDEX IF NOT EXISTS idx_verification_analytics_user_id ON verification_analytics(user_id);
CREATE INDEX IF NOT EXISTS idx_verification_analytics_event_type ON verification_analytics(event_type);
CREATE INDEX IF NOT EXISTS idx_verification_analytics_created_at ON verification_analytics(created_at);

-- Update existing phone_verification records to have resend_count = 0
UPDATE phone_verification 
SET resend_count = 0 
WHERE resend_count IS NULL; 