#!/usr/bin/env python3
"""Vibe Tracker API: tracked people, linked checkup assessments, trends."""

from __future__ import annotations

import uuid
from datetime import datetime

from flask import Blueprint, g, jsonify, request
from sqlalchemy.exc import IntegrityError

from backend.auth.decorators import require_auth, require_csrf
from backend.middleware.limiter_ext import limiter
from backend.models.database import db
from backend.models.user_models import User
from backend.models.vibe_checkups import VibeCheckupsLead
from backend.models.vibe_tracker import (
    VibePersonAssessment,
    VibePersonTrend,
    VibeTrackedPerson,
)
from backend.services import vibe_tracker_service as vts
from backend.tasks.life_correlation_tasks import record_life_snapshot

vibe_tracker_bp = Blueprint("vibe_tracker", __name__)


def _user_for_jwt():
    ext = getattr(g, "current_user_id", None)
    if ext is None:
        return None
    return User.query.filter_by(user_id=str(ext)).first()


def _parse_json() -> dict:
    data = request.get_json(silent=True)
    return data if isinstance(data, dict) else {}


def _parse_uuid(value: str | None) -> uuid.UUID | None:
    if not value or not isinstance(value, str):
        return None
    try:
        return uuid.UUID(str(value).strip())
    except (ValueError, TypeError, AttributeError):
        return None


def _person_for_user(person_id: uuid.UUID, user: User) -> VibeTrackedPerson | None:
    p = db.session.get(VibeTrackedPerson, person_id)
    if not p or p.user_id != user.id:
        return None
    return p


def _trend_dict(t: VibePersonTrend | None) -> dict | None:
    if not t:
        return None
    return {
        "id": str(t.id),
        "tracked_person_id": str(t.tracked_person_id),
        "trend_direction": t.trend_direction,
        "emotional_delta": t.emotional_delta,
        "financial_delta": t.financial_delta,
        "projection_delta": t.projection_delta,
        "assessment_count": t.assessment_count,
        "last_computed_at": t.last_computed_at.isoformat() + "Z"
        if t.last_computed_at
        else None,
        "stay_or_go_signal": t.stay_or_go_signal,
        "stay_or_go_confidence": t.stay_or_go_confidence,
    }


def _assessment_summary(a: VibePersonAssessment) -> dict:
    return {
        "id": str(a.id),
        "emotional_score": a.emotional_score,
        "financial_score": a.financial_score,
        "verdict_label": a.verdict_label,
        "verdict_emoji": a.verdict_emoji,
        "annual_projection": a.annual_projection,
        "completed_at": a.completed_at.isoformat() + "Z" if a.completed_at else None,
    }


def _assessment_full(a: VibePersonAssessment) -> dict:
    d = _assessment_summary(a)
    d.update(
        {
            "lead_id": str(a.lead_id) if a.lead_id else None,
            "notes": a.notes,
            "answers_snapshot": a.answers_snapshot,
        }
    )
    return d


def _person_core(p: VibeTrackedPerson) -> dict:
    return {
        "id": str(p.id),
        "nickname": p.nickname,
        "emoji": p.emoji,
        "created_at": p.created_at.isoformat() + "Z" if p.created_at else None,
        "last_assessed_at": p.last_assessed_at.isoformat() + "Z"
        if p.last_assessed_at
        else None,
        "is_archived": p.is_archived,
        "archived_at": p.archived_at.isoformat() + "Z" if p.archived_at else None,
        "assessment_count": p.assessment_count,
    }


@vibe_tracker_bp.route("/people/archived", methods=["GET"])
@require_auth
def list_archived_people():
    user = _user_for_jwt()
    if not user:
        return jsonify({"error": "User not found"}), 404

    rows = (
        VibeTrackedPerson.query.filter_by(user_id=user.id, is_archived=True)
        .order_by(*vts.list_people_order_clause())
        .all()
    )
    out = []
    for p in rows:
        tr = VibePersonTrend.query.filter_by(tracked_person_id=p.id).first()
        latest = vts.latest_assessment_for_person(p.id)
        item = _person_core(p)
        item["trend"] = _trend_dict(tr)
        item["latest_assessment"] = _assessment_summary(latest) if latest else None
        out.append(item)
    return jsonify({"people": out})


