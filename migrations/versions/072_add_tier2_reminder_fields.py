"""Add Tier 2 reminder tracking fields to BTS sessions (BTS8).

Revision ID: 072_add_tier2_reminder_fields
Revises: 071_create_bts_job_commitments
Create Date: 2026-07-10
"""

from alembic import op
import sqlalchemy as sa


revision = "072_add_tier2_reminder_fields"
down_revision = "071_create_bts_job_commitments"
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    existing = {
        c["name"] for c in sa.inspect(conn).get_columns("back_to_school_sessions")
    }

    if "tier1_purchased_at" not in existing:
        op.add_column(
            "back_to_school_sessions",
            sa.Column("tier1_purchased_at", sa.DateTime(), nullable=True),
        )
    if "tier2_reminder_sent" not in existing:
        op.add_column(
            "back_to_school_sessions",
            sa.Column(
                "tier2_reminder_sent",
                sa.Boolean(),
                nullable=False,
                server_default=sa.text("false"),
            ),
        )
    if "tier2_reminder_sent_at" not in existing:
        op.add_column(
            "back_to_school_sessions",
            sa.Column("tier2_reminder_sent_at", sa.DateTime(), nullable=True),
        )
    if "tier2_reminder_dismissed" not in existing:
        op.add_column(
            "back_to_school_sessions",
            sa.Column(
                "tier2_reminder_dismissed",
                sa.Boolean(),
                nullable=False,
                server_default=sa.text("false"),
            ),
        )


def downgrade():
    conn = op.get_bind()
    existing = {
        c["name"] for c in sa.inspect(conn).get_columns("back_to_school_sessions")
    }
    for col in (
        "tier2_reminder_dismissed",
        "tier2_reminder_sent_at",
        "tier2_reminder_sent",
        "tier1_purchased_at",
    ):
        if col in existing:
            op.drop_column("back_to_school_sessions", col)
