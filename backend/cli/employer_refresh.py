#!/usr/bin/env python3
"""Flask CLI commands for employer health refresh and 8-K layoff scanning (CR9c)."""

from __future__ import annotations

import logging
import re
import sys
import time
from datetime import date, datetime, timedelta

import click
from flask import Flask
from flask.cli import with_appcontext

from backend.models.career_profile import CareerProfile
from backend.models.database import db
from backend.models.employer import Employer, LayoffEvent
from backend.services.employer_health_scoring import (
    compute_health_scores,
    get_latest_snapshot,
    refresh_employer_health,
)
from backend.services.sec_edgar_client import SecEdgarClient

logger = logging.getLogger(__name__)

AFFECTED_COUNT_RE = re.compile(
    r"(\d[\d,]*)\s*(employees|workers|positions|jobs)",
    re.IGNORECASE,
)
LAYOFF_KEYWORDS_HIGH = (
    "workforce reduction",
    "reduction in force",
    "layoff",
)
LAYOFF_KEYWORD_MED = "restructuring"
ITEM_205_RE = re.compile(r"item\s+2\.05", re.IGNORECASE)


def _pad_cik(cik: str) -> str:
    return str(cik).strip().zfill(10)


def _distinct_user_employer_ciks() -> list[str]:
    rows = (
        db.session.query(CareerProfile.employer_cik)
        .filter(CareerProfile.employer_cik.isnot(None))
        .distinct()
        .all()
    )
    return [_pad_cik(row[0]) for row in rows if row[0]]


def _parse_affected_count(text: str) -> int | None:
    match = AFFECTED_COUNT_RE.search(text)
    if not match:
        return None
    try:
        return int(match.group(1).replace(",", ""))
    except ValueError:
        return None


def _compute_layoff_confidence(item_text: str) -> float:
    lowered = item_text.lower()
    if any(kw in lowered for kw in LAYOFF_KEYWORDS_HIGH):
        return 1.0
    if LAYOFF_KEYWORD_MED in lowered:
        return 0.7
    if ITEM_205_RE.search(item_text):
        return 0.5
    return 0.0


def _extract_item_205_excerpt(filing_text: str, max_len: int = 500) -> str:
    match = ITEM_205_RE.search(filing_text)
    if not match:
        return filing_text[:max_len]
    start = match.start()
    return filing_text[start:start + max_len]


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


def _mark_snapshot_fresh(employer_id: int) -> None:
    snapshot = get_latest_snapshot(employer_id, db_session=db.session)
    if snapshot is not None:
        snapshot.is_stale = False
        snapshot.refreshed_at = datetime.utcnow()


