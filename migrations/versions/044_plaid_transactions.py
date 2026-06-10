"""Plaid transactions table + user Plaid connection fields (#177)

Revision ID: 044_plaid_transactions
Revises: 043_weekly_checkin_unified
Create Date: 2026-06-10

Adds optional Plaid connection columns to users and creates transactions table
for measured bank spending in the correlation engine.
"""
from alembic import op
import sqlalchemy as sa


revision = "044_plaid_transactions"
down_revision = "043_weekly_checkin_unified"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("users", sa.Column("plaid_access_token", sa.String(255), nullable=True))
    op.add_column("users", sa.Column("plaid_item_id", sa.String(100), nullable=True))
    op.add_column("users", sa.Column("plaid_connected_at", sa.DateTime(), nullable=True))

    op.create_table(
        "transactions",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("plaid_transaction_id", sa.String(100), nullable=False),
        sa.Column("amount", sa.Float(), nullable=False),
        sa.Column("merchant", sa.String(200), nullable=True),
        sa.Column("category", sa.String(100), nullable=True),
        sa.Column("subcategory", sa.String(100), nullable=True),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("is_debit", sa.Boolean(), nullable=False),
        sa.Column("account_id", sa.String(100), nullable=True),
        sa.Column("pending", sa.Boolean(), server_default=sa.text("false"), nullable=True),
        sa.Column("user_tagged_stress_spending", sa.Boolean(), nullable=True),
        sa.Column("user_tagged_relationship_spending", sa.Boolean(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_transactions_id", "transactions", ["id"])
    op.create_index("ix_transactions_user_id", "transactions", ["user_id"])
    op.create_index("ix_transactions_plaid_transaction_id", "transactions", ["plaid_transaction_id"], unique=True)
    op.create_index("ix_transactions_date", "transactions", ["date"])
    op.create_index("idx_transactions_user_date", "transactions", ["user_id", "date"])


def downgrade():
    op.drop_index("idx_transactions_user_date", table_name="transactions")
    op.drop_index("ix_transactions_date", table_name="transactions")
    op.drop_index("ix_transactions_plaid_transaction_id", table_name="transactions")
    op.drop_index("ix_transactions_user_id", table_name="transactions")
    op.drop_index("ix_transactions_id", table_name="transactions")
    op.drop_table("transactions")

    op.drop_column("users", "plaid_connected_at")
    op.drop_column("users", "plaid_item_id")
    op.drop_column("users", "plaid_access_token")
