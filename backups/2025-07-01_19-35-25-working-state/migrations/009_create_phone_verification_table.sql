-- 009_create_phone_verification_table.sql
-- Migration: Create phone_verification table for smart resend functionality

-- Create phone_verification table
CREATE TABLE IF NOT EXISTS phone_verification (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    phone_number TEXT NOT NULL,
    verification_code_hash TEXT NOT NULL,
    code_sent_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    code_expires_at DATETIME NOT NULL,
    attempts INTEGER DEFAULT 0,
    status TEXT DEFAULT 'pending', -- 'pending', 'verified', 'failed', 'expired'
    resend_count INTEGER DEFAULT 0,
    last_attempt_at DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_phone_verification_user_id ON phone_verification(user_id);
CREATE INDEX IF NOT EXISTS idx_phone_verification_phone_number ON phone_verification(phone_number);
CREATE INDEX IF NOT EXISTS idx_phone_verification_status ON phone_verification(status);
CREATE INDEX IF NOT EXISTS idx_phone_verification_created_at ON phone_verification(created_at);
CREATE INDEX IF NOT EXISTS idx_phone_verification_user_phone ON phone_verification(user_id, phone_number);
CREATE INDEX IF NOT EXISTS idx_phone_verification_resend_count ON phone_verification(resend_count);
CREATE INDEX IF NOT EXISTS idx_phone_verification_user_phone_resend ON phone_verification(user_id, phone_number, resend_count); 