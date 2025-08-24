import os
import tempfile
import pytest

from backend.app_factory import create_app
from backend.database import init_app_database, create_tables, drop_tables


@pytest.fixture(scope="session")
def app():
    """Create a Flask app configured for testing with a temp SQLite database."""
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
        BYPASS_AUTH=True,
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


@pytest.fixture(scope="session")
def client(app):
    """Provide a Flask test client bound to the test app."""
    return app.test_client()


@pytest.fixture(scope="session")
def demographic_profiles():
    """Sample culturally appropriate user data for target demographic (25-35, $40k-$100k)."""
    return [
        {
            "email": "marcus.johnson@example.com",
            "password": "StrongPass!123",
            "first_name": "Marcus",
            "last_name": "Johnson",
            "phone_number": "+14045551234",
            "zip_code": "30309",
            "city": "Atlanta",
            "state": "GA",
            "industry": "Technology",
            "job_title": "Software Developer",
            "monthly_income": 85000,
        },
        {
            "email": "alicia.brown@example.com",
            "password": "StrongPass!123",
            "first_name": "Alicia",
            "last_name": "Brown",
            "phone_number": "+17135551234",
            "zip_code": "77002",
            "city": "Houston",
            "state": "TX",
            "industry": "Healthcare",
            "job_title": "Clinical Data Analyst",
            "monthly_income": 72000,
        },
        {
            "email": "darius.williams@example.com",
            "password": "StrongPass!123",
            "first_name": "Darius",
            "last_name": "Williams",
            "phone_number": "+12025551234",
            "zip_code": "20001",
            "city": "Washington",
            "state": "DC",
            "industry": "Consulting",
            "job_title": "Management Consultant",
            "monthly_income": 98000,
        },
        {
            "email": "tanya.harris@example.com",
            "password": "StrongPass!123",
            "first_name": "Tanya",
            "last_name": "Harris",
            "phone_number": "+12145551234",
            "zip_code": "75201",
            "city": "Dallas",
            "state": "TX",
            "industry": "Finance",
            "job_title": "Financial Analyst",
            "monthly_income": 90000,
        },
    ]


@pytest.fixture(scope="function")
def sample_user_data(demographic_profiles):
    """Return a copy of the first profile for mutation per test."""
    return dict(demographic_profiles[0])


@pytest.fixture(scope="session")
def auth_helpers(client):
    """Helper functions for registering and logging in a user."""

    class Helpers:
        def register(self, payload: dict):
            return client.post("/api/auth/register", json=payload)

        def login(self, email: str, password: str):
            return client.post("/api/auth/login", json={"email": email, "password": password})

    return Helpers()


