"""Add users.last_vibe_moment_shown_at for once-per-day Vibe Moment tracking

Revision ID: 038_user_last_vibe_moment_shown_at
Revises: 037_current_balance_default_null
Create Date: 2026-05-11
"""

import sqlalchemy as sa
from alembic import op

revision = "038_user_last_vibe_moment_shown_at"
down_revision = "037_current_balance_default_null"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "users",
        sa.Column("last_vibe_moment_shown_at", sa.DateTime(), nullable=True),
    )


def downgrade():
    op.drop_column("users", "last_vibe_moment_shown_at")
