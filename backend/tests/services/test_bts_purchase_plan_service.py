"""Unit tests for BTS2 purchase plan service (validation + Claude parsing)."""

from __future__ import annotations

import json
import uuid
from datetime import date
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from backend.services.bts_purchase_plan_service import (
    BtsPurchasePlanService,
    _strip_markdown_fences,
)


SAMPLE_PLAN = {
    "tier1": {
        "budget": 520,
        "purchaseBy": "2026-08-14",
        "justification": "Essentials",
        "items": [
            {
                "category": "underwear",
                "quantity": 8,
                "estimatedCost": 50,
                "priority": "MUST_HAVE",
                "note": "8-pack",
            }
        ],
        "totalEstimated": 430,
        "remaining": 90,
    },
    "tier2": {
        "budget": 280,
        "purchaseBy": "2026-08-21",
        "contingency": "If side job hits",
        "justification": "Variety",
        "items": [],
        "totalEstimated": 270,
        "remaining": 10,
    },
    "tier3": {
        "budget": 450,
        "purchaseBy": "2026-08-28",
        "contingency": "If cash left",
        "justification": "Nice-to-haves",
        "items": [],
        "totalEstimated": 330,
        "remaining": 120,
    },
    "summary": {
        "totalBudgetAvailable": 1250,
        "totalEstimatedSpend": 1030,
        "bufferRemaining": 220,
        "jobDependent": False,
        "fallbackIfJobFails": "Tier 1 covers essentials",
    },
    "warnings": ["If job earnings don't hit, skip Tier 2"],
}


def test_strip_markdown_fences():
    raw = "```json\n{\"a\": 1}\n```"
    assert _strip_markdown_fences(raw) == '{"a": 1}'


def test_validate_capsule_rejects_invalid_category():
    svc = BtsPurchasePlanService(llm_caller=lambda s, u: "{}")
    with pytest.raises(ValueError, match="Invalid category"):
        svc._validate_capsule({"spaceship": 1})


def test_validate_capsule_rejects_non_positive():
    svc = BtsPurchasePlanService(llm_caller=lambda s, u: "{}")
    with pytest.raises(ValueError, match="positive integer"):
        svc._validate_capsule({"jeans": 0})
    with pytest.raises(ValueError, match="positive integer"):
        svc._validate_capsule({"jeans": 1.5})  # type: ignore[dict-item]


def test_validate_plan_structure_requires_tiers():
    svc = BtsPurchasePlanService(llm_caller=lambda s, u: "{}")
    with pytest.raises(ValueError, match="missing required key"):
        svc._validate_plan_structure({"tier1": {}})


def test_validate_plan_structure_accepts_sample():
    svc = BtsPurchasePlanService(llm_caller=lambda s, u: "{}")
    svc._validate_plan_structure(SAMPLE_PLAN)


def test_generate_plan_happy_path():
    session_id = uuid.uuid4()
    session = SimpleNamespace(
        session_id=session_id,
        user_id="user-abc",
        tier1_date=date(2026, 8, 14),
        tier2_date=date(2026, 8, 21),
        tier3_date=date(2026, 8, 28),
        tier1_balance=520,
        tier2_balance=280,
        tier3_balance=450,
        child_name="Emma",
        child_age=8,
        child_gender="girl",
    )

    def fake_llm(system, user):
        return "```json\n" + json.dumps(SAMPLE_PLAN) + "\n```"

    svc = BtsPurchasePlanService(llm_caller=fake_llm)

    with (
        patch.object(svc, "_fetch_and_validate_session", return_value=session),
        patch.object(svc, "_save_plan", return_value=MagicMock()) as save_mock,
    ):
        result = svc.generate_plan(
            str(session_id),
            {"underwear": 8, "jeans": 3, "shirt_short": 6},
        )

    assert result["status"] == "success"
    assert result["sessionId"] == str(session_id)
    assert result["tier1"]["budget"] == 520
    assert result["summary"]["bufferRemaining"] == 220
    save_mock.assert_called_once()


def test_generate_plan_retries_on_bad_json_then_succeeds():
    session_id = uuid.uuid4()
    session = SimpleNamespace(
        session_id=session_id,
        user_id="user-abc",
        tier1_date=date(2026, 8, 14),
        tier2_date=date(2026, 8, 21),
        tier3_date=date(2026, 8, 28),
        tier1_balance=520,
        tier2_balance=280,
        tier3_balance=450,
        child_name="Emma",
        child_age=8,
        child_gender="girl",
    )
    calls = {"n": 0}

    def flaky_llm(system, user):
        calls["n"] += 1
        if calls["n"] == 1:
            return "not json"
        return json.dumps(SAMPLE_PLAN)

    svc = BtsPurchasePlanService(llm_caller=flaky_llm)
    with (
        patch.object(svc, "_fetch_and_validate_session", return_value=session),
        patch.object(svc, "_save_plan", return_value=MagicMock()),
    ):
        result = svc.generate_plan(str(session_id), {"jeans": 3})

    assert result["status"] == "success"
    assert calls["n"] == 2


def test_parse_session_id_rejects_legacy_string():
    svc = BtsPurchasePlanService(llm_caller=lambda s, u: "{}")
    with pytest.raises(ValueError, match="Invalid sessionId"):
        svc.get_plan("bts-session-abc123")
