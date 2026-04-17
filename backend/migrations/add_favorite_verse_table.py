"""Migration: Add favorite_verse table for Faith Card favorites."""
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
        'favorite_verse',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('verse_reference', sa.String(100), nullable=False),
        sa.Column('verse_text', sa.Text(), nullable=False),
        sa.Column('bridge_sentence', sa.Text(), nullable=False),
        sa.Column('balance_status_at_save', sa.String(20), nullable=True),
        sa.Column('goal_at_save', sa.String(255), nullable=True),
        sa.Column('saved_at', sa.DateTime(), nullable=False, server_default=sa.text("(now() at time zone 'utc')")),
    )
    op.create_unique_constraint('uq_favorite_verse_user_ref', 'favorite_verse', ['user_id', 'verse_reference'])
def downgrade():
    if not HAS_ALEMBIC:
        return
    op.drop_constraint('uq_favorite_verse_user_ref', 'favorite_verse', type_='unique')
    op.drop_table('favorite_verse')
