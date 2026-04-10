#!/usr/bin/env python3
"""Life Ledger composite score and insight generation."""

from __future__ import annotations

from decimal import Decimal
from typing import Any
from uuid import UUID

from backend.models.database import db
from backend.models.financial_setup import RecurringExpense
from backend.models.life_ledger import (
    LifeLedgerInsight,
    LifeLedgerProfile,
)
from backend.models.user_models import User
from backend.models.vibe_checkups import VibeCheckupsLead

VC_IMPORT_SOURCE = "vibe_checkups_import"


MODULE_WEIGHTS = {
    "vibe": 0.20,
    "body": 0.25,
    "roof": 0.35,
    "vehicle": 0.20,
}


def compute_life_ledger_score(profile: LifeLedgerProfile) -> int:
    """Weighted mean of non-null module scores; weights renormalized; clamped 0–100."""
    pairs: list[tuple[int, float]] = []
    if profile.vibe_score is not None:
        pairs.append((profile.vibe_score, MODULE_WEIGHTS["vibe"]))
    if profile.body_score is not None:
        pairs.append((profile.body_score, MODULE_WEIGHTS["body"]))
    if profile.roof_score is not None:
        pairs.append((profile.roof_score, MODULE_WEIGHTS["roof"]))
    if profile.vehicle_score is not None:
        pairs.append((profile.vehicle_score, MODULE_WEIGHTS["vehicle"]))
    if not pairs:
        return 0
    total_w = sum(w for _, w in pairs)
    weighted = sum(s * w for s, w in pairs) / total_w
    rounded = int(round(weighted))
    return max(0, min(100, rounded))


def generate_insights(user_id: int, profile: LifeLedgerProfile) -> list[dict[str, Any]]:
    """Up to one low-score insight per module (only modules with a score)."""
    out: list[dict[str, Any]] = []

    if profile.vibe_score is not None and profile.vibe_score < 50:
        out.append(
            {
                "module": "vibe",
                "insight_type": "relationship_financial_drain",
                "message": (
                    "Your relationship wellness score suggests meaningful financial "
                    "drain risk—review shared money patterns before they compound."
                ),
                "action_url": "/dashboard/wellness",
            }
        )

    if profile.body_score is not None and profile.body_score < 50:
        out.append(
            {
                "module": "body",
                "insight_type": "health_productivity_cost",
                "message": (
                    "Health habits that slip often show up as lost focus and "
                    "productivity—worth budgeting time and care like any other cost."
                ),
                "action_url": "/dashboard/wellness",
            }
        )

    if profile.roof_score is not None and profile.roof_score < 60:
        out.append(
            {
                "module": "roof",
                "insight_type": "housing_wealth_gap",
                "message": (
                    "Your housing score hints at a wealth-building gap—small location "
                    "or cost tweaks can materially change long-term net worth."
                ),
                "action_url": "/dashboard?tab=housing",
            }
        )

    if profile.vehicle_score is not None and profile.vehicle_score < 60:
        out.append(
            {
                "module": "vehicle",
                "insight_type": "maintenance_cost_risk",
                "message": (
                    "Vehicle upkeep risk is elevated—plan for maintenance spikes so "
                    "they do not derail cash flow."
                ),
                "action_url": "/dashboard/vehicle",
            }
        )

    return out


def get_or_create_profile(user_id: int) -> LifeLedgerProfile:
    profile = LifeLedgerProfile.query.filter_by(user_id=user_id).first()
    if profile:
        return profile
    profile = LifeLedgerProfile(user_id=user_id)
    db.session.add(profile)
    db.session.flush()
    return profile


def _ensure_vibe_checkups_relationship_expense(user_id: int, lead: VibeCheckupsLead) -> None:
    existing = RecurringExpense.query.filter_by(
        user_id=user_id, source=VC_IMPORT_SOURCE
    ).first()
    if existing:
        return
    monthly = max(0, int(round(lead.total_annual_projection / 12)))
    row = RecurringExpense(
        user_id=user_id,
        name="Estimated relationship costs (Vibe Checkups)",
        amount=Decimal(monthly),
        category="relationship",
        frequency="monthly",
        is_active=True,
        source=VC_IMPORT_SOURCE,
    )
    db.session.add(row)


