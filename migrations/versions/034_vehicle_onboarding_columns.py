"""GC2 follow-up: vehicle monthly_fuel_cost, monthly_payment, recent_maintenance columns

Revision ID: 034_vehicle_onboarding_columns
Revises: 033_career_profile_table
Create Date: 2026-04-18
"""

from alembic import op
import sqlalchemy as sa


revision = "034_vehicle_onboarding_columns"
down_revision = "033_career_profile_table"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "vehicles",
        sa.Column("monthly_fuel_cost", sa.Numeric(10, 2), nullable=True),
    )
    op.add_column(
        "vehicles",
        sa.Column("monthly_payment", sa.Numeric(10, 2), nullable=True),
    )
    op.add_column(
        "vehicles",
        sa.Column("recent_maintenance", sa.Boolean(), nullable=True),
    )


def downgrade():
    op.drop_column("vehicles", "recent_maintenance")
    op.drop_column("vehicles", "monthly_payment")
    op.drop_column("vehicles", "monthly_fuel_cost")