@vibe_tracker_bp.route("/people", methods=["GET"])
@require_auth
def list_people():
    user = _user_for_jwt()
    if not user:
        return jsonify({"error": "User not found"}), 404

    rows = (
        VibeTrackedPerson.query.filter_by(user_id=user.id, is_archived=False)
        .order_by(*vts.list_people_order_clause())
        .all()
    )
    out = []
    for p in rows:
        tr = VibePersonTrend.query.filter_by(tracked_person_id=p.id).first()
        latest = vts.latest_assessment_for_person(p.id)
        item = _person_core(p)
        item["trend"] = _trend_dict(tr)
        item["latest_assessment"] = _assessment_summary(latest) if latest else None
        out.append(item)
    return jsonify({"people": out})


@vibe_tracker_bp.route("/people", methods=["POST"])
@require_auth
@require_csrf
@limiter.limit("10 per minute")
def create_person():
    user = _user_for_jwt()
    if not user:
        return jsonify({"error": "User not found"}), 404

    if not vts.check_person_limit(user.id, user.tier):
        return jsonify({"error": "Vibe Tracker limit reached for your tier"}), 403

    body = _parse_json()
    nickname = body.get("nickname")
    if not isinstance(nickname, str):
        return jsonify({"error": "nickname is required (string)"}), 400
    nickname = nickname.strip()
    if len(nickname) < 1 or len(nickname) > 30:
        return jsonify({"error": "nickname must be 1–30 characters"}), 400

    emoji = body.get("emoji")
    if emoji is not None:
        if not isinstance(emoji, str):
            return jsonify({"error": "emoji must be a string"}), 400
        emoji = emoji.strip()[:8] or None
    else:
        emoji = None

    person = VibeTrackedPerson(
        user_id=user.id,
        nickname=nickname,
        emoji=emoji,
    )
    db.session.add(person)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "A tracked person with this nickname already exists"}), 409

    return jsonify(_person_core(person)), 201


@vibe_tracker_bp.route("/people/<uuid:person_id>", methods=["GET"])
@require_auth
def get_person(person_id: uuid.UUID):
    user = _user_for_jwt()
    if not user:
        return jsonify({"error": "User not found"}), 404

    p = _person_for_user(person_id, user)
    if not p:
        return jsonify({"error": "Not found"}), 404

    assessments = (
        VibePersonAssessment.query.filter_by(tracked_person_id=p.id)
        .order_by(
            VibePersonAssessment.completed_at.asc(),
            VibePersonAssessment.id.asc(),
        )
        .all()
    )
    tr = VibePersonTrend.query.filter_by(tracked_person_id=p.id).first()
    payload = _person_core(p)
    payload["assessments"] = [_assessment_full(a) for a in assessments]
    payload["trend"] = _trend_dict(tr)
    return jsonify(payload)


@vibe_tracker_bp.route("/people/<uuid:person_id>", methods=["PATCH"])
@require_auth
@require_csrf
def patch_person(person_id: uuid.UUID):
    user = _user_for_jwt()
    if not user:
        return jsonify({"error": "User not found"}), 404

    p = _person_for_user(person_id, user)
    if not p:
        return jsonify({"error": "Not found"}), 404

    body = _parse_json()
    if "nickname" in body:
        nick = body.get("nickname")
        if not isinstance(nick, str):
            return jsonify({"error": "nickname must be a string"}), 400
        nick = nick.strip()
        if len(nick) < 1 or len(nick) > 30:
            return jsonify({"error": "nickname must be 1–30 characters"}), 400
        p.nickname = nick
    if "emoji" in body:
        em = body.get("emoji")
        if em is None:
            p.emoji = None
        elif isinstance(em, str):
            em = em.strip()[:8] or None
            p.emoji = em
        else:
            return jsonify({"error": "emoji must be a string or null"}), 400

    if "nickname" not in body and "emoji" not in body:
        return jsonify({"error": "Provide nickname and/or emoji"}), 400

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "A tracked person with this nickname already exists"}), 409

    return jsonify(_person_core(p))


@vibe_tracker_bp.route(
    "/people/<uuid:person_id>/assessment/<uuid:assessment_id>/note",
    methods=["PATCH"],
)
@require_auth
@require_csrf
def patch_assessment_note(person_id: uuid.UUID, assessment_id: uuid.UUID):
    user = _user_for_jwt()
    if not user:
        return jsonify({"error": "User not found"}), 404

    p = _person_for_user(person_id, user)
    if not p:
        return jsonify({"error": "Not found"}), 404

    a = db.session.get(VibePersonAssessment, assessment_id)
    if not a or a.tracked_person_id != p.id:
        return jsonify({"error": "Assessment not found"}), 404

    body = _parse_json()
    if "note" in body:
        note = body["note"]
    elif "notes" in body:
        note = body["notes"]
    else:
        return jsonify({"error": "Provide note or notes"}), 400
    if note is not None and not isinstance(note, str):
        return jsonify({"error": "note must be a string"}), 400
    a.notes = note
    db.session.commit()
    return jsonify(_assessment_full(a))


