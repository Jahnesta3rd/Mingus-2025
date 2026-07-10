#!/usr/bin/env python3
"""BTS5: Claude product recommendations for a purchase-plan tier."""

from __future__ import annotations

import json
import logging
import re
import uuid
from typing import Any, Callable

import anthropic

from backend.constants.anthropic_models import CLAUDE_SONNET_MODEL
from backend.models.bts import (
    BackToSchoolPurchasePlan,
    BackToSchoolRecommendation,
    BackToSchoolSession,
)
from backend.models.database import db
from backend.services.products_service import ProductsService

logger = logging.getLogger(__name__)

VALID_TIERS = frozenset({"tier1", "tier2", "tier3"})
RETAILERS = ("h&m", "nordstrom", "amazon")

# Map capsule/plan categories → BTS4 product categories to try (in order).
CATEGORY_ALIASES: dict[str, list[str]] = {
    "shoes": ["sneakers", "shoes"],
    "sneakers": ["sneakers", "shoes"],
    "sweater": ["hoodie", "shirt_long", "sweater"],
    "romper": ["leggings", "romper"],
    "pajamas": ["shirt_long", "hoodie", "pajamas"],
}

_PICKED_REQUIRED = ("retailer", "sku", "name", "price", "quantity", "reason")
_RETRY_APPEND = (
    "\n\nIMPORTANT: Return ONLY raw JSON with no markdown fences. "
    "Include retailer, sku, name, price, quantity, and reason."
)


def _parse_session_id(session_id: str | uuid.UUID) -> uuid.UUID:
    if isinstance(session_id, uuid.UUID):
        return session_id
    try:
        return uuid.UUID(str(session_id).strip())
    except ValueError as exc:
        raise ValueError(f"Invalid sessionId (expected UUID): {session_id}") from exc


def _strip_markdown_fences(text: str) -> str:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*\n?", "", cleaned, count=1)
        cleaned = re.sub(r"\n?```\s*$", "", cleaned)
    return cleaned.strip()


def _resolve_product_categories(category: str) -> list[str]:
    key = (category or "").strip().lower()
    aliases = CATEGORY_ALIASES.get(key)
    if aliases:
        return aliases
    return [key] if key else []


