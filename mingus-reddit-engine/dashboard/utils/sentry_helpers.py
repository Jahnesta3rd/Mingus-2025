"""
Sentry helper utilities for admin dashboard API endpoints.
"""

import time
from functools import wraps

import sentry_sdk
from flask import jsonify, request


def admin_error_handler(endpoint_name=None):
    """Capture errors in admin endpoints with timing and context."""

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            name = endpoint_name or func.__name__
            start_time = time.time()

            try:
                result = func(*args, **kwargs)
                duration_ms = (time.time() - start_time) * 1000

                sentry_sdk.add_breadcrumb(
                    category="admin-endpoint",
                    message=f"{name} completed successfully",
                    level="info",
                    data={
                        "endpoint": name,
                        "duration_ms": duration_ms,
                        "status": "success",
                    },
                )

                return result

            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000

                with sentry_sdk.push_scope() as scope:
                    scope.set_tag("endpoint", name)
                    scope.set_tag("type", "admin_endpoint_error")
                    scope.set_tag("method", request.method)
                    scope.set_extra("endpoint_name", name)
                    scope.set_extra("duration_ms", duration_ms)
                    scope.set_extra("path", request.path)
                    scope.set_extra("method", request.method)
                    scope.set_extra("content_length", request.content_length or 0)
                    event_id = sentry_sdk.capture_exception(e)

                return jsonify({
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "sentry_event_id": event_id,
                }), 500

        return wrapper

    return decorator


def track_db_operation(operation_name, tags=None):
    """Context manager to track database operations."""

    tags = tags or {}

    class DBOperationTracker:
        def __enter__(self):
            self.start_time = time.time()

            sentry_sdk.add_breadcrumb(
                category="database.operation",
                message=f"DB: {operation_name}",
                level="info",
                data={"operation": operation_name, **tags},
            )

            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            duration_ms = (time.time() - self.start_time) * 1000

            if exc_type is not None:
                with sentry_sdk.push_scope() as scope:
                    scope.set_tag("operation", operation_name)
                    scope.set_tag("type", "database_error")
                    for key, value in tags.items():
                        scope.set_tag(key, value)
                    scope.set_extra("operation_name", operation_name)
                    scope.set_extra("duration_ms", duration_ms)
                    scope.set_extra("error_type", exc_type.__name__)
                    sentry_sdk.capture_exception(exc_val)
                return False

            sentry_sdk.add_breadcrumb(
                category="database.operation",
                message=f"{operation_name} completed",
                level="info",
                data={
                    "operation": operation_name,
                    "duration_ms": duration_ms,
                    "status": "success",
                    **tags,
                },
            )

            return False

    return DBOperationTracker()


def track_csv_import(filename, operation):
    """Context manager for tracking CSV import operations."""

    class CSVImportTracker:
        def __init__(self):
            self.start_time = None
            self.stats = {
                "inserted": 0,
                "skipped": 0,
                "errors": 0,
            }

        def __enter__(self):
            self.start_time = time.time()

            sentry_sdk.add_breadcrumb(
                category="csv-import",
                message=f"CSV import started: {filename}",
                level="info",
                data={
                    "filename": filename,
                    "operation": operation,
                },
            )

            return self.stats

        def __exit__(self, exc_type, exc_val, exc_tb):
            duration_ms = (time.time() - self.start_time) * 1000

            if exc_type is not None:
                with sentry_sdk.push_scope() as scope:
                    scope.set_tag("action", "csv_import")
                    scope.set_tag("status", "failed")
                    scope.set_extra("filename", filename)
                    scope.set_extra("operation", operation)
                    scope.set_extra("duration_ms", duration_ms)
                    scope.set_extra("stats", self.stats)
                    sentry_sdk.capture_exception(exc_val)
                return False

            sentry_sdk.add_breadcrumb(
                category="csv-import",
                message="CSV import completed",
                level="info",
                data={
                    "filename": filename,
                    "operation": operation,
                    "duration_ms": duration_ms,
                    "inserted": self.stats["inserted"],
                    "skipped": self.stats["skipped"],
                    "errors": self.stats["errors"],
                },
            )

            return False

    return CSVImportTracker()
