"""Create expense audit snapshots table.

Revision ID: 064_create_expense_audit_snapshots
Revises: 063_create_user_side_income_commitment
Create Date: 2026-07-08

90-day spending analysis with tier-based cut recommendations for ICC integration.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID


revision = "064_create_expense_audit_snapshots"
down_revision = "063_create_user_side_income_commitment"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "expense_audit_snapshots",
        sa.Column(
            "id",
            PG_UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column(
            "days_lookback",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("90"),
        ),
        sa.Column("total_monthly_spending", sa.Numeric(8, 2), nullable=False),
        sa.Column("spending_by_category", JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("tier_recommendations", JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("combined_savings", JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("replacement_activities", JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("selected_tiers", sa.String(length=10), nullable=True),
        sa.Column("total_savings_selected", sa.Numeric(8, 2), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.UniqueConstraint(
            "user_id",
            "created_at",
            name="uq_expense_audit_user_date",
        ),
    )
    op.create_index(
        "ix_expense_audit_user",
        "expense_audit_snapshots",
        ["user_id", "created_at"],
    )


def downgrade():
    op.drop_index("ix_expense_audit_user", table_name="expense_audit_snapshots")
    op.drop_table("expense_audit_snapshots")
