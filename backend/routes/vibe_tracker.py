#!/usr/bin/env python3
"""Vibe Tracker API: tracked people, linked checkup assessments, trends."""

from __future__ import annotations

import calendar
import uuid
from datetime import date, datetime, timedelta

from flask import Blueprint, g, jsonify, request
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError

from backend.auth.decorators import require_auth, require_csrf
from backend.middleware.limiter_ext import limiter
from backend.models.connection_trend import ConnectionTrendAssessment
from backend.models.database import db
from backend.models.user_models import User
from backend.models.vibe_checkups import VibeCheckupsLead
from backend.models.vibe_tracker import (
    VibePersonAssessment,
    VibePersonTrend,
    VibeTrackedPerson,
)
from backend.services import vibe_tracker_service as vts
from backend.services.connection_trend_service import compute_fade_tier
from backend.services.cash_forecast_service import (
    _load_profile_balance_and_dates,
    generate_daily_forecast,
)
from backend.tasks.life_correlation_tasks import record_life_snapshot
from backend.tasks.vibe_financial_alert_tasks import check_for_alerts

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


def _latest_archived_connection_trend_for_nickname(
    user_id: int, nickname: str
) -> ConnectionTrendAssessment | None:
    """
    Most recent Connection Trend row for this user and nickname (case-insensitive)
    on an archived roster person. Rows tied to deleted people are CASCADE-deleted,
    so true post-delete re-entry cannot be detected without additional storage.
    """
    nick_lower = nickname.strip().lower()
    if not nick_lower:
        return None
    return (
        ConnectionTrendAssessment.query.join(
            VibeTrackedPerson,
            ConnectionTrendAssessment.person_id == VibeTrackedPerson.id,
        )
        .filter(
            ConnectionTrendAssessment.user_id == user_id,
            func.lower(VibeTrackedPerson.nickname) == nick_lower,
            VibeTrackedPerson.is_archived.is_(True),
        )
        .order_by(ConnectionTrendAssessment.assessed_at.desc())
        .first()
    )


def _person_core(p: VibeTrackedPerson) -> dict:
    return {
        "id": str(p.id),
        "nickname": p.nickname,
        "card_type": getattr(p, "card_type", None) or "person",
        "emoji": p.emoji,
        "created_at": p.created_at.isoformat() + "Z" if p.created_at else None,
        "last_assessed_at": p.last_assessed_at.isoformat() + "Z"
        if p.last_assessed_at
        else None,
        "is_archived": p.is_archived,
        "archived_at": p.archived_at.isoformat() + "Z" if p.archived_at else None,
        "assessment_count": p.assessment_count,
    }


def _nick_from_event_node(node: object) -> str:
    if not isinstance(node, dict):
        return ""
    raw = node.get("person_nickname")
    if raw is None:
        raw = node.get("personNickname")
    if raw is None:
        return ""
    return str(raw).strip()


def _format_label_key(key: str) -> str:
    return " ".join(w[:1].upper() + w[1:].lower() for w in key.split("_") if w)


def _next_birthday_occurrence(birthday_iso: str, today: date) -> date | None:
    s = (birthday_iso or "").strip()[:10]
    if len(s) < 10:
        return None
    try:
        _y, m_str, d_str = s.split("-")
        m, d = int(m_str), int(d_str)
    except (ValueError, AttributeError):
        return None
    try:
        cand = date(today.year, m, d)
    except ValueError:
        last = calendar.monthrange(today.year, m)[1]
        cand = date(today.year, m, min(d, last))
    if cand < today:
        try:
            cand = date(today.year + 1, m, d)
        except ValueError:
            last = calendar.monthrange(today.year + 1, m)[1]
            cand = date(today.year + 1, m, min(d, last))
    return cand


def _get_nested_important(obj: dict, *keys: str) -> object | None:
    for k in keys:
        if k in obj:
            return obj[k]
    return None


