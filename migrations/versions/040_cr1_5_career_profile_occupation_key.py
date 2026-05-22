"""CR1.5: add career_profile.occupation_key

Revision ID: 040_cr1_5_career_profile_occupation_key
Revises: 039_recurring_expense_category_wizard
Create Date: 2026-05-22
"""

import sqlalchemy as sa
from alembic import op

revision = "040_cr1_5_career_profile_occupation_key"
down_revision = "039_recurring_expense_category_wizard"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "career_profile",
        sa.Column("occupation_key", sa.String(length=50), nullable=True),
    )


def downgrade():
    op.drop_column("career_profile", "occupation_key")
