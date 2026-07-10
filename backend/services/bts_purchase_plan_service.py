#!/usr/bin/env python3
"""BTS2: Claude-powered tiered purchase plan generator."""

from __future__ import annotations

import json
import logging
import re
import uuid
from typing import Any, Callable

import anthropic

from backend.constants.anthropic_models import CLAUDE_SONNET_MODEL
from backend.models.bts import BackToSchoolPurchasePlan, BackToSchoolSession
from backend.models.database import db

logger = logging.getLogger(__name__)

VALID_CAPSULE_CATEGORIES = frozenset(
    {
        "underwear",
        "shirt_short",
        "shirt_long",
        "sweater",
        "jeans",
        "shoes",
        "hoodie",
        "leggings",
        "romper",
        "pajamas",
        # Aliases aligned with BTS4 product categories
        "socks",
        "sneakers",
        "backpack",
        "polo",
    }
)

_SYSTEM_PROMPT = """You are a back-to-school shopping advisor. Tier a capsule wardrobe across 3 purchase windows.

TIER DEFINITIONS:
- Tier 1 (MUST BUY NOW): Essentials child cannot start school without (underwear, socks, jeans, shoes, basic shirts)
- Tier 2 (CAN WAIT 1 WEEK): Important but deferrable (additional shirts, sweaters, leggings)
- Tier 3 (CAN WAIT 2 WEEKS): Nice-to-haves (hoodies, pajamas, rompers)

RULES:
1. Stay within each tier's budget
2. Provide specific quantities per category
3. Include brief justification for each tier placement
4. Warn if any risk (e.g., tight budget)
5. Assume multi-pack discounts available (e.g., 8-pack underwear cheaper than singles)

OUTPUT: Return ONLY valid JSON (no markdown, no extra text). Use the exact structure requested."""

_RETRY_APPEND = (
    "\n\nIMPORTANT: Return ONLY raw JSON with no markdown fences. "
    "Include keys tier1, tier2, tier3, summary, and warnings."
)

_TIER_REQUIRED = (
    "budget",
    "purchaseBy",
    "justification",
    "items",
    "totalEstimated",
    "remaining",
)


def _parse_session_id(session_id: str | uuid.UUID) -> uuid.UUID:
    if isinstance(session_id, uuid.UUID):
        return session_id
    raw = str(session_id).strip()
    # Support legacy in-memory ids that were not UUIDs.
    try:
        return uuid.UUID(raw)
    except ValueError as exc:
        raise ValueError(f"Invalid sessionId (expected UUID): {raw}") from exc


def _strip_markdown_fences(text: str) -> str:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*\n?", "", cleaned, count=1)
        cleaned = re.sub(r"\n?```\s*$", "", cleaned)
    return cleaned.strip()


class BtsPurchasePlanService:
    """
    Generates tiered purchase plan using Claude.
    Validates input, calls Claude, stores result.
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

    def generate_plan(self, session_id: str | uuid.UUID, capsule: dict) -> dict[str, Any]:
        """
        Fetch session, validate capsule, call Claude, store, return plan.
        """
        session = self._fetch_and_validate_session(session_id)
        self._validate_capsule(capsule)

        prompt_data = self._build_prompt(session, capsule)
        plan_json = self._call_claude(prompt_data)
        self._validate_plan_structure(plan_json)
        self._save_plan(session.user_id, session.session_id, plan_json)

        return {
            "status": "success",
            "sessionId": str(session.session_id),
            **plan_json,
        }

    def _fetch_and_validate_session(
        self, session_id: str | uuid.UUID
    ) -> BackToSchoolSession:
        sid = _parse_session_id(session_id)
        session = BackToSchoolSession.query.filter_by(session_id=sid).first()
        if not session:
            raise ValueError(f"BTS session not found: {sid}")
        return session

    def _validate_capsule(self, capsule: Any) -> None:
        if not isinstance(capsule, dict) or not capsule:
            raise ValueError("capsule must be a non-empty object of category → quantity")

        for category, quantity in capsule.items():
            if category not in VALID_CAPSULE_CATEGORIES:
                raise ValueError(
                    f"Invalid category: {category}. "
                    f"Allowed: {', '.join(sorted(VALID_CAPSULE_CATEGORIES))}"
                )
            if isinstance(quantity, bool) or not isinstance(quantity, int):
                raise ValueError(
                    f"{category} quantity must be a positive integer, got {quantity!r}"
                )
            if quantity <= 0:
                raise ValueError(
                    f"{category} quantity must be a positive integer, got {quantity}"
                )

    def _build_prompt(
        self, session: BackToSchoolSession, capsule: dict[str, int]
    ) -> dict[str, Any]:
        return {
            "session": {
                "tier1_date": session.tier1_date.isoformat(),
                "tier2_date": session.tier2_date.isoformat(),
                "tier3_date": session.tier3_date.isoformat(),
                "tier1_budget": float(session.tier1_balance),
                "tier2_budget": float(session.tier2_balance),
                "tier3_budget": float(session.tier3_balance),
            },
            "child": {
                "name": session.child_name or "Child",
                "age": session.child_age,
                "gender": session.child_gender or "unspecified",
            },
            "capsule": capsule,
        }

    def _call_claude(self, prompt_data: dict[str, Any]) -> dict[str, Any]:
        child = prompt_data["child"]
        sess = prompt_data["session"]
        user_message = f"""Child: {child['name']}, age {child['age']}, {child['gender']}

