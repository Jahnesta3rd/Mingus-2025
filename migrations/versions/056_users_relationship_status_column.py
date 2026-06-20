"""056_users_relationship_status_column

Revision ID: 056_users_relationship_status
Revises: 055_sean_ellis_survey
Create Date: 2026-06-20

Nullable relationship_status on users for onboarding roster step.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision = "056_users_relationship_status"
down_revision = "055_sean_ellis_survey"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = inspect(bind)
    if not inspector.has_table("users"):
        return
    cols = {c["name"] for c in inspector.get_columns("users")}
    if "relationship_status" not in cols:
        op.add_column(
            "users",
            sa.Column("relationship_status", sa.String(length=32), nullable=True),
        )


def downgrade():
    bind = op.get_bind()
    inspector = inspect(bind)
    if not inspector.has_table("users"):
        return
    cols = {c["name"] for c in inspector.get_columns("users")}
    if "relationship_status" in cols:
        op.drop_column("users", "relationship_status")
