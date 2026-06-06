"""
Focused regression: import_vibe_lead must accept JWT-style UUID strings (P8 / #28)
and resolve User via User.user_id, not integer PK on db.session.get.
"""
from __future__ import annotations

import os
import sys
import uuid

import pytest
from flask import Flask

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from backend.models.database import db, init_database
from backend.models.financial_setup import RecurringExpense
from backend.models.life_ledger import LifeLedgerInsight, LifeLedgerProfile
from backend.models.user_models import User
from backend.models.vibe_checkups import VibeCheckupsLead, VibeCheckupsSession
from backend.services.life_ledger_service import VC_IMPORT_SOURCE, import_vibe_lead


def _database_url() -> str | None:
    return os.environ.get("TEST_DATABASE_URL") or os.environ.get("DATABASE_URL")


@pytest.fixture
def life_ledger_app():
    url = _database_url()
    if not url:
        pytest.skip(
            "DATABASE_URL or TEST_DATABASE_URL required "
            "(init_database does not support SQLite-only runs)."
        )

    app = Flask(__name__)
    app.config["TESTING"] = True
    app.config["SECRET_KEY"] = "life-ledger-service-test-secret"
    app.config["WTF_CSRF_ENABLED"] = False
    init_database(app)
    return app


class TestLifeLedgerService:
    def test_import_vibe_lead_accepts_uuid_string(self, life_ledger_app):
        """Fails if User is still loaded with db.session.get(User, uuid_string)."""
        ext_user_id = str(uuid.uuid4())
        lead_id = uuid.uuid4()
        session_id = uuid.uuid4()
        session_token = f"test_session_{uuid.uuid4().hex}"
        email = f"life_ledger_svc_{ext_user_id[:12]}@example.com"

        with life_ledger_app.app_context():
            session_row = VibeCheckupsSession(
                id=session_id,
                session_token=session_token,
                answers={},
            )
            db.session.add(session_row)
            db.session.flush()

            lead = VibeCheckupsLead(
                id=lead_id,
                session_id=session_id,
                email=email,
                emotional_score=60,
                financial_score=60,
                verdict_label="balanced",
                total_annual_projection=12000,
                projection_data=[],
                mingus_converted=True,
            )
            db.session.add(lead)

            user = User(
                user_id=ext_user_id,
                email=email,
                password_hash="unused",
            )
            db.session.add(user)
            db.session.commit()

            uid = user.id
            try:
                profile = import_vibe_lead(user.user_id, str(lead_id))
                assert profile.user_id == uid
                assert profile.vibe_lead_id == lead_id
                assert profile.vibe_score == 60
            finally:
                LifeLedgerInsight.query.filter_by(user_id=uid).delete(
                    synchronize_session=False
                )
                LifeLedgerProfile.query.filter_by(user_id=uid).delete(
                    synchronize_session=False
                )
                RecurringExpense.query.filter_by(
                    user_id=uid, source=VC_IMPORT_SOURCE
                ).delete(synchronize_session=False)
                db.session.commit()

                lr = db.session.get(VibeCheckupsLead, lead_id)
                if lr is not None:
                    db.session.delete(lr)
                sr = db.session.get(VibeCheckupsSession, session_id)
                if sr is not None:
                    db.session.delete(sr)
                ur = User.query.filter_by(user_id=ext_user_id).first()
                if ur is not None:
                    db.session.delete(ur)
                db.session.commit()
