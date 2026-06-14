#!/usr/bin/env python3
"""LLM-generated homeownership action plans from gap analysis results."""

from __future__ import annotations

import json
import logging
import re
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any

import anthropic

from backend.models.database import db
from backend.models.gap_analysis import GapAnalysisResult
from backend.models.housing_profile import HousingProfile
from backend.services.hprs_input_service import get_hprs_inputs

logger = logging.getLogger(__name__)

_LLM_MODEL = "claude-sonnet-4-6"
_MAX_TOKENS = 1500
_CACHE_DAYS = 30
_RETRY_APPEND = "\n\nReturn only raw JSON. No backticks, no prose, no markdown."

_REQUIRED_PLAN_KEYS = (
    "summary",
    "pillar_1",
    "pillar_2",
    "pillar_3",
    "unified_timeline",
    "scenario_label",
)

_SYSTEM_PROMPT = (
    "You are a homeownership advisor for Black professionals in the US.\n"
    "You coordinate three levers — savings, career income, and a second\n"
    "income stream — into a unified action plan. Return ONLY valid JSON.\n"
    "No preamble, no markdown fences, no explanation outside the JSON.\n"
    "The JSON must contain exactly these top-level keys:\n"
    "summary, pillar_1, pillar_2, pillar_3, unified_timeline,\n"
    "scenario_label."
)

_OUTPUT_SCHEMA = """REQUIRED JSON OUTPUT SCHEMA:
{
  'summary': '2-3 sentence plain-English assessment of where
              this buyer stands and what the plan coordinates',

  'pillar_1': {
    'title': 'Savings Acceleration',
    'invoke': true,  // always true
    'monthly_target': float,   // required_monthly_savings
    'current_monthly': float,  // current_monthly_savings
    'gap': float,
    'actions': [str, str, str],  // 3 concrete monthly actions
    'timeline_months': int       // months to close savings gap
  },

  'pillar_2': {
    'title': 'Career Income Growth',
    'invoke': bool,  // true if income_severity is stretched or blocked
    'income_gap': float,
    'actions': [str, str],   // 2 career actions
    'timeline_months': int
  },

  'pillar_3': {
    'title': 'Second Income Stream',
    'invoke': bool,  // true if income_severity is blocked
    'monthly_target': float,  // income gap / 2 (split between career and side income)
    'job_types': [str, str],  // 2 suggested job types based on profile
    'timeline_months': int
  },

  'unified_timeline': [
    {'month': int, 'milestone': str, 'pillar': str}
  ],  // 3-6 milestones across the timeline

  'scenario_label': str  // e.g. 'On track in 18 months' or
                         // 'Achievable in 24 months with income boost'
}"""


class ActionPlanGenerationError(Exception):
    """Raised when the LLM plan cannot be generated or parsed."""


def _to_float(value: Decimal | float | int | None) -> float:
    if value is None:
        return 0.0
    if isinstance(value, Decimal):
        return float(value)
    return float(value)


def _load_current_situation(user_id: int) -> dict[str, Any]:
    hprs_inputs = get_hprs_inputs(user_id)
    gross_monthly_income = hprs_inputs.get("gross_monthly_income")
    total_monthly_obligations = hprs_inputs.get("total_monthly_obligations")
    credit_score = hprs_inputs.get("credit_score")

    current_monthly_savings = 0.0
    if gross_monthly_income is not None and total_monthly_obligations is not None:
        surplus = gross_monthly_income - total_monthly_obligations
        if surplus > 0:
            current_monthly_savings = float(surplus)

    housing = HousingProfile.query.filter_by(user_id=user_id).first()
    if housing and housing.down_payment_saved is not None:
        current_savings_balance = float(housing.down_payment_saved)
    else:
        saved = hprs_inputs.get("down_payment_saved")
        current_savings_balance = float(saved) if saved is not None else 0.0

    return {
        "gross_monthly_income": gross_monthly_income,
        "current_monthly_savings": current_monthly_savings,
        "current_savings_balance": current_savings_balance,
        "back_end_dti": float(hprs_inputs.get("current_dti") or 0),
        "credit_score": credit_score,
    }


def _format_money(value: float | None) -> str:
    if value is None:
        return "Unknown"
    return f"${value:,.0f}"


