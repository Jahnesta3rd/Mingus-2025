#!/usr/bin/env python3
"""Rule-based Health Insurance Advisor plan scoring."""

from __future__ import annotations

import json
import logging
from decimal import Decimal
from typing import Any

from backend.api.profile_endpoints import get_db_connection
from backend.models.health_insurance_plan import HealthInsurancePlan
from backend.models.housing_profile import HousingProfile
from backend.models.transaction_schedule import IncomeStream
from backend.models.user_models import User
from backend.services.cms_benchmark_service import get_benchmark_context
from backend.utils.user_profile_context import extract_zip_from_text

logger = logging.getLogger(__name__)

_MONTHLY_INCOME_MULTIPLIERS: dict[str, float] = {
    "weekly": 52 / 12,
    "biweekly": 26 / 12,
    "semimonthly": 2.0,
    "monthly": 1.0,
    "quarterly": 1 / 3,
    "annual": 1 / 12,
}

# 50+ common US ZIP codes → state abbreviations
ZIP_TO_STATE: dict[str, str] = {
    "10001": "NY",
    "10019": "NY",
    "10036": "NY",
    "11201": "NY",
    "90210": "CA",
    "90001": "CA",
    "90012": "CA",
    "94102": "CA",
    "92101": "CA",
    "95110": "CA",
    "60601": "IL",
    "60614": "IL",
    "77001": "TX",
    "77002": "TX",
    "75201": "TX",
    "78701": "TX",
    "79901": "TX",
    "33101": "FL",
    "32801": "FL",
    "33602": "FL",
    "19103": "PA",
    "19104": "PA",
    "30301": "GA",
    "30303": "GA",
    "98101": "WA",
    "98104": "WA",
    "80202": "CO",
    "80203": "CO",
    "02108": "MA",
    "02116": "MA",
    "43215": "OH",
    "44114": "OH",
    "28202": "NC",
    "27601": "NC",
    "37201": "TN",
    "37203": "TN",
    "85001": "AZ",
    "85281": "AZ",
    "97201": "OR",
    "97205": "OR",
    "84101": "UT",
    "84111": "UT",
    "64108": "MO",
    "63101": "MO",
    "53202": "WI",
    "53703": "WI",
    "55401": "MN",
    "55101": "MN",
    "70112": "LA",
    "70801": "LA",
    "21201": "MD",
    "21401": "MD",
    "23219": "VA",
    "23220": "VA",
    "46204": "IN",
    "46202": "IN",
    "40202": "KY",
    "40507": "KY",
    "73102": "OK",
    "74103": "OK",
    "87101": "NM",
    "87501": "NM",
    "50309": "IA",
    "68102": "NE",
    "57104": "SD",
    "59718": "MT",
    "82001": "WY",
    "83702": "ID",
    "96813": "HI",
    "99501": "AK",
    "35203": "AL",
    "72201": "AR",
    "19801": "DE",
    "04101": "ME",
    "48933": "MI",
    "48226": "MI",
    "39201": "MS",
    "65101": "MO",
    "89101": "NV",
    "03301": "NH",
    "07030": "NJ",
    "07302": "NJ",
    "02903": "RI",
    "29201": "SC",
    "25301": "WV",
    "05401": "VT",
    "36104": "AL",
    "96815": "HI",
    "99508": "AK",
}


def _num(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, Decimal):
        return float(value)
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _parse_json_object(raw: Any) -> dict:
    if raw is None or raw == "":
        return {}
    if isinstance(raw, dict):
        return dict(raw)
    if isinstance(raw, str):
        try:
            parsed = json.loads(raw)
            return dict(parsed) if isinstance(parsed, dict) else {}
        except (TypeError, ValueError, json.JSONDecodeError):
            return {}
    return {}


def _stream_to_monthly(amount: Decimal | float, frequency: str) -> float:
    freq = (frequency or "monthly").strip().lower()
    multiplier = _MONTHLY_INCOME_MULTIPLIERS.get(freq, 1.0)
    return float(amount) * multiplier


def _compute_gross_monthly_income(user_id: int) -> float | None:
    streams = IncomeStream.query.filter_by(user_id=user_id, is_active=True).all()
    if not streams:
        return None
    return round(sum(_stream_to_monthly(s.amount, s.frequency) for s in streams), 2)


