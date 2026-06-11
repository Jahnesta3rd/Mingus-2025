#!/usr/bin/env python3
"""Employer health API — CIK search, health scores, snapshot history (CR9c)."""

from __future__ import annotations

import logging
import time
from datetime import date, datetime

from flask import Blueprint, g, jsonify, request
from flask_cors import cross_origin

from backend.auth.decorators import require_auth
from backend.models.database import db
from backend.models.employer import Employer, EmployerHealthSnapshot, LayoffEvent
from backend.services.employer_health_scoring import (
    get_latest_snapshot,
    get_multiplier,
    refresh_employer_health,
)
from backend.services.sec_edgar_client import SecEdgarClient

logger = logging.getLogger(__name__)

employer_health_api = Blueprint("employer_health_api", __name__)

_SEARCH_CACHE_TTL = 3600
_search_cache: dict[str, tuple[float, list[dict]]] = {}

LAYOFF_MULTIPLIER = 1.60


def _pad_cik(cik: str) -> str:
    return str(cik).strip().zfill(10)


def _float_or_none(value) -> float | None:
    if value is None:
        return None
    return float(value)


def _iso_date(value: date | None) -> str | None:
    if value is None:
        return None
    return value.isoformat()


def _iso_datetime(value: datetime | None) -> str | None:
    if value is None:
        return None
    return value.isoformat()


def _components_from_snapshot(snapshot: EmployerHealthSnapshot | None) -> dict | None:
    if snapshot is None:
        return None
    return {
        "revenue_delta": _float_or_none(snapshot.revenue_delta_score),
        "margin": _float_or_none(snapshot.margin_score),
        "fcf": _float_or_none(snapshot.fcf_score),
        "runway": _float_or_none(snapshot.runway_score),
        "leverage": _float_or_none(snapshot.leverage_score),
    }


def _active_layoff_event(employer_id: int) -> LayoffEvent | None:
    today = date.today()
    return (
        db.session.query(LayoffEvent)
        .filter(
            LayoffEvent.employer_id == employer_id,
            LayoffEvent.expires_at >= today,
            LayoffEvent.review_state != "rejected",
        )
        .order_by(LayoffEvent.filing_date.desc())
        .first()
    )


def _history_entry(snapshot: EmployerHealthSnapshot) -> dict:
    return {
        "score": _float_or_none(snapshot.score),
        "components": _components_from_snapshot(snapshot),
        "fiscal_period_end": _iso_date(snapshot.fiscal_period_end),
        "refreshed_at": _iso_datetime(snapshot.refreshed_at),
        "is_stale": bool(snapshot.is_stale),
    }


@employer_health_api.route("/api/employer/search", methods=["GET", "OPTIONS"])
@cross_origin()
def employer_search():
    """Public CIK typeahead for employer name search."""
    if request.method == "OPTIONS":
        return jsonify({}), 200

    query = (request.args.get("q") or "").strip()
    if len(query) < 2:
        return jsonify({"results": []}), 200

    cache_key = query.lower()
    cached = _search_cache.get(cache_key)
    now = time.monotonic()
    if cached and (now - cached[0]) < _SEARCH_CACHE_TTL:
        return jsonify({"results": cached[1]}), 200

    try:
        client = SecEdgarClient()
        results = client.resolve_cik(query)
        if results:
            _search_cache[cache_key] = (now, results)
        return jsonify({"results": results}), 200
    except Exception as exc:
        logger.warning("employer search failed for %r: %s", query, exc)
        return jsonify({"results": []}), 200


@employer_health_api.route("/api/career-risk/employer/<cik>", methods=["GET", "OPTIONS"])
@cross_origin()
@require_auth
def career_risk_employer(cik):
    """Authenticated employer health score and career risk multiplier."""
    if request.method == "OPTIONS":
        return jsonify({}), 200

    cik_padded = _pad_cik(cik)
    employer = db.session.query(Employer).filter_by(cik=cik_padded).first()
    if employer is None:
        refresh_employer_health(cik_padded, db_session=db.session)
        employer = db.session.query(Employer).filter_by(cik=cik_padded).first()

    if employer is None:
        return jsonify(
            {
                "cik": cik_padded,
                "name": None,
                "ticker": None,
                "health_score": None,
                "multiplier": 1.0,
                "data_source": "user_reported",
                "components": None,
                "fiscal_period_end": None,
                "refreshed_at": None,
                "is_stale": True,
                "recent_layoff_event": None,
            }
        ), 200

    snapshot = get_latest_snapshot(employer.id, db_session=db.session)
    layoff = _active_layoff_event(employer.id)

    if layoff is not None:
        multiplier = LAYOFF_MULTIPLIER
        data_source = "8k_filing"
    elif snapshot is not None and not snapshot.is_stale:
        multiplier = get_multiplier(_float_or_none(snapshot.score))
        data_source = "sec_edgar"
    else:
        multiplier = 1.0
        data_source = "user_reported"

    layoff_payload = None
    if layoff is not None:
        layoff_payload = {
            "filing_date": _iso_date(layoff.filing_date),
            "confidence": _float_or_none(layoff.confidence),
            "affected_count": layoff.affected_count,
            "expires_at": _iso_date(layoff.expires_at),
        }

    return jsonify(
        {
            "cik": employer.cik,
            "name": employer.name,
            "ticker": employer.ticker,
            "health_score": _float_or_none(snapshot.score) if snapshot else None,
            "multiplier": multiplier,
            "data_source": data_source,
            "components": _components_from_snapshot(snapshot),
            "fiscal_period_end": _iso_date(snapshot.fiscal_period_end) if snapshot else None,
            "refreshed_at": _iso_datetime(snapshot.refreshed_at) if snapshot else None,
            "is_stale": bool(snapshot.is_stale) if snapshot else True,
            "recent_layoff_event": layoff_payload,
        }
    ), 200


@employer_health_api.route("/api/employer/<cik>/history", methods=["GET", "OPTIONS"])
@cross_origin()
@require_auth
def employer_history(cik):
    """Authenticated employer health snapshot history (last 8)."""
    if request.method == "OPTIONS":
        return jsonify({}), 200

    cik_padded = _pad_cik(cik)
    employer = db.session.query(Employer).filter_by(cik=cik_padded).first()

    if employer is None:
        return jsonify({"cik": cik_padded, "name": None, "history": []}), 200

    snapshots = (
        db.session.query(EmployerHealthSnapshot)
        .filter_by(employer_id=employer.id)
        .order_by(EmployerHealthSnapshot.refreshed_at.desc())
        .limit(8)
        .all()
    )

    return jsonify(
        {
            "cik": employer.cik,
            "name": employer.name,
            "history": [_history_entry(s) for s in snapshots],
        }
    ), 200