def import_vibe_lead(user_id: int, vc_lead_id: str) -> LifeLedgerProfile:
    """
    Link a converted Vibe Checkups lead to the user's Life Ledger profile and
    add the relationship recurring expense import line (idempotent on source).
    """
    try:
        lead_uuid = UUID(str(vc_lead_id).strip())
    except (ValueError, TypeError) as e:
        raise ValueError(f"Invalid vc_lead_id: {vc_lead_id!r}") from e

    lead = VibeCheckupsLead.query.filter_by(id=lead_uuid).first()
    if lead is None:
        raise ValueError("Vibe Checkups lead not found")

    user = db.session.get(User, user_id)
    if user is None:
        raise ValueError("User not found")
    if (lead.email or "").strip().lower() != (user.email or "").strip().lower():
        raise ValueError("Lead email does not match registered user")
    if not lead.mingus_converted:
        raise ValueError(
            "Lead is not eligible for import (mingus_converted is false)"
        )

    profile = get_or_create_profile(user_id)
    profile.vibe_lead_id = lead.id
    profile.vibe_score = int(round((lead.emotional_score + lead.financial_score) / 2))
    profile.vibe_annual_projection = lead.total_annual_projection
    profile.life_ledger_score = compute_life_ledger_score(profile)

    _ensure_vibe_checkups_relationship_expense(user_id, lead)
    sync_insights_for_user(user_id, profile)
    db.session.commit()
    return profile


def sync_insights_for_user(user_id: int, profile: LifeLedgerProfile) -> list[dict[str, Any]]:
    """
    Align DB insights with generate_insights: drop stale active rows, upsert messages,
    skip dismissed pairs.
    """
    generated = generate_insights(user_id, profile)
    desired_keys = {(g["module"], g["insight_type"]) for g in generated}

    active = LifeLedgerInsight.query.filter_by(user_id=user_id, dismissed=False).all()
    for row in active:
        if (row.module, row.insight_type) not in desired_keys:
            db.session.delete(row)

    result: list[dict[str, Any]] = []
    for g in generated:
        row = LifeLedgerInsight.query.filter_by(
            user_id=user_id,
            module=g["module"],
            insight_type=g["insight_type"],
        ).first()
        if row is None:
            row = LifeLedgerInsight(
                user_id=user_id,
                module=g["module"],
                insight_type=g["insight_type"],
                message=g["message"],
                action_url=g["action_url"],
                dismissed=False,
            )
            db.session.add(row)
            db.session.flush()
            result.append(_insight_to_dict(row))
        elif row.dismissed:
            continue
        else:
            row.message = g["message"]
            row.action_url = g["action_url"]
            result.append(_insight_to_dict(row))

    return result


def _insight_to_dict(row: LifeLedgerInsight) -> dict[str, Any]:
    return {
        "id": str(row.id),
        "module": row.module,
        "insight_type": row.insight_type,
        "message": row.message,
        "action_url": row.action_url,
        "dismissed": row.dismissed,
    }


def profile_to_dict(
    profile: LifeLedgerProfile, insights: list[dict[str, Any]]
) -> dict[str, Any]:
    computed = compute_life_ledger_score(profile)
    return {
        "id": str(profile.id),
        "user_id": profile.user_id,
        "vibe_score": profile.vibe_score,
        "body_score": profile.body_score,
        "roof_score": profile.roof_score,
        "vehicle_score": profile.vehicle_score,
        "life_ledger_score": computed,
        "vibe_lead_id": str(profile.vibe_lead_id) if profile.vibe_lead_id else None,
        "vibe_annual_projection": profile.vibe_annual_projection,
        "body_health_cost_projection": profile.body_health_cost_projection,
        "roof_housing_wealth_gap": profile.roof_housing_wealth_gap,
        "vehicle_annual_maintenance": profile.vehicle_annual_maintenance,
        "created_at": profile.created_at.isoformat() if profile.created_at else None,
        "updated_at": profile.updated_at.isoformat() if profile.updated_at else None,
        "insights": insights,
    }
