"""Add housing_profile.down_payment_saved for onboarding buy-goal tracking

Revision ID: 041_housing_profile_down_payment_saved
Revises: a113a2_job_postings
Create Date: 2026-06-05
"""

import sqlalchemy as sa
from alembic import op

revision = "041_housing_profile_down_payment_saved"
down_revision = "a113a2_job_postings"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "housing_profile",
        sa.Column(
            "down_payment_saved",
            sa.Float(),
            nullable=True,
            server_default="0",
        ),
    )


def downgrade():
    op.drop_column("housing_profile", "down_payment_saved")
