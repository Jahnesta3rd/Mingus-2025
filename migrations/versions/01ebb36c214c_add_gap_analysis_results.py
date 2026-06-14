"""add_gap_analysis_results

Revision ID: 01ebb36c214c
Revises: cef9f986028e
Create Date: 2026-06-14 16:48:54.278705

"""
from alembic import op
import sqlalchemy as sa


revision = "01ebb36c214c"
down_revision = "cef9f986028e"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "gap_analysis_results",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("home_price", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("down_payment_pct", sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column("interest_rate", sa.Numeric(precision=5, scale=3), nullable=False),
        sa.Column("loan_term_years", sa.Integer(), nullable=False),
        sa.Column("timeline_months", sa.Integer(), nullable=False),
        sa.Column("gap_income", sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column("gap_savings_rate", sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column("gap_down_payment", sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column("gap_dti", sa.Numeric(precision=7, scale=4), nullable=True),
        sa.Column("gap_credit", sa.Integer(), nullable=True),
        sa.Column("income_severity", sa.String(length=20), nullable=True),
        sa.Column("savings_severity", sa.String(length=20), nullable=True),
        sa.Column("down_payment_severity", sa.String(length=20), nullable=True),
        sa.Column("dti_severity", sa.String(length=20), nullable=True),
        sa.Column("credit_severity", sa.String(length=20), nullable=True),
        sa.Column("required_gross_income", sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column("required_monthly_savings", sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column("target_down_payment", sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column("monthly_piti", sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column("action_plan_json", sa.JSON(), nullable=True),
        sa.Column("plan_generated_at", sa.DateTime(), nullable=True),
        sa.Column("expires_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_gap_analysis_results_created_at"),
        "gap_analysis_results",
        ["created_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_gap_analysis_results_user_id"),
        "gap_analysis_results",
        ["user_id"],
        unique=False,
    )


def downgrade():
    op.drop_index(
        op.f("ix_gap_analysis_results_user_id"), table_name="gap_analysis_results"
    )
    op.drop_index(
        op.f("ix_gap_analysis_results_created_at"), table_name="gap_analysis_results"
    )
    op.drop_table("gap_analysis_results")
