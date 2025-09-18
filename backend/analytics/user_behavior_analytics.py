#!/usr/bin/env python3
"""
User Behavior Analytics System for Job Recommendation Engine

This module provides comprehensive tracking and analysis of user behavior
throughout the job recommendation process, including session management,
interaction tracking, and feature usage analytics.

Features:
- Session tracking and user journey analysis
- Resume upload and processing event tracking
- User interaction and engagement metrics
- Feature usage patterns and success rates
- Real-time behavior analytics
- User retention and engagement scoring
"""

import sqlite3
import json
import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import time
import hashlib

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class InteractionType(Enum):
    """Types of user interactions to track"""
    PAGE_VIEW = "page_view"
    BUTTON_CLICK = "button_click"
    FORM_SUBMIT = "form_submit"
    SCROLL_DEPTH = "scroll_depth"
    TIME_ON_PAGE = "time_on_page"
    RECOMMENDATION_VIEW = "recommendation_view"
    RECOMMENDATION_CLICK = "recommendation_click"
    APPLICATION_START = "application_start"
    APPLICATION_COMPLETE = "application_complete"
    SHARE = "share"
    BOOKMARK = "bookmark"
    # Risk-based interactions
    RISK_ASSESSMENT_STARTED = "risk_assessment_started"
    RISK_ASSESSMENT_COMPLETED = "risk_assessment_completed"
    RISK_ALERT_VIEWED = "risk_alert_viewed"
    RISK_ALERT_ACKNOWLEDGED = "risk_alert_acknowledged"
    EMERGENCY_UNLOCK_ACTIVATED = "emergency_unlock_activated"
    RISK_RECOMMENDATION_VIEWED = "risk_recommendation_viewed"
    RISK_RECOMMENDATION_CLICKED = "risk_recommendation_clicked"
    PROACTIVE_ACTION_TAKEN = "proactive_action_taken"
    RISK_MITIGATION_STARTED = "risk_mitigation_started"

class ResumeEventType(Enum):
    """Types of resume processing events"""
    UPLOAD_STARTED = "upload_started"
    UPLOAD_COMPLETED = "upload_completed"
    UPLOAD_FAILED = "upload_failed"
    PARSING_STARTED = "parsing_started"
    PARSING_COMPLETED = "parsing_completed"
    PARSING_FAILED = "parsing_failed"
    VALIDATION_STARTED = "validation_started"
    VALIDATION_COMPLETED = "validation_completed"
    VALIDATION_FAILED = "validation_failed"

@dataclass
class UserSession:
    """Data class for user session information"""
    session_id: str
    user_id: str
    session_start: datetime
    device_type: str
    browser: str
    os: str
    ip_address: str
    user_agent: str
    referrer: str = ""
    session_end: Optional[datetime] = None
    session_duration: Optional[int] = None
    exit_page: str = ""
    bounce_rate: bool = False
    conversion_events: int = 0

@dataclass
class ResumeEvent:
    """Data class for resume processing events"""
    session_id: str
    user_id: str
    event_type: str
    file_name: str = ""
    file_size: int = 0
    file_type: str = ""
    processing_time: float = 0.0
    error_message: str = ""
    success_rate: float = 0.0
    confidence_score: float = 0.0
    extracted_fields: str = ""

@dataclass
class UserInteraction:
    """Data class for user interactions"""
    session_id: str
    user_id: str
    interaction_type: str
    page_url: str = ""
    element_id: str = ""
    element_text: str = ""
    interaction_data: str = ""

@dataclass
class FeatureUsage:
    """Data class for feature usage tracking"""
    user_id: str
    feature_name: str
    usage_count: int = 1
    first_used: datetime = None
    last_used: datetime = None
    total_time_spent: int = 0
    success_rate: float = 0.0
    satisfaction_score: Optional[int] = None

