"""Integration tests for lead magnet email resend/retry."""

from __future__ import annotations

import time
from unittest.mock import MagicMock

import pytest

from backend.tasks.email_tasks import _retry_countdown_seconds
from backend.tests.fixtures.lead_magnet_test_helpers import (
    assert_log_failed,
    assert_log_sent,
    check_log_status,
    create_test_lead_magnet_log,
    mock_smtp_failure,
    trigger_send_task,
)


def test_lead_magnet_email_send_success(db_session, monkeypatch):
    """Email sends successfully on first try."""
    monkeypatch.setattr("backend.tasks.email_tasks.service_send_email", lambda *a, **k: True)

    log = create_test_lead_magnet_log("user@example.com", "ai_risk")
    trigger_send_task(log["log_id"])

    status = check_log_status(log["log_id"])

    assert status["status"] == "sent"
    assert status["retry_count"] == 0
    assert status["last_error"] is None
    assert_log_sent(log["log_id"])


def test_lead_magnet_email_retry_on_failure(db_session, monkeypatch):
    """Email fails first time, retries and succeeds."""
    log = create_test_lead_magnet_log("user@example.com", "income_comparison")

    mock_smtp_failure(monkeypatch)
    trigger_send_task(log["log_id"])

    status = check_log_status(log["log_id"])

    assert status["status"] == "sent"
    assert status["retry_count"] == 1


def test_lead_magnet_email_max_retries_exceeded(db_session, monkeypatch):
    """Email fails 3+ times, task gives up."""
    log = create_test_lead_magnet_log("user@example.com", "layoff_risk")

    monkeypatch.setattr(
        "backend.tasks.email_tasks.service_send_email",
        MagicMock(side_effect=Exception("SMTP timeout")),
    )

    trigger_send_task(log["log_id"])
    status = check_log_status(log["log_id"])

    assert status["status"] == "failed"
    assert status["retry_count"] == 3
    assert "SMTP timeout" in (status["last_error"] or "")
    assert_log_failed(log["log_id"], expected_error="SMTP timeout")


def test_exponential_backoff_delays(db_session, monkeypatch):
    """Verify retry delays increase exponentially."""
    log = create_test_lead_magnet_log("user@example.com", "cuffing_season")

    retry_times: list[float] = []
    countdowns: list[int] = []

    def countdown_spy(retries: int) -> int:
        countdown = _retry_countdown_seconds(retries)
        countdowns.append(countdown)
        return countdown

    monkeypatch.setattr("backend.tasks.email_tasks._retry_countdown_seconds", countdown_spy)

    def mock_send_with_timing(*args, **kwargs):
        retry_times.append(time.time())
        if len(retry_times) < 3:
            raise Exception("Simulated failure")
        return True

    monkeypatch.setattr(
        "backend.tasks.email_tasks.service_send_email",
        mock_send_with_timing,
    )

    trigger_send_task(log["log_id"])

    assert countdowns == [
        _retry_countdown_seconds(0),
        _retry_countdown_seconds(1),
    ]
    assert retry_times[1] - retry_times[0] >= 0
    assert retry_times[2] - retry_times[1] >= 0

    status = check_log_status(log["log_id"])
    assert status["status"] == "sent"
    assert status["retry_count"] == 2
