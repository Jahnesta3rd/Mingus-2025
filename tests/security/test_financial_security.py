import pytest


class TestFinancialSecurity:
    def test_subscription_endpoints_require_auth(self, client):
        for path in ("/api/subscription/status", "/api/subscription/upgrade"):
            r = client.get(path)
            assert r.status_code in (401, 403, 404)

    def test_payment_keys_not_exposed(self, client):
        # Ensure no secret keys are exposed via public endpoints
        r = client.get('/api/system/health')
        if r.status_code == 200:
            text = r.get_data(as_text=True)
            assert 'STRIPE' not in text and 'PLAID' not in text



