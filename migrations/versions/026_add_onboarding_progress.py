"""add onboarding_progress table

Revision ID: 026_add_onboarding_progress
Revises: 025_add_bug_reports
Create Date: 2026-04-18
"""
from alembic import op
import sqlalchemy as sa


revision = "026_add_onboarding_progress"
down_revision = "025_add_bug_reports"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "onboarding_progress",
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("completed_modules", sa.JSON(), nullable=False),
        sa.Column("skipped_modules", sa.JSON(), nullable=False),
        sa.Column("current_module", sa.String(length=64), nullable=False),
        sa.Column("started_at", sa.DateTime(), nullable=False),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("last_activity_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("user_id"),
    )


def downgrade():
    op.drop_table("onboarding_progress")
