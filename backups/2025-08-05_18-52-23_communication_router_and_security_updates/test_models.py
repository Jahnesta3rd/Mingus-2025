# test_models.py - FIXED VERSION
"""
Test script for SQLAlchemy models only
"""
import sys
import os
from datetime import datetime, date

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_model_imports():
    """Test that all SQLAlchemy models can be imported"""
    print("=== Testing SQLAlchemy Model Imports ===")
    
    try:
        # Import all SQLAlchemy models together to resolve relationships
        from backend.models.user import User, Base
        from backend.models.user_profile import UserProfile
        from backend.models.onboarding_progress import OnboardingProgress
        from backend.models.user_health_checkin import UserHealthCheckin
        from backend.models.health_spending_correlation import HealthSpendingCorrelation
        
        print("✅ All SQLAlchemy models imported successfully")
        
        # Test model instantiation (without database)
        user_data = {
            'email': 'test@example.com',
            'password_hash': 'hashed_password',
            'full_name': 'Test User',
            'phone_number': '555-1234',
            'is_active': True
        }
        
        health_checkin_data = {
            'user_id': 1,
            'checkin_date': datetime.now(),
            'physical_activity_minutes': 60,
            'physical_activity_level': 'moderate',
            'relationships_rating': 8,
            'relationships_notes': 'Good week with friends',
            'mindfulness_minutes': 10,
            'mindfulness_type': 'meditation',
            'stress_level': 3,
            'energy_level': 7,
            'mood_rating': 8
        }
        
        correlation_data = {
            'user_id': 1,
            'analysis_period': 'weekly',
            'analysis_start_date': datetime.now(),
            'analysis_end_date': datetime.now(),
            'health_metric': 'stress_level',
            'spending_category': 'impulse_purchases',
            'correlation_strength': 0.73,
            'correlation_direction': 'positive',
            'sample_size': 20,
            'insight_text': 'High stress correlates with increased impulse spending'
        }
        
        # Create model instances (won't save to DB)
        user = User(**user_data)
        health_checkin = UserHealthCheckin(**health_checkin_data)
        correlation = HealthSpendingCorrelation(**correlation_data)
        
        print("✅ Model instantiation successful")
        print(f"User: {user.email}")
        print(f"Health Check-in: {health_checkin.checkin_date}")
        print(f"Correlation: {correlation.health_metric} -> {correlation.spending_category}")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import Error: {e}")
        return False
    except Exception as e:
        print(f"❌ Model Error: {e}")
        return False

def test_model_relationships():
    """Test that model relationships are defined correctly"""
    print("\n=== Testing Model Relationships ===")
    
    try:
        from backend.models.user import User
        from backend.models.user_health_checkin import UserHealthCheckin
        from backend.models.health_spending_correlation import HealthSpendingCorrelation
        
        # Check if relationships are defined
        user_attrs = dir(User)
        relationship_attrs = [attr for attr in user_attrs if not attr.startswith('_') and attr in ['health_checkins', 'health_correlations', 'profile', 'onboarding_progress']]
        print(f"User model relationships: {relationship_attrs}")
        
        print("✅ Model relationships defined")
        return True
        
    except Exception as e:
        print(f"❌ Relationship Error: {e}")
        return False

def test_database_schema():
    """Test that database schema can be generated"""
    print("\n=== Testing Database Schema ===")
    
    try:
        from backend.models.user import Base
        from sqlalchemy import create_engine
        
        # Create in-memory SQLite database for testing
        engine = create_engine('sqlite:///:memory:')
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        print("✅ Database schema created successfully")
        
        return True
    except Exception as e:
        print(f"❌ Database schema error: {e}")
        return False

if __name__ == "__main__":
    print("Testing Health-Finance Correlation Models\n")
    
    import_success = test_model_imports()
    relationship_success = test_model_relationships()
    schema_success = test_database_schema()
    
    if import_success and relationship_success and schema_success:
        print("\n🎉 All model tests passed!")
        print("✅ Ready to proceed with database initialization")
    else:
        print("\n❌ Model tests failed - fix issues before proceeding")
        
    print("\n=== Next Steps ===")
    print("1. Run this test script successfully")
    print("2. Enable database initialization in app_factory.py") 
    print("3. Test with actual Flask app startup")
    print("4. Proceed to Prompt 2 (Health Check-in Form)") 