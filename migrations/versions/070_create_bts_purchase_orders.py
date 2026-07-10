"""Create bts_purchase_orders table (BTS9 checkout).

Revision ID: 070_create_bts_purchase_orders
Revises: 069_create_bts_recommendations
Create Date: 2026-07-10
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID


revision = "070_create_bts_purchase_orders"
down_revision = "069_create_bts_recommendations"
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    exists = conn.execute(
        sa.text("SELECT to_regclass('public.bts_purchase_orders') IS NOT NULL")
    ).scalar()
    if exists:
        return

    op.create_table(
        "bts_purchase_orders",
        sa.Column(
            "order_id",
            PG_UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("session_id", PG_UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", sa.String(length=255), nullable=False),
        sa.Column("tier", sa.Integer(), nullable=False),
        sa.Column("cart_items", JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("items_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("shipping_address", JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("stripe_payment_intent_id", sa.String(length=255), nullable=True),
        sa.Column("coupon_code", sa.String(length=100), nullable=True),
        sa.Column(
            "coupon_discount",
            sa.Numeric(10, 2),
            nullable=False,
            server_default="0",
        ),
        sa.Column("subtotal", sa.Numeric(10, 2), nullable=False),
        sa.Column("discount", sa.Numeric(10, 2), nullable=False, server_default="0"),
        sa.Column("tax", sa.Numeric(10, 2), nullable=False, server_default="0"),
        sa.Column("total", sa.Numeric(10, 2), nullable=False),
        sa.Column(
            "status",
            sa.String(length=50),
            nullable=False,
            server_default="pending",
        ),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ["session_id"],
            ["back_to_school_sessions.session_id"],
            ondelete="CASCADE",
        ),
    )
    op.create_index("idx_bts_orders_session", "bts_purchase_orders", ["session_id"])
    op.create_index("idx_bts_orders_user", "bts_purchase_orders", ["user_id"])
    op.create_index(
        "idx_bts_orders_tier",
        "bts_purchase_orders",
        ["session_id", "tier"],
    )


def downgrade():
    op.execute("DROP INDEX IF EXISTS idx_bts_orders_tier")
    op.execute("DROP INDEX IF EXISTS idx_bts_orders_user")
    op.execute("DROP INDEX IF EXISTS idx_bts_orders_session")
    op.execute("DROP TABLE IF EXISTS bts_purchase_orders")