def _iter_normalized_important_events(important: dict) -> list[dict]:
    """Flatten important_dates into {name, date, cost, person_nickname, emoji}."""
    out: list[dict] = []
    today = date.today()

    bd_raw = important.get("birthday")
    bd_nick = important.get("birthday_person_nickname") or important.get(
        "birthdayPersonNickname"
    )
    if isinstance(bd_nick, str):
        bd_nick = bd_nick.strip()
    else:
        bd_nick = ""
    if bd_raw:
        if isinstance(bd_raw, dict):
            ds = str(bd_raw.get("date") or bd_raw.get("birthday") or "")[:10]
            if not bd_nick:
                bd_nick = _nick_from_event_node(bd_raw)
        else:
            ds = str(bd_raw).strip()[:10]
        if len(ds) >= 10:
            nxt = _next_birthday_occurrence(ds, today)
            if nxt:
                out.append(
                    {
                        "name": "Birthday",
                        "date": nxt.isoformat(),
                        "cost": 0.0,
                        "person_nickname": bd_nick,
                        "emoji": "🎂",
                    }
                )

    pairs = [
        ("plannedVacation", "vacation", "Vacation", "✈️"),
        ("carInspection", "car_inspection", "car_inspection", "🚗"),
        ("sistersWedding", "sisters_wedding", "sisters_wedding", "💍"),
    ]
    for a, b, label_key, emo in pairs:
        node = _get_nested_important(important, a, b)
        if not isinstance(node, dict):
            continue
        raw_d = node.get("date") or node.get("Date")
        if not raw_d:
            continue
        ds = str(raw_d)[:10]
        try:
            evd = date.fromisoformat(ds)
        except ValueError:
            continue
        c = node.get("cost", node.get("Cost", 0))
        try:
            cost = float(c)
        except (TypeError, ValueError):
            cost = 0.0
        name = _format_label_key(label_key) if "_" in label_key else label_key
        out.append(
            {
                "name": name,
                "date": evd.isoformat(),
                "cost": cost,
                "person_nickname": _nick_from_event_node(node),
                "emoji": emo,
            }
        )

    customs = important.get("customEvents") or important.get("custom_events")
    if isinstance(customs, list):
        for item in customs:
            if not isinstance(item, dict):
                continue
            raw_d = item.get("date") or item.get("Date")
            if not raw_d:
                continue
            ds = str(raw_d)[:10]
            try:
                evd = date.fromisoformat(ds)
            except ValueError:
                continue
            c = item.get("cost", item.get("Cost", 0))
            try:
                cost = float(c)
            except (TypeError, ValueError):
                cost = 0.0
            nm = item.get("name") or item.get("Name") or "Event"
            nm = str(nm).strip() or "Event"
            title = nm[:1].upper() + nm[1:] if nm else "Event"
            out.append(
                {
                    "name": title,
                    "date": evd.isoformat(),
                    "cost": cost,
                    "person_nickname": _nick_from_event_node(item),
                    "emoji": "📅",
                }
            )

    return out


def _coverage_from_daily(
    daily: list[dict], event_date: str, cost: float
) -> tuple[float | None, str | None]:
    if cost == 0:
        return None, None
    row = next((r for r in daily if r.get("date") == event_date), None)
    if not row:
        return None, None
    try:
        closing = float(row.get("closing_balance", 0))
    except (TypeError, ValueError):
        return None, None
    after = closing - cost
    if after > 500:
        return round(after, 2), "covered"
    if after >= 0:
        return round(after, 2), "tight"
    return round(after, 2), "shortfall"


