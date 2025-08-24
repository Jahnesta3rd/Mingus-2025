"""
Test Reporting System Integration
Tests for Flask app structure integration and session management
"""

import pytest
import json
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from sqlalchemy.exc import SQLAlchemyError

from backend.services.reporting_service import ReportingService
from backend.services.flask_reporting_service import FlaskReportingService
from backend.routes.reporting_api import reporting_api_bp, handle_reporting_error
from backend.database import get_flask_db_session, close_flask_db_session


class TestReportingServiceIntegration:
    """Test reporting service integration with Flask session management"""
    
    def setup_method(self):
        """Setup test environment"""
        self.mock_session = Mock()
        self.reporting_service = ReportingService(db_session=self.mock_session)
    
    def test_flask_session_integration(self):
        """Test that reporting service uses Flask session management"""
        with patch('backend.services.reporting_service.get_flask_db_session') as mock_get_session:
            mock_get_session.return_value = self.mock_session
            
            service = ReportingService()  # No db_session provided
            assert service._use_flask_session is True
            
            # Test that _get_session returns Flask session
            session = service._get_session()
            assert session == self.mock_session
            mock_get_session.assert_called_once()
    
    def test_custom_session_integration(self):
        """Test that reporting service can use custom session"""
        custom_session = Mock()
        service = ReportingService(db_session=custom_session)
        
        assert service._use_flask_session is False
        assert service._get_session() == custom_session
    
    def test_database_error_handling(self):
        """Test database error handling with Flask session"""
        with patch('backend.services.reporting_service.get_flask_db_session') as mock_get_session:
            mock_get_session.return_value = self.mock_session
            self.mock_session.query.side_effect = SQLAlchemyError("Database error")
            
            service = ReportingService()
            
            with pytest.raises(SQLAlchemyError):
                service.get_dashboard_summary()
    
    def test_session_cleanup(self):
        """Test session cleanup on service destruction"""
        custom_session = Mock()
        service = ReportingService(db_session=custom_session)
        
        # Simulate service destruction
        service.__del__()
        
        # Should close the custom session
        custom_session.close.assert_called_once()
    
    def test_flask_session_no_cleanup(self):
        """Test that Flask sessions are not closed by service"""
        with patch('backend.services.reporting_service.get_flask_db_session') as mock_get_session:
            mock_get_session.return_value = self.mock_session
            
            service = ReportingService()
            
            # Simulate service destruction
            service.__del__()
            
            # Should not close Flask session
            self.mock_session.close.assert_not_called()


class TestFlaskReportingService:
    """Test Flask-specific reporting service wrapper"""
    
    def setup_method(self):
        """Setup test environment"""
        self.flask_service = FlaskReportingService()
    
    def test_service_initialization(self):
        """Test Flask reporting service initialization"""
        assert self.flask_service._reporting_service is None
    
    def test_lazy_service_creation(self):
        """Test that reporting service is created lazily"""
        with patch('backend.services.flask_reporting_service.ReportingService') as mock_service_class:
            mock_service = Mock()
            mock_service_class.return_value = mock_service
            
            # Service should be created on first use
            service = self.flask_service._get_service()
            
            assert service == mock_service
            mock_service_class.assert_called_once()
    
    def test_dashboard_summary_success(self):
        """Test successful dashboard summary retrieval"""
        mock_data = {'summary': {'total_messages': 100}}
        
        with patch('backend.services.flask_reporting_service.ReportingService') as mock_service_class:
            mock_service = Mock()
            mock_service.get_dashboard_summary.return_value = mock_data
            mock_service_class.return_value = mock_service
            
            result = self.flask_service.get_dashboard_summary()
            
            assert result == mock_data
            mock_service.get_dashboard_summary.assert_called_once()
    
    def test_dashboard_summary_error(self):
        """Test dashboard summary error handling"""
        with patch('backend.services.flask_reporting_service.ReportingService') as mock_service_class:
            mock_service = Mock()
            mock_service.get_dashboard_summary.side_effect = Exception("Test error")
            mock_service_class.return_value = mock_service
            
            result = self.flask_service.get_dashboard_summary()
            
            assert result is None
    
    def test_performance_metrics_success(self):
        """Test successful performance metrics retrieval"""
        mock_data = {'performance_data': []}
        
        with patch('backend.services.flask_reporting_service.ReportingService') as mock_service_class:
            mock_service = Mock()
            mock_service.get_performance_metrics.return_value = mock_data
            mock_service_class.return_value = mock_service
            
            result = self.flask_service.get_performance_metrics(group_by='channel')
            
            assert result == mock_data
            mock_service.get_performance_metrics.assert_called_once_with(None, None, 'channel')
    
    def test_time_series_data_success(self):
        """Test successful time series data retrieval"""
        mock_data = [{'timestamp': '2025-01-01', 'value': 10}]
        
        with patch('backend.services.flask_reporting_service.ReportingService') as mock_service_class:
            mock_service = Mock()
            mock_service.get_time_series_data.return_value = mock_data
            mock_service_class.return_value = mock_service
            
            result = self.flask_service.get_time_series_data(metric='messages', interval='day')
            
            assert result == mock_data
            mock_service.get_time_series_data.assert_called_once_with(None, None, 'messages', 'day')


