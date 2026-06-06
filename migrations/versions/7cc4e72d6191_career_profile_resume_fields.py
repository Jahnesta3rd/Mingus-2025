"""career_profile_resume_fields

Revision ID: 7cc4e72d6191
Revises: 041_housing_profile_down_payment_saved
Create Date: 2026-06-06 18:05:35.704396

"""

import sqlalchemy as sa
from alembic import op

revision = "7cc4e72d6191"
down_revision = "041_housing_profile_down_payment_saved"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "career_profile",
        sa.Column("resume_file_path", sa.String(length=500), nullable=True),
    )
    op.add_column(
        "career_profile",
        sa.Column("resume_parsed_at", sa.DateTime(), nullable=True),
    )
    op.add_column(
        "career_profile",
        sa.Column(
            "resume_confidence_score",
            sa.Numeric(precision=4, scale=2),
            nullable=True,
        ),
    )


def downgrade():
    op.drop_column("career_profile", "resume_confidence_score")
    op.drop_column("career_profile", "resume_parsed_at")
    op.drop_column("career_profile", "resume_file_path")
