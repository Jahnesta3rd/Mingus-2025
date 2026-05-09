#!/usr/bin/env python3
"""Smoke tests for vehicle_dashboard_public_bp GET /api/vehicles/dashboard."""

from __future__ import annotations

import os
import uuid
from datetime import datetime, timedelta

import jwt
import pytest
from flask import Flask
from sqlalchemy import text

from backend.auth.decorators import JWT_ALGORITHM, JWT_SECRET_KEY
from backend.models.database import db, init_database
from backend.routes.vehicle_dashboard_routes import vehicle_dashboard_public_bp


def _ensure_user_sql(app: Flask, user_id: str) -> int:
    """Insert test user without ORM; return internal numeric users.id."""
    with app.app_context():
        row = db.session.execute(
            text("SELECT id FROM users WHERE user_id = :u LIMIT 1"),
            {"u": user_id},
        ).first()
        if row:
            return int(row[0])
        now = datetime.utcnow()
        email = f"{user_id}@smoke.test"
        db.session.execute(
            text(
                """
                INSERT INTO users (
                    user_id, email, password_hash, tier, is_beta, is_admin,
                    referral_count, successful_referrals, feature_unlocked,
                    last_activity, created_at, updated_at
                ) VALUES (
                    :user_id, :email, :ph, 'budget', false, false,
                    0, 0, false,
                    :now, :now, :now
                )
                """
            ),
            {
                "user_id": user_id,
                "email": email,
                "ph": "smoke-test-no-login",
                "now": now,
            },
        )
        db.session.commit()
        row2 = db.session.execute(
            text("SELECT id FROM users WHERE user_id = :u"),
            {"u": user_id},
        ).first()
        return int(row2[0])


@pytest.fixture
def smoke_app():
    if not os.environ.get("DATABASE_URL"):
        pytest.skip("DATABASE_URL required for vehicle dashboard smoke tests")
    app = Flask(__name__)
    app.config["TESTING"] = True
    init_database(app)
    app.register_blueprint(vehicle_dashboard_public_bp)

    @app.teardown_request
    def _rollback_on_error(exc):
        if exc is not None:
            db.session.rollback()

    with app.app_context():
        db.create_all()
    yield app


@pytest.fixture
def smoke_client(smoke_app):
    return smoke_app.test_client()


def _make_token(user_id: str) -> str:
    payload = {
        "user_id": user_id,
        "email": "vd@m.test",
        "exp": int((datetime.utcnow() + timedelta(hours=2)).timestamp()),
    }
    raw = jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return raw if isinstance(raw, str) else raw.decode("ascii")


def test_vehicle_dashboard_public_smoke(smoke_app, smoke_client):
    r401 = smoke_client.get("/api/vehicles/dashboard")
    assert r401.status_code == 401

    uid = f"vd{uuid.uuid4().hex[:30]}"
    _ensure_user_sql(smoke_app, uid)
    tok = _make_token(uid)
    headers = {"Authorization": f"Bearer {tok}"}

    r200 = smoke_client.get("/api/vehicles/dashboard", headers=headers)
    assert r200.status_code == 200, r200.get_data(as_text=True)
    body = r200.get_json()
    assert body["vehicles"] == []
    assert body["upcomingMaintenance"] == []
    assert body["maintenancePredictions"] == []
    assert body["budgets"] == []
    assert body["recentExpenses"] == []
    assert isinstance(body["quickActions"], list) and len(body["quickActions"]) >= 1
    assert body["stats"]["totalVehicles"] == 0

    internal_id = _ensure_user_sql(smoke_app, uid)
    vin = f"SMK{uuid.uuid4().hex[:12].upper()}"
    now = datetime.utcnow()
    with smoke_app.app_context():
        db.session.execute(
            text(
                """
                INSERT INTO vehicles (
                    user_id, vin, year, make, model,
                    current_mileage, monthly_miles, user_zipcode,
                    created_date, updated_date
                ) VALUES (
                    :uid, :vin, 2020, 'Smoke', 'TestCar',
                    10000, 800, '94102',
                    :now, :now
                )
                """
            ),
            {"uid": internal_id, "vin": vin, "now": now},
        )
        db.session.commit()

    rveh = smoke_client.get("/api/vehicles/dashboard", headers=headers)
    assert rveh.status_code == 200, rveh.get_data(as_text=True)
    data = rveh.get_json()
    assert len(data["vehicles"]) == 1
    assert data["vehicles"][0]["make"] == "Smoke"
    assert data["vehicles"][0]["vin"] == vin
    assert data["stats"]["totalVehicles"] == 1