class TestReportingAPIEndpoints:
    """Test reporting API endpoints integration"""
    
    def setup_method(self):
        """Setup test environment"""
        self.app = Mock()
        self.app.config = {}
        self.client = Mock()
    
    def test_dashboard_summary_endpoint_success(self):
        """Test successful dashboard summary endpoint"""
        with patch('backend.routes.reporting_api.ReportingService') as mock_service_class:
            mock_service = Mock()
            mock_data = {'summary': {'total_messages': 100}}
            mock_service.get_dashboard_summary.return_value = mock_data
            mock_service_class.return_value = mock_service
            
            with patch('backend.routes.reporting_api.get_jwt_identity') as mock_identity:
                mock_identity.return_value = 123
                
                with patch('backend.routes.reporting_api.request') as mock_request:
                    mock_request.args = {'start_date': '2025-01-01'}
                    
                    with patch('backend.routes.reporting_api.jsonify') as mock_jsonify:
                        mock_jsonify.return_value = Mock()
                        
                        # This would be called in the actual endpoint
                        from backend.routes.reporting_api import get_dashboard_summary
                        result = get_dashboard_summary()
                        
                        # Verify service was called
                        mock_service.get_dashboard_summary.assert_called_once()
    
    def test_performance_metrics_endpoint_validation(self):
        """Test performance metrics endpoint parameter validation"""
        with patch('backend.routes.reporting_api.ReportingService') as mock_service_class:
            mock_service = Mock()
            mock_service_class.return_value = mock_service
            
            with patch('backend.routes.reporting_api.get_jwt_identity') as mock_identity:
                mock_identity.return_value = 123
                
                with patch('backend.routes.reporting_api.request') as mock_request:
                    mock_request.args = {'group_by': 'invalid_group'}
                    
                    with patch('backend.routes.reporting_api.handle_reporting_error') as mock_error_handler:
                        mock_error_handler.return_value = Mock()
                        
                        # This would raise ValueError in the actual endpoint
                        from backend.routes.reporting_api import get_performance_metrics
                        result = get_performance_metrics()
                        
                        # Verify error handler was called
                        mock_error_handler.assert_called_once()
    
    def test_error_handling_sqlalchemy_error(self):
        """Test SQLAlchemy error handling"""
        error = SQLAlchemyError("Database connection failed")
        
        with patch('backend.routes.reporting_api.jsonify') as mock_jsonify:
            mock_jsonify.return_value = Mock()
            
            result = handle_reporting_error("test operation", error)
            
            # Verify error response structure
            mock_jsonify.assert_called_once()
            call_args = mock_jsonify.call_args[0][0]
            assert call_args['error'] == 'Database error occurred'
            assert call_args['operation'] == 'test operation'
    
    def test_error_handling_value_error(self):
        """Test ValueError handling"""
        error = ValueError("Invalid parameter")
        
        with patch('backend.routes.reporting_api.jsonify') as mock_jsonify:
            mock_jsonify.return_value = Mock()
            
            result = handle_reporting_error("test operation", error)
            
            # Verify error response structure
            mock_jsonify.assert_called_once()
            call_args = mock_jsonify.call_args[0][0]
            assert call_args['error'] == 'Invalid parameter'
            assert call_args['operation'] == 'test operation'
    
    def test_error_handling_generic_error(self):
        """Test generic error handling"""
        error = Exception("Unexpected error")
        
        with patch('backend.routes.reporting_api.jsonify') as mock_jsonify:
            mock_jsonify.return_value = Mock()
            
            result = handle_reporting_error("test operation", error)
            
            # Verify error response structure
            mock_jsonify.assert_called_once()
            call_args = mock_jsonify.call_args[0][0]
            assert call_args['error'] == 'An unexpected error occurred'
            assert call_args['operation'] == 'test operation'


