"""
Assessment Analytics Service

Comprehensive analytics tracking for assessment system and landing page:
- Event tracking and aggregation
- Conversion funnel analysis
- Lead quality scoring
- Real-time metrics
- Performance monitoring
- Geographic analytics
"""

import json
import time
import uuid
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional, Union, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
from collections import defaultdict, Counter
import geoip2.database
import geoip2.errors
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func, text, case, cast, Float, Integer
from sqlalchemy.exc import SQLAlchemyError

from ..models.assessment_analytics_models import (
    AssessmentAnalyticsEvent, AssessmentSession, ConversionFunnel,
    LeadQualityMetrics, RealTimeMetrics, PerformanceMetrics, GeographicAnalytics,
    AnalyticsEventType, ConversionStage, LeadQualityScore
)
from ..models.assessment_models import Assessment, UserAssessment
from ..models.user import User
from ..utils.encryption import encrypt_data, decrypt_data
from ..config.base import Config

logger = logging.getLogger(__name__)

@dataclass
class AnalyticsEvent:
    """Analytics event data structure"""
    event_type: AnalyticsEventType
    session_id: str
    user_id: Optional[str] = None
    assessment_id: Optional[str] = None
    assessment_type: Optional[str] = None
    properties: Dict[str, Any] = None
    source: str = 'web'
    user_agent: Optional[str] = None
    ip_address: Optional[str] = None
    referrer: Optional[str] = None
    utm_source: Optional[str] = None
    utm_medium: Optional[str] = None
    utm_campaign: Optional[str] = None
    utm_term: Optional[str] = None
    utm_content: Optional[str] = None
    page_load_time: Optional[float] = None
    time_on_page: Optional[float] = None

@dataclass
class ConversionFunnelData:
    """Conversion funnel data structure"""
    session_id: str
    assessment_type: str
    current_stage: ConversionStage
    landing_viewed_at: Optional[datetime] = None
    assessment_started_at: Optional[datetime] = None
    assessment_completed_at: Optional[datetime] = None
    email_captured_at: Optional[datetime] = None
    conversion_modal_opened_at: Optional[datetime] = None
    payment_attempted_at: Optional[datetime] = None
    payment_successful_at: Optional[datetime] = None
    dropped_off_at: Optional[str] = None
    conversion_value: Optional[float] = None
    lead_quality_score: Optional[str] = None
    risk_level: Optional[str] = None
    assessment_score: Optional[int] = None

@dataclass
class LeadQualityData:
    """Lead quality data structure"""
    session_id: str
    assessment_type: str
    assessment_score: Optional[int] = None
    risk_level: Optional[str] = None
    completion_time_seconds: Optional[int] = None
    questions_answered: Optional[int] = None
    time_spent_on_assessment: Optional[int] = None
    assessment_abandoned: bool = False
    assessment_resumed: bool = False
    assessment_shared: bool = False
    email_captured: bool = False
    conversion_modal_opened: bool = False
    payment_attempted: bool = False
    converted: bool = False