class UserBehaviorAnalytics:
    """
    Comprehensive user behavior analytics system for job recommendation engine.
    
    Tracks user sessions, interactions, resume processing events, and feature usage
    to provide insights into user behavior patterns and system effectiveness.
    """
    
    def __init__(self, db_path: str = "backend/analytics/recommendation_analytics.db"):
        """Initialize the user behavior analytics system"""
        self.db_path = db_path
        self._init_database()
        logger.info("UserBehaviorAnalytics initialized successfully")
    
    def _init_database(self):
        """Initialize the analytics database with required tables"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Read and execute the schema
            with open('backend/analytics/recommendation_analytics_schema.sql', 'r') as f:
                schema_sql = f.read()
            
            cursor.executescript(schema_sql)
            conn.commit()
            conn.close()
            logger.info("Analytics database initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing analytics database: {e}")
            raise
    
    def start_user_session(
        self,
        user_id: str,
        device_type: str = "desktop",
        browser: str = "",
        os: str = "",
        ip_address: str = "",
        user_agent: str = "",
        referrer: str = ""
    ) -> str:
        """
        Start a new user session and return session ID
        
        Args:
            user_id: Unique user identifier
            device_type: Type of device (mobile, tablet, desktop)
            browser: Browser name and version
            os: Operating system
            ip_address: User's IP address
            user_agent: Full user agent string
            referrer: Referring page URL
            
        Returns:
            session_id: Unique session identifier
        """
        try:
            session_id = str(uuid.uuid4())
            session = UserSession(
                session_id=session_id,
                user_id=user_id,
                session_start=datetime.now(),
                device_type=device_type,
                browser=browser,
                os=os,
                ip_address=ip_address,
                user_agent=user_agent,
                referrer=referrer
            )
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO user_sessions (
                    session_id, user_id, session_start, device_type,
                    browser, os, ip_address, user_agent, referrer
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                session.session_id, session.user_id, session.session_start,
                session.device_type, session.browser, session.os,
                session.ip_address, session.user_agent, session.referrer
            ))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Started session {session_id} for user {user_id}")
            return session_id
            
        except Exception as e:
            logger.error(f"Error starting user session: {e}")
            raise
    
    def end_user_session(
        self,
        session_id: str,
        exit_page: str = "",
        conversion_events: int = 0
    ) -> bool:
        """
        End a user session and calculate session metrics
        
        Args:
            session_id: Session identifier
            exit_page: Last page visited
            conversion_events: Number of conversion events
            
        Returns:
            bool: Success status
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get session start time
            cursor.execute('''
                SELECT session_start FROM user_sessions WHERE session_id = ?
            ''', (session_id,))
            
            result = cursor.fetchone()
            if not result:
                logger.warning(f"Session {session_id} not found")
                return False
            
            session_start = datetime.fromisoformat(result[0])
            session_end = datetime.now()
            session_duration = int((session_end - session_start).total_seconds())
            
            # Calculate bounce rate (session < 30 seconds with no interactions)
            bounce_rate = session_duration < 30 and conversion_events == 0
            
            # Update session
            cursor.execute('''
                UPDATE user_sessions SET
                    session_end = ?, session_duration = ?, exit_page = ?,
                    bounce_rate = ?, conversion_events = ?
                WHERE session_id = ?
            ''', (session_end, session_duration, exit_page, bounce_rate, conversion_events, session_id))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Ended session {session_id}, duration: {session_duration}s")
            return True
            
        except Exception as e:
            logger.error(f"Error ending user session: {e}")
            return False
    
    def track_resume_event(
        self,
        session_id: str,
        user_id: str,
        event_type: str,
        file_name: str = "",
        file_size: int = 0,
        file_type: str = "",
        processing_time: float = 0.0,
        error_message: str = "",
        success_rate: float = 0.0,
        confidence_score: float = 0.0,
        extracted_fields: Dict[str, Any] = None
    ) -> bool:
        """
        Track resume processing events
        
        Args:
            session_id: Session identifier
            user_id: User identifier
            event_type: Type of resume event
            file_name: Name of uploaded file
            file_size: Size of file in bytes
            file_type: Type of file (pdf, doc, etc.)
            processing_time: Time taken to process in seconds
            error_message: Error message if failed
            success_rate: Success rate of processing
            confidence_score: Confidence score of extraction
            extracted_fields: Dictionary of extracted resume fields
            
        Returns:
            bool: Success status
        """
        try:
            event = ResumeEvent(
                session_id=session_id,
                user_id=user_id,
                event_type=event_type,
                file_name=file_name,
                file_size=file_size,
                file_type=file_type,
                processing_time=processing_time,
                error_message=error_message,
                success_rate=success_rate,
                confidence_score=confidence_score,
                extracted_fields=json.dumps(extracted_fields or {})
            )
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO resume_events (
                    session_id, user_id, event_type, file_name, file_size,
                    file_type, processing_time, error_message, success_rate,
                    confidence_score, extracted_fields
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                event.session_id, event.user_id, event.event_type,
                event.file_name, event.file_size, event.file_type,
                event.processing_time, event.error_message, event.success_rate,
                event.confidence_score, event.extracted_fields
            ))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Tracked resume event: {event_type} for session {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error tracking resume event: {e}")
            return False
    
    def track_user_interaction(
        self,
        session_id: str,
        user_id: str,
        interaction_type: str,
        page_url: str = "",
        element_id: str = "",
        element_text: str = "",
        interaction_data: Dict[str, Any] = None
    ) -> bool:
        """
        Track user interactions
        
        Args:
            session_id: Session identifier
            user_id: User identifier
            interaction_type: Type of interaction
            page_url: URL of the page
            element_id: ID of the interacted element
            element_text: Text content of the element
            interaction_data: Additional interaction data
            
        Returns:
            bool: Success status
        """
        try:
            interaction = UserInteraction(
                session_id=session_id,
                user_id=user_id,
                interaction_type=interaction_type,
                page_url=page_url,
                element_id=element_id,
                element_text=element_text,
                interaction_data=json.dumps(interaction_data or {})
            )
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO user_interactions (
                    session_id, user_id, interaction_type, page_url,
                    element_id, element_text, interaction_data
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                interaction.session_id, interaction.user_id, interaction.interaction_type,
                interaction.page_url, interaction.element_id, interaction.element_text,
                interaction.interaction_data
            ))
            
            conn.commit()
            conn.close()
            
            logger.debug(f"Tracked interaction: {interaction_type} for session {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error tracking user interaction: {e}")
            return False
    
    def track_feature_usage(
        self,
        user_id: str,
        feature_name: str,
        time_spent: int = 0,
        success: bool = True,
        satisfaction_score: Optional[int] = None
    ) -> bool:
        """
        Track feature usage and update metrics
        
        Args:
            user_id: User identifier
            feature_name: Name of the feature
            time_spent: Time spent using feature in seconds
            success: Whether the feature usage was successful
            satisfaction_score: User satisfaction score (1-5)
            
        Returns:
            bool: Success status
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Check if feature usage record exists
            cursor.execute('''
                SELECT usage_count, total_time_spent, success_rate, first_used
                FROM feature_usage WHERE user_id = ? AND feature_name = ?
            ''', (user_id, feature_name))
            
            result = cursor.fetchone()
            now = datetime.now()
            
            if result:
                # Update existing record
                usage_count, total_time_spent, success_rate, first_used = result
                new_usage_count = usage_count + 1
                new_total_time = total_time_spent + time_spent
                
                # Calculate new success rate
                successful_uses = int(success_rate * usage_count / 100) + (1 if success else 0)
                new_success_rate = (successful_uses / new_usage_count) * 100
                
                cursor.execute('''
                    UPDATE feature_usage SET
                        usage_count = ?, last_used = ?, total_time_spent = ?,
                        success_rate = ?, satisfaction_score = ?
                    WHERE user_id = ? AND feature_name = ?
                ''', (new_usage_count, now, new_total_time, new_success_rate,
                      satisfaction_score, user_id, feature_name))
            else:
                # Create new record
                cursor.execute('''
                    INSERT INTO feature_usage (
                        user_id, feature_name, usage_count, first_used, last_used,
                        total_time_spent, success_rate, satisfaction_score
                    ) VALUES (?, ?, 1, ?, ?, ?, ?, ?)
                ''', (user_id, feature_name, now, now, time_spent,
                      (100 if success else 0), satisfaction_score))
            
            conn.commit()
            conn.close()
            
            logger.debug(f"Tracked feature usage: {feature_name} for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error tracking feature usage: {e}")
            return False
    
    def get_user_behavior_metrics(
        self,
        user_id: str,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Get comprehensive behavior metrics for a user
        
        Args:
            user_id: User identifier
            days: Number of days to analyze
            
        Returns:
            Dict containing behavior metrics
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            start_date = datetime.now() - timedelta(days=days)
            
            # Session metrics
            cursor.execute('''
                SELECT 
                    COUNT(*) as total_sessions,
                    AVG(session_duration) as avg_session_duration,
                    COUNT(CASE WHEN bounce_rate = 1 THEN 1 END) as bounce_sessions,
                    COUNT(CASE WHEN conversion_events > 0 THEN 1 END) as conversion_sessions
                FROM user_sessions 
                WHERE user_id = ? AND session_start >= ?
            ''', (user_id, start_date))
            
            session_metrics = cursor.fetchone()
            
            # Resume processing metrics
            cursor.execute('''
                SELECT 
                    COUNT(*) as total_uploads,
                    COUNT(CASE WHEN event_type = 'upload_completed' THEN 1 END) as successful_uploads,
                    AVG(processing_time) as avg_processing_time,
                    AVG(confidence_score) as avg_confidence_score
                FROM resume_events 
                WHERE user_id = ? AND timestamp >= ?
            ''', (user_id, start_date))
            
            resume_metrics = cursor.fetchone()
            
            # Interaction metrics
            cursor.execute('''
                SELECT 
                    interaction_type,
                    COUNT(*) as count
                FROM user_interactions 
                WHERE user_id = ? AND timestamp >= ?
                GROUP BY interaction_type
                ORDER BY count DESC
            ''', (user_id, start_date))
            
            interaction_metrics = dict(cursor.fetchall())
            
            # Feature usage metrics
            cursor.execute('''
                SELECT 
                    feature_name,
                    usage_count,
                    success_rate,
                    total_time_spent,
                    satisfaction_score
                FROM feature_usage 
                WHERE user_id = ?
                ORDER BY usage_count DESC
            ''', (user_id,))
            
            feature_metrics = []
            for row in cursor.fetchall():
                feature_metrics.append({
                    'feature_name': row[0],
                    'usage_count': row[1],
                    'success_rate': row[2],
                    'total_time_spent': row[3],
                    'satisfaction_score': row[4]
                })
            
            conn.close()
            
            return {
                'user_id': user_id,
                'analysis_period_days': days,
                'session_metrics': {
                    'total_sessions': session_metrics[0] or 0,
                    'avg_session_duration': session_metrics[1] or 0,
                    'bounce_rate': (session_metrics[2] or 0) / max(session_metrics[0] or 1, 1) * 100,
                    'conversion_rate': (session_metrics[3] or 0) / max(session_metrics[0] or 1, 1) * 100
                },
                'resume_metrics': {
                    'total_uploads': resume_metrics[0] or 0,
                    'success_rate': (resume_metrics[1] or 0) / max(resume_metrics[0] or 1, 1) * 100,
                    'avg_processing_time': resume_metrics[2] or 0,
                    'avg_confidence_score': resume_metrics[3] or 0
                },
                'interaction_metrics': interaction_metrics,
                'feature_metrics': feature_metrics
            }
            
        except Exception as e:
            logger.error(f"Error getting user behavior metrics: {e}")
            return {}
    
    def get_system_behavior_metrics(
        self,
        days: int = 7
    ) -> Dict[str, Any]:
        """
        Get system-wide behavior metrics
        
        Args:
            days: Number of days to analyze
            
        Returns:
            Dict containing system metrics
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            start_date = datetime.now() - timedelta(days=days)
            
            # Overall session metrics
            cursor.execute('''
                SELECT 
                    COUNT(DISTINCT user_id) as unique_users,
                    COUNT(*) as total_sessions,
                    AVG(session_duration) as avg_session_duration,
                    COUNT(CASE WHEN bounce_rate = 1 THEN 1 END) * 100.0 / COUNT(*) as bounce_rate,
                    COUNT(CASE WHEN conversion_events > 0 THEN 1 END) * 100.0 / COUNT(*) as conversion_rate
                FROM user_sessions 
                WHERE session_start >= ?
            ''', (start_date,))
            
            session_metrics = cursor.fetchone()
            
            # Resume processing metrics
            cursor.execute('''
                SELECT 
                    COUNT(*) as total_uploads,
                    COUNT(CASE WHEN event_type = 'upload_completed' THEN 1 END) * 100.0 / COUNT(*) as success_rate,
                    AVG(processing_time) as avg_processing_time,
                    AVG(confidence_score) as avg_confidence_score
                FROM resume_events 
                WHERE timestamp >= ?
            ''', (start_date,))
            
            resume_metrics = cursor.fetchone()
            
            # Most popular features
            cursor.execute('''
                SELECT 
                    feature_name,
                    SUM(usage_count) as total_usage,
                    AVG(success_rate) as avg_success_rate,
                    AVG(satisfaction_score) as avg_satisfaction
                FROM feature_usage 
                WHERE last_used >= ?
                GROUP BY feature_name
                ORDER BY total_usage DESC
                LIMIT 10
            ''', (start_date,))
            
            top_features = []
            for row in cursor.fetchall():
                top_features.append({
                    'feature_name': row[0],
                    'total_usage': row[1],
                    'avg_success_rate': row[2],
                    'avg_satisfaction': row[3]
                })
            
            # Device and browser breakdown
            cursor.execute('''
                SELECT 
                    device_type,
                    COUNT(*) as count
                FROM user_sessions 
                WHERE session_start >= ?
                GROUP BY device_type
                ORDER BY count DESC
            ''', (start_date,))
            
            device_breakdown = dict(cursor.fetchall())
            
            conn.close()
            
            return {
                'analysis_period_days': days,
                'session_metrics': {
                    'unique_users': session_metrics[0] or 0,
                    'total_sessions': session_metrics[1] or 0,
                    'avg_session_duration': session_metrics[2] or 0,
                    'bounce_rate': session_metrics[3] or 0,
                    'conversion_rate': session_metrics[4] or 0
                },
                'resume_metrics': {
                    'total_uploads': resume_metrics[0] or 0,
                    'success_rate': resume_metrics[1] or 0,
                    'avg_processing_time': resume_metrics[2] or 0,
                    'avg_confidence_score': resume_metrics[3] or 0
                },
                'top_features': top_features,
                'device_breakdown': device_breakdown
            }
            
        except Exception as e:
            logger.error(f"Error getting system behavior metrics: {e}")
            return {}
    
    def get_user_journey(
        self,
        user_id: str,
        session_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get detailed user journey for analysis
        
        Args:
            user_id: User identifier
            session_id: Specific session ID (optional)
            
        Returns:
            List of journey events in chronological order
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get session information
            if session_id:
                cursor.execute('''
                    SELECT session_id, session_start, session_duration, device_type
                    FROM user_sessions 
                    WHERE user_id = ? AND session_id = ?
                    ORDER BY session_start
                ''', (user_id, session_id))
            else:
                cursor.execute('''
                    SELECT session_id, session_start, session_duration, device_type
                    FROM user_sessions 
                    WHERE user_id = ?
                    ORDER BY session_start DESC
                    LIMIT 1
                ''', (user_id,))
            
            session_info = cursor.fetchone()
            if not session_info:
                return []
            
            session_id, session_start, session_duration, device_type = session_info
            
            # Get all events for this session
            journey_events = []
            
            # Resume events
            cursor.execute('''
                SELECT 'resume_event' as event_type, event_type as event_name,
                       timestamp, file_name, processing_time, success_rate
                FROM resume_events 
                WHERE session_id = ?
                ORDER BY timestamp
            ''', (session_id,))
            
            for row in cursor.fetchall():
                journey_events.append({
                    'type': row[0],
                    'name': row[1],
                    'timestamp': row[2],
                    'file_name': row[3],
                    'processing_time': row[4],
                    'success_rate': row[5]
                })
            
            # User interactions
            cursor.execute('''
                SELECT 'interaction' as event_type, interaction_type as event_name,
                       timestamp, page_url, element_id, element_text
                FROM user_interactions 
                WHERE session_id = ?
                ORDER BY timestamp
            ''', (session_id,))
            
            for row in cursor.fetchall():
                journey_events.append({
                    'type': row[0],
                    'name': row[1],
                    'timestamp': row[2],
                    'page_url': row[3],
                    'element_id': row[4],
                    'element_text': row[5]
                })
            
            # Sort by timestamp
            journey_events.sort(key=lambda x: x['timestamp'])
            
            conn.close()
            
            return {
                'session_id': session_id,
                'session_start': session_start,
                'session_duration': session_duration,
                'device_type': device_type,
                'events': journey_events
            }
            
        except Exception as e:
            logger.error(f"Error getting user journey: {e}")
            return []
    
    def calculate_engagement_score(
        self,
        user_id: str,
        days: int = 30
    ) -> float:
        """
        Calculate user engagement score based on behavior patterns
        
        Args:
            user_id: User identifier
            days: Number of days to analyze
            
        Returns:
            Engagement score between 0 and 100
        """
        try:
            metrics = self.get_user_behavior_metrics(user_id, days)
            
            if not metrics:
                return 0.0
            
            session_metrics = metrics['session_metrics']
            resume_metrics = metrics['resume_metrics']
            feature_metrics = metrics['feature_metrics']
            
            # Calculate engagement components
            session_score = min(session_metrics['total_sessions'] * 10, 40)  # Max 40 points
            duration_score = min(session_metrics['avg_session_duration'] / 60 * 5, 20)  # Max 20 points
            conversion_score = session_metrics['conversion_rate'] * 0.2  # Max 20 points
            feature_score = min(len(feature_metrics) * 2, 20)  # Max 20 points
            
            # Penalty for high bounce rate
            bounce_penalty = max(0, session_metrics['bounce_rate'] - 50) * 0.2
            
            engagement_score = max(0, session_score + duration_score + conversion_score + feature_score - bounce_penalty)
            
            return min(engagement_score, 100.0)
            
        except Exception as e:
            logger.error(f"Error calculating engagement score: {e}")
            return 0.0
    
    # Risk-based user journey tracking methods
    
    def track_risk_user_journey(self, user_id: str, session_id: str, journey_step: str, 
                              risk_data: Dict[str, Any] = None) -> bool:
        """
        Track risk-based user journey steps
        
        Args:
            user_id: User identifier
            session_id: Session identifier
            journey_step: Risk journey step (e.g., 'risk_detected', 'assessment_started', 'recommendation_viewed')
            risk_data: Additional risk-related data
            
        Returns:
            bool: Success status
        """
        try:
            # Track as user interaction with risk-specific type
            interaction_type = f"risk_{journey_step}"
            
            return self.track_user_interaction(
                session_id=session_id,
                user_id=user_id,
                interaction_type=interaction_type,
                page_url=f"/risk-journey/{journey_step}",
                element_id=f"risk_{journey_step}",
                element_text=f"Risk Journey: {journey_step}",
                interaction_data=risk_data or {}
            )
            
        except Exception as e:
            logger.error(f"Error tracking risk user journey: {e}")
            return False
    
    def get_risk_user_journey_analysis(self, user_id: str, days: int = 30) -> Dict[str, Any]:
        """
        Analyze risk-based user journey for a specific user
        
        Args:
            user_id: User identifier
            days: Analysis period in days
            
        Returns:
            Dict containing journey analysis
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get risk-related interactions
                cursor.execute('''
                    SELECT 
                        interaction_type,
                        interaction_timestamp,
                        interaction_data,
                        page_url
                    FROM user_interactions
                    WHERE user_id = ? 
                    AND interaction_type LIKE 'risk_%'
                    AND interaction_timestamp >= datetime('now', '-{} days')
                    ORDER BY interaction_timestamp
                '''.format(days), (user_id,))
                
                risk_interactions = cursor.fetchall()
                
                # Analyze journey flow
                journey_steps = []
                step_times = []
                
                for interaction in risk_interactions:
                    interaction_type = interaction[0]
                    timestamp = datetime.fromisoformat(interaction[1])
                    interaction_data = json.loads(interaction[2]) if interaction[2] else {}
                    
                    journey_steps.append({
                        'step': interaction_type.replace('risk_', ''),
                        'timestamp': timestamp,
                        'data': interaction_data
                    })
                
                # Calculate journey metrics
                if len(journey_steps) > 1:
                    for i in range(1, len(journey_steps)):
                        time_diff = (journey_steps[i]['timestamp'] - journey_steps[i-1]['timestamp']).total_seconds()
                        step_times.append(time_diff)
                
                # Determine journey completion
                completed_steps = ['assessment_completed', 'recommendation_viewed', 'proactive_action_taken']
                journey_completion = sum(1 for step in journey_steps if step['step'] in completed_steps) / len(completed_steps)
                
                # Calculate engagement score
                risk_engagement_score = self._calculate_risk_engagement_score(journey_steps)
                
                return {
                    'user_id': user_id,
                    'analysis_period_days': days,
                    'total_risk_interactions': len(risk_interactions),
                    'journey_steps': journey_steps,
                    'journey_completion_rate': journey_completion,
                    'risk_engagement_score': risk_engagement_score,
                    'average_step_time_seconds': sum(step_times) / len(step_times) if step_times else 0,
                    'journey_duration_hours': (journey_steps[-1]['timestamp'] - journey_steps[0]['timestamp']).total_seconds() / 3600 if len(journey_steps) > 1 else 0
                }
                
        except Exception as e:
            logger.error(f"Error analyzing risk user journey: {e}")
            return {'error': str(e)}
    
    def _calculate_risk_engagement_score(self, journey_steps: List[Dict[str, Any]]) -> float:
        """Calculate risk engagement score based on journey steps"""
        try:
            if not journey_steps:
                return 0.0
            
            # Define engagement weights for different steps
            engagement_weights = {
                'assessment_started': 0.1,
                'assessment_completed': 0.2,
                'alert_viewed': 0.15,
                'alert_acknowledged': 0.2,
                'emergency_unlock_activated': 0.3,
                'recommendation_viewed': 0.15,
                'recommendation_clicked': 0.2,
                'proactive_action_taken': 0.4,
                'mitigation_started': 0.25
            }
            
            # Calculate weighted engagement score
            total_score = 0.0
            for step in journey_steps:
                step_name = step['step']
                if step_name in engagement_weights:
                    total_score += engagement_weights[step_name]
            
            # Normalize to 0-1 scale
            max_possible_score = sum(engagement_weights.values())
            engagement_score = min(1.0, total_score / max_possible_score)
            
            return engagement_score
            
        except Exception as e:
            logger.error(f"Error calculating risk engagement score: {e}")
            return 0.0
    
    def get_risk_user_segments(self, days: int = 30) -> Dict[str, Any]:
        """
        Get risk-based user segments based on behavior patterns
        
        Args:
            days: Analysis period in days
            
        Returns:
            Dict containing user segment analysis
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get users with risk interactions
                cursor.execute('''
                    SELECT 
                        user_id,
                        COUNT(*) as risk_interaction_count,
                        COUNT(CASE WHEN interaction_type = 'risk_assessment_completed' THEN 1 END) as assessments,
                        COUNT(CASE WHEN interaction_type = 'risk_recommendation_clicked' THEN 1 END) as recommendations_clicked,
                        COUNT(CASE WHEN interaction_type = 'proactive_action_taken' THEN 1 END) as proactive_actions,
                        MAX(interaction_timestamp) as last_interaction
                    FROM user_interactions
                    WHERE interaction_type LIKE 'risk_%'
                    AND interaction_timestamp >= datetime('now', '-{} days')
                    GROUP BY user_id
                '''.format(days))
                
                user_data = cursor.fetchall()
                
                # Segment users based on risk behavior
                segments = {
                    'high_risk_high_engagement': [],
                    'high_risk_low_engagement': [],
                    'low_risk_high_engagement': [],
                    'low_risk_low_engagement': []
                }
                
                for user_row in user_data:
                    user_id = user_row[0]
                    risk_interaction_count = user_row[1]
                    assessments = user_row[2]
                    recommendations_clicked = user_row[3]
                    proactive_actions = user_row[4]
                    last_interaction = user_row[5]
                    
                    # Calculate engagement level
                    engagement_score = (recommendations_clicked + proactive_actions) / max(1, assessments)
                    
                    # Determine risk level (simplified - would need actual risk scores)
                    risk_level = 'high' if risk_interaction_count > 5 else 'low'
                    engagement_level = 'high' if engagement_score > 0.5 else 'low'
                    
                    # Assign to segment
                    segment_key = f"{risk_level}_risk_{engagement_level}_engagement"
                    if segment_key in segments:
                        segments[segment_key].append({
                            'user_id': user_id,
                            'risk_interaction_count': risk_interaction_count,
                            'engagement_score': engagement_score,
                            'last_interaction': last_interaction
                        })
                
                # Calculate segment statistics
                segment_stats = {}
                for segment_name, users in segments.items():
                    segment_stats[segment_name] = {
                        'count': len(users),
                        'avg_engagement_score': sum(u['engagement_score'] for u in users) / max(1, len(users)),
                        'avg_risk_interactions': sum(u['risk_interaction_count'] for u in users) / max(1, len(users))
                    }
                
                return {
                    'analysis_period_days': days,
                    'total_users_analyzed': len(user_data),
                    'segment_distribution': segment_stats,
                    'detailed_segments': segments
                }
                
        except Exception as e:
            logger.error(f"Error getting risk user segments: {e}")
            return {'error': str(e)}
