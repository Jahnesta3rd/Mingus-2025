#!/usr/bin/env python3
"""HPRS orchestrator — runs pillar scoring and risk modifiers into one result."""

from __future__ import annotations

import json
import logging
import re
from datetime import datetime
from typing import Any

import anthropic

from backend.models.database import db
from backend.models.hprs_plan import HprsPlan
from backend.models.hprs_score import HprsScore
from backend.services.hprs_career_risk_service import derive_career_risk
from backend.services.hprs_score_service import compute_hprs_score
from backend.services.hprs_vehicle_risk_service import derive_vehicle_risk

logger = logging.getLogger(__name__)


class HprsPlanParseError(Exception):
    """Raised when LLM plan output cannot be parsed or validated."""


_REQUIRED_PLAN_FIELDS = [
    "summary",
    "score_band",
    "plan_phases",
    "monthly_actions",
    "quick_wins",
    "watch_flags",
    "projected_score",
    "mortgage_estimate",
]

_LLM_MODEL = "claude-sonnet-4-6"
_RETRY_APPEND = "\n\nReturn only raw JSON. No backticks, no prose, no markdown."

_SYSTEM_PROMPT = (
    "You are a licensed mortgage planning advisor helping a first-time or repeat home buyer\n"
    "understand their readiness and build a concrete action plan. Analyze the financial profile\n"
    "below and return ONLY a valid JSON object. No preamble, no markdown fences, no explanation\n"
    "outside the JSON. The JSON must contain exactly these fields:\n"
    "summary, score_band, plan_phases, monthly_actions, quick_wins, watch_flags,\n"
    "projected_score, mortgage_estimate.\n"
    "Never tell the user they cannot buy a home. Frame all risk signals as timing and\n"
    "preparation factors. Use plain English — no jargon, no clinical language."
)

_OUTPUT_SCHEMA = """REQUIRED JSON OUTPUT SCHEMA:
{
  "summary": "2-3 sentence plain-English assessment",
  "score_band": "one of: Foundation First | Early Stage | Building Foundation | Nearly There | Ready to Move",
  "plan_phases": [{"phase_name": str, "duration_months": int, "goal": str, "actions": [str]}],
  "monthly_actions": [{"action": str, "impact_score": int, "dimension": str}],
  "quick_wins": [str],
  "watch_flags": [str],
  "projected_score": int,
  "mortgage_estimate": {"monthly_piti": float | null, "front_end_dti": float | null}
}
Return exactly 3 monthly_actions. Return 2-5 plan_phases. Return 1-3 quick_wins."""

_PILLAR_WEIGHTS = {
    "down_payment": 0.30,
    "dti": 0.25,
    "credit": 0.20,
    "income": 0.10,
    "reserves": 0.10,
}


def _iso_timestamp(value: Any) -> str | None:
    if value is None:
        return None
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return str(value)


def _assemble_result(
    row: HprsScore,
    career_result: dict[str, Any],
    vehicle_result: dict[str, Any],
) -> dict[str, Any]:
    inputs_snapshot = row.inputs_snapshot if isinstance(row.inputs_snapshot, dict) else {}
    partial_data = inputs_snapshot.get("partial_data")
    if partial_data is None:
        partial_data = bool(inputs_snapshot.get("partial_data", False))

    return {
        "overall_score": int(row.overall_score),
        "readiness_tier": row.readiness_tier,
        "partial_data": bool(partial_data),
        "computed_at": _iso_timestamp(row.computed_at),
        "pillars": {
            "down_payment": {
                "score": int(row.down_payment_score or 0),
                "weight": _PILLAR_WEIGHTS["down_payment"],
            },
            "dti": {
                "score": int(row.dti_score or 0),
                "weight": _PILLAR_WEIGHTS["dti"],
            },
            "credit": {
                "score": int(row.credit_score or 0),
                "weight": _PILLAR_WEIGHTS["credit"],
            },
            "income": {
                "score": int(row.income_stability_score or 0),
                "weight": _PILLAR_WEIGHTS["income"],
            },
            "reserves": {
                "score": int(row.savings_rate_score or 0),
                "weight": _PILLAR_WEIGHTS["reserves"],
            },
        },
        "career_risk": {
            "score": row.career_risk_score,
            "band": row.career_risk_band,
            "modifier": int(row.career_modifier or 0),
            "active_layoff": bool(career_result.get("active_layoff", False)),
        },
        "vehicle_risk": {
            "score": row.vehicle_risk_score,
            "band": row.vehicle_risk_band,
            "modifier": int(row.vehicle_modifier or 0),
            "verdict": vehicle_result.get("verdict"),
            "annual_repair_exposure": vehicle_result.get("annual_repair_exposure"),
        },
        "combined_modifier": int(row.combined_modifier or 0),
        "target_price": row.target_price,
        "target_timeline_months": row.target_timeline_months,
        "down_payment_saved": row.down_payment_saved,
        "down_payment_needed": row.down_payment_needed,
        "inputs_snapshot": inputs_snapshot,
    }


