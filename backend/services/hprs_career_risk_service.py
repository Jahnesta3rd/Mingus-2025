#!/usr/bin/env python3
"""Career risk derivation for HPRS from career profile and CR9 employer health data."""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any

from backend.models.career_profile import CareerProfile
from backend.models.database import db
from backend.models.employer import Employer, LayoffEvent
from backend.models.hprs_score import HprsScore
from backend.services.employer_health_scoring import get_latest_snapshot

_BAND_MODIFIERS = {
    "LOW": 0,
    "MODERATE": -3,
    "HIGH": -7,
    "CRITICAL": -15,
}

_FALLBACK = {
    "career_risk_score": 30,
    "career_risk_band": "LOW",
    "career_modifier": 0,
    "active_layoff": False,
    "data_source": "unresolved",
    "employer_health_score": None,
}


def _pad_cik(cik: str) -> str:
    return str(cik).strip().zfill(10)


def _modifier_for_band(band: str) -> int:
    return _BAND_MODIFIERS.get(band, 0)


def _band_from_score(score: int) -> str:
    score = max(0, min(100, int(score)))
    if score <= 24:
        return "LOW"
    if score <= 49:
        return "MODERATE"
    if score <= 74:
        return "HIGH"
    return "CRITICAL"


def _commitment_pipeline_context(user_id: int, db_session) -> tuple[str | None, int, int]:
    from backend.models.career_commitment_profile import CareerCommitmentProfile

    commitment_profile = (
        db_session.query(CareerCommitmentProfile).filter_by(user_id=user_id).first()
    )
    commitment_type = commitment_profile.commitment_type if commitment_profile else None
    skill_freq = commitment_profile.skill_development_frequency if commitment_profile else 0

    pipeline_credit = 0
    if commitment_type in ("type_2", "type_3") and (skill_freq or 0) >= 4:
        pipeline_credit = 4

    return commitment_type, skill_freq or 0, pipeline_credit


def get_commitment_pipeline_context(user_id: int, db_session) -> dict[str, int | str | None]:
    from backend.services.career_commitment_service import get_classification_rationale

    commitment_type, _skill_freq, pipeline_credit = _commitment_pipeline_context(
        user_id,
        db_session,
    )
    row = db_session.query(HprsScore).filter_by(user_id=user_id).first()
    return {
        "commitment_type": commitment_type,
        "pipeline_credit": pipeline_credit,
        "classification_rationale": get_classification_rationale(commitment_type),
        "career_risk_band": row.career_risk_band if row else None,
    }


def apply_pipeline_credit(result: dict[str, Any], user_id: int, db_session) -> dict[str, Any]:
    """Apply commitment pipeline credit and attach commitment context to a career risk result."""
    updated = dict(result)
    career_risk_score = max(0, min(100, int(updated["career_risk_score"])))

    commitment_type, _skill_freq, pipeline_credit = _commitment_pipeline_context(
        user_id,
        db_session,
    )

    if pipeline_credit > 0:
        career_risk_score = max(0, career_risk_score - pipeline_credit)
        band = _band_from_score(career_risk_score)
        updated["career_risk_band"] = band
        updated["career_modifier"] = _modifier_for_band(band)

    updated["career_risk_score"] = career_risk_score
    updated["pipeline_credit"] = pipeline_credit
    updated["commitment_type"] = commitment_type
    return updated


def _health_score_int(snapshot_score: Any) -> int | None:
    if snapshot_score is None:
        return None
    try:
        return int(round(float(snapshot_score)))
    except (TypeError, ValueError):
        return None


def _has_active_layoff(employer_id: int) -> bool:
    cutoff = date.today() - timedelta(days=90)
    return (
        db.session.query(LayoffEvent.id)
        .filter(
            LayoffEvent.employer_id == employer_id,
            LayoffEvent.filing_date >= cutoff,
            LayoffEvent.review_state != "rejected",
        )
        .first()
        is not None
    )


def _derive_from_employer_type(employer_type: str | None) -> tuple[int, str, str]:
    et = (employer_type or "").strip().lower()
    if et == "federal":
        return 5, "LOW", "employer_type_fallback"
    if et in {"state_local", "nonprofit"}:
        return 20, "LOW", "employer_type_fallback"
    if et in {"self_employed", "1099"}:
        return 45, "MODERATE", "employer_type_fallback"
    return 30, "LOW", "unresolved"


