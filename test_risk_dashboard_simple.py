#!/usr/bin/env python3
"""
Simplified Test Suite for Risk-Based Success Metrics Dashboard

This test suite validates the core functionality without requiring ML libraries.
"""

import unittest
import sqlite3
import json
import tempfile
import os
import sys
from datetime import datetime, timedelta

# Add the backend directory to the path
backend_path = os.path.join(os.path.dirname(__file__), 'backend')
sys.path.insert(0, backend_path)

def test_database_schema():
    """Test that the database schema is properly created"""
    print("🧪 Testing Database Schema...")
    
    # Create temporary database
    test_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
    test_db.close()
    
    try:
        # Initialize database with schema
        conn = sqlite3.connect(test_db.name)
        cursor = conn.cursor()
        
        with open('backend/analytics/recommendation_analytics_schema.sql', 'r') as f:
            schema_sql = f.read()
        
        cursor.executescript(schema_sql)
        conn.commit()
        
        # Check that risk tables exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        risk_tables = [
            'user_risk_assessments',
            'risk_interventions',
            'career_protection_outcomes',
            'risk_forecasts',
            'risk_success_stories',
            'risk_analytics_aggregations',
            'risk_dashboard_alerts'
        ]
        
        missing_tables = []
        for table in risk_tables:
            if table not in tables:
                missing_tables.append(table)
        
        if missing_tables:
            print(f"❌ Missing tables: {missing_tables}")
            return False
        
        print("✅ All risk tables created successfully")
        
        # Test inserting data
        cursor.execute('''
            INSERT INTO user_risk_assessments (
                user_id, risk_level, risk_score, risk_factors
            ) VALUES (?, ?, ?, ?)
        ''', ('test_user', 'high', 75.0, '{"industry_volatility": true}'))
        
        cursor.execute('''
            INSERT INTO risk_interventions (
                user_id, risk_assessment_id, intervention_type, intervention_status, intervention_data
            ) VALUES (?, ?, ?, ?, ?)
        ''', ('test_user', 1, 'early_warning', 'triggered', '{"priority": "high"}'))
        
        cursor.execute('''
            INSERT INTO career_protection_outcomes (
                user_id, risk_assessment_id, outcome_type, outcome_details
            ) VALUES (?, ?, ?, ?)
        ''', ('test_user', 1, 'successful_transition', '{"new_company": "Test Corp"}'))
        
        conn.commit()
        conn.close()
        
        print("✅ Data insertion test passed")
        return True
        
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False
    finally:
        os.unlink(test_db.name)

def test_risk_analytics_tracker():
    """Test RiskAnalyticsTracker basic functionality"""
    print("🧪 Testing RiskAnalyticsTracker...")
    
    try:
        from analytics.risk_analytics_tracker import RiskAnalyticsTracker
        
        # Create temporary database
        test_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        test_db.close()
        
        tracker = RiskAnalyticsTracker(test_db.name)
        
        # Test risk assessment
        assessment_id = tracker.assess_user_risk(
            user_id='test_user',
            risk_factors={'industry_volatility': True},
            industry_risk_score=75.0
        )
        
        if not isinstance(assessment_id, int) or assessment_id <= 0:
            print("❌ Risk assessment creation failed")
            return False
        
        print("✅ Risk assessment creation passed")
        
        # Test intervention triggering
        intervention_id = tracker.trigger_intervention(
            user_id='test_user',
            risk_assessment_id=assessment_id,
            intervention_type='early_warning',
            intervention_data={'priority': 'high'}
        )
        
        if not isinstance(intervention_id, int) or intervention_id <= 0:
            print("❌ Intervention triggering failed")
            return False
        
        print("✅ Intervention triggering passed")
        
        # Test outcome tracking
        outcome_id = tracker.track_career_protection_outcome(
            user_id='test_user',
            risk_assessment_id=assessment_id,
            outcome_type='successful_transition',
            outcome_details={'new_company': 'Test Corp'}
        )
        
        if not isinstance(outcome_id, int) or outcome_id <= 0:
            print("❌ Outcome tracking failed")
            return False
        
        print("✅ Outcome tracking passed")
        
        # Test metrics calculation
        metrics = tracker.get_career_protection_metrics('last_30_days')
        
        if not isinstance(metrics, dict):
            print("❌ Metrics calculation failed")
            return False
        
        print("✅ Metrics calculation passed")
        
        os.unlink(test_db.name)
        return True
        
    except Exception as e:
        print(f"❌ RiskAnalyticsTracker test failed: {e}")
        return False

