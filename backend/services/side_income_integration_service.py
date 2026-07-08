#!/usr/bin/env python3
"""ICC ↔ DF1 integration: side income commitments and milestone tracking."""

from __future__ import annotations

import math
from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy.exc import IntegrityError

from backend.models.database import db
from backend.models.independence_cost_assessment import IndependenceCostAssessment
from backend.models.side_income_commitment import UserSideIncomeCommitment

HANDOFF_URL = "/dashboard/tools?tab=debt&subTab=second-job"


class IntegrationError(Exception):
    def __init__(self, message: str, *, status_code: int = 400, error: str = "invalid_request"):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.error = error


def _parse_uuid(value: Any, field: str) -> UUID:
    if value is None or value == "":
        raise IntegrationError(f"{field} is required", status_code=400, error="invalid_input")
    try:
        return UUID(str(value).strip())
    except (TypeError, ValueError, AttributeError) as exc:
        raise IntegrationError(f"{field} must be a valid UUID", status_code=400, error="invalid_input") from exc


def _to_int_months(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(math.ceil(float(value)))
    except (TypeError, ValueError):
        return None


def _recalculate_timeline(
    assessment: IndependenceCostAssessment | None,
    income_amount: float,
) -> tuple[int | None, int | None]:
    if assessment is None:
        return None, None

    original_gap = float(assessment.monthly_independence_gap or 0)
    startup_cost = float(assessment.total_startup_cost or 0)
    original_timeline = _to_int_months(assessment.months_to_save_startup)

    new_gap = max(0.0, original_gap - income_amount)
    if new_gap > 0 and startup_cost > 0:
        new_timeline = int(math.ceil(startup_cost / new_gap))
    else:
        new_timeline = 0

    return original_timeline, new_timeline


class SideIncomeIntegrationService:
    """Create commitments on ICC job selection and update milestones from DF1."""

    def create_icc_to_df1_handoff(
        self,
        *,
        user_id: int,
        icc_assessment_id: UUID,
        person_id: UUID,
        selected_job: str,
        df1_job_type: str | None,
        target_monthly_income: float,
        gap_coverage_pct: float,
    ) -> dict[str, Any]:
        selected_job = str(selected_job or "").strip()
        if not selected_job:
            raise IntegrationError("selected_job is required", status_code=400, error="invalid_input")
        if target_monthly_income <= 0:
            raise IntegrationError(
                "target_monthly_income must be positive",
                status_code=400,
                error="invalid_input",
            )

        assessment = IndependenceCostAssessment.query.filter_by(id=icc_assessment_id).first()
        if assessment is None:
            raise IntegrationError("ICC assessment not found", status_code=404, error="not_found")
        if assessment.user_id != user_id:
            raise IntegrationError(
                "You do not have access to this assessment",
                status_code=403,
                error="forbidden",
            )
        if assessment.person_id != person_id:
            raise IntegrationError(
                "person_id does not match the ICC assessment partner",
                status_code=400,
                error="person_mismatch",
            )

        existing = UserSideIncomeCommitment.query.filter_by(
            user_id=user_id,
            icc_assessment_id=icc_assessment_id,
        ).first()
        if existing is not None:
            raise IntegrationError(
                "A side income commitment already exists for this assessment",
                status_code=409,
                error="already_committed",
            )

        original_timeline = _to_int_months(assessment.months_to_save_startup)
        commitment = UserSideIncomeCommitment(
            user_id=user_id,
            icc_assessment_id=icc_assessment_id,
            person_id=person_id,
            selected_job=selected_job,
            df1_job_type=df1_job_type,
            target_monthly_income=round(float(target_monthly_income), 2),
            status="selected",
            independence_timeline_original_months=original_timeline,
            gap_coverage_pct_at_selection=round(float(gap_coverage_pct), 2),
        )
        db.session.add(commitment)
        try:
            db.session.commit()
        except IntegrityError as exc:
            db.session.rollback()
            raise IntegrationError(
                "A side income commitment already exists for this assessment",
                status_code=409,
                error="already_committed",
            ) from exc

        return {
            "success": True,
            "commitment_id": str(commitment.id),
            "handoff_url": HANDOFF_URL,
            "message": f"Great! You selected {selected_job}. Let's get you set up.",
        }

    def record_df1_milestone(
        self,
        *,
        commitment_id: UUID,
        milestone_type: str,
        income_amount: float,
        income_date: datetime | None = None,
        user_id: int | None = None,
    ) -> dict[str, Any]:
        if income_amount < 0:
            raise IntegrationError(
                "income_amount must be non-negative",
                status_code=400,
                error="invalid_input",
            )
        if milestone_type not in {"first_income", "monthly_update"}:
            raise IntegrationError(
                "milestone_type must be first_income or monthly_update",
                status_code=400,
                error="invalid_input",
            )

        commitment = UserSideIncomeCommitment.query.filter_by(id=commitment_id).first()
        if commitment is None:
            raise IntegrationError("Commitment not found", status_code=404, error="not_found")
        if user_id is not None and commitment.user_id != user_id:
            raise IntegrationError(
                "You do not have access to this commitment",
                status_code=403,
                error="forbidden",
            )

        recorded_at = income_date or datetime.utcnow()
        commitment.df1_monthly_income_actual = round(float(income_amount), 2)
        if milestone_type == "first_income":
            commitment.status = "income_earned"
            commitment.df1_first_income_date = recorded_at

        assessment = None
        if commitment.icc_assessment_id is not None:
            assessment = IndependenceCostAssessment.query.filter_by(
                id=commitment.icc_assessment_id
            ).first()

        original_timeline, new_timeline = _recalculate_timeline(assessment, income_amount)
        if original_timeline is not None and commitment.independence_timeline_original_months is None:
            commitment.independence_timeline_original_months = original_timeline
        if new_timeline is not None:
            commitment.independence_timeline_with_income_months = new_timeline

        commitment.updated_at = datetime.utcnow()
        db.session.commit()

        original = commitment.independence_timeline_original_months
        updated = commitment.independence_timeline_with_income_months
        acceleration = None
        if original is not None and updated is not None:
            acceleration = max(0, original - updated)

        return {
            "success": True,
            "commitment_id": str(commitment.id),
            "status": commitment.status,
            "actual_monthly_income": float(commitment.df1_monthly_income_actual or 0),
            "independence_timeline_original_months": original,
            "independence_timeline_with_income_months": updated,
            "timeline_acceleration_months": acceleration,
            "message": (
                f"Congrats! {commitment.selected_job} earning "
                f"${float(commitment.df1_monthly_income_actual or 0):,.0f}/month. "
                f"Timeline now {updated} months."
                if updated is not None
                else f"Updated income for {commitment.selected_job}."
            ),
        }
