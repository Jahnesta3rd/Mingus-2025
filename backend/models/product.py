#!/usr/bin/env python3
"""Back-to-school product inventory (BTS4)."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy.dialects.postgresql import UUID as PG_UUID

from .database import db


class Product(db.Model):
    """Retail product row for BTS recommendation queries."""

    __tablename__ = "products"

    id = db.Column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=db.text("gen_random_uuid()"),
    )
    sku = db.Column(db.String(255), unique=True, nullable=False)
    retailer = db.Column(db.String(50), nullable=False)  # h&m | nordstrom | amazon
    category = db.Column(db.String(100), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    original_price = db.Column(db.Numeric(10, 2))
    image_url = db.Column(db.Text)
    rating = db.Column(db.Numeric(3, 2))  # 0–5
    review_count = db.Column(db.Integer, default=0, server_default="0")
    color = db.Column(db.String(50))
    in_stock = db.Column(db.Boolean, default=True, server_default=db.text("true"))
    coupon_eligible = db.Column(
        db.Boolean, default=True, server_default=db.text("true")
    )
    url = db.Column(db.Text)
    last_updated = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        server_default=db.text("NOW()"),
    )
    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        server_default=db.text("NOW()"),
    )

    def to_dict(self) -> dict:
        return {
            "id": str(self.id) if self.id else None,
            "sku": self.sku,
            "retailer": self.retailer,
            "category": self.category,
            "name": self.name,
            "description": self.description,
            "price": float(self.price) if self.price is not None else None,
            "original_price": (
                float(self.original_price) if self.original_price is not None else None
            ),
            "image_url": self.image_url,
            "rating": float(self.rating) if self.rating is not None else None,
            "review_count": int(self.review_count or 0),
            "color": self.color,
            "in_stock": bool(self.in_stock) if self.in_stock is not None else True,
            "coupon_eligible": (
                bool(self.coupon_eligible) if self.coupon_eligible is not None else True
            ),
            "url": self.url,
        }

    def __repr__(self) -> str:
        return f"<Product sku={self.sku!r} retailer={self.retailer!r} price={self.price}>"
