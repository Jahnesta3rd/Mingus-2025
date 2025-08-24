#!/usr/bin/env python3
"""
Test script for fixed SQLAlchemy models with shared Base
"""
import sys
import os
from datetime import datetime, date

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_shared_base():
    """Test that all models use the same shared Base"""
    print("=== Testing Shared Base ===")
    
    try:
        from backend.models import Base
        from backend.models import (
            User, UserProfile, OnboardingProgress,
            UserHealthCheckin, HealthSpendingCorrelation
        )
        
        # Verify all models use the same Base
        models = [User, UserProfile, OnboardingProgress, UserHealthCheckin, HealthSpendingCorrelation]
        
        print(f"Shared Base: {Base}")
        for model in models:
            model_base = model.metadata
            print(f"{model.__name__} uses metadata: {model_base}")
            
        # Check that all models are in the same metadata registry
        table_names = list(Base.metadata.tables.keys())
        print(f"Tables registered in shared Base: {table_names}")
        
        expected_tables = ['users', 'user_profiles', 'onboarding_progress', 
                          'user_health_checkins', 'health_spending_correlations']
        
        missing_tables = set(expected_tables) - set(table_names)
        if missing_tables:
            print(f"❌ Missing tables: {missing_tables}")
            return False
        
        print("✅ All models use shared Base correctly")
        return True
        
    except Exception as e:
        print(f"❌ Shared Base Error: {e}")
        return False

def test_model_relationships():
    """Test that relationships can be resolved"""
    print("\n=== Testing Model Relationships ===")
    
    try:
        from backend.models import User, UserProfile, UserHealthCheckin, HealthSpendingCorrelation
        
        # Create model instances (without database)
        user = User(
            email='test@example.com',
            password_hash='hashed_password',
            full_name='Test User'
        )
        
        print("✅ User model created")
        
        # Test that relationships are defined
        assert hasattr(User, 'profile'), "User missing profile relationship"
        assert hasattr(User, 'health_checkins'), "User missing health_checkins relationship"
        assert hasattr(User, 'health_correlations'), "User missing health_correlations relationship"
        
        assert hasattr(UserProfile, 'user'), "UserProfile missing user relationship"
        assert hasattr(UserHealthCheckin, 'user'), "UserHealthCheckin missing user relationship"
        assert hasattr(HealthSpendingCorrelation, 'user'), "HealthSpendingCorrelation missing user relationship"
        
        print("✅ All relationships defined correctly")
        return True
        
    except Exception as e:
        print(f"❌ Relationship Error: {e}")
        return False

def test_model_creation():
    """Test creating model instances"""
    print("\n=== Testing Model Creation ===")
    
    try:
        from backend.models import (
            User, UserProfile, UserHealthCheckin, HealthSpendingCorrelation
        )
        
        # Create test instances
        user = User(
            email='test@example.com',
            password_hash='hashed_password',
            full_name='Test User',
            phone_number='555-1234'
        )
        
        health_checkin = UserHealthCheckin(
            user_id=1,
            checkin_date=date.today(),
            physical_activity_minutes=60,
            physical_activity_level='moderate',
            relationships_rating=8,
            stress_level=3,
            energy_level=7,
            mood_rating=8
        )
        
        correlation = HealthSpendingCorrelation(
            user_id=1,
            analysis_period='weekly',
            health_metric='stress_level',
            spending_category='impulse_purchases',
            correlation_strength=0.73,
            insight_text='High stress correlates with increased impulse spending'
        )
        
        print(f"✅ User: {user}")
        print(f"✅ Health Check-in: {health_checkin}")
        print(f"✅ Correlation: {correlation}")
        
        return True
        
    except Exception as e:
        print(f"❌ Model Creation Error: {e}")
        return False

if __name__ == "__main__":
    print("Testing Fixed Health-Finance Correlation Models\n")
    
    shared_base_success = test_shared_base()
    relationship_success = test_model_relationships()
    creation_success = test_model_creation()
    
    if shared_base_success and relationship_success and creation_success:
        print("\n🎉 ALL TESTS PASSED!")
        print("✅ Shared Base working correctly")
        print("✅ Model relationships resolved")
        print("✅ Model creation successful")
        print("✅ Ready for database initialization")
        
        print("\n=== Next Steps ===")
        print("1. Enable database initialization in app_factory.py")
        print("2. Start Flask app to create tables")
        print("3. Proceed to Prompt 2 (Health Check-in Form)")
        
    else:
        print("\n❌ TESTS FAILED - Fix remaining issues")
        
        print("\n=== Troubleshooting ===")
        print("1. Ensure all model files use 'from .base import Base'")
        print("2. Check that all relationships use back_populates")
        print("3. Verify import order in __init__.py") 