def test_success_metrics_extension():
    """Test extended SuccessMetrics functionality"""
    print("🧪 Testing SuccessMetrics Extension...")
    
    try:
        from analytics.success_metrics import SuccessMetrics
        
        # Create temporary database
        test_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        test_db.close()
        
        metrics = SuccessMetrics(test_db.name)
        
        # Test that new methods exist
        required_methods = [
            'career_protection_success_rate',
            'early_warning_accuracy',
            'risk_intervention_effectiveness',
            'income_protection_rate',
            'unemployment_prevention_rate',
            'get_risk_based_success_metrics'
        ]
        
        for method in required_methods:
            if not hasattr(metrics, method):
                print(f"❌ Missing method: {method}")
                return False
        
        print("✅ All required methods exist")
        
        # Test method calls
        success_rate = metrics.career_protection_success_rate('last_30_days')
        if not isinstance(success_rate, (int, float)):
            print("❌ career_protection_success_rate returned invalid type")
            return False
        
        print("✅ Method calls work correctly")
        
        os.unlink(test_db.name)
        return True
        
    except Exception as e:
        print(f"❌ SuccessMetrics test failed: {e}")
        return False

def test_api_endpoints():
    """Test that API endpoints are properly defined"""
    print("🧪 Testing API Endpoints...")
    
    try:
        # Check if analytics_endpoints.py exists and has risk dashboard endpoints
        endpoints_file = 'backend/api/analytics_endpoints.py'
        if not os.path.exists(endpoints_file):
            print("❌ analytics_endpoints.py not found")
            return False
        
        with open(endpoints_file, 'r') as f:
            content = f.read()
        
        # Check for key risk dashboard endpoints
        required_endpoints = [
            '/risk-dashboard/protection-metrics',
            '/risk-dashboard/success-stories',
            '/risk-dashboard/roi-analysis',
            '/risk-dashboard/predictive-insights',
            '/risk-dashboard/user-outcome',
            '/risk-dashboard/intervention-effectiveness'
        ]
        
        missing_endpoints = []
        for endpoint in required_endpoints:
            if endpoint not in content:
                missing_endpoints.append(endpoint)
        
        if missing_endpoints:
            print(f"❌ Missing endpoints: {missing_endpoints}")
            return False
        
        print("✅ All required API endpoints found")
        return True
        
    except Exception as e:
        print(f"❌ API endpoints test failed: {e}")
        return False

def test_frontend_components():
    """Test that frontend components exist"""
    print("🧪 Testing Frontend Components...")
    
    try:
        frontend_components = [
            'frontend/src/components/RiskSuccessDashboard.tsx',
            'frontend/src/components/RiskAnalyticsVisualization.tsx',
            'frontend/src/components/ComprehensiveRiskDashboard.tsx'
        ]
        
        missing_components = []
        for component in frontend_components:
            if not os.path.exists(component):
                missing_components.append(component)
        
        if missing_components:
            print(f"❌ Missing components: {missing_components}")
            return False
        
        print("✅ All frontend components exist")
        return True
        
    except Exception as e:
        print(f"❌ Frontend components test failed: {e}")
        return False

def run_simple_tests():
    """Run all simple tests"""
    print("🎯 Risk Dashboard - Simple Test Suite")
    print("=" * 50)
    
    tests = [
        ("Database Schema", test_database_schema),
        ("RiskAnalyticsTracker", test_risk_analytics_tracker),
        ("SuccessMetrics Extension", test_success_metrics_extension),
        ("API Endpoints", test_api_endpoints),
        ("Frontend Components", test_frontend_components)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 Running {test_name}...")
        if test_func():
            passed += 1
            print(f"✅ {test_name} PASSED")
        else:
            print(f"❌ {test_name} FAILED")
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Risk dashboard is ready.")
        return True
    else:
        print("⚠️  Some tests failed. Please review the output above.")
        return False

if __name__ == '__main__':
    success = run_simple_tests()
    sys.exit(0 if success else 1)
