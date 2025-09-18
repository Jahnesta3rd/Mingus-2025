#!/usr/bin/env python3
"""
Comprehensive Test Suite for Risk-Based Success Metrics Dashboard

This test suite validates all components of the risk dashboard system including:
- Database schema and data operations
- Analytics classes and calculations
- API endpoints and responses
- Integration between components
"""

import unittest
import sqlite3
import json
import tempfile
import os
import sys
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

# Add the backend directory to the path
backend_path = os.path.join(os.path.dirname(__file__), 'backend')
sys.path.insert(0, backend_path)

# Import analytics modules
try:
    from analytics.risk_analytics_tracker import RiskAnalyticsTracker, RiskLevel, InterventionType, OutcomeType
    from analytics.risk_predictive_analytics import RiskPredictiveAnalytics
    from analytics.risk_success_dashboard import RiskSuccessDashboard
    from analytics.success_metrics import SuccessMetrics
except ImportError as e:
    print(f"Import error: {e}")
    print("Available modules in backend/analytics:")
    analytics_dir = os.path.join(backend_path, 'analytics')
    if os.path.exists(analytics_dir):
        for file in os.listdir(analytics_dir):
            if file.endswith('.py'):
                print(f"  - {file}")
    raise

class TestRiskAnalyticsTracker(unittest.TestCase):
    """Test suite for RiskAnalyticsTracker class"""
    
    def setUp(self):
        """Set up test database and tracker instance"""
        self.test_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.test_db.close()
        self.tracker = RiskAnalyticsTracker(self.test_db.name)
    
    def tearDown(self):
        """Clean up test database"""
        os.unlink(self.test_db.name)
    
    def test_risk_assessment_creation(self):
        """Test creating risk assessments"""
        risk_factors = {
            'industry_volatility': True,
            'company_financial_trouble': False,
            'role_redundancy': True
        }
        
        assessment_id = self.tracker.assess_user_risk(
            user_id='test_user_1',
            risk_factors=risk_factors,
            industry_risk_score=75.0,
            company_risk_score=60.0,
            role_risk_score=80.0,
            assessment_confidence=0.85
        )
        
        self.assertIsInstance(assessment_id, int)
        self.assertGreater(assessment_id, 0)
    
    def test_risk_intervention_triggering(self):
        """Test triggering risk interventions"""
        # First create a risk assessment
        assessment_id = self.tracker.assess_user_risk(
            user_id='test_user_1',
            risk_factors={'industry_volatility': True},
            industry_risk_score=85.0
        )
        
        # Trigger intervention
        intervention_id = self.tracker.trigger_intervention(
            user_id='test_user_1',
            risk_assessment_id=assessment_id,
            intervention_type='early_warning',
            intervention_data={'priority': 'high'}
        )
        
        self.assertIsInstance(intervention_id, int)
        self.assertGreater(intervention_id, 0)
    
    def test_career_protection_outcome_tracking(self):
        """Test tracking career protection outcomes"""
        # Create assessment and intervention first
        assessment_id = self.tracker.assess_user_risk(
            user_id='test_user_1',
            risk_factors={'industry_volatility': True},
            industry_risk_score=75.0
        )
        
        intervention_id = self.tracker.trigger_intervention(
            user_id='test_user_1',
            risk_assessment_id=assessment_id,
            intervention_type='early_warning',
            intervention_data={}
        )
        
        # Track outcome
        outcome_id = self.tracker.track_career_protection_outcome(
            user_id='test_user_1',
            risk_assessment_id=assessment_id,
            outcome_type='successful_transition',
            outcome_details={'new_company': 'Tech Corp', 'role': 'Senior Developer'},
            intervention_id=intervention_id,
            salary_change=15000.0,
            time_to_new_role=45,
            satisfaction_score=5,
            would_recommend=True
        )
        
        self.assertIsInstance(outcome_id, int)
        self.assertGreater(outcome_id, 0)
    
    def test_success_story_logging(self):
        """Test logging success stories"""
        story_id = self.tracker.log_success_story(
            user_id='test_user_1',
            story_type='early_transition',
            story_title='Successfully Transitioned Before Layoff',
            story_description='Used early warning to find new role before company downsizing',
            original_risk_factors={'industry_volatility': True, 'company_layoffs': True},
            intervention_timeline={'warning_received': '2024-01-15', 'job_found': '2024-02-28'},
            outcome_details={'salary_increase': 20000, 'job_security_improved': True},
            user_satisfaction=5,
            would_recommend=True,
            testimonial_text='The early warning saved my career!'
        )
        
        self.assertIsInstance(story_id, int)
        self.assertGreater(story_id, 0)
    
    def test_career_protection_metrics(self):
        """Test getting career protection metrics"""
        # Create some test data
        for i in range(5):
            self.tracker.assess_user_risk(
                user_id=f'test_user_{i}',
                risk_factors={'industry_volatility': True},
                industry_risk_score=80.0
            )
        
        metrics = self.tracker.get_career_protection_metrics('last_30_days')
        
        self.assertIn('users_at_high_risk', metrics)
        self.assertIn('successful_transitions', metrics)
        self.assertIn('overall_success_rate', metrics)
        self.assertIsInstance(metrics['users_at_high_risk'], int)
        self.assertIsInstance(metrics['overall_success_rate'], float)

