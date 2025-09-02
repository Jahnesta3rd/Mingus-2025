"""test_security_migration

Revision ID: 613a6fe4fcf1
Revises: cdd6e5c35e83
Create Date: 2025-01-27 15:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
import uuid

# revision identifiers, used by Alembic.
revision = '613a6fe4fcf1'
down_revision = 'cdd6e5c35e83'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create a simple test audit table."""
    
    # Create a basic audit events table for testing
    op.create_table(
        'test_audit_events',
        sa.Column('id', sa.String(36), primary_key=True, default=lambda: str(uuid.uuid4())),
        sa.Column('event_timestamp', sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column('event_type', sa.String(100), nullable=False, index=True),
        sa.Column('user_id', sa.String(36), nullable=True, index=True),
        sa.Column('ip_address', sa.String(45), nullable=False, index=True),
        sa.Column('success', sa.Boolean, nullable=False, default=True),
        sa.Column('details', sa.JSON, nullable=True),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.func.now())
    )
    
    # Create a simple index
    op.create_index('idx_test_audit_events_user_timestamp', 'test_audit_events', ['user_id', 'event_timestamp'])


def downgrade() -> None:
    """Remove the test audit table."""
    op.drop_index('idx_test_audit_events_user_timestamp', 'test_audit_events')
    op.drop_table('test_audit_events') 