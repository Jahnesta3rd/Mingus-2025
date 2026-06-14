"""add_debt_profiles

Revision ID: cef9f986028e
Revises: a1b2c3d4e5f6
Create Date: 2026-06-14 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = "cef9f986028e"
down_revision = "a1b2c3d4e5f6"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "debt_profiles",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("revolving_balance", sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column("revolving_apr", sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column("revolving_min_payment", sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column(
            "revolving_apr_unknown",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
        ),
        sa.Column("installment_balance", sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column("installment_apr", sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column("installment_payment", sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column("federal_student_balance", sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column("federal_student_payment", sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column(
            "on_idr_plan",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
        ),
        sa.Column(
            "pursuing_pslf",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
        ),
        sa.Column("private_student_balance", sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column("private_student_apr", sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column("bnpl_balance", sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column("bnpl_monthly_payment", sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column("bnpl_active_plans", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", name="uq_debt_profiles_user_id"),
    )


def downgrade():
    op.drop_table("debt_profiles")
