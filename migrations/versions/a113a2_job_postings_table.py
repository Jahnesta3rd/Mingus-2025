"""job_postings table for #113 Phase A2 seed data

Revision ID: a113a2_job_postings
Revises: f1a2b3c4d5e6
Create Date: 2026-06-03 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = "a113a2_job_postings"
down_revision = "f1a2b3c4d5e6"
branch_labels = None
depends_on = None

_CAREER_FIELD_CHECK = (
    "career_field IN ("
    "'Technology', "
    "'Healthcare (Clinical)', "
    "'Healthcare (Admin/Ops)', "
    "'Finance & Accounting', "
    "'Legal', "
    "'Marketing & Communications', "
    "'Sales', "
    "'Education & Training', "
    "'Engineering (Civil/Mech/Ind)', "
    "'Creative & Design', "
    "'Operations & Supply Chain', "
    "'Human Resources', "
    "'Real Estate', "
    "'Social Services & Nonprofit', "
    "'Government & Public Policy', "
    "'Hospitality & Food Service', "
    "'Retail & Consumer', "
    "'Construction & Trades', "
    "'Media & Journalism', "
    "'Science & Research', "
    "'Military / Veterans', "
    "'Self-Employed / Entrepreneurship'"
    ")"
)

_SENIORITY_CHECK = (
    "seniority_level IN ('entry', 'mid', 'senior', 'director')"
)


def upgrade():
    op.create_table(
        "job_postings",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("company", sa.String(length=200), nullable=False),
        sa.Column("career_field", sa.String(length=100), nullable=False),
        sa.Column("msa_code", sa.String(length=20), nullable=False),
        sa.Column("city", sa.String(length=100), nullable=False),
        sa.Column("state", sa.String(length=2), nullable=False),
        sa.Column("salary_min", sa.Integer(), nullable=False),
        sa.Column("salary_max", sa.Integer(), nullable=False),
        sa.Column("seniority_level", sa.String(length=20), nullable=False),
        sa.Column(
            "is_management",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column("advancement_trajectory", sa.String(length=300), nullable=False),
        sa.Column(
            "source",
            sa.String(length=50),
            nullable=False,
            server_default="seed_2026",
        ),
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint(_CAREER_FIELD_CHECK, name="ck_job_postings_career_field"),
        sa.CheckConstraint(_SENIORITY_CHECK, name="ck_job_postings_seniority_level"),
    )
    op.create_index(
        "ix_job_postings_career_field_msa_code",
        "job_postings",
        ["career_field", "msa_code"],
    )


def downgrade():
    op.drop_index("ix_job_postings_career_field_msa_code", table_name="job_postings")
    op.drop_table("job_postings")
