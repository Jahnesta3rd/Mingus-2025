"""Decision 5: vibe_tracked_people roster columns for modular onboarding

Revision ID: 031_vibe_tracked_person_gc2_columns
Revises: 030_recurring_expense_category_gc2
Create Date: 2026-04-18
"""

from alembic import op
import sqlalchemy as sa


revision = "031_vibe_tracked_person_gc2_columns"
down_revision = "030_recurring_expense_category_gc2"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "vibe_tracked_people",
        sa.Column("relationship_type", sa.String(length=50), nullable=True),
    )
    op.add_column(
        "vibe_tracked_people",
        sa.Column("estimated_monthly_cost", sa.Float(), nullable=True),
    )


def downgrade():
    op.drop_column("vibe_tracked_people", "estimated_monthly_cost")
    op.drop_column("vibe_tracked_people", "relationship_type")
