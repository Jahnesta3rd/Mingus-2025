"""add llm_narrative_credits table

Revision ID: 048_llm_narrative_credits
Revises: 046_employer_health
Create Date: 2026-06-12

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID as PG_UUID


revision = "048_llm_narrative_credits"
down_revision = "046_employer_health"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "llm_narrative_credits",
        sa.Column(
            "id",
            PG_UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("month_key", sa.String(length=7), nullable=False),
        sa.Column(
            "credits_used",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column(
            "credits_limit",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("10"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "month_key"),
    )
    op.create_index(
        "idx_llm_narrative_credits_user_month",
        "llm_narrative_credits",
        ["user_id", "month_key"],
    )


def downgrade():
    op.drop_index(
        "idx_llm_narrative_credits_user_month",
        table_name="llm_narrative_credits",
    )
    op.drop_table("llm_narrative_credits")
