"""062_add_independence_calculator_dismissed

Revision ID: 062_add_independence_calculator_dismissed
Revises: 061_create_independence_cost_tables
Create Date: 2026-07-08

Track whether a user has dismissed the independence cost calculator prompt.
"""
from alembic import op
import sqlalchemy as sa


revision = "062_add_independence_calculator_dismissed"
down_revision = "061_create_independence_cost_tables"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "users",
        sa.Column(
            "has_independence_calculator_dismissed",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )
    op.create_index(
        "ix_users_icc_dismissed",
        "users",
        ["has_independence_calculator_dismissed"],
    )


def downgrade():
    op.drop_index("ix_users_icc_dismissed", table_name="users")
    op.drop_column("users", "has_independence_calculator_dismissed")
