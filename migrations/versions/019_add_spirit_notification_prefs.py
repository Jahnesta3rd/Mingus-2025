"""add spirit notification prefs and in-app notifications

Revision ID: 019_add_spirit_notification_prefs
Revises: 018_add_spirit_checkin_tables
Create Date: 2026-04-09

Per-user Spirit & Finance practice reminder preferences (schedule + nudges).
"""
from alembic import op
import sqlalchemy as sa


revision = "019_add_spirit_notification_prefs"
down_revision = "018_add_spirit_checkin_tables"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "spirit_notification_prefs",
        sa.Column("id", sa.Integer(), sa.Identity(always=False), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column(
            "reminders_enabled",
            sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
        ),
        sa.Column("reminder_hour", sa.Integer(), nullable=False, server_default=sa.text("8")),
        sa.Column(
            "reminder_timezone",
            sa.String(length=50),
            nullable=False,
            server_default="America/New_York",
        ),
        sa.Column(
            "reminder_days",
            sa.String(length=50),
            nullable=False,
            server_default="mon,tue,wed,thu,fri,sat,sun",
        ),
        sa.Column(
            "streak_nudge_enabled",
            sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
        ),
        sa.Column("last_reminder_sent", sa.DateTime(), nullable=True),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", name="uq_spirit_notification_prefs_user_id"),
    )
    op.create_index(
        "ix_spirit_notification_prefs_reminders_enabled",
        "spirit_notification_prefs",
        ["reminders_enabled"],
        unique=False,
    )

    op.create_table(
        "in_app_notifications",
        sa.Column("id", sa.Integer(), sa.Identity(always=False), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("category", sa.String(length=64), nullable=True),
        sa.Column("read_at", sa.DateTime(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_in_app_notifications_user_id",
        "in_app_notifications",
        ["user_id"],
        unique=False,
    )
    op.create_index(
        "ix_in_app_notifications_user_created",
        "in_app_notifications",
        ["user_id", "created_at"],
        unique=False,
    )


def downgrade():
    op.drop_index("ix_in_app_notifications_user_created", table_name="in_app_notifications")
    op.drop_index("ix_in_app_notifications_user_id", table_name="in_app_notifications")
    op.drop_table("in_app_notifications")
    op.drop_index(
        "ix_spirit_notification_prefs_reminders_enabled",
        table_name="spirit_notification_prefs",
    )
    op.drop_table("spirit_notification_prefs")
