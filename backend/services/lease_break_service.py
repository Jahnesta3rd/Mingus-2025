#!/usr/bin/env python3
"""Lease break cost analysis — stay vs. break early."""

from __future__ import annotations

from typing import Any

from backend.models.database import db
from backend.models.lease_break_analysis import LeaseBreakAnalysis

_DEFAULT_MOVE_OUT_COST = 650.0
_DEFAULT_INTERIM_MONTHLY = 500.0
_INTERIM_ROOMMATE_FACTOR = 0.55


def _round2(value: float) -> float:
    return round(float(value), 2)


def _break_fee_amount(monthly_rent: float, break_fee_percent: float) -> float:
    """Convert break fee setting to dollars.

    Values <= 12 are treated as months of rent (e.g. 1.5 = one-and-a-half months).
    Larger values are treated as a percentage of monthly rent.
    """
    fee = float(break_fee_percent)
    rent = float(monthly_rent)
    if fee <= 12:
        return _round2(fee * rent)
    return _round2((fee / 100.0) * rent)


class LeaseBreakAnalyzer:
    """Compare staying through lease end vs. breaking early."""

    def generate_negotiation_script(
        self,
        *,
        months_remaining: int,
        monthly_rent: float,
        break_fee_percent: float,
        savings_if_negotiated: float | None = None,
    ) -> dict[str, Any]:
        fee_months = float(break_fee_percent)
        savings_line = (
            f"I've estimated that a reduced fee could save about ${_round2(savings_if_negotiated):,.0f} "
            "compared with staying through the lease."
            if savings_if_negotiated and savings_if_negotiated > 0
            else "I'm hoping we can find a fair middle ground on the termination fee."
        )
        talking_points = [
            "Ask whether a lease assignment or sublet is allowed before paying a break fee.",
            "Offer to help find a qualified replacement tenant to reduce landlord vacancy risk.",
            "Request a fee based on actual damages and marketing costs, not a punitive flat rate.",
            "Propose a phased move-out with proper notice and professional cleaning.",
            "Get any agreement in writing before paying or vacating.",
        ]
        email_template = (
            f"Subject: Early lease termination request — unit ending in {months_remaining} months\n\n"
            f"Hello,\n\n"
            f"I am writing to discuss ending my lease early. I have {months_remaining} months remaining "
            f"at ${monthly_rent:,.0f}/month and want to leave on good terms.\n\n"
            f"Would you consider any of the following?\n"
            f"- Lease assignment or approved sublet\n"
            f"- A reduced termination fee below {fee_months:g} month(s) of rent\n"
            f"- A firm move-out date with professional cleaning and walkthrough\n\n"
            f"{savings_line}\n\n"
            f"Thank you for your time — I'd appreciate discussing options this week.\n"
        )
        phone_script = (
            "Hi, this is [your name] in unit [number]. I need to discuss ending my lease early. "
            f"I have {months_remaining} months left and can provide 30–45 days notice. "
            "Are you open to a lease assignment, sublet, or a reduced termination fee? "
            "I can send photos of the unit condition and help coordinate showings for a replacement tenant."
        )
        return {
            "talking_points": talking_points,
            "email_template": email_template,
            "phone_script": phone_script,
        }

    def analyze_break_cost(
        self,
        user_id: int,
        months_remaining: int,
        monthly_rent: float,
        break_fee_percent: float = 1.5,
        *,
        interim_monthly: float | None = None,
        move_out_cost: float | None = None,
        persist: bool = True,
    ) -> dict[str, Any]:
        if months_remaining <= 0:
            raise ValueError("months_remaining must be positive")
        if monthly_rent <= 0:
            raise ValueError("monthly_rent must be positive")
        if break_fee_percent < 0:
            raise ValueError("break_fee_percent must be non-negative")

        rent = float(monthly_rent)
        months = int(months_remaining)
        interim_rate = float(interim_monthly or _DEFAULT_INTERIM_MONTHLY)
        interim_rate = min(interim_rate, rent * _INTERIM_ROOMMATE_FACTOR)
        move_out = float(move_out_cost or _DEFAULT_MOVE_OUT_COST)

        remaining_rent = _round2(months * rent)
        scenario_a_cost = _round2(remaining_rent + move_out)

        break_fee = _break_fee_amount(rent, break_fee_percent)
        interim_housing = _round2(months * interim_rate)
        moving_buffer = _round2(move_out * 0.5)
        scenario_b_cost = _round2(break_fee + interim_housing + moving_buffer)

        if scenario_b_cost < scenario_a_cost:
            recommendation = "break_early"
            savings = _round2(scenario_a_cost - scenario_b_cost)
        elif scenario_a_cost < scenario_b_cost:
            recommendation = "stay_through_lease"
            savings = _round2(scenario_b_cost - scenario_a_cost)
        else:
            recommendation = "either"
            savings = 0.0

        timeline_impact = {
            "months_remaining": months,
            "monthly_cashflow_delta_if_break": _round2(rent - interim_rate),
            "total_cash_released_if_break": savings if recommendation == "break_early" else 0.0,
            "break_even_month": (
                int(max(1, round(break_fee / max(rent - interim_rate, 1))))
                if rent > interim_rate
                else None
            ),
        }

        negotiation = self.generate_negotiation_script(
            months_remaining=months,
            monthly_rent=rent,
            break_fee_percent=break_fee_percent,
            savings_if_negotiated=savings if recommendation == "stay_through_lease" else savings * 0.3,
        )

        record_id = None
        if persist:
            record = LeaseBreakAnalysis(
                user_id=user_id,
                months_remaining=months,
                monthly_rent=rent,
                break_fee_percent=break_fee_percent,
                scenario_a_cost=scenario_a_cost,
                scenario_b_cost=scenario_b_cost,
                recommendation=recommendation,
                savings=savings,
            )
            db.session.add(record)
            db.session.commit()
            record_id = str(record.id)

        return {
            "analysis_id": record_id,
            "months_remaining": months,
            "monthly_rent": rent,
            "break_fee_percent": float(break_fee_percent),
            "scenario_a": {
                "key": "stay",
                "label": "Stay through lease end",
                "remaining_rent": remaining_rent,
                "move_out_cost": move_out,
                "total_cost": scenario_a_cost,
            },
            "scenario_b": {
                "key": "break",
                "label": "Break lease early",
                "break_fee": break_fee,
                "interim_housing_monthly": interim_rate,
                "interim_housing_total": interim_housing,
                "moving_buffer": moving_buffer,
                "total_cost": scenario_b_cost,
            },
            "scenario_a_cost": scenario_a_cost,
            "scenario_b_cost": scenario_b_cost,
            "recommendation": recommendation,
            "recommendation_label": {
                "break_early": "Breaking early likely saves money",
                "stay_through_lease": "Staying through the lease is cheaper",
                "either": "Costs are roughly equal — decide on lifestyle fit",
            }[recommendation],
            "savings": savings,
            "timeline_impact": timeline_impact,
            "negotiation_script": negotiation,
        }
