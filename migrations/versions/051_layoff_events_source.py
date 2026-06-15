"""051_layoff_events_source

Revision ID: 051_layoff_events_source
Revises: 050_merge_heads
Create Date: 2026-06-15

"""
from alembic import op
import sqlalchemy as sa


revision = "051_layoff_events_source"
down_revision = "050_merge_heads"
branch_labels = None
depends_on = None


def upgrade():
    # ADD source (new column — doesn't exist yet)
    op.add_column(
        "layoff_events",
        sa.Column(
            "source",
            sa.String(20),
            nullable=False,
            server_default="8k_filing",
        ),
    )

    # ALTER review_state (already exists — make nullable, drop server_default)
    op.alter_column(
        "layoff_events",
        "review_state",
        existing_type=sa.String(20),
        nullable=True,
        server_default=None,
    )

    # Backfill: 'auto' was the old default; map to NULL (confirmed/auto-approved)
    op.execute(
        "UPDATE layoff_events SET review_state = NULL WHERE review_state = 'auto'"
    )


def downgrade():
    # Reverse the backfill
    op.execute(
        "UPDATE layoff_events SET review_state = 'auto' WHERE review_state IS NULL"
    )
    op.alter_column(
        "layoff_events",
        "review_state",
        existing_type=sa.String(20),
        nullable=False,
        server_default="auto",
    )
    op.drop_column("layoff_events", "source")