def _build_user_message(row: GapAnalysisResult, current: dict[str, Any]) -> str:
    home_price = _to_float(row.home_price)
    target_down_payment = _to_float(row.target_down_payment)
    monthly_piti = _to_float(row.monthly_piti)
    required_gross_income = _to_float(row.required_gross_income)
    required_monthly_savings = _to_float(row.required_monthly_savings)
    gap_income = _to_float(row.gap_income)
    gap_savings_rate = _to_float(row.gap_savings_rate)
    gap_down_payment = _to_float(row.gap_down_payment)
    gap_dti = _to_float(row.gap_dti)
    gap_credit = row.gap_credit

    gross_income = current.get("gross_monthly_income")
    credit_score = current.get("credit_score")

    return (
        "HOME PURCHASE TARGET\n"
        f"Home price: {_format_money(home_price)}\n"
        f"Down payment needed: {_format_money(target_down_payment)}\n"
        f"Monthly PITI: {_format_money(monthly_piti)}\n"
        f"Required gross income: {_format_money(required_gross_income)}/month\n"
        f"Required monthly savings: {_format_money(required_monthly_savings)}/month\n"
        f"Timeline: {row.timeline_months} months\n"
        "\n"
        "CURRENT SITUATION\n"
        f"Gross monthly income: {_format_money(gross_income)}/month\n"
        f"Current monthly savings: {_format_money(current['current_monthly_savings'])}/month\n"
        f"Down payment saved: {_format_money(current['current_savings_balance'])}\n"
        f"Back-end DTI: {current['back_end_dti']:.1%}\n"
        f"Credit score: {credit_score if credit_score is not None else 'Unknown'}\n"
        "\n"
        "GAP ANALYSIS\n"
        f"Income gap: {_format_money(gap_income)}/month ({row.income_severity})\n"
        f"Savings rate gap: {_format_money(gap_savings_rate)}/month ({row.savings_severity})\n"
        f"Down payment gap: {_format_money(gap_down_payment)} ({row.down_payment_severity})\n"
        f"DTI gap: {gap_dti:.1%} ({row.dti_severity})\n"
        f"Credit gap: {gap_credit if gap_credit is not None else 'N/A'} points "
        f"({row.credit_severity or 'unknown'})\n"
        "\n"
        f"{_OUTPUT_SCHEMA}"
    )


def _parse_plan_json(raw: str) -> dict[str, Any]:
    clean = re.sub(
        r"^```json\s*|^```\s*|```$",
        "",
        raw.strip(),
        flags=re.MULTILINE,
    ).strip()
    try:
        parsed = json.loads(clean)
    except json.JSONDecodeError as exc:
        raise ActionPlanGenerationError(
            f"Failed to parse plan JSON: {clean[:200]}"
        ) from exc
    if not isinstance(parsed, dict):
        raise ActionPlanGenerationError("Plan JSON must be an object")
    return parsed


def _validate_plan_json(plan_json: dict[str, Any]) -> None:
    missing = [key for key in _REQUIRED_PLAN_KEYS if key not in plan_json]
    if missing:
        raise ActionPlanGenerationError(f"Plan missing required fields: {missing}")


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


def _is_cache_valid(row: GapAnalysisResult, now: datetime) -> bool:
    return (
        row.action_plan_json is not None
        and row.expires_at is not None
        and row.expires_at > now
    )


def generate_action_plan(gap_analysis_id: int, user_id: int) -> dict[str, Any]:
    """Generate or return cached action plan for a gap analysis snapshot."""
    row = GapAnalysisResult.query.get(gap_analysis_id)
    if row is None or row.user_id != user_id:
        raise ValueError("Gap analysis not found")

    now = datetime.utcnow()
    if _is_cache_valid(row, now):
        return row.action_plan_json

    current = _load_current_situation(user_id)
    user_message = _build_user_message(row, current)
    raw_text = _call_anthropic(user_message)

    try:
        plan_json = _parse_plan_json(raw_text)
        _validate_plan_json(plan_json)
    except ActionPlanGenerationError:
        raw_text = _call_anthropic(user_message, retry_append=_RETRY_APPEND)
        try:
            plan_json = _parse_plan_json(raw_text)
            _validate_plan_json(plan_json)
        except ActionPlanGenerationError:
            logger.error(
                "generate_action_plan: failed to parse plan for gap_analysis_id=%s raw=%s",
                gap_analysis_id,
                raw_text,
            )
            raise ActionPlanGenerationError("Plan generation failed") from None

    row.action_plan_json = plan_json
    row.plan_generated_at = now
    row.expires_at = now + timedelta(days=_CACHE_DAYS)
    db.session.commit()

    return plan_json
