"""
Data Persistence Layer for Income Comparison Calculator
Repository patterns and data access layer for all income comparison entities
"""

import logging
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, func, desc, asc
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from contextlib import contextmanager

from backend.models.income_comparison import (
    SalaryBenchmark, PredictionCache, LeadEngagementScore, SalaryPrediction,
    CareerPathRecommendation, LeadCaptureEvent, GamificationBadge, UserBadge,
    EmailSequence, EmailSend, IncomeComparisonAnalytics,
    ExperienceLevel, EducationLevel, IndustryType, BadgeType, EmailSequenceType
)
from backend.models import SessionLocal
from backend.services.monitoring_service import monitoring_service

logger = logging.getLogger(__name__)


class BaseRepository:
    """Base repository with common CRUD operations"""
    
    def __init__(self, model_class):
        self.model_class = model_class
    
    @contextmanager
    def get_session(self):
        """Get database session with automatic cleanup"""
        session = SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def create(self, data: Dict[str, Any]) -> Optional[Any]:
        """Create a new record"""
        try:
            with self.get_session() as session:
                record = self.model_class(**data)
                session.add(record)
                session.flush()
                session.refresh(record)
                return record
        except IntegrityError as e:
            logger.error(f"Integrity error creating {self.model_class.__name__}: {e}")
            return None
        except SQLAlchemyError as e:
            logger.error(f"Database error creating {self.model_class.__name__}: {e}")
            return None
    
    def get_by_id(self, record_id: int) -> Optional[Any]:
        """Get record by ID"""
        try:
            with self.get_session() as session:
                return session.query(self.model_class).filter(
                    self.model_class.id == record_id
                ).first()
        except SQLAlchemyError as e:
            logger.error(f"Database error getting {self.model_class.__name__} by ID: {e}")
            return None
    
    def update(self, record_id: int, data: Dict[str, Any]) -> Optional[Any]:
        """Update a record"""
        try:
            with self.get_session() as session:
                record = session.query(self.model_class).filter(
                    self.model_class.id == record_id
                ).first()
                if record:
                    for key, value in data.items():
                        if hasattr(record, key):
                            setattr(record, key, value)
                    session.flush()
                    session.refresh(record)
                    return record
                return None
        except SQLAlchemyError as e:
            logger.error(f"Database error updating {self.model_class.__name__}: {e}")
            return None
    
    def delete(self, record_id: int) -> bool:
        """Delete a record"""
        try:
            with self.get_session() as session:
                record = session.query(self.model_class).filter(
                    self.model_class.id == record_id
                ).first()
                if record:
                    session.delete(record)
                    return True
                return False
        except SQLAlchemyError as e:
            logger.error(f"Database error deleting {self.model_class.__name__}: {e}")
            return False
    
    def list_all(self, limit: int = 100, offset: int = 0) -> List[Any]:
        """List all records with pagination"""
        try:
            with self.get_session() as session:
                return session.query(self.model_class).limit(limit).offset(offset).all()
        except SQLAlchemyError as e:
            logger.error(f"Database error listing {self.model_class.__name__}: {e}")
            return []


