#!/usr/bin/env python3
"""Interim housing scenarios — roommate, family, and sublet alternatives to solo rent."""

from __future__ import annotations

import math
import statistics
from typing import Any

from backend.models.independence_cost_assessment import IndependenceCostAssessment
from backend.services.external_api_service import ExternalAPIService
from backend.services.independence_cost_service import IndependenceCostCalculator
from backend.utils.user_profile_context import extract_zip_from_text

_MOCK_MARKET_2BR = 1800.0
_FAMILY_MONTHLY_RANGE = (400.0, 600.0)
_SUBLET_MONTHLY_RANGE = (900.0, 1000.0)

_CONVERSATION_TEMPLATES: dict[str, dict[str, Any]] = {
    "how_to_ask_family": {
        "title": "How to ask family or friends",
        "summary": "Frame the stay as a short bridge with clear boundaries and gratitude.",
        "talking_points": [
            "Share your timeline (e.g., 3–6 months) and what independence looks like after.",
            "Offer concrete help: groceries, chores, childcare, or a modest contribution.",
            "Agree on rent/contribution, house rules, and a monthly check-in date.",
            "Put key terms in writing — even a simple text thread — to avoid misunderstandings.",
        ],
        "sample_opener": (
            "I'm working on a plan to move out on my own and wanted to ask if a short stay "
            "might work while I save for deposits. Could we talk about 3–6 months and what "
            "would feel fair for both of us?"
        ),
    },
    "how_to_vet_roommate": {
        "title": "How to vet a roommate",
        "summary": "Prioritize financial reliability and lifestyle fit before signing a lease.",
        "checklist": [
            "Run a casual interview: work schedule, cleanliness, guests, pets, and noise.",
            "Ask for references from a prior landlord or roommate.",
            "Split utilities and lease obligations in writing before move-in.",
            "Confirm income or savings — can they cover their half if you're on the same lease?",
            "Meet in person or video chat; avoid rushing with strangers from anonymous posts.",
        ],
        "red_flags": [
            "Won't discuss income or past evictions",
            "Pushes to skip the lease or put everything in your name only",
            "Inconsistent story about employment or prior living situations",
        ],
    },
    "sublet_red_flags": {
        "title": "Sublet red flags",
        "summary": "Furnished month-to-month can be flexible — but verify legitimacy first.",
        "red_flags": [
            "Landlord won't confirm the sublet in writing",
            "Wire-only deposits with no signed agreement",
            "Price far below market with pressure to decide immediately",
            "Refusal to show the unit or provide a lease addendum",
            "Listing photos that don't match the actual space",
        ],
        "must_haves": [
            "Written sublet permission from the primary tenant or landlord",
            "Clear move-in/move-out dates and deposit return terms",
            "Receipt for any deposit or first month's rent",
        ],
    },
}


def _round2(value: float) -> float:
    return round(float(value), 2)


def _timeline_months(startup: float, monthly_gap: float) -> int | None:
    if monthly_gap <= 0 or startup <= 0:
        return None
    return int(math.ceil(startup / monthly_gap))


def _median_2br_from_listings(listings: list[dict[str, Any]]) -> float | None:
    prices: list[float] = []
    for listing in listings:
        bedrooms = listing.get("bedrooms")
        if bedrooms is not None and int(bedrooms) != 2:
            continue
        price = listing.get("price") or listing.get("rent") or listing.get("monthlyRent")
        if price is None:
            continue
        try:
            prices.append(float(price))
        except (TypeError, ValueError):
            continue
    if not prices:
        for listing in listings:
            bedrooms = listing.get("bedrooms")
            if bedrooms is not None and int(bedrooms) < 2:
                continue
            price = listing.get("price") or listing.get("rent") or listing.get("monthlyRent")
            if price is None:
                continue
            try:
                prices.append(float(price))
            except (TypeError, ValueError):
                continue
    if not prices:
        return None
    return statistics.median(prices)


