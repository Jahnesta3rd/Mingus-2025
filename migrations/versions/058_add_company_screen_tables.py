"""058_add_company_screen_tables

Revision ID: 058_add_company_screen_tables
Revises: dea3e9e2743f
Create Date: 2026-06-22

Company screen scoring tables: screens, follow-up questions, jargon cache.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID


revision = "058_add_company_screen_tables"
down_revision = "dea3e9e2743f"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "company_screens",
        sa.Column(
            "id",
            PG_UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("employer_cik", sa.String(length=20), nullable=True),
        sa.Column("employer_name_text", sa.String(length=200), nullable=False),
        sa.Column("composite_score", sa.Integer(), nullable=True),
        sa.Column("composite_band", sa.String(length=20), nullable=True),
        sa.Column("layer1_score", sa.Integer(), nullable=True),
        sa.Column(
            "layer1_status",
            sa.String(length=20),
            nullable=False,
            server_default=sa.text("'pending'"),
        ),
        sa.Column("layer2_score", sa.Integer(), nullable=True),
        sa.Column(
            "layer2_status",
            sa.String(length=20),
            nullable=False,
            server_default=sa.text("'pending'"),
        ),
        sa.Column("layer3_band", sa.String(length=30), nullable=True),
        sa.Column(
            "layer3_status",
            sa.String(length=20),
            nullable=False,
            server_default=sa.text("'pending'"),
        ),
        sa.Column(
            "layoff_event_detected",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column("layoff_event_date", sa.String(length=20), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "expires_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("(now() + interval '7 days')"),
        ),
        sa.Column(
            "screens_used_this_cycle",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("1"),
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_company_screens_user_id"),
        "company_screens",
        ["user_id"],
        unique=False,
    )

    op.create_table(
        "company_screen_questions",
        sa.Column(
            "id",
            PG_UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("screen_id", PG_UUID(as_uuid=True), nullable=False),
        sa.Column("question_text", sa.Text(), nullable=False),
        sa.Column("flag_source", sa.String(length=50), nullable=True),
        sa.Column(
            "display_order",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column("dismissed_at", sa.DateTime(), nullable=True),
        sa.Column("copied_at", sa.DateTime(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.ForeignKeyConstraint(
            ["screen_id"],
            ["company_screens.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_company_screen_questions_screen_id"),
        "company_screen_questions",
        ["screen_id"],
        unique=False,
    )

    op.create_table(
        "company_jargon_cache",
        sa.Column(
            "id",
            PG_UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("employer_cik", sa.String(length=20), nullable=True),
        sa.Column("employer_name_hash", sa.String(length=64), nullable=False),
        sa.Column("raw_text_hash", sa.String(length=64), nullable=False),
        sa.Column("jargon_score", sa.Integer(), nullable=False),
        sa.Column("jargon_density_pct", sa.Float(), nullable=True),
        sa.Column("top_jargon_phrases", JSONB(), nullable=True),
        sa.Column(
            "scored_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "expires_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("(now() + interval '14 days')"),
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "employer_name_hash",
            "raw_text_hash",
            name="uq_company_jargon_cache_name_text_hash",
        ),
    )


def downgrade():
    op.drop_table("company_jargon_cache")
    op.drop_index(
        op.f("ix_company_screen_questions_screen_id"),
        table_name="company_screen_questions",
    )
    op.drop_table("company_screen_questions")
    op.drop_index(op.f("ix_company_screens_user_id"), table_name="company_screens")
    op.drop_table("company_screens")