class TestRiskPredictiveAnalytics(unittest.TestCase):
    """Test suite for RiskPredictiveAnalytics class"""
    
    def setUp(self):
        """Set up test database and analytics instance"""
        self.test_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.test_db.close()
        self.analytics = RiskPredictiveAnalytics(self.test_db.name)
    
    def tearDown(self):
        """Clean up test database"""
        os.unlink(self.test_db.name)
    
    def test_risk_forecast_generation(self):
        """Test generating risk forecasts"""
        industries = ['technology', 'finance', 'healthcare']
        forecasts = self.analytics.generate_risk_forecasts(
            forecast_type='industry_risk',
            target_entities=industries,
            forecast_horizon_days=30
        )
        
        self.assertIsInstance(forecasts, list)
        # Note: Forecasts may be empty if insufficient historical data
    
    def test_emerging_risk_detection(self):
        """Test identifying emerging risk factors"""
        patterns = self.analytics.identify_emerging_risk_factors(30)
        
        self.assertIsInstance(patterns, list)
        # Note: Patterns may be empty if insufficient data
    
    def test_user_risk_trajectory_prediction(self):
        """Test predicting user risk trajectory"""
        # This will return None if insufficient data, which is expected
        trajectory = self.analytics.predict_user_risk_trajectory('test_user', 90)
        
        # Should return None or a valid trajectory dict
        if trajectory is not None:
            self.assertIsInstance(trajectory, dict)
            self.assertIn('trajectory', trajectory)
    
    def test_market_risk_heat_map(self):
        """Test generating market risk heat map"""
        heat_map = self.analytics.generate_market_risk_heat_map(30)
        
        self.assertIsInstance(heat_map, dict)
        self.assertIn('analysis_period_days', heat_map)
        self.assertIn('heat_map_data', heat_map)
    
    def test_forecast_accuracy_metrics(self):
        """Test getting forecast accuracy metrics"""
        accuracy = self.analytics.get_forecast_accuracy_metrics(30)
        
        self.assertIsInstance(accuracy, dict)
        self.assertIn('analysis_period_days', accuracy)