class InterimHousingAnalyzer:
    """Compare interim housing paths against a solo-apartment ICC baseline."""

    def __init__(
        self,
        external_api_service: ExternalAPIService | None = None,
        icc_calculator: IndependenceCostCalculator | None = None,
    ) -> None:
        self.external_api_service = external_api_service or ExternalAPIService()
        self.icc_calculator = icc_calculator or IndependenceCostCalculator()

    def get_market_rent_2br(self, zip_code: str) -> dict[str, Any]:
        clean_zip = extract_zip_from_text(zip_code) or (zip_code or "").strip()[:5]
        if not clean_zip:
            return {"median_2br_rent": _MOCK_MARKET_2BR, "source": "default"}

        try:
            response = self.external_api_service.get_rental_listings(
                clean_zip,
                {"bedrooms": 2, "limit": 25},
            )
            if response.get("success"):
                listings = response.get("data") or []
                median_rent = _median_2br_from_listings(listings)
                if median_rent is not None:
                    return {
                        "median_2br_rent": _round2(median_rent),
                        "source": "rentcast",
                    }
        except Exception:
            pass

        market_1br = self.icc_calculator.get_market_rent(clean_zip)
        estimated_2br = float(market_1br.get("median_1br_rent") or _MOCK_MARKET_2BR) * 1.35
        return {"median_2br_rent": _round2(estimated_2br), "source": "estimated_from_1br"}

    def _resolve_icc_inputs(
        self,
        user_id: int,
        zip_code: str | None,
        startup_cost_needed: float | None,
        monthly_gap: float | None,
    ) -> tuple[str, float, float, float]:
        clean_zip = extract_zip_from_text(zip_code or "") if zip_code else None
        gap = float(monthly_gap) if monthly_gap is not None else None
        startup = float(startup_cost_needed) if startup_cost_needed is not None else None
        solo_1br = None

        if gap is None or startup is None or not clean_zip:
            latest = (
                IndependenceCostAssessment.query.filter_by(user_id=user_id)
                .order_by(IndependenceCostAssessment.created_at.desc())
                .first()
            )
            if latest:
                if gap is None and latest.monthly_independence_gap is not None:
                    gap = float(latest.monthly_independence_gap)
                if startup is None and latest.total_startup_cost is not None:
                    startup = float(latest.total_startup_cost)
                if not clean_zip and latest.zip_code:
                    clean_zip = latest.zip_code
                if latest.market_rent_1br is not None:
                    solo_1br = float(latest.market_rent_1br)

        if not clean_zip:
            resolved_zip, _city = self.icc_calculator.get_user_location(user_id)
            clean_zip = resolved_zip or "10001"

        if gap is None or startup is None:
            raise ValueError(
                "monthly_gap and startup_cost_needed are required when no ICC assessment exists"
            )

        if solo_1br is None:
            solo_1br = float(
                self.icc_calculator.get_market_rent(clean_zip).get("median_1br_rent") or 1850.0
            )

        return clean_zip, _round2(startup), _round2(gap), _round2(solo_1br)

    def _roommate_startup(self, market_2br: float, solo_startup: float) -> float:
        deposit_share = market_2br
        moving = 500.0
        furniture = 400.0
        utilities_deposit = 300.0
        calculated = deposit_share + moving + furniture + utilities_deposit
        return _round2(min(calculated, max(4000.0, solo_startup * 0.25)))

    def _family_startup(self) -> float:
        return 1000.0

    def _sublet_startup(self, sublet_monthly: float) -> float:
        return _round2(max(2000.0, sublet_monthly * 2.0 + 500.0))

    def _build_scenario(
        self,
        *,
        key: str,
        name: str,
        monthly_cost: float,
        monthly_cost_range: tuple[float, float] | None,
        startup_cost: float,
        solo_startup: float,
        solo_gap: float,
        monthly_savings_vs_solo: float,
        difficulty: str,
        pros: list[str],
        cons: list[str],
        features: dict[str, str | bool],
    ) -> dict[str, Any]:
        reduced_gap = _round2(max(0.0, solo_gap - monthly_savings_vs_solo))
        timeline = _timeline_months(startup_cost, reduced_gap)
        startup_savings = _round2(max(0.0, solo_startup - startup_cost))
        return {
            "key": key,
            "name": name,
            "monthly_rent": _round2(monthly_cost),
            "monthly_rent_range": (
                {"min": _round2(monthly_cost_range[0]), "max": _round2(monthly_cost_range[1])}
                if monthly_cost_range
                else None
            ),
            "startup_cost": _round2(startup_cost),
            "monthly_savings_vs_solo": _round2(monthly_savings_vs_solo),
            "startup_savings_vs_solo": startup_savings,
            "reduced_monthly_gap": reduced_gap,
            "timeline_months": timeline,
            "difficulty": difficulty,
            "pros": pros,
            "cons": cons,
            "features": features,
        }

    def _build_phased_exit_plan(
        self,
        scenarios: list[dict[str, Any]],
        solo_startup: float,
        solo_gap: float,
    ) -> dict[str, Any]:
        by_key = {row["key"]: row for row in scenarios}
        family = by_key["family"]
        sublet = by_key["sublet"]
        roommate = by_key["roommate"]

        phase1_months = 6
        phase2_months = 5
        family_savings = float(family["monthly_savings_vs_solo"])
        sublet_savings = float(sublet["monthly_savings_vs_solo"])

        phase1_cash = phase1_months * family_savings
        phase2_cash = phase2_months * sublet_savings
        remaining_startup = max(0.0, solo_startup - phase1_cash - phase2_cash)

        roommate_gap = float(roommate["reduced_monthly_gap"])
        phase3_months = (
            int(math.ceil(remaining_startup / roommate_gap))
            if roommate_gap > 0 and remaining_startup > 0
            else 0
        )

        total_months = phase1_months + phase2_months + phase3_months
        solo_timeline = _timeline_months(solo_startup, solo_gap)

        phases = [
            {
                "phase": 1,
                "label": "Stabilize with family or friends",
                "scenario_key": "family",
                "duration_months": phase1_months,
                "monthly_savings": family_savings,
                "cumulative_savings": _round2(phase1_cash),
                "goal": "Lowest burn rate while rebuilding cash reserves",
            },
            {
                "phase": 2,
                "label": "Flexible sublet bridge",
                "scenario_key": "sublet",
                "duration_months": phase2_months,
                "monthly_savings": sublet_savings,
                "cumulative_savings": _round2(phase1_cash + phase2_cash),
                "goal": "Furnished month-to-month while income and paperwork stabilize",
            },
            {
                "phase": 3,
                "label": "Roommate savings sprint",
                "scenario_key": "roommate",
                "duration_months": phase3_months,
                "monthly_savings": float(roommate["monthly_savings_vs_solo"]),
                "remaining_startup_target": _round2(remaining_startup),
                "goal": "Split a 2BR and finish funding solo move-in costs",
            },
        ]

        return {
            "phases": phases,
            "total_months_to_solo_readiness": total_months,
            "solo_baseline_months": solo_timeline,
            "months_saved_vs_solo": (
                max(0, solo_timeline - total_months) if solo_timeline is not None else None
            ),
            "summary": (
                f"Family ({phase1_months} mo) → sublet ({phase2_months} mo) → "
                f"roommate ({phase3_months} mo) before solo move-in"
            ),
        }

    def analyze_interim_options(
        self,
        user_id: int,
        zip_code: str,
        startup_cost_needed: float | None,
        monthly_gap: float | None,
    ) -> dict[str, Any]:
        clean_zip, solo_startup, solo_gap, solo_1br = self._resolve_icc_inputs(
            user_id,
            zip_code,
            startup_cost_needed,
            monthly_gap,
        )
        market = self.get_market_rent_2br(clean_zip)
        market_2br = float(market["median_2br_rent"])
        rent_per_person = _round2(market_2br / 2.0)

        roommate_savings = _round2(max(0.0, solo_1br - rent_per_person))
        family_mid = _round2(sum(_FAMILY_MONTHLY_RANGE) / 2.0)
        family_savings = _round2(max(0.0, solo_1br - family_mid))
        sublet_mid = _round2(sum(_SUBLET_MONTHLY_RANGE) / 2.0)
        sublet_savings = _round2(max(0.0, solo_1br - sublet_mid))

        roommate_startup = self._roommate_startup(market_2br, solo_startup)
        family_startup = self._family_startup()
        sublet_startup = self._sublet_startup(sublet_mid)

        scenarios = [
            self._build_scenario(
                key="roommate",
                name="Roommate — shared 2BR",
                monthly_cost=rent_per_person,
                monthly_cost_range=None,
                startup_cost=roommate_startup,
                solo_startup=solo_startup,
                solo_gap=solo_gap,
                monthly_savings_vs_solo=roommate_savings,
                difficulty="medium",
                pros=[
                    "Lower rent than solo without giving up independence",
                    "Shared utilities and household costs",
                    "Build savings while keeping a fixed address",
                ],
                cons=[
                    "Roommate compatibility risk",
                    "Less privacy than living alone",
                    "Joint lease exposure if names are on the same contract",
                ],
                features={
                    "privacy": "medium",
                    "lease_flexibility": "low",
                    "furniture_included": False,
                    "furnished": False,
                    "month_to_month": False,
                    "social_support": "medium",
                    "burnout_risk": "low",
                },
            ),
            self._build_scenario(
                key="family",
                name="Family or friend stay",
                monthly_cost=family_mid,
                monthly_cost_range=_FAMILY_MONTHLY_RANGE,
                startup_cost=family_startup,
                solo_startup=solo_startup,
                solo_gap=solo_gap,
                monthly_savings_vs_solo=family_savings,
                difficulty="easy",
                pros=[
                    "Lowest monthly burn and startup cash needed",
                    "Built-in emotional support during transition",
                    "Time to rebuild credit and savings",
                ],
                cons=[
                    "Boundaries and timeline must be explicit",
                    "Less autonomy over daily routines",
                    "Relationship strain if expectations are unclear",
                ],
                features={
                    "privacy": "low",
                    "lease_flexibility": "high",
                    "furniture_included": True,
                    "furnished": True,
                    "month_to_month": True,
                    "social_support": "high",
                    "burnout_risk": "medium",
                },
            ),
            self._build_scenario(
                key="sublet",
                name="Furnished sublet",
                monthly_cost=sublet_mid,
                monthly_cost_range=_SUBLET_MONTHLY_RANGE,
                startup_cost=sublet_startup,
                solo_startup=solo_startup,
                solo_gap=solo_gap,
                monthly_savings_vs_solo=sublet_savings,
                difficulty="medium",
                pros=[
                    "Furnished and month-to-month flexibility",
                    "Faster move-in than a standard lease",
                    "Good bridge while paperwork or job changes settle",
                ],
                cons=[
                    "Sublet legitimacy must be verified",
                    "Less control over lease terms and renewals",
                    "May still cost more than family stay",
                ],
                features={
                    "privacy": "high",
                    "lease_flexibility": "high",
                    "furniture_included": True,
                    "furnished": True,
                    "month_to_month": True,
                    "social_support": "low",
                    "burnout_risk": "low",
                },
            ),
        ]

        phased_exit_plan = self._build_phased_exit_plan(scenarios, solo_startup, solo_gap)
        solo_timeline = _timeline_months(solo_startup, solo_gap)

        return {
            "zip_code": clean_zip,
            "market_rent_2br": market_2br,
            "market_rent_source": market.get("source"),
            "solo_comparison": {
                "label": "Solo 1BR apartment",
                "monthly_rent": solo_1br,
                "monthly_gap": solo_gap,
                "startup_cost_needed": solo_startup,
                "timeline_months": solo_timeline,
            },
            "scenarios": scenarios,
            "phased_exit_plan": phased_exit_plan,
            "conversation_templates": _CONVERSATION_TEMPLATES,
            "feature_matrix_keys": [
                "privacy",
                "lease_flexibility",
                "furniture_included",
                "furnished",
                "month_to_month",
                "social_support",
                "burnout_risk",
            ],
        }
