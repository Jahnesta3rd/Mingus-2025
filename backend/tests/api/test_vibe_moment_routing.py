"""API tests for Vibe Moment routing fields on setup-status and mark endpoint."""
import json
import os
import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import jwt
import pytest

from backend.api.profile_endpoints import ALL_ONBOARDING_STEPS
from backend.auth.decorators import JWT_ALGORITHM, JWT_SECRET_KEY
from backend.models.database import db
from backend.models.user_models import User


def _jwt(user_id: str, email: str) -> str:
    payload = {
        'user_id': user_id,
        'email': email,
        'exp': datetime.utcnow() + timedelta(hours=24),
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


@pytest.fixture
def vibe_routing_user(app):
    suffix = uuid.uuid4().hex[:12]
    user_id = f'vibe_rt_{suffix}'
    email = f'vibe_rt_{suffix}@test.example'
    with app.app_context():
        user = User(
            user_id=user_id,
            email=email,
            password_hash='x',
        )
        db.session.add(user)
        db.session.commit()
    try:
        yield user_id, email
    finally:
        with app.app_context():
            u = User.query.filter_by(user_id=user_id).first()
            if u is not None:
                db.session.delete(u)
                db.session.commit()


@pytest.mark.skipif(
    not os.environ.get('DATABASE_URL'),
    reason='DATABASE_URL required (app init uses Postgres)',
)
def test_show_vibe_moment_today_and_mark_shown(app, client, vibe_routing_user):
    user_id, email = vibe_routing_user
    token = _jwt(user_id, email)
    auth_headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json',
    }
    complete_steps = (list(ALL_ONBOARDING_STEPS), [])

    with patch(
        'backend.api.profile_endpoints._compute_onboarding_steps',
        return_value=complete_steps,
    ):
        r1 = client.get('/api/profile/setup-status', headers=auth_headers)
    assert r1.status_code == 200
    d1 = json.loads(r1.data)
    assert d1.get('onboarding_complete') is True
    assert d1.get('show_vibe_moment_today') is True

    r2 = client.post('/api/profile/vibe-moment-shown', headers=auth_headers)
    assert r2.status_code == 200
    d2 = json.loads(r2.data)
    assert d2.get('success') is True
    assert d2.get('last_vibe_moment_shown_at')

    with patch(
        'backend.api.profile_endpoints._compute_onboarding_steps',
        return_value=complete_steps,
    ):
        r3 = client.get('/api/profile/setup-status', headers=auth_headers)
    assert r3.status_code == 200
    d3 = json.loads(r3.data)
    assert d3.get('show_vibe_moment_today') is False

    with app.app_context():
        u = User.query.filter_by(user_id=user_id).first()
        assert u is not None
        u.last_vibe_moment_shown_at = datetime.now(timezone.utc) - timedelta(days=2)
        db.session.commit()

    with patch(
        'backend.api.profile_endpoints._compute_onboarding_steps',
        return_value=complete_steps,
    ):
        r4 = client.get('/api/profile/setup-status', headers=auth_headers)
    assert r4.status_code == 200
    d4 = json.loads(r4.data)
    assert d4.get('show_vibe_moment_today') is True
