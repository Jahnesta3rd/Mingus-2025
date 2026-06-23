"""add_career_commitment_profiles

Revision ID: c56cc3904151
Revises: 058_add_company_screen_tables
Create Date: 2026-06-23 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = "c56cc3904151"
down_revision = "058_add_company_screen_tables"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "career_commitment_profiles",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("commitment_type", sa.String(length=20), nullable=True),
        sa.Column("commitment_score", sa.Integer(), nullable=True),
        sa.Column("skill_development_frequency", sa.Integer(), nullable=True),
        sa.Column("field_research_done", sa.Boolean(), nullable=True),
        sa.Column("real_world_signal", sa.Boolean(), nullable=True),
        sa.Column("pivot_intent", sa.String(length=30), nullable=True),
        sa.Column("classified_at", sa.DateTime(), nullable=True),
        sa.Column("last_reviewed_at", sa.DateTime(), nullable=True),
        sa.Column(
            "review_stage",
            sa.String(length=20),
            server_default="initial",
            nullable=True,
        ),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", name="uq_career_commitment_profiles_user_id"),
    )
    op.create_index(
        "ix_career_commitment_profiles_user_id",
        "career_commitment_profiles",
        ["user_id"],
        unique=False,
    )
    op.create_index(
        "ix_career_commitment_profiles_user_id_review_stage",
        "career_commitment_profiles",
        ["user_id", "review_stage"],
        unique=False,
    )


def downgrade():
    op.drop_index(
        "ix_career_commitment_profiles_user_id_review_stage",
        table_name="career_commitment_profiles",
    )
    op.drop_index(
        "ix_career_commitment_profiles_user_id",
        table_name="career_commitment_profiles",
    )
    op.drop_table("career_commitment_profiles")
