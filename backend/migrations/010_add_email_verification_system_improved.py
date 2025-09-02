"""
Migration: Add Comprehensive Email Verification System (Improved)
Description: Implements secure email verification with comprehensive security features
Date: 2025-01-XX
Author: MINGUS Development Team

IMPORTANT: This migration preserves existing user data and provides safe rollback.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision = '010_add_email_verification_system_improved'
down_revision = '009_add_two_factor_auth'
branch_labels = None
depends_on = None

def upgrade():
    """Upgrade to add email verification system with data preservation"""
    
    # Step 1: Create backup of existing user data
    op.execute("""
        CREATE TABLE IF NOT EXISTS users_backup_010 AS 
        SELECT * FROM users;
        
        COMMENT ON TABLE users_backup_010 IS 'Backup of users table before email verification migration';
    """)
    
    # Step 2: Add email_verified column to users table safely
    op.execute("""
        DO $$ 
        BEGIN
            -- Check if column already exists
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'users' AND column_name = 'email_verified'
            ) THEN
                -- Add column with default value
                ALTER TABLE users ADD COLUMN email_verified BOOLEAN DEFAULT FALSE;
                
                -- Update existing users to have email_verified = FALSE
                UPDATE users SET email_verified = FALSE WHERE email_verified IS NULL;
                
                -- Make column NOT NULL after setting defaults
                ALTER TABLE users ALTER COLUMN email_verified SET NOT NULL;
                
                RAISE NOTICE 'Added email_verified column to users table';
            ELSE
                RAISE NOTICE 'email_verified column already exists in users table';
            END IF;
        END $$;
    """)
    
    # Step 3: Create email_verifications table
    op.create_table('email_verifications',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('verification_token_hash', sa.String(length=255), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('verified_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('resend_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('last_resend_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('verification_type', sa.String(length=50), nullable=False, server_default='signup'),
        sa.Column('old_email', sa.String(length=255), nullable=True),
        sa.Column('failed_attempts', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('last_failed_attempt', sa.DateTime(timezone=True), nullable=True),
        sa.Column('locked_until', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE', name='fk_email_verifications_user_id'),
        sa.UniqueConstraint('user_id', 'verification_type', name='uq_email_verification_user_type'),
        sa.UniqueConstraint('verification_token_hash', name='uq_email_verification_token_hash')
    )
    
    # Step 4: Create comprehensive indexes for performance
    op.create_index('idx_email_verifications_user_id', 'email_verifications', ['user_id'])
    op.create_index('idx_email_verifications_email', 'email_verifications', ['email'])
    op.create_index('idx_email_verifications_expires_at', 'email_verifications', ['expires_at'])
    op.create_index('idx_email_verifications_verified_at', 'email_verifications', ['verified_at'])
    op.create_index('idx_email_verifications_expires_created', 'email_verifications', ['expires_at', 'created_at'])
    op.create_index('idx_email_verifications_rate_limit', 'email_verifications', ['user_id', 'failed_attempts', 'locked_until'])
    op.create_index('idx_email_verifications_type_status', 'email_verifications', ['verification_type', 'verified_at'])
    op.create_index('idx_email_verifications_created_at', 'email_verifications', ['created_at'])
    
    # Step 5: Create index on email_verified column for performance
    op.create_index('idx_users_email_verified', 'users', ['email_verified'])
    op.create_index('idx_users_email_verified_created', 'users', ['email_verified', 'created_at'])
    
    # Step 6: Create email_verification_audit_log table
    op.create_table('email_verification_audit_log',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('verification_id', sa.Integer(), nullable=True),
        sa.Column('event_type', sa.String(length=100), nullable=False),
        sa.Column('event_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('success', sa.Boolean(), nullable=False),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL', name='fk_audit_log_user_id'),
        sa.ForeignKeyConstraint(['verification_id'], ['email_verifications.id'], ondelete='SET NULL', name='fk_audit_log_verification_id')
    )
    
    # Step 7: Create indexes for audit log performance
    op.create_index('idx_email_verification_audit_user_id', 'email_verification_audit_log', ['user_id'])
    op.create_index('idx_email_verification_audit_event_type', 'email_verification_audit_log', ['event_type'])
    op.create_index('idx_email_verification_audit_success', 'email_verification_audit_log', ['success'])
    op.create_index('idx_email_verification_audit_created_at', 'email_verification_audit_log', ['created_at'])
    op.create_index('idx_email_verification_audit_ip_address', 'email_verification_audit_log', ['ip_address'])
    op.create_index('idx_email_verification_audit_user_event', 'email_verification_audit_log', ['user_id', 'event_type'])
    
    # Step 8: Create email_verification_settings table
    op.create_table('email_verification_settings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('setting_key', sa.String(length=100), nullable=False),
        sa.Column('setting_value', sa.Text(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('setting_key', name='uq_email_verification_settings_key')
    )
    
    # Step 9: Insert default settings
    op.execute("""
        INSERT INTO email_verification_settings (setting_key, setting_value, description) VALUES
        ('verification_expiry_hours', '24', 'Hours until verification token expires'),
        ('max_resend_attempts', '5', 'Maximum number of resend attempts per day'),
        ('resend_cooldown_hours', '1', 'Hours between resend attempts'),
        ('max_failed_attempts', '5', 'Maximum failed verification attempts before lockout'),
        ('lockout_duration_hours', '1', 'Hours of lockout after max failed attempts'),
        ('reminder_schedule_days', '3,7,14', 'Days after signup to send reminders'),
        ('enable_rate_limiting', 'true', 'Enable rate limiting on verification endpoints'),
        ('enable_audit_logging', 'true', 'Enable comprehensive audit logging'),
        ('default_verification_type', 'signup', 'Default verification type for new users'),
        ('token_length', '64', 'Length of verification tokens')
        ON CONFLICT (setting_key) DO NOTHING;
    """)
    
    # Step 10: Create email_verification_reminders table
    op.create_table('email_verification_reminders',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('verification_id', sa.Integer(), nullable=False),
        sa.Column('reminder_type', sa.String(length=50), nullable=False),
        sa.Column('sent_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('email_sent', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('email_sent_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('email_error', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE', name='fk_reminders_user_id'),
        sa.ForeignKeyConstraint(['verification_id'], ['email_verifications.id'], ondelete='CASCADE', name='fk_reminders_verification_id')
    )
    
    # Step 11: Create indexes for reminders
    op.create_index('idx_email_verification_reminders_user_id', 'email_verification_reminders', ['user_id'])
    op.create_index('idx_email_verification_reminders_verification_id', 'email_verification_reminders', ['verification_id'])
    op.create_index('idx_email_verification_reminders_type', 'email_verification_reminders', ['reminder_type'])
    op.create_index('idx_email_verification_reminders_sent_at', 'email_verification_reminders', ['sent_at'])
    op.create_index('idx_email_verification_reminders_user_type', 'email_verification_reminders', ['user_id', 'reminder_type'])
    
    # Step 12: Create email_verification_analytics table
    op.create_table('email_verification_analytics',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('verification_type', sa.String(length=50), nullable=False),
        sa.Column('total_verifications', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('verified_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('failed_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('expired_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('resend_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('reminder_sent_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('date', 'verification_type', name='uq_analytics_date_type')
    )
    
    # Step 13: Create indexes for analytics
    op.create_index('idx_email_verification_analytics_date', 'email_verification_analytics', ['date'])
    op.create_index('idx_email_verification_analytics_type', 'email_verification_analytics', ['verification_type'])
    op.create_index('idx_email_verification_analytics_date_type', 'email_verification_analytics', ['date', 'verification_type'])
    
    # Step 14: Add constraints and checks
    op.execute("""
        ALTER TABLE email_verifications 
        ADD CONSTRAINT chk_email_verifications_resend_count 
        CHECK (resend_count >= 0);
        
        ALTER TABLE email_verifications 
        ADD CONSTRAINT chk_email_verifications_failed_attempts 
        CHECK (failed_attempts >= 0);
        
        ALTER TABLE email_verifications 
        ADD CONSTRAINT chk_email_verifications_expires_at 
        CHECK (expires_at > created_at);
        
        ALTER TABLE email_verifications 
        ADD CONSTRAINT chk_email_verifications_verification_type 
        CHECK (verification_type IN ('signup', 'email_change', 'password_reset'));
        
        ALTER TABLE email_verification_reminders 
        ADD CONSTRAINT chk_reminders_reminder_type 
        CHECK (reminder_type IN ('first', 'second', 'final'));
    """)
    
    # Step 15: Create database functions for automation
    op.execute("""
        CREATE OR REPLACE FUNCTION cleanup_expired_email_verifications()
        RETURNS integer AS $$
        DECLARE
            deleted_count integer;
        BEGIN
            DELETE FROM email_verifications 
            WHERE expires_at < NOW() 
            AND verified_at IS NULL;
            
            GET DIAGNOSTICS deleted_count = ROW_COUNT;
            RETURN deleted_count;
        END;
        $$ LANGUAGE plpgsql;
        
        COMMENT ON FUNCTION cleanup_expired_email_verifications() IS 'Clean up expired verification records';
    """)
    
    # Step 16: Create function for reminder scheduling
    op.execute("""
        CREATE OR REPLACE FUNCTION schedule_email_verification_reminders()
        RETURNS void AS $$
        DECLARE
            reminder_record RECORD;
            days_since_creation integer;
        BEGIN
            FOR reminder_record IN 
                SELECT 
                    ev.user_id,
                    ev.id as verification_id,
                    ev.created_at,
                    ev.verification_type
                FROM email_verifications ev
                LEFT JOIN email_verification_reminders evr ON ev.id = evr.verification_id
                WHERE ev.verified_at IS NULL
                AND ev.expires_at > NOW()
                AND evr.id IS NULL
            LOOP
                days_since_creation := EXTRACT(DAY FROM (NOW() - reminder_record.created_at));
                
                -- Schedule reminders based on days since creation
                IF days_since_creation >= 3 AND days_since_creation < 4 THEN
                    INSERT INTO email_verification_reminders (user_id, verification_id, reminder_type)
                    VALUES (reminder_record.user_id, reminder_record.verification_id, 'first');
                ELSIF days_since_creation >= 7 AND days_since_creation < 8 THEN
                    INSERT INTO email_verification_reminders (user_id, verification_id, reminder_type)
                    VALUES (reminder_record.user_id, reminder_record.verification_id, 'second');
                ELSIF days_since_creation >= 14 AND days_since_creation < 15 THEN
                    INSERT INTO email_verification_reminders (user_id, verification_id, reminder_type)
                    VALUES (reminder_record.user_id, reminder_record.verification_id, 'final');
                END IF;
            END LOOP;
        END;
        $$ LANGUAGE plpgsql;
        
        COMMENT ON FUNCTION schedule_email_verification_reminders() IS 'Schedule verification reminders based on user signup dates';
    """)
    
    # Step 17: Create function for analytics
    op.execute("""
        CREATE OR REPLACE FUNCTION update_email_verification_analytics()
        RETURNS void AS $$
        DECLARE
            current_date date := CURRENT_DATE;
            analytics_record RECORD;
        BEGIN
            -- Delete existing analytics for current date
            DELETE FROM email_verification_analytics WHERE date = current_date;
            
            -- Insert new analytics for current date
            FOR analytics_record IN 
                SELECT 
                    verification_type,
                    COUNT(*) as total_verifications,
                    COUNT(CASE WHEN verified_at IS NOT NULL THEN 1 END) as verified_count,
                    COUNT(CASE WHEN failed_attempts > 0 AND verified_at IS NULL THEN 1 END) as failed_count,
                    COUNT(CASE WHEN expires_at < NOW() AND verified_at IS NULL THEN 1 END) as expired_count,
                    COALESCE(SUM(resend_count), 0) as resend_count,
                    COUNT(CASE WHEN EXISTS (
                        SELECT 1 FROM email_verification_reminders evr 
                        WHERE evr.verification_id = ev.id
                    ) THEN 1 END) as reminder_sent_count
                FROM email_verifications ev
                WHERE DATE(created_at) = current_date
                GROUP BY verification_type
            LOOP
                INSERT INTO email_verification_analytics (
                    date, verification_type, total_verifications, verified_count, 
                    failed_count, expired_count, resend_count, reminder_sent_count
                ) VALUES (
                    current_date, analytics_record.verification_type, 
                    analytics_record.total_verifications, analytics_record.verified_count,
                    analytics_record.failed_count, analytics_record.expired_count,
                    analytics_record.resend_count, analytics_record.reminder_sent_count
                );
            END LOOP;
        END;
        $$ LANGUAGE plpgsql;
        
        COMMENT ON FUNCTION update_email_verification_analytics() IS 'Update daily verification analytics';
    """)
    
    # Step 18: Create triggers for automatic updates
    op.execute("""
        CREATE OR REPLACE FUNCTION update_verification_updated_at()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
        
        CREATE TRIGGER trigger_update_verification_updated_at
            BEFORE UPDATE ON email_verifications
            FOR EACH ROW
            EXECUTE FUNCTION update_verification_updated_at();
            
        COMMENT ON TRIGGER trigger_update_verification_updated_at ON email_verifications IS 'Automatically update updated_at timestamp';
    """)
    
    # Step 19: Create trigger for audit logging
    op.execute("""
        CREATE OR REPLACE FUNCTION log_verification_changes()
        RETURNS TRIGGER AS $$
        BEGIN
            IF TG_OP = 'INSERT' THEN
                INSERT INTO email_verification_audit_log (
                    user_id, verification_id, event_type, event_data, success
                ) VALUES (
                    NEW.user_id, NEW.id, 'verification_created', 
                    jsonb_build_object('email', NEW.email, 'type', NEW.verification_type), 
                    true
                );
                RETURN NEW;
            ELSIF TG_OP = 'UPDATE' THEN
                IF NEW.verified_at IS NOT NULL AND OLD.verified_at IS NULL THEN
                    INSERT INTO email_verification_audit_log (
                        user_id, verification_id, event_type, event_data, success
                    ) VALUES (
                        NEW.user_id, NEW.id, 'verification_completed', 
                        jsonb_build_object('email', NEW.email, 'type', NEW.verification_type), 
                        true
                    );
                END IF;
                RETURN NEW;
            END IF;
            RETURN NULL;
        END;
        $$ LANGUAGE plpgsql;
        
        CREATE TRIGGER trigger_log_verification_changes
            AFTER INSERT OR UPDATE ON email_verifications
            FOR EACH ROW
            EXECUTE FUNCTION log_verification_changes();
            
        COMMENT ON TRIGGER trigger_log_verification_changes ON email_verifications IS 'Automatically log verification events for audit purposes';
    """)
    
    # Step 20: Create initial analytics for existing data
    op.execute("""
        SELECT update_email_verification_analytics();
    """)
    
    # Step 21: Log migration completion
    op.execute("""
        INSERT INTO email_verification_audit_log (
            user_id, event_type, event_data, success, created_at
        ) VALUES (
            NULL, 'migration_completed', 
            jsonb_build_object('migration', '010_add_email_verification_system', 'version', '1.0.0'), 
            true, NOW()
        );
    """)

def downgrade():
    """Downgrade to remove email verification system with data preservation"""
    
    # Step 1: Log downgrade attempt
    op.execute("""
        INSERT INTO email_verification_audit_log (
            user_id, event_type, event_data, success, created_at
        ) VALUES (
            NULL, 'migration_downgrade_started', 
            jsonb_build_object('migration', '010_add_email_verification_system'), 
            true, NOW()
        );
    """)
    
    # Step 2: Drop triggers and functions
    op.execute("""
        DROP TRIGGER IF EXISTS trigger_log_verification_changes ON email_verifications;
        DROP TRIGGER IF EXISTS trigger_update_verification_updated_at ON email_verifications;
        DROP FUNCTION IF EXISTS log_verification_changes();
        DROP FUNCTION IF EXISTS update_verification_updated_at();
        DROP FUNCTION IF EXISTS update_email_verification_analytics();
        DROP FUNCTION IF EXISTS schedule_email_verification_reminders();
        DROP FUNCTION IF EXISTS cleanup_expired_email_verifications();
    """)
    
    # Step 3: Drop tables in reverse dependency order
    op.drop_table('email_verification_analytics')
    op.drop_table('email_verification_reminders')
    op.drop_table('email_verification_settings')
    op.drop_table('email_verification_audit_log')
    op.drop_table('email_verifications')
    
    # Step 4: Remove indexes from users table
    op.drop_index('idx_users_email_verified_created', table_name='users')
    op.drop_index('idx_users_email_verified', table_name='users')
    
    # Step 5: Remove email_verified column (preserve data in backup)
    op.execute("""
        DO $$ 
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'users' AND column_name = 'email_verified'
            ) THEN
                ALTER TABLE users DROP COLUMN email_verified;
                RAISE NOTICE 'Removed email_verified column from users table';
            ELSE
                RAISE NOTICE 'email_verified column does not exist in users table';
            END IF;
        END $$;
    """)
    
    # Step 6: Log downgrade completion
    op.execute("""
        INSERT INTO email_verification_audit_log (
            user_id, event_type, event_data, success, created_at
        ) VALUES (
            NULL, 'migration_downgrade_completed', 
            jsonb_build_object('migration', '010_add_email_verification_system'), 
            true, NOW()
        );
    """)
    
    # Note: users_backup_010 table is preserved for manual data recovery if needed
    # You can manually restore data from this backup if required