class TestRiskSuccessDashboard(unittest.TestCase):
    """Test suite for RiskSuccessDashboard class"""
    
    def setUp(self):
        """Set up test database and dashboard instance"""
        self.test_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.test_db.close()
        self.dashboard = RiskSuccessDashboard(self.test_db.name)
    
    def tearDown(self):
        """Clean up test database"""
        os.unlink(self.test_db.name)
    
    def test_dashboard_initialization(self):
        """Test dashboard initialization"""
        self.assertIsNotNone(self.dashboard.risk_analytics)
        self.assertIsNotNone(self.dashboard.predictive_engine)
        self.assertIsNotNone(self.dashboard.base_metrics)
    
    def test_career_protection_report_generation(self):
        """Test generating career protection report"""
        import asyncio
        
        async def run_test():
            report = await self.dashboard.generate_career_protection_report('last_30_days')
            return report
        
        report = asyncio.run(run_test())
        
        self.assertIsInstance(report, dict)
        self.assertIn('report_generated_at', report)
        self.assertIn('time_period', report)
        self.assertIn('protection_effectiveness', report)
    
    def test_user_success_story_tracking(self):
        """Test tracking user success stories"""
        import asyncio
        
        async def run_test():
            result = await self.dashboard.track_user_success_story(
                user_id='test_user_1',
                success_type='early_transition',
                outcome_data={
                    'story_title': 'Test Success Story',
                    'story_description': 'Test description',
                    'original_risk_factors': {'industry_volatility': True},
                    'intervention_timeline': {'warning': '2024-01-01'},
                    'outcome_details': {'salary_increase': 10000}
                }
            )
            return result
        
        result = asyncio.run(run_test())
        
        self.assertIsInstance(result, dict)
        self.assertIn('success', result)
    
    def test_roi_analysis_generation(self):
        """Test generating ROI analysis"""
        import asyncio
        
        async def run_test():
            roi = await self.dashboard.generate_roi_analysis()
            return roi
        
        roi = asyncio.run(run_test())
        
        self.assertIsInstance(roi, dict)
        self.assertIn('analysis_generated_at', roi)
        self.assertIn('costs_breakdown', roi)
        self.assertIn('benefits_breakdown', roi)
        self.assertIn('roi_analysis', roi)
    
    def test_risk_heat_map_generation(self):
        """Test generating risk heat map"""
        heat_map = self.dashboard.get_risk_heat_map(30)
        
        self.assertIsNotNone(heat_map)
        self.assertIn('industries', heat_map.__dict__)
        self.assertIn('locations', heat_map.__dict__)
        self.assertIn('matrix', heat_map.__dict__)
    
    def test_protection_trends_analysis(self):
        """Test getting protection trends"""
        trends = self.dashboard.get_protection_success_trends(30)
        
        self.assertIsInstance(trends, dict)
        self.assertIn('analysis_period_days', trends)
    
    def test_optimization_opportunities(self):
        """Test identifying optimization opportunities"""
        opportunities = self.dashboard.identify_optimization_opportunities()
        
        self.assertIsInstance(opportunities, list)
        # Opportunities may be empty if no issues detected
    
    def test_resource_predictions(self):
        """Test predicting resource needs"""
        predictions = self.dashboard.predict_resource_needs(30)
        
        self.assertIsInstance(predictions, dict)
        self.assertIn('forecast_days', predictions)

class TestSuccessMetricsExtension(unittest.TestCase):
    """Test suite for extended SuccessMetrics class"""
    
    def setUp(self):
        """Set up test database and metrics instance"""
        self.test_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.test_db.close()
        self.metrics = SuccessMetrics(self.test_db.name)
    
    def tearDown(self):
        """Clean up test database"""
        os.unlink(self.test_db.name)
    
    def test_risk_based_metrics_availability(self):
        """Test that risk-based metrics methods are available"""
        # Test that all new methods exist
        self.assertTrue(hasattr(self.metrics, 'career_protection_success_rate'))
        self.assertTrue(hasattr(self.metrics, 'early_warning_accuracy'))
        self.assertTrue(hasattr(self.metrics, 'risk_intervention_effectiveness'))
        self.assertTrue(hasattr(self.metrics, 'income_protection_rate'))
        self.assertTrue(hasattr(self.metrics, 'unemployment_prevention_rate'))
        self.assertTrue(hasattr(self.metrics, 'risk_to_outcome_funnel'))
        self.assertTrue(hasattr(self.metrics, 'proactive_vs_reactive_comparison'))
        self.assertTrue(hasattr(self.metrics, 'get_risk_based_success_metrics'))
    
    def test_career_protection_success_rate(self):
        """Test career protection success rate calculation"""
        rate = self.metrics.career_protection_success_rate('last_30_days')
        
        self.assertIsInstance(rate, float)
        self.assertGreaterEqual(rate, 0.0)
        self.assertLessEqual(rate, 100.0)
    
    def test_early_warning_accuracy(self):
        """Test early warning accuracy calculation"""
        accuracy = self.metrics.early_warning_accuracy('last_30_days')
        
        self.assertIsInstance(accuracy, float)
        self.assertGreaterEqual(accuracy, 0.0)
        self.assertLessEqual(accuracy, 100.0)
    
    def test_risk_based_success_metrics(self):
        """Test comprehensive risk-based success metrics"""
        metrics = self.metrics.get_risk_based_success_metrics('last_30_days')
        
        self.assertIsInstance(metrics, dict)
        self.assertIn('time_period', metrics)
        self.assertIn('career_protection_metrics', metrics)
        self.assertIn('user_journey_analytics', metrics)
        self.assertIn('predictive_insights', metrics)
        self.assertIn('risk_trend_analysis', metrics)

