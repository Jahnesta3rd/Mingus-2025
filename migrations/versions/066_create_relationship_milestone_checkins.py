"""Create relationship milestone check-ins table.

Revision ID: 066_create_relationship_milestone_checkins
Revises: 065_create_lease_break_analyses
Create Date: 2026-07-08

Monthly readiness gates and emergency exit triggers for relationship safety.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID


revision = "066_create_relationship_milestone_checkins"
down_revision = "065_create_lease_break_analyses"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "relationship_milestone_checkins",
        sa.Column(
            "id",
            PG_UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("person_id", PG_UUID(as_uuid=True), nullable=False),
        sa.Column("vibe_trend", sa.String(length=20), nullable=False),
        sa.Column("feels_safe", sa.String(length=10), nullable=False),
        sa.Column(
            "needs_to_leave_sooner",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column(
            "on_track_savings",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column(
            "prefer_leave_now",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("emergency_flags", JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("next_steps", JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("resources_provided", JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["person_id"], ["vibe_tracked_people.id"], ondelete="CASCADE"),
        sa.UniqueConstraint(
            "user_id",
            "person_id",
            "created_at",
            name="uq_milestone_checkin",
        ),
    )
    op.create_index(
        "ix_milestone_user_person",
        "relationship_milestone_checkins",
        ["user_id", "person_id"],
    )
    op.create_index(
        "ix_milestone_emergency",
        "relationship_milestone_checkins",
        ["status"],
    )


def downgrade():
    op.drop_index("ix_milestone_emergency", table_name="relationship_milestone_checkins")
    op.drop_index("ix_milestone_user_person", table_name="relationship_milestone_checkins")
    op.drop_table("relationship_milestone_checkins")
