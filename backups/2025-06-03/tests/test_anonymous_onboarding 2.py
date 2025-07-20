import pytest
from datetime import datetime, timezone
from typing import Dict, Any
from backend.models.onboarding import (
    AnonymousOnboardingCreate,
    AnonymousOnboardingResponse,
    FinancialChallengeType,
    StressHandlingType,
    MotivationType
)
from backend.services.onboarding_service import OnboardingService
from pydantic import ValidationError

pytestmark = pytest.mark.asyncio

class TestAnonymousOnboarding:
    async def test_create_anonymous_onboarding(
        self,
        onboarding_service: OnboardingService,
        sample_anonymous_onboarding_data: Dict[str, Any]
    ):
        """Test creating an anonymous onboarding response."""
        # Create onboarding data
        onboarding_data = AnonymousOnboardingCreate(**sample_anonymous_onboarding_data)
        response = await onboarding_service.create_anonymous_onboarding(onboarding_data)

        # Verify response
        assert response.id == 1
        assert response.financial_challenge == FinancialChallengeType.EMERGENCY_SAVINGS
        assert StressHandlingType.EXERCISE in response.stress_handling
        assert MotivationType.FAMILY_GOALS in response.motivation
        assert response.monthly_income == 5000.0
        assert response.session_id == sample_anonymous_onboarding_data["session_id"]
        assert response.created_at is not None

    async def test_get_anonymous_onboarding(
        self,
        onboarding_service: OnboardingService,
        sample_anonymous_onboarding_data: Dict[str, Any]
    ):
        """Test retrieving anonymous onboarding responses."""
        # Create test data
        onboarding_data = AnonymousOnboardingCreate(**sample_anonymous_onboarding_data)
        await onboarding_service.create_anonymous_onboarding(onboarding_data)

        # Retrieve responses
        responses = await onboarding_service.get_anonymous_onboarding(
            sample_anonymous_onboarding_data["session_id"]
        )

        # Verify responses
        assert len(responses) == 1
        assert responses[0].session_id == sample_anonymous_onboarding_data["session_id"]
        assert responses[0].financial_challenge == sample_anonymous_onboarding_data["financial_challenge"]

    async def test_convert_anonymous_to_user(
        self,
        onboarding_service: OnboardingService,
        sample_anonymous_onboarding_data: Dict[str, Any]
    ):
        """Test converting anonymous responses to user responses."""
        # Create test data
        onboarding_data = AnonymousOnboardingCreate(**sample_anonymous_onboarding_data)
        await onboarding_service.create_anonymous_onboarding(onboarding_data)

        # Convert to user
        user_id = "test-user-123"
        result = await onboarding_service.convert_anonymous_to_user(
            session_id=sample_anonymous_onboarding_data["session_id"],
            user_id=user_id
        )

        # Verify conversion
        assert result.user_id == user_id
        assert result.converted_to_signup is True
        assert result.conversion_date is not None

    async def test_get_anonymous_onboarding_stats(
        self,
        onboarding_service: OnboardingService,
        sample_anonymous_onboarding_data: Dict[str, Any]
    ):
        """Test retrieving anonymous onboarding statistics."""
        # Create multiple test responses
        onboarding_data = AnonymousOnboardingCreate(**sample_anonymous_onboarding_data)
        await onboarding_service.create_anonymous_onboarding(onboarding_data)

        # Create another response with different session_id
        data2 = sample_anonymous_onboarding_data.copy()
        data2["session_id"] = "550e8400-e29b-41d4-a716-446655440001"
        data2["monthly_income"] = 7000.0
        onboarding_data2 = AnonymousOnboardingCreate(**data2)
        await onboarding_service.create_anonymous_onboarding(onboarding_data2)

        # Convert one response
        await onboarding_service.convert_anonymous_to_user(
            session_id=sample_anonymous_onboarding_data["session_id"],
            user_id="test-user-123"
        )

        # Get stats
        stats = await onboarding_service.get_anonymous_onboarding_stats()

        # Verify stats
        assert stats.total_responses == 2
        assert stats.conversion_rate == 0.5  # 1 out of 2 converted
        assert stats.average_income == 6000.0  # (5000 + 7000) / 2

    @pytest.mark.parametrize("invalid_field,invalid_value,expected_error", [
        ("monthly_income", -1000, "Input should be greater than or equal to 0"),
        ("risk_tolerance", 11, "Input should be less than or equal to 10"),
        ("preferred_contact_method", "invalid", "String should match pattern '^(email|sms|both)$'"),
        ("contact_info", "invalid-email", "Invalid email format"),
    ])
    async def test_invalid_data_validation(
        self,
        onboarding_service: OnboardingService,
        sample_anonymous_onboarding_data: Dict[str, Any],
        invalid_field: str,
        invalid_value: Any,
        expected_error: str
    ):
        """Test validation of invalid data."""
        # Modify sample data with invalid value
        invalid_data = sample_anonymous_onboarding_data.copy()
        invalid_data[invalid_field] = invalid_value

        # Attempt to create with invalid data
        with pytest.raises(ValidationError) as exc_info:
            onboarding_data = AnonymousOnboardingCreate(**invalid_data)
            await onboarding_service.create_anonymous_onboarding(onboarding_data)

        # Verify error message
        assert expected_error in str(exc_info.value)

    async def test_duplicate_session_responses(
        self,
        onboarding_service: OnboardingService,
        sample_anonymous_onboarding_data: Dict[str, Any]
    ):
        """Test handling multiple responses from same session."""
        # Create first response
        onboarding_data1 = AnonymousOnboardingCreate(**sample_anonymous_onboarding_data)
        response1 = await onboarding_service.create_anonymous_onboarding(onboarding_data1)

        # Create second response with same session_id but different answers
        data2 = sample_anonymous_onboarding_data.copy()
        data2["financial_challenge"] = FinancialChallengeType.DEBT
        data2["monthly_income"] = 6000.0
        onboarding_data2 = AnonymousOnboardingCreate(**data2)
        response2 = await onboarding_service.create_anonymous_onboarding(onboarding_data2)

        # Get all responses for session
        responses = await onboarding_service.get_anonymous_onboarding(
            sample_anonymous_onboarding_data["session_id"]
        )

        # Verify both responses are stored and ordered by creation date
        assert len(responses) == 2
        assert responses[0].id == response1.id
        assert responses[1].id == response2.id
        assert responses[0].financial_challenge == FinancialChallengeType.EMERGENCY_SAVINGS
        assert responses[1].financial_challenge == FinancialChallengeType.DEBT

    async def test_conversion_idempotency(
        self,
        onboarding_service: OnboardingService,
        sample_anonymous_onboarding_data: Dict[str, Any]
    ):
        """Test that converting the same session multiple times is idempotent."""
        # Create test data
        onboarding_data = AnonymousOnboardingCreate(**sample_anonymous_onboarding_data)
        await onboarding_service.create_anonymous_onboarding(onboarding_data)

        # Convert first time
        user_id = "test-user-123"
        result1 = await onboarding_service.convert_anonymous_to_user(
            session_id=sample_anonymous_onboarding_data["session_id"],
            user_id=user_id
        )

        # Convert second time
        result2 = await onboarding_service.convert_anonymous_to_user(
            session_id=sample_anonymous_onboarding_data["session_id"],
            user_id=user_id
        )

        # Verify both conversions return same result
        assert result1.user_id == result2.user_id
        assert result1.conversion_date == result2.conversion_date 