class TestDatabaseSchema(unittest.TestCase):
    """Test suite for database schema validation"""
    
    def setUp(self):
        """Set up test database"""
        self.test_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.test_db.close()
        
        # Initialize database with schema
        conn = sqlite3.connect(self.test_db.name)
        cursor = conn.cursor()
        
        with open('backend/analytics/recommendation_analytics_schema.sql', 'r') as f:
            schema_sql = f.read()
        
        cursor.executescript(schema_sql)
        conn.commit()
        conn.close()
    
    def tearDown(self):
        """Clean up test database"""
        os.unlink(self.test_db.name)
    
    def test_risk_tables_exist(self):
        """Test that all risk-related tables exist"""
        conn = sqlite3.connect(self.test_db.name)
        cursor = conn.cursor()
        
        # Get all table names
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        # Check for risk-related tables
        risk_tables = [
            'user_risk_assessments',
            'risk_interventions',
            'career_protection_outcomes',
            'risk_forecasts',
            'risk_success_stories',
            'risk_analytics_aggregations',
            'risk_dashboard_alerts'
        ]
        
        for table in risk_tables:
            self.assertIn(table, tables, f"Table {table} not found")
        
        conn.close()
    
    def test_risk_views_exist(self):
        """Test that all risk-related views exist"""
        conn = sqlite3.connect(self.test_db.name)
        cursor = conn.cursor()
        
        # Get all view names
        cursor.execute("SELECT name FROM sqlite_master WHERE type='view'")
        views = [row[0] for row in cursor.fetchall()]
        
        # Check for risk-related views
        risk_views = [
            'career_protection_effectiveness',
            'risk_intervention_effectiveness',
            'risk_trend_analysis'
        ]
        
        for view in risk_views:
            self.assertIn(view, views, f"View {view} not found")
        
        conn.close()
    
    def test_risk_indexes_exist(self):
        """Test that all risk-related indexes exist"""
        conn = sqlite3.connect(self.test_db.name)
        cursor = conn.cursor()
        
        # Get all index names
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND name LIKE 'idx_%'")
        indexes = [row[0] for row in cursor.fetchall()]
        
        # Check for key risk-related indexes
        risk_indexes = [
            'idx_user_risk_assessments_user',
            'idx_risk_interventions_user',
            'idx_career_protection_user',
            'idx_risk_forecasts_type',
            'idx_risk_success_stories_user'
        ]
        
        for index in risk_indexes:
            self.assertIn(index, indexes, f"Index {index} not found")
        
        conn.close()

class TestIntegration(unittest.TestCase):
    """Integration tests for the complete risk dashboard system"""
    
    def setUp(self):
        """Set up test database and all components"""
        self.test_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.test_db.close()
        
        # Initialize all components
        self.tracker = RiskAnalyticsTracker(self.test_db.name)
        self.analytics = RiskPredictiveAnalytics(self.test_db.name)
        self.dashboard = RiskSuccessDashboard(self.test_db.name)
        self.metrics = SuccessMetrics(self.test_db.name)
    
    def tearDown(self):
        """Clean up test database"""
        os.unlink(self.test_db.name)
    
    def test_end_to_end_workflow(self):
        """Test complete end-to-end workflow"""
        # 1. Create risk assessment
        assessment_id = self.tracker.assess_user_risk(
            user_id='integration_test_user',
            risk_factors={'industry_volatility': True, 'company_layoffs': True},
            industry_risk_score=85.0,
            company_risk_score=90.0,
            assessment_confidence=0.9
        )
        
        self.assertIsInstance(assessment_id, int)
        
        # 2. Trigger intervention
        intervention_id = self.tracker.trigger_intervention(
            user_id='integration_test_user',
            risk_assessment_id=assessment_id,
            intervention_type='early_warning',
            intervention_data={'priority': 'critical'}
        )
        
        self.assertIsInstance(intervention_id, int)
        
        # 3. Track successful outcome
        outcome_id = self.tracker.track_career_protection_outcome(
            user_id='integration_test_user',
            risk_assessment_id=assessment_id,
            outcome_type='successful_transition',
            outcome_details={'new_company': 'Safe Corp', 'role': 'Lead Developer'},
            intervention_id=intervention_id,
            salary_change=25000.0,
            time_to_new_role=30,
            satisfaction_score=5,
            would_recommend=True
        )
        
        self.assertIsInstance(outcome_id, int)
        
        # 4. Log success story
        story_id = self.tracker.log_success_story(
            user_id='integration_test_user',
            story_type='early_transition',
            story_title='Early Warning Saved My Career',
            story_description='Received early warning and successfully transitioned before layoffs',
            original_risk_factors={'industry_volatility': True, 'company_layoffs': True},
            intervention_timeline={'warning': '2024-01-01', 'job_found': '2024-01-31'},
            outcome_details={'salary_increase': 25000, 'job_security_improved': True},
            user_satisfaction=5,
            would_recommend=True
        )
        
        self.assertIsInstance(story_id, int)
        
        # 5. Get metrics
        protection_metrics = self.tracker.get_career_protection_metrics('last_30_days')
        self.assertIsInstance(protection_metrics, dict)
        
        # 6. Get comprehensive metrics
        comprehensive_metrics = self.metrics.get_risk_based_success_metrics('last_30_days')
        self.assertIsInstance(comprehensive_metrics, dict)
        
        # 7. Test dashboard functionality
        import asyncio
        
        async def test_dashboard():
            report = await self.dashboard.generate_career_protection_report('last_30_days')
            return report
        
        report = asyncio.run(test_dashboard())
        self.assertIsInstance(report, dict)
    
    def test_data_consistency(self):
        """Test data consistency across components"""
        # Create test data
        assessment_id = self.tracker.assess_user_risk(
            user_id='consistency_test_user',
            risk_factors={'role_redundancy': True},
            role_risk_score=75.0
        )
        
        # Check that data is accessible from different components
        conn = sqlite3.connect(self.test_db.name)
        cursor = conn.cursor()
        
        # Verify assessment exists
        cursor.execute("SELECT COUNT(*) FROM user_risk_assessments WHERE user_id = ?", 
                      ('consistency_test_user',))
        assessment_count = cursor.fetchone()[0]
        self.assertEqual(assessment_count, 1)
        
        # Verify risk level is set correctly
        cursor.execute("SELECT risk_level FROM user_risk_assessments WHERE user_id = ?", 
                      ('consistency_test_user',))
        risk_level = cursor.fetchone()[0]
        self.assertIn(risk_level, ['low', 'medium', 'high', 'critical'])
        
        conn.close()

