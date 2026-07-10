"""Unit tests for BTS5 recommendation service."""

from __future__ import annotations

import json
import uuid
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from backend.services.bts_recommendation_service import (
    BtsRecommendationService,
    _resolve_product_categories,
    _strip_markdown_fences,
)


SAMPLE_PICK = {
    "retailer": "h&m",
    "sku": "hm_jeans_g_001",
    "name": "Black Skinny Fit Jeans",
    "price": 29.99,
    "rating": 4.3,
    "reviewCount": 256,
    "color": "black",
    "imageUrl": "https://example.com/j.png",
    "url": "https://www.hm.com/us/product/hm_jeans_g_001",
    "quantity": 3,
    "reason": "Best value stretch denim under budget.",
}


def test_strip_markdown_fences():
    assert _strip_markdown_fences('```json\n{"a":1}\n```') == '{"a":1}'


def test_resolve_product_categories_aliases():
    assert _resolve_product_categories("shoes")[0] == "sneakers"
    assert _resolve_product_categories("jeans") == ["jeans"]


def test_invalid_tier_raises():
    svc = BtsRecommendationService(llm_caller=lambda s, u: "{}")
    with pytest.raises(ValueError, match="Invalid tier"):
        svc.generate_recommendations(uuid.uuid4(), "tier9")


def test_calculate_summary():
    summary = BtsRecommendationService._calculate_summary(
        "tier1",
        520,
        {
            "h&m": [{"price": 20, "quantity": 1}],
            "nordstrom": [{"price": 45, "quantity": 3}],
            "amazon": [],
        },
    )
    assert summary["totalEstimated"] == 155.0
    assert summary["remaining"] == 365.0
    assert summary["byRetailer"]["nordstrom"] == 135.0


def test_generate_recommendations_happy_path():
    session_id = uuid.uuid4()
    session = SimpleNamespace(
        session_id=session_id,
        user_id="user-abc",
        child_age=8,
        child_gender="girl",
    )
    plan = SimpleNamespace(
        plan_data={
            "tier1": {
                "budget": 520,
                "items": [
                    {
                        "category": "jeans",
                        "quantity": 3,
                        "estimatedCost": 90,
                        "priority": "MUST_HAVE",
                        "note": "black denim",
                    }
                ],
            }
        }
    )

    products = {
        "h&m": [
            {
                "sku": "hm_jeans_g_001",
                "name": "Black Skinny Fit Jeans",
                "price": 29.99,
                "rating": 4.3,
                "review_count": 256,
                "color": "black",
                "url": "https://www.hm.com/us/product/hm_jeans_g_001",
                "image_url": "https://example.com/j.png",
                "retailer": "h&m",
            }
        ],
        "nordstrom": [],
        "amazon": [],
    }

    svc = BtsRecommendationService(
        llm_caller=lambda s, u: "```json\n" + json.dumps(SAMPLE_PICK) + "\n```"
    )

    with (
        patch.object(svc, "_fetch_and_validate_session", return_value=session),
        patch.object(svc, "_fetch_and_validate_plan", return_value=plan),
        patch.object(svc, "_get_top_products_for_category", return_value=products),
        patch.object(svc, "_save_recommendations", return_value=MagicMock()) as save_mock,
    ):
        result = svc.generate_recommendations(str(session_id), "tier1")

    assert result["status"] == "success"
    assert result["tier"] == "tier1"
    assert len(result["recommendations"]["h&m"]) == 1
    item = result["recommendations"]["h&m"][0]
    assert item["sku"] == "hm_jeans_g_001"
    assert item["category"] == "jeans"
    assert item["reason"]
    assert result["summary"]["tierBudget"] == 520
    save_mock.assert_called_once()


def test_empty_tier_items_raises():
    session_id = uuid.uuid4()
    session = SimpleNamespace(
        session_id=session_id,
        user_id="user-abc",
        child_age=8,
        child_gender="girl",
    )
    plan = SimpleNamespace(plan_data={"tier1": {"budget": 100, "items": []}})
    svc = BtsRecommendationService(llm_caller=lambda s, u: "{}")
    with (
        patch.object(svc, "_fetch_and_validate_session", return_value=session),
        patch.object(svc, "_fetch_and_validate_plan", return_value=plan),
    ):
        with pytest.raises(ValueError, match="No items"):
            svc.generate_recommendations(str(session_id), "tier1")
