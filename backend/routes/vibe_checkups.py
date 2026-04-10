#!/usr/bin/env python3
"""Vibe Checkups anonymous quiz API (lead funnel)."""

from __future__ import annotations

import logging
import os
import uuid
from datetime import datetime, timedelta
from urllib.parse import urlencode

from flask import Blueprint, g, jsonify, request
from sqlalchemy import case, func

from backend.auth.decorators import require_auth, require_csrf
from backend.middleware.limiter_ext import limiter
from backend.models.database import db
from backend.models.user_models import User
from backend.models.vibe_checkups import (
    VIBE_CHECKUPS_EVENT_TYPES,
    VibeCheckupsFunnelEvent,
    VibeCheckupsLead,
    VibeCheckupsSession,
)
from backend.services import vibe_checkups_service as vc_svc

vibe_checkups_bp = Blueprint("vibe_checkups", __name__)

_ALLOWED_TRACK_EVENTS = frozenset(VIBE_CHECKUPS_EVENT_TYPES)


def _user_for_jwt():
    ext = getattr(g, "current_user_id", None)
    if ext is None:
        return None
    return User.query.filter_by(user_id=str(ext)).first()


def _is_admin_user(user: User | None) -> bool:
    if not user:
        return False
    if getattr(user, "is_admin", False):
        return True
    role = (getattr(user, "role", None) or "").lower()
    return role == "admin"


def _jwt_admin_ok() -> bool:
    payload = getattr(g, "token_payload", None) or {}
    return (payload.get("role") or "").lower() == "admin"


def _admin_forbidden():
    return jsonify({"error": "Admin access required"}), 403


def _parse_json() -> dict:
    data = request.get_json(silent=True)
    return data if isinstance(data, dict) else {}


def _log_funnel_event(
    *,
    event_type: str,
    session_id=None,
    lead_id=None,
    event_data=None,
    utm_source=None,
    utm_medium=None,
):
    ev = VibeCheckupsFunnelEvent(
        session_id=session_id,
        lead_id=lead_id,
        event_type=event_type,
        event_data=event_data,
        occurred_at=datetime.utcnow(),
        utm_source=utm_source,
        utm_medium=utm_medium,
    )
    db.session.add(ev)


def _session_by_token(token: str) -> VibeCheckupsSession | None:
    if not token:
        return None
    safe = vc_svc.sanitize_optional_str(token, max_length=255, allow_empty=False)
    if not safe:
        return None
    return VibeCheckupsSession.query.filter_by(session_token=safe).first()


def _parse_uuid_param(value: str):
    try:
        return uuid.UUID(str(value).strip())
    except (ValueError, TypeError, AttributeError):
        return None


@vibe_checkups_bp.route("/unsubscribe", methods=["GET"])
def vibe_checkups_unsubscribe():
    """One-click unsubscribe for Vibe Checkups sequence (signed token in query)."""
    from backend.tasks.vibe_checkups_emails import verify_unsubscribe_token

    token = request.args.get("token") or ""
    if not isinstance(token, str) or not token.strip():
        return (
            "<!DOCTYPE html><html><body style=\"font-family:system-ui;padding:2rem\">"
            "<p>Missing unsubscribe token.</p></body></html>",
            400,
        )
    lid_str = verify_unsubscribe_token(token.strip())
    if not lid_str:
        return (
            "<!DOCTYPE html><html><body style=\"font-family:system-ui;padding:2rem\">"
            "<p>This link is invalid or has expired.</p></body></html>",
            400,
        )
    lid = _parse_uuid_param(lid_str)
    if not lid:
        return (
            "<!DOCTYPE html><html><body style=\"font-family:system-ui;padding:2rem\">"
            "<p>Invalid link.</p></body></html>",
            400,
        )
    lead = db.session.get(VibeCheckupsLead, lid)
    if lead:
        lead.email_opt_out = True
        db.session.commit()
    html_ok = (
        "<!DOCTYPE html><html><head><meta charset=\"UTF-8\"/></head>"
        "<body style=\"font-family:system-ui;padding:2rem;max-width:32rem;line-height:1.5\">"
        "<h1 style=\"font-size:1.25rem\">You&rsquo;re unsubscribed</h1>"
        "<p style=\"color:#4b5563\">We won&rsquo;t send more Vibe Checkups follow-ups to this address.</p>"
        "<p style=\"margin-top:1.5rem\"><a href=\"https://mingusapp.com\">mingusapp.com</a></p>"
        "</body></html>"
    )
    return html_ok, 200


