import os
import pytest


class TestDataProtection:
    def test_https_recommended_in_production(self):
        # Ensure HTTPS is expected in non-local environments
        env = os.environ.get('FLASK_ENV', 'development')
        if env == 'production':
            assert os.environ.get('PREFERRED_URL_SCHEME', 'https') == 'https'

    def test_sensitive_fields_not_returned_in_profile(self, client):
        # After unauthenticated fetch, should not leak sensitive data
        r = client.get('/api/auth/profile')
        if r.status_code == 200:
            data = r.get_json() or {}
            profile = data.get('profile') or {}
            assert 'password' not in profile
            assert 'ssn' not in profile



