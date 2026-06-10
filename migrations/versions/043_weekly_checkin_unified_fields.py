"""Weekly check-in unified fields + checkin_question_log (#176)

Revision ID: 043_weekly_checkin_unified
Revises: 042_life_ledger_checkup_fields
Create Date: 2026-06-09

Adds nullable unified check-in columns to weekly_checkins (does not rename/drop
existing columns). Adds spending_discipline_rating alongside spending_control.
Creates checkin_question_log for rotating question tracking.
"""
from alembic import op
import sqlalchemy as sa


revision = "043_weekly_checkin_unified"
down_revision = "042_life_ledger_checkup_fields"
branch_labels = None
depends_on = None

_WEEKLY_CHECKINS = "weekly_checkins"

# All new WeeklyCheckin columns (stress_level already exists — not included)
_NEW_WEEKLY_COLUMNS = [
    ("week_number", sa.Integer()),
    ("year", sa.Integer()),
    ("mood_rating", sa.Integer()),
    ("activity_frequency", sa.Integer()),
    ("body_score", sa.Integer()),
    ("avg_sleep_hours", sa.Float()),
    ("rest_quality", sa.Integer()),
    ("relationship_temperature", sa.Integer()),
    ("meaningful_time_with_people", sa.Boolean()),
    ("primary_partner_rating", sa.Integer()),
    ("financial_convo_with_partner", sa.Boolean()),
    ("financial_communication_with_partner", sa.Integer()),
    ("parenting_stress", sa.Integer()),
    ("unexpected_kid_spending", sa.Boolean()),
    ("unexpected_kid_amount", sa.Float()),
    ("meditation_minutes_total", sa.Integer()),
    ("practice_felt_grounding", sa.Boolean()),
    ("felt_spiritual_connection", sa.Boolean()),
    ("spiritual_connection_rating", sa.Integer()),
    ("spending_discipline_rating", sa.Integer()),
    ("discretionary_spending", sa.Numeric(10, 2)),
    ("social_spending_unplanned", sa.Boolean()),
    ("social_spending_amount", sa.Numeric(10, 2)),
    ("partner_spending_unplanned", sa.Boolean()),
    ("partner_spending_amount", sa.Numeric(10, 2)),
    ("kids_spending_total", sa.Numeric(10, 2)),
    ("kids_spending_unplanned", sa.Numeric(10, 2)),
    ("financial_reflection", sa.Text()),
    ("spending_trigger_description", sa.Text()),
    ("weekly_reflection_change", sa.Text()),
]


def upgrade():
    for name, col_type in _NEW_WEEKLY_COLUMNS:
        op.add_column(_WEEKLY_CHECKINS, sa.Column(name, col_type, nullable=True))

    op.create_index("idx_weekly_checkins_week_number", _WEEKLY_CHECKINS, ["week_number"])
    op.create_index("idx_weekly_checkins_year", _WEEKLY_CHECKINS, ["year"])
    op.create_index(
        "idx_weekly_checkins_user_week_year",
        _WEEKLY_CHECKINS,
        ["user_id", "week_number", "year"],
    )

    op.create_table(
        "checkin_question_log",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("question_id", sa.String(20), nullable=False),
        sa.Column("week_number", sa.Integer(), nullable=False),
        sa.Column("year", sa.Integer(), nullable=False),
        sa.Column("answer", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
    )
    op.create_index("idx_checkin_question_log_user_id", "checkin_question_log", ["user_id"])
    op.create_index(
        "idx_checkin_question_log_user_question",
        "checkin_question_log",
        ["user_id", "question_id"],
    )
    op.create_index(
        "idx_checkin_question_log_user_week_year",
        "checkin_question_log",
        ["user_id", "week_number", "year"],
    )
    op.create_unique_constraint(
        "uq_checkin_question_log_user_q_week",
        "checkin_question_log",
        ["user_id", "question_id", "week_number", "year"],
    )


def downgrade():
    op.drop_constraint("uq_checkin_question_log_user_q_week", "checkin_question_log", type_="unique")
    op.drop_index("idx_checkin_question_log_user_week_year", table_name="checkin_question_log")
    op.drop_index("idx_checkin_question_log_user_question", table_name="checkin_question_log")
    op.drop_index("idx_checkin_question_log_user_id", table_name="checkin_question_log")
    op.drop_table("checkin_question_log")

    op.drop_index("idx_weekly_checkins_user_week_year", table_name=_WEEKLY_CHECKINS)
    op.drop_index("idx_weekly_checkins_year", table_name=_WEEKLY_CHECKINS)
    op.drop_index("idx_weekly_checkins_week_number", table_name=_WEEKLY_CHECKINS)

    for name, _ in reversed(_NEW_WEEKLY_COLUMNS):
        op.drop_column(_WEEKLY_CHECKINS, name)
