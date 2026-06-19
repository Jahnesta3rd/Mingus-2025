"""052_user_profiles_zip_code

Revision ID: 052_user_profiles_zip_code
Revises: 051_layoff_events_source
Create Date: 2026-06-19

JRA-01: Add zip_code to user_profiles for MSA resolver fallback chain.
"""
from alembic import op
import sqlalchemy as sa


revision = "052_user_profiles_zip_code"
down_revision = "051_layoff_events_source"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "user_profiles",
        sa.Column("zip_code", sa.String(10), nullable=True),
    )


def downgrade():
    op.drop_column("user_profiles", "zip_code")
