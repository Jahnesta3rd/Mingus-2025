"""beta_invite_log for batched beta email invites

Revision ID: 010_beta_invite_log
Revises: 009_perf_monitoring
Create Date: 2026-03-30
"""
from alembic import op
import sqlalchemy as sa

revision = "010_beta_invite_log"
down_revision = "009_perf_monitoring"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "beta_invite_log",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("first_name", sa.String(length=120), nullable=True),
        sa.Column("code", sa.String(length=20), nullable=False),
        sa.Column("wave_label", sa.String(length=64), nullable=False),
        sa.Column("sent_at", sa.DateTime(), nullable=True),
        sa.Column(
            "status",
            sa.String(length=20),
            nullable=False,
            server_default="queued",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_beta_invite_log_email"), "beta_invite_log", ["email"], unique=False
    )
    op.create_index(
        op.f("ix_beta_invite_log_wave_label"),
        "beta_invite_log",
        ["wave_label"],
        unique=False,
    )


def downgrade():
    op.drop_index(op.f("ix_beta_invite_log_wave_label"), table_name="beta_invite_log")
    op.drop_index(op.f("ix_beta_invite_log_email"), table_name="beta_invite_log")
    op.drop_table("beta_invite_log")
