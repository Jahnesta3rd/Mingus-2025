#!/usr/bin/env python3
"""Batch beta invite preparation, Celery dispatch, and wave status."""

from __future__ import annotations

from datetime import timezone
from typing import Any

from sqlalchemy import func

from backend.models.beta_code import BetaCode
from backend.models.beta_invite_log import BetaInviteLog
from backend.models.database import db


class BetaInviteService:
    """Queue and send beta invitation emails backed by ``beta_invite_log``."""

    @staticmethod
    def prepare_wave(
        wave_label: str,
        recipient_list: list[dict[str, Any]],
        *,
        dry_run: bool = False,
    ) -> dict[str, Any]:
        """
        Validate recipients and optionally insert ``queued`` rows.

        recipient_list items: {"email": str, "first_name": str, "code": str}

        Returns:
            {"valid": list, "skipped": list, "reason": str}
        """
        wave_label = (wave_label or "").strip()
        valid: list[dict[str, Any]] = []
        skipped: list[dict[str, Any]] = []

        seen_emails: set[str] = set()
        seen_codes: set[str] = set()

        for raw in recipient_list:
            email = (raw.get("email") or "").strip()
            first_name = (raw.get("first_name") or "").strip()
            code = (raw.get("code") or "").strip()
            email_key = email.lower()

            base = {"email": email, "first_name": first_name, "code": code}

            if not email or not code:
                skipped.append({**base, "reason": "missing_email_or_code"})
                continue

            if email_key in seen_emails:
                skipped.append({**base, "reason": "duplicate_email_in_batch"})
                continue
            if code in seen_codes:
                skipped.append({**base, "reason": "duplicate_code_in_batch"})
                continue

            bc = BetaCode.query.filter_by(code=code).first()
            if not bc or bc.status != "available":
                skipped.append({**base, "reason": "invalid_or_unavailable_code"})
                continue

            dup = (
                BetaInviteLog.query.filter(
                    func.lower(BetaInviteLog.email) == email_key,
                    BetaInviteLog.status.in_(("sent", "queued")),
                ).first()
            )
            if dup:
                skipped.append({**base, "reason": "already_invited"})
                continue

            seen_emails.add(email_key)
            seen_codes.add(code)

            if dry_run:
                valid.append(dict(base))
            else:
                row = BetaInviteLog(
                    email=email,
                    first_name=first_name or None,
                    code=code,
                    wave_label=wave_label,
                    status="queued",
                )
                db.session.add(row)
                db.session.flush()
                valid.append({**base, "log_id": row.id})

        if not dry_run and valid:
            db.session.commit()
        elif not dry_run:
            db.session.rollback()

        n_skip = len(skipped)
        n_ok = len(valid)
        reason = (
            f"Prepared {n_ok} invite(s); skipped {n_skip}."
            if n_skip or n_ok
            else "No recipients processed."
        )
        return {"valid": valid, "skipped": skipped, "reason": reason}

    @staticmethod
    def send_wave(wave_label: str, beta_url: str) -> dict[str, Any]:
        from backend.tasks.email_tasks import send_beta_invite_email

        wave_label = (wave_label or "").strip()
        rows = BetaInviteLog.query.filter_by(
            wave_label=wave_label, status="queued"
        ).all()
        for row in rows:
            send_beta_invite_email.delay(row.id, beta_url)
        return {"dispatched": len(rows), "wave": wave_label}

    @staticmethod
    def get_wave_status(wave_label: str) -> dict[str, Any]:
        wave_label = (wave_label or "").strip()
        rows = (
            db.session.query(BetaInviteLog.status, func.count(BetaInviteLog.id))
            .filter(BetaInviteLog.wave_label == wave_label)
            .group_by(BetaInviteLog.status)
            .all()
        )
        counts = {status: int(c) for status, c in rows}
        total = sum(counts.values())
        sent = counts.get("sent", 0)
        failed = counts.get("failed", 0)
        queued = counts.get("queued", 0)

        last = (
            db.session.query(
                func.max(
                    func.coalesce(
                        BetaInviteLog.sent_at, BetaInviteLog.created_at
                    )
                )
            )
            .filter(BetaInviteLog.wave_label == wave_label)
            .scalar()
        )
        last_updated = ""
        if last:
            if getattr(last, "tzinfo", None) is None:
                last_updated = last.replace(tzinfo=timezone.utc).isoformat()
            else:
                last_updated = last.isoformat()

        return {
            "wave": wave_label,
            "total": total,
            "sent": sent,
            "failed": failed,
            "queued": queued,
            "last_updated": last_updated,
        }
