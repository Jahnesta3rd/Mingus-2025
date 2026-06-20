#!/usr/bin/env python3
"""PostgreSQL test database helpers for pytest and unittest suites."""

from __future__ import annotations

import os
import threading
from types import SimpleNamespace

from sqlalchemy import text

DEFAULT_TEST_DATABASE_URL = "postgresql://test:test@localhost:5432/mingus_test"

REQUIRED_CI_TABLES = (
    "users",
    "daily_outlooks",
    "wellness_scores",
    "user_relationship_status",
    "user_housing_preferences",
)

_schema_lock = threading.Lock()
_schema_initialized = False


def ensure_libpq_env() -> None:
    """Set DATABASE_URL and PG* vars so clients never fall back to the OS user."""
    url = get_test_database_uri()
    os.environ["DATABASE_URL"] = url

    try:
        from urllib.parse import urlparse

        parsed = urlparse(url)
        if parsed.username:
            os.environ["PGUSER"] = parsed.username
        if parsed.password:
            os.environ["PGPASSWORD"] = parsed.password
        if parsed.hostname:
            os.environ["PGHOST"] = parsed.hostname
        if parsed.port:
            os.environ["PGPORT"] = str(parsed.port)
        if parsed.path and parsed.path != "/":
            os.environ["PGDATABASE"] = parsed.path.lstrip("/")
    except Exception:
        pass

    os.environ.setdefault("PGUSER", "test")
    os.environ.setdefault("PGPASSWORD", "test")
    os.environ.setdefault("PGHOST", "localhost")
    os.environ.setdefault("PGPORT", "5432")
    os.environ.setdefault("PGDATABASE", "mingus_test")


def get_test_database_uri() -> str:
    """Return the PostgreSQL URL used for tests (CI sets DATABASE_URL)."""
    url = os.environ.get("DATABASE_URL", DEFAULT_TEST_DATABASE_URL)
    if url.startswith("sqlite:"):
        raise RuntimeError(
            "Tests require PostgreSQL (models use JSONB/UUID). "
            f"Got SQLite DATABASE_URL: {url!r}. "
            "Set DATABASE_URL to a postgres URL or start the CI postgres service."
        )
    return url


def persist_test_user(db, **kwargs) -> SimpleNamespace:
    """Insert a user and return scalar fields safe to use outside the session."""
    from backend.models.user_models import User

    user = User(**kwargs)
    db.session.add(user)
    db.session.commit()
    return SimpleNamespace(
        id=user.id,
        user_id=user.user_id,
        email=user.email,
        tier=getattr(user, "tier", None),
    )


def configure_app_for_tests(app) -> None:
    """Apply standard Flask/SQLAlchemy settings for integration tests."""
    app.config["TESTING"] = True
    app.config["SQLALCHEMY_DATABASE_URI"] = get_test_database_uri()
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False


def ensure_all_models_imported() -> None:
    """Load all SQLAlchemy models so create_all() sees every table."""
    import backend.models  # noqa: F401
    import backend.models.professional_tier_models  # noqa: F401
    import backend.models.tax_adjacent_models  # noqa: F401


