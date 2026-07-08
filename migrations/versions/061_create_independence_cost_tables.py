"""061_create_independence_cost_tables

Revision ID: 061_create_independence_cost_tables
Revises: 060_add_assessment_events
Create Date: 2026-07-08

Independence cost calculator: per-person assessment history with monthly and startup costs.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID as PG_UUID


revision = "061_create_independence_cost_tables"
down_revision = "060_add_assessment_events"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "independence_cost_assessments",
        sa.Column(
            "id",
            PG_UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("person_id", PG_UUID(as_uuid=True), nullable=False),
        sa.Column(
            "assessment_date",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("zip_code", sa.String(length=5), nullable=True),
        sa.Column("city_name", sa.String(length=100), nullable=True),
        sa.Column("market_rent_1br", sa.Numeric(8, 2), nullable=True),
        sa.Column("estimated_housing", sa.Numeric(8, 2), nullable=False),
        sa.Column("estimated_utilities", sa.Numeric(8, 2), nullable=False),
        sa.Column("estimated_food", sa.Numeric(8, 2), nullable=False),
        sa.Column("estimated_transportation", sa.Numeric(8, 2), nullable=False),
        sa.Column("estimated_phone_internet", sa.Numeric(8, 2), nullable=False),
        sa.Column("estimated_other", sa.Numeric(8, 2), nullable=False),
        sa.Column("total_monthly_solo", sa.Numeric(8, 2), nullable=False),
        sa.Column("startup_moving", sa.Numeric(8, 2), nullable=True),
        sa.Column("startup_utilities_deposits", sa.Numeric(8, 2), nullable=True),
        sa.Column("startup_rental_deposits", sa.Numeric(8, 2), nullable=True),
        sa.Column("startup_phone_internet", sa.Numeric(8, 2), nullable=True),
        sa.Column("startup_furniture_basics", sa.Numeric(8, 2), nullable=True),
        sa.Column("startup_kitchen_appliances", sa.Numeric(8, 2), nullable=True),
        sa.Column("startup_household_items", sa.Numeric(8, 2), nullable=True),
        sa.Column("startup_transportation_car", sa.Numeric(8, 2), nullable=True),
        sa.Column("startup_car_insurance_deposit", sa.Numeric(8, 2), nullable=True),
        sa.Column("startup_registration", sa.Numeric(8, 2), nullable=True),
        sa.Column("startup_car_maintenance_fund", sa.Numeric(8, 2), nullable=True),
        sa.Column("startup_emergency_fund", sa.Numeric(8, 2), nullable=True),
        sa.Column("total_startup_cost", sa.Numeric(10, 2), nullable=True),
        sa.Column("current_housing_contribution", sa.Numeric(8, 2), nullable=True),
        sa.Column("monthly_independence_gap", sa.Numeric(8, 2), nullable=True),
        sa.Column("months_to_save_startup", sa.Numeric(8, 2), nullable=True),
        sa.Column("partner_emotional_score_current", sa.Integer(), nullable=True),
        sa.Column("partner_emotional_trend", sa.String(length=30), nullable=True),
        sa.Column("emotional_score_week_1", sa.Integer(), nullable=True),
        sa.Column("emotional_score_week_2", sa.Integer(), nullable=True),
        sa.Column("emotional_score_week_3", sa.Integer(), nullable=True),
        sa.Column("emotional_score_week_4", sa.Integer(), nullable=True),
        sa.Column("emotional_score_week_5", sa.Integer(), nullable=True),
        sa.Column("emotional_score_week_6", sa.Integer(), nullable=True),
        sa.Column("emotional_score_week_7", sa.Integer(), nullable=True),
        sa.Column("emotional_score_week_8", sa.Integer(), nullable=True),
        sa.Column("emotional_score_week_9", sa.Integer(), nullable=True),
        sa.Column("emotional_score_week_10", sa.Integer(), nullable=True),
        sa.Column("emotional_score_week_11", sa.Integer(), nullable=True),
        sa.Column("emotional_score_week_12", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["person_id"], ["vibe_tracked_people.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "user_id",
            "person_id",
            "assessment_date",
            name="uq_icc_user_person_date",
        ),
    )
    op.create_index(
        "ix_independence_cost_assessments_user_id",
        "independence_cost_assessments",
        ["user_id"],
    )
    op.create_index(
        "ix_independence_cost_assessments_person_id",
        "independence_cost_assessments",
        ["person_id"],
    )
    op.create_index(
        "ix_icc_user_created",
        "independence_cost_assessments",
        ["user_id", "created_at"],
    )


def downgrade():
    op.drop_index("ix_icc_user_created", table_name="independence_cost_assessments")
    op.drop_index(
        "ix_independence_cost_assessments_person_id",
        table_name="independence_cost_assessments",
    )
    op.drop_index(
        "ix_independence_cost_assessments_user_id",
        table_name="independence_cost_assessments",
    )
    op.drop_table("independence_cost_assessments")
