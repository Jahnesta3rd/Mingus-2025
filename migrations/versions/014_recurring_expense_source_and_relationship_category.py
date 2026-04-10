"""recurring_expenses.source and relationship category

Revision ID: 014_recurring_expense_source_relationship
Revises: 013_add_life_ledger_tables
Create Date: 2026-04-08

Adds optional import source for recurring expenses and allows category 'relationship'
(Vibe Checkups → Life Ledger budget line).
"""
from alembic import op
import sqlalchemy as sa


revision = "014_recurring_expense_source_relationship"
down_revision = "013_add_life_ledger_tables"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "recurring_expenses",
        sa.Column("source", sa.String(length=64), nullable=True),
    )
    op.create_index(
        "ix_recurring_expenses_user_source",
        "recurring_expenses",
        ["user_id", "source"],
        unique=False,
    )
    op.drop_constraint("ck_recurring_expenses_category", "recurring_expenses", type_="check")
    op.create_check_constraint(
        "ck_recurring_expenses_category",
        "recurring_expenses",
        "category IN ("
        "'housing', 'transportation', 'insurance', 'debt', 'subscription', "
        "'utilities', 'other', 'relationship'"
        ")",
    )


def downgrade():
    op.drop_constraint("ck_recurring_expenses_category", "recurring_expenses", type_="check")
    op.create_check_constraint(
        "ck_recurring_expenses_category",
        "recurring_expenses",
        "category IN ("
        "'housing', 'transportation', 'insurance', 'debt', 'subscription', "
        "'utilities', 'other'"
        ")",
    )
    op.drop_index("ix_recurring_expenses_user_source", table_name="recurring_expenses")
    op.drop_column("recurring_expenses", "source")