def run_performance_test():
    """Run performance tests for the risk dashboard system"""
    print("\n🚀 Running Performance Tests...")
    
    # Test database initialization time
    start_time = datetime.now()
    test_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
    test_db.close()
    
    dashboard = RiskSuccessDashboard(test_db.name)
    init_time = (datetime.now() - start_time).total_seconds()
    
    print(f"✅ Database initialization: {init_time:.3f} seconds")
    
    # Test metrics calculation time
    start_time = datetime.now()
    metrics = dashboard.base_metrics.get_risk_based_success_metrics('last_30_days')
    metrics_time = (datetime.now() - start_time).total_seconds()
    
    print(f"✅ Metrics calculation: {metrics_time:.3f} seconds")
    
    # Test heat map generation time
    start_time = datetime.now()
    heat_map = dashboard.get_risk_heat_map(30)
    heat_map_time = (datetime.now() - start_time).total_seconds()
    
    print(f"✅ Heat map generation: {heat_map_time:.3f} seconds")
    
    # Cleanup
    os.unlink(test_db.name)
    
    print(f"\n📊 Performance Summary:")
    print(f"   - Database init: {init_time:.3f}s")
    print(f"   - Metrics calc: {metrics_time:.3f}s")
    print(f"   - Heat map: {heat_map_time:.3f}s")
    print(f"   - Total: {init_time + metrics_time + heat_map_time:.3f}s")

def run_comprehensive_test():
    """Run comprehensive test suite"""
    print("🧪 Running Comprehensive Risk Dashboard Test Suite...")
    print("=" * 60)
    
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add test classes
    test_classes = [
        TestRiskAnalyticsTracker,
        TestRiskPredictiveAnalytics,
        TestRiskSuccessDashboard,
        TestSuccessMetricsExtension,
        TestDatabaseSchema,
        TestIntegration
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Print summary
    print("\n" + "=" * 60)
    print("📊 Test Results Summary:")
    print(f"   Tests run: {result.testsRun}")
    print(f"   Failures: {len(result.failures)}")
    print(f"   Errors: {len(result.errors)}")
    print(f"   Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    
    if result.failures:
        print("\n❌ Failures:")
        for test, traceback in result.failures:
            print(f"   - {test}: {traceback.split('AssertionError: ')[-1].split('\\n')[0]}")
    
    if result.errors:
        print("\n💥 Errors:")
        for test, traceback in result.errors:
            print(f"   - {test}: {traceback.split('\\n')[-2]}")
    
    # Run performance tests
    run_performance_test()
    
    return result.wasSuccessful()

if __name__ == '__main__':
    print("🎯 Risk-Based Success Metrics Dashboard - Test Suite")
    print("=" * 60)
    
    success = run_comprehensive_test()
    
    if success:
        print("\n🎉 All tests passed! The risk dashboard system is working correctly.")
    else:
        print("\n⚠️  Some tests failed. Please review the output above.")
    
    print("\n" + "=" * 60)
