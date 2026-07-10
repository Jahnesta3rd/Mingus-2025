"""Create bts_job_commitments table (BTS7).

Revision ID: 071_create_bts_job_commitments
Revises: 070_create_bts_purchase_orders
Create Date: 2026-07-10
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID as PG_UUID


revision = "071_create_bts_job_commitments"
down_revision = "070_create_bts_purchase_orders"
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    exists = conn.execute(
        sa.text("SELECT to_regclass('public.bts_job_commitments') IS NOT NULL")
    ).scalar()
    if exists:
        return

    op.create_table(
        "bts_job_commitments",
        sa.Column(
            "commitment_id",
            PG_UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("session_id", PG_UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", sa.String(length=255), nullable=False),
        sa.Column("job_id", sa.String(length=255), nullable=False),
        sa.Column("job_title", sa.String(length=255), nullable=False),
        sa.Column("tier2_date", sa.Date(), nullable=False),
        sa.Column("tier2_base_budget", sa.Numeric(10, 2), nullable=False),
        sa.Column("target_earnings", sa.Numeric(10, 2), nullable=False),
        sa.Column(
            "actual_earnings",
            sa.Numeric(10, 2),
            nullable=False,
            server_default="0",
        ),
        sa.Column(
            "tier2_budget_with_earnings",
            sa.Numeric(10, 2),
            nullable=False,
            server_default="0",
        ),
        sa.Column(
            "status",
            sa.String(length=50),
            nullable=False,
            server_default="active",
        ),
        sa.Column("last_sync_at", sa.DateTime(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.ForeignKeyConstraint(
            ["session_id"],
            ["back_to_school_sessions.session_id"],
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint(
            "session_id",
            name="uq_bts_job_commitment_session",
        ),
    )
    op.create_index(
        "idx_commitment_session",
        "bts_job_commitments",
        ["session_id"],
    )
    op.create_index(
        "idx_commitment_user",
        "bts_job_commitments",
        ["user_id"],
    )
    op.create_index(
        "idx_commitment_active",
        "bts_job_commitments",
        ["status"],
    )

    # Optional denormalized budget on session for plan/shop consumers
    session_cols = {
        c["name"]
        for c in sa.inspect(conn).get_columns("back_to_school_sessions")
    }
    if "tier2_budget_with_earnings" not in session_cols:
        op.add_column(
            "back_to_school_sessions",
            sa.Column(
                "tier2_budget_with_earnings",
                sa.Numeric(10, 2),
                nullable=True,
            ),
        )


def downgrade():
    conn = op.get_bind()
    session_cols = {
        c["name"]
        for c in sa.inspect(conn).get_columns("back_to_school_sessions")
    }
    if "tier2_budget_with_earnings" in session_cols:
        op.drop_column("back_to_school_sessions", "tier2_budget_with_earnings")

    op.execute("DROP INDEX IF EXISTS idx_commitment_active")
    op.execute("DROP INDEX IF EXISTS idx_commitment_user")
    op.execute("DROP INDEX IF EXISTS idx_commitment_session")
    op.execute("DROP TABLE IF EXISTS bts_job_commitments")
