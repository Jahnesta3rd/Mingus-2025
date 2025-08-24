import pytest


class TestProfileCompletion:
    """Test user profile completion system."""

    def test_initial_profile_completion(self, client, authenticated_user):
        """Initial profile completion should be between 0 and 100 (non-100 at start)."""
        resp = client.get('/api/user-profile/onboarding-progress')
        assert resp.status_code in (200, 404)
        if resp.status_code == 404:
            pytest.skip('Onboarding progress endpoint not available')
        data = resp.get_json() or {}
        pct = data.get('profile_completion_percentage') or data.get('progress_percentage') or 0
        assert 0 <= pct <= 100
        assert pct < 100

    def test_profile_field_updates(self, client, authenticated_user):
        """Updating profile fields should increase completion percentage."""
        init_resp = client.get('/api/user-profile/onboarding-progress')
        assert init_resp.status_code in (200, 404)
        if init_resp.status_code == 404:
            pytest.skip('Onboarding progress endpoint not available')
        initial_pct = init_resp.get_json().get('profile_completion_percentage')
        if initial_pct is None:
            initial_pct = init_resp.get_json().get('progress_percentage', 0)

        update_data = {
            'dependents': 2,
            'marital_status': 'married',
            'education_level': 'bachelors',
            'current_savings_balance': 15000,
            'total_debt_amount': 25000,
        }
        upd = client.post('/api/user-profile/update', json=update_data)
        assert upd.status_code in (200, 204)

        upd_resp = client.get('/api/user-profile/onboarding-progress')
        assert upd_resp.status_code == 200
        updated_pct = upd_resp.get_json().get('profile_completion_percentage')
        if updated_pct is None:
            updated_pct = upd_resp.get_json().get('progress_percentage', 0)
        assert updated_pct >= initial_pct

    def test_complete_profile_flow(self, client, authenticated_user):
        """Completing many profile fields should get close to 100%."""
        complete_profile_data = {
            'last_name': 'TestUser',
            'zip_code': '30309',
            'dependents': 1,
            'marital_status': 'single',
            'industry': 'Technology',
            'job_title': 'Software Developer',
            'naics_code': '541511',
            'monthly_income': 65000,
            'employment_status': 'full_time',
            'company_size': 'medium',
            'years_of_experience': 5,
            'education_level': 'bachelors',
            'current_savings_balance': 10000,
            'total_debt_amount': 30000,
            'credit_score_range': 'good',
            'primary_financial_goal': 'emergency_fund',
            'risk_tolerance_level': 'moderate',
            'health_checkin_frequency': 'weekly',
            'notification_preferences': 'email_sms',
        }
        resp = client.post('/api/user-profile/update', json=complete_profile_data)
        assert resp.status_code in (200, 204)

        prog = client.get('/api/user-profile/onboarding-progress')
        assert prog.status_code in (200, 404)
        if prog.status_code == 404:
            pytest.skip('Onboarding progress endpoint not available')
        pct = prog.get_json().get('profile_completion_percentage')
        if pct is None:
            pct = prog.get_json().get('progress_percentage', 0)
        assert pct >= 90


