"""047_lifescoresnapshot_career_score

Revision ID: 049_lifescoresnapshot_career_score
Revises: 048_llm_narrative_credits
Create Date: 2026-06-15

Add career_score to life_score_snapshots for Whole-Life trend history.
"""
from alembic import op
import sqlalchemy as sa


revision = "049_lifescoresnapshot_career_score"
down_revision = "048_llm_narrative_credits"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "life_score_snapshots",
        sa.Column("career_score", sa.Float(), nullable=True),
    )


def downgrade():
    op.drop_column("life_score_snapshots", "career_score")
