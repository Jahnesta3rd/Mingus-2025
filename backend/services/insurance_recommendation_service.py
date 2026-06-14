#!/usr/bin/env python3
"""LLM-generated health insurance plan recommendations."""

from __future__ import annotations

import json
import logging
import re
from datetime import datetime, timedelta
from typing import Any

import anthropic

from backend.models.database import db
from backend.models.health_insurance_plan import HealthInsurancePlan
from backend.models.health_insurance_recommendation import HealthInsuranceRecommendation
from backend.services.insurance_plan_scorer import _load_usage_context, score_plans

logger = logging.getLogger(__name__)

_LLM_MODEL = "claude-sonnet-4-6"
_MAX_TOKENS = 1500
_CACHE_DAYS = 30
_RETRY_APPEND = "\n\nReturn only raw JSON. No backticks, no prose, no markdown."

_REQUIRED_KEYS = (
    "summary",
    "recommended_plan_name",
    "key_reason",
    "when_to_reconsider",
    "plan_comparisons",
    "risk_assessment",
    "hsa_guidance",
    "disclaimer",
)

_SYSTEM_PROMPT = (
    "You are a health insurance advisor helping a user choose between "
    "employer-sponsored health plans. You have access to plan cost data, "
    "the user's healthcare usage patterns, and their financial profile. "
    "Return ONLY valid JSON — no preamble, no markdown fences. "
    "The JSON must contain exactly these keys: "
    "summary, recommended_plan_name, key_reason, when_to_reconsider, "
    "plan_comparisons, risk_assessment, hsa_guidance, disclaimer. "
    "Never tell the user which plan to choose definitively — frame as "
    "'based on your usage pattern, Plan A has the lowest estimated cost.' "
    "Use plain English. No jargon."
)


class RecommendationGenerationError(Exception):
    """Raised when an insurance recommendation cannot be generated or parsed."""


def _format_money(value: float | None) -> str:
    if value is None:
        return "$0"
    return f"${value:,.0f}"


def _benchmark_summary(scored_plan: dict[str, Any]) -> str:
    benchmark = scored_plan.get("benchmark_context") or {}
    comparison = benchmark.get("comparison") or {}
    return comparison.get("summary_line") or "Benchmark unavailable"


def _build_user_message(
    usage: dict[str, Any],
    scored: list[dict[str, Any]],
) -> str:
    gross_monthly_income = usage.get("gross_monthly_income") or 0
    emergency_fund = usage.get("emergency_fund") or 0
    coverage_type = usage.get("coverage_type") or "self"
    rx_type = usage.get("rx_type") or "none"

    plan_blocks: list[str] = []
    for plan in scored:
        plan_blocks.append(
            "\n".join(
                [
                    f"  Plan: {plan['plan_name']} ({plan.get('plan_type') or 'unknown'})",
                    f"  Score: {plan['score']}/100",
                    f"  Estimated annual cost: {_format_money(plan['expected_annual_cost'])}",
                    f"  Monthly premium: {_format_money(plan.get('monthly_premium_employee') or 0)}",
                    f"  Deductible: {_format_money(plan.get('annual_deductible_individual') or 0)}",
                    f"  OOP max: {_format_money(plan.get('out_of_pocket_max_individual') or 0)}",
                    f"  HSA eligible: {plan.get('has_hsa_eligible')}",
                    f"  Risk flags: {plan.get('risk_flags') or []}",
                    f"  Benchmark: {_benchmark_summary(plan)}",
                ]
            )
        )

    return (
        "HEALTH INSURANCE PLAN COMPARISON\n\n"
        "User profile:\n"
        f"  Coverage: {coverage_type}\n"
        f"  Doctor visits/year: {usage.get('primary_care_visits')}\n"
        f"  Specialist visits/year: {usage.get('specialist_visits')}\n"
        f"  ER visits/year: {usage.get('er_visits')}\n"
        f"  Planned procedure: {usage.get('planned_procedure')}\n"
        f"  Takes prescriptions: {usage.get('takes_rx')} ({rx_type})\n"
        f"  Monthly income: {_format_money(gross_monthly_income)}\n"
        f"  Emergency fund: {_format_money(emergency_fund)}\n\n"
        "PLAN SCORES AND COSTS:\n"
        + "\n\n".join(plan_blocks)
        + "\n\n"
        "REQUIRED JSON OUTPUT:\n"
        "{\n"
        "  'summary': '2-3 sentence assessment of the comparison',\n"
        "  'recommended_plan_name': str,\n"
        "  'key_reason': str,\n"
        "  'when_to_reconsider': str,\n"
        "  'plan_comparisons': [\n"
        "    {\n"
        "      'plan_name': str,\n"
        "      'estimated_annual_cost': float,\n"
        "      'monthly_premium': float,\n"
        "      'deductible': float,\n"
        "      'oop_max': float,\n"
        "      'score': int,\n"
        "      'pros': [str],\n"
        "      'cons': [str]\n"
        "    }\n"
        "  ],\n"
        "  'risk_assessment': str,\n"
        "  'hsa_guidance': str | null,\n"
        "  'disclaimer': 'Cost estimates are based on your reported usage "
        "patterns. Actual costs depend on provider rates, network "
        "status, and claims. Verify provider networks before enrolling.'\n"
        "}"
    )


