#!/usr/bin/env python3
"""Flask CLI command for daily WARN Act layoff notice scanning."""

from __future__ import annotations

import logging
import re
import sys
import time
from datetime import date, timedelta
from decimal import Decimal

import click
from flask.cli import with_appcontext
from rapidfuzz import fuzz

from backend.models.career_profile import CareerProfile
from backend.models.database import db
from backend.models.employer import Employer, LayoffEvent
from backend.models.user_models import User
from backend.services.insurance_plan_scorer import ZIP_TO_STATE
from backend.services.warn_act_client import WarnActClient
from backend.utils.user_profile_context import resolve_user_zip_code

logger = logging.getLogger(__name__)


def _pad_cik(cik: str) -> str:
    return str(cik).strip().zfill(10)


def _resolve_user_state(user: User) -> str | None:
    zip_code = resolve_user_zip_code(user)
    if not zip_code:
        return None
    return ZIP_TO_STATE.get(zip_code)


def _get_or_create_employer(cik: str, name: str | None = None) -> Employer:
    cik_padded = _pad_cik(cik)
    employer = db.session.query(Employer).filter_by(cik=cik_padded).first()
    if employer is None:
        employer = Employer(cik=cik_padded, name=name or "Unknown")
        db.session.add(employer)
        db.session.flush()
    elif name and employer.name != name:
        employer.name = name
    return employer


def _resolve_employer_by_name(company_name: str) -> tuple[Employer | None, int]:
    best_employer: Employer | None = None
    best_score = 0
    for employer in db.session.query(Employer).all():
        score = fuzz.WRatio(company_name, employer.name)
        if score > best_score:
            best_score = score
            best_employer = employer
    if best_employer is None or best_score < 75:
        return None, best_score
    return best_employer, best_score


def _warn_accession(state: str, filing_date: date, company_name: str) -> str:
    slug = re.sub(r"[^a-z0-9]", "", company_name.lower())[:10] or "warn"
    value = f"warn-{state}-{filing_date.isoformat()}-{slug}"
    return value[:25]


def _review_state_for_score(match_score: int) -> str | None:
    if match_score == 100:
        return None
    if match_score < 85:
        return "needs_review"
    return None


def _confidence_for_score(match_score: int) -> Decimal:
    return Decimal(str(round(min(max(match_score, 0), 100) / 100, 3)))


def _layoff_event_exists(
    *,
    employer_id: int,
    filing_date: date,
) -> bool:
    return (
        db.session.query(LayoffEvent.id)
        .filter_by(
            employer_id=employer_id,
            filing_date=filing_date,
            source="warn_act",
        )
        .first()
        is not None
    )


def _insert_warn_layoff_event(
    *,
    employer_id: int,
    filing_date: date,
    worker_count: int,
    state: str,
    company_name: str,
    notice_url: str | None,
    layoff_type: str,
    review_state: str | None,
    match_score: int,
) -> LayoffEvent:
    excerpt_parts = [f"type={layoff_type}", f"state={state}", f"match_score={match_score}"]
    if notice_url:
        excerpt_parts.append(f"url={notice_url}")

    event = LayoffEvent(
        employer_id=employer_id,
        filing_date=filing_date,
        accession_number=_warn_accession(state, filing_date, company_name),
        item_number="warn",
        affected_count=worker_count or None,
        confidence=_confidence_for_score(match_score),
        raw_excerpt="; ".join(excerpt_parts)[:500],
        source="warn_act",
        review_state=review_state,
        expires_at=filing_date + timedelta(days=90),
    )
    db.session.add(event)
    return event


def _career_profiles(user_id: int | None) -> list[CareerProfile]:
    query = db.session.query(CareerProfile)
    if user_id is not None:
        query = query.filter_by(user_id=user_id)
    return query.all()


