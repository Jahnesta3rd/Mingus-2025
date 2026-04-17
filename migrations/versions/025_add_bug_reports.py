"""add bug_reports table

Revision ID: 025_add_bug_reports
Revises: 024_add_users_primary_financial_goal
Create Date: 2026-04-15
"""
from alembic import op
import sqlalchemy as sa


revision = "025_add_bug_reports"
down_revision = "024_add_users_primary_financial_goal"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "bug_reports",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("ticket_number", sa.String(length=12), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("user_email", sa.String(length=255), nullable=False),
        sa.Column("user_name", sa.String(length=100), nullable=False),
        sa.Column("user_tier", sa.String(length=20), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("current_route", sa.String(length=255), nullable=True),
        sa.Column("browser_info", sa.String(length=255), nullable=True),
        sa.Column("balance_status", sa.String(length=20), nullable=True),
        sa.Column("last_feature", sa.String(length=100), nullable=True),
        sa.Column("onboarding_complete", sa.Boolean(), nullable=False),
        sa.Column("account_age_days", sa.Integer(), nullable=True),
        sa.Column("is_beta", sa.Boolean(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("admin_notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("resolved_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("ticket_number", name="uq_bug_reports_ticket_number"),
    )
    op.create_index(
        op.f("ix_bug_reports_created_at"),
        "bug_reports",
        ["created_at"],
        unique=False,
    )


def downgrade():
    op.drop_index(op.f("ix_bug_reports_created_at"), table_name="bug_reports")
    op.drop_table("bug_reports")
