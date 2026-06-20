#!/usr/bin/env python3
"""Apply Alembic migrations using DATABASE_URL (no alembic.ini required in CI)."""

from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from tests.db_helpers import ensure_libpq_env, get_test_database_uri, run_alembic_migrations  # noqa: E402


def main() -> int:
    if not os.environ.get("DATABASE_URL"):
        os.environ["DATABASE_URL"] = get_test_database_uri()
    ensure_libpq_env()
    run_alembic_migrations()
    print("Alembic migrations applied (head)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
