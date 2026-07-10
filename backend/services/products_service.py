#!/usr/bin/env python3
"""Product query + transform service for BTS5 recommendation engine."""

from __future__ import annotations

from typing import Any

from sqlalchemy import asc, desc, func

from backend.models.database import db
from backend.models.product import Product


class ProductsService:
    """Query products for BTS tiering (BTS2) and recommendations (BTS5)."""

    @staticmethod
    def search_products(
        retailer: str | None = None,
        category: str | None = None,
        color: str | None = None,
        min_price: float = 0,
        max_price: float = 999,
        *,
        in_stock_only: bool = True,
    ) -> list[dict[str, Any]]:
        """
        Query products for BTS5 recommendation engine.

        Sorted by rating DESC, then price ASC.
        """
        query = Product.query

        if retailer:
            query = query.filter(Product.retailer == retailer)
        if category:
            query = query.filter(Product.category == category)
        if color:
            query = query.filter(Product.color == color)

        query = query.filter(
            Product.price >= min_price,
            Product.price <= max_price,
        )
        if in_stock_only:
            query = query.filter(Product.in_stock.is_(True))

        products = query.order_by(
            desc(Product.rating).nullslast(),
            asc(Product.price),
        ).all()
        return [p.to_dict() for p in products]

    @staticmethod
    def get_products_by_category(category: str) -> list[dict[str, Any]]:
        """Get all in-stock products in a category (for BTS5 context)."""
        products = (
            Product.query.filter_by(category=category, in_stock=True)
            .order_by(desc(Product.rating).nullslast(), asc(Product.price))
            .all()
        )
        return [p.to_dict() for p in products]

    @staticmethod
    def get_available_colors(category: str) -> list[str]:
        """Get distinct colors available in a category."""
        rows = (
            db.session.query(Product.color)
            .filter(Product.category == category, Product.color.isnot(None))
            .distinct()
            .order_by(Product.color)
            .all()
        )
        return [c[0] for c in rows if c[0]]

    @staticmethod
    def get_price_range(category: str) -> dict[str, float]:
        """Get min/max price in a category."""
        result = (
            db.session.query(
                func.min(Product.price),
                func.max(Product.price),
            )
            .filter(Product.category == category)
            .first()
        )
        if not result or result[0] is None:
            return {"min": 0.0, "max": 0.0}
        return {
            "min": float(result[0]),
            "max": float(result[1]),
        }

    @staticmethod
    def create_product(
        sku: str,
        retailer: str,
        category: str,
        name: str,
        price: float,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Create a single product (used by seed data)."""
        product = Product(
            sku=sku,
            retailer=retailer,
            category=category,
            name=name,
            price=price,
            **kwargs,
        )
        db.session.add(product)
        db.session.commit()
        return product.to_dict()

    @staticmethod
    def bulk_create_products(products_list: list[dict[str, Any]]) -> int:
        """
        Bulk insert products (used by seed + scrapers in V2).

        Skips rows whose sku already exists. Returns count of newly inserted rows.
        """
        inserted = 0
        for product_data in products_list:
            sku = product_data.get("sku")
            if not sku:
                continue
            existing = Product.query.filter_by(sku=sku).first()
            if existing:
                continue
            product = Product(**product_data)
            db.session.add(product)
            inserted += 1
        db.session.commit()
        return inserted
