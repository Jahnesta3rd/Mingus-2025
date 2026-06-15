"""050_merge_heads

Revision ID: 050_merge_heads
Revises: d822d7cafdb5, 049_lifescoresnapshot_career_score
Create Date: 2026-06-15 16:00:56.530581

"""
from alembic import op
import sqlalchemy as sa


revision = "050_merge_heads"
down_revision = ("d822d7cafdb5", "049_lifescoresnapshot_career_score")
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
