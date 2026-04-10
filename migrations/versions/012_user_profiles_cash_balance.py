"""user_profiles current_balance and balance_last_updated

Revision ID: 012_user_profiles_cash_balance
Revises: 011_add_vibe_checkups_tables
Create Date: 2026-04-07

Adds self-reported cash balance fields to user_profiles for cash flow forecasting.
"""
from alembic import op
import sqlalchemy as sa


revision = "012_user_profiles_cash_balance"
down_revision = "011_add_vibe_checkups_tables"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "user_profiles",
        sa.Column(
            "current_balance",
            sa.Float(),
            nullable=False,
            server_default=sa.text("5000.0"),
        ),
    )
    op.add_column(
        "user_profiles",
        sa.Column("balance_last_updated", sa.DateTime(), nullable=True),
    )


def downgrade():
    op.drop_column("user_profiles", "balance_last_updated")
    op.drop_column("user_profiles", "current_balance")
