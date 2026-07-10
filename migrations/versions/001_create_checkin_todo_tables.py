"""Create Todo table and add WeeklyCheckin wisdom/financial columns.

Revision ID: 001_create_checkin_todo_tables
Revises: 072_add_tier2_reminder_fields
Create Date: 2026-07-10

- Adds spending_delta_from_baseline, unusual_spending_detected, and wisdom_call_*
  columns to weekly_checkins (base table from 006 / unified fields from 043).
- Unique constraint on (user_id, week_number).
- Creates todos table.
- wisdom_call_audio_url remains nullable (NULL until Phase 5).
"""
from alembic import op
import sqlalchemy as sa


revision = "001_create_checkin_todo_tables"
down_revision = "072_add_tier2_reminder_fields"
branch_labels = None
depends_on = None

_WEEKLY_CHECKINS = "weekly_checkins"

_NEW_WEEKLY_COLUMNS = [
    ("spending_delta_from_baseline", sa.Float(), True, None),
    ("unusual_spending_detected", sa.Boolean(), False, sa.text("false")),
    ("wisdom_call_script", sa.Text(), True, None),
    ("wisdom_call_audio_url", sa.String(512), True, None),
    ("wisdom_call_sent_at", sa.DateTime(), True, None),
    ("wisdom_call_listened_at", sa.DateTime(), True, None),
]


