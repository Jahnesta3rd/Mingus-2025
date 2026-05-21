"""Expand recurring_expenses category check for wizard ExpCategory values

Revision ID: 039_recurring_expense_category_wizard
Revises: 038_user_last_vibe_moment_shown_at
Create Date: 2026-05-21

Adds family_support, child_support, alimony, caregiving to ck_recurring_expenses_category
so modular onboarding commit-module can persist wizard recurring-expense rows.
"""

import sqlalchemy as sa
from alembic import op

revision = "039_recurring_expense_category_wizard"
down_revision = "038_user_last_vibe_moment_shown_at"
branch_labels = None
depends_on = None

_CATEGORY_CHECK_15 = (
    "category IN ("
    "'housing', 'transportation', 'insurance', 'debt', 'subscription', "
    "'utilities', 'other', 'relationship', 'groceries', 'healthcare', 'childcare', "
    "'family_support', 'child_support', 'alimony', 'caregiving'"
    ")"
)

_CATEGORY_CHECK_11 = (
    "category IN ("
    "'housing', 'transportation', 'insurance', 'debt', 'subscription', "
    "'utilities', 'other', 'relationship', 'groceries', 'healthcare', 'childcare'"
    ")"
)

_WIZARD_ONLY_CATEGORIES = (
    "family_support",
    "child_support",
    "alimony",
    "caregiving",
)


def upgrade():
    op.drop_constraint("ck_recurring_expenses_category", "recurring_expenses", type_="check")
    op.create_check_constraint(
        "ck_recurring_expenses_category",
        "recurring_expenses",
        _CATEGORY_CHECK_15,
    )


def downgrade():
    """
    Reverts to the 11-value category check (pre-wizard expansion).

    Before running downgrade, confirm no recurring_expenses rows use the wizard-only
    categories (family_support, child_support, alimony, caregiving). If any exist,
    reassign those rows to an allowed category or delete them; otherwise PostgreSQL
    cannot apply the narrower constraint and this migration will raise.
    """
    conn = op.get_bind()
    count = conn.execute(
        sa.text(
            "SELECT COUNT(*) FROM recurring_expenses "
            "WHERE category IN ('family_support', 'child_support', 'alimony', 'caregiving')"
        )
    ).scalar()
    if count and int(count) > 0:
        raise RuntimeError(
            f"Cannot downgrade 039: {count} recurring_expenses row(s) use wizard-only "
            f"categories {_WIZARD_ONLY_CATEGORIES}. Reassign or delete them first."
        )

    op.drop_constraint("ck_recurring_expenses_category", "recurring_expenses", type_="check")
    op.create_check_constraint(
        "ck_recurring_expenses_category",
        "recurring_expenses",
        _CATEGORY_CHECK_11,
    )
