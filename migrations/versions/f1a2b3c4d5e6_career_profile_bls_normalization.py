"""career_profile_bls_normalization

Revision ID: f1a2b3c4d5e6
Revises: e978e3d9a0ca
Create Date: 2026-06-04 00:45:00.000000

"""
import sqlalchemy as sa
from alembic import op

revision = "f1a2b3c4d5e6"
down_revision = "e978e3d9a0ca"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "career_profile",
        sa.Column("bls_career_field", sa.String(length=100), nullable=True),
    )
    op.add_column(
        "career_profile",
        sa.Column("seniority_level", sa.String(length=20), nullable=True),
    )
    op.add_column(
        "career_profile",
        sa.Column("is_management", sa.Boolean(), nullable=True),
    )
    op.add_column(
        "career_profile",
        sa.Column("title_normalized_at", sa.DateTime(), nullable=True),
    )
    op.add_column(
        "career_profile",
        sa.Column("title_normalization_source", sa.String(length=20), nullable=True),
    )


def downgrade():
    op.drop_column("career_profile", "title_normalization_source")
    op.drop_column("career_profile", "title_normalized_at")
    op.drop_column("career_profile", "is_management")
    op.drop_column("career_profile", "seniority_level")
    op.drop_column("career_profile", "bls_career_field")
