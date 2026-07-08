#!/usr/bin/env python3
"""ICC side income accelerator — enrich DF1 recommendations for independence gap closure."""

from __future__ import annotations

import json
import logging
from typing import Any, Callable

from backend.models.career_profile import CareerProfile
from backend.models.user_models import User
from backend.models.user_profile import UserProfile
from backend.services.independence_cost_service import IndependenceCostCalculator

logger = logging.getLogger(__name__)

_ROOMMATE_RENT_SAVINGS = 300.0
_DEFAULT_JOB_TITLE = "Professional"


def _round2(value: float) -> float:
    return round(float(value), 2)


def _parse_json_object(raw: Any) -> dict[str, Any]:
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


def _relationship_exit_urgency(timeline_months: float) -> str:
    if timeline_months <= 6:
        return "high"
    if timeline_months <= 12:
        return "medium"
    return "low"


class SideIncomeAccelerator:
    """Wrap DF1 (Second Job Advisor) with ICC-specific impact enrichment."""

    def __init__(
        self,
        *,
        location_calculator: IndependenceCostCalculator | None = None,
        job_generator: Callable[[str], list[dict[str, Any]] | None] | None = None,
    ) -> None:
        self.location_calculator = location_calculator or IndependenceCostCalculator()
        self._job_generator = job_generator

    def extract_current_job(self, user_id: int) -> str:
        career = CareerProfile.query.filter_by(user_id=user_id).first()
        if career and career.current_role and str(career.current_role).strip():
            return str(career.current_role).strip()

        user = User.query.filter_by(id=user_id).first()
        if user and user.email:
            profile = UserProfile.query.filter_by(email=user.email).first()
            if profile:
                for source in (
                    _parse_json_object(profile.personal_info),
                    _parse_json_object(profile.goals),
                ):
                    for key in ("current_job", "currentJob", "job_title", "jobTitle"):
                        value = source.get(key)
                        if value and str(value).strip():
                            return str(value).strip()

        return _DEFAULT_JOB_TITLE

    def extract_skills_from_profile(self, user_id: int) -> str | None:
        skills: list[str] = []
        user = User.query.filter_by(id=user_id).first()
        if user and user.email:
            profile = UserProfile.query.filter_by(email=user.email).first()
            if profile:
                personal = _parse_json_object(profile.personal_info)
                raw_skills = personal.get("skills") or personal.get("skill_list")
                if isinstance(raw_skills, list):
                    skills.extend(str(s).strip() for s in raw_skills if str(s).strip())
                elif isinstance(raw_skills, str) and raw_skills.strip():
                    skills.extend(s.strip() for s in raw_skills.split(",") if s.strip())

        career = CareerProfile.query.filter_by(user_id=user_id).first()
        if career:
            for value in (career.industry, career.bls_career_field, career.occupation_key):
                if value and str(value).strip():
                    skills.append(str(value).strip())

        deduped: list[str] = []
        seen: set[str] = set()
        for skill in skills:
            key = skill.lower()
            if key not in seen:
                seen.add(key)
                deduped.append(skill)
        return ", ".join(deduped) if deduped else None

    def _fetch_df1_jobs(
        self,
        *,
        current_job: str,
        city: str | None,
        hours_per_week_available: int,
        skills: str | None,
    ) -> list[dict[str, Any]]:
        if self._job_generator is not None:
            from backend.routes.second_job_advisor import _build_user_prompt

            prompt = _build_user_prompt(
                current_job=current_job,
                city=city,
                free_hours_per_week=hours_per_week_available,
                schedule_preference="flexible",
                skills=skills,
                total_debt=None,
            )
            jobs = self._job_generator(prompt)
            if jobs is not None:
                return jobs
            raise RuntimeError("DF1 job generation failed")

        from backend.routes.second_job_advisor import _build_user_prompt, _generate_jobs

        prompt = _build_user_prompt(
            current_job=current_job,
            city=city,
            free_hours_per_week=hours_per_week_available,
            schedule_preference="flexible",
            skills=skills,
            total_debt=None,
        )
        jobs = _generate_jobs(prompt)
        if jobs is None:
            raise RuntimeError("DF1 job generation failed")
        return jobs

    def _enrich_job(
        self,
        job: dict[str, Any],
        *,
        monthly_gap: float,
        startup_cost_needed: float,
        timeline_months: float,
    ) -> dict[str, Any]:
        monthly_income = float(job.get("monthly_est") or 0)
        gap_coverage_pct = (
            _round2((monthly_income / monthly_gap) * 100) if monthly_gap > 0 else 0.0
        )
        closes_monthly_gap = gap_coverage_pct >= 100
        timeline_acceleration_months = (
            _round2(timeline_months - (startup_cost_needed / monthly_income))
            if monthly_income > 0
            else _round2(timeline_months)
        )

        roommate_rent_savings = _ROOMMATE_RENT_SAVINGS
        new_gap_with_roommate = _round2(
            max(0.0, monthly_gap - monthly_income - roommate_rent_savings)
        )
        combined_monthly = monthly_income + roommate_rent_savings
        months_to_startup_with_roommate = (
            _round2(startup_cost_needed / combined_monthly)
            if combined_monthly > 0
            else None
        )

        return {
            "title": job.get("title"),
            "type": job.get("type"),
            "hourly_range": job.get("hourly_range"),
            "hours_per_week": job.get("hours_per_week"),
            "monthly_income": _round2(monthly_income),
            "schedule_fit": job.get("schedule_fit"),
            "why_it_fits": job.get("why_it_fits"),
            "first_step": job.get("first_step"),
            "startup_cost": job.get("startup_cost"),
            "icc_impact": {
                "closes_monthly_gap": closes_monthly_gap,
                "gap_coverage_pct": gap_coverage_pct,
                "timeline_acceleration_months": timeline_acceleration_months,
            },
            "interim_housing_combo": {
                "roommate_rent_savings": roommate_rent_savings,
                "new_gap_with_roommate": new_gap_with_roommate,
                "months_to_startup_with_roommate": months_to_startup_with_roommate,
            },
        }

    def get_side_income_recommendations(
        self,
        user_id: int,
        monthly_gap: float,
        hours_per_week_available: int,
        startup_cost_needed: float,
        timeline_months: int,
    ) -> dict[str, Any]:
        if monthly_gap <= 0:
            raise ValueError("monthly_gap must be positive")

        current_job = self.extract_current_job(user_id)
        _zip_code, city_name = self.location_calculator.get_user_location(user_id)
        skills = self.extract_skills_from_profile(user_id)

        raw_jobs = self._fetch_df1_jobs(
            current_job=current_job,
            city=city_name,
            hours_per_week_available=hours_per_week_available,
            skills=skills,
        )
        if len(raw_jobs) != 3:
            logger.warning(
                "DF1 returned %s jobs for user_id=%s; expected 3",
                len(raw_jobs),
                user_id,
            )

        timeline = float(timeline_months)
        matches = [
            self._enrich_job(
                job,
                monthly_gap=monthly_gap,
                startup_cost_needed=float(startup_cost_needed),
                timeline_months=timeline,
            )
            for job in raw_jobs
        ]
        matches.sort(
            key=lambda item: item["icc_impact"]["gap_coverage_pct"],
            reverse=True,
        )

        urgency = _relationship_exit_urgency(timeline)
        return {
            "matches": matches,
            "recommendation": matches[0] if matches else None,
            "context": {
                "relationship_exit_urgency": urgency,
                "timeline_pressure": f"{int(timeline_months)}_months",
                "total_monthly_gap": _round2(monthly_gap),
                "startup_cost": _round2(float(startup_cost_needed)),
                "current_job": current_job,
                "city": city_name,
            },
        }