class SalaryBenchmarkRepository(BaseRepository):
    """Repository for salary benchmark data"""
    
    def __init__(self):
        super().__init__(SalaryBenchmark)
    
    def get_benchmark(self, location: str, industry: IndustryType, 
                     experience_level: ExperienceLevel, 
                     education_level: EducationLevel,
                     job_title: Optional[str] = None) -> Optional[SalaryBenchmark]:
        """Get salary benchmark for specific criteria"""
        try:
            with self.get_session() as session:
                query = session.query(SalaryBenchmark).filter(
                    and_(
                        SalaryBenchmark.location == location,
                        SalaryBenchmark.industry == industry,
                        SalaryBenchmark.experience_level == experience_level,
                        SalaryBenchmark.education_level == education_level
                    )
                )
                
                if job_title:
                    query = query.filter(SalaryBenchmark.job_title == job_title)
                
                return query.first()
        except SQLAlchemyError as e:
            logger.error(f"Database error getting salary benchmark: {e}")
            return None
    
    def get_benchmarks_by_location(self, location: str) -> List[SalaryBenchmark]:
        """Get all benchmarks for a location"""
        try:
            with self.get_session() as session:
                return session.query(SalaryBenchmark).filter(
                    SalaryBenchmark.location == location
                ).all()
        except SQLAlchemyError as e:
            logger.error(f"Database error getting benchmarks by location: {e}")
            return []
    
    def get_benchmarks_by_industry(self, industry: IndustryType) -> List[SalaryBenchmark]:
        """Get all benchmarks for an industry"""
        try:
            with self.get_session() as session:
                return session.query(SalaryBenchmark).filter(
                    SalaryBenchmark.industry == industry
                ).all()
        except SQLAlchemyError as e:
            logger.error(f"Database error getting benchmarks by industry: {e}")
            return []
    
    def update_benchmark_data(self, location: str, industry: IndustryType,
                            experience_level: ExperienceLevel,
                            education_level: EducationLevel,
                            benchmark_data: Dict[str, Any]) -> Optional[SalaryBenchmark]:
        """Update or create benchmark data"""
        try:
            with self.get_session() as session:
                benchmark = session.query(SalaryBenchmark).filter(
                    and_(
                        SalaryBenchmark.location == location,
                        SalaryBenchmark.industry == industry,
                        SalaryBenchmark.experience_level == experience_level,
                        SalaryBenchmark.education_level == education_level
                    )
                ).first()
                
                if benchmark:
                    # Update existing benchmark
                    for key, value in benchmark_data.items():
                        if hasattr(benchmark, key):
                            setattr(benchmark, key, value)
                    benchmark.last_updated = datetime.now()
                else:
                    # Create new benchmark
                    benchmark_data.update({
                        'location': location,
                        'industry': industry,
                        'experience_level': experience_level,
                        'education_level': education_level,
                        'created_at': datetime.now(),
                        'last_updated': datetime.now()
                    })
                    benchmark = SalaryBenchmark(**benchmark_data)
                    session.add(benchmark)
                
                session.flush()
                session.refresh(benchmark)
                return benchmark
        except SQLAlchemyError as e:
            logger.error(f"Database error updating benchmark data: {e}")
            return None
    
    def get_outdated_benchmarks(self, days_old: int = 30) -> List[SalaryBenchmark]:
        """Get benchmarks that haven't been updated recently"""
        cutoff_date = datetime.now() - timedelta(days=days_old)
        try:
            with self.get_session() as session:
                return session.query(SalaryBenchmark).filter(
                    SalaryBenchmark.last_updated < cutoff_date
                ).all()
        except SQLAlchemyError as e:
            logger.error(f"Database error getting outdated benchmarks: {e}")
            return []


