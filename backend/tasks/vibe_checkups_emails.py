#!/usr/bin/env python3
"""Celery tasks: Vibe Checkups funnel emails (welcome, nudge, Mingus offer)."""

from __future__ import annotations

import html
import os
import uuid
from typing import Any

import psycopg2
import psycopg2.extras
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer
from loguru import logger

from backend.celery import celery
from backend.services.email_service import EmailService


def _get_db_connection():
    """PostgreSQL connection (same pattern as backend/api/resume_endpoints.py)."""
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        raise RuntimeError("DATABASE_URL is required. SQLite is not supported.")
    conn = psycopg2.connect(db_url)
    conn.cursor_factory = psycopg2.extras.RealDictCursor
    return conn


def _lead_id_uuid(lead_id: str) -> uuid.UUID | None:
    try:
        return uuid.UUID(str(lead_id).strip())
    except (ValueError, TypeError, AttributeError):
        return None


def _fetch_lead_for_email_tasks(lead_id: str) -> dict[str, Any] | None:
    """Load lead row without Flask / SQLAlchemy session."""
    lid = _lead_id_uuid(lead_id)
    if not lid:
        return None
    conn = _get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, email, emotional_score, financial_score, verdict_label,
                       COALESCE(verdict_emoji, '') AS verdict_emoji,
                       total_annual_projection,
                       COALESCE(mingus_converted, false) AS mingus_converted,
                       COALESCE(email_opt_out, false) AS email_opt_out
                FROM vibe_checkups_leads
                WHERE id = %s
                """,
                (str(lid),),
            )
            row = cur.fetchone()
            return dict(row) if row else None
    finally:
        conn.close()


def _serializer() -> URLSafeTimedSerializer:
    secret = os.environ.get("SECRET_KEY") or os.environ.get("CSRF_SECRET_KEY") or "dev-insecure"
    return URLSafeTimedSerializer(secret, salt="vibe-checkups-email")


def build_vibe_checkups_unsubscribe_url(lead_id: str) -> str:
    """
    Mingus-style preference link with signed token (same pattern as beta: footer URL + query).
    Validates via GET /api/vibe-checkups/unsubscribe?token=...
    """
    token = _serializer().dumps({"l": str(lead_id)})
    base = (
        os.environ.get("VIBE_CHECKUPS_UNSUBSCRIBE_URL", "").strip().rstrip("/")
        or f"{os.environ.get('PUBLIC_APP_URL', 'https://mingusapp.com').rstrip('/')}/api/vibe-checkups/unsubscribe"
    )
    sep = "&" if "?" in base else "?"
    return f"{base}{sep}token={token}"


def _footer(unsubscribe_url: str) -> str:
    u = html.escape(unsubscribe_url, quote=True)
    return (
        "<hr style=\"border:none;border-top:1px solid #e5e7eb;margin:28px 0\"/>"
        "<p style=\"color:#9ca3af;font-size:0.75rem;line-height:1.5;margin:0\">"
        f'<a href="{u}" style="color:#6b7280;text-decoration:underline;">Unsubscribe</a>'
        " from Vibe Checkups emails · "
        '<a href="https://mingusapp.com" style="color:#9ca3af">mingusapp.com</a>'
        "</p>"
    )


def _projection_link(lead_id: str) -> str:
    base = os.environ.get("PUBLIC_APP_URL", "https://mingusapp.com").rstrip("/")
    return f"{base}/vibe-checkups?lead={lead_id}"


def _format_money(n: int) -> str:
    return f"{int(n):,}"


def _welcome_html(
    *,
    verdict_label: str,
    verdict_emoji: str,
    emotional_score: int,
    financial_score: int,
    projection_url: str,
    unsubscribe_url: str,
) -> str:
    label_e = html.escape(verdict_label)
    emoji_e = html.escape(verdict_emoji)
    pu = html.escape(projection_url, quote=True)
    return f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8"/></head>
<body style="font-family:system-ui,-apple-system,sans-serif;color:#1a1a1a;max-width:600px;margin:0 auto;padding:28px 20px">
  <p style="font-size:2.5rem;margin:0 0 8px">{emoji_e}</p>
  <h1 style="font-size:1.35rem;font-weight:700;margin:0 0 12px">{label_e}</h1>
  <p style="color:#4b5563;line-height:1.6;margin:0 0 20px">Here are your Vibe Checkups scores — tap through for your full 12-month projection when you&apos;re ready.</p>
  <table style="width:100%;border-collapse:collapse;margin:20px 0">
    <tr>
      <td style="padding:14px 16px;background:#f9fafb;border-radius:10px 0 0 10px;border:1px solid #e5e7eb;width:50%">
        <div style="font-size:0.7rem;text-transform:uppercase;letter-spacing:0.06em;color:#6b7280">Emotional match</div>
        <div style="font-size:1.75rem;font-weight:800;color:#111">{emotional_score}<span style="font-size:0.9rem;color:#6b7280">%</span></div>
      </td>
      <td style="padding:14px 16px;background:#f9fafb;border-radius:0 10px 10px 0;border:1px solid #e5e7eb;border-left:none;width:50%">
        <div style="font-size:0.7rem;text-transform:uppercase;letter-spacing:0.06em;color:#6b7280">Financial match</div>
        <div style="font-size:1.75rem;font-weight:800;color:#111">{financial_score}<span style="font-size:0.9rem;color:#6b7280">%</span></div>
      </td>
    </tr>
  </table>
  <p style="margin:24px 0">
    <a href="{pu}" style="display:inline-block;background:#111827;color:#fff;padding:14px 22px;border-radius:10px;text-decoration:none;font-weight:600">Open your full results</a>
  </p>
  <p style="color:#6b7280;font-size:0.9rem;line-height:1.55;margin:20px 0 0">
    Ready to take your own finances seriously? Mingus was built for exactly that.
  </p>
  {_footer(unsubscribe_url)}
</body></html>"""


