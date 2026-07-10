"""Create back_to_school_recommendations audit table (BTS5).

Revision ID: 069_create_bts_recommendations
Revises: 068_create_bts_tables
Create Date: 2026-07-10
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID


revision = "069_create_bts_recommendations"
down_revision = "068_create_bts_tables"
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    exists = conn.execute(
        sa.text(
            "SELECT to_regclass('public.back_to_school_recommendations') IS NOT NULL"
        )
    ).scalar()
    if exists:
        return

    op.create_table(
        "back_to_school_recommendations",
        sa.Column(
            "recommendation_id",
            PG_UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("session_id", PG_UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", sa.String(length=255), nullable=False),
        sa.Column("tier", sa.String(length=20), nullable=False),
        sa.Column("recommendation_data", JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.ForeignKeyConstraint(
            ["session_id"],
            ["back_to_school_sessions.session_id"],
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint(
            "session_id",
            "tier",
            name="uq_bts_recommendation_session_tier",
        ),
    )
    op.create_index(
        "idx_bts_rec_user",
        "back_to_school_recommendations",
        ["user_id"],
    )
    op.create_index(
        "idx_bts_rec_session",
        "back_to_school_recommendations",
        ["session_id"],
    )


def downgrade():
    op.execute("DROP INDEX IF EXISTS idx_bts_rec_session")
    op.execute("DROP INDEX IF EXISTS idx_bts_rec_user")
    op.execute("DROP TABLE IF EXISTS back_to_school_recommendations")
