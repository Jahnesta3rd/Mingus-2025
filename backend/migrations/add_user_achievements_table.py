#!/usr/bin/env python3
"""
Migration: Add user_achievements table for wellness check-in gamification.

CREATE TABLE user_achievements (
  id UUID PRIMARY KEY,
  user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  achievement_key VARCHAR(50) NOT NULL,
  unlocked_at TIMESTAMP NOT NULL DEFAULT (now() at time zone 'utc'),
  UNIQUE(user_id, achievement_key)
);
"""

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
        'user_achievements',
        sa.Column('id', sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('achievement_key', sa.String(50), nullable=False, index=True),
        sa.Column('unlocked_at', sa.DateTime(), nullable=False, server_default=sa.text("(now() at time zone 'utc')")),
    )
    op.create_index('idx_user_achievements_user_id', 'user_achievements', ['user_id'], unique=False)
    op.create_index('idx_user_achievements_key', 'user_achievements', ['achievement_key'], unique=False)
    op.create_unique_constraint('uq_user_achievements_user_key', 'user_achievements', ['user_id', 'achievement_key'])


def downgrade():
    if not HAS_ALEMBIC:
        return
    op.drop_constraint('uq_user_achievements_user_key', 'user_achievements', type_='unique')
    op.drop_index('idx_user_achievements_key', table_name='user_achievements')
    op.drop_index('idx_user_achievements_user_id', table_name='user_achievements')
    op.drop_table('user_achievements')
