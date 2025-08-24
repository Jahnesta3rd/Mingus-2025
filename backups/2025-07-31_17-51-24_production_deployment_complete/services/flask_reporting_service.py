"""
Flask Reporting Service
Flask-specific wrapper for the reporting service with proper session management
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from sqlalchemy.exc import SQLAlchemyError

from .reporting_service import ReportingService
from ..database import get_flask_db_session, get_current_db_session

logger = logging.getLogger(__name__)


class FlaskReportingService:
    """
    Flask-specific wrapper for the reporting service
    Provides easy-to-use functions with proper session management
    """
    
    def __init__(self):
        """Initialize the Flask reporting service"""
        self._reporting_service = None
    
    def _get_service(self) -> ReportingService:
        """Get or create reporting service with Flask session"""
        if self._reporting_service is None:
            self._reporting_service = ReportingService()
        return self._reporting_service
    
    def get_dashboard_summary(self, start_date: Optional[datetime] = None, 
                            end_date: Optional[datetime] = None) -> Optional[Dict[str, Any]]:
        """
        Get dashboard summary with Flask session management
        
        Args:
            start_date: Start date for analysis
            end_date: End date for analysis
            
        Returns:
            Dashboard summary data or None on error
        """
        try:
            service = self._get_service()
            return service.get_dashboard_summary(start_date, end_date)
        except Exception as e:
            logger.error(f"Error getting dashboard summary: {e}")
            return None
    
    def get_performance_metrics(self, start_date: Optional[datetime] = None, 
                              end_date: Optional[datetime] = None, 
                              group_by: str = 'day') -> Optional[Dict[str, Any]]:
        """
        Get performance metrics with Flask session management
        
        Args:
            start_date: Start date for analysis
            end_date: End date for analysis
            group_by: Grouping level
            
        Returns:
            Performance metrics data or None on error
        """
        try:
            service = self._get_service()
            return service.get_performance_metrics(start_date, end_date, group_by)
        except Exception as e:
            logger.error(f"Error getting performance metrics: {e}")
            return None
    
    def get_time_series_data(self, start_date: Optional[datetime] = None, 
                           end_date: Optional[datetime] = None,
                           metric: str = 'messages', 
                           interval: str = 'day') -> Optional[List[Dict[str, Any]]]:
        """
        Get time series data with Flask session management
        
        Args:
            start_date: Start date for analysis
            end_date: End date for analysis
            metric: Metric to analyze
            interval: Time interval
            
        Returns:
            Time series data or None on error
        """
        try:
            service = self._get_service()
            return service.get_time_series_data(start_date, end_date, metric, interval)
        except Exception as e:
            logger.error(f"Error getting time series data: {e}")
            return None
    
    def get_trend_analysis(self, start_date: Optional[datetime] = None, 
                          end_date: Optional[datetime] = None) -> Optional[Dict[str, Any]]:
        """
        Get trend analysis with Flask session management
        
        Args:
            start_date: Start date for analysis
            end_date: End date for analysis
            
        Returns:
            Trend analysis data or None on error
        """
        try:
            service = self._get_service()
            return service.get_trend_analysis(start_date, end_date)
        except Exception as e:
            logger.error(f"Error getting trend analysis: {e}")
            return None
    
    def get_user_segments(self) -> Optional[Dict[str, Any]]:
        """
        Get user segments with Flask session management
        
        Returns:
            User segments data or None on error
        """
        try:
            service = self._get_service()
            return service.get_user_segments()
        except Exception as e:
            logger.error(f"Error getting user segments: {e}")
            return None
    
    def get_segment_performance(self, segment: str, 
                              start_date: Optional[datetime] = None, 
                              end_date: Optional[datetime] = None) -> Optional[Dict[str, Any]]:
        """
        Get segment performance with Flask session management
        
        Args:
            segment: Segment to analyze
            start_date: Start date for analysis
            end_date: End date for analysis
            
        Returns:
            Segment performance data or None on error
        """
        try:
            service = self._get_service()
            return service.get_segment_performance(segment, start_date, end_date)
        except Exception as e:
            logger.error(f"Error getting segment performance: {e}")
            return None
    
    def get_correlation_analysis(self, start_date: Optional[datetime] = None, 
                               end_date: Optional[datetime] = None) -> Optional[Dict[str, Any]]:
        """
        Get correlation analysis with Flask session management
        
        Args:
            start_date: Start date for analysis
            end_date: End date for analysis
            
        Returns:
            Correlation analysis data or None on error
        """
        try:
            service = self._get_service()
            return service.get_correlation_analysis(start_date, end_date)
        except Exception as e:
            logger.error(f"Error getting correlation analysis: {e}")
            return None
    
    def get_predictive_insights(self, start_date: Optional[datetime] = None, 
                              end_date: Optional[datetime] = None) -> Optional[Dict[str, Any]]:
        """
        Get predictive insights with Flask session management
        
        Args:
            start_date: Start date for analysis
            end_date: End date for analysis
            
        Returns:
            Predictive insights data or None on error
        """
        try:
            service = self._get_service()
            return service.get_predictive_insights(start_date, end_date)
        except Exception as e:
            logger.error(f"Error getting predictive insights: {e}")
            return None
    
    def get_comprehensive_report(self, start_date: Optional[datetime] = None, 
                               end_date: Optional[datetime] = None,
                               include_segments: bool = True,
                               include_predictions: bool = True) -> Optional[Dict[str, Any]]:
        """
        Get comprehensive report with Flask session management
        
        Args:
            start_date: Start date for analysis
            end_date: End date for analysis
            include_segments: Include user segments
            include_predictions: Include predictive insights
            
        Returns:
            Comprehensive report data or None on error
        """
        try:
            service = self._get_service()
            
            # Build comprehensive report
            report = {
                'generated_at': datetime.utcnow().isoformat(),
                'period': {
                    'start_date': start_date.isoformat() if start_date else None,
                    'end_date': end_date.isoformat() if end_date else None
                }
            }
            
            # Get dashboard summary
            dashboard = service.get_dashboard_summary(start_date, end_date)
            if dashboard:
                report['dashboard_summary'] = dashboard
            
            # Get performance metrics
            metrics = service.get_performance_metrics(start_date, end_date, 'day')
            if metrics:
                report['performance_metrics'] = metrics
            
            # Get trend analysis
            trends = service.get_trend_analysis(start_date, end_date)
            if trends:
                report['trend_analysis'] = trends
            
            # Get time series data
            time_series = {}
            for metric in ['messages', 'delivery_rate', 'open_rate', 'cost']:
                data = service.get_time_series_data(start_date, end_date, metric, 'day')
                if data:
                    time_series[metric] = data
            if time_series:
                report['time_series'] = time_series
            
            # Get correlation analysis
            correlations = service.get_correlation_analysis(start_date, end_date)
            if correlations:
                report['correlation_analysis'] = correlations
            
            # Include user segments if requested
            if include_segments:
                segments = service.get_user_segments()
                if segments:
                    report['user_segments'] = segments
                    
                    # Get performance for each segment
                    segment_performance = {}
                    for segment in ['high_engagement', 'medium_engagement', 'low_engagement']:
                        try:
                            perf = service.get_segment_performance(segment, start_date, end_date)
                            if perf:
                                segment_performance[segment] = perf
                        except Exception as e:
                            logger.warning(f"Could not get performance for segment {segment}: {e}")
                    
                    if segment_performance:
                        report['segment_performance'] = segment_performance
            
            # Include predictive insights if requested
            if include_predictions:
                insights = service.get_predictive_insights(start_date, end_date)
                if insights:
                    report['predictive_insights'] = insights
            
            return report
            
        except Exception as e:
            logger.error(f"Error getting comprehensive report: {e}")
            return None


# Convenience functions for direct import
def get_dashboard_summary(start_date: Optional[datetime] = None, 
                         end_date: Optional[datetime] = None) -> Optional[Dict[str, Any]]:
    """Convenience function to get dashboard summary"""
    service = FlaskReportingService()
    return service.get_dashboard_summary(start_date, end_date)


def get_performance_metrics(start_date: Optional[datetime] = None, 
                          end_date: Optional[datetime] = None, 
                          group_by: str = 'day') -> Optional[Dict[str, Any]]:
    """Convenience function to get performance metrics"""
    service = FlaskReportingService()
    return service.get_performance_metrics(start_date, end_date, group_by)


def get_time_series_data(start_date: Optional[datetime] = None, 
                        end_date: Optional[datetime] = None,
                        metric: str = 'messages', 
                        interval: str = 'day') -> Optional[List[Dict[str, Any]]]:
    """Convenience function to get time series data"""
    service = FlaskReportingService()
    return service.get_time_series_data(start_date, end_date, metric, interval)


def get_trend_analysis(start_date: Optional[datetime] = None, 
                      end_date: Optional[datetime] = None) -> Optional[Dict[str, Any]]:
    """Convenience function to get trend analysis"""
    service = FlaskReportingService()
    return service.get_trend_analysis(start_date, end_date)


def get_user_segments() -> Optional[Dict[str, Any]]:
    """Convenience function to get user segments"""
    service = FlaskReportingService()
    return service.get_user_segments()


def get_segment_performance(segment: str, 
                          start_date: Optional[datetime] = None, 
                          end_date: Optional[datetime] = None) -> Optional[Dict[str, Any]]:
    """Convenience function to get segment performance"""
    service = FlaskReportingService()
    return service.get_segment_performance(segment, start_date, end_date)


def get_correlation_analysis(start_date: Optional[datetime] = None, 
                           end_date: Optional[datetime] = None) -> Optional[Dict[str, Any]]:
    """Convenience function to get correlation analysis"""
    service = FlaskReportingService()
    return service.get_correlation_analysis(start_date, end_date)


def get_predictive_insights(start_date: Optional[datetime] = None, 
                          end_date: Optional[datetime] = None) -> Optional[Dict[str, Any]]:
    """Convenience function to get predictive insights"""
    service = FlaskReportingService()
    return service.get_predictive_insights(start_date, end_date)


def get_comprehensive_report(start_date: Optional[datetime] = None, 
                           end_date: Optional[datetime] = None,
                           include_segments: bool = True,
                           include_predictions: bool = True) -> Optional[Dict[str, Any]]:
    """Convenience function to get comprehensive report"""
    service = FlaskReportingService()
    return service.get_comprehensive_report(start_date, end_date, include_segments, include_predictions) 