@vibe_checkups_bp.route("/csrf-token", methods=["GET"])
def vibe_checkups_csrf_token():
    """Public CSRF secret for anonymous Vibe Checkups POSTs (matches X-CSRF-Token validation)."""
    return jsonify(
        {"csrf_token": os.environ.get("CSRF_SECRET_KEY", "your-csrf-secret-key")}
    )


@vibe_checkups_bp.route("/session/start", methods=["POST"])
@limiter.limit("60 per minute")
@require_csrf
def session_start():
    body = _parse_json()
    utm_source = vc_svc.sanitize_optional_str(body.get("utm_source"))
    utm_medium = vc_svc.sanitize_optional_str(body.get("utm_medium"))
    utm_campaign = vc_svc.sanitize_optional_str(body.get("utm_campaign"))
    ip_address = vc_svc.sanitize_optional_str(
        body.get("ip_address"), max_length=45
    ) or vc_svc.sanitize_optional_str(
        request.headers.get("X-Forwarded-For", "").split(",")[0].strip(),
        max_length=45,
    )
    user_agent = vc_svc.sanitize_optional_str(
        body.get("user_agent"), max_length=2000
    ) or vc_svc.sanitize_optional_str(
        request.headers.get("User-Agent", ""), max_length=2000
    )

    session_token = str(uuid.uuid4())
    sess = VibeCheckupsSession(
        session_token=session_token,
        answers={},
        current_question=0,
        started_at=datetime.utcnow(),
        utm_source=utm_source,
        utm_medium=utm_medium,
        utm_campaign=utm_campaign,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    db.session.add(sess)
    db.session.flush()

    _log_funnel_event(
        event_type="quiz_started",
        session_id=sess.id,
        utm_source=utm_source,
        utm_medium=utm_medium,
    )
    db.session.commit()

    return (
        jsonify(
            {
                "session_token": session_token,
                "created_at": sess.started_at.isoformat() + "Z",
            }
        ),
        201,
    )


@vibe_checkups_bp.route("/session/<session_token>/answer", methods=["POST"])
@limiter.limit("120 per minute")
@require_csrf
def session_answer(session_token: str):
    body = _parse_json()
    qid = vc_svc.sanitize_optional_str(body.get("question_id"), max_length=128)
    if not qid:
        return jsonify({"error": "question_id is required"}), 400

    try:
        value = int(body.get("value"))
        financial = int(body.get("financial"))
    except (TypeError, ValueError):
        return jsonify({"error": "value and financial must be integers"}), 400

    value = max(0, min(3, value))
    financial = max(0, min(3, financial))

    sess = _session_by_token(session_token)
    if not sess:
        return jsonify({"error": "Session not found"}), 404
    if sess.completed_at is not None:
        return jsonify({"error": "Session already completed"}), 409

    answers = dict(sess.answers or {})
    answers[qid] = {"value": value, "financial": financial}
    sess.answers = answers
    sess.current_question = (sess.current_question or 0) + 1

    db.session.commit()
    return jsonify({"saved": True, "current_question": sess.current_question})


@vibe_checkups_bp.route("/session/<session_token>/complete", methods=["POST"])
@limiter.limit("30 per minute")
@require_csrf
def session_complete(session_token: str):
    sess = _session_by_token(session_token)
    if not sess:
        return jsonify({"error": "Session not found"}), 404

    answers = dict(sess.answers or {})
    scores = vc_svc.calculate_scores(answers)
    emotional = scores["emotional_score"]
    financial = scores["financial_score"]
    overall = (emotional + financial) / 2.0
    verdict = vc_svc.get_verdict(overall, 100.0)

    already = sess.completed_at is not None
    if not already:
        sess.completed_at = datetime.utcnow()
        _log_funnel_event(
            event_type="quiz_completed",
            session_id=sess.id,
            utm_source=sess.utm_source,
            utm_medium=sess.utm_medium,
        )
    db.session.commit()

    return jsonify(
        {
            "emotional_score": emotional,
            "financial_score": financial,
            "verdict_label": verdict["label"],
            "verdict_emoji": verdict["emoji"],
            "verdict_description": verdict["description"],
        }
    )


@vibe_checkups_bp.route("/session/<session_token>/capture-email", methods=["POST"])
@limiter.limit("20 per minute")
@require_csrf
def session_capture_email(session_token: str):
    body = _parse_json()
    raw_email = body.get("email")
    if not isinstance(raw_email, str):
        return jsonify({"error": "email is required"}), 400
    email = raw_email.strip().lower()
    if not vc_svc.is_valid_email(email):
        return jsonify({"error": "Invalid email format"}), 400

    sess = _session_by_token(session_token)
    if not sess:
        return jsonify({"error": "Session not found"}), 404
    if not sess.completed_at:
        return jsonify({"error": "Complete the quiz before submitting email"}), 400

    existing = VibeCheckupsLead.query.filter_by(session_id=sess.id).first()
    if existing:
        return jsonify({"error": "Email already captured for this session"}), 409

    answers = dict(sess.answers or {})
    scores = vc_svc.calculate_scores(answers)
    emotional = scores["emotional_score"]
    financial = scores["financial_score"]
    overall = (emotional + financial) / 2.0
    verdict = vc_svc.get_verdict(overall, 100.0)
    projection_data = vc_svc.build_projection(answers)
    total_annual = (
        projection_data[-1]["cumulative_cost"] if projection_data else 0
    )

    lead = VibeCheckupsLead(
        session_id=sess.id,
        email=email,
        emotional_score=emotional,
        financial_score=financial,
        verdict_label=verdict["label"],
        verdict_emoji=verdict.get("emoji") or "",
        total_annual_projection=int(total_annual),
        projection_data=projection_data,
        created_at=datetime.utcnow(),
        email_sequence_started=True,
    )
    db.session.add(lead)
    db.session.flush()

    _log_funnel_event(
        event_type="email_captured",
        session_id=sess.id,
        lead_id=lead.id,
        event_data={"email_domain": email.split("@")[-1] if "@" in email else None},
        utm_source=sess.utm_source,
        utm_medium=sess.utm_medium,
    )
    db.session.commit()

    try:
        from backend.tasks.vibe_checkups_emails import (
            send_vibe_checkups_mingus_offer,
            send_vibe_checkups_nudge,
            send_vibe_checkups_welcome,
        )

        send_vibe_checkups_welcome.delay(str(lead.id))
        send_vibe_checkups_nudge.apply_async(args=[str(lead.id)], countdown=3 * 24 * 3600)
        send_vibe_checkups_mingus_offer.apply_async(
            args=[str(lead.id)], countdown=7 * 24 * 3600
        )
    except Exception as exc:
        logging.getLogger(__name__).warning(
            "Vibe Checkups email sequence not queued: %s", exc
        )

    return (
        jsonify(
            {
                "lead_id": str(lead.id),
                "verdict_label": verdict["label"],
                "verdict_emoji": verdict["emoji"],
                "verdict_description": verdict["description"],
                "emotional_score": emotional,
                "financial_score": financial,
            }
        ),
        201,
    )


@vibe_checkups_bp.route("/lead/<lead_id>/unlock-projection", methods=["POST"])
@limiter.limit("60 per minute")
@require_csrf
def lead_unlock_projection(lead_id: str):
    lid = _parse_uuid_param(lead_id)
    if not lid:
        return jsonify({"error": "Invalid lead_id"}), 400

    lead = db.session.get(VibeCheckupsLead, lid)
    if not lead:
        return jsonify({"error": "Lead not found"}), 404

    body = _parse_json()
    amount_cents = body.get("amount_cents")
    if amount_cents is not None:
        try:
            ac = int(amount_cents)
        except (TypeError, ValueError):
            return jsonify({"error": "amount_cents must be an integer"}), 400
        if ac < 0:
            return jsonify({"error": "amount_cents must be non-negative"}), 400
        lead.unlock_paid = True
        lead.unlock_amount_cents = ac

    lead.unlocked_projection = True

    sess = db.session.get(VibeCheckupsSession, lead.session_id)
    _log_funnel_event(
        event_type="projection_unlocked",
        session_id=lead.session_id,
        lead_id=lead.id,
        event_data={"unlock_paid": lead.unlock_paid},
        utm_source=sess.utm_source if sess else None,
        utm_medium=sess.utm_medium if sess else None,
    )
    db.session.commit()

    return jsonify({"projection_data": lead.projection_data})


@vibe_checkups_bp.route("/lead/<lead_id>/convert-to-mingus", methods=["POST"])
@limiter.limit("60 per minute")
@require_csrf
def lead_convert_to_mingus(lead_id: str):
    lid = _parse_uuid_param(lead_id)
    if not lid:
        return jsonify({"error": "Invalid lead_id"}), 400

    lead = db.session.get(VibeCheckupsLead, lid)
    if not lead:
        return jsonify({"error": "Lead not found"}), 404
    if not lead.unlocked_projection:
        return jsonify({"error": "Projection not unlocked"}), 400

    lead.mingus_signup_clicked = True
    sess = db.session.get(VibeCheckupsSession, lead.session_id)
    utm_source = sess.utm_source if sess else None
    utm_medium = sess.utm_medium if sess else None
    db.session.commit()

    params = {
        "source": "love_ledger",
        "email": lead.email.strip(),
        "vc_lead_id": str(lead.id),
    }
    if utm_source:
        params["utm_source"] = utm_source
    if utm_medium:
        params["utm_medium"] = utm_medium
    if sess and sess.utm_campaign:
        params["utm_campaign"] = sess.utm_campaign

    redirect_url = f"/register?{urlencode(params)}"
    return jsonify({"redirect_url": redirect_url})


@vibe_checkups_bp.route("/lead/mingus-converted-by-email", methods=["POST"])
@limiter.limit("30 per minute")
@require_csrf
def lead_mingus_converted_by_email():
    """Fallback when vc_lead_id is missing: latest love-ledger lead for this email."""
    body = _parse_json()
    raw = body.get("email")
    if not isinstance(raw, str) or not raw.strip():
        return jsonify({"error": "email is required"}), 400
    email = raw.strip().lower()
    if not vc_svc.is_valid_email(email):
        return jsonify({"error": "Invalid email format"}), 400

    lead = (
        VibeCheckupsLead.query.filter(
            VibeCheckupsLead.email == email,
            VibeCheckupsLead.mingus_signup_clicked.is_(True),
        )
        .order_by(VibeCheckupsLead.created_at.desc())
        .first()
    )
    if not lead:
        return jsonify({"error": "Lead not found"}), 404

    if lead.mingus_converted:
        return jsonify({"ok": True, "already": True})

    lead.mingus_converted = True
    sess = db.session.get(VibeCheckupsSession, lead.session_id)
    _log_funnel_event(
        event_type="mingus_converted",
        session_id=lead.session_id,
        lead_id=lead.id,
        utm_source=sess.utm_source if sess else None,
        utm_medium=sess.utm_medium if sess else None,
    )
    db.session.commit()
    return jsonify({"ok": True})


@vibe_checkups_bp.route("/lead/<lead_id>/mingus-converted", methods=["POST"])
@limiter.limit("30 per minute")
@require_csrf
def lead_mingus_converted(lead_id: str):
    lid = _parse_uuid_param(lead_id)
    if not lid:
        return jsonify({"error": "Invalid lead_id"}), 400

    lead = db.session.get(VibeCheckupsLead, lid)
    if not lead:
        return jsonify({"error": "Lead not found"}), 404

    body = _parse_json()
    raw = body.get("email")
    if not isinstance(raw, str) or not raw.strip():
        return jsonify({"error": "email is required"}), 400
    email = raw.strip().lower()
    if email != (lead.email or "").strip().lower():
        return jsonify({"error": "Email does not match lead"}), 400

    if lead.mingus_converted:
        return jsonify({"ok": True, "already": True})

    lead.mingus_converted = True
    sess = db.session.get(VibeCheckupsSession, lead.session_id)
    _log_funnel_event(
        event_type="mingus_converted",
        session_id=lead.session_id,
        lead_id=lead.id,
        utm_source=sess.utm_source if sess else None,
        utm_medium=sess.utm_medium if sess else None,
    )
    db.session.commit()
    return jsonify({"ok": True})


@vibe_checkups_bp.route("/lead/<lead_id>/track-event", methods=["POST"])
@limiter.limit("120 per minute")
@require_csrf
def lead_track_event(lead_id: str):
    lid = _parse_uuid_param(lead_id)
    if not lid:
        return jsonify({"error": "Invalid lead_id"}), 400

    lead = db.session.get(VibeCheckupsLead, lid)
    if not lead:
        return jsonify({"error": "Lead not found"}), 404

    body = _parse_json()
    event_type = body.get("event_type")
    if not isinstance(event_type, str):
        return jsonify({"error": "event_type is required"}), 400
    event_type = event_type.strip()
    if event_type not in _ALLOWED_TRACK_EVENTS:
        return jsonify(
            {
                "error": "Invalid event_type",
                "allowed": sorted(_ALLOWED_TRACK_EVENTS),
            }
        ), 400

    event_data = body.get("event_data")
    if event_data is not None and not isinstance(event_data, dict):
        return jsonify({"error": "event_data must be a JSON object"}), 400

    sess = db.session.get(VibeCheckupsSession, lead.session_id)
    _log_funnel_event(
        event_type=event_type,
        session_id=lead.session_id,
        lead_id=lead.id,
        event_data=event_data,
        utm_source=sess.utm_source if sess else None,
        utm_medium=sess.utm_medium if sess else None,
    )
    db.session.commit()
    return jsonify({"ok": True})


def _window_start(days: int | None) -> datetime | None:
    if days is None:
        return None
    return datetime.utcnow() - timedelta(days=days)


def _distinct_lead_event_count(event_type: str, since: datetime | None) -> int:
    """Count distinct leads per funnel event (avoids double-counting duplicate posts)."""
    q = db.session.query(func.count(func.distinct(VibeCheckupsFunnelEvent.lead_id))).filter(
        VibeCheckupsFunnelEvent.event_type == event_type,
        VibeCheckupsFunnelEvent.lead_id.isnot(None),
    )
    if since is not None:
        q = q.filter(VibeCheckupsFunnelEvent.occurred_at >= since)
    return int(q.scalar() or 0)


def _metrics_for_window(since: datetime | None) -> dict:
    sq = VibeCheckupsSession.query
    if since is not None:
        sq = sq.filter(VibeCheckupsSession.started_at >= since)
    started = sq.count()

    cq = VibeCheckupsSession.query.filter(VibeCheckupsSession.completed_at.isnot(None))
    if since is not None:
        cq = cq.filter(VibeCheckupsSession.completed_at >= since)
    completed = cq.count()

    lq = VibeCheckupsLead.query
    if since is not None:
        lq = lq.filter(VibeCheckupsLead.created_at >= since)
    leads = lq.count()

    projection_unlocks = _distinct_lead_event_count("projection_unlocked", since)
    mingus_clicks = _distinct_lead_event_count("mingus_cta_clicked", since)
    mingus_converted_n = _distinct_lead_event_count("mingus_converted", since)

    completion_rate = (completed / started) if started else 0.0
    email_capture_rate = (leads / completed) if completed else 0.0
    projection_unlock_rate = (projection_unlocks / leads) if leads else 0.0
    mingus_cta_rate = (mingus_clicks / projection_unlocks) if projection_unlocks else 0.0
    mingus_conversion_rate = (mingus_converted_n / leads) if leads else 0.0
    mingus_funnel_rate = (mingus_converted_n / mingus_clicks) if mingus_clicks else 0.0

    return {
        "quiz_sessions_started": started,
        "quiz_sessions_completed": completed,
        "completion_rate": round(completion_rate, 4),
        "leads_captured": leads,
        "email_capture_rate": round(email_capture_rate, 4),
        "projection_unlocks": projection_unlocks,
        "projection_unlock_rate": round(projection_unlock_rate, 4),
        "mingus_cta_clicks": mingus_clicks,
        "mingus_cta_click_rate": round(mingus_cta_rate, 4),
        "mingus_converted": mingus_converted_n,
        "mingus_conversion_rate": round(mingus_conversion_rate, 4),
        "mingus_conversion_of_cta_rate": round(mingus_funnel_rate, 4),
    }


@vibe_checkups_bp.route("/analytics/summary", methods=["GET"])
@require_auth
def analytics_summary():
    user = _user_for_jwt()
    if not user:
        return jsonify({"error": "User not found"}), 404
    if not (_is_admin_user(user) or _jwt_admin_ok()):
        return _admin_forbidden()

    ts = VibeCheckupsSession.query.count()
    cs = VibeCheckupsSession.query.filter(
        VibeCheckupsSession.completed_at.isnot(None)
    ).count()
    tl = VibeCheckupsLead.query.count()
    unlocked = VibeCheckupsLead.query.filter(
        VibeCheckupsLead.unlocked_projection.is_(True)
    ).count()
    mingus_conv = VibeCheckupsLead.query.filter(
        VibeCheckupsLead.mingus_converted.is_(True)
    ).count()
    mingus_cta_total = VibeCheckupsLead.query.filter(
        VibeCheckupsLead.mingus_signup_clicked.is_(True)
    ).count()

    completion_rate = (cs / ts) if ts else 0.0
    email_capture_rate = (tl / cs) if cs else 0.0
    projection_unlock_rate = (unlocked / tl) if tl else 0.0
    mingus_conversion_rate = (mingus_conv / tl) if tl else 0.0
    mingus_cta_click_rate = (mingus_cta_total / unlocked) if unlocked else 0.0

    top_sources_rows = (
        db.session.query(VibeCheckupsSession.utm_source, func.count().label("c"))
        .filter(
            VibeCheckupsSession.utm_source.isnot(None),
            VibeCheckupsSession.utm_source != "",
        )
        .group_by(VibeCheckupsSession.utm_source)
        .order_by(func.count().desc())
        .limit(10)
        .all()
    )
    top_utm_sources = [
        {"utm_source": row[0], "sessions": int(row[1])} for row in top_sources_rows
    ]

    since_7 = _window_start(7)
    since_30 = _window_start(30)

    utm_table_rows = (
        db.session.query(
            VibeCheckupsSession.utm_source,
            VibeCheckupsSession.utm_medium,
            func.count(VibeCheckupsSession.id).label("session_count"),
            func.count(VibeCheckupsLead.id).label("lead_count"),
            func.coalesce(
                func.sum(case((VibeCheckupsLead.mingus_converted.is_(True), 1), else_=0)),
                0,
            ).label("converted_count"),
        )
        .outerjoin(VibeCheckupsLead, VibeCheckupsLead.session_id == VibeCheckupsSession.id)
        .filter(VibeCheckupsSession.started_at >= since_30)
        .group_by(VibeCheckupsSession.utm_source, VibeCheckupsSession.utm_medium)
        .order_by(func.count(VibeCheckupsSession.id).desc())
        .limit(25)
        .all()
    )
    top_utm_breakdown = []
    for row in utm_table_rows:
        src = row[0] if row[0] not in (None, "") else "(direct / none)"
        med = row[1] if row[1] not in (None, "") else "—"
        lc = int(row[3] or 0)
        conv = int(row[4] or 0)
        top_utm_breakdown.append(
            {
                "utm_source": src,
                "utm_medium": med,
                "count": int(row[2] or 0),
                "lead_count": lc,
                "conversion_rate": round((conv / lc), 4) if lc else 0.0,
            }
        )

    verdict_rows = (
        db.session.query(
            VibeCheckupsLead.verdict_label,
            func.count(VibeCheckupsLead.id),
        )
        .group_by(VibeCheckupsLead.verdict_label)
        .all()
    )
    verdict_total = sum(int(r[1]) for r in verdict_rows) or 0
    verdict_distribution = [
        {
            "verdict_label": r[0],
            "count": int(r[1]),
            "pct": round((int(r[1]) / verdict_total), 4) if verdict_total else 0.0,
        }
        for r in verdict_rows
    ]
    verdict_distribution.sort(key=lambda x: -x["count"])

    return jsonify(
        {
            "total_sessions": ts,
            "completed_sessions": cs,
            "total_leads": tl,
            "completion_rate": round(completion_rate, 4),
            "email_capture_rate": round(email_capture_rate, 4),
            "projection_unlock_rate": round(projection_unlock_rate, 4),
            "mingus_cta_click_rate": round(mingus_cta_click_rate, 4),
            "mingus_conversion_rate": round(mingus_conversion_rate, 4),
            "top_utm_sources": top_utm_sources,
            "windows": {
                "last_7d": _metrics_for_window(since_7),
                "last_30d": _metrics_for_window(since_30),
                "all_time": _metrics_for_window(None),
            },
            "top_utm_breakdown_30d": top_utm_breakdown,
            "verdict_distribution": verdict_distribution,
        }
    )
