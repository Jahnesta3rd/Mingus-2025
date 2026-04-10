"""add income_streams and schedule_recurring_expenses for cash forecast scheduling

Revision ID: 015_add_transaction_schedule
Revises: 019_add_spirit_notification_prefs
Create Date: 2026-04-10

Scheduled take-home income and recurring outflows with next occurrence dates.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID as PG_UUID


revision = "015_add_transaction_schedule"
down_revision = "019_add_spirit_notification_prefs"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "income_streams",
        sa.Column(
            "id",
            PG_UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("label", sa.String(length=100), nullable=False),
        sa.Column("amount", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("frequency", sa.String(length=20), nullable=False),
        sa.Column("next_date", sa.Date(), nullable=False),
        sa.Column(
            "income_type",
            sa.String(length=30),
            nullable=False,
            server_default="earned",
        ),
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
        ),
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
        "ix_income_streams_user_id",
        "income_streams",
        ["user_id"],
    )
    op.create_index(
        "ix_income_streams_user_id_is_active",
        "income_streams",
        ["user_id", "is_active"],
    )

    op.create_table(
        "schedule_recurring_expenses",
        sa.Column(
            "id",
            PG_UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("label", sa.String(length=100), nullable=False),
        sa.Column("amount", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("category", sa.String(length=50), nullable=False),
        sa.Column("frequency", sa.String(length=20), nullable=False),
        sa.Column("due_day", sa.Integer(), nullable=False),
        sa.Column("next_date", sa.Date(), nullable=False),
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
        ),
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
        "ix_schedule_recurring_expenses_user_id",
        "schedule_recurring_expenses",
        ["user_id"],
    )
    op.create_index(
        "ix_schedule_recurring_expenses_user_id_is_active",
        "schedule_recurring_expenses",
        ["user_id", "is_active"],
    )


def downgrade():
    op.drop_index(
        "ix_schedule_recurring_expenses_user_id_is_active",
        table_name="schedule_recurring_expenses",
    )
    op.drop_index(
        "ix_schedule_recurring_expenses_user_id",
        table_name="schedule_recurring_expenses",
    )
    op.drop_table("schedule_recurring_expenses")
    op.drop_index(
        "ix_income_streams_user_id_is_active",
        table_name="income_streams",
    )
    op.drop_index("ix_income_streams_user_id", table_name="income_streams")
    op.drop_table("income_streams")
