"""
Migration: Add Comprehensive Email Verification System
Description: Implements secure email verification with comprehensive security features
Date: 2025-01-XX
Author: MINGUS Development Team
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '010_add_email_verification_system'
down_revision = '009_add_two_factor_auth'
branch_labels = None
depends_on = None

def upgrade():
    """Upgrade to add email verification system"""
    
    # Create email_verifications table
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
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('user_id', 'verification_type', name='idx_email_verification_user_type'),
        sa.UniqueConstraint('verification_token_hash', name='idx_email_verification_token_hash')
    )
    
    # Create indexes for performance and security
    op.create_index('idx_email_verifications_user_id', 'email_verifications', ['user_id'])
    op.create_index('idx_email_verifications_email', 'email_verifications', ['email'])
    op.create_index('idx_email_verifications_expires_at', 'email_verifications', ['expires_at'])
    op.create_index('idx_email_verifications_verified_at', 'email_verifications', ['verified_at'])
    op.create_index('idx_email_verifications_expires_created', 'email_verifications', ['expires_at', 'created_at'])
    op.create_index('idx_email_verifications_rate_limit', 'email_verifications', ['user_id', 'failed_attempts', 'locked_until'])
    
    # Add email_verified column to users table if it doesn't exist
    op.execute("""
        DO $$ 
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'users' AND column_name = 'email_verified'
            ) THEN
                ALTER TABLE users ADD COLUMN email_verified BOOLEAN DEFAULT FALSE;
            END IF;
        END $$;
    """)
    
    # Create index on email_verified column
    op.create_index('idx_users_email_verified', 'users', ['email_verified'])
    
    # Create email_verification_audit_log table for comprehensive logging
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
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['verification_id'], ['email_verifications.id'], ondelete='SET NULL')
    )
    
    # Create indexes for audit log
    op.create_index('idx_email_verification_audit_user_id', 'email_verification_audit_log', ['user_id'])
    op.create_index('idx_email_verification_audit_event_type', 'email_verification_audit_log', ['event_type'])
    op.create_index('idx_email_verification_audit_success', 'email_verification_audit_log', ['success'])
    op.create_index('idx_email_verification_audit_created_at', 'email_verification_audit_log', ['created_at'])
    op.create_index('idx_email_verification_audit_ip_address', 'email_verification_audit_log', ['ip_address'])
    
    # Create email_verification_settings table for configurable settings
    op.create_table('email_verification_settings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('setting_key', sa.String(length=100), nullable=False),
        sa.Column('setting_value', sa.Text(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('setting_key')
    )
    
    # Insert default settings
    op.execute("""
        INSERT INTO email_verification_settings (setting_key, setting_value, description) VALUES
        ('verification_expiry_hours', '24', 'Hours until verification token expires'),
        ('max_resend_attempts', '5', 'Maximum number of resend attempts per day'),
        ('resend_cooldown_hours', '1', 'Hours between resend attempts'),
        ('max_failed_attempts', '5', 'Maximum failed verification attempts before lockout'),
        ('lockout_duration_hours', '1', 'Hours of lockout after max failed attempts'),
        ('reminder_schedule_days', '3,7,14', 'Days after signup to send reminders'),
        ('enable_rate_limiting', 'true', 'Enable rate limiting on verification endpoints'),
        ('enable_audit_logging', 'true', 'Enable comprehensive audit logging')
    """)
    
    # Create email_verification_reminders table for tracking reminder sends
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
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['verification_id'], ['email_verifications.id'], ondelete='CASCADE')
    )
    
    # Create indexes for reminders
    op.create_index('idx_email_verification_reminders_user_id', 'email_verification_reminders', ['user_id'])
    op.create_index('idx_email_verification_reminders_verification_id', 'email_verification_reminders', ['verification_id'])
    op.create_index('idx_email_verification_reminders_type', 'email_verification_reminders', ['reminder_type'])
    op.create_index('idx_email_verification_reminders_sent_at', 'email_verification_reminders', ['sent_at'])
    
    # Create email_verification_analytics table for metrics
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
        sa.UniqueConstraint('date', 'verification_type')
    )
    
    # Create indexes for analytics
    op.create_index('idx_email_verification_analytics_date', 'email_verification_analytics', ['date'])
    op.create_index('idx_email_verification_analytics_type', 'email_verification_analytics', ['verification_type'])
    
    # Add constraints and checks
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
    """)
    
    # Create function for automatic cleanup of expired verifications
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
    """)
    
    # Create function for automatic reminder scheduling
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
    """)
    
    # Create function for verification analytics
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
                    SUM(resend_count) as resend_count,
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
    """)
    
    # Create triggers for automatic updates
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
    """)
    
    # Create trigger for automatic audit logging
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
    """)

def downgrade():
    """Downgrade to remove email verification system"""
    
    # Drop triggers and functions
    op.execute("""
        DROP TRIGGER IF EXISTS trigger_log_verification_changes ON email_verifications;
        DROP TRIGGER IF EXISTS trigger_update_verification_updated_at ON email_verifications;
        DROP FUNCTION IF EXISTS log_verification_changes();
        DROP FUNCTION IF EXISTS update_verification_updated_at();
        DROP FUNCTION IF EXISTS update_email_verification_analytics();
        DROP FUNCTION IF EXISTS schedule_email_verification_reminders();
        DROP FUNCTION IF EXISTS cleanup_expired_email_verifications();
    """)
    
    # Drop tables
    op.drop_table('email_verification_analytics')
    op.drop_table('email_verification_reminders')
    op.drop_table('email_verification_settings')
    op.drop_table('email_verification_audit_log')
    op.drop_table('email_verifications')
    
    # Remove email_verified column from users table
    op.execute("""
        ALTER TABLE users DROP COLUMN IF EXISTS email_verified;
    """)
    
    # Drop indexes
    op.drop_index('idx_users_email_verified', table_name='users')