def _nudge_html(*, annual: int, projection_url: str, unsubscribe_url: str) -> str:
    a = _format_money(annual)
    pu = html.escape(projection_url, quote=True)
    return f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8"/></head>
<body style="font-family:system-ui,-apple-system,sans-serif;color:#1a1a1a;max-width:600px;margin:0 auto;padding:28px 20px">
  <p style="line-height:1.65;color:#374151;margin:0 0 16px">That <strong>${a}</strong> year-one number isn&apos;t just &ldquo;relationship spend&rdquo; — it&apos;s money that could compound for you instead. Even half of it invested steadily becomes something entirely different ten years out.</p>
  <p style="line-height:1.65;color:#374151;margin:0 0 22px">You already did the hard part: seeing the pattern clearly.</p>
  <p style="margin:0 0 8px">
    <a href="{pu}" style="display:inline-block;background:#111827;color:#fff;padding:14px 22px;border-radius:10px;text-decoration:none;font-weight:600">Revisit your projection</a>
  </p>
  <p style="margin:20px 0 0">
    <a href="https://mingusapp.com/signup" style="color:#2563eb;font-weight:600">See what Mingus can do for your finances →</a>
  </p>
  {_footer(unsubscribe_url)}
</body></html>"""


def _mingus_offer_html(*, unsubscribe_url: str) -> str:
    return f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8"/></head>
<body style="font-family:system-ui,-apple-system,sans-serif;color:#1a1a1a;max-width:600px;margin:0 auto;padding:28px 20px">
  <h1 style="font-size:1.25rem;font-weight:700;margin:0 0 12px">Your first month on Mingus is on us</h1>
  <p style="line-height:1.65;color:#374151;margin:0 0 16px">Start a <strong>30-day free trial</strong> — no credit card required. Bring the same clarity you felt in Vibe Checkups to your real numbers, goals, and stress points.</p>
  <p style="margin:22px 0">
    <a href="https://mingusapp.com/signup" style="display:inline-block;background:#2563eb;color:#fff;padding:14px 22px;border-radius:10px;text-decoration:none;font-weight:600">Claim your free month</a>
  </p>
  {_footer(unsubscribe_url)}
</body></html>"""


