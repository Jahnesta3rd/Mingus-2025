#!/usr/bin/env python3
"""Phased independence tiers — staged move-out planning with buying guides."""

from __future__ import annotations

import math
from typing import Any

_TIER_INCREMENTS = (3500.0, 2500.0, 2000.0, 8100.0)
_TIER_NAMES = (
    "Emergency independence",
    "Stable setup",
    "Really comfortable",
    "Fully established with car",
)
_TIER_DESCRIPTIONS = (
    "Bare essentials to leave in 2–3 months — used/IKEA basics only.",
    "Adds real couch, dining table, and better appliances for a 6-month exit.",
    "Nice furniture, entertainment, and decor for a 12-month solo move.",
    "Full setup including car purchase, insurance, registration, and maintenance fund.",
)
_TIER_FURNITURE = (
    "Used/IKEA basics: bed frame, mattress, 2 chairs, small table, used cookware.",
    "Adds real couch, dining table, microwave, and better kitchen tools.",
    "Adds quality sofa, TV stand, decor, linens, and entertainment setup.",
    "Vehicle plus remaining household upgrades for long-term independence.",
)
_TIER_TARGET_MONTHS = (3, 6, 12, 18)

_BUYING_GUIDES: dict[int, dict[str, Any]] = {
    0: {
        "tier": 0,
        "title": "Tier 0 — Emergency basics",
        "budget_target": 3500.0,
        "strategy": "Prioritize used marketplaces and IKEA essentials. Skip non-essentials.",
        "categories": [
            {
                "name": "Sleep",
                "budget": 600.0,
                "items": [
                    {"item": "Bed frame (IKEA or used)", "budget": 150.0},
                    {"item": "Mattress (budget or floor model)", "budget": 250.0},
                    {"item": "Bedding set", "budget": 80.0},
                    {"item": "Curtain panels", "budget": 40.0},
                ],
            },
            {
                "name": "Seating & table",
                "budget": 250.0,
                "items": [
                    {"item": "2 folding chairs or used dining chairs", "budget": 60.0},
                    {"item": "Small table (IKEA LACK or used)", "budget": 80.0},
                    {"item": "Floor lamp", "budget": 35.0},
                ],
            },
            {
                "name": "Kitchen",
                "budget": 200.0,
                "items": [
                    {"item": "Used cookware set", "budget": 60.0},
                    {"item": "Plates, utensils, mugs (thrift/Target)", "budget": 50.0},
                    {"item": "Basic cleaning supplies", "budget": 40.0},
                ],
            },
            {
                "name": "Move-in cash buffer",
                "budget": 2450.0,
                "items": [
                    {"item": "First month + deposit share (interim housing)", "budget": 1500.0},
                    {"item": "Utility deposits + moving", "budget": 500.0},
                    {"item": "Emergency buffer", "budget": 450.0},
                ],
            },
        ],
        "retailers": [
            {"name": "IKEA", "url": "https://www.ikea.com/us/en/", "tip": "KALLAX, LACK, FADO lamp"},
            {"name": "Target", "url": "https://www.target.com/", "tip": "Kitchen starter kits, Threshold basics"},
            {"name": "Craigslist", "url": "https://www.craigslist.org/", "tip": "Mattress + couch bundles near move-out dates"},
            {"name": "Facebook Marketplace", "url": "https://www.facebook.com/marketplace/", "tip": "Free/low-cost furniture pickups"},
        ],
    },
    1: {
        "tier": 1,
        "title": "Tier 1 — Stable setup",
        "budget_target": 2500.0,
        "strategy": "Add durable mid-range pieces you will keep after upgrading later.",
        "categories": [
            {
                "name": "Living room",
                "budget": 900.0,
                "items": [
                    {"item": "Couch (floor model or IKEA)", "budget": 450.0},
                    {"item": "Coffee table", "budget": 120.0},
                    {"item": "TV stand (optional)", "budget": 100.0},
                ],
            },
            {
                "name": "Dining",
                "budget": 500.0,
                "items": [
                    {"item": "Dining table + 4 chairs", "budget": 350.0},
                    {"item": "Tableware upgrade", "budget": 80.0},
                ],
            },
            {
                "name": "Appliances",
                "budget": 600.0,
                "items": [
                    {"item": "Microwave", "budget": 120.0},
                    {"item": "Toaster / kettle", "budget": 60.0},
                    {"item": "Vacuum", "budget": 150.0},
                    {"item": "Iron + ironing board", "budget": 70.0},
                ],
            },
            {
                "name": "Storage & misc",
                "budget": 500.0,
                "items": [
                    {"item": "Dresser or shelving unit", "budget": 200.0},
                    {"item": "Tool kit + hangers", "budget": 80.0},
                    {"item": "Bathroom upgrades", "budget": 120.0},
                ],
            },
        ],
        "retailers": [
            {"name": "IKEA", "url": "https://www.ikea.com/us/en/", "tip": "EKTORP sofa, MALM dresser"},
            {"name": "Target", "url": "https://www.target.com/", "tip": "Room Essentials bundles"},
            {"name": "Wayfair", "url": "https://www.wayfair.com/", "tip": "Open-box furniture deals"},
            {"name": "OfferUp", "url": "https://offerup.com/", "tip": "Local appliance pickups"},
        ],
    },
    2: {
        "tier": 2,
        "title": "Tier 2 — Comfortable solo",
        "budget_target": 2000.0,
        "strategy": "Invest in comfort and items that make solo living feel permanent.",
        "categories": [
            {
                "name": "Furniture upgrades",
                "budget": 900.0,
                "items": [
                    {"item": "Quality sofa upgrade or sectional", "budget": 500.0},
                    {"item": "Bookshelf / office desk", "budget": 250.0},
                    {"item": "Accent chairs or bar stools", "budget": 150.0},
                ],
            },
            {
                "name": "Entertainment",
                "budget": 500.0,
                "items": [
                    {"item": "TV (refurbished or mid-range)", "budget": 350.0},
                    {"item": "Streaming device / soundbar", "budget": 100.0},
                ],
            },
            {
                "name": "Decor & linens",
                "budget": 400.0,
                "items": [
                    {"item": "Rugs, curtains, wall art", "budget": 200.0},
                    {"item": "Premium bedding + towels", "budget": 150.0},
                ],
            },
            {
                "name": "Kitchen extras",
                "budget": 200.0,
                "items": [
                    {"item": "Coffee maker, blender, cookware upgrade", "budget": 200.0},
                ],
            },
        ],
        "retailers": [
            {"name": "IKEA", "url": "https://www.ikea.com/us/en/", "tip": "HEMNES, BILLY for storage"},
            {"name": "Target", "url": "https://www.target.com/", "tip": "Threshold decor collections"},
            {"name": "Best Buy", "url": "https://www.bestbuy.com/", "tip": "Open-box TVs"},
            {"name": "Craigslist", "url": "https://www.craigslist.org/", "tip": "Whole-apartment buyouts"},
        ],
    },
    3: {
        "tier": 3,
        "title": "Tier 3 — Car & full establishment",
        "budget_target": 8100.0,
        "strategy": "Budget car plus insurance, registration, and a maintenance reserve.",
        "categories": [
            {
                "name": "Vehicle purchase",
                "budget": 5500.0,
                "items": [
                    {"item": "Reliable used car (private party or dealer)", "budget": 5000.0},
                    {"item": "Pre-purchase inspection", "budget": 150.0},
                    {"item": "Initial repairs buffer", "budget": 350.0},
                ],
            },
            {
                "name": "Insurance & registration",
                "budget": 1100.0,
                "items": [
                    {"item": "First insurance payment + deposit", "budget": 450.0},
                    {"item": "Registration, title, taxes", "budget": 400.0},
                    {"item": "License / ID updates", "budget": 80.0},
                ],
            },
            {
                "name": "Maintenance fund",
                "budget": 1000.0,
                "items": [
                    {"item": "Oil, tires, emergency repair reserve", "budget": 1000.0},
                ],
            },
            {
                "name": "Driving essentials",
                "budget": 500.0,
                "items": [
                    {"item": "Emergency kit, jumper cables, floor mats", "budget": 150.0},
                    {"item": "Parking permit / toll transponder", "budget": 200.0},
                ],
            },
        ],
        "retailers": [
            {"name": "CarGurus", "url": "https://www.cargurus.com/", "tip": "Compare dealer vs private pricing"},
            {"name": "Kelley Blue Book", "url": "https://www.kbb.com/", "tip": "Fair purchase price checks"},
            {"name": "DMV.org", "url": "https://www.dmv.org/", "tip": "State registration fee estimates"},
            {"name": "Costco Auto", "url": "https://www.costcoauto.com/", "tip": "Member pricing on new/used"},
        ],
    },
}

