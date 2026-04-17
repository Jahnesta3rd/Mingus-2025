"""Migration: Add bug_reports table for in-app bug reporting."""
import logging
try:
    from alembic import op
    import sqlalchemy as sa
    HAS_ALEMBIC = True
except ImportError:
    HAS_ALEMBIC = False
logger = logging.getLogger(__name__)
def upgrade():
    if not HAS_ALEMBIC:
        logger.warning("alembic not installed; run SQL manually if needed")
        return
    op.create_table(
        'bug_reports',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('ticket_number', sa.String(12), unique=True, nullable=False, index=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_email', sa.String(255), nullable=False),
        sa.Column('user_name', sa.String(100), nullable=False),
        sa.Column('user_tier', sa.String(20), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('current_route', sa.String(255), nullable=True),
        sa.Column('browser_info', sa.String(255), nullable=True),
        sa.Column('balance_status', sa.String(20), nullable=True),
        sa.Column('last_feature', sa.String(100), nullable=True),
        sa.Column('onboarding_complete', sa.Boolean(), default=False),
        sa.Column('account_age_days', sa.Integer(), nullable=True),
        sa.Column('is_beta', sa.Boolean(), default=False),
        sa.Column('status', sa.String(20), nullable=False, server_default='open'),
        sa.Column('admin_notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text("(now() at time zone 'utc')"), index=True),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text("(now() at time zone 'utc')")),
        sa.Column('resolved_at', sa.DateTime(), nullable=True),
    )
def downgrade():
    if not HAS_ALEMBIC:
        return
    op.drop_table('bug_reports')
