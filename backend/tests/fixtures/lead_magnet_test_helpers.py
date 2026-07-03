"""Helpers for lead magnet email resend/retry integration tests."""

from __future__ import annotations

from smtplib import SMTPException

from backend.models.database import db
from backend.models.lead_magnet_email_log import LeadMagnetEmailLog
from backend.tasks.email_tasks import send_lead_magnet_email

DEFAULT_RESULTS_DATA = {
    "score": 72,
    "risk_level": "medium",
    "recommendations": ["Update your resume", "Build emergency savings"],
}


def create_test_lead_magnet_log(email: str, assessment_type: str) -> dict:
    """Insert a test log entry and return the ID."""
    row = LeadMagnetEmailLog(
        email=email,
        assessment_type=assessment_type,
        status="queued",
        results_data=DEFAULT_RESULTS_DATA,
    )
    db.session.add(row)
    db.session.commit()
    return {"log_id": row.id, "email": email, "status": row.status}


def trigger_send_task(log_id: int) -> str:
    """Dispatch the Celery task synchronously for testing."""
    row = db.session.get(LeadMagnetEmailLog, log_id)
    if not row:
        raise ValueError(f"lead_magnet_email_log id={log_id} not found")
    result = send_lead_magnet_email.delay(
        log_id,
        row.email,
        row.assessment_type,
        row.results_data or {},
    )
    return result.id


def check_log_status(log_id: int) -> dict:
    """Query the log and return current status."""
    db.session.expire_all()
    row = db.session.get(LeadMagnetEmailLog, log_id)
    if not row:
        raise ValueError(f"lead_magnet_email_log id={log_id} not found")
    return {
        "email": row.email,
        "status": row.status,
        "retry_count": row.retry_count,
        "last_error": row.last_error,
        "sent_at": row.sent_at,
    }


def mock_smtp_failure(monkeypatch) -> None:
    """Mock send_email() to fail once, then succeed on retry."""
    calls = {"count": 0}

    def _send(*args, **kwargs):
        calls["count"] += 1
        if calls["count"] == 1:
            raise SMTPException("Simulated SMTP failure")
        return True

    monkeypatch.setattr("backend.tasks.email_tasks.service_send_email", _send)


def assert_log_queued(log_id: int) -> None:
    status = check_log_status(log_id)
    assert status["status"] == "queued"


def assert_log_sent(log_id: int) -> None:
    status = check_log_status(log_id)
    assert status["status"] == "sent"
    assert status["sent_at"] is not None


def assert_log_failed(log_id: int, expected_error: str | None = None) -> None:
    status = check_log_status(log_id)
    assert status["status"] == "failed"
    if expected_error:
        assert expected_error in (status["last_error"] or "")
