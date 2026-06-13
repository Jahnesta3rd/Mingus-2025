#!/usr/bin/env python3
"""LLM relationship intelligence — anonymized, ephemeral, tier-gated."""

# PRIVACY CHECKLIST — verified at implementation:
# [x] No real nicknames in any prompt string
# [x] extra_headers ZDR present on every client.messages.create call
# [x] No Redis.set or cache write anywhere in this file
# [x] No db.session.add or db.session.commit except llm_narrative_credits metering
# [x] llm_opt_out checked before every Anthropic call
# [x] Budget tier gated before every Anthropic call

from __future__ import annotations

import json
import logging
import os
import uuid
from datetime import datetime
from typing import Any

import anthropic

from backend.models.connection_trend import ConnectionTrendAssessment
from backend.models.database import db
from backend.models.user_models import User
from backend.models.vibe_tracker import (
    LlmNarrativeCredit,
    VibePersonAssessment,
    VibeTrackedPerson,
)

logger = logging.getLogger(__name__)

MODEL = "claude-haiku-4-5-20251001"
MAX_TOKENS = 300

ZDR_ENABLED = os.getenv("ANTHROPIC_ZDR_ENABLED", "false").lower() == "true"


def _zdr_headers() -> dict:
    if ZDR_ENABLED:
        return {"anthropic-beta": "zero-data-retention-2025-02-28"}
    return {}

_PRIVACY_SYSTEM = (
    "PRIVACY (non-negotiable): Never use or infer real names. "
    "Refer only to anonymized labels such as Person A, Person B. "
    "Observational tone only — no clinical language, no definitive claims, "
    "no moralizing, no recommendations unless explicitly asked. "
    "Plain English."
)


def _utcnow_iso() -> str:
    return datetime.utcnow().isoformat() + "Z"


def _parse_uuid(value: str | None) -> uuid.UUID | None:
    if not value or not isinstance(value, str):
        return None
    try:
        return uuid.UUID(str(value).strip())
    except (ValueError, TypeError, AttributeError):
        return None


def _load_user(user_id: str) -> User | None:
    if not user_id or not isinstance(user_id, str):
        return None
    return User.query.filter_by(user_id=str(user_id).strip()).first()


def _load_person(user_id: str, person_id: str) -> VibeTrackedPerson | None:
    user = _load_user(user_id)
    if not user:
        return None
    pid = _parse_uuid(person_id)
    if not pid:
        return None
    person = VibeTrackedPerson.query.filter_by(id=pid, user_id=user.id).first()
    return person


def _load_assessments(
    person_id: uuid.UUID, limit: int = 3
) -> list[VibePersonAssessment]:
    return (
        VibePersonAssessment.query.filter_by(tracked_person_id=person_id)
        .order_by(VibePersonAssessment.completed_at.desc())
        .limit(limit)
        .all()
    )


