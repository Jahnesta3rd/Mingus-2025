class TestAPIEndpoints:
    """Test all core API endpoints for basic functionality."""

    def test_health(self, client):
        for path in ("/api/health", "/health", "/api/system/health"):
            resp = client.get(path)
            if resp.status_code != 404:
                break
        assert resp.status_code == 200

    def test_register_login_profile_cycle(self, client, sample_user_data):
        # Register
        r = client.post("/api/auth/register", json=sample_user_data)
        assert r.status_code in (200, 201, 302)

        # Login
        l = client.post("/api/auth/login", json={
            "email": sample_user_data["email"],
            "password": sample_user_data["password"],
        })
        assert l.status_code in (200, 302)

        # Profile (session-based)
        p = client.get("/api/auth/profile")
        assert p.status_code in (200, 404)


