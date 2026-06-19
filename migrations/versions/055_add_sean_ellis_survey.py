"""055_add_sean_ellis_survey

Revision ID: 055_sean_ellis_survey
Revises: 054_acquisition_source
Create Date: 2026-06-19

Sean Ellis PMF survey responses (one per user).
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision = "055_sean_ellis_survey"
down_revision = "054_acquisition_source"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = inspect(bind)
    if "sean_ellis_survey" not in inspector.get_table_names():
        op.create_table(
            "sean_ellis_survey",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("user_id", sa.Integer(), nullable=False),
            sa.Column("response", sa.String(length=20), nullable=False),
            sa.Column("submitted_at", sa.DateTime(), server_default=sa.text("NOW()"), nullable=True),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("user_id"),
        )


def downgrade():
    bind = op.get_bind()
    inspector = inspect(bind)
    if "sean_ellis_survey" in inspector.get_table_names():
        op.drop_table("sean_ellis_survey")