def compute_full_hprs(user_id: int) -> dict:
    """Run pillar scoring, career risk, and vehicle risk; return assembled HPRS dict."""
    career_result: dict[str, Any] = {}
    vehicle_result: dict[str, Any] = {}

    try:
        compute_hprs_score(user_id)
    except Exception:
        logger.warning(
            "compute_full_hprs: compute_hprs_score failed for user_id=%s",
            user_id,
            exc_info=True,
        )
        return {"error": "score_computation_failed"}

    try:
        career_result = derive_career_risk(user_id)
    except Exception:
        logger.warning(
            "compute_full_hprs: derive_career_risk failed for user_id=%s",
            user_id,
            exc_info=True,
        )

    try:
        vehicle_result = derive_vehicle_risk(user_id)
    except Exception:
        logger.warning(
            "compute_full_hprs: derive_vehicle_risk failed for user_id=%s",
            user_id,
            exc_info=True,
        )

    row = HprsScore.query.filter_by(user_id=user_id).first()
    if row is None:
        logger.warning(
            "compute_full_hprs: hprs_scores row missing after pipeline for user_id=%s",
            user_id,
        )
        return {"error": "score_computation_failed"}

    return _assemble_result(row, career_result, vehicle_result)


def _prompt_value(value: Any) -> str:
    if value is None:
        return "N/A"
    return str(value)


def _pillar_score(pillars: dict[str, Any], name: str) -> int:
    pillar = pillars.get(name) or {}
    return int(pillar.get("score") or 0)


def build_hprs_prompt(score_result: dict) -> list:
    """Build Anthropic /v1/messages payload from an assembled HPRS score dict."""
    pillars = score_result.get("pillars") or {}
    inputs = score_result.get("inputs_snapshot") or {}
    career = score_result.get("career_risk") or {}
    vehicle = score_result.get("vehicle_risk") or {}

    user_message = (
        "HOME PURCHASE READINESS PROFILE\n"
        "\n"
        f"Overall Score: {score_result.get('overall_score', 'N/A')}/100 "
        f"({score_result.get('readiness_tier', 'N/A')})\n"
        f"Partial Data: {score_result.get('partial_data', False)}\n"
        "\n"
        "PILLAR SCORES\n"
        f"Down Payment Readiness: {_pillar_score(pillars, 'down_payment')}/100 (weight 30%)\n"
        f"Debt-to-Income:         {_pillar_score(pillars, 'dti')}/100 (weight 25%)\n"
        f"Credit Score:           {_pillar_score(pillars, 'credit')}/100 (weight 20%)\n"
        f"Income Stability:       {_pillar_score(pillars, 'income')}/100 (weight 10%)\n"
        f"Cash Reserves:          {_pillar_score(pillars, 'reserves')}/100 (weight 10%)\n"
        "\n"
        "RAW INPUTS\n"
        f"Gross Monthly Income:   {_prompt_value(inputs.get('gross_monthly_income'))}\n"
        f"Monthly Debt:           {_prompt_value(inputs.get('total_monthly_debt'))}\n"
        f"Current DTI:            {_prompt_value(inputs.get('current_dti'))}\n"
        f"Credit Score (reported):{_prompt_value(inputs.get('credit_score'))}\n"
        f"Down Payment Saved:     {_prompt_value(score_result.get('down_payment_saved'))}\n"
        f"Down Payment Needed:    {_prompt_value(score_result.get('down_payment_needed'))}\n"
        f"Target Price:           {_prompt_value(score_result.get('target_price'))}\n"
        f"Target Timeline:        {_prompt_value(score_result.get('target_timeline_months'))} months\n"
        f"Target ZIP:             {_prompt_value(inputs.get('target_zip'))}\n"
        f"Income Percentile:      {_prompt_value(inputs.get('income_percentile'))}\n"
        "\n"
        "CAREER RISK\n"
        f"Band: {_prompt_value(career.get('band'))}  "
        f"Score: {_prompt_value(career.get('score'))}  "
        f"Modifier: {_prompt_value(career.get('modifier'))}\n"
        f"Active Layoff Event: {career.get('active_layoff', False)}\n"
        "\n"
        "VEHICLE RISK\n"
        f"Band: {_prompt_value(vehicle.get('band'))}  "
        f"Score: {_prompt_value(vehicle.get('score'))}  "
        f"Modifier: {_prompt_value(vehicle.get('modifier'))}\n"
        f"Annual Repair Exposure: {_prompt_value(vehicle.get('annual_repair_exposure'))}\n"
        f"VIN Verdict: {_prompt_value(vehicle.get('verdict'))}\n"
        "\n"
        f"Combined Risk Modifier: {_prompt_value(score_result.get('combined_modifier'))}\n"
    )

    career_band = career.get("band") or ""
    if career_band in {"HIGH", "CRITICAL"}:
        user_message += (
            "\nCAREER RISK INSTRUCTION: plan_phases MUST include a Phase 0 named "
            "'Stabilize Employment' before any housing steps. watch_flags MUST include "
            "a specific career risk entry."
        )
    elif career_band == "MODERATE":
        user_message += (
            "\nCAREER RISK INSTRUCTION: Add a career monitoring action to monthly_actions. "
            "Do not create a blocking phase."
        )

    vehicle_band = vehicle.get("band") or ""
    repair_exposure = _prompt_value(vehicle.get("annual_repair_exposure"))
    if vehicle_band in {"ELEVATED", "CRITICAL"}:
        user_message += (
            "\nVEHICLE RISK INSTRUCTION: plan_phases must include a vehicle decision action "
            "in the first active phase. Include replacement_cost_est "
            f"(${repair_exposure}) in plan language. Frame as: Resolve vehicle situation "
            "before down payment savings ramp."
        )
    elif vehicle_band == "WATCH":
        user_message += (
            "\nVEHICLE RISK INSTRUCTION: Add vehicle monitoring to watch_flags."
        )

    user_message += f"\n\n{_OUTPUT_SCHEMA}"

    return [
        {"role": "system", "content": _SYSTEM_PROMPT},
        {"role": "user", "content": user_message},
    ]


