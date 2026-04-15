#!/usr/bin/env python3
"""Bug report API: submit (authenticated), admin list/detail/status."""

from __future__ import annotations

import os
import sqlite3
from datetime import datetime

from flask import Blueprint, jsonify, request, g

from backend.auth.decorators import require_auth, require_csrf
from backend.models.bug_report import BugReport
from backend.models.database import db
from backend.models.user_models import User
from backend.services.business_intelligence_log import _db_path as _bi_db_path

bug_report_bp = Blueprint("bug_report", __name__, url_prefix="/api/bug-report")


def _user_for_jwt() -> User | None:
    ext = getattr(g, "current_user_id", None)
    if ext is None:
        return None
    return User.query.filter_by(user_id=str(ext)).first()


def _is_admin(user: User | None) -> bool:
    return bool(user and getattr(user, "is_admin", False))


def _admin_forbidden():
    return jsonify({"error": "Admin access required"}), 403


def _display_name(user: User) -> str:
    parts = [p for p in (user.first_name, user.last_name) if p]
    name = " ".join(parts).strip()
    if not name:
        name = (user.email or "User").strip()
    return name[:100]


def _last_feature_from_bi(user: User) -> str | None:
    path = _bi_db_path()
    if not os.path.isfile(path):
        return None
    try:
        conn = sqlite3.connect(path)
        try:
            cur = conn.execute(
                """
                SELECT feature_name FROM feature_events
                WHERE user_id = ?
                ORDER BY timestamp DESC
                LIMIT 1
                """,
                (str(user.user_id),),
            )
            row = cur.fetchone()
            if row and row[0]:
                return str(row[0])[:100]
        finally:
            conn.close()
    except sqlite3.Error:
        pass
    return None


@bug_report_bp.route("/submit", methods=["POST"])
@require_auth
@require_csrf
def submit_bug_report():
    data = request.get_json(silent=True) or {}
    description = (data.get("description") or "").strip()
    if not description or len(description) > 1000:
        return jsonify({"error": "description required, max 1000 characters"}), 400

    current_route = data.get("current_route")
    if current_route is not None:
        current_route = str(current_route).strip()[:255] or None
    browser_info = data.get("browser_info")
    if browser_info is not None:
        browser_info = str(browser_info).strip()[:255] or None

    balance_status = data.get("balance_status")
    if balance_status is not None:
        balance_status = str(balance_status).strip()[:20] or None

    body_last_feature = data.get("last_feature")
    if body_last_feature is not None:
        body_last_feature = str(body_last_feature).strip()[:100] or None

    additional = data.get("additional_context")
    if additional is not None:
        additional = str(additional).strip()
        if additional:
            description = f"{description}\n\nAdditional context:\n{additional}"

    user = _user_for_jwt()
    if not user:
        return jsonify({"error": "User not found"}), 404
    if not (user.email or "").strip():
        return jsonify({"error": "User email required"}), 400

    last_feature = _last_feature_from_bi(user)
    if not last_feature and body_last_feature:
        last_feature = body_last_feature

    created = user.created_at or datetime.utcnow()
    account_age_days = (datetime.utcnow() - created).days

    ticket_number = BugReport.next_ticket_number()
    tier = (user.tier or "budget")[:20]

    report = BugReport(
        ticket_number=ticket_number,
        user_id=user.id,
        user_email=(user.email or "")[:255],
        user_name=_display_name(user),
        user_tier=tier,
        description=description,
        current_route=current_route,
        browser_info=browser_info,
        balance_status=balance_status,
        last_feature=last_feature,
        account_age_days=account_age_days,
        is_beta=bool(getattr(user, "is_beta", False)),
    )
    db.session.add(report)
    db.session.commit()

    from backend.tasks.bug_report_tasks import (
        send_bug_report_admin_email,
        send_bug_report_user_email,
    )

    send_bug_report_admin_email.delay(report.id)
    send_bug_report_user_email.delay(report.id)

    return (
        jsonify(
            {
                "ticket_number": report.ticket_number,
                "created_at": report.created_at.isoformat() if report.created_at else None,
            }
        ),
        201,
    )


@bug_report_bp.route("/list", methods=["GET"])
@require_auth
def list_bug_reports():
    user = _user_for_jwt()
    if not user:
        return jsonify({"error": "User not found"}), 404
    if not _is_admin(user):
        return _admin_forbidden()

    raw_status = request.args.get("status")
    status_filter = None
    if raw_status is not None and str(raw_status).strip():
        status_filter = str(raw_status).strip().lower()
        if status_filter not in BugReport.ALLOWED_STATUS:
            return jsonify({"error": "invalid status filter"}), 400

    try:
        page = int(request.args.get("page", 1))
    except (TypeError, ValueError):
        page = 1
    try:
        per_page = int(request.args.get("per_page", 25))
    except (TypeError, ValueError):
        per_page = 25
    page = max(1, page)
    per_page = min(max(1, per_page), 100)

    q = BugReport.query
    if status_filter:
        q = q.filter(BugReport.status == status_filter)
    q = q.order_by(BugReport.created_at.desc())

    total = q.count()
    items = q.offset((page - 1) * per_page).limit(per_page).all()

    return (
        jsonify(
            {
                "items": [r.to_dict() for r in items],
                "page": page,
                "per_page": per_page,
                "total": total,
            }
        ),
        200,
    )


@bug_report_bp.route("/<ticket_number>", methods=["GET"])
@require_auth
def get_bug_report(ticket_number: str):
    user = _user_for_jwt()
    if not user:
        return jsonify({"error": "User not found"}), 404
    if not _is_admin(user):
        return _admin_forbidden()

    ticket_number = (ticket_number or "").strip().upper()
    report = BugReport.query.filter_by(ticket_number=ticket_number).first()
    if not report:
        return jsonify({"error": "Not found"}), 404
    return jsonify(report.to_dict()), 200


@bug_report_bp.route("/<ticket_number>/status", methods=["PATCH"])
@require_auth
@require_csrf
def patch_bug_report_status(ticket_number: str):
    user = _user_for_jwt()
    if not user:
        return jsonify({"error": "User not found"}), 404
    if not _is_admin(user):
        return _admin_forbidden()

    ticket_number = (ticket_number or "").strip().upper()
    report = BugReport.query.filter_by(ticket_number=ticket_number).first()
    if not report:
        return jsonify({"error": "Not found"}), 404

    data = request.get_json(silent=True) or {}
    raw_status = data.get("status")
    if raw_status is None or not str(raw_status).strip():
        return jsonify({"error": "invalid status"}), 400
    new_status = str(raw_status).strip().lower()
    if new_status not in BugReport.ALLOWED_STATUS:
        return jsonify({"error": "invalid status"}), 400

    if "admin_notes" in data:
        an = data.get("admin_notes")
        report.admin_notes = None if an is None else str(an)

    report.status = new_status
    now = datetime.utcnow()
    if new_status == "resolved":
        report.resolved_at = now
    else:
        report.resolved_at = None
    report.updated_at = now
    db.session.commit()

    return jsonify(report.to_dict()), 200
