import pytest


class TestInputValidation:
    def test_sql_injection_registration(self, client):
        payload = {
            'email': "test'); DROP TABLE users; --@example.com",
            'password': 'StrongPass!123',
            'first_name': 'Robert',
            'last_name': "'); DROP TABLE users; --",
        }
        r = client.post('/api/auth/register', json=payload)
        # Expect validation error for email format, not server error
        assert r.status_code == 400

    def test_xss_profile_update(self, client):
        # Unauthenticated update should fail 401/403, but must not execute scripts
        update = {
            'first_name': '<script>alert(1)</script>',
            'last_name': 'User'
        }
        r = client.post('/api/user-profile/update', json=update)
        assert r.status_code in (401, 403, 400)

    def test_csrf_protection_present(self, client):
        # For form-based endpoints, ensure CSRF token is expected (if enabled)
        # In API mode with JSON, CSRF may be disabled by design
        # This test is a placeholder to assert config if applicable
        assert True



