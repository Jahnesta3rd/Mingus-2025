"""Notification dispatcher — email digests via SendGrid, SMS via Twilio."""

import logging
import os
from datetime import date, datetime, timezone

from storage import db

logger = logging.getLogger(__name__)

HOT_LEAD_THRESHOLD = float(os.getenv("HOT_LEAD_THRESHOLD", "9.0"))
DIGEST_LIMIT = 15

DIVIDER = "─" * 50


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _signal_strength(composite: float) -> str:
    if composite >= 8.0:
        return "HIGH 🔴"
    if composite >= 6.5:
        return "MEDIUM 🟡"
    return "LOW ⚪"


def _format_lead_block(lead: dict) -> str:
    composite = float(lead.get("composite_score") or 0)
    heat = lead.get("heat_score") or lead.get("community_heat_score") or "?"
    subreddit = lead.get("subreddit") or lead.get("community_name") or "unknown"
    city = lead.get("city_signal") or "city unknown"
    magnet = lead.get("lead_magnet_match") or "no assessment match"
    body_preview = (lead.get("body") or "")[:300]
    if len(lead.get("body") or "") > 300:
        body_preview += "..."

    lines = [
        DIVIDER,
        f"[SIGNAL: {_signal_strength(composite)} | Score: {composite}]",
        f"Community: r/{subreddit} 🔥 {heat}/10",
        f"Domain: {lead.get('domain_id') or 'unknown'}",
        f"📍 {city}",
        f"🎯 {magnet}",
        DIVIDER,
        "THEIR POST:",
        f'"{body_preview}"',
        "",
        f"AI SUMMARY: {lead.get('ai_summary') or '(none)'}",
        "",
        "DRAFTED REPLY — EDIT BEFORE POSTING:",
        lead.get("drafted_reply") or "(no draft — run reply crafter)",
        "",
        f"→ POST HERE: {lead.get('url') or '(no url)'}",
        DIVIDER,
    ]
    return "\n".join(lines)


def _sendgrid_available() -> bool:
    return bool(os.getenv("SENDGRID_API_KEY"))


def _twilio_available() -> bool:
    return all([
        os.getenv("TWILIO_ACCOUNT_SID"),
        os.getenv("TWILIO_AUTH_TOKEN"),
        os.getenv("TWILIO_FROM_NUMBER"),
        os.getenv("NOTIFICATION_PHONE"),
    ])


def _send_email(subject: str, body: str) -> bool:
    """Send plain-text email via SendGrid. Returns True on success."""
    try:
        from sendgrid import SendGridAPIClient
        from sendgrid.helpers.mail import Mail

        message = Mail(
            from_email=os.getenv("NOTIFICATION_EMAIL"),
            to_emails=os.getenv("NOTIFICATION_EMAIL"),
            subject=subject,
            plain_text_content=body,
        )
        sg = SendGridAPIClient(os.getenv("SENDGRID_API_KEY"))
        response = sg.send(message)
        if response.status_code not in (200, 201, 202):
            logger.error(
                "SendGrid returned unexpected status %s", response.status_code
            )
            return False
        logger.info("Email sent: %s", subject)
        return True
    except Exception as exc:
        logger.error("SendGrid send failed: %s", exc)
        return False


# ---------------------------------------------------------------------------
# Notification type 1 — daily digest
# ---------------------------------------------------------------------------

