"""
Analytics Service for tracking user events and behavior
Handles meme opt-out/opt-in tracking and other user engagement analytics
"""

from sqlalchemy.orm import Session
from sqlalchemy import and_, func, desc
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import json
import uuid
from ..models.analytics_models import UserEvent, AnalyticsEvent
from ..models.user import User


class AnalyticsService:
    """Service for tracking and analyzing user events"""
    
    def __init__(self, db_session: Session):
        self.db = db_session
    
    def track_event(self, user_id: int, event_type: str, event_data: Dict[str, Any] = None) -> UserEvent:
        """Track a user event"""
        try:
            event = UserEvent(
                id=str(uuid.uuid4()),
                user_id=user_id,
                event_type=event_type,
                event_data=json.dumps(event_data) if event_data else None,
                timestamp=datetime.utcnow(),
                session_id=event_data.get('session_id') if event_data else None,
                source=event_data.get('source') if event_data else None,
                user_agent=event_data.get('user_agent') if event_data else None,
                ip_address=event_data.get('ip_address') if event_data else None
            )
            
            self.db.add(event)
            self.db.commit()
            self.db.refresh(event)
            return event
            
        except Exception as e:
            self.db.rollback()
            raise e
    
    def get_meme_opt_out_analytics(self, days: int = 30) -> Dict[str, Any]:
        """Get analytics for meme opt-outs"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            # Total opt-outs in period
            total_opt_outs = self.db.query(func.count(UserEvent.id)).filter(
                and_(
                    UserEvent.event_type == 'meme_opt_out',
                    UserEvent.timestamp >= cutoff_date
                )
            ).scalar()
            
            # Opt-outs by source
            opt_outs_by_source = self.db.query(
                UserEvent.source,
                func.count(UserEvent.id)
            ).filter(
                and_(
                    UserEvent.event_type == 'meme_opt_out',
                    UserEvent.timestamp >= cutoff_date
                )
            ).group_by(UserEvent.source).all()
            
            # Opt-outs by reason
            opt_outs_by_reason = self.db.query(
                func.json_extract(UserEvent.event_data, '$.reason'),
                func.count(UserEvent.id)
            ).filter(
                and_(
                    UserEvent.event_type == 'meme_opt_out',
                    UserEvent.timestamp >= cutoff_date
                )
            ).group_by(func.json_extract(UserEvent.event_data, '$.reason')).all()
            
            # Daily opt-out trend
            daily_opt_outs = self.db.query(
                func.date(UserEvent.timestamp),
                func.count(UserEvent.id)
            ).filter(
                and_(
                    UserEvent.event_type == 'meme_opt_out',
                    UserEvent.timestamp >= cutoff_date
                )
            ).group_by(func.date(UserEvent.timestamp)).order_by(
                func.date(UserEvent.timestamp)
            ).all()
            
            return {
                'total_opt_outs': total_opt_outs,
                'opt_outs_by_source': dict(opt_outs_by_source),
                'opt_outs_by_reason': dict(opt_outs_by_reason),
                'daily_trend': [{'date': str(date), 'count': count} for date, count in daily_opt_outs],
                'period_days': days
            }
            
        except Exception as e:
            return {
                'error': str(e),
                'total_opt_outs': 0,
                'opt_outs_by_source': {},
                'opt_outs_by_reason': {},
                'daily_trend': [],
                'period_days': days
            }
    
    def get_meme_opt_in_analytics(self, days: int = 30) -> Dict[str, Any]:
        """Get analytics for meme opt-ins"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            # Total opt-ins in period
            total_opt_ins = self.db.query(func.count(UserEvent.id)).filter(
                and_(
                    UserEvent.event_type == 'meme_opt_in',
                    UserEvent.timestamp >= cutoff_date
                )
            ).scalar()
            
            # Opt-ins by source
            opt_ins_by_source = self.db.query(
                UserEvent.source,
                func.count(UserEvent.id)
            ).filter(
                and_(
                    UserEvent.event_type == 'meme_opt_in',
                    UserEvent.timestamp >= cutoff_date
                )
            ).group_by(UserEvent.source).all()
            
            # Categories selected on opt-in
            categories_selected = self.db.query(
                func.json_extract(UserEvent.event_data, '$.categories_selected'),
                func.count(UserEvent.id)
            ).filter(
                and_(
                    UserEvent.event_type == 'meme_opt_in',
                    UserEvent.timestamp >= cutoff_date
                )
            ).group_by(func.json_extract(UserEvent.event_data, '$.categories_selected')).all()
            
            # Daily opt-in trend
            daily_opt_ins = self.db.query(
                func.date(UserEvent.timestamp),
                func.count(UserEvent.id)
            ).filter(
                and_(
                    UserEvent.event_type == 'meme_opt_in',
                    UserEvent.timestamp >= cutoff_date
                )
            ).group_by(func.date(UserEvent.timestamp)).order_by(
                func.date(UserEvent.timestamp)
            ).all()
            
            return {
                'total_opt_ins': total_opt_ins,
                'opt_ins_by_source': dict(opt_ins_by_source),
                'categories_selected': dict(categories_selected),
                'daily_trend': [{'date': str(date), 'count': count} for date, count in daily_opt_ins],
                'period_days': days
            }
            
        except Exception as e:
            return {
                'error': str(e),
                'total_opt_ins': 0,
                'opt_ins_by_source': {},
                'categories_selected': {},
                'daily_trend': [],
                'period_days': days
            }
    
    def get_meme_engagement_analytics(self, days: int = 30) -> Dict[str, Any]:
        """Get comprehensive meme engagement analytics"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            # Total meme interactions
            total_interactions = self.db.query(func.count(UserEvent.id)).filter(
                and_(
                    UserEvent.event_type.in_(['meme_view', 'meme_like', 'meme_share', 'meme_skip']),
                    UserEvent.timestamp >= cutoff_date
                )
            ).scalar()
            
            # Interactions by type
            interactions_by_type = self.db.query(
                UserEvent.event_type,
                func.count(UserEvent.id)
            ).filter(
                and_(
                    UserEvent.event_type.in_(['meme_view', 'meme_like', 'meme_share', 'meme_skip']),
                    UserEvent.timestamp >= cutoff_date
                )
            ).group_by(UserEvent.event_type).all()
            
            # Unique users engaging with memes
            unique_users = self.db.query(func.count(func.distinct(UserEvent.user_id))).filter(
                and_(
                    UserEvent.event_type.in_(['meme_view', 'meme_like', 'meme_share', 'meme_skip', 'meme_opt_out', 'meme_opt_in']),
                    UserEvent.timestamp >= cutoff_date
                )
            ).scalar()
            
            # Conversion rate (opt-ins / opt-outs)
            opt_outs = self.db.query(func.count(UserEvent.id)).filter(
                and_(
                    UserEvent.event_type == 'meme_opt_out',
                    UserEvent.timestamp >= cutoff_date
                )
            ).scalar()
            
            opt_ins = self.db.query(func.count(UserEvent.id)).filter(
                and_(
                    UserEvent.event_type == 'meme_opt_in',
                    UserEvent.timestamp >= cutoff_date
                )
            ).scalar()
            
            conversion_rate = (opt_ins / opt_outs * 100) if opt_outs > 0 else 0
            
            return {
                'total_interactions': total_interactions,
                'interactions_by_type': dict(interactions_by_type),
                'unique_users': unique_users,
                'opt_outs': opt_outs,
                'opt_ins': opt_ins,
                'conversion_rate': round(conversion_rate, 2),
                'period_days': days
            }
            
        except Exception as e:
            return {
                'error': str(e),
                'total_interactions': 0,
                'interactions_by_type': {},
                'unique_users': 0,
                'opt_outs': 0,
                'opt_ins': 0,
                'conversion_rate': 0,
                'period_days': days
            }
    
    def get_user_demographics_analytics(self, event_type: str = 'meme_opt_out', days: int = 30) -> Dict[str, Any]:
        """Get analytics by user demographics"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            # Join with user profile data to get demographics
            results = self.db.query(
                User.age_group,
                User.income_level,
                User.education_level,
                func.count(UserEvent.id)
            ).join(UserEvent, User.id == UserEvent.user_id).filter(
                and_(
                    UserEvent.event_type == event_type,
                    UserEvent.timestamp >= cutoff_date
                )
            ).group_by(
                User.age_group,
                User.income_level,
                User.education_level
            ).all()
            
            # Organize by demographic
            demographics = {
                'age_groups': {},
                'income_levels': {},
                'education_levels': {}
            }
            
            for age_group, income_level, education_level, count in results:
                if age_group:
                    demographics['age_groups'][age_group] = demographics['age_groups'].get(age_group, 0) + count
                if income_level:
                    demographics['income_levels'][income_level] = demographics['income_levels'].get(income_level, 0) + count
                if education_level:
                    demographics['education_levels'][education_level] = demographics['education_levels'].get(education_level, 0) + count
            
            return demographics
            
        except Exception as e:
            return {
                'error': str(e),
                'age_groups': {},
                'income_levels': {},
                'education_levels': {}
            }
    
    def get_churn_correlation_analytics(self, days: int = 30) -> Dict[str, Any]:
        """Analyze correlation between meme opt-outs and overall app usage"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            # Users who opted out of memes
            opt_out_users = self.db.query(UserEvent.user_id).filter(
                and_(
                    UserEvent.event_type == 'meme_opt_out',
                    UserEvent.timestamp >= cutoff_date
                )
            ).distinct().subquery()
            
            # App usage after opt-out (login events, dashboard visits, etc.)
            post_opt_out_usage = self.db.query(
                func.count(UserEvent.id)
            ).filter(
                and_(
                    UserEvent.user_id.in_(opt_out_users),
                    UserEvent.event_type.in_(['user_login', 'dashboard_visit', 'transaction_view']),
                    UserEvent.timestamp >= cutoff_date
                )
            ).scalar()
            
            # Users who didn't opt out
            non_opt_out_users = self.db.query(UserEvent.user_id).filter(
                and_(
                    UserEvent.event_type.in_(['user_login', 'dashboard_visit']),
                    UserEvent.timestamp >= cutoff_date
                )
            ).distinct().subquery()
            
            # App usage for non-opt-out users
            non_opt_out_usage = self.db.query(
                func.count(UserEvent.id)
            ).filter(
                and_(
                    UserEvent.user_id.in_(non_opt_out_users),
                    UserEvent.event_type.in_(['user_login', 'dashboard_visit', 'transaction_view']),
                    UserEvent.timestamp >= cutoff_date
                )
            ).scalar()
            
            return {
                'opt_out_users_count': self.db.query(opt_out_users).count(),
                'non_opt_out_users_count': self.db.query(non_opt_out_users).count(),
                'post_opt_out_usage': post_opt_out_usage,
                'non_opt_out_usage': non_opt_out_usage,
                'usage_difference_percentage': round(
                    ((post_opt_out_usage - non_opt_out_usage) / non_opt_out_usage * 100) if non_opt_out_usage > 0 else 0, 
                    2
                ),
                'period_days': days
            }
            
        except Exception as e:
            return {
                'error': str(e),
                'opt_out_users_count': 0,
                'non_opt_out_users_count': 0,
                'post_opt_out_usage': 0,
                'non_opt_out_usage': 0,
                'usage_difference_percentage': 0,
                'period_days': days
            } 