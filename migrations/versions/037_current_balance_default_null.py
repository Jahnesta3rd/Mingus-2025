"""Set user_profiles.current_balance default to NULL

Revision ID: 037_current_balance_default_null
Revises: 036_backfill_gmail_co_truncation_bug
Create Date: 2026-05-11
"""

from alembic import op


revision = "037_current_balance_default_null"
down_revision = "036_backfill_gmail_co_truncation_bug"
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column(
        "user_profiles",
        "current_balance",
        nullable=True,
        server_default=None,
    )
    op.execute(
        """
        UPDATE user_profiles
        SET current_balance = NULL
        WHERE current_balance = 5000.0
          AND balance_last_updated IS NULL
        """
    )


def downgrade():
    op.alter_column(
        "user_profiles",
        "current_balance",
        server_default="5000.0",
    )