def _derive_from_health(
    health_score: int,
    active_layoff: bool,
    snapshot_data_source: str | None,
) -> tuple[int, str, str]:
    if active_layoff:
        return 90, "CRITICAL", "8k_filing"
    if health_score >= 70:
        return 10, "LOW", snapshot_data_source or "sec_edgar"
    if health_score >= 50:
        return 30, "MODERATE", snapshot_data_source or "sec_edgar"
    if health_score >= 30:
        return 60, "HIGH", snapshot_data_source or "sec_edgar"
    return 80, "HIGH", snapshot_data_source or "sec_edgar"


def _update_hprs_score_row(user_id: int, result: dict[str, Any]) -> None:
    row = HprsScore.query.filter_by(user_id=user_id).first()
    if row is None:
        return

    vehicle_modifier = int(row.vehicle_modifier or 0)
    career_modifier = int(result["career_modifier"])
    combined_modifier = career_modifier + vehicle_modifier
    adjusted_overall = max(
        0,
        min(100, int(row.overall_score) + career_modifier + vehicle_modifier),
    )

    row.career_risk_score = result["career_risk_score"]
    row.career_risk_band = result["career_risk_band"]
    row.career_modifier = career_modifier
    row.combined_modifier = combined_modifier
    row.overall_score = adjusted_overall
    db.session.commit()


def _finalize_career_risk(user_id: int, result: dict[str, Any]) -> dict[str, Any]:
    finalized = apply_pipeline_credit(result, user_id, db.session)
    _update_hprs_score_row(user_id, finalized)
    return finalized


def derive_career_risk(user_id: int) -> dict:
    """Derive career risk from profile/employer data and update hprs_scores."""
    try:
        career = CareerProfile.query.filter_by(user_id=user_id).first()
        if career is None:
            return _finalize_career_risk(user_id, dict(_FALLBACK))

        employer_cik = (career.employer_cik or "").strip()
        employer_type = career.employer_type

        if not employer_cik:
            score, band, data_source = _derive_from_employer_type(employer_type)
            result = {
                "career_risk_score": score,
                "career_risk_band": band,
                "career_modifier": _modifier_for_band(band),
                "active_layoff": False,
                "data_source": data_source,
                "employer_health_score": None,
            }
            return _finalize_career_risk(user_id, result)

        cik_padded = _pad_cik(employer_cik)
        employer = db.session.query(Employer).filter_by(cik=cik_padded).first()
        if employer is None:
            score, band, data_source = _derive_from_employer_type(employer_type)
            result = {
                "career_risk_score": score,
                "career_risk_band": band,
                "career_modifier": _modifier_for_band(band),
                "active_layoff": False,
                "data_source": data_source,
                "employer_health_score": None,
            }
            return _finalize_career_risk(user_id, result)

        active_layoff = _has_active_layoff(employer.id)
        snapshot = get_latest_snapshot(employer.id, db_session=db.session)
        health_score = _health_score_int(snapshot.score if snapshot else None)

        if health_score is None and not active_layoff:
            score, band, data_source = _derive_from_employer_type(employer_type)
            result = {
                "career_risk_score": score,
                "career_risk_band": band,
                "career_modifier": _modifier_for_band(band),
                "active_layoff": False,
                "data_source": data_source,
                "employer_health_score": None,
            }
            return _finalize_career_risk(user_id, result)

        snapshot_source = snapshot.data_source if snapshot else None
        if health_score is None and active_layoff:
            score, band, data_source = 90, "CRITICAL", "8k_filing"
        else:
            score, band, data_source = _derive_from_health(
                health_score or 0,
                active_layoff,
                snapshot_source,
            )

        result = {
            "career_risk_score": score,
            "career_risk_band": band,
            "career_modifier": _modifier_for_band(band),
            "active_layoff": active_layoff,
            "data_source": data_source,
            "employer_health_score": health_score,
        }
        return _finalize_career_risk(user_id, result)
    except Exception:
        db.session.rollback()
        return _finalize_career_risk(user_id, dict(_FALLBACK))


def compute_career_risk_for_hprs(user_id: int) -> dict:
    """Derive career risk with commitment pipeline credit for HPRS."""
    return derive_career_risk(user_id)
