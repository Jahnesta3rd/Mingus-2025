"""Unit tests for ProductsService and Product.to_dict (BTS4)."""

from __future__ import annotations

from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from backend.models.product import Product
from backend.seeds.seed_products import get_seed_products
from backend.services.products_service import ProductsService


def test_seed_has_30_products_across_three_retailers():
    products = get_seed_products()
    assert len(products) == 30
    retailers = {p["retailer"] for p in products}
    assert retailers == {"h&m", "nordstrom", "amazon"}
    for retailer in retailers:
        assert sum(1 for p in products if p["retailer"] == retailer) == 10
    skus = [p["sku"] for p in products]
    assert len(skus) == len(set(skus))
    required = {"sku", "retailer", "category", "name", "price", "rating", "color", "url"}
    for p in products:
        assert required.issubset(p.keys())
        assert p["price"] > 0


def test_product_to_dict():
    product = Product(
        sku="hm_jeans_g_001",
        retailer="h&m",
        category="jeans",
        name="Black Skinny Fit Jeans",
        price=Decimal("29.99"),
        rating=Decimal("4.30"),
        review_count=256,
        color="black",
        url="https://www.hm.com/us/product/hm_jeans_g_001",
        in_stock=True,
        coupon_eligible=True,
    )
    data = product.to_dict()
    assert data["sku"] == "hm_jeans_g_001"
    assert data["price"] == 29.99
    assert data["rating"] == 4.3
    assert data["color"] == "black"
    assert data["retailer"] == "h&m"


def test_search_products_filters_and_sorts():
    cheap = SimpleNamespace(
        to_dict=lambda: {"sku": "a", "price": 10.0, "rating": 4.0}
    )
    mid = SimpleNamespace(
        to_dict=lambda: {"sku": "b", "price": 20.0, "rating": 4.5}
    )
    query = MagicMock()
    query.filter.return_value = query
    query.order_by.return_value = query
    query.all.return_value = [mid, cheap]

    with patch("backend.services.products_service.Product") as MockProduct:
        MockProduct.query = query
        # Preserve real column descriptors for filter expressions.
        for attr in ("price", "rating", "in_stock", "retailer", "category", "color"):
            setattr(MockProduct, attr, getattr(Product, attr))
        results = ProductsService.search_products(
            retailer="h&m",
            category="jeans",
            color="black",
            min_price=5,
            max_price=50,
        )

    assert len(results) == 2
    assert results[0]["sku"] == "b"
    assert query.filter.call_count >= 2
    query.order_by.assert_called_once()


def test_get_price_range_empty():
    with patch("backend.services.products_service.db") as mock_db:
        mock_db.session.query.return_value.filter.return_value.first.return_value = (
            None,
            None,
        )
        result = ProductsService.get_price_range("jeans")
    assert result == {"min": 0.0, "max": 0.0}


def test_get_price_range_values():
    with patch("backend.services.products_service.db") as mock_db:
        mock_db.session.query.return_value.filter.return_value.first.return_value = (
            Decimal("18.90"),
            Decimal("54.00"),
        )
        result = ProductsService.get_price_range("jeans")
    assert result == {"min": 18.9, "max": 54.0}


def test_get_available_colors():
    with patch("backend.services.products_service.db") as mock_db:
        mock_db.session.query.return_value.filter.return_value.distinct.return_value.order_by.return_value.all.return_value = [
            ("black",),
            ("blue",),
            (None,),
        ]
        colors = ProductsService.get_available_colors("jeans")
    assert colors == ["black", "blue"]


def test_bulk_create_skips_existing():
    def filter_by(**kw):
        result = MagicMock()
        result.first.return_value = (
            MagicMock() if kw.get("sku") == "hm_jeans_g_001" else None
        )
        return result

    query = MagicMock()
    query.filter_by.side_effect = filter_by

    with (
        patch("backend.services.products_service.Product") as MockProduct,
        patch("backend.services.products_service.db") as mock_db,
    ):
        MockProduct.query = query
        MockProduct.side_effect = lambda **kw: SimpleNamespace(**kw)
        inserted = ProductsService.bulk_create_products(
            [
                {
                    "sku": "hm_jeans_g_001",
                    "retailer": "h&m",
                    "category": "jeans",
                    "name": "Existing",
                    "price": 29.99,
                },
                {
                    "sku": "hm_jeans_g_002",
                    "retailer": "h&m",
                    "category": "jeans",
                    "name": "New",
                    "price": 19.99,
                },
            ]
        )

    assert inserted == 1
    mock_db.session.commit.assert_called_once()
