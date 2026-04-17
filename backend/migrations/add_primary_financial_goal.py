"""Migration: Add primary_financial_goal column to users table."""
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
    op.add_column('users', sa.Column('primary_financial_goal', sa.String(255), nullable=True))
def downgrade():
    if not HAS_ALEMBIC:
        return
    op.drop_column('users', 'primary_financial_goal')
