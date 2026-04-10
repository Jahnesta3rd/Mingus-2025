"""add_vibe_checkups_tables

Revision ID: 011_add_vibe_checkups_tables
Revises: 010_beta_invite_log
Create Date: 2026-04-05

Creates tables for the Vibe Checkups anonymous quiz funnel:
- vibe_checkups_sessions
- vibe_checkups_leads
- vibe_checkups_funnel_events
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID as PG_UUID


revision = "011_add_vibe_checkups_tables"
down_revision = "010_beta_invite_log"
branch_labels = None
depends_on = None


def _uuid_pk(postgres: bool):
    if postgres:
        return sa.Column(
            "id",
            PG_UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        )
    return sa.Column("id", sa.String(length=36), primary_key=True)


def _uuid_fk(
    postgres: bool,
    name: str,
    ref_table: str,
    ondelete: str,
    nullable: bool = False,
):
    if postgres:
        return sa.Column(
            name,
            PG_UUID(as_uuid=True),
            sa.ForeignKey(f"{ref_table}.id", ondelete=ondelete),
            nullable=nullable,
        )
    return sa.Column(
        name,
        sa.String(length=36),
        sa.ForeignKey(f"{ref_table}.id", ondelete=ondelete),
        nullable=nullable,
    )


def upgrade():
    bind = op.get_bind()
    postgres = bind.dialect.name == "postgresql"

    op.create_table(
        "vibe_checkups_sessions",
        _uuid_pk(postgres),
        sa.Column("session_token", sa.String(length=255), nullable=False),
        sa.Column("answers", sa.JSON(), nullable=False),
        sa.Column("current_question", sa.Integer(), nullable=False),
        sa.Column("started_at", sa.DateTime(), nullable=False),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("ip_address", sa.String(length=45), nullable=True),
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.Column("utm_source", sa.String(length=255), nullable=True),
        sa.Column("utm_medium", sa.String(length=255), nullable=True),
        sa.Column("utm_campaign", sa.String(length=255), nullable=True),
        sa.UniqueConstraint("session_token", name="uq_vibe_checkups_sessions_session_token"),
    )
    op.create_index(
        "ix_vibe_checkups_sessions_utm_source_utm_medium",
        "vibe_checkups_sessions",
        ["utm_source", "utm_medium"],
    )

    op.create_table(
        "vibe_checkups_leads",
        _uuid_pk(postgres),
        _uuid_fk(postgres, "session_id", "vibe_checkups_sessions", "CASCADE", nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("emotional_score", sa.Integer(), nullable=False),
        sa.Column("financial_score", sa.Integer(), nullable=False),
        sa.Column("verdict_label", sa.String(length=255), nullable=False),
        sa.Column("total_annual_projection", sa.Integer(), nullable=False),
        sa.Column("projection_data", sa.JSON(), nullable=False),
        sa.Column(
            "unlocked_projection",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
        sa.Column(
            "unlock_paid",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
        sa.Column("unlock_amount_cents", sa.Integer(), nullable=True),
        sa.Column(
            "mingus_signup_clicked",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
        sa.Column(
            "mingus_converted",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column(
            "email_sequence_started",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )
    op.create_index(
        "ix_vibe_checkups_leads_session_id",
        "vibe_checkups_leads",
        ["session_id"],
    )
    op.create_index(
        "ix_vibe_checkups_leads_email",
        "vibe_checkups_leads",
        ["email"],
    )
    op.create_index(
        "ix_vibe_checkups_leads_created_at",
        "vibe_checkups_leads",
        ["created_at"],
    )

    op.create_table(
        "vibe_checkups_funnel_events",
        _uuid_pk(postgres),
        _uuid_fk(
            postgres, "session_id", "vibe_checkups_sessions", "SET NULL", nullable=True
        ),
        _uuid_fk(postgres, "lead_id", "vibe_checkups_leads", "SET NULL", nullable=True),
        sa.Column("event_type", sa.String(length=64), nullable=False),
        sa.Column("event_data", sa.JSON(), nullable=True),
        sa.Column("occurred_at", sa.DateTime(), nullable=False),
        sa.Column("utm_source", sa.String(length=255), nullable=True),
        sa.Column("utm_medium", sa.String(length=255), nullable=True),
    )
    op.create_index(
        "ix_vibe_checkups_funnel_events_session_id",
        "vibe_checkups_funnel_events",
        ["session_id"],
    )
    op.create_index(
        "ix_vibe_checkups_funnel_events_lead_id",
        "vibe_checkups_funnel_events",
        ["lead_id"],
    )
    op.create_index(
        "ix_vibe_checkups_funnel_events_event_type",
        "vibe_checkups_funnel_events",
        ["event_type"],
    )


def downgrade():
    op.drop_index(
        "ix_vibe_checkups_funnel_events_event_type",
        table_name="vibe_checkups_funnel_events",
    )
    op.drop_index(
        "ix_vibe_checkups_funnel_events_lead_id",
        table_name="vibe_checkups_funnel_events",
    )
    op.drop_index(
        "ix_vibe_checkups_funnel_events_session_id",
        table_name="vibe_checkups_funnel_events",
    )
    op.drop_table("vibe_checkups_funnel_events")

    op.drop_index("ix_vibe_checkups_leads_created_at", table_name="vibe_checkups_leads")
    op.drop_index("ix_vibe_checkups_leads_email", table_name="vibe_checkups_leads")
    op.drop_index("ix_vibe_checkups_leads_session_id", table_name="vibe_checkups_leads")
    op.drop_table("vibe_checkups_leads")

    op.drop_index(
        "ix_vibe_checkups_sessions_utm_source_utm_medium",
        table_name="vibe_checkups_sessions",
    )
    op.drop_table("vibe_checkups_sessions")
