"""add_quick_spend_entries

Revision ID: 03df5bea7b11
Revises: 053_job_postings_url
Create Date: 2026-06-19 20:18:17.415767

"""
from alembic import op
import sqlalchemy as sa


revision = "03df5bea7b11"
down_revision = "053_job_postings_url"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "quick_spend_entries",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("logged_at", sa.DateTime(), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("amount", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("spend_vibe", sa.String(length=50), nullable=False),
        sa.Column("vibe_signal", sa.String(length=50), nullable=False),
        sa.Column("merchant_id", sa.String(length=50), nullable=True),
        sa.Column("merchant_name", sa.String(length=100), nullable=True),
        sa.Column("merchant_group", sa.String(length=60), nullable=True),
        sa.Column("notes", sa.String(length=200), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_quick_spend_entries_date"),
        "quick_spend_entries",
        ["date"],
        unique=False,
    )
    op.create_index(
        op.f("ix_quick_spend_entries_user_id"),
        "quick_spend_entries",
        ["user_id"],
        unique=False,
    )
    op.create_index(
        "ix_quick_spend_user_date",
        "quick_spend_entries",
        ["user_id", "date"],
        unique=False,
    )


def downgrade():
    op.drop_index("ix_quick_spend_user_date", table_name="quick_spend_entries")
    op.drop_index(
        op.f("ix_quick_spend_entries_user_id"), table_name="quick_spend_entries"
    )
    op.drop_index(
        op.f("ix_quick_spend_entries_date"), table_name="quick_spend_entries"
    )
    op.drop_table("quick_spend_entries")
