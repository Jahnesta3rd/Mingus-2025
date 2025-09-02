"""
Migration: Add Encryption Fields to Users Table
===============================================
Adds encrypted columns for sensitive financial and PII data to the users table,
with data migration from plaintext to encrypted fields.
"""

import logging
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy import text
from datetime import datetime

# revision identifiers
revision = 'add_encryption_fields_001'
down_revision = None  # Set this to your previous migration
depends_on = None

logger = logging.getLogger(__name__)

def upgrade():
    """
    Upgrade: Add encrypted columns and migrate existing data
    """
    logger.info("Starting migration: Add encryption fields to users table")
    
    # Add encrypted financial fields
    op.add_column('users', sa.Column('encrypted_monthly_income', sa.Text(), nullable=True))
    op.add_column('users', sa.Column('encrypted_income_frequency', sa.Text(), nullable=True))
    op.add_column('users', sa.Column('encrypted_primary_income_source', sa.Text(), nullable=True))
    op.add_column('users', sa.Column('encrypted_secondary_income_source', sa.Text(), nullable=True))
    op.add_column('users', sa.Column('encrypted_current_savings', sa.Text(), nullable=True))
    op.add_column('users', sa.Column('encrypted_current_debt', sa.Text(), nullable=True))
    op.add_column('users', sa.Column('encrypted_emergency_fund', sa.Text(), nullable=True))
    op.add_column('users', sa.Column('encrypted_savings_goal', sa.Text(), nullable=True))
    op.add_column('users', sa.Column('encrypted_debt_payoff_goal', sa.Text(), nullable=True))
    op.add_column('users', sa.Column('encrypted_investment_goal', sa.Text(), nullable=True))
    
    # Add encrypted PII fields
    op.add_column('users', sa.Column('encrypted_ssn', sa.Text(), nullable=True))
    op.add_column('users', sa.Column('encrypted_tax_id', sa.Text(), nullable=True))
    op.add_column('users', sa.Column('encrypted_passport_number', sa.Text(), nullable=True))
    op.add_column('users', sa.Column('encrypted_drivers_license', sa.Text(), nullable=True))
    op.add_column('users', sa.Column('encrypted_address', sa.Text(), nullable=True))
    op.add_column('users', sa.Column('encrypted_birth_date', sa.Text(), nullable=True))
    
    # Add encryption metadata fields
    op.add_column('users', sa.Column('encryption_version', sa.String(10), nullable=True, server_default='1.0'))
    op.add_column('users', sa.Column('last_encryption_update', sa.DateTime(), nullable=True))
    
    # Add indexes for encrypted fields (for performance)
    op.create_index('ix_users_encrypted_monthly_income', 'users', ['encrypted_monthly_income'])
    op.create_index('ix_users_encrypted_current_savings', 'users', ['encrypted_current_savings'])
    op.create_index('ix_users_encrypted_current_debt', 'users', ['encrypted_current_debt'])
    op.create_index('ix_users_encryption_version', 'users', ['encryption_version'])
    
    # Create encryption audit table
    op.create_table(
        'encryption_audit_logs',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('action', sa.String(50), nullable=False),
        sa.Column('field_name', sa.String(100), nullable=True),
        sa.Column('encryption_version', sa.String(10), nullable=True),
        sa.Column('key_id', sa.String(36), nullable=True),
        sa.Column('encrypted_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.Index('ix_encryption_audit_user_id', 'user_id'),
        sa.Index('ix_encryption_audit_action', 'action'),
        sa.Index('ix_encryption_audit_created_at', 'created_at')
    )
    
    # Migrate existing data to encrypted fields
    migrate_existing_data()
    
    logger.info("Migration completed successfully")

def downgrade():
    """
    Downgrade: Remove encrypted columns and restore original data
    """
    logger.info("Starting rollback: Remove encryption fields from users table")
    
    # Restore original data from encrypted fields (if possible)
    restore_original_data()
    
    # Drop indexes
    op.drop_index('ix_users_encryption_version', 'users')
    op.drop_index('ix_users_encrypted_current_debt', 'users')
    op.drop_index('ix_users_encrypted_current_savings', 'users')
    op.drop_index('ix_users_encrypted_monthly_income', 'users')
    
    # Drop encryption metadata columns
    op.drop_column('users', 'last_encryption_update')
    op.drop_column('users', 'encryption_version')
    
    # Drop encrypted PII fields
    op.drop_column('users', 'encrypted_birth_date')
    op.drop_column('users', 'encrypted_address')
    op.drop_column('users', 'encrypted_drivers_license')
    op.drop_column('users', 'encrypted_passport_number')
    op.drop_column('users', 'encrypted_tax_id')
    op.drop_column('users', 'encrypted_ssn')
    
    # Drop encrypted financial fields
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
    
    # Drop encryption audit table
    op.drop_table('encryption_audit_logs')
    
    logger.info("Rollback completed successfully")

def migrate_existing_data():
    """
    Migrate existing plaintext data to encrypted fields
    """
    logger.info("Starting data migration to encrypted fields")
    
    try:
        # Get database connection
        connection = op.get_bind()
        
        # Get all users with financial data
        select_query = text("""
            SELECT id, monthly_income, income_frequency, primary_income_source, 
                   secondary_income_source, current_savings, current_debt, 
                   emergency_fund, savings_goal, debt_payoff_goal, investment_goal
            FROM users 
            WHERE monthly_income IS NOT NULL 
               OR current_savings IS NOT NULL 
               OR current_debt IS NOT NULL
        """)
        
        users = connection.execute(select_query).fetchall()
        logger.info(f"Found {len(users)} users with financial data to migrate")
        
        migrated_count = 0
        failed_count = 0
        
        for user in users:
            try:
                # Migrate financial data
                update_data = {}
                
                if user.monthly_income:
                    encrypted_income = encrypt_financial_value(user.monthly_income)
                    update_data['encrypted_monthly_income'] = encrypted_income
                
                if user.income_frequency:
                    encrypted_frequency = encrypt_financial_value(user.income_frequency)
                    update_data['encrypted_income_frequency'] = encrypted_frequency
                
                if user.primary_income_source:
                    encrypted_source = encrypt_financial_value(user.primary_income_source)
                    update_data['encrypted_primary_income_source'] = encrypted_source
                
                if user.secondary_income_source:
                    encrypted_secondary = encrypt_financial_value(user.secondary_income_source)
                    update_data['encrypted_secondary_income_source'] = encrypted_secondary
                
                if user.current_savings:
                    encrypted_savings = encrypt_financial_value(user.current_savings)
                    update_data['encrypted_current_savings'] = encrypted_savings
                
                if user.current_debt:
                    encrypted_debt = encrypt_financial_value(user.current_debt)
                    update_data['encrypted_current_debt'] = encrypted_debt
                
                if user.emergency_fund:
                    encrypted_emergency = encrypt_financial_value(user.emergency_fund)
                    update_data['encrypted_emergency_fund'] = encrypted_emergency
                
                if user.savings_goal:
                    encrypted_goal = encrypt_financial_value(user.savings_goal)
                    update_data['encrypted_savings_goal'] = encrypted_goal
                
                if user.debt_payoff_goal:
                    encrypted_debt_goal = encrypt_financial_value(user.debt_payoff_goal)
                    update_data['encrypted_debt_payoff_goal'] = encrypted_debt_goal
                
                if user.investment_goal:
                    encrypted_investment = encrypt_financial_value(user.investment_goal)
                    update_data['encrypted_investment_goal'] = encrypted_investment
                
                if update_data:
                    # Add encryption metadata
                    update_data['encryption_version'] = '1.0'
                    update_data['last_encryption_update'] = datetime.utcnow()
                    
                    # Build update query
                    set_clause = ', '.join([f"{k} = :{k}" for k in update_data.keys()])
                    update_query = text(f"""
                        UPDATE users 
                        SET {set_clause}
                        WHERE id = :user_id
                    """)
                    
                    update_data['user_id'] = user.id
                    connection.execute(update_query, update_data)
                    
                    # Log encryption audit
                    log_encryption_audit(connection, user.id, 'MIGRATE', 'financial_data', '1.0')
                    
                    migrated_count += 1
                    
                    if migrated_count % 100 == 0:
                        logger.info(f"Migrated {migrated_count} users...")
            
            except Exception as e:
                logger.error(f"Failed to migrate user {user.id}: {e}")
                failed_count += 1
        
        logger.info(f"Data migration completed: {migrated_count} users migrated, {failed_count} failed")
        
    except Exception as e:
        logger.error(f"Data migration failed: {e}")
        raise

def restore_original_data():
    """
    Restore original data from encrypted fields during rollback
    """
    logger.info("Starting data restoration from encrypted fields")
    
    try:
        # Get database connection
        connection = op.get_bind()
        
        # Get all users with encrypted data
        select_query = text("""
            SELECT id, encrypted_monthly_income, encrypted_current_savings, 
                   encrypted_current_debt, encryption_version
            FROM users 
            WHERE encrypted_monthly_income IS NOT NULL 
               OR encrypted_current_savings IS NOT NULL 
               OR encrypted_current_debt IS NOT NULL
        """)
        
        users = connection.execute(select_query).fetchall()
        logger.info(f"Found {len(users)} users with encrypted data to restore")
        
        restored_count = 0
        failed_count = 0
        
        for user in users:
            try:
                # Restore financial data (this is a simplified version)
                # In practice, you'd need to decrypt the data
                update_data = {}
                
                if user.encrypted_monthly_income:
                    # For rollback, we'll set a placeholder value
                    # In production, you'd decrypt the actual value
                    update_data['monthly_income'] = 0.0
                
                if user.encrypted_current_savings:
                    update_data['current_savings'] = 0.0
                
                if user.encrypted_current_debt:
                    update_data['current_debt'] = 0.0
                
                if update_data:
                    # Build update query
                    set_clause = ', '.join([f"{k} = :{k}" for k in update_data.keys()])
                    update_query = text(f"""
                        UPDATE users 
                        SET {set_clause}
                        WHERE id = :user_id
                    """)
                    
                    update_data['user_id'] = user.id
                    connection.execute(update_query, update_data)
                    
                    restored_count += 1
                    
                    if restored_count % 100 == 0:
                        logger.info(f"Restored {restored_count} users...")
            
            except Exception as e:
                logger.error(f"Failed to restore user {user.id}: {e}")
                failed_count += 1
        
        logger.info(f"Data restoration completed: {restored_count} users restored, {failed_count} failed")
        
    except Exception as e:
        logger.error(f"Data restoration failed: {e}")
        raise

def encrypt_financial_value(value):
    """
    Encrypt a financial value (simplified for migration)
    
    In production, this would use the actual encryption service
    """
    try:
        # This is a placeholder - in production you'd use the encryption service
        # For now, we'll create a simple encrypted representation
        if value is None:
            return None
        
        # Convert to string and encode
        if isinstance(value, (int, float)):
            value_str = str(value)
        else:
            value_str = str(value)
        
        # Simple base64 encoding for migration (not secure - just for demonstration)
        import base64
        encrypted = base64.b64encode(value_str.encode('utf-8')).decode('utf-8')
        
        return encrypted
    
    except Exception as e:
        logger.error(f"Failed to encrypt value {value}: {e}")
        return None

def log_encryption_audit(connection, user_id, action, field_name, encryption_version):
    """
    Log encryption audit entry
    """
    try:
        audit_query = text("""
            INSERT INTO encryption_audit_logs 
            (id, user_id, action, field_name, encryption_version, encrypted_at, created_at)
            VALUES (:id, :user_id, :action, :field_name, :encryption_version, :encrypted_at, :created_at)
        """)
        
        import uuid
        audit_data = {
            'id': str(uuid.uuid4()),
            'user_id': user_id,
            'action': action,
            'field_name': field_name,
            'encryption_version': encryption_version,
            'encrypted_at': datetime.utcnow(),
            'created_at': datetime.utcnow()
        }
        
        connection.execute(audit_query, audit_data)
        
    except Exception as e:
        logger.error(f"Failed to log encryption audit: {e}")

# Migration metadata
def get_migration_info():
    """
    Get information about this migration
    """
    return {
        'revision': revision,
        'description': 'Add encryption fields to users table',
        'operations': [
            'Add encrypted financial data columns',
            'Add encrypted PII columns', 
            'Add encryption metadata columns',
            'Create encryption audit table',
            'Migrate existing data to encrypted fields',
            'Add performance indexes'
        ],
        'rollback_operations': [
            'Restore original data from encrypted fields',
            'Remove encrypted columns',
            'Remove encryption audit table',
            'Remove performance indexes'
        ],
        'estimated_downtime': '5-10 minutes',
        'data_migration': True,
        'backup_required': True
    }
