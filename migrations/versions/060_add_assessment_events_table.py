"""Add assessment_events table and assessments.email_plain for follow-ups.

Revision ID: 060_add_assessment_events
Revises: 059_add_assessment_tokens
Create Date: 2026-07-02

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "060_add_assessment_events"
down_revision = "059_add_assessment_tokens"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "assessment_events",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("assessment_id", sa.Integer(), nullable=False),
        sa.Column("email_hash", sa.String(length=255), nullable=False),
        sa.Column("event_type", sa.String(length=50), nullable=False),
        sa.Column("token", sa.String(length=255), nullable=True),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_assessment_events_assessment_id"),
        "assessment_events",
        ["assessment_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_assessment_events_email_hash"),
        "assessment_events",
        ["email_hash"],
        unique=False,
    )
    op.create_index(
        op.f("ix_assessment_events_event_type"),
        "assessment_events",
        ["event_type"],
        unique=False,
    )

    op.add_column(
        "assessments",
        sa.Column("email_plain", sa.String(length=255), nullable=True),
    )


def downgrade():
    op.drop_column("assessments", "email_plain")
    op.drop_index(op.f("ix_assessment_events_event_type"), table_name="assessment_events")
    op.drop_index(op.f("ix_assessment_events_email_hash"), table_name="assessment_events")
    op.drop_index(op.f("ix_assessment_events_assessment_id"), table_name="assessment_events")
    op.drop_table("assessment_events")
