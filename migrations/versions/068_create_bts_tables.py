"""Create back-to-school sessions and purchase plans tables (BTS1/BTS2).

Revision ID: 068_create_bts_tables
Revises: 067_create_products_table
Create Date: 2026-07-10
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID


revision = "068_create_bts_tables"
down_revision = "067_create_products_table"
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()

    sessions_exist = conn.execute(
        sa.text("SELECT to_regclass('public.back_to_school_sessions') IS NOT NULL")
    ).scalar()
    if not sessions_exist:
        op.create_table(
            "back_to_school_sessions",
            sa.Column(
                "session_id",
                PG_UUID(as_uuid=True),
                primary_key=True,
                server_default=sa.text("gen_random_uuid()"),
            ),
            sa.Column("user_id", sa.String(length=255), nullable=False),
            sa.Column("bts_date", sa.Date(), nullable=False),
            sa.Column("tier1_date", sa.Date(), nullable=False),
            sa.Column("tier2_date", sa.Date(), nullable=False),
            sa.Column("tier3_date", sa.Date(), nullable=False),
            sa.Column("tier1_balance", sa.Numeric(12, 2), nullable=False),
            sa.Column("tier2_balance", sa.Numeric(12, 2), nullable=False),
            sa.Column("tier3_balance", sa.Numeric(12, 2), nullable=False),
            sa.Column("child_name", sa.String(length=255), nullable=True),
            sa.Column("child_age", sa.Integer(), nullable=True),
            sa.Column("child_gender", sa.String(length=50), nullable=True),
            sa.Column(
                "shortfall",
                sa.Numeric(12, 2),
                nullable=False,
                server_default="0",
            ),
            sa.Column("estimated_budget", sa.Numeric(12, 2), nullable=True),
            sa.Column(
                "created_at",
                sa.DateTime(),
                nullable=False,
                server_default=sa.text("NOW()"),
            ),
        )
        op.create_index(
            "ix_bts_sessions_user_id",
            "back_to_school_sessions",
            ["user_id"],
        )

    plans_exist = conn.execute(
        sa.text(
            "SELECT to_regclass('public.back_to_school_purchase_plans') IS NOT NULL"
        )
    ).scalar()
    if not plans_exist:
        op.create_table(
            "back_to_school_purchase_plans",
            sa.Column(
                "plan_id",
                PG_UUID(as_uuid=True),
                primary_key=True,
                server_default=sa.text("gen_random_uuid()"),
            ),
            sa.Column("session_id", PG_UUID(as_uuid=True), nullable=False),
            sa.Column("user_id", sa.String(length=255), nullable=False),
            sa.Column("plan_data", JSONB(astext_type=sa.Text()), nullable=False),
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
            sa.UniqueConstraint("session_id", name="uq_bts_plan_session"),
        )
        op.create_index(
            "idx_bts_plan_user",
            "back_to_school_purchase_plans",
            ["user_id"],
        )
        op.create_index(
            "idx_bts_plan_session",
            "back_to_school_purchase_plans",
            ["session_id"],
        )


def downgrade():
    op.execute("DROP INDEX IF EXISTS idx_bts_plan_session")
    op.execute("DROP INDEX IF EXISTS idx_bts_plan_user")
    op.execute("DROP TABLE IF EXISTS back_to_school_purchase_plans")
    op.execute("DROP INDEX IF EXISTS ix_bts_sessions_user_id")
    op.execute("DROP TABLE IF EXISTS back_to_school_sessions")
