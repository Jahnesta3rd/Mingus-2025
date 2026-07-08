#!/usr/bin/env python3
"""Independence Cost Calculator (ICC) trigger detection and API routes."""

from __future__ import annotations

import logging
from datetime import date, datetime
from typing import Any
from uuid import UUID

from flask import Blueprint, jsonify, request
from sqlalchemy import func, text

from backend.auth.decorators import current_user, get_current_user_db_id, require_auth
from backend.models.database import db
from backend.models.independence_cost_assessment import IndependenceCostAssessment
from backend.models.user_models import User
from backend.models.vibe_tracker import VibePersonAssessment, VibeTrackedPerson
from backend.services.independence_cost_service import (
    IndependenceCostCalculator,
    _is_monotonically_declining,
)

logger = logging.getLogger(__name__)

independence_cost_bp = Blueprint(
    "independence_cost",
    __name__,
    url_prefix="/api/independence-cost",
)

_PARTNER_RELATIONSHIP_TYPES = frozenset({"partner", "spouse"})
_COHABITING_COST_THRESHOLD = 800.0


class IndependenceCostTriggerDetector:
    """Detect when the independence cost calculator card should be shown."""

    def should_show_independence_calculator(
        self,
        user_id: int,
    ) -> tuple[bool, UUID | None]:
        partners = (
            VibeTrackedPerson.query.filter(
                VibeTrackedPerson.user_id == user_id,
                VibeTrackedPerson.is_archived.is_(False),
                func.lower(VibeTrackedPerson.relationship_type).in_(
                    sorted(_PARTNER_RELATIONSHIP_TYPES)
                ),
            )
            .order_by(VibeTrackedPerson.created_at.asc())
            .all()
        )

        for person in partners:
            if not self.is_cohabiting(person.id):
                continue
            is_declining, _scores = self.is_declining_12_weeks(person.id)
            if is_declining:
                return True, person.id

        return False, None

    def is_cohabiting(self, person_id: UUID) -> bool:
        person = VibeTrackedPerson.query.filter_by(id=person_id).first()
        if person is None or person.estimated_monthly_cost is None:
            return False
        return float(person.estimated_monthly_cost) >= _COHABITING_COST_THRESHOLD

    def is_declining_12_weeks(self, person_id: UUID) -> tuple[bool, list[int]]:
        assessments = (
            VibePersonAssessment.query.filter_by(tracked_person_id=person_id)
            .order_by(VibePersonAssessment.completed_at.desc())
            .limit(12)
            .all()
        )
        scores = [int(row.emotional_score) for row in reversed(assessments)]
        if len(scores) < 10:
            return False, scores

        is_declining = (
            _is_monotonically_declining(scores)
            and scores[-1] <= 2
            and scores[0] != scores[-1]
        )
        return is_declining, scores


def _resolve_db_user() -> User | None:
    user = current_user
    if user is not None:
        return user
    db_id = get_current_user_db_id()
    if db_id is None:
        return None
    return User.query.get(db_id)


def _parse_person_id(raw: str | None) -> UUID | None:
    if not raw:
        return None
    try:
        return UUID(str(raw).strip())
    except (TypeError, ValueError, AttributeError):
        return None


def _get_partner_for_user(user_id: int, person_id: UUID) -> VibeTrackedPerson | None:
    return VibeTrackedPerson.query.filter_by(id=person_id, user_id=user_id).first()


def _user_dismissed_flag(user: User) -> bool:
    if hasattr(user, "has_independence_calculator_dismissed"):
        return bool(user.has_independence_calculator_dismissed)
    try:
        row = db.session.execute(
            text(
                "SELECT has_independence_calculator_dismissed "
                "FROM users WHERE id = :user_id LIMIT 1"
            ),
            {"user_id": user.id},
        ).fetchone()
        return bool(row[0]) if row else False
    except Exception:
        logger.debug("Dismiss flag lookup failed for user_id=%s", user.id, exc_info=True)
        return False