class TestDatabaseIntegration:
    """Test database integration with existing mingus.db structure"""
    
    def test_session_management_integration(self):
        """Test integration with existing session management"""
        with patch('backend.database.get_flask_db_session') as mock_get_session:
            mock_session = Mock()
            mock_get_session.return_value = mock_session
            
            # Test that reporting service integrates with Flask session management
            service = ReportingService()
            
            # Verify session is retrieved correctly
            session = service._get_session()
            assert session == mock_session
            mock_get_session.assert_called_once()
    
    def test_session_cleanup_integration(self):
        """Test session cleanup integration"""
        with patch('backend.database.get_current_db_session') as mock_get_current:
            with patch('backend.database.get_flask_db_session') as mock_get_session:
                mock_session = Mock()
                mock_get_session.return_value = mock_session
                mock_get_current.return_value = mock_session
                
                service = ReportingService()
                
                # Simulate database error
                with patch.object(service, '_get_session') as mock_get:
                    mock_get.return_value = mock_session
                    mock_session.query.side_effect = SQLAlchemyError("Test error")
                    
                    with pytest.raises(SQLAlchemyError):
                        service.get_dashboard_summary()
                    
                    # Verify rollback was called
                    mock_session.rollback.assert_called_once()
    
    def test_database_models_integration(self):
        """Test integration with existing database models"""
        with patch('backend.database.get_flask_db_session') as mock_get_session:
            mock_session = Mock()
            mock_get_session.return_value = mock_session
            
            # Mock query results
            mock_metrics = [
                Mock(
                    id=1,
                    user_id=123,
                    message_type='test',
                    channel='sms',
                    status='delivered',
                    cost=0.05,
                    sent_at=datetime.utcnow(),
                    delivered_at=datetime.utcnow(),
                    opened_at=None,
                    clicked_at=None,
                    action_taken=None
                )
            ]
            
            mock_session.query.return_value.filter.return_value.count.return_value = 1
            mock_session.query.return_value.filter.return_value.group_by.return_value.all.return_value = []
            
            service = ReportingService()
            
            # Test that service can work with existing models
            result = service.get_dashboard_summary()
            
            # Verify query was executed
            mock_session.query.assert_called()


class TestConvenienceFunctions:
    """Test convenience functions for easy integration"""
    
    def test_convenience_function_imports(self):
        """Test that convenience functions can be imported"""
        from backend.services.flask_reporting_service import (
            get_dashboard_summary,
            get_performance_metrics,
            get_time_series_data,
            get_trend_analysis,
            get_user_segments,
            get_segment_performance,
            get_correlation_analysis,
            get_predictive_insights,
            get_comprehensive_report
        )
        
        # Verify all functions are callable
        assert callable(get_dashboard_summary)
        assert callable(get_performance_metrics)
        assert callable(get_time_series_data)
        assert callable(get_trend_analysis)
        assert callable(get_user_segments)
        assert callable(get_segment_performance)
        assert callable(get_correlation_analysis)
        assert callable(get_predictive_insights)
        assert callable(get_comprehensive_report)
    
    def test_convenience_function_usage(self):
        """Test convenience function usage"""
        with patch('backend.services.flask_reporting_service.FlaskReportingService') as mock_service_class:
            mock_service = Mock()
            mock_service_class.return_value = mock_service
            mock_service.get_dashboard_summary.return_value = {'test': 'data'}
            
            from backend.services.flask_reporting_service import get_dashboard_summary
            
            result = get_dashboard_summary()
            
            assert result == {'test': 'data'}
            mock_service.get_dashboard_summary.assert_called_once()


class TestMigrationIntegration:
    """Test migration integration with existing database"""
    
    def test_migration_file_structure(self):
        """Test that migration file has correct structure"""
        # This would test the actual migration file
        # For now, we'll verify the file exists and has expected content
        import os
        
        migration_file = 'migrations/006_create_reporting_indexes.sql'
        assert os.path.exists(migration_file)
        
        with open(migration_file, 'r') as f:
            content = f.read()
            
            # Verify key components exist
            assert 'CREATE INDEX' in content
            assert 'communication_metrics' in content
            assert 'user_engagement_summary' in content
            assert 'channel_performance_summary' in content
            assert 'message_type_performance_summary' in content
    
    def test_migration_sql_syntax(self):
        """Test that migration SQL has correct syntax"""
        # This would validate SQL syntax
        # For now, we'll check for basic SQL structure
        import os
        
        migration_file = 'migrations/006_create_reporting_indexes.sql'
        
        with open(migration_file, 'r') as f:
            content = f.read()
            
            # Verify SQL statements are properly terminated
            assert content.count(';') > 0
            
            # Verify CREATE statements
            assert 'CREATE INDEX' in content
            assert 'CREATE OR REPLACE VIEW' in content
            assert 'CREATE OR REPLACE FUNCTION' in content


if __name__ == '__main__':
    pytest.main([__file__]) 