Budget & Timeline:
- Tier 1 (by {sess['tier1_date']}): ${sess['tier1_budget']}
- Tier 2 (by {sess['tier2_date']}): ${sess['tier2_budget']}
- Tier 3 (by {sess['tier3_date']}): ${sess['tier3_budget']}

Capsule needed (total quantities):
{json.dumps(prompt_data['capsule'], indent=2)}

Create tiered purchase plan. Return this JSON structure (no markdown):
{{
  "tier1": {{
    "budget": NUMBER,
    "purchaseBy": "DATE_ISO",
    "justification": "STRING",
    "items": [
      {{"category": "STRING", "quantity": NUMBER, "estimatedCost": NUMBER, "priority": "MUST_HAVE", "note": "STRING"}}
    ],
    "totalEstimated": NUMBER,
    "remaining": NUMBER
  }},
  "tier2": {{
    "budget": NUMBER,
    "purchaseBy": "DATE_ISO",
    "contingency": "STRING",
    "justification": "STRING",
    "items": [],
    "totalEstimated": NUMBER,
    "remaining": NUMBER
  }},
  "tier3": {{
    "budget": NUMBER,
    "purchaseBy": "DATE_ISO",
    "contingency": "STRING",
    "justification": "STRING",
    "items": [],
    "totalEstimated": NUMBER,
    "remaining": NUMBER
  }},
  "summary": {{
    "totalBudgetAvailable": NUMBER,
    "totalEstimatedSpend": NUMBER,
    "bufferRemaining": NUMBER,
    "jobDependent": false,
    "fallbackIfJobFails": "STRING"
  }},
  "warnings": ["STRING"]
}}"""

        raw = self._invoke_llm(_SYSTEM_PROMPT, user_message)
        plan = self._parse_plan_json(raw)
        if plan is not None:
            return plan

        raw = self._invoke_llm(_SYSTEM_PROMPT, user_message + _RETRY_APPEND)
        plan = self._parse_plan_json(raw)
        if plan is None:
            raise ValueError(f"Claude returned invalid JSON: {(raw or '')[:200]}")
        return plan

    def _invoke_llm(self, system: str, user_message: str) -> str:
        if self._llm_caller is not None:
            return self._llm_caller(system, user_message)

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=2000,
                system=system,
                messages=[{"role": "user", "content": user_message}],
            )
            block = response.content[0] if response.content else None
            return (getattr(block, "text", None) or "").strip()
        except Exception as exc:
            logger.exception("BTS purchase plan Claude call failed: %s", exc)
            raise ValueError(f"Claude API call failed: {exc}") from exc

    @staticmethod
    def _parse_plan_json(raw: str | None) -> dict[str, Any] | None:
        if not raw:
            return None
        cleaned = _strip_markdown_fences(raw)
        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError:
            return None
        return data if isinstance(data, dict) else None

    def _validate_plan_structure(self, plan: dict[str, Any]) -> None:
        required_keys = ["tier1", "tier2", "tier3", "summary", "warnings"]
        for key in required_keys:
            if key not in plan:
                raise ValueError(f"Claude plan missing required key: {key}")

        for tier_key in ("tier1", "tier2", "tier3"):
            tier = plan[tier_key]
            if not isinstance(tier, dict):
                raise ValueError(f"{tier_key} must be an object")
            for key in _TIER_REQUIRED:
                if key not in tier:
                    raise ValueError(f"{tier_key} missing required key: {key}")
            if not isinstance(tier["items"], list):
                raise ValueError(f"{tier_key} items must be a list")

        if not isinstance(plan["summary"], dict):
            raise ValueError("summary must be an object")
        if not isinstance(plan["warnings"], list):
            raise ValueError("warnings must be a list")

    def _save_plan(
        self,
        user_id: str,
        session_id: uuid.UUID,
        plan_json: dict[str, Any],
    ) -> BackToSchoolPurchasePlan:
        existing = BackToSchoolPurchasePlan.query.filter_by(session_id=session_id).first()
        if existing:
            existing.plan_data = plan_json
            existing.user_id = user_id
            db.session.commit()
            return existing

        plan = BackToSchoolPurchasePlan(
            session_id=session_id,
            user_id=user_id,
            plan_data=plan_json,
        )
        db.session.add(plan)
        db.session.commit()
        return plan

    @staticmethod
    def get_plan(session_id: str | uuid.UUID) -> dict[str, Any] | None:
        sid = _parse_session_id(session_id)
        plan = BackToSchoolPurchasePlan.query.filter_by(session_id=sid).first()
        if not plan:
            return None
        return plan.to_dict()


# Default singleton used by routes.
bts_plan_service = BtsPurchasePlanService()
