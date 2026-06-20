#!/usr/bin/env python3
"""Apply Alembic migrations using DATABASE_URL (production/local use)."""

from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from tests.db_helpers import (  # noqa: E402
    ensure_libpq_env,
    get_test_database_uri,
    run_alembic_migrations,
    verify_users_table,
)


def main() -> int:
    url = os.environ.get("DATABASE_URL")
    if not url:
        os.environ["DATABASE_URL"] = get_test_database_uri()
    ensure_libpq_env()

    print(f"Running Alembic upgrade against {os.environ['DATABASE_URL']}")
    try:
        run_alembic_migrations()
    except Exception as exc:
        print(f"Alembic upgrade failed: {exc}", file=sys.stderr)
        return 1

    try:
        verify_users_table()
    except Exception as exc:
        print(f"Post-migration verification failed: {exc}", file=sys.stderr)
        print(
            "Hint: no Alembic revision creates public.users; bootstrap with "
            "scripts/ci_init_test_db.py or create_all before upgrade.",
            file=sys.stderr,
        )
        return 1

    print("Alembic migrations applied (head)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