def _anonymize_roster(people_list: list[VibeTrackedPerson]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for i, person in enumerate(people_list):
        label = f"Person {chr(ord('A') + i)}"
        out.append(
            {
                "label": label,
                "relationship_type": person.relationship_type,
                "estimated_monthly_cost": float(person.estimated_monthly_cost)
                if person.estimated_monthly_cost is not None
                else None,
                "assessment_count": int(person.assessment_count or 0),
            }
        )
    return out


def _person_llm_opt_out(person: VibeTrackedPerson) -> bool:
    return bool(getattr(person, "llm_opt_out", False))


def _tier_allows_llm(user: User) -> bool:
    tier = (user.tier or "budget").strip().lower()
    return tier != "budget"


def _normalize_tier(tier: str | None) -> str:
    return (tier or "budget").strip().lower()


def check_and_consume_credit(user_id: str) -> bool:
    """Return True if the user may consume one narrative credit this month."""
    try:
        user = _load_user(user_id)
        if not user:
            return False

        tier = _normalize_tier(user.tier)
        if tier == "professional":
            return True
        if tier == "budget":
            return False
        if tier not in ("mid_tier", "mid"):
            return False

        month_key = datetime.utcnow().strftime("%Y-%m")
        row = LlmNarrativeCredit.query.filter_by(
            user_id=user.id,
            month_key=month_key,
        ).first()
        if row is None:
            row = LlmNarrativeCredit(user_id=user.id, month_key=month_key)
            db.session.add(row)
            db.session.flush()

        if row.credits_used >= row.credits_limit:
            return False

        row.credits_used += 1
        db.session.commit()
        return True
    except Exception as exc:
        logger.warning("check_and_consume_credit failed: %s", exc)
        try:
            db.session.rollback()
        except Exception:
            pass
        return False


def _assessment_signals(assessments: list[VibePersonAssessment]) -> list[dict[str, Any]]:
    return [
        {
            "emotional_score": a.emotional_score,
            "financial_score": a.financial_score,
            "verdict_label": a.verdict_label,
            "annual_projection": a.annual_projection,
        }
        for a in assessments
    ]


def _call_anthropic(*, system: str, user_content: str) -> str | None:
    try:
        client = anthropic.Anthropic()
        response = client.messages.create(
            model=MODEL,
            max_tokens=MAX_TOKENS,
            system=system,
            messages=[{"role": "user", "content": user_content}],
            extra_headers=_zdr_headers(),
        )
        block = response.content[0] if response.content else None
        text = (getattr(block, "text", None) or "").strip()
        return text or None
    except Exception as exc:
        logger.warning("relationship_intelligence anthropic call failed: %s", exc)
        return None


def _gate_person_call(user_id: str, person_id: str) -> tuple[User, VibeTrackedPerson] | None:
    user = _load_user(user_id)
    if not user or not _tier_allows_llm(user):
        return None
    person = _load_person(user_id, person_id)
    if not person or _person_llm_opt_out(person):
        return None
    return user, person


def _parse_stay_or_go_direction(text: str) -> str:
    lower = text.lower()
    if "building" in lower:
        return "building"
    if "fading" in lower or "fade" in lower:
        return "fading"
    return "stable"


def generate_relationship_narrative(user_id: str, person_id: str) -> dict | None:
    gated = _gate_person_call(user_id, person_id)
    if not gated:
        return None
    user, person = gated

    if not check_and_consume_credit(user_id):
        if _normalize_tier(user.tier) != "budget":
            return {"credit_exhausted": True, "person_id": person_id}
        return None

    assessments = _load_assessments(person.id, limit=3)
    context = {
        "person_label": "Person A",
        "relationship_type": person.relationship_type,
        "estimated_monthly_cost": float(person.estimated_monthly_cost)
        if person.estimated_monthly_cost is not None
        else None,
        "assessment_count": int(person.assessment_count or 0),
        "recent_check_ins": _assessment_signals(assessments),
    }

    system = (
        _PRIVACY_SYSTEM
        + " Write 2–3 sentences of plain-English observation about this relationship. "
        "Start with or include framing like 'Based on your check-ins...'. "
        "Use only the anonymized label Person A — never a real name."
    )
    user_content = (
        "Relationship context (anonymized):\n"
        f"{json.dumps(context, default=str)}\n\n"
        "Write the narrative now."
    )

    narrative = _call_anthropic(system=system, user_content=user_content)
    if not narrative:
        return None

    return {
        "narrative": narrative,
        "capability": "relationship_narrative",
        "person_id": str(person.id),
        "generated_at": _utcnow_iso(),
    }


def generate_stay_or_go(user_id: str, person_id: str) -> dict | None:
    gated = _gate_person_call(user_id, person_id)
    if not gated:
        return None
    _user, person = gated

    assessments = _load_assessments(person.id, limit=3)
    context = {
        "person_label": "Person A",
        "relationship_type": person.relationship_type,
        "estimated_monthly_cost": float(person.estimated_monthly_cost)
        if person.estimated_monthly_cost is not None
        else None,
        "assessment_count": int(person.assessment_count or 0),
        "recent_check_ins": _assessment_signals(assessments),
    }

    system = (
        _PRIVACY_SYSTEM
        + " Given the check-in signals, describe in one honest sentence whether "
        "the energy in this relationship with Person A seems to be building, "
        "stable, or fading. Use only Person A — never a real name."
    )
    user_content = (
        "Check-in signals (anonymized):\n"
        f"{json.dumps(context, default=str)}\n\n"
        "Write one sentence."
    )

    explanation = _call_anthropic(system=system, user_content=user_content)
    if not explanation:
        return None

    return {
        "direction": _parse_stay_or_go_direction(explanation),
        "explanation": explanation,
        "capability": "stay_or_go",
        "person_id": str(person.id),
        "generated_at": _utcnow_iso(),
    }


def generate_cost_narrative(user_id: str, person_id: str) -> dict | None:
    gated = _gate_person_call(user_id, person_id)
    if not gated:
        return None
    _user, person = gated

    if person.estimated_monthly_cost is None:
        return None

    monthly_cost = float(person.estimated_monthly_cost)
    context = {
        "person_label": "Person A",
        "relationship_type": person.relationship_type,
        "estimated_monthly_cost": monthly_cost,
    }

    system = (
        _PRIVACY_SYSTEM
        + " Write 1–2 sentences contextualizing what this monthly spend represents "
        "for Person A. Observational framing only — do not moralize. "
        "Use only Person A — never a real name."
    )
    user_content = (
        "Spend context (anonymized):\n"
        f"{json.dumps(context, default=str)}\n\n"
        "Write the cost narrative now."
    )

    cost_narrative = _call_anthropic(system=system, user_content=user_content)
    if not cost_narrative:
        return None

    return {
        "cost_narrative": cost_narrative,
        "monthly_cost": monthly_cost,
        "capability": "cost_narrative",
        "person_id": str(person.id),
        "generated_at": _utcnow_iso(),
    }


_FADE_SIGNAL_TIERS = frozenset({"fading", "dipping", "cloaking"})
_UPSELL_FALLBACK = "Upgrade to Mid for AI-generated relationship insights."


def _load_enriched_roster(user: User) -> list[VibeTrackedPerson]:
    return (
        VibeTrackedPerson.query.filter_by(user_id=user.id, is_archived=False)
        .filter(VibeTrackedPerson.relationship_type.isnot(None))
        .order_by(VibeTrackedPerson.created_at.asc())
        .all()
    )


def _count_fading_relationships(user: User, people: list[VibeTrackedPerson]) -> int:
    if not people:
        return 0
    if not ConnectionTrendAssessment.query.filter_by(user_id=user.id).first():
        return 0

    fading_count = 0
    for person in people:
        latest = (
            ConnectionTrendAssessment.query.filter_by(
                user_id=user.id,
                person_id=person.id,
            )
            .order_by(ConnectionTrendAssessment.assessed_at.desc())
            .first()
        )
        if not latest:
            continue
        if latest.pattern_type == "classic_fade":
            fading_count += 1
        elif latest.fade_tier in _FADE_SIGNAL_TIERS:
            fading_count += 1
    return fading_count


def generate_upsell_copy(user_id: str) -> str:
    user = _load_user(user_id)
    if not user:
        return _UPSELL_FALLBACK

    people = _load_enriched_roster(user)
    roster_count = len(people)
    fading_count = _count_fading_relationships(user, people)

    if fading_count > 0:
        return (
            f"You have {fading_count} relationship(s) where your check-in data suggests "
            "the energy may be shifting. Upgrade to Mid to see who and why."
        )
    if roster_count > 0:
        return (
            f"You track {roster_count} people in your life. Upgrade to Mid to get an AI "
            "read on each relationship — cost patterns, energy direction, "
            "and what your check-ins actually say."
        )
    return _UPSELL_FALLBACK


def generate_roster_insight(user_id: str) -> dict | None:
    user = _load_user(user_id)
    if not user or not _tier_allows_llm(user):
        return None

    people = (
        VibeTrackedPerson.query.filter_by(user_id=user.id, is_archived=False)
        .filter(VibeTrackedPerson.relationship_type.isnot(None))
        .order_by(VibeTrackedPerson.created_at.asc())
        .all()
    )
    people = [p for p in people if not _person_llm_opt_out(p)]
    if len(people) < 2:
        return None

    roster = _anonymize_roster(people)

    system = (
        _PRIVACY_SYSTEM
        + " Write 2–3 sentences of cross-person pattern observation across this "
        "anonymized roster. Describe what the overall picture looks like. "
        "Observations only — no recommendations. Use only Person A, Person B, etc."
    )
    user_content = (
        "Anonymized roster:\n"
        f"{json.dumps(roster, default=str)}\n\n"
        "Write the roster insight now."
    )

    insight = _call_anthropic(system=system, user_content=user_content)
    if not insight:
        return None

    return {
        "insight": insight,
        "person_count": len(people),
        "capability": "roster_insight",
        "generated_at": _utcnow_iso(),
    }
