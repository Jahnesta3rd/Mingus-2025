#!/usr/bin/env python3
"""Monthly readiness gates and emergency exit triggers for relationship safety."""

from __future__ import annotations

import math
from datetime import datetime, timedelta
from typing import Any
from uuid import UUID

from backend.models.database import db
from backend.models.independence_cost_assessment import IndependenceCostAssessment
from backend.models.relationship_milestone_checkin import RelationshipMilestoneCheckin
from backend.models.side_income_commitment import UserSideIncomeCommitment
from backend.models.vibe_tracker import VibePersonAssessment, VibeTrackedPerson

VALID_VIBE_TRENDS = frozenset({"declining", "stable", "improving"})
VALID_FEELS_SAFE = frozenset({"yes", "mostly", "sometimes", "no", "unsafe"})
_UNSAFE_FEELS = frozenset({"no", "unsafe", "never", "not_safe"})

EMERGENCY_TRIGGER_TYPES = (
    "abuse_escalation",
    "physical_threat",
    "substance_abuse",
    "infidelity",
    "financial_control",
    "isolation",
    "emotional_abuse",
    "imminent_danger",
    "stalking_or_monitoring",
    "sexual_coercion",
)

DV_RESOURCES: list[dict[str, str]] = [
    {
        "name": "National Domestic Violence Hotline",
        "phone": "1-800-799-7233",
        "url": "https://www.thehotline.org",
        "type": "hotline",
    },
    {
        "name": "Crisis Text Line",
        "phone": "Text HOME to 741741",
        "url": "https://www.crisistextline.org",
        "type": "text",
    },
    {
        "name": "Safety plan template",
        "phone": "",
        "url": "https://www.thehotline.org/plan-for-safety/",
        "type": "safety_plan",
    },
    {
        "name": "Local shelter finder",
        "phone": "1-800-799-7233",
        "url": "https://www.domesticshelters.org",
        "type": "shelter",
    },
    {
        "name": "Free counseling (SAMHSA)",
        "phone": "1-800-662-4357",
        "url": "https://www.samhsa.gov/find-help",
        "type": "counseling",
    },
]


def _bool_value(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"true", "1", "yes", "on"}
    return bool(value)