@vibe_tracker_bp.route("/people/<uuid:person_id>/assessment", methods=["POST"])
@require_auth
@require_csrf
def add_assessment(person_id: uuid.UUID):
    user = _user_for_jwt()
    if not user:
        return jsonify({"error": "User not found"}), 404

    p = _person_for_user(person_id, user)
    if not p:
        return jsonify({"error": "Not found"}), 404

    body = _parse_json()
    lead_id_raw = body.get("lead_id")
    if not lead_id_raw or not isinstance(lead_id_raw, str):
        return jsonify({"error": "lead_id is required (string)"}), 400
    lid = _parse_uuid(lead_id_raw)
    if not lid:
        return jsonify({"error": "Invalid lead_id"}), 400

    lead = db.session.get(VibeCheckupsLead, lid)
    if not lead:
        return jsonify({"error": "Lead not found"}), 404

    if (lead.email or "").strip().lower() != (user.email or "").strip().lower():
        return jsonify({"error": "Lead does not belong to this account"}), 403

    notes = body.get("notes")
    if notes is not None and not isinstance(notes, str):
        return jsonify({"error": "notes must be a string"}), 400

    row = vts.assessment_from_lead(lead)
    row.tracked_person_id = p.id
    if notes is not None:
        row.notes = notes

    db.session.add(row)
    p.assessment_count = (p.assessment_count or 0) + 1
    p.last_assessed_at = row.completed_at

    db.session.flush()
    trend = vts.compute_trend(p.id)
    db.session.flush()

    payload = _person_core(p)
    payload["trend"] = _trend_dict(trend)
    payload["latest_assessment"] = _assessment_summary(row)
    db.session.commit()
    record_life_snapshot.delay(str(user.id), "vibe_assessment")
    return jsonify(payload), 201


@vibe_tracker_bp.route("/people/<uuid:person_id>/archive", methods=["POST"])
@require_auth
@require_csrf
def archive_person(person_id: uuid.UUID):
    user = _user_for_jwt()
    if not user:
        return jsonify({"error": "User not found"}), 404

    p = _person_for_user(person_id, user)
    if not p:
        return jsonify({"error": "Not found"}), 404

    now = datetime.utcnow()
    p.is_archived = True
    p.archived_at = now
    db.session.commit()
    out = _person_core(p)
    tr = VibePersonTrend.query.filter_by(tracked_person_id=p.id).first()
    latest = vts.latest_assessment_for_person(p.id)
    out["trend"] = _trend_dict(tr)
    out["latest_assessment"] = _assessment_summary(latest) if latest else None
    return jsonify(out)


@vibe_tracker_bp.route("/people/<uuid:person_id>/unarchive", methods=["POST"])
@require_auth
@require_csrf
def unarchive_person(person_id: uuid.UUID):
    user = _user_for_jwt()
    if not user:
        return jsonify({"error": "User not found"}), 404

    p = _person_for_user(person_id, user)
    if not p:
        return jsonify({"error": "Not found"}), 404

    if not p.is_archived:
        return jsonify({"error": "Person is not archived"}), 400

    p.is_archived = False
    p.archived_at = None
    db.session.commit()
    out = _person_core(p)
    tr = VibePersonTrend.query.filter_by(tracked_person_id=p.id).first()
    latest = vts.latest_assessment_for_person(p.id)
    out["trend"] = _trend_dict(tr)
    out["latest_assessment"] = _assessment_summary(latest) if latest else None
    return jsonify(out)


@vibe_tracker_bp.route("/people/<uuid:person_id>", methods=["DELETE"])
@require_auth
@require_csrf
def delete_person(person_id: uuid.UUID):
    user = _user_for_jwt()
    if not user:
        return jsonify({"error": "User not found"}), 404

    p = _person_for_user(person_id, user)
    if not p:
        return jsonify({"error": "Not found"}), 404

    body = _parse_json()
    if body.get("confirm") != "DELETE":
        return jsonify({"error": 'Request body must include {"confirm": "DELETE"}'}), 400

    db.session.delete(p)
    db.session.commit()
    return "", 204
