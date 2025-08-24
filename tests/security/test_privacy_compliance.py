import json
import pytest


class TestPrivacyCompliance:
    def test_user_consent_not_assumed(self, client):
        # Without explicit consent, marketing preferences should not default to enabled
        r = client.get('/api/auth/profile')
        if r.status_code == 200:
            data = r.get_json() or {}
            profile = data.get('profile') or {}
            prefs = profile.get('data_sharing_preferences')
            if isinstance(prefs, str):
                try:
                    prefs = json.loads(prefs)
                except Exception:
                    prefs = {}
            if isinstance(prefs, dict):
                assert prefs.get('marketing_consent', False) in (False, None)

    @pytest.mark.skip(reason="Implement delete/anonymize endpoint then enable")
    def test_user_data_deletion_request(self, client):
        # Placeholder for GDPR/CCPA-like deletion test
        pass



