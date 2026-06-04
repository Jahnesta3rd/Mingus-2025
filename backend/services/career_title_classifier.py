"""LLM and rule-based career title classification with usage logging."""

from __future__ import annotations

import json
import logging
import re
import time
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any

import anthropic

from backend.models.llm_usage import LlmUsage

logger = logging.getLogger(__name__)

HAIKU_INPUT_COST_PER_TOKEN = 0.00000025
HAIKU_OUTPUT_COST_PER_TOKEN = 0.00000125

MODEL = "claude-haiku-4-5-20251001"

VALID_CAREER_FIELDS = frozenset(
    {
        "Technology",
        "Healthcare (Clinical)",
        "Healthcare (Admin/Ops)",
        "Finance & Accounting",
        "Legal",
        "Marketing & Communications",
        "Sales",
        "Education & Training",
        "Engineering (Civil/Mech/Ind)",
        "Creative & Design",
        "Operations & Supply Chain",
        "Human Resources",
        "Real Estate",
        "Social Services & Nonprofit",
        "Government & Public Policy",
        "Hospitality & Food Service",
        "Retail & Consumer",
        "Construction & Trades",
        "Media & Journalism",
        "Science & Research",
        "Military / Veterans",
        "Self-Employed / Entrepreneurship",
    }
)

SYSTEM_PROMPT = (
    "You are a career classification assistant. Given a job title and "
    "optional industry, return ONLY a JSON object with these exact keys: "
    "career_field, seniority_level, is_management, confidence. "
    "career_field must be exactly one of these 22 values: "
    "Technology | Healthcare (Clinical) | Healthcare (Admin/Ops) | "
    "Finance & Accounting | Legal | Marketing & Communications | Sales | "
    "Education & Training | Engineering (Civil/Mech/Ind) | Creative & Design | "
    "Operations & Supply Chain | Human Resources | Real Estate | "
    "Social Services & Nonprofit | Government & Public Policy | "
    "Hospitality & Food Service | Retail & Consumer | Construction & Trades | "
    "Media & Journalism | Science & Research | Military / Veterans | "
    "Self-Employed / Entrepreneurship. "
    "seniority_level: entry | mid | senior | director. "
    "is_management: true or false. "
    "confidence: float 0.0 to 1.0. "
    "Return nothing except the JSON object. No markdown. No explanation."
)

_FIELD_KEYWORDS: list[tuple[str, tuple[str, ...]]] = [
    ("Technology", ("engineer", "developer", "software", "sre", "devops", "data scien")),
    ("Healthcare (Clinical)", ("nurse", "physician", "therapist", "clinician", "rn", "np", "pa", "md")),
    ("Legal", ("attorney", "lawyer", "counsel", "paralegal")),
    ("Finance & Accounting", ("accountant", "cpa", "controller", "auditor", "cfo")),
    ("Education & Training", ("teacher", "professor", "instructor", "curriculum")),
    ("Creative & Design", ("designer", "ux", "ui", "art director")),
    ("Social Services & Nonprofit", ("social worker", "case manager")),
    ("Military / Veterans", ("general", "colonel", "sergeant", "veteran", "military")),
]

_SENIORITY_KEYWORDS: list[tuple[str, tuple[str, ...]]] = [
    ("entry", ("intern", "junior", "associate", "entry")),
    ("senior", ("senior", "lead", "staff", "principal", "sr.")),
    ("director", ("director", "vp", "vice president", "chief")),
]

_MANAGEMENT_KEYWORDS = ("manager", "head of", "people manager")


def log_llm_usage(db_session, **kwargs) -> None:
    """Write one row to llm_usage; never propagate logging failures."""
    try:
        row = LlmUsage(**kwargs)
        db_session.add(row)
        db_session.commit()
    except Exception:
        logger.error("Failed to log LLM usage", exc_info=True)
        try:
            db_session.rollback()
        except Exception:
            pass


def classify_by_rules(raw_title: str) -> dict:
    """Pure rule-based fallback. No DB, no API, no logging."""
    title_lower = (raw_title or "").lower()
    matched = False
    career_field = "Self-Employed / Entrepreneurship"

    for field, keywords in _FIELD_KEYWORDS:
        if any(kw in title_lower for kw in keywords):
            career_field = field
            matched = True
            break

    seniority_level = "mid"
    for level, keywords in _SENIORITY_KEYWORDS:
        if any(kw in title_lower for kw in keywords):
            seniority_level = level
            break

    is_management = any(kw in title_lower for kw in _MANAGEMENT_KEYWORDS)
    confidence = 0.6 if matched else 0.3

    return {
        "career_field": career_field,
        "seniority_level": seniority_level,
        "is_management": is_management,
        "confidence": confidence,
    }


