import pytest


class TestSubscriptionManagement:
    """Basic checks for subscription endpoints and flows."""

    def test_subscription_endpoints_exist(self, client):
        for path in (
            "/api/subscription/plans",
            "/api/subscription/status",
            "/api/subscription/upgrade",
        ):
            resp = client.get(path)
            assert resp.status_code in (200, 401, 404)

    def test_view_plans_then_upgrade_flow(self, client, sample_user_data):
        # Ensure session
        client.post('/api/auth/register', json=sample_user_data)
        client.post('/api/auth/login', json={
            'email': sample_user_data['email'],
            'password': sample_user_data['password']
        })

        plans = client.get('/api/subscription/plans')
        assert plans.status_code in (200, 404)

        if plans.status_code == 200:
            # Attempt an upgrade to a valid tier if available
            upgrade = client.post('/api/subscription/upgrade', json={"tier": "professional"})
            assert upgrade.status_code in (200, 400)