class AssessmentAnalyticsService:
    """Comprehensive analytics service for assessment system"""
    
    def __init__(self, db_session: Session, config: Config):
        self.db = db_session
        self.config = config
        self.geoip_reader = None
        
        # Initialize GeoIP database if available
        try:
            self.geoip_reader = geoip2.database.Reader('GeoLite2-City.mmdb')
        except Exception as e:
            logger.warning(f"GeoIP database not available: {e}")
        
        # Analytics configuration
        self.analytics_config = {
            'enabled': True,
            'batch_size': 100,
            'flush_interval_seconds': 60,
            'max_retry_attempts': 3,
            'privacy_mode': True,  # Anonymize PII
            'retention_days': 365,
            'real_time_updates': True
        }
    
    def track_event(self, event: AnalyticsEvent) -> bool:
        """Track an analytics event"""
        try:
            # Extract device and location data
            device_data = self._extract_device_data(event.user_agent)
            location_data = self._get_location_data(event.ip_address)
            
            # Create analytics event record
            analytics_event = AssessmentAnalyticsEvent(
                event_type=event.event_type.value,
                session_id=event.session_id,
                user_id=event.user_id,
                assessment_id=event.assessment_id,
                assessment_type=event.assessment_type,
                properties=event.properties or {},
                source=event.source,
                user_agent=event.user_agent,
                ip_address=event.ip_address,
                referrer=event.referrer,
                utm_source=event.utm_source,
                utm_medium=event.utm_medium,
                utm_campaign=event.utm_campaign,
                utm_term=event.utm_term,
                utm_content=event.utm_content,
                device_type=device_data.get('device_type'),
                browser=device_data.get('browser'),
                os=device_data.get('os'),
                country=location_data.get('country'),
                region=location_data.get('region'),
                city=location_data.get('city'),
                page_load_time=event.page_load_time,
                time_on_page=event.time_on_page
            )
            
            self.db.add(analytics_event)
            self.db.commit()
            
            # Update real-time metrics
            self._update_real_time_metrics(event)
            
            # Update conversion funnel
            self._update_conversion_funnel(event)
            
            # Update geographic analytics
            if location_data.get('country'):
                self._update_geographic_analytics(event, location_data)
            
            logger.info(f"Tracked event: {event.event_type.value} for session {event.session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error tracking event: {e}")
            self.db.rollback()
            return False
    
    def get_conversion_funnel(self, assessment_type: Optional[str] = None, 
                            days: int = 30) -> Dict[str, Any]:
        """Get conversion funnel analysis"""
        try:
            start_date = datetime.now(timezone.utc) - timedelta(days=days)
            
            query = self.db.query(ConversionFunnel).filter(
                ConversionFunnel.created_at >= start_date
            )
            
            if assessment_type:
                query = query.filter(ConversionFunnel.assessment_type == assessment_type)
            
            funnels = query.all()
            
            # Calculate funnel metrics
            total_sessions = len(funnels)
            stage_counts = defaultdict(int)
            drop_off_counts = defaultdict(int)
            
            for funnel in funnels:
                stage_counts[funnel.current_stage] += 1
                if funnel.dropped_off_at:
                    drop_off_counts[funnel.dropped_off_at] += 1
            
            # Calculate conversion rates
            conversion_rates = {}
            stages = [
                ConversionStage.LANDING_VIEW,
                ConversionStage.ASSESSMENT_START,
                ConversionStage.ASSESSMENT_COMPLETE,
                ConversionStage.EMAIL_CAPTURE,
                ConversionStage.CONVERSION_MODAL,
                ConversionStage.PAYMENT_ATTEMPT,
                ConversionStage.PAYMENT_SUCCESS
            ]
            
            previous_count = total_sessions
            for stage in stages:
                current_count = stage_counts.get(stage.value, 0)
                conversion_rates[stage.value] = {
                    'count': current_count,
                    'rate': (current_count / previous_count * 100) if previous_count > 0 else 0,
                    'drop_off': drop_off_counts.get(stage.value, 0)
                }
                previous_count = current_count
            
            return {
                'total_sessions': total_sessions,
                'conversion_rates': conversion_rates,
                'drop_off_analysis': dict(drop_off_counts),
                'time_period_days': days,
                'assessment_type': assessment_type
            }
            
        except Exception as e:
            logger.error(f"Error getting conversion funnel: {e}")
            return {}
    
    def get_lead_quality_metrics(self, assessment_type: Optional[str] = None,
                                days: int = 30) -> Dict[str, Any]:
        """Get lead quality metrics and scoring"""
        try:
            start_date = datetime.now(timezone.utc) - timedelta(days=days)
            
            query = self.db.query(LeadQualityMetrics).filter(
                LeadQualityMetrics.created_at >= start_date
            )
            
            if assessment_type:
                query = query.filter(LeadQualityMetrics.assessment_type == assessment_type)
            
            leads = query.all()
            
            # Calculate lead quality distribution
            quality_distribution = Counter(lead.lead_quality_score for lead in leads)
            
            # Calculate conversion rates by quality
            conversion_by_quality = defaultdict(lambda: {'total': 0, 'converted': 0})
            for lead in leads:
                conversion_by_quality[lead.lead_quality_score]['total'] += 1
                if lead.converted:
                    conversion_by_quality[lead.lead_quality_score]['converted'] += 1
            
            # Calculate average metrics
            avg_score = sum(lead.assessment_score or 0 for lead in leads) / len(leads) if leads else 0
            avg_completion_time = sum(lead.completion_time_seconds or 0 for lead in leads) / len(leads) if leads else 0
            
            return {
                'total_leads': len(leads),
                'quality_distribution': dict(quality_distribution),
                'conversion_by_quality': dict(conversion_by_quality),
                'average_score': avg_score,
                'average_completion_time': avg_completion_time,
                'time_period_days': days,
                'assessment_type': assessment_type
            }
            
        except Exception as e:
            logger.error(f"Error getting lead quality metrics: {e}")
            return {}
    
    def get_real_time_metrics(self) -> Dict[str, Any]:
        """Get real-time metrics for dashboard"""
        try:
            # Get current period (last 24 hours)
            now = datetime.now(timezone.utc)
            period_start = now - timedelta(hours=24)
            
            # Get real-time metrics
            metrics = self.db.query(RealTimeMetrics).filter(
                RealTimeMetrics.period_start >= period_start
            ).all()
            
            real_time_data = {}
            for metric in metrics:
                real_time_data[metric.metric_type] = {
                    'value': metric.value,
                    'previous_value': metric.previous_value,
                    'change_percentage': metric.change_percentage,
                    'last_updated': metric.last_updated.isoformat()
                }
            
            return {
                'real_time_metrics': real_time_data,
                'period_start': period_start.isoformat(),
                'period_end': now.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting real-time metrics: {e}")
            return {}
    
    def get_performance_metrics(self, days: int = 7) -> Dict[str, Any]:
        """Get performance monitoring metrics"""
        try:
            start_date = datetime.now(timezone.utc) - timedelta(days=days)
            
            # Get performance metrics
            performance_data = self.db.query(PerformanceMetrics).filter(
                PerformanceMetrics.timestamp >= start_date
            ).all()
            
            # Aggregate by metric type
            metrics_by_type = defaultdict(list)
            for metric in performance_data:
                metrics_by_type[metric.metric_type].append(metric)
            
            # Calculate averages and trends
            performance_summary = {}
            for metric_type, metrics in metrics_by_type.items():
                if metric_type == 'page_load_time':
                    avg_load_time = sum(m.page_load_time or 0 for m in metrics) / len(metrics)
                    performance_summary[metric_type] = {
                        'average_ms': avg_load_time,
                        'count': len(metrics)
                    }
                elif metric_type == 'api_response_time':
                    avg_response_time = sum(m.api_response_time or 0 for m in metrics) / len(metrics)
                    performance_summary[metric_type] = {
                        'average_ms': avg_response_time,
                        'count': len(metrics)
                    }
                elif metric_type == 'error_rate':
                    avg_error_rate = sum(m.error_rate or 0 for m in metrics) / len(metrics)
                    performance_summary[metric_type] = {
                        'average_percentage': avg_error_rate,
                        'count': len(metrics)
                    }
            
            return {
                'performance_metrics': performance_summary,
                'time_period_days': days,
                'total_metrics': len(performance_data)
            }
            
        except Exception as e:
            logger.error(f"Error getting performance metrics: {e}")
            return {}
    
    def get_geographic_analytics(self, days: int = 30) -> Dict[str, Any]:
        """Get geographic distribution analytics"""
        try:
            start_date = datetime.now(timezone.utc) - timedelta(days=days)
            
            # Get geographic analytics
            geo_data = self.db.query(GeographicAnalytics).filter(
                GeographicAnalytics.date >= start_date
            ).all()
            
            # Aggregate by country
            country_data = defaultdict(lambda: {
                'total_sessions': 0,
                'completed_assessments': 0,
                'conversion_rate': 0,
                'average_score': 0,
                'average_completion_time': 0,
                'average_page_load_time': 0,
                'error_rate': 0
            })
            
            for geo in geo_data:
                country_data[geo.country]['total_sessions'] += geo.total_sessions
                country_data[geo.country]['completed_assessments'] += geo.completed_assessments
                country_data[geo.country]['average_score'] += geo.average_score or 0
                country_data[geo.country]['average_completion_time'] += geo.average_completion_time or 0
                country_data[geo.country]['average_page_load_time'] += geo.average_page_load_time or 0
                country_data[geo.country]['error_rate'] += geo.error_rate or 0
            
            # Calculate averages
            for country, data in country_data.items():
                if data['total_sessions'] > 0:
                    data['conversion_rate'] = (data['completed_assessments'] / data['total_sessions']) * 100
                    data['average_score'] /= data['total_sessions']
                    data['average_completion_time'] /= data['total_sessions']
                    data['average_page_load_time'] /= data['total_sessions']
                    data['error_rate'] /= data['total_sessions']
            
            return {
                'geographic_data': dict(country_data),
                'time_period_days': days,
                'total_countries': len(country_data)
            }
            
        except Exception as e:
            logger.error(f"Error getting geographic analytics: {e}")
            return {}
    
    def calculate_lead_quality_score(self, lead_data: LeadQualityData) -> str:
        """Calculate lead quality score based on behavioral signals"""
        try:
            score = 0
            
            # Assessment completion (40% weight)
            if lead_data.assessment_score is not None:
                score += (lead_data.assessment_score / 100) * 40
            
            # Engagement signals (30% weight)
            if lead_data.time_spent_on_assessment and lead_data.time_spent_on_assessment > 300:  # 5+ minutes
                score += 15
            if lead_data.questions_answered and lead_data.questions_answered > 10:
                score += 15
            
            # Conversion signals (20% weight)
            if lead_data.email_captured:
                score += 10
            if lead_data.conversion_modal_opened:
                score += 10
            
            # Behavioral signals (10% weight)
            if lead_data.assessment_shared:
                score += 5
            if not lead_data.assessment_abandoned:
                score += 5
            
            # Determine quality level
            if score >= 80:
                return LeadQualityScore.HOT.value
            elif score >= 60:
                return LeadQualityScore.WARM.value
            elif score >= 40:
                return LeadQualityScore.COLD.value
            else:
                return LeadQualityScore.UNQUALIFIED.value
                
        except Exception as e:
            logger.error(f"Error calculating lead quality score: {e}")
            return LeadQualityScore.COLD.value
    
    def _extract_device_data(self, user_agent: Optional[str]) -> Dict[str, str]:
        """Extract device information from user agent"""
        if not user_agent:
            return {}
        
        try:
            # Simple device detection (can be enhanced with user-agent-parser library)
            user_agent_lower = user_agent.lower()
            
            device_type = 'desktop'
            if 'mobile' in user_agent_lower:
                device_type = 'mobile'
            elif 'tablet' in user_agent_lower or 'ipad' in user_agent_lower:
                device_type = 'tablet'
            
            browser = 'unknown'
            if 'chrome' in user_agent_lower:
                browser = 'chrome'
            elif 'firefox' in user_agent_lower:
                browser = 'firefox'
            elif 'safari' in user_agent_lower:
                browser = 'safari'
            elif 'edge' in user_agent_lower:
                browser = 'edge'
            
            os = 'unknown'
            if 'windows' in user_agent_lower:
                os = 'windows'
            elif 'mac' in user_agent_lower:
                os = 'macos'
            elif 'linux' in user_agent_lower:
                os = 'linux'
            elif 'android' in user_agent_lower:
                os = 'android'
            elif 'ios' in user_agent_lower:
                os = 'ios'
            
            return {
                'device_type': device_type,
                'browser': browser,
                'os': os
            }
            
        except Exception as e:
            logger.error(f"Error extracting device data: {e}")
            return {}
    
    def _get_location_data(self, ip_address: Optional[str]) -> Dict[str, str]:
        """Get location data from IP address"""
        if not ip_address or not self.geoip_reader:
            return {}
        
        try:
            response = self.geoip_reader.city(ip_address)
            return {
                'country': response.country.iso_code,
                'region': response.subdivisions.most_specific.name if response.subdivisions.most_specific else None,
                'city': response.city.name
            }
        except geoip2.errors.AddressNotFoundError:
            return {}
        except Exception as e:
            logger.error(f"Error getting location data: {e}")
            return {}
    
    def _update_real_time_metrics(self, event: AnalyticsEvent):
        """Update real-time metrics"""
        try:
            now = datetime.now(timezone.utc)
            period_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            period_end = period_start + timedelta(days=1)
            
            # Update assessment completion counter
            if event.event_type == AnalyticsEventType.ASSESSMENT_COMPLETED:
                metric = self.db.query(RealTimeMetrics).filter(
                    RealTimeMetrics.metric_type == 'assessments_completed_today',
                    RealTimeMetrics.period_start == period_start
                ).first()
                
                if metric:
                    metric.value += 1
                    metric.last_updated = now
                else:
                    metric = RealTimeMetrics(
                        metric_type='assessments_completed_today',
                        assessment_type=event.assessment_type,
                        value=1,
                        period_start=period_start,
                        period_end=period_end
                    )
                    self.db.add(metric)
                
                self.db.commit()
                
        except Exception as e:
            logger.error(f"Error updating real-time metrics: {e}")
    
    def _update_conversion_funnel(self, event: AnalyticsEvent):
        """Update conversion funnel tracking"""
        try:
            # Get or create funnel record
            funnel = self.db.query(ConversionFunnel).filter(
                ConversionFunnel.session_id == event.session_id,
                ConversionFunnel.assessment_type == event.assessment_type
            ).first()
            
            if not funnel:
                funnel = ConversionFunnel(
                    session_id=event.session_id,
                    assessment_type=event.assessment_type,
                    current_stage=ConversionStage.LANDING_VIEW.value
                )
                self.db.add(funnel)
            
            # Update funnel based on event type
            now = datetime.now(timezone.utc)
            
            if event.event_type == AnalyticsEventType.ASSESSMENT_LANDING_VIEWED:
                funnel.landing_viewed_at = now
                funnel.current_stage = ConversionStage.LANDING_VIEW.value
                
            elif event.event_type == AnalyticsEventType.ASSESSMENT_STARTED:
                funnel.assessment_started_at = now
                funnel.current_stage = ConversionStage.ASSESSMENT_START.value
                if funnel.landing_viewed_at:
                    funnel.time_to_start = int((now - funnel.landing_viewed_at).total_seconds())
                    
            elif event.event_type == AnalyticsEventType.ASSESSMENT_COMPLETED:
                funnel.assessment_completed_at = now
                funnel.current_stage = ConversionStage.ASSESSMENT_COMPLETE.value
                if funnel.assessment_started_at:
                    funnel.time_to_complete = int((now - funnel.assessment_started_at).total_seconds())
                    
            elif event.event_type == AnalyticsEventType.EMAIL_CAPTURED:
                funnel.email_captured_at = now
                funnel.current_stage = ConversionStage.EMAIL_CAPTURE.value
                if funnel.assessment_completed_at:
                    funnel.time_to_email_capture = int((now - funnel.assessment_completed_at).total_seconds())
                    
            elif event.event_type == AnalyticsEventType.CONVERSION_MODAL_OPENED:
                funnel.conversion_modal_opened_at = now
                funnel.current_stage = ConversionStage.CONVERSION_MODAL.value
                
            elif event.event_type == AnalyticsEventType.PAYMENT_INITIATED:
                funnel.payment_attempted_at = now
                funnel.current_stage = ConversionStage.PAYMENT_ATTEMPT.value
                
            funnel.updated_at = now
            self.db.commit()
            
        except Exception as e:
            logger.error(f"Error updating conversion funnel: {e}")
    
    def _update_geographic_analytics(self, event: AnalyticsEvent, location_data: Dict[str, str]):
        """Update geographic analytics"""
        try:
            if not location_data.get('country'):
                return
            
            today = datetime.now(timezone.utc).date()
            
            geo_analytics = self.db.query(GeographicAnalytics).filter(
                GeographicAnalytics.country == location_data['country'],
                GeographicAnalytics.region == location_data.get('region'),
                GeographicAnalytics.city == location_data.get('city'),
                GeographicAnalytics.assessment_type == event.assessment_type,
                GeographicAnalytics.date == today
            ).first()
            
            if not geo_analytics:
                geo_analytics = GeographicAnalytics(
                    country=location_data['country'],
                    region=location_data.get('region'),
                    city=location_data.get('city'),
                    assessment_type=event.assessment_type,
                    date=today
                )
                self.db.add(geo_analytics)
            
            # Update metrics based on event type
            geo_analytics.total_sessions += 1
            
            if event.event_type == AnalyticsEventType.ASSESSMENT_COMPLETED:
                geo_analytics.completed_assessments += 1
            
            if event.page_load_time:
                current_avg = geo_analytics.average_page_load_time or 0
                total_sessions = geo_analytics.total_sessions
                geo_analytics.average_page_load_time = (
                    (current_avg * (total_sessions - 1) + event.page_load_time) / total_sessions
                )
            
            self.db.commit()
            
        except Exception as e:
            logger.error(f"Error updating geographic analytics: {e}")
    
    def cleanup_old_data(self, days: int = 365):
        """Clean up old analytics data for privacy compliance"""
        try:
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
            
            # Delete old analytics events
            deleted_events = self.db.query(AssessmentAnalyticsEvent).filter(
                AssessmentAnalyticsEvent.timestamp < cutoff_date
            ).delete()
            
            # Delete old sessions
            deleted_sessions = self.db.query(AssessmentSession).filter(
                AssessmentSession.started_at < cutoff_date
            ).delete()
            
            # Delete old conversion funnels
            deleted_funnels = self.db.query(ConversionFunnel).filter(
                ConversionFunnel.created_at < cutoff_date
            ).delete()
            
            # Delete old lead quality metrics
            deleted_leads = self.db.query(LeadQualityMetrics).filter(
                LeadQualityMetrics.created_at < cutoff_date
            ).delete()
            
            # Delete old performance metrics
            deleted_performance = self.db.query(PerformanceMetrics).filter(
                PerformanceMetrics.timestamp < cutoff_date
            ).delete()
            
            self.db.commit()
            
            logger.info(f"Cleaned up old analytics data: {deleted_events} events, {deleted_sessions} sessions, "
                       f"{deleted_funnels} funnels, {deleted_leads} leads, {deleted_performance} performance metrics")
            
        except Exception as e:
            logger.error(f"Error cleaning up old data: {e}")
            self.db.rollback()
