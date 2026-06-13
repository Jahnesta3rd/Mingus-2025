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


def derive_career_risk(user_id: int) -> dict:
    """Derive career risk from profile/employer data and update hprs_scores."""
    try:
        career = CareerProfile.query.filter_by(user_id=user_id).first()
        if career is None:
            result = dict(_FALLBACK)
            _update_hprs_score_row(user_id, result)
            return result

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
            _update_hprs_score_row(user_id, result)
            return result

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
            _update_hprs_score_row(user_id, result)
            return result

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
            _update_hprs_score_row(user_id, result)
            return result

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
        _update_hprs_score_row(user_id, result)
        return result
    except Exception:
        db.session.rollback()
        result = dict(_FALLBACK)
        _update_hprs_score_row(user_id, result)
        return result
