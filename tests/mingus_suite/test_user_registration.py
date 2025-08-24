import uuid
import pytest


class TestUserRegistration:
    """Test complete user registration flow."""

    @staticmethod
    def _make_payload(email: str | None = None) -> dict:
        return {
            "email": email or f"marcus_{uuid.uuid4().hex[:6]}@example.com",
            "password": "StrongPass!123",
            "first_name": "Marcus",
            "last_name": "Johnson",
            "phone_number": "+14045551234",
        }

    def test_valid_registration(self, client):
        payload = self._make_payload()
        resp = client.post("/api/auth/register", json=payload)
        assert resp.status_code in (200, 201, 302)

    def test_duplicate_email_registration(self, client):
        payload = self._make_payload(email=f"dupe_{uuid.uuid4().hex[:6]}@example.com")
        first = client.post("/api/auth/register", json=payload)
        assert first.status_code in (200, 201, 302)
        dupe = client.post("/api/auth/register", json=payload)
        assert dupe.status_code in (400, 409)

    def test_invalid_email_format(self, client):
        payload = self._make_payload(email="invalid-email")
        resp = client.post("/api/auth/register", json=payload)
        assert resp.status_code == 400

    def test_weak_password(self, client):
        payload = self._make_payload()
        payload["password"] = "123"
        resp = client.post("/api/auth/register", json=payload)
        assert resp.status_code == 400

    @pytest.mark.parametrize("missing_field", ["email", "password", "first_name", "last_name"])
    def test_missing_required_fields(self, client, missing_field):
        payload = self._make_payload()
        del payload[missing_field]
        resp = client.post("/api/auth/register", json=payload)
        assert resp.status_code == 400


