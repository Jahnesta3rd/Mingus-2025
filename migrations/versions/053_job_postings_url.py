"""053_job_postings_url

Revision ID: 053_job_postings_url
Revises: 052_user_profiles_zip_code
Create Date: 2026-06-19

JRA-02: Add nullable url column to job_postings for future live job board links.
"""
from alembic import op
import sqlalchemy as sa


revision = "053_job_postings_url"
down_revision = "052_user_profiles_zip_code"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "job_postings",
        sa.Column("url", sa.Text(), nullable=True),
    )


def downgrade():
    op.drop_column("job_postings", "url")
