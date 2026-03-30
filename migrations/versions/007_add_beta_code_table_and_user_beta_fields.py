"""add_beta_code_table_and_user_beta_fields

Revision ID: 007_add_beta_code_table_and_user_beta_fields
Revises: 006_weekly_checkin_system
Create Date: 2026-03-30

Adds:
- beta_codes (invite codes, redemption tracking)
- users.is_beta, users.beta_batch, users.is_admin, users.role
"""
from alembic import op
import sqlalchemy as sa

revision = "007_add_beta_code_table_and_user_beta_fields"
down_revision = "006_weekly_checkin_system"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    postgres = bind.dialect.name == "postgresql"
    bool_false = sa.text("false") if postgres else sa.text("0")

    op.create_table(
        "beta_codes",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("code", sa.String(length=20), nullable=False),
        sa.Column("status", sa.String(length=10), nullable=False, server_default="available"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("redeemed_at", sa.DateTime(), nullable=True),
        sa.Column("redeemed_by_user_id", sa.Integer(), nullable=True),
        sa.Column("batch", sa.String(length=30), nullable=True),
        sa.ForeignKeyConstraint(
            ["redeemed_by_user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_beta_codes_code"), "beta_codes", ["code"], unique=True)

    op.add_column(
        "users",
        sa.Column(
            "is_beta",
            sa.Boolean(),
            nullable=False,
            server_default=bool_false,
        ),
    )
    op.add_column("users", sa.Column("beta_batch", sa.String(length=30), nullable=True))
    op.add_column(
        "users",
        sa.Column(
            "is_admin",
            sa.Boolean(),
            nullable=False,
            server_default=bool_false,
        ),
    )
    op.add_column("users", sa.Column("role", sa.String(length=32), nullable=True))


def downgrade():
    op.drop_column("users", "role")
    op.drop_column("users", "is_admin")
    op.drop_column("users", "beta_batch")
    op.drop_column("users", "is_beta")
    op.drop_index(op.f("ix_beta_codes_code"), table_name="beta_codes")
    op.drop_table("beta_codes")
