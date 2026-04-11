"""add user_alerts for vibe/financial notifications

Revision ID: 022_add_user_alerts
Revises: 021_add_connection_trend
Create Date: 2026-04-11

Stores dismissible dashboard alerts (vibe drop, connection trend warning, savings drag).
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID as PG_UUID


revision = "022_add_user_alerts"
down_revision = "021_add_connection_trend"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "user_alerts",
        sa.Column(
            "id",
            PG_UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("alert_type", sa.String(length=50), nullable=False),
        sa.Column("severity", sa.String(length=20), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("action_label", sa.String(length=100), nullable=False),
        sa.Column("action_route", sa.String(length=255), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("read_at", sa.DateTime(), nullable=True),
        sa.Column("dismissed_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_user_alerts_user_id_read_at",
        "user_alerts",
        ["user_id", "read_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_user_alerts_user_id"),
        "user_alerts",
        ["user_id"],
        unique=False,
    )


def downgrade():
    op.drop_index(op.f("ix_user_alerts_user_id"), table_name="user_alerts")
    op.drop_index("ix_user_alerts_user_id_read_at", table_name="user_alerts")
    op.drop_table("user_alerts")
