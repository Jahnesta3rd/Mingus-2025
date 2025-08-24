"""
Session Service for Enhanced Job Recommendations
Manages user sessions, upload data, and results storage
"""

import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from loguru import logger
import redis
import os

class SessionService:
    """Service for managing user sessions and data storage"""
    
    def __init__(self, redis_url: Optional[str] = None):
        """Initialize session service"""
        self.redis_url = redis_url or os.getenv('REDIS_URL', 'redis://localhost:6379')
        self.session_ttl = 3600 * 24  # 24 hours
        self.result_ttl = 3600 * 24 * 7  # 7 days
        
        try:
            self.redis_client = redis.from_url(self.redis_url)
            self.redis_client.ping()
            logger.info("Session service connected to Redis")
        except Exception as e:
            logger.warning(f"Redis connection failed: {str(e)}. Using in-memory storage.")
            self.redis_client = None
            self._memory_storage = {}
    
    def store_session(self, session_id: str, session_data: Dict[str, Any]) -> bool:
        """Store session data"""
        try:
            session_data['updated_at'] = datetime.utcnow().isoformat()
            
            if self.redis_client:
                self.redis_client.setex(
                    f"session:{session_id}",
                    self.session_ttl,
                    json.dumps(session_data)
                )
            else:
                self._memory_storage[f"session:{session_id}"] = {
                    'data': session_data,
                    'expires_at': datetime.utcnow() + timedelta(seconds=self.session_ttl)
                }
            
            logger.info(f"Session stored: {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error storing session {session_id}: {str(e)}")
            return False
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session data"""
        try:
            if self.redis_client:
                data = self.redis_client.get(f"session:{session_id}")
                if data:
                    return json.loads(data)
            else:
                storage_key = f"session:{session_id}"
                if storage_key in self._memory_storage:
                    item = self._memory_storage[storage_key]
                    if datetime.utcnow() < item['expires_at']:
                        return item['data']
                    else:
                        del self._memory_storage[storage_key]
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting session {session_id}: {str(e)}")
            return None
    
    def update_session(self, session_id: str, updates: Dict[str, Any]) -> bool:
        """Update session data"""
        try:
            session_data = self.get_session(session_id)
            if not session_data:
                return False
            
            session_data.update(updates)
            session_data['updated_at'] = datetime.utcnow().isoformat()
            
            return self.store_session(session_id, session_data)
            
        except Exception as e:
            logger.error(f"Error updating session {session_id}: {str(e)}")
            return False
    
    def delete_session(self, session_id: str) -> bool:
        """Delete session data"""
        try:
            if self.redis_client:
                self.redis_client.delete(f"session:{session_id}")
            else:
                storage_key = f"session:{session_id}"
                if storage_key in self._memory_storage:
                    del self._memory_storage[storage_key]
            
            logger.info(f"Session deleted: {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting session {session_id}: {str(e)}")
            return False
    
    def store_result(self, session_id: str, result_data: Dict[str, Any]) -> bool:
        """Store processing results"""
        try:
            result_data['stored_at'] = datetime.utcnow().isoformat()
            
            if self.redis_client:
                self.redis_client.setex(
                    f"result:{session_id}",
                    self.result_ttl,
                    json.dumps(result_data)
                )
            else:
                self._memory_storage[f"result:{session_id}"] = {
                    'data': result_data,
                    'expires_at': datetime.utcnow() + timedelta(seconds=self.result_ttl)
                }
            
            logger.info(f"Result stored for session: {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error storing result for session {session_id}: {str(e)}")
            return False
    
    def get_result(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get processing results"""
        try:
            if self.redis_client:
                data = self.redis_client.get(f"result:{session_id}")
                if data:
                    return json.loads(data)
            else:
                storage_key = f"result:{session_id}"
                if storage_key in self._memory_storage:
                    item = self._memory_storage[storage_key]
                    if datetime.utcnow() < item['expires_at']:
                        return item['data']
                    else:
                        del self._memory_storage[storage_key]
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting result for session {session_id}: {str(e)}")
            return None
    
    def get_user_sessions(self, user_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent sessions for a user"""
        try:
            sessions = []
            
            if self.redis_client:
                # Scan for user sessions
                pattern = f"session:*"
                for key in self.redis_client.scan_iter(match=pattern):
                    data = self.redis_client.get(key)
                    if data:
                        session_data = json.loads(data)
                        if session_data.get('user_id') == user_id:
                            sessions.append(session_data)
                
                # Sort by creation date and limit
                sessions.sort(key=lambda x: x.get('created_at', ''), reverse=True)
                return sessions[:limit]
            else:
                # In-memory search
                for key, item in self._memory_storage.items():
                    if key.startswith('session:') and datetime.utcnow() < item['expires_at']:
                        session_data = item['data']
                        if session_data.get('user_id') == user_id:
                            sessions.append(session_data)
                
                sessions.sort(key=lambda x: x.get('created_at', ''), reverse=True)
                return sessions[:limit]
            
        except Exception as e:
            logger.error(f"Error getting user sessions for {user_id}: {str(e)}")
            return []
    
    def get_analytics(self, start_date: Optional[str] = None, 
                     end_date: Optional[str] = None, 
                     user_id: Optional[int] = None) -> Dict[str, Any]:
        """Get analytics data for sessions"""
        try:
            analytics = {
                'total_sessions': 0,
                'completed_sessions': 0,
                'failed_sessions': 0,
                'avg_processing_time': 0,
                'user_activity': {},
                'field_distribution': {},
                'risk_preference_distribution': {}
            }
            
            if self.redis_client:
                # Scan for sessions
                pattern = f"session:*"
                for key in self.redis_client.scan_iter(match=pattern):
                    data = self.redis_client.get(key)
                    if data:
                        session_data = json.loads(data)
                        
                        # Apply filters
                        if user_id and session_data.get('user_id') != user_id:
                            continue
                        
                        if start_date and session_data.get('created_at', '') < start_date:
                            continue
                        
                        if end_date and session_data.get('created_at', '') > end_date:
                            continue
                        
                        # Update analytics
                        analytics['total_sessions'] += 1
                        
                        if session_data.get('status') == 'completed':
                            analytics['completed_sessions'] += 1
                        elif session_data.get('status') == 'failed':
                            analytics['failed_sessions'] += 1
                        
                        # User activity
                        user_id = session_data.get('user_id')
                        if user_id:
                            analytics['user_activity'][user_id] = analytics['user_activity'].get(user_id, 0) + 1
                        
                        # Field distribution
                        field = session_data.get('demographic_data', {}).get('industry', 'Unknown')
                        analytics['field_distribution'][field] = analytics['field_distribution'].get(field, 0) + 1
                        
                        # Risk preference
                        risk = session_data.get('risk_preference', 'unknown')
                        analytics['risk_preference_distribution'][risk] = analytics['risk_preference_distribution'].get(risk, 0) + 1
            else:
                # In-memory analytics
                for key, item in self._memory_storage.items():
                    if key.startswith('session:') and datetime.utcnow() < item['expires_at']:
                        session_data = item['data']
                        
                        # Apply filters
                        if user_id and session_data.get('user_id') != user_id:
                            continue
                        
                        if start_date and session_data.get('created_at', '') < start_date:
                            continue
                        
                        if end_date and session_data.get('created_at', '') > end_date:
                            continue
                        
                        # Update analytics
                        analytics['total_sessions'] += 1
                        
                        if session_data.get('status') == 'completed':
                            analytics['completed_sessions'] += 1
                        elif session_data.get('status') == 'failed':
                            analytics['failed_sessions'] += 1
                        
                        # User activity
                        user_id = session_data.get('user_id')
                        if user_id:
                            analytics['user_activity'][user_id] = analytics['user_activity'].get(user_id, 0) + 1
                        
                        # Field distribution
                        field = session_data.get('demographic_data', {}).get('industry', 'Unknown')
                        analytics['field_distribution'][field] = analytics['field_distribution'].get(field, 0) + 1
                        
                        # Risk preference
                        risk = session_data.get('risk_preference', 'unknown')
                        analytics['risk_preference_distribution'][risk] = analytics['risk_preference_distribution'].get(risk, 0) + 1
            
            # Calculate completion rate
            if analytics['total_sessions'] > 0:
                analytics['completion_rate'] = analytics['completed_sessions'] / analytics['total_sessions']
            else:
                analytics['completion_rate'] = 0
            
            return analytics
            
        except Exception as e:
            logger.error(f"Error getting analytics: {str(e)}")
            return {}
    
    def cleanup_expired_sessions(self) -> int:
        """Clean up expired sessions and results"""
        try:
            cleaned_count = 0
            
            if self.redis_client:
                # Redis handles expiration automatically
                return 0
            else:
                # Clean up in-memory storage
                current_time = datetime.utcnow()
                keys_to_delete = []
                
                for key, item in self._memory_storage.items():
                    if current_time >= item['expires_at']:
                        keys_to_delete.append(key)
                
                for key in keys_to_delete:
                    del self._memory_storage[key]
                    cleaned_count += 1
                
                logger.info(f"Cleaned up {cleaned_count} expired sessions/results")
                return cleaned_count
            
        except Exception as e:
            logger.error(f"Error cleaning up expired sessions: {str(e)}")
            return 0
    
    def ping(self) -> bool:
        """Health check for the service"""
        try:
            if self.redis_client:
                self.redis_client.ping()
            return True
        except Exception as e:
            logger.error(f"Session service health check failed: {str(e)}")
            return False 