class PredictionCacheRepository(BaseRepository):
    """Repository for prediction cache data"""
    
    def __init__(self):
        super().__init__(PredictionCache)
    
    def get_cached_prediction(self, cache_key: str) -> Optional[PredictionCache]:
        """Get cached prediction by key"""
        try:
            with self.get_session() as session:
                cache_entry = session.query(PredictionCache).filter(
                    and_(
                        PredictionCache.cache_key == cache_key,
                        PredictionCache.expires_at > datetime.now()
                    )
                ).first()
                
                if cache_entry:
                    # Update hit count and last accessed
                    cache_entry.hit_count += 1
                    cache_entry.last_accessed = datetime.now()
                    session.flush()
                
                return cache_entry
        except SQLAlchemyError as e:
            logger.error(f"Database error getting cached prediction: {e}")
            return None
    
    def cache_prediction(self, cache_key: str, prediction_data: Dict[str, Any],
                        prediction_type: str, ttl_hours: int = 24) -> Optional[PredictionCache]:
        """Cache a prediction"""
        try:
            with self.get_session() as session:
                # Check if cache entry already exists
                existing = session.query(PredictionCache).filter(
                    PredictionCache.cache_key == cache_key
                ).first()
                
                expires_at = datetime.now() + timedelta(hours=ttl_hours)
                
                if existing:
                    # Update existing cache entry
                    existing.prediction_data = prediction_data
                    existing.expires_at = expires_at
                    existing.last_accessed = datetime.now()
                    session.flush()
                    session.refresh(existing)
                    return existing
                else:
                    # Create new cache entry
                    cache_entry = PredictionCache(
                        cache_key=cache_key,
                        prediction_data=prediction_data,
                        prediction_type=prediction_type,
                        expires_at=expires_at,
                        created_at=datetime.now(),
                        last_accessed=datetime.now()
                    )
                    session.add(cache_entry)
                    session.flush()
                    session.refresh(cache_entry)
                    return cache_entry
        except SQLAlchemyError as e:
            logger.error(f"Database error caching prediction: {e}")
            return None
    
    def cleanup_expired_cache(self) -> int:
        """Remove expired cache entries"""
        try:
            with self.get_session() as session:
                deleted_count = session.query(PredictionCache).filter(
                    PredictionCache.expires_at < datetime.now()
                ).delete()
                return deleted_count
        except SQLAlchemyError as e:
            logger.error(f"Database error cleaning up expired cache: {e}")
            return 0
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        try:
            with self.get_session() as session:
                total_entries = session.query(PredictionCache).count()
                expired_entries = session.query(PredictionCache).filter(
                    PredictionCache.expires_at < datetime.now()
                ).count()
                total_hits = session.query(func.sum(PredictionCache.hit_count)).scalar() or 0
                
                return {
                    'total_entries': total_entries,
                    'expired_entries': expired_entries,
                    'active_entries': total_entries - expired_entries,
                    'total_hits': total_hits,
                    'average_hits': total_hits / total_entries if total_entries > 0 else 0
                }
        except SQLAlchemyError as e:
            logger.error(f"Database error getting cache stats: {e}")
            return {}


class LeadEngagementRepository(BaseRepository):
    """Repository for lead engagement data"""
    
    def __init__(self):
        super().__init__(LeadEngagementScore)
    
    def get_lead_by_email(self, email: str) -> Optional[LeadEngagementScore]:
        """Get lead engagement by email"""
        try:
            with self.get_session() as session:
                return session.query(LeadEngagementScore).filter(
                    LeadEngagementScore.email == email
                ).first()
        except SQLAlchemyError as e:
            logger.error(f"Database error getting lead by email: {e}")
            return None
    
    def update_engagement_score(self, lead_id: str, engagement_data: Dict[str, Any]) -> Optional[LeadEngagementScore]:
        """Update lead engagement score"""
        try:
            with self.get_session() as session:
                lead = session.query(LeadEngagementScore).filter(
                    LeadEngagementScore.lead_id == lead_id
                ).first()
                
                if lead:
                    # Update engagement metrics
                    if 'interaction_count' in engagement_data:
                        lead.interaction_count += engagement_data['interaction_count']
                    
                    if 'time_spent_seconds' in engagement_data:
                        lead.time_spent_seconds += engagement_data['time_spent_seconds']
                    
                    if 'pages_visited' in engagement_data:
                        current_pages = lead.pages_visited or []
                        new_pages = engagement_data['pages_visited']
                        lead.pages_visited = list(set(current_pages + new_pages))
                    
                    if 'features_used' in engagement_data:
                        current_features = lead.features_used or []
                        new_features = engagement_data['features_used']
                        lead.features_used = list(set(current_features + new_features))
                    
                    lead.last_interaction = datetime.now()
                    lead.updated_at = datetime.now()
                    
                    # Recalculate engagement score
                    lead.engagement_score = self._calculate_engagement_score(lead)
                    
                    session.flush()
                    session.refresh(lead)
                    return lead
                
                return None
        except SQLAlchemyError as e:
            logger.error(f"Database error updating engagement score: {e}")
            return None
    
    def _calculate_engagement_score(self, lead: LeadEngagementScore) -> float:
        """Calculate engagement score based on various metrics"""
        score = 0.0
        
        # Base score for having an email
        score += 10.0
        
        # Interaction count (max 30 points)
        score += min(lead.interaction_count * 2, 30.0)
        
        # Time spent (max 20 points)
        score += min(lead.time_spent_seconds / 60, 20.0)  # 1 point per minute, max 20
        
        # Pages visited (max 20 points)
        if lead.pages_visited:
            score += min(len(lead.pages_visited) * 2, 20.0)
        
        # Features used (max 20 points)
        if lead.features_used:
            score += min(len(lead.features_used) * 4, 20.0)
        
        return min(score, 100.0)
    
    def get_high_engagement_leads(self, min_score: float = 50.0, limit: int = 100) -> List[LeadEngagementScore]:
        """Get leads with high engagement scores"""
        try:
            with self.get_session() as session:
                return session.query(LeadEngagementScore).filter(
                    LeadEngagementScore.engagement_score >= min_score
                ).order_by(desc(LeadEngagementScore.engagement_score)).limit(limit).all()
        except SQLAlchemyError as e:
            logger.error(f"Database error getting high engagement leads: {e}")
            return []
    
    def get_leads_by_conversion_stage(self, stage: str) -> List[LeadEngagementScore]:
        """Get leads by conversion stage"""
        try:
            with self.get_session() as session:
                return session.query(LeadEngagementScore).filter(
                    LeadEngagementScore.conversion_stage == stage
                ).all()
        except SQLAlchemyError as e:
            logger.error(f"Database error getting leads by conversion stage: {e}")
            return []