class BtsRecommendationService:
    """
    Generates product recommendations for a specific tier.
    Fetches tier items from BTS2 plan, queries products DB, calls Claude per category.
    """

    def __init__(
        self,
        *,
        client: anthropic.Anthropic | None = None,
        model: str = CLAUDE_SONNET_MODEL,
        llm_caller: Callable[[str, str], str] | None = None,
    ) -> None:
        self._client = client
        self.model = model
        self._llm_caller = llm_caller

    @property
    def client(self) -> anthropic.Anthropic:
        if self._client is None:
            self._client = anthropic.Anthropic()
        return self._client

    def generate_recommendations(
        self, session_id: str | uuid.UUID, tier: str
    ) -> dict[str, Any]:
        """Fetch session + plan, recommend products for the given tier."""
        tier_key = str(tier or "").strip().lower()
        if tier_key not in VALID_TIERS:
            raise ValueError(
                f"Invalid tier: {tier}. Must be tier1, tier2, or tier3"
            )

        session = self._fetch_and_validate_session(session_id)
        plan = self._fetch_and_validate_plan(session.session_id)
        plan_data = plan.plan_data if isinstance(plan.plan_data, dict) else {}

        tier_block = plan_data.get(tier_key) or {}
        if not isinstance(tier_block, dict):
            raise ValueError(f"Invalid {tier_key} block in purchase plan")

        tier_items = tier_block.get("items") or []
        tier_budget = float(tier_block.get("budget") or 0)
        if not isinstance(tier_items, list) or not tier_items:
            raise ValueError(f"No items in {tier_key}")

        recommendations_by_retailer = self._get_recommendations_per_category(
            tier_items=tier_items,
            tier_budget=tier_budget,
            child_age=session.child_age,
            child_gender=session.child_gender,
        )
        summary = self._calculate_summary(
            tier_key, tier_budget, recommendations_by_retailer
        )

        payload = {
            "status": "success",
            "sessionId": str(session.session_id),
            "tier": tier_key,
            "recommendations": recommendations_by_retailer,
            "summary": summary,
        }
        self._save_recommendations(
            user_id=session.user_id,
            session_id=session.session_id,
            tier=tier_key,
            payload=payload,
        )
        return payload

    def _fetch_and_validate_session(
        self, session_id: str | uuid.UUID
    ) -> BackToSchoolSession:
        sid = _parse_session_id(session_id)
        session = BackToSchoolSession.query.filter_by(session_id=sid).first()
        if not session:
            raise ValueError(f"BTS session not found: {sid}")
        return session

    def _fetch_and_validate_plan(
        self, session_id: uuid.UUID
    ) -> BackToSchoolPurchasePlan:
        plan = BackToSchoolPurchasePlan.query.filter_by(session_id=session_id).first()
        if not plan:
            raise ValueError(
                f"Purchase plan not found for session: {session_id}. Run BTS2 first."
            )
        if not isinstance(plan.plan_data, dict):
            raise ValueError("Plan data is not valid JSON")
        return plan

    def _get_recommendations_per_category(
        self,
        *,
        tier_items: list[dict[str, Any]],
        tier_budget: float,
        child_age: int | None,
        child_gender: str | None,
    ) -> dict[str, list[dict[str, Any]]]:
        recommendations_by_retailer: dict[str, list[dict[str, Any]]] = {
            retailer: [] for retailer in RETAILERS
        }
        item_count = max(len(tier_items), 1)
        default_max = tier_budget / item_count if tier_budget > 0 else 999.0

        for item in tier_items:
            if not isinstance(item, dict):
                continue
            category = str(item.get("category") or "").strip()
            if not category:
                continue
            try:
                quantity = int(item.get("quantity") or 1)
            except (TypeError, ValueError):
                quantity = 1
            if quantity <= 0:
                quantity = 1

            try:
                max_price = float(item.get("estimatedCost") or default_max)
            except (TypeError, ValueError):
                max_price = default_max
            if max_price <= 0:
                max_price = default_max

            category_products = self._get_top_products_for_category(category)
            if not any(category_products.values()):
                logger.info("No products found for category=%s", category)
                continue

            picked = self._call_claude_for_category(
                category=category,
                quantity=quantity,
                max_price=max_price,
                available_products=category_products,
                child_age=child_age,
                child_gender=child_gender,
            )
            if not picked:
                continue

            retailer = str(picked.get("retailer") or "").strip().lower()
            if retailer not in recommendations_by_retailer:
                # Normalize common variants
                if retailer in ("hm", "h and m", "h&m"):
                    retailer = "h&m"
                else:
                    logger.warning(
                        "Claude returned unknown retailer %r for %s; skipping",
                        retailer,
                        category,
                    )
                    continue

            recommendations_by_retailer[retailer].append(picked)

        return recommendations_by_retailer

    def _get_top_products_for_category(
        self, category: str
    ) -> dict[str, list[dict[str, Any]]]:
        """Query BTS4 for top products per retailer (try category aliases)."""
        results: dict[str, list[dict[str, Any]]] = {r: [] for r in RETAILERS}
        for product_category in _resolve_product_categories(category):
            for retailer in RETAILERS:
                if results[retailer]:
                    continue
                products = ProductsService.search_products(
                    retailer=retailer,
                    category=product_category,
                    min_price=0,
                    max_price=999,
                )
                results[retailer] = products[:5]
            if any(results.values()):
                break
        return results

    def _call_claude_for_category(
        self,
        *,
        category: str,
        quantity: int,
        max_price: float,
        available_products: dict[str, list[dict[str, Any]]],
        child_age: int | None,
        child_gender: str | None,
    ) -> dict[str, Any] | None:
        product_options: list[dict[str, Any]] = []
        by_sku: dict[str, dict[str, Any]] = {}
        for retailer, products in available_products.items():
            for p in products[:3]:
                option = {
                    "retailer": retailer,
                    "sku": p.get("sku"),
                    "name": p.get("name"),
                    "price": p.get("price"),
                    "rating": p.get("rating"),
                    "review_count": p.get("review_count"),
                    "color": p.get("color"),
                    "url": p.get("url"),
                    "image_url": p.get("image_url"),
                }
                product_options.append(option)
                if option["sku"]:
                    by_sku[str(option["sku"])] = option

        if not product_options:
            return None

        age_label = child_age if child_age is not None else "school-age"
        gender_label = child_gender or "child"
        system_prompt = f"""You are a back-to-school shopping advisor. Pick the BEST product for a {age_label}-year-old {gender_label}.

RULES:
1. Maximize rating (prefer 4.5★+)
2. Prefer options at or under max price: ${max_price:.2f}
3. Match quantity needed: {quantity} (use pack size when relevant)
4. Explain your choice briefly (1-2 sentences)
5. Return ONLY valid JSON (no markdown)
6. sku/retailer/name/price MUST match one of the available options exactly

OUTPUT: Return exactly this JSON:
{{
  "retailer": "STRING (h&m|nordstrom|amazon)",
  "sku": "STRING",
  "name": "STRING",
  "price": NUMBER,
  "rating": NUMBER,
  "reviewCount": NUMBER,
  "color": "STRING",
  "imageUrl": "STRING",
  "url": "STRING",
  "quantity": NUMBER,
  "reason": "STRING (1-2 sentences)"
}}"""
        user_message = f"""Category: {category}
Quantity needed: {quantity}
Max price for this line item: ${max_price:.2f}

Available options:
{json.dumps(product_options, indent=2)}

Pick the best product."""

        raw = self._invoke_llm(system_prompt, user_message)
        picked = self._parse_picked_json(raw)
        if picked is None:
            raw = self._invoke_llm(system_prompt, user_message + _RETRY_APPEND)
            picked = self._parse_picked_json(raw)
        if picked is None:
            raise ValueError(
                f"Claude returned invalid JSON for {category}: {(raw or '')[:200]}"
            )

        for field in _PICKED_REQUIRED:
            if field not in picked:
                raise ValueError(f"Claude response missing field: {field}")

        # Enrich / normalize from catalog when possible.
        catalog = by_sku.get(str(picked.get("sku") or ""))
        if catalog:
            picked.setdefault("rating", catalog.get("rating"))
            picked.setdefault("reviewCount", catalog.get("review_count"))
            picked.setdefault("color", catalog.get("color"))
            picked.setdefault("imageUrl", catalog.get("image_url"))
            picked.setdefault("url", catalog.get("url"))
            if not picked.get("name"):
                picked["name"] = catalog.get("name")
            if picked.get("price") is None:
                picked["price"] = catalog.get("price")
            picked["retailer"] = catalog.get("retailer") or picked.get("retailer")

        try:
            price = float(picked["price"])
        except (TypeError, ValueError) as exc:
            raise ValueError(f"Invalid price from Claude for {category}") from exc
        try:
            qty = int(picked["quantity"])
        except (TypeError, ValueError):
            qty = quantity
        if qty <= 0:
            qty = quantity

        return {
            "category": category,
            "productId": str(picked.get("sku")),
            "sku": str(picked.get("sku")),
            "name": str(picked.get("name")),
            "retailer": str(picked.get("retailer")),
            "quantity": qty,
            "price": round(price, 2),
            "imageUrl": picked.get("imageUrl") or picked.get("image_url"),
            "rating": picked.get("rating"),
            "reviewCount": picked.get("reviewCount") or picked.get("review_count"),
            "color": picked.get("color"),
            "reason": str(picked.get("reason") or ""),
            "url": picked.get("url"),
        }

    def _invoke_llm(self, system: str, user_message: str) -> str:
        if self._llm_caller is not None:
            return self._llm_caller(system, user_message)
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=500,
                system=system,
                messages=[{"role": "user", "content": user_message}],
            )
            block = response.content[0] if response.content else None
            return (getattr(block, "text", None) or "").strip()
        except Exception as exc:
            logger.exception("BTS recommendation Claude call failed: %s", exc)
            raise ValueError(f"Claude API call failed: {exc}") from exc

    @staticmethod
    def _parse_picked_json(raw: str | None) -> dict[str, Any] | None:
        if not raw:
            return None
        try:
            data = json.loads(_strip_markdown_fences(raw))
        except json.JSONDecodeError:
            return None
        return data if isinstance(data, dict) else None

    @staticmethod
    def _calculate_summary(
        tier: str,
        tier_budget: float,
        recommendations_by_retailer: dict[str, list[dict[str, Any]]],
    ) -> dict[str, Any]:
        total = 0.0
        by_retailer: dict[str, float] = {}
        for retailer, items in recommendations_by_retailer.items():
            retailer_total = sum(
                float(item.get("price") or 0) * int(item.get("quantity") or 1)
                for item in items
            )
            by_retailer[retailer] = round(retailer_total, 2)
            total += retailer_total
        total = round(total, 2)
        return {
            "tier": tier,
            "totalEstimated": total,
            "tierBudget": round(float(tier_budget), 2),
            "remaining": round(float(tier_budget) - total, 2),
            "byRetailer": by_retailer,
        }

    def _save_recommendations(
        self,
        *,
        user_id: str,
        session_id: uuid.UUID,
        tier: str,
        payload: dict[str, Any],
    ) -> BackToSchoolRecommendation:
        existing = BackToSchoolRecommendation.query.filter_by(
            session_id=session_id, tier=tier
        ).first()
        if existing:
            existing.recommendation_data = payload
            existing.user_id = user_id
            db.session.commit()
            return existing

        row = BackToSchoolRecommendation(
            session_id=session_id,
            user_id=user_id,
            tier=tier,
            recommendation_data=payload,
        )
        db.session.add(row)
        db.session.commit()
        return row

    @staticmethod
    def get_recommendations(
        session_id: str | uuid.UUID, tier: str
    ) -> dict[str, Any] | None:
        sid = _parse_session_id(session_id)
        tier_key = str(tier or "").strip().lower()
        row = BackToSchoolRecommendation.query.filter_by(
            session_id=sid, tier=tier_key
        ).first()
        if not row:
            return None
        return row.to_dict()


bts_recommendation_service = BtsRecommendationService()
