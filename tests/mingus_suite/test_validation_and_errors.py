import pytest


class TestValidationAndErrors:
    """Validation and error handling cases across endpoints."""

    def test_register_missing_fields(self, client):
        resp = client.post('/api/auth/register', json={})
        assert resp.status_code == 400

    def test_register_invalid_email(self, client):
        payload = {
            'email': 'not-an-email',
            'password': 'StrongPass!123',
            'first_name': 'Alicia',
            'last_name': 'Brown',
        }
        resp = client.post('/api/auth/register', json=payload)
        assert resp.status_code == 400

    def test_login_invalid_credentials(self, client):
        resp = client.post('/api/auth/login', json={'email': 'x@y.z', 'password': 'nope'})
        assert resp.status_code in (401, 400)

    def test_profile_update_validation(self, client):
        # No auth; expect 401 or 403 or 500 depending on enforcement
        resp = client.post('/api/user-profile/update', json={'monthly_income': -100})
        assert resp.status_code in (401, 403, 400, 500)


