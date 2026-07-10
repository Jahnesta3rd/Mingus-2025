#!/usr/bin/env python3
"""BTS7 — job commitment + DF1 earnings sync for Tier 2 budget."""

from __future__ import annotations

import logging
import uuid
from datetime import date, datetime
from decimal import Decimal, ROUND_HALF_UP
from typing import Any

from backend.models.bts import BackToSchoolSession
from backend.models.database import db
from backend.models.job_commitment import JobCommitment

logger = logging.getLogger(__name__)

# Align with BTS1 catalog (+ a couple extras for the picker UI).
JOB_CATALOG: list[dict[str, str]] = [
    {"id": "doordash", "title": "DoorDash"},
    {"id": "instacart", "title": "Instacart"},
    {"id": "rideshare", "title": "Rideshare"},
    {"id": "tutoring", "title": "After-School Tutor"},
    {"id": "uber", "title": "Uber Eats"},
    {"id": "taskrabbit", "title": "TaskRabbit"},
    {"id": "other", "title": "Other side job"},
]


def _money(value: Any) -> Decimal:
    return Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


class BTSJobIntegrationService:
    """Create commitments and sync side-job earnings into Tier 2 budget."""

    def create_commitment(
        self,
        *,
        session_id: str,
        user_id: str,
        job_id: str,
        job_title: str,
        tier2_date: date,
        tier2_base_budget: float | Decimal,
        target_earnings: float | Decimal,
    ) -> dict:
        if not session_id:
            raise ValueError("sessionId is required")
        if not user_id:
            raise ValueError("userId is required")
        if not job_id or not str(job_id).strip():
            raise ValueError("jobId is required")
        if not job_title or not str(job_title).strip():
            raise ValueError("jobTitle is required")
        if not isinstance(tier2_date, date):
            raise ValueError("tier2Date is required")

        base = _money(tier2_base_budget)
        target = _money(target_earnings)
        if target <= 0:
            raise ValueError("targetEarnings must be positive")
        if base < 0:
            raise ValueError("tier2BaseBudget must be non-negative")

        try:
            session_uuid = uuid.UUID(str(session_id))
        except (TypeError, ValueError) as exc:
            raise ValueError("Invalid sessionId") from exc

        session = BackToSchoolSession.query.filter_by(session_id=session_uuid).first()
        if not session:
            raise ValueError("BTS session not found")
        if session.user_id != str(user_id):
            raise ValueError("Session does not belong to this user")

        existing = JobCommitment.query.filter_by(session_id=session_uuid).first()
        if existing:
            # Update in place (one commitment per session)
            existing.job_id = str(job_id).strip()
            existing.job_title = str(job_title).strip()
            existing.tier2_date = tier2_date
            existing.tier2_base_budget = base
            existing.target_earnings = target
            existing.tier2_budget_with_earnings = _money(
                base + _money(existing.actual_earnings or 0)
            )
            existing.status = "active"
            existing.updated_at = datetime.utcnow()
            commitment = existing
        else:
            commitment = JobCommitment(
                session_id=session_uuid,
                user_id=str(user_id),
                job_id=str(job_id).strip(),
                job_title=str(job_title).strip(),
                tier2_date=tier2_date,
                tier2_base_budget=base,
                target_earnings=target,
                actual_earnings=Decimal("0.00"),
                tier2_budget_with_earnings=base,
                status="active",
            )
            db.session.add(commitment)

        self._sync_session_budget(session, commitment.tier2_budget_with_earnings)

        try:
            db.session.commit()
            return commitment.to_dict()
        except Exception as exc:
            db.session.rollback()
            logger.exception("Failed to create job commitment: %s", exc)
            raise ValueError(f"Failed to create commitment: {exc}") from exc

    def get_commitment(self, session_id: str, user_id: str | None = None) -> dict | None:
        try:
            session_uuid = uuid.UUID(str(session_id))
        except (TypeError, ValueError) as exc:
            raise ValueError("Invalid sessionId") from exc

        q = JobCommitment.query.filter_by(session_id=session_uuid)
        if user_id:
            q = q.filter_by(user_id=str(user_id))
        commitment = q.first()
        return commitment.to_dict() if commitment else None

    def _resolve_db_user_id(self, external_user_id: str) -> int | None:
        """Map JWT/external user id string → users.id integer for DF1 tables."""
        from backend.models.user_models import User

        user = User.query.filter_by(user_id=str(external_user_id)).first()
        if user:
            return int(user.id)
        if str(external_user_id).isdigit():
            by_pk = User.query.filter_by(id=int(external_user_id)).first()
            if by_pk:
                return int(by_pk.id)
        return None

    def fetch_df1_earnings(self, user_id: str, job_id: str) -> dict[str, Any]:
        """
        Pull earnings from DF1 (in-process).

        Source of truth: UserSideIncomeCommitment.df1_monthly_income_actual
        matched by job type / selected job title. Falls back to 0 when no
        DF1 commitment exists yet.
        """
        from backend.models.side_income_commitment import UserSideIncomeCommitment

        db_user_id = self._resolve_db_user_id(user_id)
        if db_user_id is None:
            return {
                "totalEarnings": 0.0,
                "lastUpdated": None,
                "source": "none",
                "message": "No DF1 user mapping found",
            }

        job_key = str(job_id or "").strip().lower()
        commitments = (
            UserSideIncomeCommitment.query.filter_by(user_id=db_user_id)
            .order_by(UserSideIncomeCommitment.updated_at.desc())
            .all()
        )

        matched = None
        for row in commitments:
            df1_type = (row.df1_job_type or "").strip().lower()
            selected = (row.selected_job or "").strip().lower()
            if job_key and (job_key == df1_type or job_key in selected or selected in job_key):
                matched = row
                break
        if matched is None and commitments:
            # Soft fallback: most recent DF1 commitment for this user
            matched = commitments[0]

        if matched is None:
            return {
                "totalEarnings": 0.0,
                "lastUpdated": None,
                "source": "none",
                "message": "No DF1 earnings recorded yet",
            }

        total = float(matched.df1_monthly_income_actual or 0)
        return {
            "totalEarnings": total,
            "lastUpdated": (
                matched.updated_at.isoformat() if matched.updated_at else None
            ),
            "source": "df1_commitment",
            "df1CommitmentId": str(matched.id),
        }

    def sync_earnings_from_df1(self, user_id: str, job_id: str) -> dict[str, Any]:
        """Pull DF1 earnings and update the active BTS commitment for this job."""
        try:
            earnings_data = self.fetch_df1_earnings(user_id, job_id)
            total_earnings = _money(earnings_data.get("totalEarnings", 0))

            commitment = (
                JobCommitment.query.filter_by(
                    user_id=str(user_id),
                    job_id=str(job_id),
                    status="active",
                )
                .order_by(JobCommitment.created_at.desc())
                .first()
            )
            if not commitment:
                return {"status": "no_commitment"}

            commitment.actual_earnings = total_earnings
            commitment.tier2_budget_with_earnings = _money(
                _money(commitment.tier2_base_budget) + total_earnings
            )
            commitment.last_sync_at = datetime.utcnow()
            commitment.updated_at = datetime.utcnow()

            if total_earnings >= _money(commitment.target_earnings):
                commitment.status = "complete"

            session = BackToSchoolSession.query.filter_by(
                session_id=commitment.session_id
            ).first()
            if session:
                self._sync_session_budget(
                    session, commitment.tier2_budget_with_earnings
                )

            db.session.commit()
            return {
                "status": "synced",
                "sessionId": str(commitment.session_id),
                "actualEarnings": float(total_earnings),
                "tier2BudgetWithEarnings": float(
                    commitment.tier2_budget_with_earnings
                ),
                "commitmentStatus": commitment.status,
                "df1": earnings_data,
            }
        except Exception as exc:
            db.session.rollback()
            logger.exception("DF1 earnings sync failed: %s", exc)
            return {"status": "error", "message": str(exc)}

    def _sync_session_budget(
        self, session: BackToSchoolSession, budget: Decimal | float
    ) -> None:
        """Denormalize boosted Tier 2 budget onto the BTS session when column exists."""
        if hasattr(session, "tier2_budget_with_earnings"):
            session.tier2_budget_with_earnings = _money(budget)

    def get_tier2_status(self, session_id: str, user_id: str | None = None) -> dict:
        commitment = self.get_commitment(session_id, user_id=user_id)
        if not commitment:
            return {
                "status": "no_commitment",
                "message": "No side job linked",
            }

        earnings = float(commitment["actualEarnings"])
        target = float(commitment["targetEarnings"])
        percent = min((earnings / target * 100) if target > 0 else 0.0, 100.0)
        tier2_date = commitment.get("tier2Date")
        today = date.today().isoformat()
        date_reached = bool(tier2_date and today >= tier2_date)

        return {
            "status": "ready" if date_reached else "tracking",
            "dateReached": date_reached,
            "jobTitle": commitment["jobTitle"],
            "jobId": commitment["jobId"],
            "targetEarnings": target,
            "actualEarnings": earnings,
            "progressPercent": round(percent, 1),
            "tier2BaseBudget": float(commitment["tier2BaseBudget"]),
            "tier2BudgetWithEarnings": float(commitment["tier2BudgetWithEarnings"]),
            "earningsGoalMet": earnings >= target,
            "tier2Date": tier2_date,
            "commitmentStatus": commitment["status"],
        }

    def record_decision(
        self, session_id: str, user_id: str, decision: str
    ) -> dict:
        """Record proceed / defer / skip for Tier 2 (MVP: status note only)."""
        decision_norm = str(decision or "").strip().lower()
        if decision_norm not in ("proceed", "defer", "skip"):
            raise ValueError("decision must be proceed, defer, or skip")

        commitment_dict = self.get_commitment(session_id, user_id=user_id)
        if not commitment_dict:
            raise ValueError("No side job linked for this session")

        session_uuid = uuid.UUID(str(session_id))
        commitment = JobCommitment.query.filter_by(session_id=session_uuid).first()
        if not commitment:
            raise ValueError("No side job linked for this session")

        if decision_norm == "skip":
            commitment.status = "complete"
        commitment.updated_at = datetime.utcnow()
        db.session.commit()

        return {
            "status": "ok",
            "decision": decision_norm,
            "commitment": commitment.to_dict(),
        }


bts_job_integration_service = BTSJobIntegrationService()
