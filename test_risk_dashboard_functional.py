#!/usr/bin/env python3
"""
Functional Test Suite for Risk-Based Success Metrics Dashboard

This test suite validates the actual functionality of the risk dashboard system.
"""

import unittest
import sqlite3
import json
import tempfile
import os
import sys
import asyncio
from datetime import datetime, timedelta

# Add backend to path
backend_path = os.path.join(os.path.dirname(__file__), 'backend')
sys.path.insert(0, backend_path)

def test_risk_analytics_tracker_functionality():
    """Test RiskAnalyticsTracker actual functionality"""
    print("🧪 Testing RiskAnalyticsTracker Functionality...")
    
    try:
        from analytics.risk_analytics_tracker import RiskAnalyticsTracker
        
        # Create temporary database
        test_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        test_db.close()
        
        tracker = RiskAnalyticsTracker(test_db.name)
        
        # Test 1: Risk assessment creation
        assessment_id = tracker.assess_user_risk(
            user_id='test_user_1',
            risk_factors={'industry_volatility': True, 'company_layoffs': True},
            industry_risk_score=85.0,
            company_risk_score=90.0,
            assessment_confidence=0.9
        )
        
        if not isinstance(assessment_id, int) or assessment_id <= 0:
            print("❌ Risk assessment creation failed")
            return False
        
        print("✅ Risk assessment creation successful")
        
        # Test 2: Intervention triggering
        intervention_id = tracker.trigger_intervention(
            user_id='test_user_1',
            risk_assessment_id=assessment_id,
            intervention_type='early_warning',
            intervention_data={'priority': 'critical', 'message': 'High risk detected'}
        )
        
        if not isinstance(intervention_id, int) or intervention_id <= 0:
            print("❌ Intervention triggering failed")
            return False
        
        print("✅ Intervention triggering successful")
        
        # Test 3: Outcome tracking
        outcome_id = tracker.track_career_protection_outcome(
            user_id='test_user_1',
            risk_assessment_id=assessment_id,
            outcome_type='successful_transition',
            outcome_details={'new_company': 'Safe Corp', 'role': 'Senior Developer'},
            intervention_id=intervention_id,
            salary_change=25000.0,
            time_to_new_role=30,
            satisfaction_score=5,
            would_recommend=True
        )
        
        if not isinstance(outcome_id, int) or outcome_id <= 0:
            print("❌ Outcome tracking failed")
            return False
        
        print("✅ Outcome tracking successful")
        
        # Test 4: Success story logging
        story_id = tracker.log_success_story(
            user_id='test_user_1',
            story_type='early_transition',
            story_title='Early Warning Saved My Career',
            story_description='Received early warning and successfully transitioned before layoffs',
            original_risk_factors={'industry_volatility': True, 'company_layoffs': True},
            intervention_timeline={'warning': '2024-01-01', 'job_found': '2024-01-31'},
            outcome_details={'salary_increase': 25000, 'job_security_improved': True},
            user_satisfaction=5,
            would_recommend=True
        )
        
        if not isinstance(story_id, int) or story_id <= 0:
            print("❌ Success story logging failed")
            return False
        
        print("✅ Success story logging successful")
        
        # Test 5: Metrics calculation
        metrics = tracker.get_career_protection_metrics('last_30_days')
        
        if not isinstance(metrics, dict):
            print("❌ Metrics calculation failed")
            return False
        
        required_keys = ['users_at_high_risk', 'successful_transitions', 'overall_success_rate']
        for key in required_keys:
            if key not in metrics:
                print(f"❌ Missing metric key: {key}")
                return False
        
        print("✅ Metrics calculation successful")
        
        # Test 6: Intervention effectiveness
        intervention_metrics = tracker.get_intervention_effectiveness('last_30_days')
        
        if not isinstance(intervention_metrics, dict):
            print("❌ Intervention effectiveness calculation failed")
            return False
        
        print("✅ Intervention effectiveness calculation successful")
        
        # Test 7: Success stories retrieval
        stories = tracker.get_risk_success_stories(limit=5)
        
        if not isinstance(stories, list):
            print("❌ Success stories retrieval failed")
            return False
        
        print("✅ Success stories retrieval successful")
        
        os.unlink(test_db.name)
        return True
        
    except Exception as e:
        print(f"❌ RiskAnalyticsTracker functionality test failed: {e}")
        import traceback
        traceback.print_exc()
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
        
        # Test that new methods exist and are callable
        required_methods = [
            'career_protection_success_rate',
            'early_warning_accuracy',
            'risk_intervention_effectiveness',
            'income_protection_rate',
            'unemployment_prevention_rate',
            'get_risk_based_success_metrics'
        ]
        
        for method_name in required_methods:
            if not hasattr(metrics, method_name):
                print(f"❌ Missing method: {method_name}")
                return False
            
            method = getattr(metrics, method_name)
            if not callable(method):
                print(f"❌ Method {method_name} is not callable")
                return False
        
        print("✅ All required methods exist and are callable")
        
        # Test method calls (they should return valid values even with no data)
        success_rate = metrics.career_protection_success_rate('last_30_days')
        if not isinstance(success_rate, (int, float)):
            print("❌ career_protection_success_rate returned invalid type")
            return False
        
        early_warning = metrics.early_warning_accuracy('last_30_days')
        if not isinstance(early_warning, (int, float)):
            print("❌ early_warning_accuracy returned invalid type")
            return False
        
        comprehensive_metrics = metrics.get_risk_based_success_metrics('last_30_days')
        if not isinstance(comprehensive_metrics, dict):
            print("❌ get_risk_based_success_metrics returned invalid type")
            return False
        
        required_keys = ['time_period', 'career_protection_metrics', 'user_journey_analytics']
        for key in required_keys:
            if key not in comprehensive_metrics:
                print(f"❌ Missing key in comprehensive metrics: {key}")
                return False
        
        print("✅ Method calls return valid data")
        
        os.unlink(test_db.name)
        return True
        
    except Exception as e:
        print(f"❌ SuccessMetrics extension test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_risk_predictive_analytics():
    """Test RiskPredictiveAnalytics functionality"""
    print("🧪 Testing RiskPredictiveAnalytics...")
    
    try:
        from analytics.risk_predictive_analytics import RiskPredictiveAnalytics
        
        # Create temporary database
        test_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        test_db.close()
        
        analytics = RiskPredictiveAnalytics(test_db.name)
        
        # Test 1: Risk forecast generation
        forecasts = analytics.generate_risk_forecasts(
            forecast_type='industry_risk',
            target_entities=['technology', 'finance'],
            forecast_horizon_days=30
        )
        
        if not isinstance(forecasts, list):
            print("❌ Risk forecast generation failed")
            return False
        
        print("✅ Risk forecast generation successful")
        
        # Test 2: Emerging risk factor detection
        patterns = analytics.identify_emerging_risk_factors(30)
        
        if not isinstance(patterns, list):
            print("❌ Emerging risk factor detection failed")
            return False
        
        print("✅ Emerging risk factor detection successful")
        
        # Test 3: User risk trajectory prediction
        trajectory = analytics.predict_user_risk_trajectory('test_user', 90)
        
        if not isinstance(trajectory, dict):
            print("❌ User risk trajectory prediction failed")
            return False
        
        print("✅ User risk trajectory prediction successful")
        
        # Test 4: Market risk heat map
        heat_map = analytics.generate_market_risk_heat_map(30)
        
        if not isinstance(heat_map, dict):
            print("❌ Market risk heat map generation failed")
            return False
        
        print("✅ Market risk heat map generation successful")
        
        # Test 5: Forecast accuracy metrics
        accuracy = analytics.get_forecast_accuracy_metrics(30)
        
        if not isinstance(accuracy, dict):
            print("❌ Forecast accuracy metrics failed")
            return False
        
        print("✅ Forecast accuracy metrics successful")
        
        os.unlink(test_db.name)
        return True
        
    except Exception as e:
        print(f"❌ RiskPredictiveAnalytics test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_risk_success_dashboard():
    """Test RiskSuccessDashboard functionality"""
    print("🧪 Testing RiskSuccessDashboard...")
    
    try:
        from analytics.risk_success_dashboard import RiskSuccessDashboard
        
        # Create temporary database
        test_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        test_db.close()
        
        dashboard = RiskSuccessDashboard(test_db.name)
        
        # Test 1: Dashboard initialization
        if not hasattr(dashboard, 'risk_analytics'):
            print("❌ Dashboard initialization failed - missing risk_analytics")
            return False
        
        if not hasattr(dashboard, 'predictive_engine'):
            print("❌ Dashboard initialization failed - missing predictive_engine")
            return False
        
        print("✅ Dashboard initialization successful")
        
        # Test 2: Career protection report generation
        async def test_report():
            report = await dashboard.generate_career_protection_report('last_30_days')
            return report
        
        report = asyncio.run(test_report())
        
        if not isinstance(report, dict):
            print("❌ Career protection report generation failed")
            return False
        
        required_keys = ['report_generated_at', 'time_period', 'protection_effectiveness']
        for key in required_keys:
            if key not in report:
                print(f"❌ Missing key in report: {key}")
                return False
        
        print("✅ Career protection report generation successful")
        
        # Test 3: ROI analysis generation
        async def test_roi():
            roi = await dashboard.generate_roi_analysis()
            return roi
        
        roi = asyncio.run(test_roi())
        
        if not isinstance(roi, dict):
            print("❌ ROI analysis generation failed")
            return False
        
        print("✅ ROI analysis generation successful")
        
        # Test 4: Risk heat map generation
        heat_map = dashboard.get_risk_heat_map(30)
        
        if not hasattr(heat_map, 'industries'):
            print("❌ Risk heat map generation failed")
            return False
        
        print("✅ Risk heat map generation successful")
        
        # Test 5: Protection trends analysis
        trends = dashboard.get_protection_success_trends(30)
        
        if not isinstance(trends, dict):
            print("❌ Protection trends analysis failed")
            return False
        
        print("✅ Protection trends analysis successful")
        
        os.unlink(test_db.name)
        return True
        
    except Exception as e:
        print(f"❌ RiskSuccessDashboard test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_end_to_end_workflow():
    """Test complete end-to-end workflow"""
    print("🧪 Testing End-to-End Workflow...")
    
    try:
        from analytics.risk_analytics_tracker import RiskAnalyticsTracker
        from analytics.risk_predictive_analytics import RiskPredictiveAnalytics
        from analytics.risk_success_dashboard import RiskSuccessDashboard
        from analytics.success_metrics import SuccessMetrics
        
        # Create temporary database
        test_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        test_db.close()
        
        # Initialize all components
        tracker = RiskAnalyticsTracker(test_db.name)
        analytics = RiskPredictiveAnalytics(test_db.name)
        dashboard = RiskSuccessDashboard(test_db.name)
        metrics = SuccessMetrics(test_db.name)
        
        # Step 1: Create risk assessment
        assessment_id = tracker.assess_user_risk(
            user_id='e2e_test_user',
            risk_factors={'industry_volatility': True, 'company_layoffs': True},
            industry_risk_score=85.0,
            company_risk_score=90.0,
            assessment_confidence=0.9
        )
        
        if not isinstance(assessment_id, int) or assessment_id <= 0:
            print("❌ Step 1: Risk assessment creation failed")
            return False
        
        print("✅ Step 1: Risk assessment created")
        
        # Step 2: Trigger intervention
        intervention_id = tracker.trigger_intervention(
            user_id='e2e_test_user',
            risk_assessment_id=assessment_id,
            intervention_type='early_warning',
            intervention_data={'priority': 'critical'}
        )
        
        if not isinstance(intervention_id, int) or intervention_id <= 0:
            print("❌ Step 2: Intervention triggering failed")
            return False
        
        print("✅ Step 2: Intervention triggered")
        
        # Step 3: Track successful outcome
        outcome_id = tracker.track_career_protection_outcome(
            user_id='e2e_test_user',
            risk_assessment_id=assessment_id,
            outcome_type='successful_transition',
            outcome_details={'new_company': 'Safe Corp', 'role': 'Lead Developer'},
            intervention_id=intervention_id,
            salary_change=25000.0,
            time_to_new_role=30,
            satisfaction_score=5,
            would_recommend=True
        )
        
        if not isinstance(outcome_id, int) or outcome_id <= 0:
            print("❌ Step 3: Outcome tracking failed")
            return False
        
        print("✅ Step 3: Outcome tracked")
        
        # Step 4: Log success story
        story_id = tracker.log_success_story(
            user_id='e2e_test_user',
            story_type='early_transition',
            story_title='Early Warning Success Story',
            story_description='Successfully transitioned before layoffs',
            original_risk_factors={'industry_volatility': True, 'company_layoffs': True},
            intervention_timeline={'warning': '2024-01-01', 'job_found': '2024-01-31'},
            outcome_details={'salary_increase': 25000, 'job_security_improved': True},
            user_satisfaction=5,
            would_recommend=True
        )
        
        if not isinstance(story_id, int) or story_id <= 0:
            print("❌ Step 4: Success story logging failed")
            return False
        
        print("✅ Step 4: Success story logged")
        
        # Step 5: Generate comprehensive metrics
        comprehensive_metrics = metrics.get_risk_based_success_metrics('last_30_days')
        
        if not isinstance(comprehensive_metrics, dict):
            print("❌ Step 5: Comprehensive metrics generation failed")
            return False
        
        print("✅ Step 5: Comprehensive metrics generated")
        
        # Step 6: Generate dashboard report
        async def test_dashboard_report():
            report = await dashboard.generate_career_protection_report('last_30_days')
            return report
        
        report = asyncio.run(test_dashboard_report())
        
        if not isinstance(report, dict):
            print("❌ Step 6: Dashboard report generation failed")
            return False
        
        print("✅ Step 6: Dashboard report generated")
        
        # Step 7: Generate predictive insights
        forecasts = analytics.generate_risk_forecasts(
            forecast_type='industry_risk',
            target_entities=['technology'],
            forecast_horizon_days=30
        )
        
        if not isinstance(forecasts, list):
            print("❌ Step 7: Predictive insights generation failed")
            return False
        
        print("✅ Step 7: Predictive insights generated")
        
        print("✅ End-to-end workflow completed successfully")
        
        os.unlink(test_db.name)
        return True
        
    except Exception as e:
        print(f"❌ End-to-end workflow test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def run_functional_tests():
    """Run all functional tests"""
    print("🎯 Risk Dashboard - Functional Test Suite")
    print("=" * 60)
    
    tests = [
        ("RiskAnalyticsTracker Functionality", test_risk_analytics_tracker_functionality),
        ("SuccessMetrics Extension", test_success_metrics_extension),
        ("RiskPredictiveAnalytics", test_risk_predictive_analytics),
        ("RiskSuccessDashboard", test_risk_success_dashboard),
        ("End-to-End Workflow", test_end_to_end_workflow)
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
    
    print("\n" + "=" * 60)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All functional tests passed! Risk dashboard is fully operational.")
        return True
    else:
        print("⚠️  Some tests failed. Please review the output above.")
        return False

if __name__ == '__main__':
    success = run_functional_tests()
    sys.exit(0 if success else 1)
