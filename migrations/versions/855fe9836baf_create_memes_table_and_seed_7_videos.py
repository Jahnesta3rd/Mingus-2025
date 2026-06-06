"""create memes table and seed 7 videos

Revision ID: 855fe9836baf
Revises: add_agreement_acceptances_clean
Create Date: 2026-04-26
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import table, column


revision = '855fe9836baf'
down_revision = 'add_agreement_acceptances_clean'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'memes',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('image_url', sa.Text, nullable=False),
        sa.Column('category', sa.String(64), nullable=True),
        sa.Column('caption', sa.Text, nullable=True),
        sa.Column('alt_text', sa.Text, nullable=True),
        sa.Column('is_active', sa.Integer, nullable=False, server_default=sa.text('1')),
        sa.Column('day_of_week', sa.Integer, nullable=True),
        sa.Column('media_type', sa.String(10), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP, nullable=False, server_default=sa.func.current_timestamp()),
        sa.Column('updated_at', sa.TIMESTAMP, nullable=False, server_default=sa.func.current_timestamp()),
    )
    op.create_index('ix_memes_image_url_unique', 'memes', ['image_url'], unique=True)
    op.create_index('ix_memes_active_day', 'memes', ['is_active', 'day_of_week'])

    memes_t = table(
        'memes',
        column('image_url', sa.Text),
        column('category', sa.String),
        column('caption', sa.Text),
        column('alt_text', sa.Text),
        column('is_active', sa.Integer),
        column('day_of_week', sa.Integer),
        column('media_type', sa.String),
    )

    op.bulk_insert(memes_t, [
        {
            'image_url': '/static/memes/sunday_faith/Faithful Quote.mp4',
            'category': 'faith',
            'caption': 'Sunday reset',
            'alt_text': 'Short video reflection on faith',
            'is_active': 1,
            'day_of_week': 6,
            'media_type': 'video',
        },
        {
            'image_url': '/static/memes/monday_work_life/Boss lying work.mp4',
            'category': 'work_life',
            'caption': 'When the boss says one thing and means another',
            'alt_text': 'Workplace humor about manager communication',
            'is_active': 1,
            'day_of_week': 0,
            'media_type': 'video',
        },
        {
            'image_url': '/static/memes/tuesday_friendships/IG Post #66.mp4',
            'category': 'friendships',
            'caption': 'Real ones check in',
            'alt_text': 'Short clip on the value of close friendships',
            'is_active': 1,
            'day_of_week': 1,
            'media_type': 'video',
        },
        {
            'image_url': '/static/memes/wednesday_children/IG Post #55 today drained.mp4',
            'category': 'children',
            'caption': 'Mid-week, kids edition',
            'alt_text': 'Parenting humor about a draining day',
            'is_active': 1,
            'day_of_week': 2,
            'media_type': 'video',
        },
        {
            'image_url': '/static/memes/thursday_relationships/Raq and brother relationships.mp4',
            'category': 'relationships',
            'caption': 'Sibling dynamics, captured',
            'alt_text': 'Short video about sibling relationships',
            'is_active': 1,
            'day_of_week': 3,
            'media_type': 'video',
        },
        {
            'image_url': '/static/memes/friday_going_out/going out scooter into wall .mp4',
            'category': 'going_out',
            'caption': 'Friday plans vs Friday reality',
            'alt_text': 'Comedic clip of a scooter accident',
            'is_active': 1,
            'day_of_week': 4,
            'media_type': 'video',
        },
        {
            'image_url': '/static/memes/saturday_mixed/mindset post.mp4',
            'category': 'general',
            'caption': 'Saturday mindset',
            'alt_text': 'Motivational mindset clip for the weekend',
            'is_active': 1,
            'day_of_week': 5,
            'media_type': 'video',
        },
    ])


def downgrade():
    op.drop_index('ix_memes_active_day', table_name='memes')
    op.drop_index('ix_memes_image_url_unique', table_name='memes')
    op.drop_table('memes')
