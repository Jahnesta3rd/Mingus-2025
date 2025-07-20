-- 007_create_phone_verification.sql
-- Migration: Create phone_verification table for secure phone verification process

-- ENUM types for status and method
CREATE TYPE verification_status AS ENUM ('pending', 'verified', 'expired', 'failed');
CREATE TYPE verification_method AS ENUM ('sms', 'fallback');

CREATE TABLE phone_verification (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES "user"(id) ON DELETE CASCADE,
    phone_number VARCHAR(20) NOT NULL, -- E.164 format (+countrycode)
    verification_code_hash VARCHAR(128) NOT NULL, -- Store hash, not raw code
    code_sent_at TIMESTAMPTZ DEFAULT NOW(),
    code_expires_at TIMESTAMPTZ NOT NULL,
    attempts INTEGER DEFAULT 0,
    max_attempts INTEGER DEFAULT 5,
    status verification_status DEFAULT 'pending',
    method verification_method DEFAULT 'sms',
    last_attempt_at TIMESTAMPTZ,
    fallback_used BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ,
    CONSTRAINT phone_verification_user_phone_unique UNIQUE (user_id, phone_number)
);

CREATE INDEX idx_phone_verification_user_id ON phone_verification(user_id);
CREATE INDEX idx_phone_verification_phone_number ON phone_verification(phone_number);
CREATE INDEX idx_phone_verification_status ON phone_verification(status);

-- Security best practices:
-- 1. Only store hashed verification codes (never raw codes)
-- 2. Use short expiration (e.g., 5-10 min) for code_expires_at
-- 3. Use attempts and max_attempts for rate limiting
-- 4. Use fallback_used and method for SMS/voice/email fallback tracking 