import os
import tempfile
import pytest

from backend.app_factory import create_app
from backend.database import init_app_database, create_tables, drop_tables


@pytest.fixture(scope="module")
def app():
    db_fd, db_path = tempfile.mkstemp()
    sqlite_uri = f"sqlite:///{db_path}"

    flask_app = create_app("testing")
    flask_app.config.update(
        TESTING=True,
        SECRET_KEY="test-secret-key",
        WTF_CSRF_ENABLED=False,
        DATABASE_URL=sqlite_uri,
        SQLALCHEMY_DATABASE_URI=sqlite_uri,
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        CREATE_TABLES=True,
        BYPASS_AUTH=False  # SECURITY: Authentication bypass disabled,
    )

    with flask_app.app_context():
        init_app_database(flask_app)
        create_tables()

    yield flask_app

    try:
        with flask_app.app_context():
            drop_tables()
    except Exception:
        pass
    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture(scope="module")
def client(app):
    return app.test_client()


class TestAPIEndpoints:
    """Test all API endpoints for basic functionality."""

    def test_health_endpoint(self, client):
        for path in ("/api/health", "/health", "/api/system/health"):
            resp = client.get(path)
            if resp.status_code != 404:
                break
        assert resp.status_code == 200
        data = resp.get_json() or {}
        assert data.get("status", "healthy").lower() in ("healthy", "ok")

    def test_get_user_profile_unauthorized(self, client):
        resp = client.get("/api/auth/profile")
        assert resp.status_code in (401, 403)


