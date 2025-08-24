"""
MINGUS Analytics Service
Backend service for analytics processing, event aggregation, and reporting
Supports Google Analytics 4 and Microsoft Clarity data integration
"""

import logging
import json
import redis
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import os
import requests
from flask import current_app, request, g
import sqlite3
from contextlib import contextmanager

logger = logging.getLogger(__name__)

class AnalyticsEventType(Enum):
    """Analytics event types"""
    PAGE_VIEW = "page_view"
    USER_ACTION = "user_action"
    CONVERSION = "conversion"
    ASSESSMENT_SELECTION = "assessment_selection"
    MODAL_INTERACTION = "modal_interaction"
    FORM_SUBMISSION = "form_submission"
    CTA_CLICK = "cta_click"
    SCROLL_DEPTH = "scroll_depth"
    TIME_ON_PAGE = "time_on_page"
    ERROR = "error"
    PERFORMANCE = "performance"

class ConversionGoal(Enum):
    """Conversion goals"""
    LEAD_GENERATION = "lead_generation"
    ASSESSMENT_COMPLETION = "assessment_completion"
    SUBSCRIPTION_SIGNUP = "subscription_signup"
    FORM_SUBMISSION = "form_submission"

@dataclass
class AnalyticsEvent:
    """Analytics event data structure"""
    event_id: str
    event_type: AnalyticsEventType
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
    properties: Dict[str, Any] = field(default_factory=dict)
    source: str = "web"
    platform: str = "mingus"

@dataclass
class ConversionEvent:
    """Conversion event data structure"""
    conversion_id: str
    goal: ConversionGoal
    value: float
    currency: str = "USD"
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
    properties: Dict[str, Any] = field(default_factory=dict)
    source: str = "web"

@dataclass
class UserSegment:
    """User segment data structure"""
    segment_id: str
    name: str
    criteria: Dict[str, Any]
    description: str
    created_at: datetime = field(default_factory=datetime.utcnow)