def register_employer_cli(app: Flask) -> None:
    """Register employer refresh CLI commands on the Flask app."""

    @app.cli.command("refresh-employer-data")
    @click.option("--cik", default=None, help="Refresh a single CIK. Omit to refresh all.")
    @click.option(
        "--dry-run",
        is_flag=True,
        default=False,
        help="Fetch and score but do not write to DB.",
    )
    @click.option("--verbose", is_flag=True, default=False)
    @with_appcontext
    def refresh_employer_data(cik, dry_run, verbose):
        """Refresh SEC EDGAR employer health snapshots."""
        start = time.monotonic()
        client = SecEdgarClient()

        if cik:
            ciks = [_pad_cik(cik)]
        else:
            ciks = _distinct_user_employer_ciks()

        refreshed = 0
        skipped = 0
        errors = 0

        if not ciks:
            click.echo("No employer CIKs to refresh.")
            sys.exit(0)

        for employer_cik in ciks:
            try:
                if dry_run:
                    facts = client.get_company_facts(employer_cik)
                    if facts is None:
                        skipped += 1
                        if verbose:
                            click.echo(f"{employer_cik}: skipped (no facts)")
                        continue
                    scores = compute_health_scores(facts)
                    refreshed += 1
                    click.echo(
                        f"[dry run] {employer_cik} score={scores['score']:.1f} "
                        f"components="
                        f"rev={scores['revenue_delta_score']:.0f} "
                        f"margin={scores['margin_score']:.0f} "
                        f"fcf={scores['fcf_score']:.0f} "
                        f"runway={scores['runway_score']:.0f} "
                        f"leverage={scores['leverage_score']:.0f}"
                    )
                else:
                    snapshot = refresh_employer_health(employer_cik, db_session=db.session)
                    if snapshot is None:
                        skipped += 1
                        if verbose:
                            click.echo(f"{employer_cik}: skipped")
                    else:
                        refreshed += 1
                        if verbose:
                            click.echo(
                                f"{employer_cik}: score={float(snapshot.score or 0):.1f} "
                                f"refreshed_at={snapshot.refreshed_at}"
                            )
            except Exception as exc:
                errors += 1
                logger.exception("Error refreshing CIK %s: %s", employer_cik, exc)
                if verbose:
                    click.echo(f"{employer_cik}: ERROR {exc}")

        elapsed = time.monotonic() - start
        click.echo(
            f"Summary: {refreshed} refreshed, {skipped} skipped, "
            f"{errors} errors, {elapsed:.1f}s elapsed"
            + (" (dry run — no DB writes)" if dry_run else "")
        )
        sys.exit(1 if errors else 0)

    @app.cli.command("scan-8k-layoff-events")
    @click.option(
        "--days",
        default=1,
        help="Number of days back to scan. Default: 1 (yesterday).",
    )
    @click.option("--dry-run", is_flag=True, default=False)
    @click.option("--verbose", is_flag=True, default=False)
    @with_appcontext
    def scan_8k_layoff_events(days, dry_run, verbose):
        """Scan 8-K filings for Item 2.05 layoff disclosures."""
        start = time.monotonic()
        client = SecEdgarClient()

        end_date = date.today()
        start_date = end_date - timedelta(days=int(days))

        user_ciks = set(_distinct_user_employer_ciks())
        hits = client.search_8k_layoff_filings(start_date, end_date)

        scanned = len(hits)
        matched = 0
        upserted = 0
        errors = 0

        for hit in hits:
            hit_cik = _pad_cik(hit.get("cik", ""))
            if hit_cik not in user_ciks:
                continue

            matched += 1
            accession = hit.get("accession")
            if not accession:
                continue

            try:
                filing_text = client.fetch_filing_text(hit_cik, accession)
                if not filing_text:
                    if verbose:
                        click.echo(f"{hit_cik} {accession}: no filing text")
                    continue

                excerpt = _extract_item_205_excerpt(filing_text)
                confidence = _compute_layoff_confidence(excerpt)
                if confidence < 0.5:
                    if verbose:
                        click.echo(
                            f"{hit_cik} {accession}: confidence {confidence} below threshold"
                        )
                    continue

                filing_date_raw = hit.get("filed")
                try:
                    filing_date = (
                        datetime.strptime(filing_date_raw, "%Y-%m-%d").date()
                        if filing_date_raw
                        else start_date
                    )
                except (TypeError, ValueError):
                    filing_date = start_date

                affected_count = _parse_affected_count(excerpt)
                entity_name = hit.get("entity_name")

                if dry_run:
                    upserted += 1
                    click.echo(
                        f"[dry run] layoff match {hit_cik} {accession} "
                        f"confidence={confidence:.2f} "
                        f"affected={affected_count}"
                    )
                    continue

                employer = _get_or_create_employer(hit_cik, name=entity_name)
                existing = (
                    db.session.query(LayoffEvent)
                    .filter_by(
                        employer_id=employer.id,
                        accession_number=accession,
                    )
                    .first()
                )
                if existing is None:
                    event = LayoffEvent(
                        employer_id=employer.id,
                        filing_date=filing_date,
                        accession_number=accession,
                        affected_count=affected_count,
                        confidence=confidence,
                        raw_excerpt=excerpt[:500],
                        review_state="auto",
                        expires_at=filing_date + timedelta(days=90),
                    )
                    db.session.add(event)
                else:
                    existing.filing_date = filing_date
                    existing.affected_count = affected_count
                    existing.confidence = confidence
                    existing.raw_excerpt = excerpt[:500]
                    existing.review_state = "auto"
                    existing.expires_at = filing_date + timedelta(days=90)

                _mark_snapshot_fresh(employer.id)
                db.session.commit()
                upserted += 1
                if verbose:
                    click.echo(f"upserted layoff {hit_cik} {accession}")
            except Exception as exc:
                errors += 1
                logger.exception("8-K scan error for %s: %s", hit_cik, exc)
                db.session.rollback()
                if verbose:
                    click.echo(f"ERROR {hit_cik}: {exc}")

        elapsed = time.monotonic() - start
        click.echo(
            f"Summary: {scanned} filings scanned, {matched} matched our employers, "
            f"{upserted} layoff events upserted, {errors} errors, {elapsed:.1f}s elapsed"
            + (" (dry run — no DB writes)" if dry_run else "")
        )
        sys.exit(1 if errors else 0)