def _has_assessment_today(user_id: int, person_id: UUID | None) -> bool:
    if person_id is None:
        return False
    today = date.today()
    return (
        IndependenceCostAssessment.query.filter(
            IndependenceCostAssessment.user_id == user_id,
            IndependenceCostAssessment.person_id == person_id,
            func.date(IndependenceCostAssessment.assessment_date) == today,
        ).count()
        > 0
    )


def _format_recommendation_message(
    *,
    city: str | None,
    monthly_cost: float,
    gap: float,
    partner_name: str,
) -> str:
    city_label = city or "your area"
    return (
        f"Based on {partner_name}'s vibe trend and shared housing costs, "
        f"living solo in {city_label} could run about ${monthly_cost:,.0f}/month "
        f"(${gap:,.0f} more than you pay now)."
    )


def _assessment_response_payload(
    assessment: dict[str, Any],
    *,
    assessment_id: UUID | None = None,
) -> dict[str, Any]:
    gap_value = assessment.get("gap", {})
    timeline = assessment.get("timeline", {})
    if isinstance(gap_value, dict):
        monthly_gap = gap_value.get("monthly_independence_gap")
    else:
        monthly_gap = gap_value
    payload = {
        "monthly_costs": assessment.get("monthly_costs", {}),
        "startup_costs": assessment.get("startup_costs", {}),
        "current_situation": assessment.get("current_situation", {}),
        "gap": monthly_gap,
        "timeline_months": timeline.get("months_to_save_startup"),
        "vibe_data": assessment.get("vibe_data", {}),
        "location": assessment.get("location", {}),
        "market_rent": assessment.get("market_rent", {}),
    }
    if assessment_id is not None:
        payload["icc_assessment_id"] = str(assessment_id)
    return payload


def _persist_assessment_record(
    user_id: int,
    person_id: UUID,
    assessment: dict[str, Any],
) -> IndependenceCostAssessment:
    """Create or return today's persisted ICC assessment row."""
    today = date.today()
    existing = (
        IndependenceCostAssessment.query.filter(
            IndependenceCostAssessment.user_id == user_id,
            IndependenceCostAssessment.person_id == person_id,
            func.date(IndependenceCostAssessment.assessment_date) == today,
        )
        .order_by(IndependenceCostAssessment.created_at.desc())
        .first()
    )
    if existing is not None:
        return existing

    monthly = assessment.get("monthly_costs", {})
    gap_info = assessment.get("gap", {})
    timeline = assessment.get("timeline", {})
    location = assessment.get("location", {})
    market = assessment.get("market_rent", {})
    current = assessment.get("current_situation", {})
    vibe = assessment.get("vibe_data", {})
    scores = vibe.get("emotional_scores") or []

    record = IndependenceCostAssessment(
        user_id=user_id,
        person_id=person_id,
        zip_code=location.get("zip_code"),
        city_name=location.get("city_name"),
        market_rent_1br=market.get("median_1br_rent"),
        estimated_housing=monthly.get("housing", 0),
        estimated_utilities=monthly.get("utilities", 0),
        estimated_food=monthly.get("food", 0),
        estimated_transportation=monthly.get("transportation", 0),
        estimated_phone_internet=monthly.get("phone_internet", 0),
        estimated_other=monthly.get("other", 0),
        total_monthly_solo=monthly.get("total_monthly", 0),
        total_startup_cost=gap_info.get("startup_cost"),
        current_housing_contribution=current.get("current_housing_contribution"),
        monthly_independence_gap=gap_info.get("monthly_independence_gap"),
        months_to_save_startup=timeline.get("months_to_save_startup"),
        partner_emotional_score_current=scores[-1] if scores else None,
        partner_emotional_trend="declining" if vibe.get("is_declining_12_weeks") else None,
    )
    db.session.add(record)
    db.session.commit()
    return record


