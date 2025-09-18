#!/usr/bin/env python3
"""
Comprehensive Test Suite for Unified Risk Analytics API

This module provides comprehensive testing for all risk analytics API endpoints,
including unit tests, integration tests, and performance tests.

Features:
- Unit tests for all API endpoints
- Integration tests for risk-triggered workflows
- Performance testing for analytics endpoints
- Authentication and authorization testing
- Error handling and edge case testing
"""

import pytest
import json
import asyncio
import time
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
import sqlite3
import tempfile
import os

# Import the risk analytics API
from backend.api.unified_risk_analytics_api import risk_analytics_api, RiskAnalyticsAPI
from backend.analytics.risk_performance_monitor import RiskPerformanceMonitor
from backend.analytics.risk_success_dashboard import RiskSuccessDashboard

class TestRiskAnalyticsAPI:
    """Test suite for Risk Analytics API"""
    
    @pytest.fixture
    def app(self):
        """Create test Flask app"""
        from flask import Flask
        app = Flask(__name__)
        app.config['TESTING'] = True
        app.config['SECRET_KEY'] = 'test-secret-key'
        app.register_blueprint(risk_analytics_api)
        return app
    
    @pytest.fixture
    def client(self, app):
        """Create test client"""
        return app.test_client()
    
    @pytest.fixture
    def mock_user(self):
        """Create mock user for testing"""
        user = Mock()
        user.id = 'test_user_123'
        user.is_authenticated = True
        user.is_admin = False
        user.risk_analytics_access = True
        user.get_profile_dict.return_value = {
            'skills': ['Python', 'JavaScript'],
            'experience_years': 5,
            'current_role': 'Software Engineer',
            'industry': 'Technology'
        }
        return user
    
    @pytest.fixture
    def temp_db(self):
        """Create temporary database for testing"""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as tmp:
            db_path = tmp.name
        
        # Initialize test database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create test tables
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS risk_assessment_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                overall_risk_score REAL NOT NULL,
                ai_replacement_risk REAL,
                layoff_risk REAL,
                industry_risk REAL,
                primary_risk_factor TEXT,
                risk_triggers TEXT,
                assessment_type TEXT DEFAULT 'user_requested',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
        
        yield db_path
        
        # Cleanup
        os.unlink(db_path)
    
    def test_health_check(self, client):
        """Test health check endpoint"""
        response = client.get('/api/risk/health')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['status'] == 'healthy'
        assert 'service' in data
        assert 'timestamp' in data
        assert 'version' in data
    
    @patch('backend.api.unified_risk_analytics_api.current_user')
    def test_assess_risk_with_tracking_success(self, mock_current_user, client, mock_user, temp_db):
        """Test successful risk assessment with tracking"""
        mock_current_user.is_authenticated = True
        mock_current_user.id = 'test_user_123'
        mock_current_user.get_profile_dict.return_value = {
            'skills': ['Python', 'JavaScript'],
            'experience_years': 5
        }
        
        # Mock the risk analyzer
        with patch('backend.api.unified_risk_analytics_api.risk_api.risk_analyzer') as mock_analyzer:
            mock_analyzer.calculate_comprehensive_risk_score.return_value = {
                'overall_risk': 0.7,
                'risk_breakdown': {
                    'ai_displacement_probability': 0.6,
                    'layoff_probability': 0.4,
                    'industry_risk_level': 0.5
                },
                'risk_triggers': [{'factor': 'AI automation', 'score': 0.8}]
            }
            
            mock_analyzer.track_risk_assessment_completed.return_value = True
            
            response = client.post('/api/risk/assess-and-track', 
                                 json={'test': 'data'})
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['success'] is True
            assert 'risk_analysis' in data
            assert 'analytics_tracked' in data
    
    @patch('backend.api.unified_risk_analytics_api.current_user')
    def test_assess_risk_unauthorized(self, mock_current_user, client):
        """Test risk assessment with unauthorized user"""
        mock_current_user.is_authenticated = False
        
        response = client.post('/api/risk/assess-and-track', 
                             json={'test': 'data'})
        
        assert response.status_code == 401
        data = json.loads(response.data)
        assert 'error' in data
    
    @patch('backend.api.unified_risk_analytics_api.current_user')
    def test_get_risk_dashboard_success(self, mock_current_user, client, mock_user):
        """Test successful risk dashboard retrieval"""
        mock_current_user.is_authenticated = True
        mock_current_user.id = 'test_user_123'
        mock_current_user.is_admin = False
        
        # Mock the success dashboard
        with patch('backend.api.unified_risk_analytics_api.risk_api.success_dashboard') as mock_dashboard:
            mock_dashboard.generate_career_protection_report.return_value = {
                'success_rate': 0.85,
                'total_interventions': 150
            }
            
            # Mock performance monitor
            with patch('backend.api.unified_risk_analytics_api.risk_api.performance_monitor') as mock_perf:
                mock_perf.get_user_risk_performance.return_value = {
                    'avg_response_time': 250.0
                }
                
                # Mock A/B testing
                with patch('backend.api.unified_risk_analytics_api.risk_api.ab_testing') as mock_ab:
                    mock_ab.get_user_active_experiments.return_value = []
                    
                    response = client.get('/api/risk/dashboard/test_user_123')
                    
                    assert response.status_code == 200
                    data = json.loads(response.data)
                    assert 'career_protection_metrics' in data
                    assert 'risk_trends' in data
                    assert 'performance_data' in data
    
    @patch('backend.api.unified_risk_analytics_api.current_user')
    def test_get_risk_dashboard_unauthorized(self, mock_current_user, client):
        """Test risk dashboard with unauthorized access"""
        mock_current_user.is_authenticated = True
        mock_current_user.id = 'test_user_123'
        mock_current_user.is_admin = False
        
        response = client.get('/api/risk/dashboard/other_user_456')
        
        assert response.status_code == 403
        data = json.loads(response.data)
        assert 'error' in data
    
    @patch('backend.api.unified_risk_analytics_api.current_user')
    def test_trigger_risk_recommendations_success(self, mock_current_user, client, mock_user):
        """Test successful risk-based recommendation triggering"""
        mock_current_user.is_authenticated = True
        mock_current_user.id = 'test_user_123'
        
        # Mock the three-tier selector
        with patch('backend.api.unified_risk_analytics_api.risk_api.three_tier_selector') as mock_selector:
            mock_selector.generate_tiered_recommendations.return_value = {
                'conservative': [{'job_id': 'job1', 'title': 'Software Engineer'}],
                'optimal': [{'job_id': 'job2', 'title': 'Senior Software Engineer'}],
                'stretch': [{'job_id': 'job3', 'title': 'Tech Lead'}]
            }
            
            # Mock risk analyzer
            with patch('backend.api.unified_risk_analytics_api.risk_api.risk_analyzer') as mock_analyzer:
                mock_analyzer.track_risk_recommendation_triggered.return_value = True
                
                response = client.post('/api/risk/trigger-recommendations', 
                                     json={
                                         'risk_data': {'overall_risk': 0.7},
                                         'recommendation_tiers': ['conservative', 'optimal']
                                     })
                
                assert response.status_code == 200
                data = json.loads(response.data)
                assert data['success'] is True
                assert 'recommendations' in data
    
    @patch('backend.api.unified_risk_analytics_api.current_user')
    def test_trigger_risk_recommendations_missing_fields(self, mock_current_user, client, mock_user):
        """Test risk recommendation triggering with missing required fields"""
        mock_current_user.is_authenticated = True
        mock_current_user.id = 'test_user_123'
        
        response = client.post('/api/risk/trigger-recommendations', 
                             json={'risk_data': {'overall_risk': 0.7}})
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
    
    @patch('backend.api.unified_risk_analytics_api.current_user')
    def test_get_effectiveness_metrics_success(self, mock_current_user, client, mock_user):
        """Test successful effectiveness metrics retrieval"""
        mock_current_user.is_authenticated = True
        mock_current_user.id = 'test_user_123'
        
        # Mock success dashboard
        with patch('backend.api.unified_risk_analytics_api.risk_api.success_dashboard') as mock_dashboard:
            mock_dashboard.generate_career_protection_report.return_value = {
                'success_rate': 0.85
            }
            
            # Mock risk analyzer
            with patch('backend.api.unified_risk_analytics_api.risk_api.risk_analyzer') as mock_analyzer:
                mock_analyzer.get_prediction_accuracy_report.return_value = {
                    'overall_accuracy': 0.78
                }
                
                # Mock risk tracker
                with patch('backend.api.unified_risk_analytics_api.risk_api.risk_tracker') as mock_tracker:
                    mock_tracker.get_user_engagement_metrics.return_value = {
                        'engagement_score': 0.9
                    }
                    
                    response = client.get('/api/risk/analytics/effectiveness')
                    
                    assert response.status_code == 200
                    data = json.loads(response.data)
                    assert data['success'] is True
                    assert 'effectiveness_metrics' in data
                    assert 'prediction_accuracy' in data
    
    @patch('backend.api.unified_risk_analytics_api.current_user')
    def test_track_risk_outcome_success(self, mock_current_user, client, mock_user):
        """Test successful risk outcome tracking"""
        mock_current_user.is_authenticated = True
        mock_current_user.id = 'test_user_123'
        
        # Mock success dashboard
        with patch('backend.api.unified_risk_analytics_api.risk_api.success_dashboard') as mock_dashboard:
            mock_dashboard.track_user_success_story.return_value = {'id': 'story_123'}
            
            # Mock risk analyzer
            with patch('backend.api.unified_risk_analytics_api.risk_api.risk_analyzer') as mock_analyzer:
                mock_analyzer.measure_risk_prediction_accuracy.return_value = True
                
                # Mock A/B testing
                with patch('backend.api.unified_risk_analytics_api.risk_api.ab_testing') as mock_ab:
                    mock_ab.track_experiment_outcome.return_value = True
                    
                    response = client.post('/api/risk/outcome/track', 
                                         json={
                                             'outcome_type': 'job_saved',
                                             'original_risk_score': 0.7,
                                             'intervention_date': '2024-01-01',
                                             'actual_outcome': 'success',
                                             'experiment_variant': 'control'
                                         })
                    
                    assert response.status_code == 200
                    data = json.loads(response.data)
                    assert data['success'] is True
                    assert data['outcome_tracked'] is True
    
    @patch('backend.api.unified_risk_analytics_api.current_user')
    def test_track_risk_outcome_missing_fields(self, mock_current_user, client, mock_user):
        """Test risk outcome tracking with missing required fields"""
        mock_current_user.is_authenticated = True
        mock_current_user.id = 'test_user_123'
        
        response = client.post('/api/risk/outcome/track', 
                             json={'outcome_type': 'job_saved'})
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
    
    @patch('backend.api.unified_risk_analytics_api.current_user')
    def test_get_risk_system_health_success(self, mock_current_user, client, mock_user):
        """Test successful risk system health retrieval"""
        mock_current_user.is_authenticated = True
        mock_current_user.id = 'test_user_123'
        
        # Mock performance monitor
        with patch('backend.api.unified_risk_analytics_api.risk_api.performance_monitor') as mock_perf:
            mock_perf.get_risk_system_health.return_value = {
                'health_score': 85.0,
                'system_status': 'healthy'
            }
            
            response = client.get('/api/risk/monitor/status')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['success'] is True
            assert 'system_health' in data
            assert 'active_alerts' in data
    
    @patch('backend.api.unified_risk_analytics_api.current_user')
    def test_trigger_risk_alert_success(self, mock_current_user, client, mock_user):
        """Test successful risk alert triggering"""
        mock_current_user.is_authenticated = True
        mock_current_user.id = 'test_user_123'
        
        # Mock risk analyzer
        with patch('backend.api.unified_risk_analytics_api.risk_api.risk_analyzer') as mock_analyzer:
            mock_analyzer.track_risk_alert_sent.return_value = True
            
            response = client.post('/api/risk/alert/trigger', 
                                 json={
                                     'alert_type': 'high_risk',
                                     'risk_level': 'critical',
                                     'message': 'High risk detected'
                                 })
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['success'] is True
            assert data['alert_triggered'] is True
    
    @patch('backend.api.unified_risk_analytics_api.current_user')
    def test_trigger_risk_alert_missing_fields(self, mock_current_user, client, mock_user):
        """Test risk alert triggering with missing required fields"""
        mock_current_user.is_authenticated = True
        mock_current_user.id = 'test_user_123'
        
        response = client.post('/api/risk/alert/trigger', 
                             json={'alert_type': 'high_risk'})
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
    
    @patch('backend.api.unified_risk_analytics_api.current_user')
    def test_get_live_risk_trends_success(self, mock_current_user, client, mock_user):
        """Test successful live risk trends retrieval"""
        mock_current_user.is_authenticated = True
        mock_current_user.id = 'test_user_123'
        
        # Mock predictive analytics
        with patch('backend.api.unified_risk_analytics_api.risk_api.predictive_analytics') as mock_pred:
            mock_pred.get_live_risk_trends.return_value = {
                'ai_risk_trend': 'increasing',
                'layoff_risk_trend': 'stable'
            }
            
            # Mock risk tracker
            with patch('backend.api.unified_risk_analytics_api.risk_api.risk_tracker') as mock_tracker:
                mock_tracker.get_user_risk_trends.return_value = {
                    'user_trend': 'improving'
                }
                
                response = client.get('/api/risk/trends/live')
                
                assert response.status_code == 200
                data = json.loads(response.data)
                assert data['success'] is True
                assert 'live_trends' in data
                assert 'user_trends' in data
    
    @patch('backend.api.unified_risk_analytics_api.current_user')
    def test_get_active_risk_predictions_success(self, mock_current_user, client, mock_user):
        """Test successful active risk predictions retrieval"""
        mock_current_user.is_authenticated = True
        mock_current_user.id = 'test_user_123'
        
        # Mock predictive analytics
        with patch('backend.api.unified_risk_analytics_api.risk_api.predictive_analytics') as mock_pred:
            mock_pred.get_active_predictions.return_value = [
                {'prediction_id': 'pred_1', 'risk_level': 'high'},
                {'prediction_id': 'pred_2', 'risk_level': 'medium'}
            ]
            
            response = client.get('/api/risk/predictions/active')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['success'] is True
            assert 'active_predictions' in data
            assert data['prediction_count'] == 2
    
    @patch('backend.api.unified_risk_analytics_api.current_user')
    def test_get_active_risk_experiments_success(self, mock_current_user, client, mock_user):
        """Test successful active risk experiments retrieval"""
        mock_current_user.is_authenticated = True
        mock_current_user.id = 'test_user_123'
        
        # Mock A/B testing
        with patch('backend.api.unified_risk_analytics_api.risk_api.ab_testing') as mock_ab:
            mock_ab.get_user_active_experiments.return_value = [
                {'test_id': 'test_1', 'test_name': 'Risk Threshold Test'},
                {'test_id': 'test_2', 'test_name': 'Communication Test'}
            ]
            
            response = client.get('/api/risk/experiments/active')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['success'] is True
            assert 'active_experiments' in data
            assert data['experiment_count'] == 2
    
    @patch('backend.api.unified_risk_analytics_api.current_user')
    def test_assign_user_to_risk_experiment_success(self, mock_current_user, client, mock_user):
        """Test successful user assignment to risk experiment"""
        mock_current_user.is_authenticated = True
        mock_current_user.id = 'test_user_123'
        
        # Mock A/B testing
        with patch('backend.api.unified_risk_analytics_api.risk_api.ab_testing') as mock_ab:
            mock_ab.assign_user_to_experiment.return_value = True
            
            response = client.post('/api/risk/experiments/assign', 
                                 json={
                                     'test_id': 'test_123',
                                     'variant': 'treatment'
                                 })
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['success'] is True
            assert data['assignment_created'] is True
    
    @patch('backend.api.unified_risk_analytics_api.current_user')
    def test_track_risk_experiment_outcome_success(self, mock_current_user, client, mock_user):
        """Test successful risk experiment outcome tracking"""
        mock_current_user.is_authenticated = True
        mock_current_user.id = 'test_user_123'
        
        # Mock A/B testing
        with patch('backend.api.unified_risk_analytics_api.risk_api.ab_testing') as mock_ab:
            mock_ab.track_experiment_outcome.return_value = True
            
            response = client.post('/api/risk/experiments/outcome', 
                                 json={
                                     'test_id': 'test_123',
                                     'outcome_type': 'success',
                                     'outcome_data': {'metric': 'conversion_rate'}
                                 })
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['success'] is True
            assert data['outcome_tracked'] is True
    
    @patch('backend.api.unified_risk_analytics_api.current_user')
    def test_get_comprehensive_risk_analytics_admin_success(self, mock_current_user, client, mock_user):
        """Test successful comprehensive risk analytics retrieval for admin"""
        mock_current_user.is_authenticated = True
        mock_current_user.id = 'test_user_123'
        mock_current_user.is_admin = True
        
        # Mock all components
        with patch('backend.api.unified_risk_analytics_api.risk_api.success_dashboard') as mock_dashboard, \
             patch('backend.api.unified_risk_analytics_api.risk_api.performance_monitor') as mock_perf, \
             patch('backend.api.unified_risk_analytics_api.risk_api.ab_testing') as mock_ab, \
             patch('backend.api.unified_risk_analytics_api.risk_api.risk_analyzer') as mock_analyzer:
            
            mock_dashboard.generate_career_protection_report.return_value = {'success_rate': 0.85}
            mock_perf.get_comprehensive_performance_report.return_value = {'health_score': 90.0}
            mock_ab.get_all_active_test_results.return_value = []
            mock_analyzer.get_prediction_accuracy_report.return_value = {'accuracy': 0.78}
            mock_dashboard.generate_roi_analysis.return_value = {'roi': 0.25}
            mock_dashboard.get_recent_success_stories.return_value = []
            mock_perf.get_risk_system_health.return_value = {'status': 'healthy'}
            
            response = client.get('/api/risk/analytics/admin/comprehensive')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['success'] is True
            assert 'comprehensive_analytics' in data
    
    @patch('backend.api.unified_risk_analytics_api.current_user')
    def test_get_comprehensive_risk_analytics_non_admin(self, mock_current_user, client, mock_user):
        """Test comprehensive risk analytics access for non-admin user"""
        mock_current_user.is_authenticated = True
        mock_current_user.id = 'test_user_123'
        mock_current_user.is_admin = False
        
        response = client.get('/api/risk/analytics/admin/comprehensive')
        
        assert response.status_code == 403
        data = json.loads(response.data)
        assert 'error' in data