def _parse_recommendation_json(raw: str) -> dict[str, Any]:
    clean = re.sub(
        r"^```json\s*|^```\s*|```$",
        "",
        raw.strip(),
        flags=re.MULTILINE,
    ).strip()
    try:
        parsed = json.loads(clean)
    except json.JSONDecodeError as exc:
        raise RecommendationGenerationError(
            f"Failed to parse recommendation JSON: {clean[:200]}"
        ) from exc
    if not isinstance(parsed, dict):
        raise RecommendationGenerationError("Recommendation JSON must be an object")
    return parsed


def _validate_recommendation_json(recommendation_json: dict[str, Any]) -> None:
    missing = [key for key in _REQUIRED_KEYS if key not in recommendation_json]
    if missing:
        raise RecommendationGenerationError(
            f"Recommendation missing required fields: {missing}"
        )


def _call_anthropic(user_message: str, retry_append: str | None = None) -> str:
    content = user_message
    if retry_append:
        content += retry_append
    client = anthropic.Anthropic()
    response = client.messages.create(
        model=_LLM_MODEL,
        max_tokens=_MAX_TOKENS,
        system=_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": content}],
    )
    return response.content[0].text


def _build_input_snapshot(
    plans: list[HealthInsurancePlan],
    usage: dict[str, Any],
    scored: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "plan_count": len(plans),
        "usage_profile": {
            "coverage_type": usage.get("coverage_type"),
            "primary_care_visits": usage.get("primary_care_visits"),
            "specialist_visits": usage.get("specialist_visits"),
            "er_visits": usage.get("er_visits"),
            "planned_procedure": usage.get("planned_procedure"),
            "takes_rx": usage.get("takes_rx"),
            "rx_type": usage.get("rx_type"),
            "emergency_fund": usage.get("emergency_fund"),
            "gross_monthly_income": usage.get("gross_monthly_income"),
            "state_code": usage.get("state_code"),
        },
        "scored_plans": [
            {
                "plan_id": item["plan_id"],
                "score": item["score"],
                "expected_annual_cost": item["expected_annual_cost"],
            }
            for item in scored
        ],
    }


