"""add connection_trend_assessments

Revision ID: 021_add_connection_trend
Revises: 020_add_vibe_tracked_person_card_type
Create Date: 2026-04-11

Connection Trend (fade scale) behavioral assessments per roster person.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID as PG_UUID


revision = "021_add_connection_trend"
down_revision = "020_add_vibe_tracked_person_card_type"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "connection_trend_assessments",
        sa.Column(
            "id",
            PG_UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("person_id", PG_UUID(as_uuid=True), nullable=False),
        sa.Column("assessed_at", sa.DateTime(), nullable=False),
        sa.Column("q1_response_pattern", sa.SmallInteger(), nullable=True),
        sa.Column("q2_initiative", sa.SmallInteger(), nullable=True),
        sa.Column("q3_followthrough", sa.SmallInteger(), nullable=True),
        sa.Column("q4_future_talk", sa.SmallInteger(), nullable=True),
        sa.Column("q5_social_visibility", sa.SmallInteger(), nullable=True),
        sa.Column("q6_reciprocity", sa.SmallInteger(), nullable=True),
        sa.Column("q7_gut_signal", sa.SmallInteger(), nullable=True),
        sa.Column("raw_score", sa.SmallInteger(), nullable=True),
        sa.Column("normalized_score", sa.SmallInteger(), nullable=True),
        sa.Column("fade_tier", sa.String(length=20), nullable=True),
        sa.Column("pattern_type", sa.String(length=30), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["person_id"],
            ["vibe_tracked_people.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_connection_trend_assessments_user_person_assessed_at",
        "connection_trend_assessments",
        ["user_id", "person_id", "assessed_at"],
    )
    op.create_index(
        op.f("ix_connection_trend_assessments_user_id"),
        "connection_trend_assessments",
        ["user_id"],
    )
    op.create_index(
        op.f("ix_connection_trend_assessments_person_id"),
        "connection_trend_assessments",
        ["person_id"],
    )


def downgrade():
    op.drop_index(
        op.f("ix_connection_trend_assessments_person_id"),
        table_name="connection_trend_assessments",
    )
    op.drop_index(
        op.f("ix_connection_trend_assessments_user_id"),
        table_name="connection_trend_assessments",
    )
    op.drop_index(
        "ix_connection_trend_assessments_user_person_assessed_at",
        table_name="connection_trend_assessments",
    )
    op.drop_table("connection_trend_assessments")