def _load_usage_context(user_id: int) -> dict[str, Any]:
    user = User.query.get(user_id)
    if user is None:
        raise ValueError(f"user_id={user_id} not found")

    usage_row = None
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                  up.hia_coverage_type,
                  up.hia_primary_care_visits,
                  up.hia_specialist_visits,
                  up.hia_er_visits,
                  up.hia_planned_procedure,
                  up.hia_takes_rx,
                  up.hia_rx_type,
                  up.financial_info
                FROM user_profiles up
                JOIN users u ON u.email = up.email
                WHERE u.id = %s
                LIMIT 1
                """,
                (user_id,),
            )
            usage_row = cur.fetchone()
    finally:
        conn.close()

    financial_info = _parse_json_object(
        usage_row.get("financial_info") if usage_row else None
    )
    emergency_fund = _num(financial_info.get("emergency_fund")) or 0.0

    housing = HousingProfile.query.filter_by(user_id=user_id).first()
    state_code = "TX"
    if housing and housing.zip_or_city:
        zip_code = extract_zip_from_text(housing.zip_or_city)
        if zip_code and zip_code in ZIP_TO_STATE:
            state_code = ZIP_TO_STATE[zip_code]

    return {
        "coverage_type": usage_row.get("hia_coverage_type") if usage_row else None,
        "primary_care_visits": (
            usage_row.get("hia_primary_care_visits") if usage_row else None
        )
        or 3,
        "specialist_visits": (
            usage_row.get("hia_specialist_visits") if usage_row else None
        )
        or 1,
        "er_visits": (usage_row.get("hia_er_visits") if usage_row else None) or 0,
        "planned_procedure": bool(
            usage_row.get("hia_planned_procedure") if usage_row else False
        ),
        "takes_rx": bool(usage_row.get("hia_takes_rx") if usage_row else False),
        "rx_type": (usage_row.get("hia_rx_type") if usage_row else None) or "generic",
        "emergency_fund": emergency_fund,
        "gross_monthly_income": _compute_gross_monthly_income(user_id),
        "state_code": state_code,
    }


def _estimate_rx_cost(takes_rx: bool, rx_type: str | None, plan: HealthInsurancePlan) -> float:
    if not takes_rx:
        return 0.0
    tiers = {
        "generic": _num(plan.rx_tier1) or 15,
        "brand": _num(plan.rx_tier2) or 50,
        "specialty": _num(plan.rx_tier3) or 150,
    }
    monthly_rx = tiers.get((rx_type or "generic").lower(), 15)
    return monthly_rx * 12


def _resolve_metal_level(plan: HealthInsurancePlan) -> str:
    plan_type = (plan.plan_type or "").upper()
    deductible = _num(plan.annual_deductible_individual) or 0
    if plan_type == "HDHP":
        return "Bronze"
    if not plan_type:
        return "Silver"
    if plan_type in {"PPO", "HMO", "EPO", "POS"}:
        if deductible >= 3000:
            return "Silver"
        return "Gold"
    return "Silver"


def _compute_utilization(
    plan: HealthInsurancePlan,
    usage: dict[str, Any],
) -> tuple[float, float]:
    annual_premium = (_num(plan.monthly_premium_employee) or 0) * 12
    deductible = _num(plan.annual_deductible_individual) or 1500
    oop_max = _num(plan.out_of_pocket_max_individual) or 5000

    pcp_cost = min(
        usage["primary_care_visits"] * (_num(plan.copay_primary_care) or 30),
        deductible,
    )
    specialist_cost = min(
        usage["specialist_visits"] * (_num(plan.copay_specialist) or 60),
        deductible,
    )
    er_cost = min(
        usage["er_visits"] * (_num(plan.copay_er) or 350),
        oop_max,
    )
    rx_cost = _estimate_rx_cost(usage["takes_rx"], usage["rx_type"], plan)
    procedure_cost = deductible * 0.5 if usage["planned_procedure"] else 0.0

    utilization_total = pcp_cost + specialist_cost + er_cost + rx_cost + procedure_cost
    expected_annual_cost = annual_premium + utilization_total
    return annual_premium, utilization_total, expected_annual_cost


def _build_risk_flags(
    plan: HealthInsurancePlan,
    usage: dict[str, Any],
    emergency_fund: float,
) -> list[str]:
    flags: list[str] = []
    oop_max = _num(plan.out_of_pocket_max_individual) or 0
    plan_type = (plan.plan_type or "").upper()

    if oop_max > emergency_fund:
        flags.append(
            f"Your emergency fund (${emergency_fund:,.0f}) is less than "
            f"this plan's OOP max (${oop_max:,.0f}). "
            f"A major health event could strain your finances."
        )
    if plan_type == "HDHP" and emergency_fund < 2000:
        flags.append(
            "HDHPs work best with a funded emergency reserve. "
            "Consider building savings before choosing this plan."
        )
    if usage["er_visits"] > 0 and plan.in_network_only:
        flags.append(
            "This plan has limited out-of-network coverage. "
            "ER visits may cost significantly more if out of network."
        )
    return flags


def _build_hsa_opportunity(
    plan: HealthInsurancePlan,
    coverage_type: str | None,
    gross_monthly_income: float | None,
) -> dict[str, Any]:
    if not plan.has_hsa_eligible:
        return {"eligible": False}

    if not gross_monthly_income:
        return {"eligible": True}

    hsa_limit = 8550 if coverage_type == "family" else 4300
    hsa_annual_benefit = round(hsa_limit * 0.22)
    return {
        "eligible": True,
        "annual_limit": hsa_limit,
        "estimated_tax_savings": hsa_annual_benefit,
        "message": (
            f"HSA-eligible. Contributing the max could save "
            f"~${hsa_annual_benefit:,}/year in taxes."
        ),
    }


def _compute_score(
    plan: HealthInsurancePlan,
    expected_annual_cost: float,
    gross_monthly_income: float | None,
    emergency_fund: float,
    flags: list[str],
) -> int:
    score = 100
    if gross_monthly_income:
        cost_pct = expected_annual_cost / (gross_monthly_income * 12)
        if cost_pct > 0.15:
            score -= 20
        elif cost_pct > 0.10:
            score -= 10

    oop_max = _num(plan.out_of_pocket_max_individual) or 0
    if oop_max > emergency_fund * 2:
        score -= 15

    score -= len(flags) * 10
    if plan.has_hsa_eligible:
        score += 10
    return max(0, min(100, score))


def _score_plan(plan: HealthInsurancePlan, usage: dict[str, Any]) -> dict[str, Any]:
    annual_premium, utilization_total, expected_annual_cost = _compute_utilization(
        plan, usage
    )
    emergency_fund = usage["emergency_fund"]
    flags = _build_risk_flags(plan, usage, emergency_fund)
    hsa_opportunity = _build_hsa_opportunity(
        plan,
        usage.get("coverage_type"),
        usage.get("gross_monthly_income"),
    )
    metal_level = _resolve_metal_level(plan)
    benchmark_context = get_benchmark_context(
        usage["state_code"],
        _num(plan.out_of_pocket_max_individual),
        _num(plan.annual_deductible_individual),
        metal_level,
    )
    score = _compute_score(
        plan,
        expected_annual_cost,
        usage.get("gross_monthly_income"),
        emergency_fund,
        flags,
    )

    return {
        "plan_id": plan.id,
        "plan_name": plan.plan_name,
        "plan_type": plan.plan_type,
        "insurer_name": plan.insurer_name,
        "score": score,
        "expected_annual_cost": round(expected_annual_cost, 2),
        "annual_premium": round(annual_premium, 2),
        "utilization_estimate": round(utilization_total, 2),
        "risk_flags": flags,
        "hsa_opportunity": hsa_opportunity,
        "benchmark_context": benchmark_context,
        "monthly_premium_employee": _num(plan.monthly_premium_employee),
        "annual_deductible_individual": _num(plan.annual_deductible_individual),
        "out_of_pocket_max_individual": _num(plan.out_of_pocket_max_individual),
        "has_hsa_eligible": bool(plan.has_hsa_eligible),
    }


def score_plans(user_id: int, plan_ids: list[int]) -> list[dict]:
    """Score insurance plans for a user; returns ranked results best-first."""
    try:
        if not plan_ids:
            return []

        usage = _load_usage_context(user_id)
        plans = HealthInsurancePlan.query.filter(
            HealthInsurancePlan.id.in_(plan_ids)
        ).all()
        plan_by_id = {plan.id: plan for plan in plans if plan.user_id == user_id}

        results: list[dict[str, Any]] = []
        for plan_id in plan_ids:
            plan = plan_by_id.get(plan_id)
            if plan is None:
                continue
            results.append(_score_plan(plan, usage))

        results.sort(key=lambda item: item["score"], reverse=True)
        return results
    except Exception:
        logger.exception("score_plans failed for user_id=%s plan_ids=%s", user_id, plan_ids)
        return []
