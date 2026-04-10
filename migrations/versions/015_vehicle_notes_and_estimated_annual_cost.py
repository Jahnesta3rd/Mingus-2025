"""vehicles.notes and vehicles.estimated_annual_cost for assessment placeholder rows

Revision ID: 015_vehicle_notes_estimated_cost
Revises: 014_recurring_expense_source_relationship
Create Date: 2026-04-08
"""
from alembic import op
import sqlalchemy as sa


revision = "015_vehicle_notes_estimated_cost"
down_revision = "014_recurring_expense_source_relationship"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("vehicles", sa.Column("notes", sa.Text(), nullable=True))
    op.add_column(
        "vehicles",
        sa.Column("estimated_annual_cost", sa.Integer(), nullable=True),
    )


def downgrade():
    op.drop_column("vehicles", "estimated_annual_cost")
    op.drop_column("vehicles", "notes")
