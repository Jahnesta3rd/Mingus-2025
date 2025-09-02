"""
Migration: Add Two-Factor Authentication tables
Adds comprehensive 2FA support including TOTP, backup codes, and audit logging
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '009_add_two_factor_auth'
down_revision = '008_add_smart_resend_analytics'
branch_labels = None
depends_on = None

def upgrade():
    """Create 2FA tables"""
    
    # Create two_factor_auth table
    op.create_table('two_factor_auth',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('encrypted_totp_secret', sa.Text(), nullable=False),
        sa.Column('totp_algorithm', sa.String(length=10), nullable=True),
        sa.Column('totp_digits', sa.Integer(), nullable=True),
        sa.Column('totp_period', sa.Integer(), nullable=True),
        sa.Column('is_enabled', sa.Boolean(), nullable=True),
        sa.Column('is_verified', sa.Boolean(), nullable=True),
        sa.Column('setup_completed_at', sa.DateTime(), nullable=True),
        sa.Column('sms_fallback_enabled', sa.Boolean(), nullable=True),
        sa.Column('encrypted_sms_secret', sa.Text(), nullable=True),
        sa.Column('max_attempts', sa.Integer(), nullable=True),
        sa.Column('lockout_until', sa.DateTime(), nullable=True),
        sa.Column('last_used_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for two_factor_auth
    op.create_index('idx_two_factor_user_id', 'two_factor_auth', ['user_id'])
    op.create_index('idx_two_factor_enabled', 'two_factor_auth', ['is_enabled'])
    op.create_index('idx_two_factor_lockout', 'two_factor_auth', ['lockout_until'])
    
    # Create two_factor_backup_codes table
    op.create_table('two_factor_backup_codes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('two_factor_auth_id', sa.Integer(), nullable=False),
        sa.Column('encrypted_code_hash', sa.Text(), nullable=False),
        sa.Column('is_used', sa.Boolean(), nullable=True),
        sa.Column('used_at', sa.DateTime(), nullable=True),
        sa.Column('used_ip_address', sa.String(length=45), nullable=True),
        sa.Column('used_user_agent', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['two_factor_auth_id'], ['two_factor_auth.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for backup codes
    op.create_index('idx_backup_code_two_factor_id', 'two_factor_backup_codes', ['two_factor_auth_id'])
    op.create_index('idx_backup_code_used', 'two_factor_backup_codes', ['is_used'])
    
    # Create two_factor_verification_attempts table
    op.create_table('two_factor_verification_attempts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('two_factor_auth_id', sa.Integer(), nullable=False),
        sa.Column('attempt_type', sa.String(length=20), nullable=False),
        sa.Column('success', sa.Boolean(), nullable=False),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('country_code', sa.String(length=10), nullable=True),
        sa.Column('city', sa.String(length=100), nullable=True),
        sa.Column('timezone', sa.String(length=50), nullable=True),
        sa.Column('attempted_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['two_factor_auth_id'], ['two_factor_auth.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for verification attempts
    op.create_index('idx_verification_attempt_two_factor_id', 'two_factor_verification_attempts', ['two_factor_auth_id'])
    op.create_index('idx_verification_attempt_success', 'two_factor_verification_attempts', ['success'])
    op.create_index('idx_verification_attempt_type', 'two_factor_verification_attempts', ['attempt_type'])
    op.create_index('idx_verification_attempt_timestamp', 'two_factor_verification_attempts', ['attempted_at'])
    
    # Create two_factor_recovery_requests table
    op.create_table('two_factor_recovery_requests',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('recovery_method', sa.String(length=20), nullable=False),
        sa.Column('encrypted_recovery_code', sa.Text(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=True),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('approved_by', sa.Integer(), nullable=True),
        sa.Column('approved_at', sa.DateTime(), nullable=True),
        sa.Column('rejection_reason', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['approved_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for recovery requests
    op.create_index('idx_recovery_request_user_id', 'two_factor_recovery_requests', ['user_id'])
    op.create_index('idx_recovery_request_status', 'two_factor_recovery_requests', ['status'])
    op.create_index('idx_recovery_request_expires', 'two_factor_recovery_requests', ['expires_at'])
    
    # Add unique constraint for user_id in two_factor_auth
    op.create_unique_constraint('uq_two_factor_auth_user_id', 'two_factor_auth', ['user_id'])
    
    # Set default values for existing columns
    op.execute("UPDATE two_factor_auth SET totp_algorithm = 'SHA1' WHERE totp_algorithm IS NULL")
    op.execute("UPDATE two_factor_auth SET totp_digits = 6 WHERE totp_digits IS NULL")
    op.execute("UPDATE two_factor_auth SET totp_period = 30 WHERE totp_period IS NULL")
    op.execute("UPDATE two_factor_auth SET is_enabled = false WHERE is_enabled IS NULL")
    op.execute("UPDATE two_factor_auth SET is_verified = false WHERE is_verified IS NULL")
    op.execute("UPDATE two_factor_auth SET sms_fallback_enabled = false WHERE sms_fallback_enabled IS NULL")
    op.execute("UPDATE two_factor_auth SET max_attempts = 5 WHERE max_attempts IS NULL")
    
    # Set default values for backup codes
    op.execute("UPDATE two_factor_backup_codes SET is_used = false WHERE is_used IS NULL")
    
    # Set default values for verification attempts
    op.execute("UPDATE two_factor_verification_attempts SET success = false WHERE success IS NULL")
    
    # Set default values for recovery requests
    op.execute("UPDATE two_factor_recovery_requests SET status = 'pending' WHERE status IS NULL")

def downgrade():
    """Remove 2FA tables"""
    
    # Drop indexes first
    op.drop_index('idx_recovery_request_expires', table_name='two_factor_recovery_requests')
    op.drop_index('idx_recovery_request_status', table_name='two_factor_recovery_requests')
    op.drop_index('idx_recovery_request_user_id', table_name='two_factor_recovery_requests')
    
    op.drop_index('idx_verification_attempt_timestamp', table_name='two_factor_verification_attempts')
    op.drop_index('idx_verification_attempt_type', table_name='two_factor_verification_attempts')
    op.drop_index('idx_verification_attempt_success', table_name='two_factor_verification_attempts')
    op.drop_index('idx_verification_attempt_two_factor_id', table_name='two_factor_verification_attempts')
    
    op.drop_index('idx_backup_code_used', table_name='two_factor_backup_codes')
    op.drop_index('idx_backup_code_two_factor_id', table_name='two_factor_backup_codes')
    
    op.drop_index('idx_two_factor_lockout', table_name='two_factor_auth')
    op.drop_index('idx_two_factor_enabled', table_name='two_factor_auth')
    op.drop_index('idx_two_factor_user_id', table_name='two_factor_auth')
    
    # Drop unique constraint
    op.drop_constraint('uq_two_factor_auth_user_id', 'two_factor_auth', type_='unique')
    
    # Drop tables in reverse order (due to foreign key constraints)
    op.drop_table('two_factor_recovery_requests')
    op.drop_table('two_factor_verification_attempts')
    op.drop_table('two_factor_backup_codes')
    op.drop_table('two_factor_auth')
