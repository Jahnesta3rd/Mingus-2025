#!/usr/bin/env python3
"""
Basic Test Suite for Risk-Based Success Metrics Dashboard

This test suite validates the core functionality with minimal dependencies.
"""

import unittest
import sqlite3
import json
import tempfile
import os
import sys
from datetime import datetime, timedelta

def test_database_creation():
    """Test that the database can be created and basic tables exist"""
    print("🧪 Testing Database Creation...")
    
    # Create temporary database
    test_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
    test_db.close()
    
    try:
        conn = sqlite3.connect(test_db.name)
        cursor = conn.cursor()
        
        # Create basic tables without foreign key constraints
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_risk_assessments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                risk_level TEXT NOT NULL,
                risk_score REAL NOT NULL,
                risk_factors TEXT,
                assessment_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS risk_interventions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                risk_assessment_id INTEGER NOT NULL,
                intervention_type TEXT NOT NULL,
                intervention_status TEXT DEFAULT 'triggered',
                intervention_data TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS career_protection_outcomes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                risk_assessment_id INTEGER NOT NULL,
                outcome_type TEXT NOT NULL,
                outcome_details TEXT,
                outcome_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        
        # Test inserting data
        cursor.execute('''
            INSERT INTO user_risk_assessments (user_id, risk_level, risk_score, risk_factors)
            VALUES (?, ?, ?, ?)
        ''', ('test_user', 'high', 75.0, '{"industry_volatility": true}'))
        
        cursor.execute('''
            INSERT INTO risk_interventions (user_id, risk_assessment_id, intervention_type, intervention_data)
            VALUES (?, ?, ?, ?)
        ''', ('test_user', 1, 'early_warning', '{"priority": "high"}'))
        
        cursor.execute('''
            INSERT INTO career_protection_outcomes (user_id, risk_assessment_id, outcome_type, outcome_details)
            VALUES (?, ?, ?, ?)
        ''', ('test_user', 1, 'successful_transition', '{"new_company": "Test Corp"}'))
        
        conn.commit()
        
        # Verify data was inserted
        cursor.execute("SELECT COUNT(*) FROM user_risk_assessments")
        count = cursor.fetchone()[0]
        
        if count != 1:
            print("❌ Data insertion failed")
            return False
        
        print("✅ Database creation and data insertion successful")
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False
    finally:
        os.unlink(test_db.name)

def test_risk_analytics_tracker_import():
    """Test that RiskAnalyticsTracker can be imported"""
    print("🧪 Testing RiskAnalyticsTracker Import...")
    
    try:
        # Add backend to path
        backend_path = os.path.join(os.path.dirname(__file__), 'backend')
        sys.path.insert(0, backend_path)
        
        from analytics.risk_analytics_tracker import RiskAnalyticsTracker
        
        print("✅ RiskAnalyticsTracker imported successfully")
        return True
        
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False

def test_success_metrics_import():
    """Test that SuccessMetrics can be imported"""
    print("🧪 Testing SuccessMetrics Import...")
    
    try:
        # Add backend to path
        backend_path = os.path.join(os.path.dirname(__file__), 'backend')
        sys.path.insert(0, backend_path)
        
        from analytics.success_metrics import SuccessMetrics
        
        print("✅ SuccessMetrics imported successfully")
        return True
        
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False

def test_risk_predictive_analytics_import():
    """Test that RiskPredictiveAnalytics can be imported"""
    print("🧪 Testing RiskPredictiveAnalytics Import...")
    
    try:
        # Add backend to path
        backend_path = os.path.join(os.path.dirname(__file__), 'backend')
        sys.path.insert(0, backend_path)
        
        from analytics.risk_predictive_analytics import RiskPredictiveAnalytics
        
        print("✅ RiskPredictiveAnalytics imported successfully")
        return True
        
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False

def test_risk_success_dashboard_import():
    """Test that RiskSuccessDashboard can be imported"""
    print("🧪 Testing RiskSuccessDashboard Import...")
    
    try:
        # Add backend to path
        backend_path = os.path.join(os.path.dirname(__file__), 'backend')
        sys.path.insert(0, backend_path)
        
        from analytics.risk_success_dashboard import RiskSuccessDashboard
        
        print("✅ RiskSuccessDashboard imported successfully")
        return True
        
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False

def test_api_endpoints_file():
    """Test that API endpoints file exists and has required content"""
    print("🧪 Testing API Endpoints File...")
    
    try:
        endpoints_file = 'backend/api/analytics_endpoints.py'
        if not os.path.exists(endpoints_file):
            print("❌ analytics_endpoints.py not found")
            return False
        
        with open(endpoints_file, 'r') as f:
            content = f.read()
        
        # Check for key risk dashboard endpoints
        required_endpoints = [
            'risk-dashboard/protection-metrics',
            'risk-dashboard/success-stories',
            'risk-dashboard/roi-analysis'
        ]
        
        missing_endpoints = []
        for endpoint in required_endpoints:
            if endpoint not in content:
                missing_endpoints.append(endpoint)
        
        if missing_endpoints:
            print(f"❌ Missing endpoints: {missing_endpoints}")
            return False
        
        print("✅ API endpoints file is valid")
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

def test_schema_file():
    """Test that the schema file exists and is valid SQL"""
    print("🧪 Testing Schema File...")
    
    try:
        schema_file = 'backend/analytics/recommendation_analytics_schema.sql'
        if not os.path.exists(schema_file):
            print("❌ Schema file not found")
            return False
        
        with open(schema_file, 'r') as f:
            content = f.read()
        
        # Check for key risk tables
        required_tables = [
            'user_risk_assessments',
            'risk_interventions',
            'career_protection_outcomes',
            'risk_forecasts',
            'risk_success_stories'
        ]
        
        missing_tables = []
        for table in required_tables:
            if f'CREATE TABLE.*{table}' not in content:
                missing_tables.append(table)
        
        if missing_tables:
            print(f"❌ Missing table definitions: {missing_tables}")
            return False
        
        print("✅ Schema file is valid")
        return True
        
    except Exception as e:
        print(f"❌ Schema file test failed: {e}")
        return False

def run_basic_tests():
    """Run all basic tests"""
    print("🎯 Risk Dashboard - Basic Test Suite")
    print("=" * 50)
    
    tests = [
        ("Database Creation", test_database_creation),
        ("RiskAnalyticsTracker Import", test_risk_analytics_tracker_import),
        ("SuccessMetrics Import", test_success_metrics_import),
        ("RiskPredictiveAnalytics Import", test_risk_predictive_analytics_import),
        ("RiskSuccessDashboard Import", test_risk_success_dashboard_import),
        ("API Endpoints File", test_api_endpoints_file),
        ("Frontend Components", test_frontend_components),
        ("Schema File", test_schema_file)
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
        print("🎉 All tests passed! Risk dashboard components are ready.")
        return True
    else:
        print("⚠️  Some tests failed. Please review the output above.")
        return False

if __name__ == '__main__':
    success = run_basic_tests()
    sys.exit(0 if success else 1)
