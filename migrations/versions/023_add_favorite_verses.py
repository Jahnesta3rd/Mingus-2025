"""add favorite_verses for faith card

Revision ID: 023_add_favorite_verses
Revises: 022_add_user_alerts
Create Date: 2026-04-15
"""
from alembic import op
import sqlalchemy as sa


revision = "023_add_favorite_verses"
down_revision = "022_add_user_alerts"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "favorite_verses",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("verse_reference", sa.String(length=100), nullable=False),
        sa.Column("verse_text", sa.Text(), nullable=False),
        sa.Column("bridge_sentence", sa.Text(), nullable=False),
        sa.Column("balance_status_at_save", sa.String(length=20), nullable=True),
        sa.Column("goal_at_save", sa.String(length=255), nullable=True),
        sa.Column("saved_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "user_id",
            "verse_reference",
            name="uq_favorite_verses_user_id_verse_reference",
        ),
    )
    op.create_index(
        op.f("ix_favorite_verses_user_id"),
        "favorite_verses",
        ["user_id"],
        unique=False,
    )


def downgrade():
    op.drop_index(op.f("ix_favorite_verses_user_id"), table_name="favorite_verses")
    op.drop_table("favorite_verses")
