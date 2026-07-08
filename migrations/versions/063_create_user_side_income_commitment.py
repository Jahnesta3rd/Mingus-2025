"""Create user side income commitment tracking table.

Revision ID: 063_create_user_side_income_commitment
Revises: 062_add_independence_calculator_dismissed
Create Date: 2026-07-08

Track ICC → DF1 side income job selections and milestone progress.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID as PG_UUID


revision = "063_create_user_side_income_commitment"
down_revision = "062_add_independence_calculator_dismissed"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "user_side_income_commitment",
        sa.Column(
            "id",
            PG_UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("icc_assessment_id", PG_UUID(as_uuid=True), nullable=True),
        sa.Column("person_id", PG_UUID(as_uuid=True), nullable=True),
        sa.Column("selected_job", sa.String(length=150), nullable=False),
        sa.Column("df1_job_type", sa.String(length=20), nullable=True),
        sa.Column("target_monthly_income", sa.Numeric(8, 2), nullable=False),
        sa.Column(
            "status",
            sa.String(length=30),
            nullable=False,
            server_default=sa.text("'selected'"),
        ),
        sa.Column("df1_first_income_date", sa.DateTime(), nullable=True),
        sa.Column("df1_monthly_income_actual", sa.Numeric(8, 2), nullable=True),
        sa.Column("independence_timeline_original_months", sa.Integer(), nullable=True),
        sa.Column("independence_timeline_with_income_months", sa.Integer(), nullable=True),
        sa.Column("gap_coverage_pct_at_selection", sa.Numeric(5, 2), nullable=True),
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
            "icc_assessment_id",
            name="uq_user_icc_assessment",
        ),
    )
    op.create_index(
        "ix_side_income_user_status",
        "user_side_income_commitment",
        ["user_id", "status"],
    )
    op.create_index(
        "ix_side_income_created",
        "user_side_income_commitment",
        ["user_id", "created_at"],
    )


def downgrade():
    op.drop_index("ix_side_income_created", table_name="user_side_income_commitment")
    op.drop_index("ix_side_income_user_status", table_name="user_side_income_commitment")
    op.drop_table("user_side_income_commitment")
