"""Decision 8: career_profile table for modular onboarding

Revision ID: 033_career_profile_table
Revises: 032_user_social_spend_monthly
Create Date: 2026-04-18
"""

from alembic import op
import sqlalchemy as sa


revision = "033_career_profile_table"
down_revision = "032_user_social_spend_monthly"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "career_profile",
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("current_role", sa.String(length=100), nullable=True),
        sa.Column("industry", sa.String(length=100), nullable=True),
        sa.Column("years_experience", sa.Integer(), nullable=True),
        sa.Column("satisfaction", sa.Integer(), nullable=True),
        sa.Column("open_to_move", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("target_comp", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("user_id"),
        sa.CheckConstraint(
            "years_experience IS NULL OR (years_experience >= 0 AND years_experience <= 60)",
            name="ck_career_profile_years_experience",
        ),
        sa.CheckConstraint(
            "satisfaction IS NULL OR (satisfaction >= 1 AND satisfaction <= 5)",
            name="ck_career_profile_satisfaction",
        ),
    )


def downgrade():
    op.drop_table("career_profile")
