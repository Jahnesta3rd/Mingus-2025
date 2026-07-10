#!/usr/bin/env python3
"""Back-to-school product query API for BTS5 recommendation engine."""

from __future__ import annotations

import logging

from flask import Blueprint, jsonify, request

from backend.auth.decorators import require_auth
from backend.services.products_service import ProductsService

logger = logging.getLogger(__name__)

products_bp = Blueprint("products", __name__, url_prefix="/api/bts")


def _parse_float(value, default: float, field: str) -> float:
    if value is None or value == "":
        return default
    try:
        return float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field} must be a number") from exc


@products_bp.route("/products/search", methods=["GET"])
@require_auth
def search_products():
    """
    Query products for recommendation engine.

    Query params:
    - retailer: "h&m" | "nordstrom" | "amazon"
    - category: "jeans" | "shirt_short" | etc
    - color: "black" | "white" | etc
    - min_price: float
    - max_price: float
    """
    try:
        retailer = request.args.get("retailer") or None
        category = request.args.get("category") or None
        color = request.args.get("color") or None
        min_price = _parse_float(request.args.get("min_price"), 0.0, "min_price")
        max_price = _parse_float(request.args.get("max_price"), 999.0, "max_price")

        products = ProductsService.search_products(
            retailer=retailer,
            category=category,
            color=color,
            min_price=min_price,
            max_price=max_price,
        )
        return (
            jsonify(
                {
                    "status": "success",
                    "count": len(products),
                    "products": products,
                }
            ),
            200,
        )
    except ValueError as exc:
        return jsonify({"status": "error", "message": str(exc)}), 400
    except Exception as exc:
        logger.exception("products search failed: %s", exc)
        return jsonify({"status": "error", "message": str(exc)}), 500


@products_bp.route("/products/category/<category>", methods=["GET"])
@require_auth
def get_products_by_category(category):
    """Get all products in a category."""
    try:
        products = ProductsService.get_products_by_category(category)
        return (
            jsonify(
                {
                    "status": "success",
                    "category": category,
                    "count": len(products),
                    "products": products,
                }
            ),
            200,
        )
    except Exception as exc:
        logger.exception("products by category failed: %s", exc)
        return jsonify({"status": "error", "message": str(exc)}), 500


@products_bp.route("/products/metadata/<category>", methods=["GET"])
@require_auth
def get_category_metadata(category):
    """Get metadata for a category (colors, price range)."""
    try:
        colors = ProductsService.get_available_colors(category)
        price_range = ProductsService.get_price_range(category)
        return (
            jsonify(
                {
                    "status": "success",
                    "category": category,
                    "colors": colors,
                    "price_range": price_range,
                }
            ),
            200,
        )
    except Exception as exc:
        logger.exception("products metadata failed: %s", exc)
        return jsonify({"status": "error", "message": str(exc)}), 500