def ensure_housingtype_enum_values() -> None:
    """Ensure housingtype enum accepts lowercase values used by API/tests."""
    import psycopg2

    ensure_libpq_env()
    conn = psycopg2.connect(os.environ["DATABASE_URL"])
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    DO $$
                    BEGIN
                      IF EXISTS (SELECT 1 FROM pg_type WHERE typname = 'housingtype') THEN
                        BEGIN
                          ALTER TYPE housingtype ADD VALUE IF NOT EXISTS 'apartment';
                        EXCEPTION WHEN duplicate_object THEN NULL;
                        END;
                        BEGIN
                          ALTER TYPE housingtype ADD VALUE IF NOT EXISTS 'house';
                        EXCEPTION WHEN duplicate_object THEN NULL;
                        END;
                        BEGIN
                          ALTER TYPE housingtype ADD VALUE IF NOT EXISTS 'condo';
                        EXCEPTION WHEN duplicate_object THEN NULL;
                        END;
                      END IF;
                    END$$;
                    """
                )
    finally:
        conn.close()


def wait_for_postgres(max_attempts: int = 60, sleep_seconds: float = 2.0) -> None:
    """Block until DATABASE_URL accepts connections."""
    import time
    import psycopg2

    ensure_libpq_env()
    url = os.environ["DATABASE_URL"]
    for attempt in range(1, max_attempts + 1):
        try:
            conn = psycopg2.connect(url)
            conn.close()
            print("Postgres reachable")
            return
        except Exception as exc:
            print(f"waiting for postgres ({attempt}/{max_attempts}): {exc}")
            time.sleep(sleep_seconds)
    raise RuntimeError("Postgres did not become ready in time")


def ensure_root_role() -> None:
    """Create a login role for OS user 'root' when clients omit PGUSER (CI workaround)."""
    import psycopg2

    ensure_libpq_env()
    conn = psycopg2.connect(os.environ["DATABASE_URL"])
    try:
        conn.autocommit = True
        with conn.cursor() as cur:
            cur.execute(
                """
                DO $$
                BEGIN
                  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'root') THEN
                    CREATE ROLE root LOGIN;
                  END IF;
                END$$;
                """
            )
            db_name = os.environ.get("PGDATABASE", "mingus_test")
            cur.execute(
                """
                SELECT EXISTS(
                  SELECT FROM pg_database WHERE datname = %s
                )
                """,
                (db_name,),
            )
            if cur.fetchone()[0]:
                cur.execute(f'GRANT CONNECT ON DATABASE "{db_name}" TO root')
        print("root role ensured")
    finally:
        conn.close()


def verify_ci_schema(required_tables: tuple[str, ...] | None = None) -> None:
    """Fail fast if critical tables are missing after schema init."""
    from sqlalchemy import create_engine, inspect

    ensure_libpq_env()
    tables = required_tables or REQUIRED_CI_TABLES
    engine = create_engine(get_test_database_uri())
    try:
        inspector = inspect(engine)
        missing = [name for name in tables if not inspector.has_table(name)]
    finally:
        engine.dispose()

    if missing:
        raise RuntimeError(
            f"Missing tables after schema init: {missing}. "
            "Run scripts/ci_init_test_db.py or fix Alembic/model bootstrap."
        )
    print(f"Verified CI tables: {', '.join(tables)}")


def verify_users_table() -> None:
    """Fail fast if the users table is missing after schema init."""
    verify_ci_schema(("users",))


def init_ci_database_schema() -> None:
    """Bootstrap CI Postgres: extensions, create_all, then Alembic sync."""
    ensure_libpq_env()
    ensure_postgres_extensions()
    initialize_shared_schema()
    try:
        run_alembic_migrations()
        print("Alembic upgrade head completed")
    except Exception as exc:
        print(f"Alembic upgrade skipped ({exc}); stamping head after create_all")
        stamp_alembic_head()
    verify_ci_schema()


def ensure_postgres_extensions() -> None:
    """Create extensions expected by migrations and UUID defaults."""
    import psycopg2

    ensure_libpq_env()
    conn = psycopg2.connect(os.environ["DATABASE_URL"])
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute('CREATE EXTENSION IF NOT EXISTS "pgcrypto"')
    finally:
        conn.close()


def run_alembic_migrations() -> None:
    """Apply Alembic migrations to head using DATABASE_URL."""
    from alembic import command
    from alembic.config import Config

    ensure_libpq_env()
    url = get_test_database_uri()
    cfg = Config()
    cfg.set_main_option("script_location", "migrations")
    cfg.set_main_option("sqlalchemy.url", url)
    try:
        command.upgrade(cfg, "head")
    except Exception as exc:
        print_alembic_diagnostics(cfg)
        raise RuntimeError(f"Alembic upgrade failed: {exc}") from exc


def stamp_alembic_head() -> None:
    """Mark Alembic at head without running migrations (after create_all in CI)."""
    from alembic import command
    from alembic.config import Config

    ensure_libpq_env()
    cfg = Config()
    cfg.set_main_option("script_location", "migrations")
    cfg.set_main_option("sqlalchemy.url", get_test_database_uri())
    command.stamp(cfg, "head")
    print("Alembic stamped at head")


def print_alembic_diagnostics(cfg) -> None:
    """Print Alembic history/current to stderr for CI debugging."""
    from alembic import command

    print("--- Alembic diagnostics ---", flush=True)
    try:
        command.current(cfg)
    except Exception as exc:
        print(f"alembic current failed: {exc}", flush=True)
    try:
        command.history(cfg, verbose=True)
    except Exception as exc:
        print(f"alembic history failed: {exc}", flush=True)


def initialize_shared_schema(db=None) -> None:
    """Create all tables once per test run (idempotent via checkfirst)."""
    global _schema_initialized
    if _schema_initialized:
        return

    with _schema_lock:
        if _schema_initialized:
            return

        ensure_libpq_env()
        ensure_postgres_extensions()

        from flask import Flask

        if db is None:
            from backend.models.database import db as db_instance

            db = db_instance

        app = Flask("test_schema_init")
        configure_app_for_tests(app)
        ensure_all_models_imported()
        db.init_app(app)
        with app.app_context():
            db.create_all()
        ensure_housingtype_enum_values()
        _schema_initialized = True


def truncate_all_tables(db) -> None:
    """Remove row data between tests without dropping schema objects."""
    ensure_all_models_imported()
    with db.engine.begin() as conn:
        conn.execute(text("SET session_replication_role = 'replica'"))
        for table in reversed(db.metadata.sorted_tables):
            conn.execute(text(f'TRUNCATE TABLE "{table.name}" RESTART IDENTITY CASCADE'))
        conn.execute(text("SET session_replication_role = 'origin'"))


def cleanup_test_data(db) -> None:
    """Clear test data and SQLAlchemy session state after a test."""
    db.session.remove()
    try:
        truncate_all_tables(db)
    except Exception:
        db.session.rollback()
        raise


def init_test_database(app, db) -> None:
    """Bind SQLAlchemy and ensure shared schema exists."""
    configure_app_for_tests(app)
    db.init_app(app)
    initialize_shared_schema(db)


def destroy_test_database(app, db) -> None:
    """Clear data after a test; keep schema intact for subsequent tests."""
    with app.app_context():
        cleanup_test_data(db)
