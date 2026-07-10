"""Create products table for back-to-school inventory (BTS4).

Revision ID: 067_create_products_table
Revises: 066_create_relationship_milestone_checkins
Create Date: 2026-07-10
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID as PG_UUID


revision = "067_create_products_table"
down_revision = "066_create_relationship_milestone_checkins"
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    exists = conn.execute(
        sa.text("SELECT to_regclass('public.products') IS NOT NULL")
    ).scalar()
    if not exists:
        op.create_table(
            "products",
            sa.Column(
                "id",
                PG_UUID(as_uuid=True),
                primary_key=True,
                server_default=sa.text("gen_random_uuid()"),
            ),
            sa.Column("sku", sa.String(length=255), nullable=False),
            sa.Column("retailer", sa.String(length=50), nullable=False),
            sa.Column("category", sa.String(length=100), nullable=False),
            sa.Column("name", sa.String(length=255), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("price", sa.Numeric(10, 2), nullable=False),
            sa.Column("original_price", sa.Numeric(10, 2), nullable=True),
            sa.Column("image_url", sa.Text(), nullable=True),
            sa.Column("rating", sa.Numeric(3, 2), nullable=True),
            sa.Column(
                "review_count",
                sa.Integer(),
                nullable=False,
                server_default="0",
            ),
            sa.Column("color", sa.String(length=50), nullable=True),
            sa.Column(
                "in_stock",
                sa.Boolean(),
                nullable=False,
                server_default=sa.text("true"),
            ),
            sa.Column(
                "coupon_eligible",
                sa.Boolean(),
                nullable=False,
                server_default=sa.text("true"),
            ),
            sa.Column("url", sa.Text(), nullable=True),
            sa.Column(
                "last_updated",
                sa.DateTime(),
                nullable=False,
                server_default=sa.text("NOW()"),
            ),
            sa.Column(
                "created_at",
                sa.DateTime(),
                nullable=False,
                server_default=sa.text("NOW()"),
            ),
            sa.UniqueConstraint("sku", name="uq_products_sku"),
        )

    # Indexes are safe to re-run with IF NOT EXISTS.
    op.execute("CREATE INDEX IF NOT EXISTS idx_retailer_category ON products (retailer, category)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_category_price ON products (category, price)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_rating ON products (rating)")


def downgrade():
    op.execute("DROP INDEX IF EXISTS idx_rating")
    op.execute("DROP INDEX IF EXISTS idx_category_price")
    op.execute("DROP INDEX IF EXISTS idx_retailer_category")
    op.execute("DROP TABLE IF EXISTS products")