class RelationshipMilestoneChecker:
    """Assess monthly readiness and detect emergency exit triggers."""

    def detect_emergency_triggers(self, responses: dict[str, Any]) -> list[str]:
        """Return triggered emergency flags. Conservative: prioritize safety over false positives."""
        triggered: list[str] = []
        seen: set[str] = set()

        def add(flag: str) -> None:
            if flag in EMERGENCY_TRIGGER_TYPES and flag not in seen:
                seen.add(flag)
                triggered.append(flag)

        explicit = responses.get("emergency_signals") or responses.get("emergency_flags") or {}
        if isinstance(explicit, dict):
            for key in EMERGENCY_TRIGGER_TYPES:
                if _bool_value(explicit.get(key)):
                    add(key)

        feels_safe = str(responses.get("feels_safe") or "").strip().lower()
        vibe_trend = str(responses.get("vibe_trend") or "").strip().lower()
        needs_sooner = _bool_value(responses.get("needs_to_leave_sooner"))
        prefer_now = _bool_value(responses.get("prefer_leave_now"))

        if feels_safe in _UNSAFE_FEELS:
            add("physical_threat")
            add("abuse_escalation")
            add("emotional_abuse")

        if prefer_now:
            add("imminent_danger")

        if needs_sooner and feels_safe != "yes":
            add("abuse_escalation")
            add("imminent_danger")

        if vibe_trend == "declining" and feels_safe in {"sometimes", "no", "unsafe", "mostly"}:
            add("abuse_escalation")

        if feels_safe == "sometimes" and needs_sooner:
            add("emotional_abuse")

        return triggered

    def _determine_status(
        self,
        responses: dict[str, Any],
        emergency_flags: list[str],
    ) -> str:
        feels_safe = str(responses.get("feels_safe") or "").strip().lower()
        vibe_trend = str(responses.get("vibe_trend") or "").strip().lower()
        needs_sooner = _bool_value(responses.get("needs_to_leave_sooner"))
        on_track = _bool_value(responses.get("on_track_savings"))
        prefer_now = _bool_value(responses.get("prefer_leave_now"))

        if emergency_flags or feels_safe in _UNSAFE_FEELS or prefer_now:
            return "emergency"

        if vibe_trend == "improving" and feels_safe in {"yes", "mostly"} and not needs_sooner:
            return "improving"

        if needs_sooner or not on_track:
            return "accelerate"

        return "on_track"

    def _build_next_steps(
        self,
        status: str,
        emergency_flags: list[str],
        responses: dict[str, Any],
    ) -> list[str]:
        steps: list[str] = []
        if status == "emergency":
            steps.extend(
                [
                    "Your safety comes first. Contact the National DV Hotline (1-800-799-7233) or local emergency services if you are in immediate danger.",
                    "Use a safety plan and identify a trusted contact you can reach tonight.",
                    "Consider Tier 0 emergency exit planning — bypass the standard savings timeline.",
                ]
            )
            if "financial_control" in emergency_flags:
                steps.append("Secure copies of important documents and access to your own funds if safe to do so.")
            if "isolation" in emergency_flags:
                steps.append("Reconnect with a trusted friend, family member, or advocate outside the household.")
            return steps

        if status == "accelerate":
            steps.extend(
                [
                    "Increase side income hours or explore interim housing (roommate, sublet).",
                    "Review your independence gap and adjust monthly savings targets.",
                ]
            )
            if _bool_value(responses.get("needs_to_leave_sooner")):
                steps.append("Prioritize lease-break analysis and emergency fund access.")
            return steps

        if status == "improving":
            steps.extend(
                [
                    "Your vibe trend is improving — you can continue independence planning at a steady pace.",
                    "Optional: invest energy in relationship repair with clear boundaries.",
                    "Keep monthly check-ins to monitor whether improvement continues.",
                ]
            )
            return steps

        steps.extend(
            [
                "Stay on your current savings and side-income plan.",
                "Complete next month's readiness check to confirm you remain on track.",
            ]
        )
        return steps

    def monthly_readiness_check(
        self,
        user_id: int,
        person_id: UUID,
        responses: dict[str, Any],
    ) -> dict[str, Any]:
        vibe_trend = str(responses.get("vibe_trend") or "").strip().lower()
        feels_safe = str(responses.get("feels_safe") or "").strip().lower()

        if vibe_trend not in VALID_VIBE_TRENDS:
            raise ValueError("vibe_trend must be declining, stable, or improving")
        if feels_safe not in VALID_FEELS_SAFE:
            raise ValueError("feels_safe must be yes, mostly, sometimes, no, or unsafe")

        partner = VibeTrackedPerson.query.filter_by(
            id=person_id,
            user_id=user_id,
            is_archived=False,
        ).first()
        if partner is None:
            raise LookupError("Partner not found")

        emergency_flags = self.detect_emergency_triggers(responses)
        status = self._determine_status(responses, emergency_flags)
        next_steps = self._build_next_steps(status, emergency_flags, responses)
        resources = list(DV_RESOURCES)

        record = RelationshipMilestoneCheckin(
            user_id=user_id,
            person_id=person_id,
            vibe_trend=vibe_trend,
            feels_safe=feels_safe,
            needs_to_leave_sooner=_bool_value(responses.get("needs_to_leave_sooner")),
            on_track_savings=_bool_value(responses.get("on_track_savings")),
            prefer_leave_now=_bool_value(responses.get("prefer_leave_now")),
            status=status,
            emergency_flags=emergency_flags or None,
            next_steps=next_steps,
            resources_provided=resources,
        )
        db.session.add(record)
        db.session.commit()

        return {
            "status": status,
            "emergency_alert": status == "emergency",
            "emergency_flags": emergency_flags,
            "next_steps": next_steps,
            "resources_if_needed": resources,
            "checkin_id": str(record.id),
            "tier_recommendation": "tier_0_emergency_exit" if status == "emergency" else None,
        }

    def quarterly_reassessment(self, user_id: int, person_id: UUID) -> dict[str, Any]:
        partner = VibeTrackedPerson.query.filter_by(
            id=person_id,
            user_id=user_id,
            is_archived=False,
        ).first()
        if partner is None:
            raise LookupError("Partner not found")

        three_months_ago = datetime.utcnow() - timedelta(days=92)
        checkins = (
            RelationshipMilestoneCheckin.query.filter(
                RelationshipMilestoneCheckin.user_id == user_id,
                RelationshipMilestoneCheckin.person_id == person_id,
                RelationshipMilestoneCheckin.created_at >= three_months_ago,
            )
            .order_by(RelationshipMilestoneCheckin.created_at.asc())
            .all()
        )

        assessments = (
            VibePersonAssessment.query.filter_by(tracked_person_id=person_id)
            .order_by(VibePersonAssessment.completed_at.desc())
            .limit(12)
            .all()
        )
        vibe_scores = [int(a.emotional_score) for a in reversed(assessments)]

        icc = (
            IndependenceCostAssessment.query.filter_by(
                user_id=user_id,
                person_id=person_id,
            )
            .order_by(IndependenceCostAssessment.created_at.desc())
            .first()
        )
        commitment = (
            UserSideIncomeCommitment.query.filter_by(
                user_id=user_id,
                person_id=person_id,
            )
            .order_by(UserSideIncomeCommitment.created_at.desc())
            .first()
        )

        original_timeline = None
        current_timeline = None
        monthly_gap = None
        startup_cost = None
        if icc is not None:
            monthly_gap = float(icc.monthly_independence_gap or 0)
            startup_cost = float(icc.total_startup_cost or 0)
            original_timeline = (
                int(math.ceil(float(icc.months_to_save_startup)))
                if icc.months_to_save_startup
                else None
            )
        if commitment is not None:
            current_timeline = commitment.independence_timeline_with_income_months
            if original_timeline is None:
                original_timeline = commitment.independence_timeline_original_months

        progress_notes: list[str] = []
        if commitment and commitment.df1_monthly_income_actual:
            progress_notes.append(
                f"Side income: earning ${float(commitment.df1_monthly_income_actual):,.0f}/month "
                f"toward {commitment.selected_job}."
            )
        if checkins:
            improving_count = sum(1 for c in checkins if c.status == "improving")
            emergency_count = sum(1 for c in checkins if c.status == "emergency")
            progress_notes.append(
                f"{len(checkins)} monthly check-in(s) in the last quarter "
                f"({improving_count} improving, {emergency_count} emergency)."
            )
        if original_timeline is not None and current_timeline is not None:
            delta = original_timeline - current_timeline
            if delta > 0:
                progress_notes.append(f"Timeline improved by {delta} month(s) since planning started.")
            elif delta < 0:
                progress_notes.append("Timeline extended — consider accelerating savings or side income.")

        latest_status = checkins[-1].status if checkins else None
        celebration = latest_status in {"on_track", "improving"}

        return {
            "partner_name": partner.nickname,
            "vibe_scores": vibe_scores,
            "checkin_history": [
                {
                    "date": c.created_at.isoformat(),
                    "status": c.status,
                    "vibe_trend": c.vibe_trend,
                    "feels_safe": c.feels_safe,
                }
                for c in checkins
            ],
            "timeline": {
                "original_months": original_timeline,
                "current_months": current_timeline,
                "monthly_gap": monthly_gap,
                "startup_cost": startup_cost,
            },
            "progress_notes": progress_notes,
            "celebrate_progress": celebration,
            "improvement_path": (
                {
                    "available": latest_status == "improving",
                    "options": [
                        "Continue independence planning at current pace",
                        "Focus on relationship repair with boundaries",
                    ],
                }
                if latest_status == "improving"
                else None
            ),
            "resources": DV_RESOURCES,
        }
