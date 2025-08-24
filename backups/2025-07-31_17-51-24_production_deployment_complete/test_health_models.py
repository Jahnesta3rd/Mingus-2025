#!/usr/bin/env python3
"""
Test script for health-finance correlation models
"""

import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_model_imports():
    """Test that all models can be imported successfully"""
    try:
        from backend.models import (
            User, UserProfile, OnboardingProgress, 
            UserHealthCheckin, HealthSpendingCorrelation, Base
        )
        print("✅ All models imported successfully")
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

def test_model_creation():
    """Test that models can be instantiated"""
    try:
        from backend.models import UserHealthCheckin, HealthSpendingCorrelation
        from datetime import datetime
        
        # Test UserHealthCheckin creation
        checkin = UserHealthCheckin(
            user_id="test-user-id",
            checkin_date=datetime.now(),
            physical_activity_minutes=30,
            physical_activity_level="moderate",
            relationships_rating=8,
            stress_level=5,
            energy_level=7,
            mood_rating=8
        )
        print("✅ UserHealthCheckin created successfully")
        
        # Test HealthSpendingCorrelation creation
        correlation = HealthSpendingCorrelation(
            user_id="test-user-id",
            analysis_period="weekly",
            analysis_start_date=datetime.now(),
            analysis_end_date=datetime.now(),
            health_metric="stress_level",
            spending_category="entertainment",
            correlation_strength=0.75,
            correlation_direction="positive",
            sample_size=20
        )
        print("✅ HealthSpendingCorrelation created successfully")
        
        return True
    except Exception as e:
        print(f"❌ Model creation error: {e}")
        return False

def test_model_methods():
    """Test model methods and properties"""
    try:
        from backend.models import UserHealthCheckin, HealthSpendingCorrelation
        from datetime import datetime
        
        # Test UserHealthCheckin methods
        checkin = UserHealthCheckin(
            user_id="test-user-id",
            checkin_date=datetime.now(),
            physical_activity_minutes=150,
            stress_level=3,
            energy_level=8,
            mood_rating=9,
            relationships_rating=8
        )
        
        health_score = checkin.calculate_health_score()
        print(f"✅ Health score calculated: {health_score:.2f}")
        
        # Test HealthSpendingCorrelation methods
        correlation = HealthSpendingCorrelation(
            user_id="test-user-id",
            analysis_period="weekly",
            analysis_start_date=datetime.now(),
            analysis_end_date=datetime.now(),
            health_metric="stress_level",
            spending_category="entertainment",
            correlation_strength=0.75,
            correlation_direction="positive",
            sample_size=20,
            p_value=0.01
        )
        
        interpretation = correlation.get_correlation_interpretation()
        print(f"✅ Correlation interpretation: {interpretation}")
        
        is_significant = correlation.is_statistically_significant()
        print(f"✅ Statistically significant: {is_significant}")
        
        return True
    except Exception as e:
        print(f"❌ Model method test error: {e}")
        return False

def test_database_schema():
    """Test that database schema can be generated"""
    try:
        from backend.models import Base
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

def main():
    """Run all tests"""
    print("🧪 Testing Health-Finance Correlation Models")
    print("=" * 50)
    
    tests = [
        ("Model Imports", test_model_imports),
        ("Model Creation", test_model_creation),
        ("Model Methods", test_model_methods),
        ("Database Schema", test_database_schema),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 Running {test_name}...")
        if test_func():
            passed += 1
        else:
            print(f"❌ {test_name} failed")
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Models are ready to use.")
        return 0
    else:
        print("⚠️  Some tests failed. Please check the errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 