def _persist_recommendation(
    user_id: int,
    recommended: dict[str, Any],
    runner_up: dict[str, Any] | None,
    scored: list[dict[str, Any]],
    recommendation_json: dict[str, Any],
    usage: dict[str, Any],
    plans: list[HealthInsurancePlan],
    generated_at: datetime,
    expires_at: datetime,
) -> HealthInsuranceRecommendation:
    hsa_benefits = [
        item["hsa_opportunity"].get("estimated_tax_savings", 0)
        for item in scored
        if item.get("hsa_opportunity", {}).get("eligible")
    ]
    all_risk_flags = [flag for item in scored for flag in (item.get("risk_flags") or [])]

    existing = HealthInsuranceRecommendation.query.filter_by(user_id=user_id).first()
    if existing is not None:
        row = existing
    else:
        row = HealthInsuranceRecommendation(user_id=user_id)
        db.session.add(row)

    row.generated_at = generated_at
    row.expires_at = expires_at
    row.recommended_plan_id = recommended["plan_id"]
    row.runner_up_plan_id = runner_up["plan_id"] if runner_up else None
    row.recommendation_json = recommendation_json
    row.expected_annual_cost_recommended = recommended["expected_annual_cost"]
    row.expected_annual_cost_runner_up = (
        runner_up["expected_annual_cost"] if runner_up else None
    )
    row.hsa_recommended = any(
        item.get("hsa_opportunity", {}).get("eligible") for item in scored
    )
    row.hsa_annual_benefit = max(hsa_benefits) if hsa_benefits else None
    row.risk_flags_json = all_risk_flags
    row.benchmark_context_json = recommended.get("benchmark_context")
    row.model_version = _LLM_MODEL
    row.input_snapshot_json = _build_input_snapshot(plans, usage, scored)
    db.session.commit()
    return row


def generate_insurance_recommendation(user_id: int) -> dict[str, Any]:
    """Score plans, call Claude, persist, and return the recommendation payload."""
    plans = (
        HealthInsurancePlan.query.filter_by(user_id=user_id)
        .filter(HealthInsurancePlan.parse_status.in_(("completed", "manual")))
        .order_by(HealthInsurancePlan.id.asc())
        .all()
    )
    if len(plans) < 2:
        raise RecommendationGenerationError(
            "At least 2 plans required to generate a recommendation."
        )

    scored = score_plans(user_id, [plan.id for plan in plans])
    if not scored:
        raise RecommendationGenerationError("Plan scoring failed.")

    scored.sort(key=lambda item: item["score"], reverse=True)
    recommended = scored[0]
    runner_up = scored[1] if len(scored) > 1 else None

    usage = _load_usage_context(user_id)
    user_message = _build_user_message(usage, scored)
    raw_text = _call_anthropic(user_message)

    try:
        recommendation_json = _parse_recommendation_json(raw_text)
        _validate_recommendation_json(recommendation_json)
    except RecommendationGenerationError:
        raw_text = _call_anthropic(user_message, retry_append=_RETRY_APPEND)
        try:
            recommendation_json = _parse_recommendation_json(raw_text)
            _validate_recommendation_json(recommendation_json)
        except RecommendationGenerationError:
            logger.error(
                "generate_insurance_recommendation failed for user_id=%s raw=%s",
                user_id,
                raw_text,
            )
            raise RecommendationGenerationError("Recommendation generation failed") from None

    generated_at = datetime.utcnow()
    expires_at = generated_at + timedelta(days=_CACHE_DAYS)
    row = _persist_recommendation(
        user_id,
        recommended,
        runner_up,
        scored,
        recommendation_json,
        usage,
        plans,
        generated_at,
        expires_at,
    )

    all_risk_flags = [flag for item in scored for flag in (item.get("risk_flags") or [])]
    hsa_benefits = [
        item["hsa_opportunity"].get("estimated_tax_savings", 0)
        for item in scored
        if item.get("hsa_opportunity", {}).get("eligible")
    ]

    return {
        "recommendation": recommendation_json,
        "recommended_plan_id": recommended["plan_id"],
        "recommended_plan_name": recommended["plan_name"],
        "expected_annual_cost_recommended": recommended["expected_annual_cost"],
        "expected_annual_cost_runner_up": (
            runner_up["expected_annual_cost"] if runner_up else None
        ),
        "hsa_recommended": any(
            item.get("hsa_opportunity", {}).get("eligible") for item in scored
        ),
        "hsa_annual_benefit": max(hsa_benefits) if hsa_benefits else None,
        "risk_flags": all_risk_flags,
        "benchmark_context": recommended.get("benchmark_context") or {},
        "generated_at": row.generated_at.isoformat(),
        "expires_at": row.expires_at.isoformat(),
    }
