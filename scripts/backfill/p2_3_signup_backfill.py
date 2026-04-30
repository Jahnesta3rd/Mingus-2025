#!/usr/bin/env python3
"""
P2.3 signup structural backfill: ensure legacy users have user_profiles + onboarding_progress
rows matching P2.1 atomic registration behavior.

Usage:
  python3 scripts/backfill/p2_3_signup_backfill.py           # dry-run (default)
  python3 scripts/backfill/p2_3_signup_backfill.py --dry-run
  python3 scripts/backfill/p2_3_signup_backfill.py --execute

Requires DATABASE_URL (same as the Flask app). Loads .env from repo root and backend/.env.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from datetime import datetime
from typing import Any, NamedTuple, Sequence

# Repo root: .../mingus (parent of scripts/)
_REPO_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), os.pardir, os.pardir)
)
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

os.chdir(_REPO_ROOT)

from dotenv import load_dotenv  # noqa: E402

load_dotenv()
_backend_env = os.path.join(_REPO_ROOT, "backend", ".env")
if os.path.isfile(_backend_env):
    load_dotenv(_backend_env, override=True)

from flask import Flask  # noqa: E402
from sqlalchemy import Column, DateTime, Integer, MetaData, Table, Text, func, select, text  # noqa: E402
from sqlalchemy.dialects.postgresql import JSONB, insert as pg_insert  # noqa: E402

from backend.constants.onboarding import MODULE_ORDER  # noqa: E402
from backend.models.database import db, init_database  # noqa: E402

logger = logging.getLogger(__name__)

_USER_PROFILES = Table(
    "user_profiles",
    MetaData(),
    Column("id", Integer),
    Column("email", Text),
    Column("first_name", Text),
    Column("personal_info", Text),
    Column("financial_info", Text),
    Column("monthly_expenses", Text),
    Column("important_dates", Text),
    Column("health_wellness", Text),
    Column("goals", Text),
    Column("created_at", DateTime),
    Column("updated_at", DateTime),
)

_ONBOARDING_PROGRESS = Table(
    "onboarding_progress",
    MetaData(),
    Column("user_id", Integer, primary_key=True),
    Column("completed_modules", JSONB),
    Column("skipped_modules", JSONB),
    Column("current_module", Text),
    Column("started_at", DateTime),
    Column("completed_at", DateTime),
    Column("last_activity_at", DateTime),
)

# Same join semantics as scripts/diagnostics/user_state_audit.sql
_CANDIDATE_SQL = text(
    """
    SELECT
        u.id AS user_id,
        u.email AS user_email,
        u.first_name AS user_first_name,
        up.user_profile_id,
        (op.user_id IS NOT NULL) AS has_onboarding
    FROM users u
    LEFT JOIN LATERAL (
        SELECT p.id AS user_profile_id
        FROM user_profiles p
        WHERE lower(btrim(p.email)) = lower(btrim(u.email))
        ORDER BY p.id
        LIMIT 1
    ) up ON TRUE
    LEFT JOIN onboarding_progress op
        ON op.user_id = u.id
    WHERE up.user_profile_id IS NULL OR op.user_id IS NULL
    ORDER BY u.id
    """
)


class CandidateRow(NamedTuple):
    user_id: int
    email: str
    first_name: str | None
    profile_id: int | None
    has_onboarding: bool


def _personal_info_json(first_name_from_user: str | None) -> str:
    fn = (first_name_from_user or "").strip()
    payload = {
        "firstName": fn,
        "lastName": "",
        "dateOfBirth": "",
        "employmentStatus": "",
        "occupation": "",
        "city": "",
        "state": "",
        "zip": "",
        "phone": "",
    }
    return json.dumps(payload)


def _norm_email(email: str) -> str:
    return (email or "").strip().lower()


def _fetch_profile_id_by_email(session: Any, email: str) -> int | None:
    row = session.execute(
        select(_USER_PROFILES.c.id)
        .where(
            func.lower(func.btrim(_USER_PROFILES.c.email))
            == func.lower(func.btrim(email))
        )
        .order_by(_USER_PROFILES.c.id)
        .limit(1)
    ).first()
    return int(row[0]) if row else None


def _run_backfill(execute: bool) -> None:
    mode_label = "execute" if execute else "dry_run"

    app = Flask(__name__)
    init_database(app)

    users_processed = 0
    profiles_inserted = 0
    onboarding_inserted = 0

    with app.app_context():
        result = db.session.execute(_CANDIDATE_SQL)
        raw_rows: Sequence[Any] = result.mappings().all()
        candidates: list[CandidateRow] = []
        for r in raw_rows:
            candidates.append(
                CandidateRow(
                    user_id=int(r["user_id"]),
                    email=str(r["user_email"]),
                    first_name=r["user_first_name"],
                    profile_id=(
                        int(r["user_profile_id"])
                        if r["user_profile_id"] is not None
                        else None
                    ),
                    has_onboarding=bool(r["has_onboarding"]),
                )
            )

        if not execute:
            for c in candidates:
                users_processed += 1
                profile_needed = c.profile_id is None
                onboarding_needed = not c.has_onboarding
                logger.info(
                    "backfill_planned user_id=%s email=%s profile_needed=%s "
                    "onboarding_needed=%s",
                    c.user_id,
                    c.email,
                    profile_needed,
                    onboarding_needed,
                )
                if profile_needed:
                    profiles_inserted += 1
                if onboarding_needed:
                    onboarding_inserted += 1
        else:
            try:
                now = datetime.utcnow()
                for c in candidates:
                    users_processed += 1
                    profile_needed = c.profile_id is None
                    onboarding_needed = not c.has_onboarding
                    logger.info(
                        "backfill_planned user_id=%s email=%s profile_needed=%s "
                        "onboarding_needed=%s",
                        c.user_id,
                        c.email,
                        profile_needed,
                        onboarding_needed,
                    )

                    email_norm = _norm_email(c.email)
                    first_name_col = (c.first_name or "").strip()

                    prof_rows = 0
                    if profile_needed:
                        res = db.session.execute(
                            pg_insert(_USER_PROFILES)
                            .values(
                                email=email_norm,
                                first_name=first_name_col,
                                personal_info=_personal_info_json(c.first_name),
                                financial_info="{}",
                                monthly_expenses="{}",
                                important_dates="{}",
                                health_wellness="{}",
                                goals="{}",
                                created_at=now,
                                updated_at=now,
                            )
                            .on_conflict_do_nothing(
                                index_elements=[_USER_PROFILES.c.email],
                            )
                        )
                        prof_rows = int(res.rowcount or 0)
                        profiles_inserted += prof_rows

                    onboard_rows = 0
                    if onboarding_needed:
                        res = db.session.execute(
                            pg_insert(_ONBOARDING_PROGRESS)
                            .values(
                                user_id=c.user_id,
                                completed_modules=[],
                                skipped_modules=[],
                                current_module=MODULE_ORDER[0],
                                started_at=now,
                                completed_at=None,
                                last_activity_at=now,
                            )
                            .on_conflict_do_nothing(
                                index_elements=[_ONBOARDING_PROGRESS.c.user_id],
                            )
                        )
                        onboard_rows = int(res.rowcount or 0)
                        onboarding_inserted += onboard_rows

                    profile_pk = _fetch_profile_id_by_email(db.session, c.email)
                    if profile_pk is None:
                        raise RuntimeError(
                            f"Expected user_profiles row for email={c.email!r} after backfill"
                        )

                    if prof_rows and onboard_rows:
                        action = "both"
                    elif prof_rows:
                        action = "insert_profile"
                    elif onboard_rows:
                        action = "insert_onboarding"
                    else:
                        action = "skipped"

                    logger.info(
                        "backfill_complete user_id=%s profile_id=%s email=%s action=%s",
                        c.user_id,
                        profile_pk,
                        c.email,
                        action,
                    )

                db.session.commit()
            except Exception:
                db.session.rollback()
                raise

    logger.info(
        "backfill_summary users_processed=%s profiles_inserted=%s "
        "onboarding_inserted=%s mode=%s",
        users_processed,
        profiles_inserted,
        onboarding_inserted,
        mode_label,
    )


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s %(name)s %(message)s",
    )
    parser = argparse.ArgumentParser(
        description="Backfill user_profiles and onboarding_progress for pre-P2.1 users.",
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--dry-run",
        action="store_true",
        help="Print planned work only (default).",
    )
    group.add_argument(
        "--execute",
        action="store_true",
        help="Insert missing rows; one commit for the full run, rollback on any error.",
    )
    args = parser.parse_args()
    if args.execute:
        _run_backfill(execute=True)
    else:
        _run_backfill(execute=False)


if __name__ == "__main__":
    main()
