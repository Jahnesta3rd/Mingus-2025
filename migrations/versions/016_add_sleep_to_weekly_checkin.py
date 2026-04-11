"""add sleep_hours to weekly_checkins

Revision ID: 016_add_sleep_to_weekly_checkin
Revises: 015_add_transaction_schedule
Create Date: 2026-04-11

Nullable average hours slept for the week (Self Card / roster).
"""
from alembic import op
import sqlalchemy as sa


revision = "016_add_sleep_to_weekly_checkin"
down_revision = "015_add_transaction_schedule"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "weekly_checkins",
        sa.Column("sleep_hours", sa.Float(), nullable=True),
    )


def downgrade():
    op.drop_column("weekly_checkins", "sleep_hours")