def send_daily_digest() -> bool:
    """Send (or print) a digest of all unnotified leads, grouped by domain."""
    try:
        min_score = float(os.getenv("COMPOSITE_THRESHOLD", "6.5"))
        all_leads = db.get_unnotified_leads(min_score=min_score)
    except Exception as exc:
        logger.error("Could not fetch unnotified leads: %s", exc)
        return False

    if not all_leads:
        logger.info("No unnotified leads — nothing to send")
        print("No unnotified leads — nothing to send")
        return True

    # Sort by composite DESC, take up to DIGEST_LIMIT
    sorted_leads = sorted(
        all_leads,
        key=lambda l: float(l.get("composite_score") or 0),
        reverse=True,
    )
    overflow = max(0, len(sorted_leads) - DIGEST_LIMIT)
    digest_leads = sorted_leads[:DIGEST_LIMIT]

    today_str = date.today().isoformat()
    subject = f"Mingus Leads — {len(digest_leads)} new discussions found ({today_str})"

    # Group by domain
    from collections import defaultdict
    by_domain: dict = defaultdict(list)
    for lead in digest_leads:
        domain = lead.get("domain_id") or "unknown"
        by_domain[domain].append(lead)

    body_parts = [f"Mingus Daily Lead Digest — {today_str}", ""]
    for domain, leads in by_domain.items():
        body_parts.append(f"=== {domain.upper()} ({len(leads)} signal{'s' if len(leads) != 1 else ''}) ===")
        body_parts.append("")
        for lead in leads:
            body_parts.append(_format_lead_block(lead))
            body_parts.append("")

    if overflow:
        body_parts.append(f"+{overflow} more lead{'s' if overflow != 1 else ''} available in dashboard")

    body = "\n".join(body_parts)

    if not _sendgrid_available():
        print(body)
        logger.info("SENDGRID_API_KEY not set — digest printed to console")
        # Still mark as notified so they don't pile up
        lead_ids = [str(l["id"]) for l in digest_leads if l.get("id")]
        try:
            db.mark_notified(lead_ids)
        except Exception as exc:
            logger.error("mark_notified failed: %s", exc)
        return True

    success = _send_email(subject, body)
    if success:
        lead_ids = [str(l["id"]) for l in digest_leads if l.get("id")]
        try:
            db.mark_notified(lead_ids)
        except Exception as exc:
            logger.error("mark_notified failed after send: %s", exc)
    return success


# ---------------------------------------------------------------------------
# Notification type 2 — weekly ads brief email
# ---------------------------------------------------------------------------

def send_weekly_ads_brief(brief_dict: dict) -> bool:
    """Email (or print) the weekly Reddit Ads brief."""
    try:
        from pipeline.ads_brief import export_brief_markdown

        filepath = export_brief_markdown(brief_dict)
        with open(filepath, "r", encoding="utf-8") as fh:
            body = fh.read()
    except Exception as exc:
        logger.error("Could not render brief markdown: %s", exc)
        return False

    today_str = date.today().isoformat()
    subject = f"Mingus Ads Brief — Week of {today_str} | Ready to activate"
    footer = "\n\nLog in to ads.reddit.com to activate this brief."
    body = body + footer

    if not _sendgrid_available():
        print(body)
        logger.info("SENDGRID_API_KEY not set — ads brief printed to console")
        return True

    return _send_email(subject, body)


# ---------------------------------------------------------------------------
# Notification type 3 — hot lead SMS
# ---------------------------------------------------------------------------

def send_hot_lead_sms(lead: dict) -> bool:
    """Send a Twilio SMS for a hot lead. Falls back to logging if not configured."""
    composite = float(lead.get("composite_score") or 0)
    subreddit = lead.get("subreddit") or lead.get("community_name") or "unknown"
    domain = lead.get("domain_id") or "unknown"
    city = lead.get("city_signal") or "no city"
    url = lead.get("url") or ""

    # Truncate URL if needed to keep SMS under 160 chars
    sms_text = (
        f"MINGUS HOT LEAD {composite}/10 | r/{subreddit} | {domain} | "
        f"{city} | {url}"
    )[:160]

    if not _twilio_available():
        logger.info(
            "Twilio not configured — hot lead logged: score=%s r/%s %s",
            composite,
            subreddit,
            url,
        )
        return True

    try:
        from twilio.rest import Client

        client = Client(
            os.getenv("TWILIO_ACCOUNT_SID"),
            os.getenv("TWILIO_AUTH_TOKEN"),
        )
        message = client.messages.create(
            body=sms_text,
            from_=os.getenv("TWILIO_FROM_NUMBER"),
            to=os.getenv("NOTIFICATION_PHONE"),
        )
        logger.info("Hot lead SMS sent: sid=%s", message.sid)
        return True
    except Exception as exc:
        logger.error("Twilio SMS failed: %s", exc)
        return False


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main():
    result = send_daily_digest()
    leads = db.get_unnotified_leads(
        min_score=float(os.getenv("COMPOSITE_THRESHOLD", "6.5"))
    )
    if not leads:
        # Already printed inside send_daily_digest
        pass
    elif result:
        if _sendgrid_available():
            print("Digest sent")
        else:
            print("Digest printed to console")
    else:
        print("Digest failed — check logs")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    main()
