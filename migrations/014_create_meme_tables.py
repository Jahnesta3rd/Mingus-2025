"""
Migration: Create Meme Splash Page Tables
Description: Creates tables for the meme splash page feature
Date: 2025-01-27
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision = '014_create_meme_tables'
down_revision = '013_create_article_library_tables_complete'
branch_labels = None
depends_on = None


def upgrade():
    """Create meme splash page tables"""
    
    # Create memes table
    op.create_table('memes',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('image_url', sa.String(500), nullable=False),
        sa.Column('image_file_path', sa.String(500)),
        sa.Column('category', sa.String(20), nullable=False),
        sa.Column('caption_text', sa.Text, nullable=False),
        sa.Column('alt_text', sa.Text, nullable=False),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('view_count', sa.Integer, default=0),
        sa.Column('like_count', sa.Integer, default=0),
        sa.Column('share_count', sa.Integer, default=0),
        sa.Column('engagement_score', sa.Float, default=0.0),
        sa.Column('priority', sa.Integer, default=5),
        sa.Column('tags', sa.Text),
        sa.Column('source_attribution', sa.String(200)),
        sa.Column('admin_notes', sa.Text),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now())
    )
    
    # Create user_meme_history table
    op.create_table('user_meme_history',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.Integer, nullable=False),
        sa.Column('meme_id', sa.String(36), nullable=False),
        sa.Column('viewed_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column('time_spent_seconds', sa.Integer, default=0),
        sa.Column('interaction_type', sa.String(20), default='view'),
        sa.Column('session_id', sa.String(100)),
        sa.Column('source_page', sa.String(200)),
        sa.Column('device_type', sa.String(50)),
        sa.Column('user_agent', sa.Text),
        sa.Column('ip_address', sa.String(45)),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['meme_id'], ['memes.id'], ondelete='CASCADE')
    )
    
    # Create user_meme_preferences table
    op.create_table('user_meme_preferences',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.Integer, nullable=False, unique=True),
        sa.Column('memes_enabled', sa.Boolean, default=True),
        sa.Column('preferred_categories', sa.Text),
        sa.Column('frequency_setting', sa.String(20), default='daily'),
        sa.Column('custom_frequency_days', sa.Integer, default=1),
        sa.Column('last_meme_shown_at', sa.DateTime),
        sa.Column('last_meme_shown_id', sa.String(36)),
        sa.Column('opt_out_reason', sa.Text),
        sa.Column('opt_out_date', sa.DateTime),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['last_meme_shown_id'], ['memes.id'], ondelete='SET NULL')
    )
    
    # Create indexes
    op.create_index('idx_memes_category', 'memes', ['category'])
    op.create_index('idx_memes_active', 'memes', ['is_active'])
    op.create_index('idx_memes_priority', 'memes', ['priority'])
    op.create_index('idx_memes_engagement', 'memes', ['engagement_score'])
    op.create_index('idx_memes_created_at', 'memes', ['created_at'])
    op.create_index('idx_memes_category_active', 'memes', ['category', 'is_active'])
    
    op.create_index('idx_user_meme_history_user_id', 'user_meme_history', ['user_id'])
    op.create_index('idx_user_meme_history_meme_id', 'user_meme_history', ['meme_id'])
    op.create_index('idx_user_meme_history_viewed_at', 'user_meme_history', ['viewed_at'])
    op.create_index('idx_user_meme_history_user_viewed', 'user_meme_history', ['user_id', 'viewed_at'])
    op.create_index('idx_user_meme_history_interaction', 'user_meme_history', ['interaction_type'])
    
    op.create_index('idx_user_meme_preferences_enabled', 'user_meme_preferences', ['memes_enabled'])
    op.create_index('idx_user_meme_preferences_frequency', 'user_meme_preferences', ['frequency_setting'])
    op.create_index('idx_user_meme_preferences_last_shown', 'user_meme_preferences', ['last_meme_shown_at'])
    
    # Create unique constraint for user_meme_history
    op.create_unique_constraint('uq_user_meme_history_user_meme_viewed', 'user_meme_history', ['user_id', 'meme_id', 'viewed_at'])


def downgrade():
    """Drop meme splash page tables"""
    
    # Drop indexes
    op.drop_index('idx_user_meme_preferences_last_shown', 'user_meme_preferences')
    op.drop_index('idx_user_meme_preferences_frequency', 'user_meme_preferences')
    op.drop_index('idx_user_meme_preferences_enabled', 'user_meme_preferences')
    
    op.drop_index('idx_user_meme_history_interaction', 'user_meme_history')
    op.drop_index('idx_user_meme_history_user_viewed', 'user_meme_history')
    op.drop_index('idx_user_meme_history_viewed_at', 'user_meme_history')
    op.drop_index('idx_user_meme_history_meme_id', 'user_meme_history')
    op.drop_index('idx_user_meme_history_user_id', 'user_meme_history')
    
    op.drop_index('idx_memes_category_active', 'memes')
    op.drop_index('idx_memes_created_at', 'memes')
    op.drop_index('idx_memes_engagement', 'memes')
    op.drop_index('idx_memes_priority', 'memes')
    op.drop_index('idx_memes_active', 'memes')
    op.drop_index('idx_memes_category', 'memes')
    
    # Drop unique constraint
    op.drop_constraint('uq_user_meme_history_user_meme_viewed', 'user_meme_history', type_='unique')
    
    # Drop tables
    op.drop_table('user_meme_preferences')
    op.drop_table('user_meme_history')
    op.drop_table('memes')
