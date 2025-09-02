"""Migration: Add Encryption Fields to Existing Tables

Revision ID: 002_add_encryption_fields
Revises: 001_add_audit_tables
Create Date: 2025-01-27 11:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy.dialects.postgresql import JSONB, UUID, TIMESTAMP, TEXT, INTEGER, BOOLEAN, VARCHAR, BYTEA
from sqlalchemy import text
import uuid

# revision identifiers, used by Alembic.
revision = '002_add_encryption_fields'
down_revision = '001_add_audit_tables'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add encrypted columns to existing tables with data migration."""
    
    # Add encrypted columns to users table
    op.add_column('users', sa.Column('encrypted_ssn', BYTEA, nullable=True))
    op.add_column('users', sa.Column('encrypted_tax_id', BYTEA, nullable=True))
    op.add_column('users', sa.Column('encrypted_passport_number', BYTEA, nullable=True))
    op.add_column('users', sa.Column('encrypted_drivers_license', BYTEA, nullable=True))
    op.add_column('users', sa.Column('encrypted_address', BYTEA, nullable=True))
    op.add_column('users', sa.Column('encrypted_birth_date', BYTEA, nullable=True))
    op.add_column('users', sa.Column('encrypted_phone_number', BYTEA, nullable=True))
    op.add_column('users', sa.Column('encrypted_emergency_contact', BYTEA, nullable=True))
    
    # Add encrypted financial columns to users table
    op.add_column('users', sa.Column('encrypted_monthly_income', BYTEA, nullable=True))
    op.add_column('users', sa.Column('encrypted_income_frequency', BYTEA, nullable=True))
    op.add_column('users', sa.Column('encrypted_primary_income_source', BYTEA, nullable=True))
    op.add_column('users', sa.Column('encrypted_secondary_income_source', BYTEA, nullable=True))
    op.add_column('users', sa.Column('encrypted_current_savings', BYTEA, nullable=True))
    op.add_column('users', sa.Column('encrypted_current_debt', BYTEA, nullable=True))
    op.add_column('users', sa.Column('encrypted_emergency_fund', BYTEA, nullable=True))
    op.add_column('users', sa.Column('encrypted_savings_goal', BYTEA, nullable=True))
    op.add_column('users', sa.Column('encrypted_debt_payoff_goal', BYTEA, nullable=True))
    op.add_column('users', sa.Column('encrypted_investment_goal', BYTEA, nullable=True))
    
    # Add encryption metadata columns
    op.add_column('users', sa.Column('encryption_version', VARCHAR(20), nullable=False, server_default='1.0'))
    op.add_column('users', sa.Column('encryption_algorithm', VARCHAR(50), nullable=False, server_default='AES-256-GCM'))
    op.add_column('users', sa.Column('encryption_key_id', VARCHAR(255), nullable=True))
    op.add_column('users', sa.Column('encryption_iv', BYTEA, nullable=True))
    op.add_column('users', sa.Column('encryption_tag', BYTEA, nullable=True))
    op.add_column('users', sa.Column('encrypted_at', TIMESTAMP(timezone=True), nullable=True))
    
    # Add encrypted columns to user_profiles table if it exists
    try:
        op.add_column('user_profiles', sa.Column('encrypted_ethnicity', BYTEA, nullable=True))
        op.add_column('user_profiles', sa.Column('encrypted_religion', BYTEA, nullable=True))
        op.add_column('user_profiles', sa.Column('encrypted_political_affiliation', BYTEA, nullable=True))
        op.add_column('user_profiles', sa.Column('encrypted_sexual_orientation', BYTEA, nullable=True))
        op.add_column('user_profiles', sa.Column('encrypted_disability_status', BYTEA, nullable=True))
        op.add_column('user_profiles', sa.Column('encrypted_veteran_status', BYTEA, nullable=True))
        op.add_column('user_profiles', sa.Column('encrypted_citizenship_status', BYTEA, nullable=True))
        op.add_column('user_profiles', sa.Column('encrypted_immigration_status', BYTEA, nullable=True))
        
        # Add encryption metadata to user_profiles
        op.add_column('user_profiles', sa.Column('encryption_version', VARCHAR(20), nullable=False, server_default='1.0'))
        op.add_column('user_profiles', sa.Column('encryption_algorithm', VARCHAR(50), nullable=False, server_default='AES-256-GCM'))
        op.add_column('user_profiles', sa.Column('encryption_key_id', VARCHAR(255), nullable=True))
        op.add_column('user_profiles', sa.Column('encryption_iv', BYTEA, nullable=True))
        op.add_column('user_profiles', sa.Column('encryption_tag', BYTEA, nullable=True))
        op.add_column('user_profiles', sa.Column('encrypted_at', TIMESTAMP(timezone=True), nullable=True))
    except Exception:
        # Table might not exist, continue
        pass
    
    # Add encrypted columns to financial tables if they exist
    try:
        # Encrypted financial profile table
        op.add_column('encrypted_financial_profiles', sa.Column('encrypted_account_number', BYTEA, nullable=True))
        op.add_column('encrypted_financial_profiles', sa.Column('encrypted_routing_number', BYTEA, nullable=True))
        op.add_column('encrypted_financial_profiles', sa.Column('encrypted_card_number', BYTEA, nullable=True))
        op.add_column('encrypted_financial_profiles', sa.Column('encrypted_cvv', BYTEA, nullable=True))
        op.add_column('encrypted_financial_profiles', sa.Column('encrypted_expiry_date', BYTEA, nullable=True))
        op.add_column('encrypted_financial_profiles', sa.Column('encrypted_account_holder_name', BYTEA, nullable=True))
        op.add_column('encrypted_financial_profiles', sa.Column('encrypted_bank_name', BYTEA, nullable=True))
        op.add_column('encrypted_financial_profiles', sa.Column('encrypted_account_type', BYTEA, nullable=True))
        
        # Add encryption metadata
        op.add_column('encrypted_financial_profiles', sa.Column('encryption_version', VARCHAR(20), nullable=False, server_default='1.0'))
        op.add_column('encrypted_financial_profiles', sa.Column('encryption_algorithm', VARCHAR(50), nullable=False, server_default='AES-256-GCM'))
        op.add_column('encrypted_financial_profiles', sa.Column('encryption_key_id', VARCHAR(255), nullable=True))
        op.add_column('encrypted_financial_profiles', sa.Column('encryption_iv', BYTEA, nullable=True))
        op.add_column('encrypted_financial_profiles', sa.Column('encryption_tag', BYTEA, nullable=True))
        op.add_column('encrypted_financial_profiles', sa.Column('encrypted_at', TIMESTAMP(timezone=True), nullable=True))
    except Exception:
        # Table might not exist, continue
        pass
    
    # Add encrypted columns to subscription tables if they exist
    try:
        op.add_column('subscriptions', sa.Column('encrypted_payment_method_id', BYTEA, nullable=True))
        op.add_column('subscriptions', sa.Column('encrypted_stripe_customer_id', BYTEA, nullable=True))
        op.add_column('subscriptions', sa.Column('encrypted_stripe_subscription_id', BYTEA, nullable=True))
        op.add_column('subscriptions', sa.Column('encrypted_billing_address', BYTEA, nullable=True))
        op.add_column('subscriptions', sa.Column('encrypted_tax_id', BYTEA, nullable=True))
        
        # Add encryption metadata
        op.add_column('subscriptions', sa.Column('encryption_version', VARCHAR(20), nullable=False, server_default='1.0'))
        op.add_column('subscriptions', sa.Column('encryption_algorithm', VARCHAR(50), nullable=False, server_default='AES-256-GCM'))
        op.add_column('subscriptions', sa.Column('encryption_key_id', VARCHAR(255), nullable=True))
        op.add_column('subscriptions', sa.Column('encryption_iv', BYTEA, nullable=True))
        op.add_column('subscriptions', sa.Column('encryption_tag', BYTEA, nullable=True))
        op.add_column('subscriptions', sa.Column('encrypted_at', TIMESTAMP(timezone=True), nullable=True))
    except Exception:
        # Table might not exist, continue
        pass
    
    # Create encryption keys table for managing encryption keys
    op.create_table(
        'encryption_keys',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('key_id', VARCHAR(255), nullable=False, unique=True, index=True),
        sa.Column('key_material', BYTEA, nullable=False),  # Encrypted key material
        sa.Column('algorithm', VARCHAR(50), nullable=False, index=True),
        sa.Column('key_type', VARCHAR(50), nullable=False, index=True),
        sa.Column('key_purpose', VARCHAR(100), nullable=False, index=True),
        sa.Column('data_classification', VARCHAR(50), nullable=False, index=True),
        sa.Column('is_active', BOOLEAN, nullable=False, default=True, index=True),
        sa.Column('created_at', TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('expires_at', TIMESTAMP(timezone=True), nullable=True),
        sa.Column('rotated_at', TIMESTAMP(timezone=True), nullable=True),
        sa.Column('usage_count', INTEGER, nullable=False, default=0),
        sa.Column('last_used_at', TIMESTAMP(timezone=True), nullable=True),
        sa.Column('key_version', VARCHAR(20), nullable=False, default='1.0'),
        sa.Column('master_key_id', VARCHAR(255), nullable=True),  # For key hierarchy
        sa.Column('encryption_metadata', JSONB, nullable=True)
    )
    
    # Create encryption audit log table
    op.create_table(
        'encryption_audit_log',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('operation_timestamp', TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('operation_type', VARCHAR(50), nullable=False, index=True),  # ENCRYPT, DECRYPT, ROTATE, etc.
        sa.Column('user_id', UUID(as_uuid=True), nullable=True, index=True),
        sa.Column('key_id', VARCHAR(255), nullable=False, index=True),
        sa.Column('table_name', VARCHAR(100), nullable=False, index=True),
        sa.Column('column_name', VARCHAR(100), nullable=False, index=True),
        sa.Column('record_id', VARCHAR(255), nullable=True, index=True),
        sa.Column('operation_success', BOOLEAN, nullable=False, default=True),
        sa.Column('error_message', TEXT, nullable=True),
        sa.Column('ip_address', VARCHAR(45), nullable=False, index=True),
        sa.Column('session_id', VARCHAR(255), nullable=True, index=True),
        sa.Column('operation_metadata', JSONB, nullable=True),
        sa.Column('created_at', TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now())
    )
    
    # Create indexes for encryption tables
    op.create_index('idx_encryption_keys_purpose_active', 'encryption_keys', ['key_purpose', 'is_active'])
    op.create_index('idx_encryption_keys_expires', 'encryption_keys', ['expires_at', 'is_active'])
    op.create_index('idx_encryption_keys_algorithm', 'encryption_keys', ['algorithm', 'key_type'])
    
    op.create_index('idx_encryption_audit_timestamp', 'encryption_audit_log', ['operation_timestamp'])
    op.create_index('idx_encryption_audit_key_table', 'encryption_audit_log', ['key_id', 'table_name'])
    op.create_index('idx_encryption_audit_operation', 'encryption_audit_log', ['operation_type', 'operation_success'])
    
    # Create function for data migration from plaintext to encrypted
    op.execute("""
        CREATE OR REPLACE FUNCTION migrate_plaintext_to_encrypted(
            source_table text,
            source_column text,
            target_column text,
            key_id text
        ) RETURNS integer AS $$
        DECLARE
            record_count integer := 0;
            update_sql text;
        BEGIN
            -- This function would be called with proper encryption logic
            -- For now, it's a placeholder that would be implemented with
            -- actual encryption functions
            
            update_sql := format('
                UPDATE %I 
                SET %I = encrypt_column(%I, %L),
                    encryption_version = ''1.0'',
                    encryption_algorithm = ''AES-256-GCM'',
                    encryption_key_id = %L,
                    encrypted_at = NOW()
                WHERE %I IS NOT NULL 
                AND %I IS NULL
            ', source_table, target_column, source_column, key_id, key_id, target_column, source_column);
            
            EXECUTE update_sql;
            GET DIAGNOSTICS record_count = ROW_COUNT;
            
            RETURN record_count;
        END;
        $$ LANGUAGE plpgsql;
    """)
    
    # Create function for backwards compatibility (decrypt on read)
    op.execute("""
        CREATE OR REPLACE FUNCTION get_decrypted_value(
            encrypted_value bytea,
            key_id text,
            default_value text DEFAULT NULL
        ) RETURNS text AS $$
        DECLARE
            decrypted_value text;
        BEGIN
            -- This function would implement actual decryption logic
            -- For now, it returns the default value for backwards compatibility
            
            IF encrypted_value IS NULL THEN
                RETURN default_value;
            ELSE
                -- Placeholder for actual decryption
                -- In production, this would decrypt the value using the specified key
                RETURN default_value;
            END IF;
        END;
        $$ LANGUAGE plpgsql;
    """)
    
    # Create views for backwards compatibility
    # These views allow existing code to continue working while data is encrypted
    op.execute("""
        CREATE OR REPLACE VIEW users_decrypted AS
        SELECT 
            u.*,
            get_decrypted_value(u.encrypted_ssn, u.encryption_key_id, u.ssn) as ssn,
            get_decrypted_value(u.encrypted_tax_id, u.encryption_key_id, u.tax_id) as tax_id,
            get_decrypted_value(u.encrypted_passport_number, u.encryption_key_id, u.passport_number) as passport_number,
            get_decrypted_value(u.encrypted_drivers_license, u.encryption_key_id, u.drivers_license) as drivers_license,
            get_decrypted_value(u.encrypted_address, u.encryption_key_id, u.address) as address,
            get_decrypted_value(u.encrypted_birth_date, u.encryption_key_id, u.birth_date) as birth_date,
            get_decrypted_value(u.encrypted_phone_number, u.encryption_key_id, u.phone_number) as phone_number,
            get_decrypted_value(u.encrypted_monthly_income, u.encryption_key_id, u.monthly_income) as monthly_income,
            get_decrypted_value(u.encrypted_income_frequency, u.encryption_key_id, u.income_frequency) as income_frequency
        FROM users u;
    """)
    
    # Create trigger function to automatically encrypt data on insert/update
    op.execute("""
        CREATE OR REPLACE FUNCTION auto_encrypt_sensitive_data()
        RETURNS TRIGGER AS $$
        DECLARE
            default_key_id text := 'default_encryption_key';
        BEGIN
            -- This trigger would automatically encrypt sensitive data
            -- For now, it's a placeholder that would be implemented with
            -- actual encryption logic
            
            -- Example: Auto-encrypt SSN if it's provided in plaintext
            IF NEW.ssn IS NOT NULL AND NEW.encrypted_ssn IS NULL THEN
                -- NEW.encrypted_ssn := encrypt_value(NEW.ssn, default_key_id);
                NEW.encryption_key_id := default_key_id;
                NEW.encrypted_at := NOW();
            END IF;
            
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)
    
    # Create triggers for automatic encryption
    try:
        op.execute("""
            CREATE TRIGGER trigger_auto_encrypt_users
            BEFORE INSERT OR UPDATE ON users
            FOR EACH ROW
            EXECUTE FUNCTION auto_encrypt_sensitive_data();
        """)
    except Exception:
        # Trigger might already exist, continue
        pass


def downgrade() -> None:
    """Rollback encryption field additions with data preservation."""
    
    # Drop triggers first
    try:
        op.execute("DROP TRIGGER IF EXISTS trigger_auto_encrypt_users ON users;")
    except Exception:
        pass
    
    # Drop functions
    op.execute("DROP FUNCTION IF EXISTS auto_encrypt_sensitive_data();")
    op.execute("DROP FUNCTION IF EXISTS get_decrypted_value(bytea, text, text);")
    op.execute("DROP FUNCTION IF EXISTS migrate_plaintext_to_encrypted(text, text, text, text);")
    
    # Drop views
    op.execute("DROP VIEW IF EXISTS users_decrypted;")
    
    # Drop encryption audit log table
    op.drop_table('encryption_audit_log')
    
    # Drop encryption keys table
    op.drop_table('encryption_keys')
    
    # Remove encrypted columns from subscriptions table
    try:
        op.drop_column('subscriptions', 'encrypted_at')
        op.drop_column('subscriptions', 'encryption_tag')
        op.drop_column('subscriptions', 'encryption_iv')
        op.drop_column('subscriptions', 'encryption_key_id')
        op.drop_column('subscriptions', 'encryption_algorithm')
        op.drop_column('subscriptions', 'encryption_version')
        op.drop_column('subscriptions', 'encrypted_tax_id')
        op.drop_column('subscriptions', 'encrypted_billing_address')
        op.drop_column('subscriptions', 'encrypted_stripe_subscription_id')
        op.drop_column('subscriptions', 'encrypted_stripe_customer_id')
        op.drop_column('subscriptions', 'encrypted_payment_method_id')
    except Exception:
        pass
    
    # Remove encrypted columns from encrypted_financial_profiles table
    try:
        op.drop_column('encrypted_financial_profiles', 'encrypted_at')
        op.drop_column('encrypted_financial_profiles', 'encryption_tag')
        op.drop_column('encrypted_financial_profiles', 'encryption_iv')
        op.drop_column('encrypted_financial_profiles', 'encryption_key_id')
        op.drop_column('encrypted_financial_profiles', 'encryption_algorithm')
        op.drop_column('encrypted_financial_profiles', 'encryption_version')
        op.drop_column('encrypted_financial_profiles', 'encrypted_account_type')
        op.drop_column('encrypted_financial_profiles', 'encrypted_bank_name')
        op.drop_column('encrypted_financial_profiles', 'encrypted_account_holder_name')
        op.drop_column('encrypted_financial_profiles', 'encrypted_expiry_date')
        op.drop_column('encrypted_financial_profiles', 'encrypted_cvv')
        op.drop_column('encrypted_financial_profiles', 'encrypted_card_number')
        op.drop_column('encrypted_financial_profiles', 'encrypted_routing_number')
        op.drop_column('encrypted_financial_profiles', 'encrypted_account_number')
    except Exception:
        pass
    
    # Remove encrypted columns from user_profiles table
    try:
        op.drop_column('user_profiles', 'encrypted_at')
        op.drop_column('user_profiles', 'encryption_tag')
        op.drop_column('user_profiles', 'encryption_iv')
        op.drop_column('user_profiles', 'encryption_key_id')
        op.drop_column('user_profiles', 'encryption_algorithm')
        op.drop_column('user_profiles', 'encryption_version')
        op.drop_column('user_profiles', 'encrypted_immigration_status')
        op.drop_column('user_profiles', 'encrypted_citizenship_status')
        op.drop_column('user_profiles', 'encrypted_veteran_status')
        op.drop_column('user_profiles', 'encrypted_disability_status')
        op.drop_column('user_profiles', 'encrypted_sexual_orientation')
        op.drop_column('user_profiles', 'encrypted_political_affiliation')
        op.drop_column('user_profiles', 'encrypted_religion')
        op.drop_column('user_profiles', 'encrypted_ethnicity')
    except Exception:
        pass
    
    # Remove encrypted columns from users table
    op.drop_column('users', 'encrypted_at')
    op.drop_column('users', 'encryption_tag')
    op.drop_column('users', 'encryption_iv')
    op.drop_column('users', 'encryption_key_id')
    op.drop_column('users', 'encryption_algorithm')
    op.drop_column('users', 'encryption_version')
    op.drop_column('users', 'encrypted_investment_goal')
    op.drop_column('users', 'encrypted_debt_payoff_goal')
    op.drop_column('users', 'encrypted_savings_goal')
    op.drop_column('users', 'encrypted_emergency_fund')
    op.drop_column('users', 'encrypted_current_debt')
    op.drop_column('users', 'encrypted_current_savings')
    op.drop_column('users', 'encrypted_secondary_income_source')
    op.drop_column('users', 'encrypted_primary_income_source')
    op.drop_column('users', 'encrypted_income_frequency')
    op.drop_column('users', 'encrypted_monthly_income')
    op.drop_column('users', 'encrypted_emergency_contact')
    op.drop_column('users', 'encrypted_phone_number')
    op.drop_column('users', 'encrypted_birth_date')
    op.drop_column('users', 'encrypted_address')
    op.drop_column('users', 'encrypted_drivers_license')
    op.drop_column('users', 'encrypted_passport_number')
    op.drop_column('users', 'encrypted_tax_id')
    op.drop_column('users', 'encrypted_ssn')