def _parse_llm_json(text: str) -> dict:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)
    return json.loads(cleaned)


def classify_career_title(
    raw_title: str,
    raw_industry: str | None,
    user_id: int | None,
    db_session,
) -> dict:
    """Classify a job title via Claude Haiku, with rule-based fallback."""
    start = time.time()
    model = MODEL

    try:
        client = anthropic.Anthropic()
        response = client.messages.create(
            model=model,
            max_tokens=150,
            system=SYSTEM_PROMPT,
            messages=[
                {
                    "role": "user",
                    "content": f"Title: {raw_title}\nIndustry: {raw_industry or 'unknown'}",
                }
            ],
        )

        latency_ms = int((time.time() - start) * 1000)
        input_tokens = response.usage.input_tokens
        output_tokens = response.usage.output_tokens
        cost_usd = Decimal(str(
            (input_tokens * HAIKU_INPUT_COST_PER_TOKEN)
            + (output_tokens * HAIKU_OUTPUT_COST_PER_TOKEN)
        ))

        parsed = _parse_llm_json(response.content[0].text)
        career_field = parsed.get("career_field", "")

        if career_field not in VALID_CAREER_FIELDS:
            fallback = classify_by_rules(raw_title)
            log_llm_usage(
                db_session,
                user_id=user_id,
                feature="career_title_classification",
                model=model,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                total_tokens=input_tokens + output_tokens,
                cost_usd=cost_usd,
                classification_source="rule",
                result_field=fallback["career_field"],
                confidence=fallback["confidence"],
                latency_ms=latency_ms,
            )
            fallback["source"] = "rule"
            return fallback

        result = {
            "career_field": career_field,
            "seniority_level": parsed.get("seniority_level", "mid"),
            "is_management": bool(parsed.get("is_management", False)),
            "confidence": float(parsed.get("confidence", 0.0)),
        }

        log_llm_usage(
            db_session,
            user_id=user_id,
            feature="career_title_classification",
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=input_tokens + output_tokens,
            cost_usd=cost_usd,
            classification_source="llm",
            result_field=result["career_field"],
            confidence=result["confidence"],
            latency_ms=latency_ms,
        )
        result["source"] = "llm"
        return result

    except Exception as exc:
        latency_ms = int((time.time() - start) * 1000)
        log_llm_usage(
            db_session,
            user_id=user_id,
            feature="career_title_classification",
            model=model,
            input_tokens=0,
            output_tokens=0,
            total_tokens=0,
            cost_usd=Decimal("0"),
            classification_source="fallback_on_error",
            error_message=str(exc)[:500],
            latency_ms=latency_ms,
        )
        fallback = classify_by_rules(raw_title)
        fallback["source"] = "fallback_on_error"
        return fallback


def get_llm_usage_summary(db_session, days: int = 30) -> dict:
    """Return usage totals for the last N days."""
    cutoff = datetime.utcnow() - timedelta(days=days)
    rows = (
        db_session.query(LlmUsage)
        .filter(LlmUsage.created_at >= cutoff)
        .all()
    )

    total_calls = len(rows)
    llm_calls = sum(1 for r in rows if r.classification_source == "llm")
    rule_calls = sum(1 for r in rows if r.classification_source == "rule")
    error_fallbacks = sum(1 for r in rows if r.classification_source == "fallback_on_error")
    total_input_tokens = sum(r.input_tokens for r in rows)
    total_output_tokens = sum(r.output_tokens for r in rows)
    total_cost_usd = float(sum(float(r.cost_usd or 0) for r in rows))

    latencies = [r.latency_ms for r in rows if r.latency_ms is not None]
    avg_latency_ms = sum(latencies) / len(latencies) if latencies else 0.0

    by_feature: dict[str, dict[str, Any]] = {}
    for row in rows:
        feat = row.feature
        if feat not in by_feature:
            by_feature[feat] = {"calls": 0, "cost_usd": 0.0}
        by_feature[feat]["calls"] += 1
        by_feature[feat]["cost_usd"] += float(row.cost_usd or 0)

    return {
        "total_calls": total_calls,
        "llm_calls": llm_calls,
        "rule_calls": rule_calls,
        "error_fallbacks": error_fallbacks,
        "total_input_tokens": total_input_tokens,
        "total_output_tokens": total_output_tokens,
        "total_cost_usd": total_cost_usd,
        "avg_latency_ms": avg_latency_ms,
        "by_feature": by_feature,
    }
