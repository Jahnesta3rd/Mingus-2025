"""add vibe_tracker tables

Revision ID: 016_add_vibe_tracker_tables
Revises: 015_vehicle_notes_estimated_cost
Create Date: 2026-04-08

Vibe Tracker: per-user labeled tracked people, assessment history, and trend rows.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID as PG_UUID


revision = "016_add_vibe_tracker_tables"
down_revision = "015_vehicle_notes_estimated_cost"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "vibe_tracked_people",
        sa.Column(
            "id",
            PG_UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("nickname", sa.String(length=30), nullable=False),
        sa.Column("emoji", sa.String(length=8), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("last_assessed_at", sa.DateTime(), nullable=True),
        sa.Column(
            "is_archived",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
        sa.Column("archived_at", sa.DateTime(), nullable=True),
        sa.Column(
            "assessment_count",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "user_id",
            "nickname",
            name="uq_vibe_tracked_people_user_id_nickname",
        ),
    )
    op.create_index(
        "ix_vibe_tracked_people_user_id",
        "vibe_tracked_people",
        ["user_id"],
    )
    op.create_index(
        "ix_vibe_tracked_people_user_id_is_archived",
        "vibe_tracked_people",
        ["user_id", "is_archived"],
    )

    op.create_table(
        "vibe_person_assessments",
        sa.Column(
            "id",
            PG_UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("tracked_person_id", PG_UUID(as_uuid=True), nullable=False),
        sa.Column("lead_id", PG_UUID(as_uuid=True), nullable=True),
        sa.Column("emotional_score", sa.Integer(), nullable=False),
        sa.Column("financial_score", sa.Integer(), nullable=False),
        sa.Column("verdict_label", sa.String(length=100), nullable=False),
        sa.Column("verdict_emoji", sa.String(length=8), nullable=True),
        sa.Column("annual_projection", sa.Integer(), nullable=False),
        sa.Column("answers_snapshot", sa.JSON(), nullable=False),
        sa.Column("completed_at", sa.DateTime(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(
            ["tracked_person_id"],
            ["vibe_tracked_people.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["lead_id"],
            ["vibe_checkups_leads.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_vibe_person_assessments_tracked_person_completed_at",
        "vibe_person_assessments",
        ["tracked_person_id", "completed_at"],
    )

    op.create_table(
        "vibe_person_trends",
        sa.Column(
            "id",
            PG_UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("tracked_person_id", PG_UUID(as_uuid=True), nullable=False),
        sa.Column("trend_direction", sa.String(length=20), nullable=False),
        sa.Column("emotional_delta", sa.Integer(), nullable=True),
        sa.Column("financial_delta", sa.Integer(), nullable=True),
        sa.Column("projection_delta", sa.Integer(), nullable=True),
        sa.Column(
            "assessment_count",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column("last_computed_at", sa.DateTime(), nullable=False),
        sa.Column("stay_or_go_signal", sa.String(length=20), nullable=True),
        sa.Column("stay_or_go_confidence", sa.Float(), nullable=True),
        sa.ForeignKeyConstraint(
            ["tracked_person_id"],
            ["vibe_tracked_people.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "tracked_person_id",
            name="uq_vibe_person_trends_tracked_person_id",
        ),
    )


def downgrade():
    op.drop_table("vibe_person_trends")
    op.drop_index(
        "ix_vibe_person_assessments_tracked_person_completed_at",
        table_name="vibe_person_assessments",
    )
    op.drop_table("vibe_person_assessments")
    op.drop_index(
        "ix_vibe_tracked_people_user_id_is_archived",
        table_name="vibe_tracked_people",
    )
    op.drop_index("ix_vibe_tracked_people_user_id", table_name="vibe_tracked_people")
    op.drop_table("vibe_tracked_people")