_LEAVE_SCENARIOS = (
    {
        "key": "leave_3",
        "label": "Leave in 3 months",
        "target_months": 3,
        "tier_levels": [0],
        "housing": "family_or_roommate",
        "housing_label": "Family stay or roommate",
    },
    {
        "key": "leave_6",
        "label": "Leave in 6 months",
        "target_months": 6,
        "tier_levels": [0, 1],
        "housing": "roommate",
        "housing_label": "Shared 2BR with roommate",
    },
    {
        "key": "leave_12",
        "label": "Leave in 12 months",
        "target_months": 12,
        "tier_levels": [0, 1, 2],
        "housing": "solo_apartment",
        "housing_label": "Solo apartment",
    },
    {
        "key": "full_setup",
        "label": "Full setup (18+ months)",
        "target_months": 18,
        "tier_levels": [0, 1, 2, 3],
        "housing": "solo_with_car",
        "housing_label": "Solo apartment with car",
    },
)


def _round2(value: float) -> float:
    return round(float(value), 2)


def _months_to_fund(startup: float, monthly_savings: float) -> int | None:
    if monthly_savings <= 0 or startup <= 0:
        return None
    return int(math.ceil(startup / monthly_savings))


class PhasedIndependencePlanner:
    """Generate tiered independence plans, timelines, and buying guides."""

    def generate_tiers(self, startup_cost_full: float) -> dict[str, Any]:
        """Return four cumulative independence tiers with static cost structure."""
        cumulative = 0.0
        tiers: dict[str, Any] = {}

        for level, increment in enumerate(_TIER_INCREMENTS):
            cumulative += increment
            key = f"tier_{level}"
            tiers[key] = {
                "tier": level,
                "name": _TIER_NAMES[level],
                "incremental_cost": _round2(increment),
                "cumulative_cost": _round2(cumulative),
                "target_leave_months": _TIER_TARGET_MONTHS[level],
                "description": _TIER_DESCRIPTIONS[level],
                "furniture_summary": _TIER_FURNITURE[level],
                "includes_car": level == 3,
                "gap_to_full_icc_startup": _round2(max(0.0, float(startup_cost_full) - cumulative)),
            }

        tiers["summary"] = {
            "tier_0_cost": _round2(_TIER_INCREMENTS[0]),
            "tier_1_total": _round2(sum(_TIER_INCREMENTS[:2])),
            "tier_2_total": _round2(sum(_TIER_INCREMENTS[:3])),
            "tier_3_total": _round2(sum(_TIER_INCREMENTS)),
            "icc_full_startup_reference": _round2(float(startup_cost_full)),
        }
        return tiers

    def buying_guide_for_tier(self, tier: int) -> dict[str, Any]:
        if tier not in _BUYING_GUIDES:
            raise ValueError(f"tier must be between 0 and 3, got {tier}")
        guide = dict(_BUYING_GUIDES[tier])
        guide["printable_title"] = f"Independence Tier {tier} Shopping List"
        return guide

    def leave_by_month_scenarios(
        self,
        total_monthly_gap: float,
        monthly_savings: float,
    ) -> list[dict[str, Any]]:
        """Build leave-by-month scenarios with funding feasibility."""
        tier_defs = self.generate_tiers(startup_cost_full=sum(_TIER_INCREMENTS))
        scenarios: list[dict[str, Any]] = []

        for template in _LEAVE_SCENARIOS:
            tier_levels: list[int] = template["tier_levels"]
            cumulative_startup = sum(_TIER_INCREMENTS[level] for level in tier_levels)
            months_needed = _months_to_fund(cumulative_startup, monthly_savings)
            target = template["target_months"]
            on_track = months_needed is not None and months_needed <= target
            shortfall = (
                _round2(cumulative_startup - monthly_savings * target)
                if monthly_savings > 0
                else cumulative_startup
            )

            tier_breakdown = [
                {
                    "tier": level,
                    "name": tier_defs[f"tier_{level}"]["name"],
                    "cost": _round2(_TIER_INCREMENTS[level]),
                }
                for level in tier_levels
            ]

            scenarios.append(
                {
                    "key": template["key"],
                    "label": template["label"],
                    "target_months": target,
                    "tier_levels": tier_levels,
                    "tier_breakdown": tier_breakdown,
                    "cumulative_startup": _round2(cumulative_startup),
                    "housing": template["housing"],
                    "housing_label": template["housing_label"],
                    "months_to_fund": months_needed,
                    "on_track": on_track,
                    "shortfall_at_target": _round2(max(0.0, shortfall)),
                    "monthly_savings_assumed": _round2(monthly_savings),
                    "monthly_gap_reference": _round2(total_monthly_gap),
                }
            )

        return scenarios

    def contingency_scenarios(
        self,
        selected_key: str,
        total_monthly_gap: float,
        monthly_savings: float,
    ) -> list[dict[str, Any]]:
        """What-if adjustments for the selected leave-by-month scenario."""
        scenarios = self.leave_by_month_scenarios(total_monthly_gap, monthly_savings)
        selected = next((row for row in scenarios if row["key"] == selected_key), scenarios[0])
        base_startup = float(selected["cumulative_startup"])
        base_months = selected["months_to_fund"]
        target = selected["target_months"]

        what_ifs = [
            {
                "key": "savings_drop_20",
                "label": "What if savings drop 20%?",
                "adjusted_monthly_savings": _round2(monthly_savings * 0.8),
                "months_to_fund": _months_to_fund(base_startup, monthly_savings * 0.8),
            },
            {
                "key": "unexpected_500",
                "label": "What if a $500 emergency hits?",
                "adjusted_startup": _round2(base_startup + 500),
                "months_to_fund": _months_to_fund(base_startup + 500, monthly_savings),
            },
            {
                "key": "side_income_plus_200",
                "label": "What if side income adds $200/mo?",
                "adjusted_monthly_savings": _round2(monthly_savings + 200),
                "months_to_fund": _months_to_fund(base_startup, monthly_savings + 200),
            },
            {
                "key": "delay_one_month",
                "label": "What if you delay one month?",
                "extra_saved": _round2(monthly_savings),
                "new_shortfall": _round2(
                    max(0.0, base_startup - monthly_savings * (target + 1))
                ),
            },
        ]

        for row in what_ifs:
            months = row.get("months_to_fund")
            row["still_on_track"] = months is not None and months <= target
            row["delta_months"] = (
                months - base_months if months is not None and base_months is not None else None
            )

        return what_ifs

    def build_timeline_payload(
        self,
        total_monthly_gap: float,
        monthly_savings: float,
        startup_cost_full: float | None = None,
    ) -> dict[str, Any]:
        full_startup = float(startup_cost_full or sum(_TIER_INCREMENTS))
        tier_definitions = self.generate_tiers(full_startup)
        scenarios = self.leave_by_month_scenarios(total_monthly_gap, monthly_savings)
        buying_guides = {str(level): self.buying_guide_for_tier(level) for level in range(4)}

        return {
            "total_monthly_gap": _round2(total_monthly_gap),
            "monthly_savings": _round2(monthly_savings),
            "startup_cost_full": _round2(full_startup),
            "tier_definitions": tier_definitions,
            "scenarios": scenarios,
            "buying_guides": buying_guides,
            "default_scenario_key": "leave_6",
        }
