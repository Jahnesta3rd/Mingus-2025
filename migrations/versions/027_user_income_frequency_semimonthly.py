"""Decision 1: allow semimonthly on user_income.frequency

Revision ID: 027_user_income_frequency_semimonthly
Revises: 026_add_onboarding_progress
Create Date: 2026-04-18
"""

from alembic import op


revision = "027_user_income_frequency_semimonthly"
down_revision = "026_add_onboarding_progress"
branch_labels = None
depends_on = None


def upgrade():
    op.drop_constraint("ck_user_income_frequency", "user_income", type_="check")
    op.create_check_constraint(
        "ck_user_income_frequency",
        "user_income",
        "frequency IN ('monthly', 'biweekly', 'weekly', 'semimonthly', 'annual')",
    )


def downgrade():
    op.drop_constraint("ck_user_income_frequency", "user_income", type_="check")
    op.create_check_constraint(
        "ck_user_income_frequency",
        "user_income",
        "frequency IN ('monthly', 'biweekly', 'weekly', 'annual')",
    )