class TestRiskAnalyticsAPIClass:
    """Test suite for RiskAnalyticsAPI class"""
    
    def test_risk_analytics_api_initialization(self, temp_db):
        """Test RiskAnalyticsAPI initialization"""
        api = RiskAnalyticsAPI(db_path=temp_db)
        
        assert api.db_path == temp_db
        assert api.risk_analyzer is not None
        assert api.risk_tracker is not None
        assert api.ab_testing is not None
        assert api.predictive_analytics is not None
        assert api.success_dashboard is not None
        assert api.performance_monitor is not None
        assert api.recommendation_engine is not None
        assert api.three_tier_selector is not None
    
    def test_database_initialization(self, temp_db):
        """Test database initialization"""
        api = RiskAnalyticsAPI(db_path=temp_db)
        
        # Check if tables were created
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        assert 'risk_assessment_history' in tables
        assert 'risk_triggered_recommendations' in tables
        assert 'risk_monitoring_alerts' in tables
        assert 'risk_ab_test_assignments' in tables
        
        conn.close()

class TestPerformanceMonitoring:
    """Test suite for performance monitoring"""
    
    def test_performance_monitor_initialization(self, temp_db):
        """Test RiskPerformanceMonitor initialization"""
        monitor = RiskPerformanceMonitor(db_path=temp_db)
        
        assert monitor.db_path == temp_db
        assert monitor.cache_ttl == 300
        assert monitor.max_cache_size == 1000
        assert len(monitor.thresholds) > 0
    
    def test_performance_monitoring_decorator(self, temp_db):
        """Test performance monitoring decorator"""
        monitor = RiskPerformanceMonitor(db_path=temp_db)
        
        @monitor.monitor_performance('test_endpoint', 1000)
        async def test_function():
            time.sleep(0.1)  # Simulate work
            return {'result': 'success'}
        
        # Test the decorated function
        result = asyncio.run(test_function())
        assert result['result'] == 'success'
        
        # Check if metric was recorded
        assert len(monitor.metrics) == 1
        metric = monitor.metrics[0]
        assert metric.endpoint == 'test_endpoint'
        assert metric.response_time > 0
        assert metric.success is True
    
    def test_performance_summary(self, temp_db):
        """Test performance summary generation"""
        monitor = RiskPerformanceMonitor(db_path=temp_db)
        
        # Add some test metrics
        monitor.metrics = [
            monitor.PerformanceMetric(
                endpoint='test_endpoint',
                response_time=250.0,
                timestamp=datetime.utcnow(),
                success=True
            ),
            monitor.PerformanceMetric(
                endpoint='test_endpoint',
                response_time=350.0,
                timestamp=datetime.utcnow(),
                success=True
            )
        ]
        
        # Store metrics
        monitor._store_metrics_batch()
        
        # Get performance summary
        summary = monitor.get_performance_summary(hours=1)
        
        assert 'test_endpoint' in summary
        assert summary['test_endpoint']['avg_response_time'] == 300.0
        assert summary['test_endpoint']['request_count'] == 2
        assert summary['test_endpoint']['success_rate'] == 100.0

