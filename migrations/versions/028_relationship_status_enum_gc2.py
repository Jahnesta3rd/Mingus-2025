"""Decision 2: extend relationshipstatus enum for Guided Canvas roster

Revision ID: 028_relationship_status_enum_gc2
Revises: 027_user_income_frequency_semimonthly
Create Date: 2026-04-18

Adds PostgreSQL enum labels: SINGLE, PARTNERED, OTHER, DIVORCED (uppercase names,
matching SQLAlchemy / Postgres storage for RelationshipStatus member names).

Existing labels are unchanged. Each ADD VALUE runs in its own autocommit block
(Postgres cannot combine enum ADD VALUE with other DDL in one transaction).

Requires PostgreSQL 15+ for ADD VALUE IF NOT EXISTS; otherwise upgrade fails at
this revision (use a DB version that supports IF NOT EXISTS, or adjust manually).
"""

from alembic import op


revision = "028_relationship_status_enum_gc2"
down_revision = "027_user_income_frequency_semimonthly"
branch_labels = None
depends_on = None

_NEW_VALUES = ("SINGLE", "PARTNERED", "OTHER", "DIVORCED")


def upgrade():
    ctx = op.get_context()
    for val in _NEW_VALUES:
        with ctx.autocommit_block():
            op.execute(
                f"ALTER TYPE relationshipstatus ADD VALUE IF NOT EXISTS '{val}'"
            )


def downgrade():
    # PostgreSQL cannot safely remove enum values in-place; no-op downgrade.
    pass
