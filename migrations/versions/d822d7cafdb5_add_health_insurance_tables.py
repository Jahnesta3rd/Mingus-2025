"""add_health_insurance_tables

Revision ID: d822d7cafdb5
Revises: 01ebb36c214c
Create Date: 2026-06-14 21:47:21.608473

"""
from alembic import op
import sqlalchemy as sa


revision = "d822d7cafdb5"
down_revision = "01ebb36c214c"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "health_insurance_plans",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("upload_batch_id", sa.String(length=36), nullable=True),
        sa.Column("plan_name", sa.String(length=200), nullable=False),
        sa.Column("plan_type", sa.String(length=20), nullable=True),
        sa.Column("insurer_name", sa.String(length=200), nullable=True),
        sa.Column("plan_year", sa.Integer(), nullable=True),
        sa.Column("monthly_premium_employee", sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column(
            "monthly_premium_employee_spouse",
            sa.Numeric(precision=10, scale=2),
            nullable=True,
        ),
        sa.Column("monthly_premium_family", sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column("annual_deductible_individual", sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column("annual_deductible_family", sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column("out_of_pocket_max_individual", sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column("out_of_pocket_max_family", sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column("coinsurance_pct", sa.Integer(), nullable=True),
        sa.Column("copay_primary_care", sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column("copay_specialist", sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column("copay_er", sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column("rx_tier1", sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column("rx_tier2", sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column("rx_tier3", sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column("rx_tier4", sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column(
            "has_hsa_eligible",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
        ),
        sa.Column("employer_hsa_contribution", sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column("in_network_only", sa.Boolean(), nullable=True),
        sa.Column("raw_document_path", sa.String(length=500), nullable=True),
        sa.Column(
            "parse_status",
            sa.String(length=20),
            server_default=sa.text("'pending'"),
            nullable=False,
        ),
        sa.Column("parsed_json", sa.JSON(), nullable=True),
        sa.Column("parsed_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_health_insurance_plans_user_id"),
        "health_insurance_plans",
        ["user_id"],
        unique=False,
    )
    op.create_table(
        "health_insurance_recommendations",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("generated_at", sa.DateTime(), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("recommended_plan_id", sa.Integer(), nullable=True),
        sa.Column("runner_up_plan_id", sa.Integer(), nullable=True),
        sa.Column("accepted_plan_id", sa.Integer(), nullable=True),
        sa.Column("recommendation_json", sa.JSON(), nullable=False),
        sa.Column(
            "expected_annual_cost_recommended",
            sa.Numeric(precision=10, scale=2),
            nullable=True,
        ),
        sa.Column(
            "expected_annual_cost_runner_up",
            sa.Numeric(precision=10, scale=2),
            nullable=True,
        ),
        sa.Column("hsa_recommended", sa.Boolean(), nullable=True),
        sa.Column("hsa_annual_benefit", sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column("risk_flags_json", sa.JSON(), nullable=True),
        sa.Column("benchmark_context_json", sa.JSON(), nullable=True),
        sa.Column(
            "model_version",
            sa.String(length=50),
            server_default=sa.text("'claude-sonnet-4-6'"),
            nullable=False,
        ),
        sa.Column("input_snapshot_json", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["accepted_plan_id"],
            ["health_insurance_plans.id"],
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["recommended_plan_id"],
            ["health_insurance_plans.id"],
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["runner_up_plan_id"],
            ["health_insurance_plans.id"],
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id"),
    )
    op.create_index(
        op.f("ix_health_insurance_recommendations_generated_at"),
        "health_insurance_recommendations",
        ["generated_at"],
        unique=False,
    )


def downgrade():
    op.drop_index(
        op.f("ix_health_insurance_recommendations_generated_at"),
        table_name="health_insurance_recommendations",
    )
    op.drop_table("health_insurance_recommendations")
    op.drop_index(
        op.f("ix_health_insurance_plans_user_id"),
        table_name="health_insurance_plans",
    )
    op.drop_table("health_insurance_plans")
