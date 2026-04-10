"""add life_ledger tables

Revision ID: 013_add_life_ledger_tables
Revises: 012_user_profiles_cash_balance
Create Date: 2026-04-08

Life Ledger profile (per-user scores and projections), module answers, and insights.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID as PG_UUID


revision = "013_add_life_ledger_tables"
down_revision = "012_user_profiles_cash_balance"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "life_ledger_profiles",
        sa.Column(
            "id",
            PG_UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("vibe_score", sa.Integer(), nullable=True),
        sa.Column("body_score", sa.Integer(), nullable=True),
        sa.Column("roof_score", sa.Integer(), nullable=True),
        sa.Column("vehicle_score", sa.Integer(), nullable=True),
        sa.Column("life_ledger_score", sa.Integer(), nullable=True),
        sa.Column("vibe_lead_id", PG_UUID(as_uuid=True), nullable=True),
        sa.Column("vibe_annual_projection", sa.Integer(), nullable=True),
        sa.Column("body_health_cost_projection", sa.Integer(), nullable=True),
        sa.Column("roof_housing_wealth_gap", sa.Integer(), nullable=True),
        sa.Column("vehicle_annual_maintenance", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint(
            "vibe_score IS NULL OR (vibe_score >= 0 AND vibe_score <= 100)",
            name="ck_life_ledger_profiles_vibe_score",
        ),
        sa.CheckConstraint(
            "body_score IS NULL OR (body_score >= 0 AND body_score <= 100)",
            name="ck_life_ledger_profiles_body_score",
        ),
        sa.CheckConstraint(
            "roof_score IS NULL OR (roof_score >= 0 AND roof_score <= 100)",
            name="ck_life_ledger_profiles_roof_score",
        ),
        sa.CheckConstraint(
            "vehicle_score IS NULL OR (vehicle_score >= 0 AND vehicle_score <= 100)",
            name="ck_life_ledger_profiles_vehicle_score",
        ),
        sa.CheckConstraint(
            "life_ledger_score IS NULL OR (life_ledger_score >= 0 AND life_ledger_score <= 100)",
            name="ck_life_ledger_profiles_life_ledger_score",
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["vibe_lead_id"], ["vibe_checkups_leads.id"], ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", name="uq_life_ledger_profiles_user_id"),
    )

    op.create_table(
        "life_ledger_module_answers",
        sa.Column(
            "id",
            PG_UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("module", sa.String(length=32), nullable=False),
        sa.Column("answers", sa.JSON(), nullable=False),
        sa.Column("completed_at", sa.DateTime(), nullable=False),
        sa.Column("score", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_life_ledger_module_answers_user_id",
        "life_ledger_module_answers",
        ["user_id"],
    )

    op.create_table(
        "life_ledger_insights",
        sa.Column(
            "id",
            PG_UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("module", sa.String(length=32), nullable=False),
        sa.Column("insight_type", sa.String(length=64), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("action_url", sa.String(length=512), nullable=True),
        sa.Column(
            "dismissed",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_life_ledger_insights_user_id",
        "life_ledger_insights",
        ["user_id"],
    )
    op.create_index(
        "ix_life_ledger_insights_user_module_type",
        "life_ledger_insights",
        ["user_id", "module", "insight_type"],
    )


def downgrade():
    op.drop_index(
        "ix_life_ledger_insights_user_module_type",
        table_name="life_ledger_insights",
    )
    op.drop_index("ix_life_ledger_insights_user_id", table_name="life_ledger_insights")
    op.drop_table("life_ledger_insights")

    op.drop_index(
        "ix_life_ledger_module_answers_user_id",
        table_name="life_ledger_module_answers",
    )
    op.drop_table("life_ledger_module_answers")

    op.drop_table("life_ledger_profiles")
