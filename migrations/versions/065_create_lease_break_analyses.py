"""Create lease break analyses table.

Revision ID: 065_create_lease_break_analyses
Revises: 064_create_expense_audit_snapshots
Create Date: 2026-07-08

Early lease termination vs. staying cost comparison for ICC exit planning.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID as PG_UUID


revision = "065_create_lease_break_analyses"
down_revision = "064_create_expense_audit_snapshots"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "lease_break_analyses",
        sa.Column(
            "id",
            PG_UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("months_remaining", sa.Integer(), nullable=False),
        sa.Column("monthly_rent", sa.Numeric(8, 2), nullable=False),
        sa.Column(
            "break_fee_percent",
            sa.Numeric(3, 1),
            nullable=False,
            server_default=sa.text("1.5"),
        ),
        sa.Column("scenario_a_cost", sa.Numeric(10, 2), nullable=False),
        sa.Column("scenario_b_cost", sa.Numeric(10, 2), nullable=False),
        sa.Column("recommendation", sa.String(length=50), nullable=False),
        sa.Column("savings", sa.Numeric(10, 2), nullable=True),
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
            name="uq_lease_break_user_date",
        ),
    )
    op.create_index(
        "ix_lease_break_user",
        "lease_break_analyses",
        ["user_id"],
    )


def downgrade():
    op.drop_index("ix_lease_break_user", table_name="lease_break_analyses")
    op.drop_table("lease_break_analyses")