@independence_cost_bp.route("/should-recommend", methods=["GET"])
@require_auth
def should_recommend():
    user = _resolve_db_user()
    if user is None:
        return jsonify({"error": "Authentication required"}), 401

    if _user_dismissed_flag(user):
        return jsonify({"should_recommend": False})

    detector = IndependenceCostTriggerDetector()
    should_show, person_id = detector.should_show_independence_calculator(user.id)
    if not should_show or person_id is None:
        return jsonify({"should_recommend": False})

    partner = _get_partner_for_user(user.id, person_id)
    if partner is None:
        return jsonify({"should_recommend": False})

    try:
        calculator = IndependenceCostCalculator()
        assessment = calculator.calculate_full_assessment(user.id, person_id)
    except Exception as exc:
        logger.exception("ICC should-recommend calculation failed for user_id=%s", user.id)
        return jsonify({"error": "calculation_failed", "message": str(exc)}), 500

    monthly_costs = assessment.get("monthly_costs", {})
    gap_info = assessment.get("gap", {})
    location = assessment.get("location", {})
    monthly_cost = float(monthly_costs.get("total_monthly") or 0)
    current_cost = float(
        assessment.get("current_situation", {}).get("current_housing_contribution") or 0
    )
    gap = float(gap_info.get("monthly_independence_gap") or 0)
    startup_cost = float(gap_info.get("startup_cost") or 0)
    assessment_record = _persist_assessment_record(user.id, person_id, assessment)

    return jsonify(
        {
            "should_recommend": True,
            "icc_assessment_id": str(assessment_record.id),
            "partner_id": str(person_id),
            "partner_name": partner.nickname,
            "city": location.get("city_name"),
            "monthly_cost": monthly_cost,
            "current_cost": current_cost,
            "gap": gap,
            "startup_cost": startup_cost,
            "message": _format_recommendation_message(
                city=location.get("city_name"),
                monthly_cost=monthly_cost,
                gap=gap,
                partner_name=partner.nickname,
            ),
            "cta": "Explore RFR Module",
        }
    )


@independence_cost_bp.route("/assess", methods=["GET"])
@require_auth
def assess():
    user = _resolve_db_user()
    if user is None:
        return jsonify({"error": "Authentication required"}), 401

    person_id = _parse_person_id(request.args.get("person_id"))
    if person_id is None:
        return jsonify({"error": "invalid_person_id", "message": "person_id is required"}), 400

    partner = _get_partner_for_user(user.id, person_id)
    if partner is None:
        return jsonify({"error": "not_found", "message": "Partner not found"}), 404

    try:
        calculator = IndependenceCostCalculator()
        assessment = calculator.calculate_full_assessment(user.id, person_id)
    except Exception as exc:
        logger.exception("ICC assess failed for user_id=%s person_id=%s", user.id, person_id)
        return jsonify({"error": "calculation_failed", "message": str(exc)}), 500

    assessment_record = _persist_assessment_record(user.id, person_id, assessment)
    return jsonify(
        _assessment_response_payload(assessment, assessment_id=assessment_record.id)
    )


@independence_cost_bp.route("/dismiss", methods=["POST"])
@require_auth
def dismiss():
    user = _resolve_db_user()
    if user is None:
        return jsonify({"error": "Authentication required"}), 401

    if hasattr(user, "has_independence_calculator_dismissed"):
        user.has_independence_calculator_dismissed = True
    else:
        db.session.execute(
            text(
                "UPDATE users SET has_independence_calculator_dismissed = true "
                "WHERE id = :user_id"
            ),
            {"user_id": user.id},
        )
    user.updated_at = datetime.utcnow()
    db.session.commit()
    return jsonify({"success": True})


@independence_cost_bp.route("/status", methods=["GET"])
@require_auth
def status():
    user = _resolve_db_user()
    if user is None:
        return jsonify({"error": "Authentication required"}), 401

    dismissed = _user_dismissed_flag(user)
    detector = IndependenceCostTriggerDetector()
    can_calculate, partner_id = detector.should_show_independence_calculator(user.id)
    if dismissed:
        can_calculate = False

    return jsonify(
        {
            "dismissed": dismissed,
            "can_calculate": can_calculate,
            "has_assessment_today": _has_assessment_today(user.id, partner_id),
            "partner_id": str(partner_id) if partner_id else None,
        }
    )
