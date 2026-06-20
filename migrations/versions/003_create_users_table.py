"""Create users table (Alembic baseline)

Revision ID: 003_create_users_table
Revises:
Create Date: 2026-06-20

Baseline migration so ``alembic upgrade head`` can run on a fresh database
before migrations that foreign-key to ``users.id`` (starting with 004).
"""
from alembic import op
import sqlalchemy as sa


revision = "003_create_users_table"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if inspector.has_table("users"):
        return

    postgres = bind.dialect.name == "postgresql"
    bool_false = sa.text("false") if postgres else sa.text("0")

    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.String(length=255), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=True),
        sa.Column("password_reset_token", sa.String(length=255), nullable=True),
        sa.Column("password_reset_expires", sa.DateTime(), nullable=True),
        sa.Column("first_name", sa.String(length=100), nullable=True),
        sa.Column("last_name", sa.String(length=100), nullable=True),
        sa.Column("tier", sa.String(length=50), nullable=False, server_default="budget"),
        sa.Column("referral_code", sa.String(length=50), nullable=True),
        sa.Column("referred_by", sa.String(length=255), nullable=True),
        sa.Column("referral_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("successful_referrals", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "feature_unlocked",
            sa.Boolean(),
            nullable=False,
            server_default=bool_false,
        ),
        sa.Column("unlock_date", sa.DateTime(), nullable=True),
        sa.Column("last_activity", sa.DateTime(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("referral_code", name="uq_users_referral_code"),
    )
    op.create_index(op.f("ix_users_user_id"), "users", ["user_id"], unique=True)
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)
    op.create_index(
        op.f("ix_users_password_reset_token"),
        "users",
        ["password_reset_token"],
        unique=False,
    )


def downgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if not inspector.has_table("users"):
        return

    op.drop_index(op.f("ix_users_password_reset_token"), table_name="users")
    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_index(op.f("ix_users_user_id"), table_name="users")
    op.drop_table("users")
