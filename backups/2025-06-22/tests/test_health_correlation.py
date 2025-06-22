import pytest
from unittest.mock import MagicMock
import pandas as pd
import numpy as np

# Assuming scipy is installed and in the environment
from scipy import stats

from backend.services.health_correlation_service import HealthCorrelationService
from backend.models.user import User
from backend.models.user_health_checkin import UserHealthCheckin

# Mock data for testing
def create_mock_health_data(user_id, num_entries=30):
    """Generates mock health check-in data for a user."""
    checkins = []
    for i in range(num_entries):
        checkin = UserHealthCheckin(
            user_id=user_id,
            mood=np.random.randint(1, 10),
            energy=np.random.randint(1, 10),
            sleep_quality=np.random.randint(1, 10),
            stress_level=np.random.randint(1, 10),
        )
        checkins.append(checkin)
    return checkins

def create_mock_spending_data(num_entries=30):
    """Generates mock spending data."""
    return pd.DataFrame({
        'date': pd.to_datetime(pd.date_range(start='2023-01-01', periods=num_entries)),
        'amount': np.random.uniform(10, 200, num_entries)
    })

@pytest.fixture
def mock_db_session():
    """Fixture for a mocked database session."""
    return MagicMock()

def test_calculate_correlation_valid_data(mock_db_session):
    """Test correlation calculation with valid, correlated data."""
    user = User(id=1, email="test@example.com")
    health_data = create_mock_health_data(user.id)
    spending_data = create_mock_spending_data()

    # Create a positive correlation between mood and spending
    spending_data['amount'] = [h.mood * 10 + np.random.normal(0, 5) for h in health_data]

    service = HealthCorrelationService(db_session=mock_db_session)
    correlation, p_value = service._calculate_correlation(pd.Series([h.mood for h in health_data]), spending_data['amount'])

    assert correlation is not None
    assert p_value is not None
    assert correlation > 0.5  # Expect a strong positive correlation
    assert -1 <= correlation <= 1

def test_calculate_correlation_no_variance(mock_db_session):
    """Test correlation calculation when one of the series has no variance."""
    service = HealthCorrelationService(db_session=mock_db_session)
    series1 = pd.Series([5, 5, 5, 5, 5])
    series2 = pd.Series([10, 20, 15, 25, 30])
    
    correlation, p_value = service._calculate_correlation(series1, series2)
    
    assert correlation is None
    assert p_value is None

def test_calculate_correlation_insufficient_data(mock_db_session):
    """Test correlation with insufficient data (less than 2 points)."""
    service = HealthCorrelationService(db_session=mock_db_session)
    series1 = pd.Series([5])
    series2 = pd.Series([10])

    correlation, p_value = service._calculate_correlation(series1, series2)
    assert correlation is None
    assert p_value is None

def test_generate_insights_positive_correlation(mock_db_session):
    """Test insight generation for a significant positive correlation."""
    service = HealthCorrelationService(db_session=mock_db_session)
    correlation_results = {
        'mood': (0.8, 0.01),
        'energy': (0.2, 0.4)
    }
    insights = service._generate_insights(correlation_results)
    
    assert len(insights) == 1
    assert "positively correlated" in insights[0]
    assert "mood" in insights[0]

def test_generate_insights_negative_correlation(mock_db_session):
    """Test insight generation for a significant negative correlation."""
    service = HealthCorrelationService(db_session=mock_db_session)
    correlation_results = {
        'stress_level': (-0.7, 0.02),
        'sleep_quality': (0.1, 0.6)
    }
    insights = service._generate_insights(correlation_results)

    assert len(insights) == 1
    assert "negatively correlated" in insights[0]
    assert "stress" in insights[0]

def test_generate_insights_no_significant_correlation(mock_db_session):
    """Test insight generation when no significant correlation is found."""
    service = HealthCorrelationService(db_session=mock_db_session)
    correlation_results = {
        'mood': (0.1, 0.5),
        'energy': (-0.05, 0.8)
    }
    insights = service._generate_insights(correlation_results)
    
    assert len(insights) == 1
    assert "No significant correlations" in insights[0]

# More complex integration-style test for the service
def test_get_health_spending_correlation_and_insights(mock_db_session):
    """
    Integration test for the main service method, mocking data retrieval.
    """
    user_id = 1
    health_data = create_mock_health_data(user_id, 30)
    spending_data = create_mock_spending_data(30)
    
    # Mock the database query for health data
    mock_db_session.query.return_value.filter.return_value.order_by.return_value.all.return_value = health_data

    service = HealthCorrelationService(db_session=mock_db_session)

    # Mock the internal spending data retrieval
    service._get_spending_data = MagicMock(return_value=spending_data)
    
    result = service.get_health_spending_correlation_and_insights(user_id)

    assert 'correlations' in result
    assert 'insights' in result
    assert 'mood' in result['correlations']
    assert 'energy' in result['correlations']
    assert 'sleep_quality' in result['correlations']
    assert 'stress_level' in result['correlations']
    
    service._get_spending_data.assert_called_once_with(user_id)
    
    # Check if a plausible insight is generated
    assert isinstance(result['insights'], list)
    assert len(result['insights']) > 0
    assert isinstance(result['insights'][0], str) 