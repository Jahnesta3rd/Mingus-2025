"""add users.primary_financial_goal for faith card

Revision ID: 024_add_users_primary_financial_goal
Revises: 023_add_favorite_verses
Create Date: 2026-04-15
"""
from alembic import op
import sqlalchemy as sa


revision = "024_add_users_primary_financial_goal"
down_revision = "023_add_favorite_verses"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "users",
        sa.Column("primary_financial_goal", sa.String(length=255), nullable=True),
    )


def downgrade():
    op.drop_column("users", "primary_financial_goal")
