"""Decision 4: expand recurring_expenses category check for GC2 categories

Revision ID: 030_recurring_expense_category_gc2
Revises: 029_housing_profile_table
Create Date: 2026-04-18
"""

from alembic import op


revision = "030_recurring_expense_category_gc2"
down_revision = "029_housing_profile_table"
branch_labels = None
depends_on = None


def upgrade():
    op.drop_constraint("ck_recurring_expenses_category", "recurring_expenses", type_="check")
    op.create_check_constraint(
        "ck_recurring_expenses_category",
        "recurring_expenses",
        "category IN ("
        "'housing', 'transportation', 'insurance', 'debt', 'subscription', "
        "'utilities', 'other', 'relationship', 'groceries', 'healthcare', 'childcare'"
        ")",
    )


def downgrade():
    op.drop_constraint("ck_recurring_expenses_category", "recurring_expenses", type_="check")
    op.create_check_constraint(
        "ck_recurring_expenses_category",
        "recurring_expenses",
        "category IN ("
        "'housing', 'transportation', 'insurance', 'debt', 'subscription', "
        "'utilities', 'other', 'relationship'"
        ")",
    )