class TestSuccessDashboard:
    """Test suite for success dashboard"""
    
    def test_success_dashboard_initialization(self, temp_db):
        """Test RiskSuccessDashboard initialization"""
        dashboard = RiskSuccessDashboard(db_path=temp_db)
        
        assert dashboard.db_path == temp_db
    
    def test_track_success_story(self, temp_db):
        """Test success story tracking"""
        dashboard = RiskSuccessDashboard(db_path=temp_db)
        
        outcome_data = {
            'original_risk_score': 0.7,
            'intervention_date': '2024-01-01',
            'income_increase_percentage': 15.0
        }
        
        result = asyncio.run(dashboard.track_user_success_story(
            user_id='test_user',
            success_type='job_saved',
            outcome_data=outcome_data
        ))
        
        assert 'id' in result
        assert result['user_id'] == 'test_user'
        assert result['success_type'] == 'job_saved'
        assert result['impact_score'] > 0
    
    def test_generate_roi_analysis(self, temp_db):
        """Test ROI analysis generation"""
        dashboard = RiskSuccessDashboard(db_path=temp_db)
        
        # Add some test success stories
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO success_stories 
            (user_id, success_type, outcome_data, original_risk_score, 
             intervention_date, success_date, impact_score, story_text)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            'user1', 'job_saved', '{"income_increase": 10}', 0.7,
            '2024-01-01', '2024-01-15', 0.8, 'Test story'
        ))
        
        conn.commit()
        conn.close()
        
        # Generate ROI analysis
        roi_analysis = asyncio.run(dashboard.generate_roi_analysis())
        
        assert 'total_interventions' in roi_analysis
        assert 'successful_interventions' in roi_analysis
        assert 'roi_percentage' in roi_analysis
        assert roi_analysis['total_interventions'] == 1
        assert roi_analysis['successful_interventions'] == 1

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
