"""Regression: SQLAlchemy mappers initialize without duplicate-table / broken relationship errors."""
import pytest

from backend.models.user_models import User


def test_mapper_initialization(app):
    """Ensure all SQLAlchemy mappers can initialize without errors.

    Regression for duplicate user_achievements mapping (wellness vs gamification)
    and broken relationship graphs. If any model configuration is invalid,
    User.query typically raises before DB access.
    """
    with app.app_context():
        try:
            User.query.filter_by(user_id="test-mapper-init").first()
        except Exception as e:
            name = type(e).__name__
            msg = str(e).lower()
            if "InvalidRequestError" in name or "mappers" in msg or "mapper" in msg:
                pytest.fail(f"Mapper initialization failed: {e}")
            # No DB row / connection errors are acceptable in minimal test env
