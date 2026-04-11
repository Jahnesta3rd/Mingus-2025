"""add card_type to vibe_tracked_people

Revision ID: 020_add_vibe_tracked_person_card_type
Revises: 016_add_sleep_to_weekly_checkin
Create Date: 2026-04-11

Roster card kind: person | kids | social (default person).
Note: revision 017_add_life_correlation_table already exists in this repo; this chain follows 016_add_sleep_to_weekly_checkin as current head.
"""
from alembic import op
import sqlalchemy as sa


revision = "020_add_vibe_tracked_person_card_type"
down_revision = "016_add_sleep_to_weekly_checkin"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "vibe_tracked_people",
        sa.Column(
            "card_type",
            sa.String(length=20),
            nullable=False,
            server_default="person",
        ),
    )


def downgrade():
    op.drop_column("vibe_tracked_people", "card_type")
