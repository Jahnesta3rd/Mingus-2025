"""Decision 3: housing_profile table for modular onboarding

Revision ID: 029_housing_profile_table
Revises: 028_relationship_status_enum_gc2
Create Date: 2026-04-18
"""

from alembic import op
import sqlalchemy as sa


revision = "029_housing_profile_table"
down_revision = "028_relationship_status_enum_gc2"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "housing_profile",
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("housing_type", sa.String(length=10), nullable=False),
        sa.Column("monthly_cost", sa.Float(), nullable=False),
        sa.Column("zip_or_city", sa.String(length=100), nullable=False),
        sa.Column("split_share_pct", sa.Float(), nullable=True),
        sa.Column("has_buy_goal", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("target_price", sa.Float(), nullable=True),
        sa.Column("target_timeline_months", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("user_id"),
        sa.CheckConstraint(
            "housing_type IN ('rent','own')", name="ck_housing_profile_housing_type"
        ),
        sa.CheckConstraint("monthly_cost >= 0", name="ck_housing_profile_monthly_cost"),
        sa.CheckConstraint(
            "split_share_pct IS NULL OR (split_share_pct >= 0 AND split_share_pct <= 100)",
            name="ck_housing_profile_split_share_pct",
        ),
    )


def downgrade():
    op.drop_table("housing_profile")
