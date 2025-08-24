"""
Database package for backend.
Provides database utilities and Celery session integration.

This package coexists with a legacy module file at backend/database.py.
We bridge key functions used by tests by re-exporting from the legacy module
when available.
"""

from importlib import util as _importlib_util  # type: ignore
from pathlib import Path as _Path  # type: ignore

# Attempt to load legacy module backend/database.py to expose its API
_legacy_path = _Path(__file__).resolve().parent.parent / 'database.py'
if _legacy_path.exists():
    _spec = _importlib_util.spec_from_file_location('backend._legacy_database', str(_legacy_path))
    if _spec and _spec.loader:  # type: ignore[attr-defined]
        _legacy_db = _importlib_util.module_from_spec(_spec)
        _spec.loader.exec_module(_legacy_db)  # type: ignore[attr-defined]
        # Re-export commonly used functions for tests
        init_app_database = getattr(_legacy_db, 'init_app_database', None)
        create_tables = getattr(_legacy_db, 'create_tables', None)
        drop_tables = getattr(_legacy_db, 'drop_tables', None)
        init_database_session_factory = getattr(_legacy_db, 'init_database_session_factory', None)
        get_db_session = getattr(_legacy_db, 'get_db_session', None)
        get_flask_db_session = getattr(_legacy_db, 'get_flask_db_session', None)
        get_current_db_session = getattr(_legacy_db, 'get_current_db_session', None)

__all__ = [
    'celery_session',
    'connection_pool',
    'session_manager',
    # Legacy exports
    'init_app_database',
    'create_tables',
    'drop_tables',
    'init_database_session_factory',
    'get_db_session',
    'get_flask_db_session',
    'get_current_db_session',
]