@vibe_tracker_bp.route("/people/<uuid:person_id>/events", methods=["GET"])
@require_auth
def list_person_linked_events(person_id: uuid.UUID):
    user = _user_for_jwt()
    if not user:
        return jsonify({"error": "User not found"}), 404

    p = _person_for_user(person_id, user)
    if not p:
        return jsonify({"error": "Not found"}), 404

    email = (user.email or "").strip().lower()
    _bal, important = _load_profile_balance_and_dates(email)
    if not isinstance(important, dict):
        important = {}

    nick = (p.nickname or "").strip()
    today = date.today()
    horizon_end = today + timedelta(days=30)

    raw_events = _iter_normalized_important_events(important)
    linked = []
    for ev in raw_events:
        pn = (ev.get("person_nickname") or "").strip()
        if not nick or pn != nick:
            continue
        try:
            evd = date.fromisoformat(str(ev["date"])[:10])
        except ValueError:
            continue
        if evd < today:
            continue
        linked.append(ev)

    linked.sort(key=lambda x: x["date"])

    thirty_day_total = 0.0
    for ev in linked:
        try:
            evd = date.fromisoformat(str(ev["date"])[:10])
        except ValueError:
            continue
        if evd <= horizon_end:
            thirty_day_total += float(ev.get("cost") or 0)

    forecast_days = 90
    if linked:
        last_ev = max(date.fromisoformat(str(x["date"])[:10]) for x in linked)
        span = (last_ev - today).days + 1
        forecast_days = min(366, max(90, span))

    daily = generate_daily_forecast(user.id, days=forecast_days)

    payload_events = []
    for ev in linked:
        ds = str(ev["date"])[:10]
        cost = float(ev.get("cost") or 0)
        try:
            evd = date.fromisoformat(ds)
        except ValueError:
            continue
        days_until = (evd - today).days
        after_event, coverage_status = _coverage_from_daily(daily, ds, cost)
        payload_events.append(
            {
                "name": ev["name"],
                "date": ds,
                "cost": cost,
                "emoji": ev.get("emoji") or "📅",
                "days_until": days_until,
                "after_event": after_event,
                "coverage_status": coverage_status,
            }
        )

    tier = (user.tier or "budget").strip().lower()
    if tier == "budget":
        payload_events = payload_events[:2]
        thirty_day_total = sum(float(e["cost"]) for e in payload_events)

    return jsonify(
        {
            "events": payload_events,
            "thirty_day_cost_total": round(thirty_day_total, 2),
        }
    )


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

    card_type_raw = body.get("card_type", "person")
    if not isinstance(card_type_raw, str):
        return jsonify({"error": "card_type must be a string"}), 400
    card_type = card_type_raw.strip().lower()
    if card_type not in ("person", "kids", "social"):
        return jsonify({"error": "card_type must be person, kids, or social"}), 400

    prior_ct = _latest_archived_connection_trend_for_nickname(user.id, nickname)

    person = VibeTrackedPerson(
        user_id=user.id,
        nickname=nickname,
        card_type=card_type,
        emoji=emoji,
    )
    db.session.add(person)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "A tracked person with this nickname already exists"}), 409

    payload: dict = {
        "person": _person_core(person),
        "re_entry_detected": False,
        "re_entry_type": None,
        "previous_fade_tier": None,
        "previous_score": None,
        "days_since_last": None,
    }

    if prior_ct is not None:
        assessed = prior_ct.assessed_at
        today = datetime.utcnow().date()
        assessed_day = assessed.date() if assessed else today
        days_since = max(0, (today - assessed_day).days)
        prev_tier = prior_ct.fade_tier
        if (not prev_tier) and prior_ct.normalized_score is not None:
            prev_tier = compute_fade_tier(int(prior_ct.normalized_score))
        prev_score = (
            int(prior_ct.normalized_score)
            if prior_ct.normalized_score is not None
            else None
        )
        payload.update(
            {
                "re_entry_detected": True,
                "re_entry_type": "zombie" if days_since >= 60 else "submarine",
                "previous_fade_tier": prev_tier,
                "previous_score": prev_score,
                "days_since_last": days_since,
            }
        )

    return jsonify(payload), 201


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
    check_for_alerts.delay(user.id, str(p.id))
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
