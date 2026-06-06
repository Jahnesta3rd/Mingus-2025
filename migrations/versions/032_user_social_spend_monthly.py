"""Decision 7: users.social_spend_monthly for roster module

Revision ID: 032_user_social_spend_monthly
Revises: 031_vibe_tracked_person_gc2_columns
Create Date: 2026-04-18
"""

from alembic import op
import sqlalchemy as sa


revision = "032_user_social_spend_monthly"
down_revision = "031_vibe_tracked_person_gc2_columns"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "users",
        sa.Column("social_spend_monthly", sa.Float(), nullable=True),
    )


def downgrade():
    op.drop_column("users", "social_spend_monthly")