class SalaryPredictionRepository(BaseRepository):
    """Repository for salary predictions"""
    
    def __init__(self):
        super().__init__(SalaryPrediction)
    
    def get_predictions_by_user(self, user_id: str, limit: int = 10) -> List[SalaryPrediction]:
        """Get predictions for a specific user"""
        try:
            with self.get_session() as session:
                return session.query(SalaryPrediction).filter(
                    SalaryPrediction.user_id == user_id
                ).order_by(desc(SalaryPrediction.created_at)).limit(limit).all()
        except SQLAlchemyError as e:
            logger.error(f"Database error getting predictions by user: {e}")
            return []
    
    def get_predictions_by_session(self, session_id: str) -> List[SalaryPrediction]:
        """Get predictions for a specific session"""
        try:
            with self.get_session() as session:
                return session.query(SalaryPrediction).filter(
                    SalaryPrediction.session_id == session_id
                ).order_by(desc(SalaryPrediction.created_at)).all()
        except SQLAlchemyError as e:
            logger.error(f"Database error getting predictions by session: {e}")
            return []
    
    def get_predictions_by_location(self, location: str, limit: int = 100) -> List[SalaryPrediction]:
        """Get predictions for a specific location"""
        try:
            with self.get_session() as session:
                return session.query(SalaryPrediction).filter(
                    SalaryPrediction.location == location
                ).order_by(desc(SalaryPrediction.created_at)).limit(limit).all()
        except SQLAlchemyError as e:
            logger.error(f"Database error getting predictions by location: {e}")
            return []
    
    def get_predictions_by_industry(self, industry: IndustryType, limit: int = 100) -> List[SalaryPrediction]:
        """Get predictions for a specific industry"""
        try:
            with self.get_session() as session:
                return session.query(SalaryPrediction).filter(
                    SalaryPrediction.industry == industry
                ).order_by(desc(SalaryPrediction.created_at)).limit(limit).all()
        except SQLAlchemyError as e:
            logger.error(f"Database error getting predictions by industry: {e}")
            return []
    
    def create_prediction_with_recommendations(self, prediction_data: Dict[str, Any],
                                             recommendations: List[Dict[str, Any]]) -> Optional[SalaryPrediction]:
        """Create a salary prediction with career recommendations"""
        try:
            with self.get_session() as session:
                # Create the prediction
                prediction = SalaryPrediction(**prediction_data)
                session.add(prediction)
                session.flush()
                session.refresh(prediction)
                
                # Create career recommendations
                for rec_data in recommendations:
                    rec_data['salary_prediction_id'] = prediction.id
                    recommendation = CareerPathRecommendation(**rec_data)
                    session.add(recommendation)
                
                session.flush()
                return prediction
        except SQLAlchemyError as e:
            logger.error(f"Database error creating prediction with recommendations: {e}")
            return None


