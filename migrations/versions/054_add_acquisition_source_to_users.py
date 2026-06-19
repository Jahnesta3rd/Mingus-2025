"""054_add_acquisition_source_to_users

Revision ID: 054_acquisition_source
Revises: 03df5bea7b11
Create Date: 2026-06-19

Add nullable acquisition_source to users for onboarding step 0.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision = "054_acquisition_source"
down_revision = "03df5bea7b11"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = inspect(bind)
    if "acquisition_source" not in {c["name"] for c in inspector.get_columns("users")}:
        op.add_column(
            "users",
            sa.Column("acquisition_source", sa.String(50), nullable=True),
        )


def downgrade():
    bind = op.get_bind()
    inspector = inspect(bind)
    if "acquisition_source" in {c["name"] for c in inspector.get_columns("users")}:
        op.drop_column("users", "acquisition_source")
