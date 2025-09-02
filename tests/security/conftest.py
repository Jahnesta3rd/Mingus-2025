import os
import tempfile
import pytest

from backend.app_factory import create_app
from backend.database import init_app_database, create_tables, drop_tables


@pytest.fixture(scope="session")
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


@pytest.fixture(scope="session")
def client(app):
    return app.test_client()