def _parse_plan_json(raw: str) -> dict:
    clean = re.sub(
        r"^```json\s*|^```\s*|```$",
        "",
        raw.strip(),
        flags=re.MULTILINE,
    ).strip()
    try:
        return json.loads(clean)
    except json.JSONDecodeError:
        raise HprsPlanParseError(f"Failed to parse plan JSON: {clean[:200]}")


def _validate_plan_json(plan_json: dict) -> None:
    missing = [field for field in _REQUIRED_PLAN_FIELDS if field not in plan_json]
    if missing:
        raise HprsPlanParseError(f"Plan missing required fields: {missing}")


def _call_anthropic(
    messages: list,
    retry_append: str | None = None,
    max_tokens: int = 2000,
) -> str:
    client = anthropic.Anthropic()
    user_content = messages[1]["content"]
    if retry_append:
        user_content += retry_append
    response = client.messages.create(
        model=_LLM_MODEL,
        max_tokens=max_tokens,
        system=messages[0]["content"],
        messages=[{"role": "user", "content": user_content}],
    )
    return response.content[0].text


def _persist_plan(user_id: int, plan_json: dict, score_id: Any) -> datetime:
    now = datetime.utcnow()
    db.session.query(HprsPlan).filter(
        HprsPlan.user_id == user_id,
        HprsPlan.is_active.is_(True),
    ).update({"is_active": False}, synchronize_session=False)

    focus_pillar = plan_json["monthly_actions"][0]["dimension"]
    db.session.add(
        HprsPlan(
            user_id=user_id,
            score_id=score_id,
            plan_summary=plan_json["summary"],
            action_steps=plan_json,
            focus_pillar=focus_pillar,
            generated_at=now,
            is_active=True,
            llm_model=_LLM_MODEL,
        )
    )
    db.session.commit()
    return now


def generate_hprs_plan(user_id: int) -> dict:
    """Compute HPRS score, call Claude for a plan, validate, persist, and return."""
    score_result = compute_full_hprs(user_id)
    if score_result.get("error"):
        raise HprsPlanParseError(
            f"Cannot generate plan: {score_result['error']} for user_id={user_id}"
        )

    messages = build_hprs_prompt(score_result)
    raw_text = _call_anthropic(messages)

    try:
        plan_json = _parse_plan_json(raw_text)
    except HprsPlanParseError:
        raw_text = _call_anthropic(
            messages,
            retry_append=_RETRY_APPEND,
        )
        try:
            plan_json = _parse_plan_json(raw_text)
        except HprsPlanParseError:
            logger.error(
                "generate_hprs_plan: failed to parse plan JSON for user_id=%s raw=%s",
                user_id,
                raw_text,
            )
            raise

    _validate_plan_json(plan_json)

    score_row = HprsScore.query.filter_by(user_id=user_id).first()
    generated_at = _persist_plan(
        user_id,
        plan_json,
        score_row.id if score_row else None,
    )

    return {
        "plan_json": plan_json,
        "projected_score": plan_json["projected_score"],
        "focus_pillar": plan_json["monthly_actions"][0]["dimension"],
        "generated_at": generated_at.isoformat(),
        "model": _LLM_MODEL,
    }