@celery.task(name="send_vibe_checkups_welcome", bind=True, max_retries=3)
def send_vibe_checkups_welcome(self, lead_id: str) -> dict[str, Any]:
    lead = _fetch_lead_for_email_tasks(lead_id)
    if not lead:
        logger.error("send_vibe_checkups_welcome: lead not found {}", lead_id)
        return {"ok": False, "error": "lead_not_found"}
    lid = str(lead["id"])
    u = build_vibe_checkups_unsubscribe_url(lid)
    emoji = (lead.get("verdict_emoji") or "").strip() or "✨"
    html_body = _welcome_html(
        verdict_label=lead.get("verdict_label") or "",
        verdict_emoji=emoji,
        emotional_score=int(lead["emotional_score"]),
        financial_score=int(lead["financial_score"]),
        projection_url=_projection_link(lid),
        unsubscribe_url=u,
    )
    subject = "Your Vibe Checkups results are inside 💛"
    ok = EmailService().send_email(to=lead["email"], subject=subject, html_body=html_body)

    if ok:
        logger.info("send_vibe_checkups_welcome: sent lead_id={}", lead_id)
        return {"ok": True}
    if self.request.retries >= self.max_retries:
        return {"ok": False, "error": "send_failed"}
    raise self.retry(exc=RuntimeError("send_email returned False"), countdown=120)


@celery.task(name="send_vibe_checkups_nudge", bind=True, max_retries=3)
def send_vibe_checkups_nudge(self, lead_id: str) -> dict[str, Any]:
    lead = _fetch_lead_for_email_tasks(lead_id)
    if not lead:
        return {"ok": False, "error": "lead_not_found"}
    if bool(lead.get("email_opt_out")):
        return {"ok": True, "skipped": "opt_out"}
    lid = str(lead["id"])
    annual = int(lead.get("total_annual_projection") or 0)
    u = build_vibe_checkups_unsubscribe_url(lid)
    html_body = _nudge_html(
        annual=annual,
        projection_url=_projection_link(lid),
        unsubscribe_url=u,
    )
    subject = f"That ${ _format_money(annual) } number is still sitting there..."
    ok = EmailService().send_email(to=lead["email"], subject=subject, html_body=html_body)

    if ok:
        return {"ok": True}
    if self.request.retries >= self.max_retries:
        return {"ok": False, "error": "send_failed"}
    raise self.retry(exc=RuntimeError("send_email returned False"), countdown=120)


@celery.task(name="send_vibe_checkups_mingus_offer", bind=True, max_retries=3)
def send_vibe_checkups_mingus_offer(self, lead_id: str) -> dict[str, Any]:
    lead = _fetch_lead_for_email_tasks(lead_id)
    if not lead:
        return {"ok": False, "error": "lead_not_found"}
    if bool(lead.get("email_opt_out")):
        return {"ok": True, "skipped": "opt_out"}
    if bool(lead.get("mingus_converted")):
        return {"ok": True, "skipped": "converted"}
    lid = str(lead["id"])
    u = build_vibe_checkups_unsubscribe_url(lid)
    html_body = _mingus_offer_html(unsubscribe_url=u)
    subject = "Your first month on Mingus is on us"
    ok = EmailService().send_email(to=lead["email"], subject=subject, html_body=html_body)

    if ok:
        return {"ok": True}
    if self.request.retries >= self.max_retries:
        return {"ok": False, "error": "send_failed"}
    raise self.retry(exc=RuntimeError("send_email returned False"), countdown=120)


def verify_unsubscribe_token(token: str, max_age_seconds: int | None = 31536000 * 5) -> str | None:
    """Return lead_id UUID string if token is valid."""
    try:
        data = _serializer().loads(token, max_age=max_age_seconds)
    except (BadSignature, SignatureExpired):
        return None
    if not isinstance(data, dict):
        return None
    lid = data.get("l")
    if not lid or not isinstance(lid, str):
        return None
    return lid
