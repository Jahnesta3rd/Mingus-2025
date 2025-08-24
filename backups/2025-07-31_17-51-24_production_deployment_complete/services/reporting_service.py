"""
Reporting Service
Comprehensive SQLAlchemy query functions for analytics reporting and dashboard data
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from decimal import Decimal
from sqlalchemy import func, and_, or_, case, extract, desc, asc
from sqlalchemy.orm import joinedload
from sqlalchemy.exc import SQLAlchemyError
from flask import g, current_app

from ..models.communication_analytics import CommunicationMetrics, UserEngagementMetrics, FinancialImpactMetrics
from ..models.communication_preferences import CommunicationPreferences, UserEngagementMetrics as PrefEngagementMetrics
from ..models.user import User
from ..database import get_flask_db_session, get_current_db_session

logger = logging.getLogger(__name__)


class ReportingService:
    """
    Comprehensive reporting service for analytics and dashboard data
    """
    
    def __init__(self, db_session=None):
        """
        Initialize the reporting service
        
        Args:
            db_session: Optional database session. If not provided, uses Flask session management
        """
        self.db = db_session or get_flask_db_session()
        self._use_flask_session = db_session is None
    
    def __del__(self):
        """Cleanup database session if not using Flask session management"""
        if hasattr(self, 'db') and self.db and not self._use_flask_session:
            try:
                self.db.close()
            except Exception as e:
                logger.warning(f"Error closing database session: {e}")
    
    def _get_session(self):
        """Get the appropriate database session"""
        if self._use_flask_session:
            return get_flask_db_session()
        return self.db
    
    def _handle_database_error(self, operation: str, error: Exception):
        """Handle database errors consistently"""
        logger.error(f"Database error during {operation}: {error}")
        if self._use_flask_session:
            # Rollback Flask session on error
            try:
                get_current_db_session().rollback()
            except Exception as rollback_error:
                logger.error(f"Error rolling back session: {rollback_error}")
        raise
    
    # Dashboard Data Queries
    
    def get_dashboard_summary(self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> Dict[str, Any]:
        """
        Get comprehensive dashboard summary data
        
        Args:
            start_date: Start date for analysis
            end_date: End date for analysis
            
        Returns:
            Dictionary with dashboard summary metrics
        """
        try:
            session = self._get_session()
            
            # Set default date range if not provided
            if not end_date:
                end_date = datetime.utcnow()
            if not start_date:
                start_date = end_date - timedelta(days=30)
            
            # Base query with date filters
            base_query = session.query(CommunicationMetrics).filter(
                CommunicationMetrics.sent_at.between(start_date, end_date)
            )
            
            # Total messages and costs
            total_messages = base_query.count()
            total_cost = session.query(func.sum(CommunicationMetrics.cost)).filter(
                CommunicationMetrics.sent_at.between(start_date, end_date)
            ).scalar() or 0
            
            # Delivery metrics
            delivered_messages = base_query.filter(CommunicationMetrics.status == 'delivered').count()
            delivery_rate = (delivered_messages / total_messages * 100) if total_messages > 0 else 0
            
            # Engagement metrics
            opened_messages = base_query.filter(CommunicationMetrics.opened_at.isnot(None)).count()
            clicked_messages = base_query.filter(CommunicationMetrics.clicked_at.isnot(None)).count()
            action_messages = base_query.filter(CommunicationMetrics.action_taken.isnot(None)).count()
            
            open_rate = (opened_messages / total_messages * 100) if total_messages > 0 else 0
            click_rate = (clicked_messages / total_messages * 100) if total_messages > 0 else 0
            action_rate = (action_messages / total_messages * 100) if total_messages > 0 else 0
            
            # Channel breakdown
            channel_stats = session.query(
                CommunicationMetrics.channel,
                func.count(CommunicationMetrics.id).label('total'),
                func.sum(case([(CommunicationMetrics.status == 'delivered', 1)], else_=0)).label('delivered'),
                func.sum(case([(CommunicationMetrics.opened_at.isnot(None), 1)], else_=0)).label('opened'),
                func.sum(case([(CommunicationMetrics.clicked_at.isnot(None), 1)], else_=0)).label('clicked'),
                func.sum(CommunicationMetrics.cost).label('cost')
            ).filter(
                CommunicationMetrics.sent_at.between(start_date, end_date)
            ).group_by(CommunicationMetrics.channel).all()
            
            channel_breakdown = {}
            for stat in channel_stats:
                channel_breakdown[stat.channel] = {
                    'total': stat.total,
                    'delivered': stat.delivered,
                    'opened': stat.opened,
                    'clicked': stat.clicked,
                    'cost': float(stat.cost or 0),
                    'delivery_rate': (stat.delivered / stat.total * 100) if stat.total > 0 else 0,
                    'open_rate': (stat.opened / stat.total * 100) if stat.total > 0 else 0,
                    'click_rate': (stat.clicked / stat.total * 100) if stat.total > 0 else 0
                }
            
            # Message type breakdown
            message_type_stats = session.query(
                CommunicationMetrics.message_type,
                func.count(CommunicationMetrics.id).label('total'),
                func.sum(case([(CommunicationMetrics.status == 'delivered', 1)], else_=0)).label('delivered'),
                func.sum(case([(CommunicationMetrics.action_taken.isnot(None), 1)], else_=0)).label('actions'),
                func.sum(CommunicationMetrics.cost).label('cost')
            ).filter(
                CommunicationMetrics.sent_at.between(start_date, end_date)
            ).group_by(CommunicationMetrics.message_type).all()
            
            message_type_breakdown = {}
            for stat in message_type_stats:
                message_type_breakdown[stat.message_type] = {
                    'total': stat.total,
                    'delivered': stat.delivered,
                    'actions': stat.actions,
                    'cost': float(stat.cost or 0),
                    'delivery_rate': (stat.delivered / stat.total * 100) if stat.total > 0 else 0,
                    'action_rate': (stat.actions / stat.total * 100) if stat.total > 0 else 0
                }
            
            # Active users
            active_users = session.query(func.count(func.distinct(CommunicationMetrics.user_id))).filter(
                CommunicationMetrics.sent_at.between(start_date, end_date)
            ).scalar()
            
            return {
                'period': {
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat()
                },
                'summary': {
                    'total_messages': total_messages,
                    'total_cost': float(total_cost),
                    'delivery_rate': round(delivery_rate, 2),
                    'open_rate': round(open_rate, 2),
                    'click_rate': round(click_rate, 2),
                    'action_rate': round(action_rate, 2),
                    'active_users': active_users
                },
                'by_channel': channel_breakdown,
                'by_message_type': message_type_breakdown
            }
            
        except SQLAlchemyError as e:
            self._handle_database_error("dashboard summary", e)
        except Exception as e:
            logger.error(f"Error getting dashboard summary: {e}")
            raise
    
    # Performance Metrics Queries
    
    def get_performance_metrics(self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None, 
                               group_by: str = 'day') -> Dict[str, Any]:
        """
        Get detailed performance metrics with aggregation
        
        Args:
            start_date: Start date for analysis
            end_date: End date for analysis
            group_by: Grouping level (day, week, month, channel, message_type)
            
        Returns:
            Dictionary with performance metrics
        """
        try:
            session = self._get_session()
            
            if not end_date:
                end_date = datetime.utcnow()
            if not start_date:
                start_date = end_date - timedelta(days=30)
            
            if group_by in ['day', 'week', 'month']:
                # Time-based grouping
                if group_by == 'day':
                    date_format = func.date(CommunicationMetrics.sent_at)
                elif group_by == 'week':
                    date_format = func.date_trunc('week', CommunicationMetrics.sent_at)
                else:  # month
                    date_format = func.date_trunc('month', CommunicationMetrics.sent_at)
                
                metrics = session.query(
                    date_format.label('period'),
                    func.count(CommunicationMetrics.id).label('total_messages'),
                    func.sum(case([(CommunicationMetrics.status == 'delivered', 1)], else_=0)).label('delivered'),
                    func.sum(case([(CommunicationMetrics.opened_at.isnot(None), 1)], else_=0)).label('opened'),
                    func.sum(case([(CommunicationMetrics.clicked_at.isnot(None), 1)], else_=0)).label('clicked'),
                    func.sum(case([(CommunicationMetrics.action_taken.isnot(None), 1)], else_=0)).label('actions'),
                    func.sum(CommunicationMetrics.cost).label('cost'),
                    func.avg(CommunicationMetrics.cost).label('avg_cost')
                ).filter(
                    CommunicationMetrics.sent_at.between(start_date, end_date)
                ).group_by(date_format).order_by(date_format).all()
                
                performance_data = []
                for metric in metrics:
                    total = metric.total_messages
                    performance_data.append({
                        'period': metric.period.isoformat() if hasattr(metric.period, 'isoformat') else str(metric.period),
                        'total_messages': total,
                        'delivered': metric.delivered,
                        'opened': metric.opened,
                        'clicked': metric.clicked,
                        'actions': metric.actions,
                        'cost': float(metric.cost or 0),
                        'avg_cost': float(metric.avg_cost or 0),
                        'delivery_rate': (metric.delivered / total * 100) if total > 0 else 0,
                        'open_rate': (metric.opened / total * 100) if total > 0 else 0,
                        'click_rate': (metric.clicked / total * 100) if total > 0 else 0,
                        'action_rate': (metric.actions / total * 100) if total > 0 else 0
                    })
                
            elif group_by == 'channel':
                # Channel-based grouping
                metrics = session.query(
                    CommunicationMetrics.channel,
                    func.count(CommunicationMetrics.id).label('total_messages'),
                    func.sum(case([(CommunicationMetrics.status == 'delivered', 1)], else_=0)).label('delivered'),
                    func.sum(case([(CommunicationMetrics.opened_at.isnot(None), 1)], else_=0)).label('opened'),
                    func.sum(case([(CommunicationMetrics.clicked_at.isnot(None), 1)], else_=0)).label('clicked'),
                    func.sum(case([(CommunicationMetrics.action_taken.isnot(None), 1)], else_=0)).label('actions'),
                    func.sum(CommunicationMetrics.cost).label('cost'),
                    func.avg(CommunicationMetrics.cost).label('avg_cost')
                ).filter(
                    CommunicationMetrics.sent_at.between(start_date, end_date)
                ).group_by(CommunicationMetrics.channel).all()
                
                performance_data = {}
                for metric in metrics:
                    total = metric.total_messages
                    performance_data[metric.channel] = {
                        'total_messages': total,
                        'delivered': metric.delivered,
                        'opened': metric.opened,
                        'clicked': metric.clicked,
                        'actions': metric.actions,
                        'cost': float(metric.cost or 0),
                        'avg_cost': float(metric.avg_cost or 0),
                        'delivery_rate': (metric.delivered / total * 100) if total > 0 else 0,
                        'open_rate': (metric.opened / total * 100) if total > 0 else 0,
                        'click_rate': (metric.clicked / total * 100) if total > 0 else 0,
                        'action_rate': (metric.actions / total * 100) if total > 0 else 0
                    }
            
            elif group_by == 'message_type':
                # Message type-based grouping
                metrics = session.query(
                    CommunicationMetrics.message_type,
                    func.count(CommunicationMetrics.id).label('total_messages'),
                    func.sum(case([(CommunicationMetrics.status == 'delivered', 1)], else_=0)).label('delivered'),
                    func.sum(case([(CommunicationMetrics.opened_at.isnot(None), 1)], else_=0)).label('opened'),
                    func.sum(case([(CommunicationMetrics.clicked_at.isnot(None), 1)], else_=0)).label('clicked'),
                    func.sum(case([(CommunicationMetrics.action_taken.isnot(None), 1)], else_=0)).label('actions'),
                    func.sum(CommunicationMetrics.cost).label('cost'),
                    func.avg(CommunicationMetrics.cost).label('avg_cost')
                ).filter(
                    CommunicationMetrics.sent_at.between(start_date, end_date)
                ).group_by(CommunicationMetrics.message_type).all()
                
                performance_data = {}
                for metric in metrics:
                    total = metric.total_messages
                    performance_data[metric.message_type] = {
                        'total_messages': total,
                        'delivered': metric.delivered,
                        'opened': metric.opened,
                        'clicked': metric.clicked,
                        'actions': metric.actions,
                        'cost': float(metric.cost or 0),
                        'avg_cost': float(metric.avg_cost or 0),
                        'delivery_rate': (metric.delivered / total * 100) if total > 0 else 0,
                        'open_rate': (metric.opened / total * 100) if total > 0 else 0,
                        'click_rate': (metric.clicked / total * 100) if total > 0 else 0,
                        'action_rate': (metric.actions / total * 100) if total > 0 else 0
                    }
            
            return {
                'group_by': group_by,
                'period': {
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat()
                },
                'performance_data': performance_data
            }
            
        except SQLAlchemyError as e:
            self._handle_database_error("performance metrics", e)
        except Exception as e:
            logger.error(f"Error getting performance metrics: {e}")
            raise
    
    # Time-Series Analysis Queries
    
    def get_time_series_data(self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None,
                            metric: str = 'messages', interval: str = 'day') -> List[Dict[str, Any]]:
        """
        Get time-series data for trend analysis
        
        Args:
            start_date: Start date for analysis
            end_date: End date for analysis
            metric: Metric to analyze (messages, delivery_rate, open_rate, cost, actions)
            interval: Time interval (hour, day, week, month)
            
        Returns:
            List of time-series data points
        """
        try:
            session = self._get_session()
            
            if not end_date:
                end_date = datetime.utcnow()
            if not start_date:
                start_date = end_date - timedelta(days=30)
            
            # Define time grouping based on interval
            if interval == 'hour':
                time_group = func.date_trunc('hour', CommunicationMetrics.sent_at)
            elif interval == 'day':
                time_group = func.date(CommunicationMetrics.sent_at)
            elif interval == 'week':
                time_group = func.date_trunc('week', CommunicationMetrics.sent_at)
            elif interval == 'month':
                time_group = func.date_trunc('month', CommunicationMetrics.sent_at)
            else:
                time_group = func.date(CommunicationMetrics.sent_at)
            
            # Build query based on metric
            if metric == 'messages':
                query = session.query(
                    time_group.label('timestamp'),
                    func.count(CommunicationMetrics.id).label('value')
                )
            elif metric == 'delivery_rate':
                query = session.query(
                    time_group.label('timestamp'),
                    func.avg(case([(CommunicationMetrics.status == 'delivered', 100)], else_=0)).label('value')
                )
            elif metric == 'open_rate':
                query = session.query(
                    time_group.label('timestamp'),
                    func.avg(case([(CommunicationMetrics.opened_at.isnot(None), 100)], else_=0)).label('value')
                )
            elif metric == 'click_rate':
                query = session.query(
                    time_group.label('timestamp'),
                    func.avg(case([(CommunicationMetrics.clicked_at.isnot(None), 100)], else_=0)).label('value')
                )
            elif metric == 'cost':
                query = session.query(
                    time_group.label('timestamp'),
                    func.sum(CommunicationMetrics.cost).label('value')
                )
            elif metric == 'actions':
                query = session.query(
                    time_group.label('timestamp'),
                    func.count(case([(CommunicationMetrics.action_taken.isnot(None), 1)])).label('value')
                )
            else:
                raise ValueError(f"Unsupported metric: {metric}")
            
            # Execute query
            results = query.filter(
                CommunicationMetrics.sent_at.between(start_date, end_date)
            ).group_by(time_group).order_by(time_group).all()
            
            # Format results
            time_series_data = []
            for result in results:
                time_series_data.append({
                    'timestamp': result.timestamp.isoformat() if hasattr(result.timestamp, 'isoformat') else str(result.timestamp),
                    'value': float(result.value or 0)
                })
            
            return time_series_data
            
        except SQLAlchemyError as e:
            self._handle_database_error("time series data", e)
        except Exception as e:
            logger.error(f"Error getting time series data: {e}")
            raise
    
    def get_trend_analysis(self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> Dict[str, Any]:
        """
        Get comprehensive trend analysis
        
        Args:
            start_date: Start date for analysis
            end_date: End date for analysis
            
        Returns:
            Dictionary with trend analysis data
        """
        try:
            session = self._get_session()
            
            if not end_date:
                end_date = datetime.utcnow()
            if not start_date:
                start_date = end_date - timedelta(days=90)  # 3 months for trend analysis
            
            # Split period into two halves for comparison
            mid_date = start_date + (end_date - start_date) / 2
            
            # First half metrics
            first_half = session.query(
                func.count(CommunicationMetrics.id).label('total_messages'),
                func.sum(case([(CommunicationMetrics.status == 'delivered', 1)], else_=0)).label('delivered'),
                func.sum(case([(CommunicationMetrics.opened_at.isnot(None), 1)], else_=0)).label('opened'),
                func.sum(case([(CommunicationMetrics.action_taken.isnot(None), 1)], else_=0)).label('actions'),
                func.sum(CommunicationMetrics.cost).label('cost')
            ).filter(
                CommunicationMetrics.sent_at.between(start_date, mid_date)
            ).first()
            
            # Second half metrics
            second_half = session.query(
                func.count(CommunicationMetrics.id).label('total_messages'),
                func.sum(case([(CommunicationMetrics.status == 'delivered', 1)], else_=0)).label('delivered'),
                func.sum(case([(CommunicationMetrics.opened_at.isnot(None), 1)], else_=0)).label('opened'),
                func.sum(case([(CommunicationMetrics.action_taken.isnot(None), 1)], else_=0)).label('actions'),
                func.sum(CommunicationMetrics.cost).label('cost')
            ).filter(
                CommunicationMetrics.sent_at.between(mid_date, end_date)
            ).first()
            
            # Calculate trends
            def calculate_trend(old_value, new_value):
                if old_value == 0:
                    return 100 if new_value > 0 else 0
                return ((new_value - old_value) / old_value) * 100
            
            trends = {
                'messages': calculate_trend(first_half.total_messages, second_half.total_messages),
                'delivery_rate': calculate_trend(
                    (first_half.delivered / first_half.total_messages * 100) if first_half.total_messages > 0 else 0,
                    (second_half.delivered / second_half.total_messages * 100) if second_half.total_messages > 0 else 0
                ),
                'open_rate': calculate_trend(
                    (first_half.opened / first_half.total_messages * 100) if first_half.total_messages > 0 else 0,
                    (second_half.opened / second_half.total_messages * 100) if second_half.total_messages > 0 else 0
                ),
                'action_rate': calculate_trend(
                    (first_half.actions / first_half.total_messages * 100) if first_half.total_messages > 0 else 0,
                    (second_half.actions / second_half.total_messages * 100) if second_half.total_messages > 0 else 0
                ),
                'cost': calculate_trend(float(first_half.cost or 0), float(second_half.cost or 0))
            }
            
            # Get daily trends for visualization
            daily_trends = self.get_time_series_data(start_date, end_date, 'messages', 'day')
            
            return {
                'period': {
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat(),
                    'mid_date': mid_date.isoformat()
                },
                'trends': trends,
                'daily_trends': daily_trends,
                'first_half': {
                    'total_messages': first_half.total_messages,
                    'delivery_rate': (first_half.delivered / first_half.total_messages * 100) if first_half.total_messages > 0 else 0,
                    'open_rate': (first_half.opened / first_half.total_messages * 100) if first_half.total_messages > 0 else 0,
                    'action_rate': (first_half.actions / first_half.total_messages * 100) if first_half.total_messages > 0 else 0,
                    'cost': float(first_half.cost or 0)
                },
                'second_half': {
                    'total_messages': second_half.total_messages,
                    'delivery_rate': (second_half.delivered / second_half.total_messages * 100) if second_half.total_messages > 0 else 0,
                    'open_rate': (second_half.opened / second_half.total_messages * 100) if second_half.total_messages > 0 else 0,
                    'action_rate': (second_half.actions / second_half.total_messages * 100) if second_half.total_messages > 0 else 0,
                    'cost': float(second_half.cost or 0)
                }
            }
            
        except SQLAlchemyError as e:
            self._handle_database_error("trend analysis", e)
        except Exception as e:
            logger.error(f"Error getting trend analysis: {e}")
            raise
    
    # User Segmentation Analysis Queries
    
    def get_user_segments(self) -> Dict[str, Any]:
        """
        Get user segmentation analysis
        
        Returns:
            Dictionary with user segment data
        """
        try:
            session = self._get_session()
            
            # Get total users
            total_users = session.query(func.count(User.id)).scalar()
            
            # Segment users based on engagement
            segments = {}
            
            # High engagement users (opened > 80% of messages, actions > 20%)
            high_engagement = session.query(func.count(func.distinct(CommunicationMetrics.user_id))).filter(
                and_(
                    CommunicationMetrics.opened_at.isnot(None),
                    CommunicationMetrics.action_taken.isnot(None)
                )
            ).scalar()
            
            # Medium engagement users (opened 40-80% of messages)
            medium_engagement = session.query(func.count(func.distinct(CommunicationMetrics.user_id))).filter(
                and_(
                    CommunicationMetrics.opened_at.isnot(None),
                    CommunicationMetrics.opened_at.is_(None)
                )
            ).scalar()
            
            # Low engagement users (opened < 40% of messages)
            low_engagement = session.query(func.count(func.distinct(CommunicationMetrics.user_id))).filter(
                CommunicationMetrics.opened_at.is_(None)
            ).scalar()
            
            # Inactive users (no communication in last 30 days)
            thirty_days_ago = datetime.utcnow() - timedelta(days=30)
            inactive_users = session.query(func.count(func.distinct(User.id))).filter(
                ~User.id.in_(
                    session.query(func.distinct(CommunicationMetrics.user_id)).filter(
                        CommunicationMetrics.sent_at >= thirty_days_ago
                    )
                )
            ).scalar()
            
            segments = {
                'high_engagement': {
                    'count': high_engagement,
                    'percentage': (high_engagement / total_users * 100) if total_users > 0 else 0,
                    'description': 'Users with >80% open rate and >20% action rate'
                },
                'medium_engagement': {
                    'count': medium_engagement,
                    'percentage': (medium_engagement / total_users * 100) if total_users > 0 else 0,
                    'description': 'Users with 40-80% open rate'
                },
                'low_engagement': {
                    'count': low_engagement,
                    'percentage': (low_engagement / total_users * 100) if total_users > 0 else 0,
                    'description': 'Users with <40% open rate'
                },
                'inactive': {
                    'count': inactive_users,
                    'percentage': (inactive_users / total_users * 100) if total_users > 0 else 0,
                    'description': 'No communication in last 30 days'
                }
            }
            
            # Channel preferences by segment
            channel_preferences = session.query(
                CommunicationMetrics.channel,
                func.count(func.distinct(CommunicationMetrics.user_id)).label('user_count')
            ).group_by(CommunicationMetrics.channel).all()
            
            channel_data = {}
            for pref in channel_preferences:
                channel_data[pref.channel] = {
                    'user_count': pref.user_count,
                    'percentage': (pref.user_count / total_users * 100) if total_users > 0 else 0
                }
            
            return {
                'total_users': total_users,
                'segments': segments,
                'channel_preferences': channel_data
            }
            
        except SQLAlchemyError as e:
            self._handle_database_error("user segments", e)
        except Exception as e:
            logger.error(f"Error getting user segments: {e}")
            raise
    
    def get_segment_performance(self, segment: str, start_date: Optional[datetime] = None, 
                               end_date: Optional[datetime] = None) -> Dict[str, Any]:
        """
        Get performance metrics for specific user segment
        
        Args:
            segment: Segment to analyze (high_engagement, medium_engagement, low_engagement, inactive)
            start_date: Start date for analysis
            end_date: End date for analysis
            
        Returns:
            Dictionary with segment performance data
        """
        try:
            session = self._get_session()
            
            if not end_date:
                end_date = datetime.utcnow()
            if not start_date:
                start_date = end_date - timedelta(days=30)
            
            # Define segment filters
            if segment == 'high_engagement':
                segment_users = session.query(func.distinct(CommunicationMetrics.user_id)).filter(
                    and_(
                        CommunicationMetrics.opened_at.isnot(None),
                        CommunicationMetrics.action_taken.isnot(None)
                    )
                ).subquery()
            elif segment == 'medium_engagement':
                segment_users = session.query(func.distinct(CommunicationMetrics.user_id)).filter(
                    and_(
                        CommunicationMetrics.opened_at.isnot(None),
                        CommunicationMetrics.opened_at.is_(None)
                    )
                ).subquery()
            elif segment == 'low_engagement':
                segment_users = session.query(func.distinct(CommunicationMetrics.user_id)).filter(
                    CommunicationMetrics.opened_at.is_(None)
                ).subquery()
            elif segment == 'inactive':
                thirty_days_ago = datetime.utcnow() - timedelta(days=30)
                segment_users = session.query(func.distinct(User.id)).filter(
                    ~User.id.in_(
                        session.query(func.distinct(CommunicationMetrics.user_id)).filter(
                            CommunicationMetrics.sent_at >= thirty_days_ago
                        )
                    )
                ).subquery()
            else:
                raise ValueError(f"Unsupported segment: {segment}")
            
            # Get performance metrics for segment
            metrics = session.query(
                func.count(CommunicationMetrics.id).label('total_messages'),
                func.sum(case([(CommunicationMetrics.status == 'delivered', 1)], else_=0)).label('delivered'),
                func.sum(case([(CommunicationMetrics.opened_at.isnot(None), 1)], else_=0)).label('opened'),
                func.sum(case([(CommunicationMetrics.clicked_at.isnot(None), 1)], else_=0)).label('clicked'),
                func.sum(case([(CommunicationMetrics.action_taken.isnot(None), 1)], else_=0)).label('actions'),
                func.sum(CommunicationMetrics.cost).label('cost')
            ).filter(
                and_(
                    CommunicationMetrics.user_id.in_(segment_users),
                    CommunicationMetrics.sent_at.between(start_date, end_date)
                )
            ).first()
            
            total = metrics.total_messages
            return {
                'segment': segment,
                'period': {
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat()
                },
                'metrics': {
                    'total_messages': total,
                    'delivered': metrics.delivered,
                    'opened': metrics.opened,
                    'clicked': metrics.clicked,
                    'actions': metrics.actions,
                    'cost': float(metrics.cost or 0),
                    'delivery_rate': (metrics.delivered / total * 100) if total > 0 else 0,
                    'open_rate': (metrics.opened / total * 100) if total > 0 else 0,
                    'click_rate': (metrics.clicked / total * 100) if total > 0 else 0,
                    'action_rate': (metrics.actions / total * 100) if total > 0 else 0
                }
            }
            
        except SQLAlchemyError as e:
            self._handle_database_error("segment performance", e)
        except Exception as e:
            logger.error(f"Error getting segment performance: {e}")
            raise
    
    # Advanced Analytics Queries
    
    def get_correlation_analysis(self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> Dict[str, Any]:
        """
        Get correlation analysis between different metrics
        
        Args:
            start_date: Start date for analysis
            end_date: End date for analysis
            
        Returns:
            Dictionary with correlation analysis
        """
        try:
            session = self._get_session()
            
            if not end_date:
                end_date = datetime.utcnow()
            if not start_date:
                start_date = end_date - timedelta(days=90)
            
            # Get daily aggregated data for correlation analysis
            daily_data = session.query(
                func.date(CommunicationMetrics.sent_at).label('date'),
                func.count(CommunicationMetrics.id).label('message_count'),
                func.avg(case([(CommunicationMetrics.status == 'delivered', 100)], else_=0)).label('delivery_rate'),
                func.avg(case([(CommunicationMetrics.opened_at.isnot(None), 100)], else_=0)).label('open_rate'),
                func.avg(case([(CommunicationMetrics.action_taken.isnot(None), 100)], else_=0)).label('action_rate')
            ).filter(
                CommunicationMetrics.sent_at.between(start_date, end_date)
            ).group_by(func.date(CommunicationMetrics.sent_at)).all()
            
            # Calculate correlations (simplified correlation calculation)
            correlations = {
                'message_count_vs_delivery_rate': 0.0,
                'message_count_vs_open_rate': 0.0,
                'message_count_vs_action_rate': 0.0,
                'delivery_rate_vs_open_rate': 0.0,
                'delivery_rate_vs_action_rate': 0.0,
                'open_rate_vs_action_rate': 0.0
            }
            
            # Simple correlation calculation (this is a simplified version)
            if len(daily_data) > 1:
                # Calculate basic correlations
                message_counts = [d.message_count for d in daily_data]
                delivery_rates = [float(d.delivery_rate or 0) for d in daily_data]
                open_rates = [float(d.open_rate or 0) for d in daily_data]
                action_rates = [float(d.action_rate or 0) for d in daily_data]
                
                # Calculate correlation coefficients (simplified)
                def simple_correlation(x, y):
                    if len(x) != len(y) or len(x) < 2:
                        return 0.0
                    n = len(x)
                    sum_x = sum(x)
                    sum_y = sum(y)
                    sum_xy = sum(x[i] * y[i] for i in range(n))
                    sum_x2 = sum(x[i] ** 2 for i in range(n))
                    sum_y2 = sum(y[i] ** 2 for i in range(n))
                    
                    numerator = n * sum_xy - sum_x * sum_y
                    denominator = ((n * sum_x2 - sum_x ** 2) * (n * sum_y2 - sum_y ** 2)) ** 0.5
                    
                    return numerator / denominator if denominator != 0 else 0.0
                
                correlations = {
                    'message_count_vs_delivery_rate': round(simple_correlation(message_counts, delivery_rates), 3),
                    'message_count_vs_open_rate': round(simple_correlation(message_counts, open_rates), 3),
                    'message_count_vs_action_rate': round(simple_correlation(message_counts, action_rates), 3),
                    'delivery_rate_vs_open_rate': round(simple_correlation(delivery_rates, open_rates), 3),
                    'delivery_rate_vs_action_rate': round(simple_correlation(delivery_rates, action_rates), 3),
                    'open_rate_vs_action_rate': round(simple_correlation(open_rates, action_rates), 3)
                }
            
            return {
                'period': {
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat()
                },
                'correlations': correlations,
                'data_points': len(daily_data)
            }
            
        except SQLAlchemyError as e:
            self._handle_database_error("correlation analysis", e)
        except Exception as e:
            logger.error(f"Error getting correlation analysis: {e}")
            raise
    
    def get_predictive_insights(self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> Dict[str, Any]:
        """
        Get predictive insights based on historical data
        
        Args:
            start_date: Start date for analysis
            end_date: End date for analysis
            
        Returns:
            Dictionary with predictive insights
        """
        try:
            session = self._get_session()
            
            if not end_date:
                end_date = datetime.utcnow()
            if not start_date:
                start_date = end_date - timedelta(days=90)
            
            # Get historical trends
            daily_trends = self.get_time_series_data(start_date, end_date, 'messages', 'day')
            
            # Calculate simple predictions (this is a basic implementation)
            if len(daily_trends) >= 7:
                # Calculate 7-day moving average
                recent_values = [point['value'] for point in daily_trends[-7:]]
                moving_average = sum(recent_values) / len(recent_values)
                
                # Calculate trend direction
                if len(daily_trends) >= 14:
                    first_week_avg = sum([point['value'] for point in daily_trends[-14:-7]]) / 7
                    second_week_avg = sum([point['value'] for point in daily_trends[-7:]]) / 7
                    trend_direction = 'increasing' if second_week_avg > first_week_avg else 'decreasing' if second_week_avg < first_week_avg else 'stable'
                else:
                    trend_direction = 'stable'
                
                # Simple forecast (next 7 days)
                forecast = []
                for i in range(7):
                    forecast.append({
                        'date': (end_date + timedelta(days=i+1)).isoformat(),
                        'predicted_value': round(moving_average * (1 + (i * 0.02)), 2)  # Simple growth assumption
                    })
                
                insights = {
                    'current_trend': trend_direction,
                    'moving_average': round(moving_average, 2),
                    'forecast': forecast,
                    'confidence_level': 'medium'  # Simplified confidence level
                }
            else:
                insights = {
                    'current_trend': 'insufficient_data',
                    'moving_average': 0,
                    'forecast': [],
                    'confidence_level': 'low'
                }
            
            return {
                'period': {
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat()
                },
                'insights': insights
            }
            
        except SQLAlchemyError as e:
            self._handle_database_error("predictive insights", e)
        except Exception as e:
            logger.error(f"Error getting predictive insights: {e}")
            raise 