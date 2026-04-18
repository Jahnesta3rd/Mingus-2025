"""GC2 follow-up: nullable vehicles.vin and vehicles.user_zipcode for stub rows

Revision ID: 035_vehicle_nullable_vin_zip
Revises: 034_vehicle_onboarding_columns
Create Date: 2026-04-18
"""

from alembic import op
import sqlalchemy as sa


revision = "035_vehicle_nullable_vin_zip"
down_revision = "034_vehicle_onboarding_columns"
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column(
        "vehicles",
        "vin",
        existing_type=sa.String(length=17),
        nullable=True,
    )
    op.alter_column(
        "vehicles",
        "user_zipcode",
        existing_type=sa.String(length=10),
        nullable=True,
    )


def downgrade():
    op.alter_column(
        "vehicles",
        "user_zipcode",
        existing_type=sa.String(length=10),
        nullable=False,
    )
    op.alter_column(
        "vehicles",
        "vin",
        existing_type=sa.String(length=17),
        nullable=False,
    )