def upgrade():
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = set(inspector.get_table_names())

    # --- weekly_checkins: new financial + wisdom call columns ---
    if _WEEKLY_CHECKINS in existing_tables:
        existing_cols = {c["name"] for c in inspector.get_columns(_WEEKLY_CHECKINS)}
        for name, col_type, nullable, server_default in _NEW_WEEKLY_COLUMNS:
            if name in existing_cols:
                continue
            kwargs = {"nullable": nullable}
            if server_default is not None:
                kwargs["server_default"] = server_default
            op.add_column(_WEEKLY_CHECKINS, sa.Column(name, col_type, **kwargs))

        existing_uniques = {
            u["name"] for u in inspector.get_unique_constraints(_WEEKLY_CHECKINS)
        }
        if "uq_weekly_checkins_user_week_number" not in existing_uniques:
            op.create_unique_constraint(
                "uq_weekly_checkins_user_week_number",
                _WEEKLY_CHECKINS,
                ["user_id", "week_number"],
            )

        existing_indexes = {i["name"] for i in inspector.get_indexes(_WEEKLY_CHECKINS)}
        if "idx_weekly_checkins_week_number" not in existing_indexes:
            op.create_index(
                "idx_weekly_checkins_week_number",
                _WEEKLY_CHECKINS,
                ["week_number"],
            )
        if "idx_weekly_checkins_user_id" not in existing_indexes:
            op.create_index(
                "idx_weekly_checkins_user_id",
                _WEEKLY_CHECKINS,
                ["user_id"],
            )
    else:
        # Fresh DB: create full weekly_checkins table matching the model
        op.create_table(
            _WEEKLY_CHECKINS,
            sa.Column("id", sa.Uuid(), primary_key=True),
            sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
            sa.Column("week_ending_date", sa.Date(), nullable=False),
            sa.Column("week_number", sa.Integer(), nullable=True),
            sa.Column("year", sa.Integer(), nullable=True),
            sa.Column("exercise_days", sa.Integer(), nullable=True),
            sa.Column("exercise_intensity", sa.String(10), nullable=True),
            sa.Column("sleep_quality", sa.Integer(), nullable=True),
            sa.Column("sleep_hours", sa.Float(), nullable=True),
            sa.Column("meditation_minutes", sa.Integer(), nullable=True),
            sa.Column("stress_level", sa.Integer(), nullable=True),
            sa.Column("overall_mood", sa.Integer(), nullable=True),
            sa.Column("relationship_satisfaction", sa.Integer(), nullable=True),
            sa.Column("social_interactions", sa.Integer(), nullable=True),
            sa.Column("financial_stress", sa.Integer(), nullable=True),
            sa.Column("spending_control", sa.Integer(), nullable=True),
            sa.Column("groceries_estimate", sa.Numeric(10, 2), nullable=True),
            sa.Column("dining_estimate", sa.Numeric(10, 2), nullable=True),
            sa.Column("entertainment_estimate", sa.Numeric(10, 2), nullable=True),
            sa.Column("shopping_estimate", sa.Numeric(10, 2), nullable=True),
            sa.Column("transport_estimate", sa.Numeric(10, 2), nullable=True),
            sa.Column("utilities_estimate", sa.Numeric(10, 2), nullable=True),
            sa.Column("other_estimate", sa.Numeric(10, 2), nullable=True),
            sa.Column("impulse_spending", sa.Numeric(10, 2), nullable=True),
            sa.Column("stress_spending", sa.Numeric(10, 2), nullable=True),
            sa.Column("celebration_spending", sa.Numeric(10, 2), nullable=True),
            sa.Column("had_impulse_purchases", sa.Boolean(), nullable=False, server_default=sa.text("false")),
            sa.Column("had_stress_purchases", sa.Boolean(), nullable=False, server_default=sa.text("false")),
            sa.Column("biggest_unnecessary_purchase", sa.Numeric(10, 2), nullable=True),
            sa.Column("biggest_unnecessary_category", sa.String(50), nullable=True),
            sa.Column("wins", sa.Text(), nullable=True),
            sa.Column("challenges", sa.Text(), nullable=True),
            sa.Column("mood_rating", sa.Integer(), nullable=True),
            sa.Column("activity_frequency", sa.Integer(), nullable=True),
            sa.Column("body_score", sa.Integer(), nullable=True),
            sa.Column("avg_sleep_hours", sa.Float(), nullable=True),
            sa.Column("rest_quality", sa.Integer(), nullable=True),
            sa.Column("relationship_temperature", sa.Integer(), nullable=True),
            sa.Column("meaningful_time_with_people", sa.Boolean(), nullable=True),
            sa.Column("primary_partner_rating", sa.Integer(), nullable=True),
            sa.Column("financial_convo_with_partner", sa.Boolean(), nullable=True),
            sa.Column("financial_communication_with_partner", sa.Integer(), nullable=True),
            sa.Column("parenting_stress", sa.Integer(), nullable=True),
            sa.Column("unexpected_kid_spending", sa.Boolean(), nullable=True),
            sa.Column("unexpected_kid_amount", sa.Float(), nullable=True),
            sa.Column("meditation_minutes_total", sa.Integer(), nullable=True),
            sa.Column("practice_felt_grounding", sa.Boolean(), nullable=True),
            sa.Column("felt_spiritual_connection", sa.Boolean(), nullable=True),
            sa.Column("spiritual_connection_rating", sa.Integer(), nullable=True),
            sa.Column("spending_discipline_rating", sa.Integer(), nullable=True),
            sa.Column("discretionary_spending", sa.Numeric(10, 2), nullable=True),
            sa.Column("social_spending_unplanned", sa.Boolean(), nullable=True),
            sa.Column("social_spending_amount", sa.Numeric(10, 2), nullable=True),
            sa.Column("partner_spending_unplanned", sa.Boolean(), nullable=True),
            sa.Column("partner_spending_amount", sa.Numeric(10, 2), nullable=True),
            sa.Column("kids_spending_total", sa.Numeric(10, 2), nullable=True),
            sa.Column("kids_spending_unplanned", sa.Numeric(10, 2), nullable=True),
            sa.Column("financial_reflection", sa.Text(), nullable=True),
            sa.Column("spending_trigger_description", sa.Text(), nullable=True),
            sa.Column("weekly_reflection_change", sa.Text(), nullable=True),
            sa.Column("spending_delta_from_baseline", sa.Float(), nullable=True),
            sa.Column("unusual_spending_detected", sa.Boolean(), nullable=False, server_default=sa.text("false")),
            sa.Column("wisdom_call_script", sa.Text(), nullable=True),
            sa.Column("wisdom_call_audio_url", sa.String(512), nullable=True),
            sa.Column("wisdom_call_sent_at", sa.DateTime(), nullable=True),
            sa.Column("wisdom_call_listened_at", sa.DateTime(), nullable=True),
            sa.Column("completed_at", sa.DateTime(), nullable=True),
            sa.Column("completion_time_seconds", sa.Integer(), nullable=True),
            sa.Column("reminder_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
            sa.UniqueConstraint("user_id", "week_number", name="uq_weekly_checkins_user_week_number"),
            sa.UniqueConstraint("user_id", "week_ending_date", name="uq_weekly_checkins_user_week"),
        )
        op.create_index("idx_weekly_checkins_user_id", _WEEKLY_CHECKINS, ["user_id"])
        op.create_index("idx_weekly_checkins_week_number", _WEEKLY_CHECKINS, ["week_number"])
        op.create_index("idx_weekly_checkins_week_ending_date", _WEEKLY_CHECKINS, ["week_ending_date"])
        op.create_index("idx_weekly_checkins_user_week", _WEEKLY_CHECKINS, ["user_id", "week_ending_date"])

    # --- todos ---
    if "todos" not in existing_tables:
        op.create_table(
            "todos",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column(
                "user_id",
                sa.Integer(),
                sa.ForeignKey("users.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column("title", sa.String(255), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
            sa.Column("priority", sa.String(20), nullable=False, server_default="medium"),
            sa.Column("domain", sa.String(50), nullable=True),
            sa.Column("week_created", sa.Integer(), nullable=True),
            sa.Column("due_date", sa.Date(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
            sa.Column("completed_at", sa.DateTime(), nullable=True),
        )
        op.create_index("ix_todos_user_id", "todos", ["user_id"])
        op.create_index("ix_todos_week_created", "todos", ["week_created"])
        op.create_index("ix_todos_user_id_status", "todos", ["user_id", "status"])
        op.create_index("ix_todos_user_id_week_created", "todos", ["user_id", "week_created"])


def downgrade():
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = set(inspector.get_table_names())

    if "todos" in existing_tables:
        op.drop_index("ix_todos_user_id_week_created", table_name="todos")
        op.drop_index("ix_todos_user_id_status", table_name="todos")
        op.drop_index("ix_todos_week_created", table_name="todos")
        op.drop_index("ix_todos_user_id", table_name="todos")
        op.drop_table("todos")

    if _WEEKLY_CHECKINS not in existing_tables:
        return

    existing_uniques = {
        u["name"] for u in inspector.get_unique_constraints(_WEEKLY_CHECKINS)
    }
    if "uq_weekly_checkins_user_week_number" in existing_uniques:
        op.drop_constraint(
            "uq_weekly_checkins_user_week_number",
            _WEEKLY_CHECKINS,
            type_="unique",
        )

    existing_cols = {c["name"] for c in inspector.get_columns(_WEEKLY_CHECKINS)}
    for name, _, _, _ in reversed(_NEW_WEEKLY_COLUMNS):
        if name in existing_cols:
            op.drop_column(_WEEKLY_CHECKINS, name)