@click.command("scan-warn-notices")
@click.option("--user-id", type=int, default=None, help="Run for one user only.")
@click.option("--days-back", type=int, default=90, show_default=True, help="Look-back window.")
@click.option("--dry-run", is_flag=True, default=False, help="Log matches without inserting.")
@click.option("--verbose", is_flag=True, default=False, help="Log every match score.")
@with_appcontext
def scan_warn_notices(user_id, days_back, dry_run, verbose):
    """Scan WARN Act notices for users with career profiles."""
    start = time.monotonic()
    client = WarnActClient()

    profiles = _career_profiles(user_id)
    if not profiles:
        click.echo("No career profiles to scan.")
        sys.exit(0)

    totals = {
        "users": 0,
        "matched": 0,
        "inserted": 0,
        "skipped_exists": 0,
        "below_threshold": 0,
        "unresolved_employer": 0,
        "errors": 0,
    }

    for profile in profiles:
        totals["users"] += 1
        user = profile.user or db.session.get(User, profile.user_id)
        if user is None:
            continue

        user_state = _resolve_user_state(user)
        user_stats = {
            "matched": 0,
            "inserted": 0,
            "skipped_exists": 0,
            "below_threshold": 0,
            "unresolved_employer": 0,
        }

        candidates: list[tuple[dict, int, Employer | None]] = []

        if profile.employer_cik:
            cik = _pad_cik(profile.employer_cik)
            try:
                for result in client.search_by_cik_crossref(cik):
                    employer = _get_or_create_employer(
                        cik,
                        name=result.get("company_name") or profile.employer_name_text,
                    )
                    candidates.append((result, 100, employer))
            except Exception as exc:
                totals["errors"] += 1
                logger.exception("CIK WARN scan failed for user %s: %s", user.id, exc)

        if profile.employer_name_text:
            try:
                for result in client.search_by_name(
                    profile.employer_name_text,
                    state=user_state,
                    days_back=days_back,
                ):
                    score = int(
                        round(
                            fuzz.WRatio(
                                profile.employer_name_text,
                                result["company_name"],
                            )
                        )
                    )
                    if verbose:
                        click.echo(
                            f"user={user.id} name={profile.employer_name_text!r} "
                            f"result={result['company_name']!r} score={score}"
                        )
                    if score < 75:
                        user_stats["below_threshold"] += 1
                        totals["below_threshold"] += 1
                        continue

                    employer = None
                    if profile.employer_cik:
                        employer = _get_or_create_employer(
                            profile.employer_cik,
                            name=result.get("company_name"),
                        )
                    else:
                        employer, _ = _resolve_employer_by_name(result["company_name"])

                    candidates.append((result, score, employer))
            except Exception as exc:
                totals["errors"] += 1
                logger.exception("Name WARN scan failed for user %s: %s", user.id, exc)

        for result, match_score, employer in candidates:
            user_stats["matched"] += 1
            totals["matched"] += 1

            if employer is None:
                user_stats["unresolved_employer"] += 1
                totals["unresolved_employer"] += 1
                logger.info(
                    "user=%s WARN match unresolved employer=%r score=%s",
                    user.id,
                    result.get("company_name"),
                    match_score,
                )
                continue

            filing_date = result["filing_date"]
            if _layoff_event_exists(employer_id=employer.id, filing_date=filing_date):
                user_stats["skipped_exists"] += 1
                totals["skipped_exists"] += 1
                continue

            review_state = _review_state_for_score(match_score)
            if dry_run:
                user_stats["inserted"] += 1
                totals["inserted"] += 1
                click.echo(
                    f"[dry run] user={user.id} employer_id={employer.id} "
                    f"company={result['company_name']!r} filing_date={filing_date} "
                    f"score={match_score} review_state={review_state!r}"
                )
                continue

            try:
                _insert_warn_layoff_event(
                    employer_id=employer.id,
                    filing_date=filing_date,
                    worker_count=result.get("worker_count", 0),
                    state=result.get("state", ""),
                    company_name=result["company_name"],
                    notice_url=result.get("notice_url"),
                    layoff_type=result.get("layoff_type", "unknown"),
                    review_state=review_state,
                    match_score=match_score,
                )
                db.session.commit()
                user_stats["inserted"] += 1
                totals["inserted"] += 1
                logger.info(
                    "user=%s inserted WARN layoff employer_id=%s filing_date=%s "
                    "match_score=%s review_state=%r",
                    user.id,
                    employer.id,
                    filing_date,
                    match_score,
                    review_state,
                )
            except Exception as exc:
                totals["errors"] += 1
                db.session.rollback()
                logger.exception(
                    "Failed inserting WARN layoff for user %s: %s",
                    user.id,
                    exc,
                )

        click.echo(
            f"user={user.id}: matched={user_stats['matched']} "
            f"inserted={user_stats['inserted']} "
            f"skipped_exists={user_stats['skipped_exists']} "
            f"below_threshold={user_stats['below_threshold']} "
            f"unresolved_employer={user_stats['unresolved_employer']}"
        )

    elapsed = time.monotonic() - start
    click.echo(
        f"Summary: users={totals['users']} matched={totals['matched']} "
        f"inserted={totals['inserted']} skipped_exists={totals['skipped_exists']} "
        f"below_threshold={totals['below_threshold']} "
        f"unresolved_employer={totals['unresolved_employer']} "
        f"errors={totals['errors']} elapsed={elapsed:.1f}s"
        + (" (dry run — no DB writes)" if dry_run else "")
    )
    sys.exit(1 if totals["errors"] else 0)