class LeadCaptureRepository(BaseRepository):
    """Repository for lead capture events"""
    
    def __init__(self):
        super().__init__(LeadCaptureEvent)
    
    def get_leads_by_email(self, email: str) -> List[LeadCaptureEvent]:
        """Get all lead events for an email"""
        try:
            with self.get_session() as session:
                return session.query(LeadCaptureEvent).filter(
                    LeadCaptureEvent.email == email
                ).order_by(desc(LeadCaptureEvent.created_at)).all()
        except SQLAlchemyError as e:
            logger.error(f"Database error getting leads by email: {e}")
            return []
    
    def get_converted_leads(self, limit: int = 100) -> List[LeadCaptureEvent]:
        """Get all converted leads"""
        try:
            with self.get_session() as session:
                return session.query(LeadCaptureEvent).filter(
                    LeadCaptureEvent.converted == True
                ).order_by(desc(LeadCaptureEvent.conversion_date)).limit(limit).all()
        except SQLAlchemyError as e:
            logger.error(f"Database error getting converted leads: {e}")
            return []
    
    def update_conversion_status(self, lead_id: int, converted: bool, 
                               conversion_value: Optional[float] = None) -> Optional[LeadCaptureEvent]:
        """Update lead conversion status"""
        try:
            with self.get_session() as session:
                lead = session.query(LeadCaptureEvent).filter(
                    LeadCaptureEvent.id == lead_id
                ).first()
                
                if lead:
                    lead.converted = converted
                    if converted:
                        lead.conversion_date = datetime.now()
                        if conversion_value:
                            lead.conversion_value = conversion_value
                    
                    lead.updated_at = datetime.now()
                    session.flush()
                    session.refresh(lead)
                    return lead
                
                return None
        except SQLAlchemyError as e:
            logger.error(f"Database error updating conversion status: {e}")
            return None
    
    def get_conversion_analytics(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Get conversion analytics for a date range"""
        try:
            with self.get_session() as session:
                total_leads = session.query(LeadCaptureEvent).filter(
                    and_(
                        LeadCaptureEvent.created_at >= start_date,
                        LeadCaptureEvent.created_at <= end_date
                    )
                ).count()
                
                converted_leads = session.query(LeadCaptureEvent).filter(
                    and_(
                        LeadCaptureEvent.created_at >= start_date,
                        LeadCaptureEvent.created_at <= end_date,
                        LeadCaptureEvent.converted == True
                    )
                ).count()
                
                total_value = session.query(func.sum(LeadCaptureEvent.conversion_value)).filter(
                    and_(
                        LeadCaptureEvent.created_at >= start_date,
                        LeadCaptureEvent.created_at <= end_date,
                        LeadCaptureEvent.converted == True
                    )
                ).scalar() or 0.0
                
                return {
                    'total_leads': total_leads,
                    'converted_leads': converted_leads,
                    'conversion_rate': (converted_leads / total_leads * 100) if total_leads > 0 else 0,
                    'total_value': total_value,
                    'average_value': (total_value / converted_leads) if converted_leads > 0 else 0
                }
        except SQLAlchemyError as e:
            logger.error(f"Database error getting conversion analytics: {e}")
            return {}


class GamificationRepository(BaseRepository):
    """Repository for gamification data"""
    
    def __init__(self):
        super().__init__(GamificationBadge)
    
    def get_badges_by_type(self, badge_type: BadgeType) -> List[GamificationBadge]:
        """Get badges by type"""
        try:
            with self.get_session() as session:
                return session.query(GamificationBadge).filter(
                    GamificationBadge.badge_type == badge_type
                ).all()
        except SQLAlchemyError as e:
            logger.error(f"Database error getting badges by type: {e}")
            return []
    
    def get_badges_by_rarity(self, rarity: str) -> List[GamificationBadge]:
        """Get badges by rarity"""
        try:
            with self.get_session() as session:
                return session.query(GamificationBadge).filter(
                    GamificationBadge.rarity == rarity
                ).all()
        except SQLAlchemyError as e:
            logger.error(f"Database error getting badges by rarity: {e}")
            return []
    
    def assign_badge_to_user(self, session_id: str, badge_id: int, 
                           user_id: Optional[str] = None,
                           unlock_context: Optional[Dict[str, Any]] = None) -> Optional[UserBadge]:
        """Assign a badge to a user"""
        try:
            with self.get_session() as session:
                # Check if user already has this badge
                existing_badge = session.query(UserBadge).filter(
                    and_(
                        UserBadge.session_id == session_id,
                        UserBadge.badge_id == badge_id
                    )
                ).first()
                
                if existing_badge:
                    return existing_badge
                
                # Create new badge assignment
                badge_assignment = UserBadge(
                    user_id=user_id,
                    session_id=session_id,
                    badge_id=badge_id,
                    unlock_context=unlock_context,
                    unlocked_at=datetime.now(),
                    created_at=datetime.now()
                )
                
                session.add(badge_assignment)
                session.flush()
                session.refresh(badge_assignment)
                return badge_assignment
        except SQLAlchemyError as e:
            logger.error(f"Database error assigning badge: {e}")
            return None
    
    def get_user_badges(self, session_id: str) -> List[UserBadge]:
        """Get all badges for a user session"""
        try:
            with self.get_session() as session:
                return session.query(UserBadge).options(
                    joinedload(UserBadge.badge)
                ).filter(
                    UserBadge.session_id == session_id
                ).all()
        except SQLAlchemyError as e:
            logger.error(f"Database error getting user badges: {e}")
            return []


class EmailSequenceRepository(BaseRepository):
    """Repository for email sequences"""
    
    def __init__(self):
        super().__init__(EmailSequence)
    
    def get_active_sequences(self) -> List[EmailSequence]:
        """Get all active email sequences"""
        try:
            with self.get_session() as session:
                return session.query(EmailSequence).filter(
                    EmailSequence.is_active == True
                ).order_by(EmailSequence.priority).all()
        except SQLAlchemyError as e:
            logger.error(f"Database error getting active sequences: {e}")
            return []
    
    def get_sequences_by_trigger(self, trigger_event: str) -> List[EmailSequence]:
        """Get sequences by trigger event"""
        try:
            with self.get_session() as session:
                return session.query(EmailSequence).filter(
                    and_(
                        EmailSequence.trigger_event == trigger_event,
                        EmailSequence.is_active == True
                    )
                ).order_by(EmailSequence.priority).all()
        except SQLAlchemyError as e:
            logger.error(f"Database error getting sequences by trigger: {e}")
            return []
    
    def track_email_send(self, sequence_id: int, lead_id: str, recipient_email: str,
                        subject_line: str, email_content: str) -> Optional[EmailSend]:
        """Track an email send"""
        try:
            with self.get_session() as session:
                email_send = EmailSend(
                    sequence_id=sequence_id,
                    lead_id=lead_id,
                    recipient_email=recipient_email,
                    subject_line=subject_line,
                    email_content=email_content,
                    sent_at=datetime.now(),
                    created_at=datetime.now()
                )
                
                session.add(email_send)
                session.flush()
                session.refresh(email_send)
                return email_send
        except SQLAlchemyError as e:
            logger.error(f"Database error tracking email send: {e}")
            return None
    
    def update_email_engagement(self, email_send_id: int, engagement_data: Dict[str, Any]) -> Optional[EmailSend]:
        """Update email engagement metrics"""
        try:
            with self.get_session() as session:
                email_send = session.query(EmailSend).filter(
                    EmailSend.id == email_send_id
                ).first()
                
                if email_send:
                    if 'opened' in engagement_data:
                        email_send.opened = engagement_data['opened']
                        if engagement_data['opened']:
                            email_send.opened_at = datetime.now()
                    
                    if 'clicked' in engagement_data:
                        email_send.clicked = engagement_data['clicked']
                        if engagement_data['clicked']:
                            email_send.clicked_at = datetime.now()
                    
                    if 'open_count' in engagement_data:
                        email_send.open_count = engagement_data['open_count']
                    
                    if 'click_count' in engagement_data:
                        email_send.click_count = engagement_data['click_count']
                    
                    session.flush()
                    session.refresh(email_send)
                    return email_send
                
                return None
        except SQLAlchemyError as e:
            logger.error(f"Database error updating email engagement: {e}")
            return None


class AnalyticsRepository(BaseRepository):
    """Repository for analytics data"""
    
    def __init__(self):
        super().__init__(IncomeComparisonAnalytics)
    
    def get_daily_analytics(self, date: datetime) -> Optional[IncomeComparisonAnalytics]:
        """Get analytics for a specific date"""
        try:
            with self.get_session() as session:
                return session.query(IncomeComparisonAnalytics).filter(
                    func.date(IncomeComparisonAnalytics.date) == func.date(date)
                ).first()
        except SQLAlchemyError as e:
            logger.error(f"Database error getting daily analytics: {e}")
            return None
    
    def update_daily_analytics(self, date: datetime, analytics_data: Dict[str, Any]) -> Optional[IncomeComparisonAnalytics]:
        """Update or create daily analytics"""
        try:
            with self.get_session() as session:
                analytics = session.query(IncomeComparisonAnalytics).filter(
                    func.date(IncomeComparisonAnalytics.date) == func.date(date)
                ).first()
                
                if analytics:
                    # Update existing analytics
                    for key, value in analytics_data.items():
                        if hasattr(analytics, key):
                            setattr(analytics, key, value)
                    analytics.updated_at = datetime.now()
                else:
                    # Create new analytics
                    analytics_data['date'] = date
                    analytics_data['created_at'] = datetime.now()
                    analytics_data['updated_at'] = datetime.now()
                    analytics = IncomeComparisonAnalytics(**analytics_data)
                    session.add(analytics)
                
                session.flush()
                session.refresh(analytics)
                return analytics
        except SQLAlchemyError as e:
            logger.error(f"Database error updating daily analytics: {e}")
            return None
    
    def get_analytics_range(self, start_date: datetime, end_date: datetime) -> List[IncomeComparisonAnalytics]:
        """Get analytics for a date range"""
        try:
            with self.get_session() as session:
                return session.query(IncomeComparisonAnalytics).filter(
                    and_(
                        IncomeComparisonAnalytics.date >= start_date,
                        IncomeComparisonAnalytics.date <= end_date
                    )
                ).order_by(IncomeComparisonAnalytics.date).all()
        except SQLAlchemyError as e:
            logger.error(f"Database error getting analytics range: {e}")
            return []


# Repository instances
salary_benchmark_repo = SalaryBenchmarkRepository()
prediction_cache_repo = PredictionCacheRepository()
lead_engagement_repo = LeadEngagementRepository()
salary_prediction_repo = SalaryPredictionRepository()
lead_capture_repo = LeadCaptureRepository()
gamification_repo = GamificationRepository()
email_sequence_repo = EmailSequenceRepository()
analytics_repo = AnalyticsRepository()

# Export repositories
__all__ = [
    'BaseRepository',
    'SalaryBenchmarkRepository',
    'PredictionCacheRepository',
    'LeadEngagementRepository',
    'SalaryPredictionRepository',
    'LeadCaptureRepository',
    'GamificationRepository',
    'EmailSequenceRepository',
    'AnalyticsRepository',
    'salary_benchmark_repo',
    'prediction_cache_repo',
    'lead_engagement_repo',
    'salary_prediction_repo',
    'lead_capture_repo',
    'gamification_repo',
    'email_sequence_repo',
    'analytics_repo'
] 