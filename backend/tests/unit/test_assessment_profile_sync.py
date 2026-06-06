import os
import sys
from types import SimpleNamespace

from sqlalchemy.dialects import postgresql

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from backend.api import assessment_endpoints as assessment_api


class _FakeAssessmentCursor:
    def __init__(self, rows):
        self._rows = rows

    def execute(self, _query, _params):
        return None

    def fetchall(self):
        return self._rows


class _FakeAssessmentConn:
    def __init__(self, rows):
        self._cursor = _FakeAssessmentCursor(rows)
        self.closed = False

    def cursor(self):
        return self._cursor

    def close(self):
        self.closed = True


class _FakeUpsertResult:
    def __init__(self, profile_id, inserted):
        self._row = SimpleNamespace(id=profile_id, inserted=inserted)

    def first(self):
        return self._row


class _RecordingSession:
    def __init__(self, inserted):
        self.inserted = inserted
        self.committed = False
        self.rolled_back = False
        self.sql = None
        self.params = None

    def execute(self, stmt):
        compiled = stmt.compile(dialect=postgresql.dialect(), compile_kwargs={"literal_binds": False})
        self.sql = str(compiled)
        self.params = compiled.params
        return _FakeUpsertResult(profile_id=77, inserted=self.inserted)

    def commit(self):
        self.committed = True

    def rollback(self):
        self.rolled_back = True


def _sample_rows():
    return [
        {
            "id": 10,
            "assessment_type": "ai-risk",
            "answers": '{"industry":"Finance/Banking"}',
            "completed_at": "2026-04-30T12:00:00",
            "score": 72,
            "risk_level": "High",
            "recommendations": '["a","b"]',
            "subscores": '{"automation":80}',
        },
        {
            "id": 11,
            "assessment_type": "income-comparison",
            "answers": '{"currentSalary":"$75,000 - $100,000"}',
            "completed_at": "2026-04-30T13:00:00",
            "score": 60,
            "risk_level": "40th-60th percentile",
            "recommendations": '["c"]',
            "subscores": None,
        },
    ]


def test_sync_assessments_to_profile_insert_path(monkeypatch):
    fake_conn = _FakeAssessmentConn(_sample_rows())
    fake_session = _RecordingSession(inserted=True)
    info_logs = []

    monkeypatch.setattr(assessment_api, "get_db_connection", lambda: fake_conn)
    monkeypatch.setattr(assessment_api, "db", SimpleNamespace(session=fake_session))
    monkeypatch.setattr(
        assessment_api.logger,
        "info",
        lambda msg, *args: info_logs.append(msg % args if args else msg),
    )

    assessment_api.sync_assessments_to_profile("TestUser@example.com")

    assert fake_session.committed is True
    assert fake_conn.closed is True
    assert "ON CONFLICT (email) DO UPDATE" in fake_session.sql
    assert fake_session.params["email"] == "testuser@example.com"
    assert fake_session.params["personal_info"] == "{}"
    assert fake_session.params["financial_info"] == "{}"
    assert fake_session.params["monthly_expenses"] == "{}"
    assert fake_session.params["important_dates"] == "{}"
    assert fake_session.params["health_wellness"] == "{}"
    assert fake_session.params["goals"] == "{}"
    assert '"10"' in fake_session.params["assessment_results"]
    assert any("assessment_sync user_profile_id=77 email=testuser@example.com action=insert" in m for m in info_logs)


def test_sync_assessments_to_profile_update_path(monkeypatch):
    fake_conn = _FakeAssessmentConn(_sample_rows())
    fake_session = _RecordingSession(inserted=False)
    info_logs = []

    monkeypatch.setattr(assessment_api, "get_db_connection", lambda: fake_conn)
    monkeypatch.setattr(assessment_api, "db", SimpleNamespace(session=fake_session))
    monkeypatch.setattr(
        assessment_api.logger,
        "info",
        lambda msg, *args: info_logs.append(msg % args if args else msg),
    )

    assessment_api.sync_assessments_to_profile("existing@example.com")

    assert fake_session.committed is True
    assert "DO UPDATE SET assessment_results" in fake_session.sql
    assert "financial_readiness_index" in fake_session.sql
    assert "updated_at" in fake_session.sql
    do_update_sql = fake_session.sql.split("DO UPDATE SET", 1)[1]
    assert "personal_info" not in do_update_sql
    assert "financial_info" not in do_update_sql
    assert "monthly_expenses" not in do_update_sql
    assert "important_dates" not in do_update_sql
    assert "health_wellness" not in do_update_sql
    assert "goals" not in do_update_sql
    assert any("assessment_sync user_profile_id=77 email=existing@example.com action=update" in m for m in info_logs)