class AnalyticsService:
    """Comprehensive analytics service for MINGUS"""
    
    def __init__(self):
        # Redis configuration
        self.redis_host = os.getenv('REDIS_HOST', 'localhost')
        self.redis_port = int(os.getenv('REDIS_PORT', '6379'))
        self.redis_db = int(os.getenv('REDIS_DB', '0'))
        self.redis_password = os.getenv('REDIS_PASSWORD')
        
        # Initialize Redis connection
        try:
            self.redis_client = redis.Redis(
                host=self.redis_host,
                port=self.redis_port,
                db=self.redis_db,
                password=self.redis_password,
                decode_responses=True
            )
            self.redis_client.ping()
        except Exception as e:
            logger.error(f"Redis connection failed: {e}")
            self.redis_client = None
        
        # Analytics configuration
        self.config = {
            'ga4': {
                'enabled': os.getenv('GA4_ENABLED', 'false').lower() == 'true',
                'measurement_id': os.getenv('GA4_MEASUREMENT_ID'),
                'api_secret': os.getenv('GA4_API_SECRET'),
                'debug_mode': os.getenv('GA4_DEBUG_MODE', 'false').lower() == 'true'
            },
            'clarity': {
                'enabled': os.getenv('CLARITY_ENABLED', 'false').lower() == 'true',
                'project_id': os.getenv('CLARITY_PROJECT_ID'),
                'api_key': os.getenv('CLARITY_API_KEY')
            },
            'retention_days': int(os.getenv('ANALYTICS_RETENTION_DAYS', '90')),
            'batch_size': int(os.getenv('ANALYTICS_BATCH_SIZE', '100'))
        }
        
        # Initialize database
        self.init_database()
        
        # User segments
        self.user_segments = self.load_user_segments()
    
    def init_database(self):
        """Initialize analytics database tables"""
        try:
            with self.get_db_connection() as conn:
                cursor = conn.cursor()
                
                # Analytics events table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS analytics_events (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        event_id TEXT UNIQUE NOT NULL,
                        event_type TEXT NOT NULL,
                        user_id TEXT,
                        session_id TEXT,
                        timestamp DATETIME NOT NULL,
                        properties TEXT,
                        source TEXT DEFAULT 'web',
                        platform TEXT DEFAULT 'mingus',
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Conversion events table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS conversion_events (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        conversion_id TEXT UNIQUE NOT NULL,
                        goal TEXT NOT NULL,
                        value REAL NOT NULL,
                        currency TEXT DEFAULT 'USD',
                        user_id TEXT,
                        session_id TEXT,
                        timestamp DATETIME NOT NULL,
                        properties TEXT,
                        source TEXT DEFAULT 'web',
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # User segments table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS user_segments (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        segment_id TEXT UNIQUE NOT NULL,
                        name TEXT NOT NULL,
                        criteria TEXT NOT NULL,
                        description TEXT,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Analytics metrics table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS analytics_metrics (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        metric_name TEXT NOT NULL,
                        metric_value REAL NOT NULL,
                        metric_date DATE NOT NULL,
                        segment_id TEXT,
                        properties TEXT,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(metric_name, metric_date, segment_id)
                    )
                ''')
                
                conn.commit()
                logger.info("Analytics database initialized successfully")
                
        except Exception as e:
            logger.error(f"Failed to initialize analytics database: {e}")
    
    @contextmanager
    def get_db_connection(self):
        """Get database connection"""
        db_path = os.path.join(current_app.instance_path, 'analytics.db')
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()
    
    def track_event(self, event: AnalyticsEvent) -> bool:
        """
        Track an analytics event
        
        Args:
            event: AnalyticsEvent object
        
        Returns:
            bool: Success status
        """
        try:
            # Store in database
            with self.get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO analytics_events 
                    (event_id, event_type, user_id, session_id, timestamp, properties, source, platform)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    event.event_id,
                    event.event_type.value,
                    event.user_id,
                    event.session_id,
                    event.timestamp.isoformat(),
                    json.dumps(event.properties),
                    event.source,
                    event.platform
                ))
                conn.commit()
            
            # Store in Redis for real-time analytics
            if self.redis_client:
                self.store_event_redis(event)
            
            # Send to external platforms
            self.send_to_external_platforms(event)
            
            logger.info(f"Event tracked: {event.event_type.value} - {event.event_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to track event: {e}")
            return False
    
    def track_conversion(self, conversion: ConversionEvent) -> bool:
        """
        Track a conversion event
        
        Args:
            conversion: ConversionEvent object
        
        Returns:
            bool: Success status
        """
        try:
            # Store in database
            with self.get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO conversion_events 
                    (conversion_id, goal, value, currency, user_id, session_id, timestamp, properties, source)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    conversion.conversion_id,
                    conversion.goal.value,
                    conversion.value,
                    conversion.currency,
                    conversion.user_id,
                    conversion.session_id,
                    conversion.timestamp.isoformat(),
                    json.dumps(conversion.properties),
                    conversion.source
                ))
                conn.commit()
            
            # Store in Redis
            if self.redis_client:
                self.store_conversion_redis(conversion)
            
            # Send to external platforms
            self.send_conversion_to_external_platforms(conversion)
            
            logger.info(f"Conversion tracked: {conversion.goal.value} - {conversion.conversion_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to track conversion: {e}")
            return False
    
    def store_event_redis(self, event: AnalyticsEvent):
        """Store event in Redis for real-time analytics"""
        try:
            # Store event data
            event_key = f"event:{event.event_id}"
            event_data = {
                'event_type': event.event_type.value,
                'user_id': event.user_id,
                'session_id': event.session_id,
                'timestamp': event.timestamp.isoformat(),
                'properties': json.dumps(event.properties),
                'source': event.source
            }
            
            self.redis_client.hmset(event_key, event_data)
            self.redis_client.expire(event_key, self.config['retention_days'] * 86400)
            
            # Update event counters
            date_key = f"events:{event.timestamp.strftime('%Y-%m-%d')}"
            self.redis_client.hincrby(date_key, event.event_type.value, 1)
            self.redis_client.expire(date_key, self.config['retention_days'] * 86400)
            
            # Update user activity
            if event.user_id:
                user_key = f"user_activity:{event.user_id}"
                self.redis_client.hset(user_key, 'last_event', event.timestamp.isoformat())
                self.redis_client.hincrby(user_key, 'event_count', 1)
                self.redis_client.expire(user_key, self.config['retention_days'] * 86400)
            
            # Update session activity
            if event.session_id:
                session_key = f"session:{event.session_id}"
                self.redis_client.hset(session_key, 'last_event', event.timestamp.isoformat())
                self.redis_client.hincrby(session_key, 'event_count', 1)
                self.redis_client.expire(session_key, 86400)  # 24 hours
            
        except Exception as e:
            logger.error(f"Failed to store event in Redis: {e}")
    
    def store_conversion_redis(self, conversion: ConversionEvent):
        """Store conversion in Redis"""
        try:
            # Store conversion data
            conversion_key = f"conversion:{conversion.conversion_id}"
            conversion_data = {
                'goal': conversion.goal.value,
                'value': str(conversion.value),
                'currency': conversion.currency,
                'user_id': conversion.user_id,
                'session_id': conversion.session_id,
                'timestamp': conversion.timestamp.isoformat(),
                'properties': json.dumps(conversion.properties)
            }
            
            self.redis_client.hmset(conversion_key, conversion_data)
            self.redis_client.expire(conversion_key, self.config['retention_days'] * 86400)
            
            # Update conversion counters
            date_key = f"conversions:{conversion.timestamp.strftime('%Y-%m-%d')}"
            self.redis_client.hincrby(date_key, conversion.goal.value, 1)
            self.redis_client.hincrbyfloat(date_key, f"{conversion.goal.value}_value", conversion.value)
            self.redis_client.expire(date_key, self.config['retention_days'] * 86400)
            
        except Exception as e:
            logger.error(f"Failed to store conversion in Redis: {e}")
    
    def send_to_external_platforms(self, event: AnalyticsEvent):
        """Send event to external analytics platforms"""
        # Send to GA4
        if self.config['ga4']['enabled']:
            self.send_to_ga4(event)
        
        # Send to Clarity
        if self.config['clarity']['enabled']:
            self.send_to_clarity(event)
    
    def send_to_ga4(self, event: AnalyticsEvent):
        """Send event to Google Analytics 4"""
        try:
            if not self.config['ga4']['api_secret']:
                return
            
            # GA4 Measurement Protocol
            endpoint = f"https://www.google-analytics.com/mp/collect"
            params = {
                'measurement_id': self.config['ga4']['measurement_id'],
                'api_secret': self.config['ga4']['api_secret']
            }
            
            payload = {
                'client_id': event.session_id or 'anonymous',
                'user_id': event.user_id,
                'events': [{
                    'name': event.event_type.value,
                    'parameters': event.properties
                }]
            }
            
            response = requests.post(endpoint, params=params, json=payload, timeout=5)
            
            if response.status_code != 204:
                logger.warning(f"GA4 event send failed: {response.status_code}")
                
        except Exception as e:
            logger.error(f"Failed to send event to GA4: {e}")
    
    def send_to_clarity(self, event: AnalyticsEvent):
        """Send event to Microsoft Clarity"""
        try:
            if not self.config['clarity']['api_key']:
                return
            
            # Clarity API endpoint
            endpoint = f"https://clarity.microsoft.com/api/v1/projects/{self.config['clarity']['project_id']}/events"
            
            headers = {
                'Authorization': f"Bearer {self.config['clarity']['api_key']}",
                'Content-Type': 'application/json'
            }
            
            payload = {
                'event_type': event.event_type.value,
                'user_id': event.user_id,
                'session_id': event.session_id,
                'timestamp': event.timestamp.isoformat(),
                'properties': event.properties
            }
            
            response = requests.post(endpoint, headers=headers, json=payload, timeout=5)
            
            if response.status_code != 200:
                logger.warning(f"Clarity event send failed: {response.status_code}")
                
        except Exception as e:
            logger.error(f"Failed to send event to Clarity: {e}")
    
    def send_conversion_to_external_platforms(self, conversion: ConversionEvent):
        """Send conversion to external platforms"""
        # Send to GA4
        if self.config['ga4']['enabled']:
            self.send_conversion_to_ga4(conversion)
        
        # Send to Clarity
        if self.config['clarity']['enabled']:
            self.send_conversion_to_clarity(conversion)
    
    def send_conversion_to_ga4(self, conversion: ConversionEvent):
        """Send conversion to GA4"""
        try:
            if not self.config['ga4']['api_secret']:
                return
            
            endpoint = f"https://www.google-analytics.com/mp/collect"
            params = {
                'measurement_id': self.config['ga4']['measurement_id'],
                'api_secret': self.config['ga4']['api_secret']
            }
            
            payload = {
                'client_id': conversion.session_id or 'anonymous',
                'user_id': conversion.user_id,
                'events': [{
                    'name': 'conversion',
                    'parameters': {
                        'value': conversion.value,
                        'currency': conversion.currency,
                        'goal': conversion.goal.value,
                        **conversion.properties
                    }
                }]
            }
            
            response = requests.post(endpoint, params=params, json=payload, timeout=5)
            
            if response.status_code != 204:
                logger.warning(f"GA4 conversion send failed: {response.status_code}")
                
        except Exception as e:
            logger.error(f"Failed to send conversion to GA4: {e}")
    
    def send_conversion_to_clarity(self, conversion: ConversionEvent):
        """Send conversion to Clarity"""
        try:
            if not self.config['clarity']['api_key']:
                return
            
            endpoint = f"https://clarity.microsoft.com/api/v1/projects/{self.config['clarity']['project_id']}/conversions"
            
            headers = {
                'Authorization': f"Bearer {self.config['clarity']['api_key']}",
                'Content-Type': 'application/json'
            }
            
            payload = {
                'goal': conversion.goal.value,
                'value': conversion.value,
                'currency': conversion.currency,
                'user_id': conversion.user_id,
                'session_id': conversion.session_id,
                'timestamp': conversion.timestamp.isoformat(),
                'properties': conversion.properties
            }
            
            response = requests.post(endpoint, headers=headers, json=payload, timeout=5)
            
            if response.status_code != 200:
                logger.warning(f"Clarity conversion send failed: {response.status_code}")
                
        except Exception as e:
            logger.error(f"Failed to send conversion to Clarity: {e}")
    
    def get_events(self, 
                  event_type: Optional[AnalyticsEventType] = None,
                  user_id: Optional[str] = None,
                  session_id: Optional[str] = None,
                  start_date: Optional[datetime] = None,
                  end_date: Optional[datetime] = None,
                  limit: int = 100) -> List[AnalyticsEvent]:
        """Get analytics events with filters"""
        try:
            with self.get_db_connection() as conn:
                cursor = conn.cursor()
                
                query = "SELECT * FROM analytics_events WHERE 1=1"
                params = []
                
                if event_type:
                    query += " AND event_type = ?"
                    params.append(event_type.value)
                
                if user_id:
                    query += " AND user_id = ?"
                    params.append(user_id)
                
                if session_id:
                    query += " AND session_id = ?"
                    params.append(session_id)
                
                if start_date:
                    query += " AND timestamp >= ?"
                    params.append(start_date.isoformat())
                
                if end_date:
                    query += " AND timestamp <= ?"
                    params.append(end_date.isoformat())
                
                query += " ORDER BY timestamp DESC LIMIT ?"
                params.append(limit)
                
                cursor.execute(query, params)
                rows = cursor.fetchall()
                
                events = []
                for row in rows:
                    event = AnalyticsEvent(
                        event_id=row['event_id'],
                        event_type=AnalyticsEventType(row['event_type']),
                        user_id=row['user_id'],
                        session_id=row['session_id'],
                        timestamp=datetime.fromisoformat(row['timestamp']),
                        properties=json.loads(row['properties']) if row['properties'] else {},
                        source=row['source'],
                        platform=row['platform']
                    )
                    events.append(event)
                
                return events
                
        except Exception as e:
            logger.error(f"Failed to get events: {e}")
            return []
    
    def get_conversions(self,
                       goal: Optional[ConversionGoal] = None,
                       user_id: Optional[str] = None,
                       start_date: Optional[datetime] = None,
                       end_date: Optional[datetime] = None,
                       limit: int = 100) -> List[ConversionEvent]:
        """Get conversion events with filters"""
        try:
            with self.get_db_connection() as conn:
                cursor = conn.cursor()
                
                query = "SELECT * FROM conversion_events WHERE 1=1"
                params = []
                
                if goal:
                    query += " AND goal = ?"
                    params.append(goal.value)
                
                if user_id:
                    query += " AND user_id = ?"
                    params.append(user_id)
                
                if start_date:
                    query += " AND timestamp >= ?"
                    params.append(start_date.isoformat())
                
                if end_date:
                    query += " AND timestamp <= ?"
                    params.append(end_date.isoformat())
                
                query += " ORDER BY timestamp DESC LIMIT ?"
                params.append(limit)
                
                cursor.execute(query, params)
                rows = cursor.fetchall()
                
                conversions = []
                for row in rows:
                    conversion = ConversionEvent(
                        conversion_id=row['conversion_id'],
                        goal=ConversionGoal(row['goal']),
                        value=row['value'],
                        currency=row['currency'],
                        user_id=row['user_id'],
                        session_id=row['session_id'],
                        timestamp=datetime.fromisoformat(row['timestamp']),
                        properties=json.loads(row['properties']) if row['properties'] else {},
                        source=row['source']
                    )
                    conversions.append(conversion)
                
                return conversions
                
        except Exception as e:
            logger.error(f"Failed to get conversions: {e}")
            return []
    
    def get_metrics(self, 
                   metric_name: str,
                   start_date: datetime,
                   end_date: datetime,
                   segment_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get analytics metrics"""
        try:
            with self.get_db_connection() as conn:
                cursor = conn.cursor()
                
                query = """
                    SELECT metric_name, metric_value, metric_date, segment_id, properties
                    FROM analytics_metrics 
                    WHERE metric_name = ? AND metric_date BETWEEN ? AND ?
                """
                params = [metric_name, start_date.date(), end_date.date()]
                
                if segment_id:
                    query += " AND segment_id = ?"
                    params.append(segment_id)
                
                query += " ORDER BY metric_date"
                
                cursor.execute(query, params)
                rows = cursor.fetchall()
                
                metrics = []
                for row in rows:
                    metric = {
                        'metric_name': row['metric_name'],
                        'metric_value': row['metric_value'],
                        'metric_date': row['metric_date'],
                        'segment_id': row['segment_id'],
                        'properties': json.loads(row['properties']) if row['properties'] else {}
                    }
                    metrics.append(metric)
                
                return metrics
                
        except Exception as e:
            logger.error(f"Failed to get metrics: {e}")
            return []
    
    def calculate_metrics(self, date: datetime):
        """Calculate daily analytics metrics"""
        try:
            # Calculate conversion rates
            conversions = self.get_conversions(
                start_date=date.replace(hour=0, minute=0, second=0, microsecond=0),
                end_date=date.replace(hour=23, minute=59, second=59, microsecond=999999)
            )
            
            # Group conversions by goal
            conversion_counts = {}
            conversion_values = {}
            
            for conversion in conversions:
                goal = conversion.goal.value
                conversion_counts[goal] = conversion_counts.get(goal, 0) + 1
                conversion_values[goal] = conversion_values.get(goal, 0) + conversion.value
            
            # Store metrics
            for goal, count in conversion_counts.items():
                self.store_metric(
                    f"{goal}_conversions",
                    count,
                    date.date(),
                    properties={'goal': goal}
                )
            
            for goal, value in conversion_values.items():
                self.store_metric(
                    f"{goal}_value",
                    value,
                    date.date(),
                    properties={'goal': goal}
                )
            
            # Calculate event counts
            events = self.get_events(
                start_date=date.replace(hour=0, minute=0, second=0, microsecond=0),
                end_date=date.replace(hour=23, minute=59, second=59, microsecond=999999)
            )
            
            event_counts = {}
            for event in events:
                event_type = event.event_type.value
                event_counts[event_type] = event_counts.get(event_type, 0) + 1
            
            for event_type, count in event_counts.items():
                self.store_metric(
                    f"{event_type}_events",
                    count,
                    date.date(),
                    properties={'event_type': event_type}
                )
            
            logger.info(f"Metrics calculated for {date.date()}")
            
        except Exception as e:
            logger.error(f"Failed to calculate metrics: {e}")
    
    def store_metric(self, metric_name: str, value: float, date: datetime.date, 
                    segment_id: Optional[str] = None, properties: Optional[Dict[str, Any]] = None):
        """Store analytics metric"""
        try:
            with self.get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO analytics_metrics 
                    (metric_name, metric_value, metric_date, segment_id, properties)
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    metric_name,
                    value,
                    date,
                    segment_id,
                    json.dumps(properties) if properties else None
                ))
                conn.commit()
                
        except Exception as e:
            logger.error(f"Failed to store metric: {e}")
    
    def load_user_segments(self) -> List[UserSegment]:
        """Load user segments from database"""
        try:
            with self.get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM user_segments ORDER BY created_at")
                rows = cursor.fetchall()
                
                segments = []
                for row in rows:
                    segment = UserSegment(
                        segment_id=row['segment_id'],
                        name=row['name'],
                        criteria=json.loads(row['criteria']),
                        description=row['description'],
                        created_at=datetime.fromisoformat(row['created_at'])
                    )
                    segments.append(segment)
                
                return segments
                
        except Exception as e:
            logger.error(f"Failed to load user segments: {e}")
            return []
    
    def get_user_segment(self, user_id: str) -> Optional[str]:
        """Get user segment based on behavior"""
        try:
            if not self.redis_client:
                return None
            
            # Get user activity data
            user_key = f"user_activity:{user_id}"
            user_data = self.redis_client.hgetall(user_key)
            
            if not user_data:
                return 'new_user'
            
            # Apply segment criteria
            for segment in self.user_segments:
                if self.matches_segment_criteria(user_data, segment.criteria):
                    return segment.segment_id
            
            return 'general_user'
            
        except Exception as e:
            logger.error(f"Failed to get user segment: {e}")
            return None
    
    def matches_segment_criteria(self, user_data: Dict[str, str], criteria: Dict[str, Any]) -> bool:
        """Check if user data matches segment criteria"""
        try:
            for key, condition in criteria.items():
                if key not in user_data:
                    return False
                
                value = user_data[key]
                
                if isinstance(condition, dict):
                    if 'min' in condition and float(value) < condition['min']:
                        return False
                    if 'max' in condition and float(value) > condition['max']:
                        return False
                    if 'equals' in condition and value != str(condition['equals']):
                        return False
                else:
                    if value != str(condition):
                        return False
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to check segment criteria: {e}")
            return False
    
    def get_real_time_stats(self) -> Dict[str, Any]:
        """Get real-time analytics statistics"""
        try:
            if not self.redis_client:
                return {}
            
            now = datetime.utcnow()
            today = now.strftime('%Y-%m-%d')
            
            stats = {
                'active_users': 0,
                'active_sessions': 0,
                'events_today': 0,
                'conversions_today': 0,
                'conversion_value_today': 0.0
            }
            
            # Count active users (users with activity in last 30 minutes)
            active_users = 0
            for key in self.redis_client.scan_iter("user_activity:*"):
                last_event = self.redis_client.hget(key, 'last_event')
                if last_event:
                    last_event_time = datetime.fromisoformat(last_event)
                    if (now - last_event_time).total_seconds() < 1800:  # 30 minutes
                        active_users += 1
            stats['active_users'] = active_users
            
            # Count active sessions (sessions with activity in last 30 minutes)
            active_sessions = 0
            for key in self.redis_client.scan_iter("session:*"):
                last_event = self.redis_client.hget(key, 'last_event')
                if last_event:
                    last_event_time = datetime.fromisoformat(last_event)
                    if (now - last_event_time).total_seconds() < 1800:  # 30 minutes
                        active_sessions += 1
            stats['active_sessions'] = active_sessions
            
            # Get today's events
            events_key = f"events:{today}"
            events_data = self.redis_client.hgetall(events_key)
            stats['events_today'] = sum(int(count) for count in events_data.values())
            
            # Get today's conversions
            conversions_key = f"conversions:{today}"
            conversions_data = self.redis_client.hgetall(conversions_key)
            stats['conversions_today'] = sum(int(count) for key, count in conversions_data.items() 
                                           if not key.endswith('_value'))
            stats['conversion_value_today'] = sum(float(value) for key, value in conversions_data.items() 
                                                 if key.endswith('_value'))
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get real-time stats: {e}")
            return {}

# Create singleton instance
analytics_service = AnalyticsService() 