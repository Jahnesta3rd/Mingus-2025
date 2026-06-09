"""Add dashboard checkup answer columns to life_ledger_profiles (#170)

Revision ID: 042_life_ledger_checkup_fields
Revises: 7cc4e72d6191
Create Date: 2026-06-09

All 36 nullable columns for authenticated checkup hub cards (body through
relationships). Vehicle fields live on life_ledger_profiles — no VehicleProfile.
"""

import sqlalchemy as sa
from alembic import op

revision = "042_life_ledger_checkup_fields"
down_revision = "7cc4e72d6191"
branch_labels = None
depends_on = None

_TABLE = "life_ledger_profiles"


def upgrade():
    # Card 1 — Body
    op.add_column(_TABLE, sa.Column("body_energy_rating", sa.Integer(), nullable=True))
    op.add_column(_TABLE, sa.Column("body_work_impact", sa.String(length=20), nullable=True))
    op.add_column(_TABLE, sa.Column("body_ongoing_health_cost", sa.Boolean(), nullable=True))

    # Card 2 — Mind & Mood
    op.add_column(
        _TABLE,
        sa.Column("mood_stress_triggered_purchase", sa.String(length=10), nullable=True),
    )
    op.add_column(_TABLE, sa.Column("mood_avoided_finances", sa.Boolean(), nullable=True))
    op.add_column(_TABLE, sa.Column("mood_coping_methods", sa.Text(), nullable=True))
    op.add_column(
        _TABLE,
        sa.Column("spending_intentionality_rating", sa.Integer(), nullable=True),
    )

    # Card 3 — Spirit & Calm
    op.add_column(_TABLE, sa.Column("practice_had_moments", sa.Boolean(), nullable=True))
    op.add_column(
        _TABLE,
        sa.Column("practice_affected_finances", sa.String(length=20), nullable=True),
    )
    op.add_column(
        _TABLE,
        sa.Column("spirit_financially_anxious", sa.String(length=10), nullable=True),
    )

    # Card 4 — Housing & Roof
    op.add_column(_TABLE, sa.Column("housing_stability_rating", sa.Integer(), nullable=True))
    op.add_column(_TABLE, sa.Column("housing_tenure", sa.String(length=10), nullable=True))
    op.add_column(
        _TABLE,
        sa.Column("housing_lease_end_horizon", sa.String(length=20), nullable=True),
    )
    op.add_column(_TABLE, sa.Column("housing_cost_changed", sa.String(length=15), nullable=True))
    op.add_column(
        _TABLE,
        sa.Column("housing_down_payment_status", sa.String(length=20), nullable=True),
    )
    op.add_column(_TABLE, sa.Column("housing_unexpected_cost", sa.Boolean(), nullable=True))
    op.add_column(_TABLE, sa.Column("housing_unexpected_cost_amount", sa.Float(), nullable=True))

    # Card 5 — Vehicle Health (LifeLedgerProfile only)
    op.add_column(_TABLE, sa.Column("vehicle_satisfaction_rating", sa.Integer(), nullable=True))
    op.add_column(
        _TABLE,
        sa.Column("vehicle_maintenance_confidence", sa.Integer(), nullable=True),
    )
    op.add_column(_TABLE, sa.Column("vehicle_recent_concern", sa.Boolean(), nullable=True))
    op.add_column(_TABLE, sa.Column("vehicle_concern_description", sa.Text(), nullable=True))
    op.add_column(_TABLE, sa.Column("vehicle_weekly_miles", sa.Integer(), nullable=True))
    op.add_column(
        _TABLE,
        sa.Column("vehicle_last_service_horizon", sa.String(length=15), nullable=True),
    )
    op.add_column(_TABLE, sa.Column("vehicle_insurance_known", sa.Boolean(), nullable=True))
    op.add_column(_TABLE, sa.Column("vehicle_insurance_premium", sa.Float(), nullable=True))
    op.add_column(
        _TABLE,
        sa.Column("vehicle_insurance_last_shopped", sa.String(length=15), nullable=True),
    )
    op.add_column(
        _TABLE,
        sa.Column("vehicle_decision_horizon", sa.String(length=25), nullable=True),
    )
    op.add_column(_TABLE, sa.Column("vehicle_reliability_rating", sa.Integer(), nullable=True))
    op.add_column(_TABLE, sa.Column("vehicle_value_perception", sa.Integer(), nullable=True))

    # Card 6 — Relationships
    op.add_column(
        _TABLE,
        sa.Column("relationship_friction_type", sa.String(length=20), nullable=True),
    )
    op.add_column(
        _TABLE,
        sa.Column("relationship_spending_this_week", sa.Boolean(), nullable=True),
    )
    op.add_column(_TABLE, sa.Column("relationship_spending_amount", sa.Float(), nullable=True))
    op.add_column(
        _TABLE,
        sa.Column("relationship_spending_type", sa.String(length=20), nullable=True),
    )
    op.add_column(_TABLE, sa.Column("relationship_direction", sa.String(length=20), nullable=True))
    op.add_column(
        _TABLE,
        sa.Column("relationship_cost_awareness", sa.String(length=20), nullable=True),
    )
    op.add_column(
        _TABLE,
        sa.Column("relationship_future_intention", sa.String(length=20), nullable=True),
    )


def downgrade():
    cols = [
        "body_energy_rating",
        "body_work_impact",
        "body_ongoing_health_cost",
        "mood_stress_triggered_purchase",
        "mood_avoided_finances",
        "mood_coping_methods",
        "spending_intentionality_rating",
        "practice_had_moments",
        "practice_affected_finances",
        "spirit_financially_anxious",
        "housing_stability_rating",
        "housing_tenure",
        "housing_lease_end_horizon",
        "housing_cost_changed",
        "housing_down_payment_status",
        "housing_unexpected_cost",
        "housing_unexpected_cost_amount",
        "vehicle_satisfaction_rating",
        "vehicle_maintenance_confidence",
        "vehicle_recent_concern",
        "vehicle_concern_description",
        "vehicle_weekly_miles",
        "vehicle_last_service_horizon",
        "vehicle_insurance_known",
        "vehicle_insurance_premium",
        "vehicle_insurance_last_shopped",
        "vehicle_decision_horizon",
        "vehicle_reliability_rating",
        "vehicle_value_perception",
        "relationship_friction_type",
        "relationship_spending_this_week",
        "relationship_spending_amount",
        "relationship_spending_type",
        "relationship_direction",
        "relationship_cost_awareness",
        "relationship_future_intention",
    ]
    for col in cols:
        op.drop_column(_TABLE, col)
