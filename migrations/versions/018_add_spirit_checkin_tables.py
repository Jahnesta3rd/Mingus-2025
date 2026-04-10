"""add spirit check-in, streak, and spirit-finance correlation tables

Revision ID: 018_add_spirit_checkin_tables
Revises: 017_add_life_correlation_table
Create Date: 2026-04-09

Spirit & Finance: daily practice log (one per user per day), per-user streak row,
and stored correlation/insight snapshots.
"""
from alembic import op
import sqlalchemy as sa


revision = "018_add_spirit_checkin_tables"
down_revision = "017_add_life_correlation_table"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "spirit_checkins",
        sa.Column("id", sa.Integer(), sa.Identity(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("checked_in_date", sa.Date(), nullable=False),
        sa.Column("practice_type", sa.String(length=20), nullable=False),
        sa.Column("duration_minutes", sa.Integer(), nullable=False),
        sa.Column("feeling_before", sa.Integer(), nullable=True),
        sa.Column("feeling_after", sa.Integer(), nullable=False),
        sa.Column("intention_text", sa.Text(), nullable=True),
        sa.Column("practice_score", sa.Float(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.CheckConstraint(
            "practice_type IN ('prayer', 'meditation', 'gratitude', 'affirmation')",
            name="ck_spirit_checkins_practice_type",
        ),
        sa.CheckConstraint(
            "duration_minutes IN (5, 10, 15, 20, 30)",
            name="ck_spirit_checkins_duration_minutes",
        ),
        sa.CheckConstraint(
            "feeling_before IS NULL OR (feeling_before >= 1 AND feeling_before <= 5)",
            name="ck_spirit_checkins_feeling_before",
        ),
        sa.CheckConstraint(
            "feeling_after >= 1 AND feeling_after <= 5",
            name="ck_spirit_checkins_feeling_after",
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "user_id",
            "checked_in_date",
            name="uq_spirit_checkins_user_checked_in_date",
        ),
    )
    op.create_index("ix_spirit_checkins_user_id", "spirit_checkins", ["user_id"])
    op.create_index(
        "ix_spirit_checkins_user_id_checked_in_date",
        "spirit_checkins",
        ["user_id", "checked_in_date"],
    )

    op.create_table(
        "spirit_checkin_streaks",
        sa.Column("id", sa.Integer(), sa.Identity(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column(
            "current_streak",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column(
            "longest_streak",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column("last_checkin_date", sa.Date(), nullable=True),
        sa.Column(
            "total_checkins",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", name="uq_spirit_checkin_streaks_user_id"),
    )

    op.create_table(
        "spirit_finance_correlations",
        sa.Column("id", sa.Integer(), sa.Identity(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column(
            "computed_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "weeks_analyzed",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("8"),
        ),
        sa.Column("corr_practice_savings", sa.Float(), nullable=True),
        sa.Column("corr_practice_impulse", sa.Float(), nullable=True),
        sa.Column("corr_practice_stress", sa.Float(), nullable=True),
        sa.Column("corr_practice_bills_ontime", sa.Float(), nullable=True),
        sa.Column("avg_practice_score_high_weeks", sa.Float(), nullable=True),
        sa.Column("avg_impulse_miss_days", sa.Float(), nullable=True),
        sa.Column("avg_impulse_checkin_days", sa.Float(), nullable=True),
        sa.Column("insight_summary", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_spirit_finance_correlations_user_id",
        "spirit_finance_correlations",
        ["user_id"],
    )
    op.create_index(
        "ix_spirit_finance_correlations_user_id_computed_at",
        "spirit_finance_correlations",
        ["user_id", "computed_at"],
    )


def downgrade():
    op.drop_index(
        "ix_spirit_finance_correlations_user_id_computed_at",
        table_name="spirit_finance_correlations",
    )
    op.drop_index(
        "ix_spirit_finance_correlations_user_id",
        table_name="spirit_finance_correlations",
    )
    op.drop_table("spirit_finance_correlations")
    op.drop_table("spirit_checkin_streaks")
    op.drop_index(
        "ix_spirit_checkins_user_id_checked_in_date",
        table_name="spirit_checkins",
    )
    op.drop_index("ix_spirit_checkins_user_id", table_name="spirit_checkins")
    op.drop_table("spirit_checkins")
