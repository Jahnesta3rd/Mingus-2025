"""
Progress Service for Enhanced Job Recommendations
Tracks real-time processing progress and status updates
"""

import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from loguru import logger
import redis
import os

class ProgressService:
    """Service for tracking processing progress"""
    
    def __init__(self, redis_url: Optional[str] = None):
        """Initialize progress service"""
        self.redis_url = redis_url or os.getenv('REDIS_URL', 'redis://localhost:6379')
        self.progress_ttl = 3600 * 2  # 2 hours
        
        try:
            self.redis_client = redis.from_url(self.redis_url)
            self.redis_client.ping()
            logger.info("Progress service connected to Redis")
        except Exception as e:
            logger.warning(f"Redis connection failed: {str(e)}. Using in-memory storage.")
            self.redis_client = None
            self._memory_storage = {}
    
    def store_progress(self, progress_id: str, progress_data: Dict[str, Any]) -> bool:
        """Store progress data"""
        try:
            progress_data['created_at'] = datetime.utcnow().isoformat()
            progress_data['updated_at'] = datetime.utcnow().isoformat()
            
            if self.redis_client:
                self.redis_client.setex(
                    f"progress:{progress_id}",
                    self.progress_ttl,
                    json.dumps(progress_data)
                )
            else:
                self._memory_storage[f"progress:{progress_id}"] = {
                    'data': progress_data,
                    'expires_at': datetime.utcnow() + timedelta(seconds=self.progress_ttl)
                }
            
            logger.info(f"Progress stored: {progress_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error storing progress {progress_id}: {str(e)}")
            return False
    
    def get_progress(self, progress_id: str) -> Optional[Dict[str, Any]]:
        """Get progress data"""
        try:
            if self.redis_client:
                data = self.redis_client.get(f"progress:{progress_id}")
                if data:
                    return json.loads(data)
            else:
                storage_key = f"progress:{progress_id}"
                if storage_key in self._memory_storage:
                    item = self._memory_storage[storage_key]
                    if datetime.utcnow() < item['expires_at']:
                        return item['data']
                    else:
                        del self._memory_storage[storage_key]
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting progress {progress_id}: {str(e)}")
            return None
    
    def update_progress(self, progress_id: str, status: str, progress: int, 
                       error_message: Optional[str] = None) -> bool:
        """Update overall progress"""
        try:
            progress_data = self.get_progress(progress_id)
            if not progress_data:
                return False
            
            progress_data['status'] = status
            progress_data['progress'] = progress
            progress_data['updated_at'] = datetime.utcnow().isoformat()
            
            if error_message:
                progress_data['error_message'] = error_message
            
            if status in ['completed', 'failed']:
                progress_data['completed_at'] = datetime.utcnow().isoformat()
            
            return self.store_progress(progress_id, progress_data)
            
        except Exception as e:
            logger.error(f"Error updating progress {progress_id}: {str(e)}")
            return False
    
    def update_step(self, progress_id: str, step_name: str, status: str, progress: int) -> bool:
        """Update specific step progress"""
        try:
            progress_data = self.get_progress(progress_id)
            if not progress_data:
                return False
            
            # Find and update the step
            steps = progress_data.get('steps', [])
            for step in steps:
                if step['name'] == step_name:
                    step['status'] = status
                    step['progress'] = progress
                    step['updated_at'] = datetime.utcnow().isoformat()
                    break
            
            # Update overall progress
            completed_steps = sum(1 for step in steps if step['status'] == 'completed')
            total_steps = len(steps)
            overall_progress = int((completed_steps / total_steps) * 100) if total_steps > 0 else 0
            
            progress_data['progress'] = overall_progress
            progress_data['updated_at'] = datetime.utcnow().isoformat()
            
            return self.store_progress(progress_id, progress_data)
            
        except Exception as e:
            logger.error(f"Error updating step {step_name} for progress {progress_id}: {str(e)}")
            return False
    
    def add_step_log(self, progress_id: str, step_name: str, message: str, 
                    level: str = 'info') -> bool:
        """Add log message to a step"""
        try:
            progress_data = self.get_progress(progress_id)
            if not progress_data:
                return False
            
            # Find the step
            steps = progress_data.get('steps', [])
            for step in steps:
                if step['name'] == step_name:
                    if 'logs' not in step:
                        step['logs'] = []
                    
                    step['logs'].append({
                        'message': message,
                        'level': level,
                        'timestamp': datetime.utcnow().isoformat()
                    })
                    break
            
            return self.store_progress(progress_id, progress_data)
            
        except Exception as e:
            logger.error(f"Error adding log for step {step_name} in progress {progress_id}: {str(e)}")
            return False
    
    def get_active_progress(self, user_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get active progress entries"""
        try:
            active_progress = []
            
            if self.redis_client:
                # Scan for active progress
                pattern = f"progress:*"
                for key in self.redis_client.scan_iter(match=pattern):
                    data = self.redis_client.get(key)
                    if data:
                        progress_data = json.loads(data)
                        
                        # Filter by user if specified
                        if user_id and progress_data.get('user_id') != user_id:
                            continue
                        
                        # Only include active progress
                        if progress_data.get('status') in ['processing', 'pending']:
                            active_progress.append(progress_data)
            else:
                # In-memory search
                for key, item in self._memory_storage.items():
                    if key.startswith('progress:') and datetime.utcnow() < item['expires_at']:
                        progress_data = item['data']
                        
                        # Filter by user if specified
                        if user_id and progress_data.get('user_id') != user_id:
                            continue
                        
                        # Only include active progress
                        if progress_data.get('status') in ['processing', 'pending']:
                            active_progress.append(progress_data)
            
            return active_progress
            
        except Exception as e:
            logger.error(f"Error getting active progress: {str(e)}")
            return []
    
    def cleanup_completed_progress(self, max_age_hours: int = 24) -> int:
        """Clean up completed progress older than specified age"""
        try:
            cleaned_count = 0
            cutoff_time = datetime.utcnow() - timedelta(hours=max_age_hours)
            
            if self.redis_client:
                # Scan for completed progress
                pattern = f"progress:*"
                for key in self.redis_client.scan_iter(match=pattern):
                    data = self.redis_client.get(key)
                    if data:
                        progress_data = json.loads(data)
                        
                        # Check if completed and old enough
                        if progress_data.get('status') in ['completed', 'failed']:
                            completed_at = progress_data.get('completed_at')
                            if completed_at:
                                try:
                                    completed_time = datetime.fromisoformat(completed_at.replace('Z', '+00:00'))
                                    if completed_time < cutoff_time:
                                        self.redis_client.delete(key)
                                        cleaned_count += 1
                                except ValueError:
                                    # Invalid date format, delete anyway
                                    self.redis_client.delete(key)
                                    cleaned_count += 1
            else:
                # In-memory cleanup
                keys_to_delete = []
                
                for key, item in self._memory_storage.items():
                    if key.startswith('progress:'):
                        progress_data = item['data']
                        
                        # Check if completed and old enough
                        if progress_data.get('status') in ['completed', 'failed']:
                            completed_at = progress_data.get('completed_at')
                            if completed_at:
                                try:
                                    completed_time = datetime.fromisoformat(completed_at.replace('Z', '+00:00'))
                                    if completed_time < cutoff_time:
                                        keys_to_delete.append(key)
                                except ValueError:
                                    # Invalid date format, delete anyway
                                    keys_to_delete.append(key)
                
                for key in keys_to_delete:
                    del self._memory_storage[key]
                    cleaned_count += 1
            
            logger.info(f"Cleaned up {cleaned_count} completed progress entries")
            return cleaned_count
            
        except Exception as e:
            logger.error(f"Error cleaning up completed progress: {str(e)}")
            return 0
    
    def get_progress_analytics(self, hours: int = 24) -> Dict[str, Any]:
        """Get analytics for progress tracking"""
        try:
            analytics = {
                'total_progress': 0,
                'completed_progress': 0,
                'failed_progress': 0,
                'active_progress': 0,
                'avg_completion_time': 0,
                'step_performance': {},
                'user_activity': {}
            }
            
            completion_times = []
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)
            
            if self.redis_client:
                # Scan for progress entries
                pattern = f"progress:*"
                for key in self.redis_client.scan_iter(match=pattern):
                    data = self.redis_client.get(key)
                    if data:
                        progress_data = json.loads(data)
                        
                        # Only include recent entries
                        created_at = progress_data.get('created_at')
                        if created_at:
                            try:
                                created_time = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                                if created_time < cutoff_time:
                                    continue
                            except ValueError:
                                continue
                        
                        # Update analytics
                        analytics['total_progress'] += 1
                        
                        status = progress_data.get('status', 'unknown')
                        if status == 'completed':
                            analytics['completed_progress'] += 1
                            
                            # Calculate completion time
                            completed_at = progress_data.get('completed_at')
                            if completed_at and created_at:
                                try:
                                    completed_time = datetime.fromisoformat(completed_at.replace('Z', '+00:00'))
                                    created_time = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                                    completion_time = (completed_time - created_time).total_seconds()
                                    completion_times.append(completion_time)
                                except ValueError:
                                    pass
                                    
                        elif status == 'failed':
                            analytics['failed_progress'] += 1
                        elif status in ['processing', 'pending']:
                            analytics['active_progress'] += 1
                        
                        # Step performance
                        steps = progress_data.get('steps', [])
                        for step in steps:
                            step_name = step['name']
                            if step_name not in analytics['step_performance']:
                                analytics['step_performance'][step_name] = {
                                    'total': 0,
                                    'completed': 0,
                                    'failed': 0,
                                    'avg_time': 0
                                }
                            
                            analytics['step_performance'][step_name]['total'] += 1
                            if step['status'] == 'completed':
                                analytics['step_performance'][step_name]['completed'] += 1
                            elif step['status'] == 'failed':
                                analytics['step_performance'][step_name]['failed'] += 1
                        
                        # User activity
                        user_id = progress_data.get('user_id')
                        if user_id:
                            analytics['user_activity'][user_id] = analytics['user_activity'].get(user_id, 0) + 1
            else:
                # In-memory analytics
                for key, item in self._memory_storage.items():
                    if key.startswith('progress:') and datetime.utcnow() < item['expires_at']:
                        progress_data = item['data']
                        
                        # Only include recent entries
                        created_at = progress_data.get('created_at')
                        if created_at:
                            try:
                                created_time = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                                if created_time < cutoff_time:
                                    continue
                            except ValueError:
                                continue
                        
                        # Update analytics
                        analytics['total_progress'] += 1
                        
                        status = progress_data.get('status', 'unknown')
                        if status == 'completed':
                            analytics['completed_progress'] += 1
                            
                            # Calculate completion time
                            completed_at = progress_data.get('completed_at')
                            if completed_at and created_at:
                                try:
                                    completed_time = datetime.fromisoformat(completed_at.replace('Z', '+00:00'))
                                    created_time = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                                    completion_time = (completed_time - created_time).total_seconds()
                                    completion_times.append(completion_time)
                                except ValueError:
                                    pass
                                    
                        elif status == 'failed':
                            analytics['failed_progress'] += 1
                        elif status in ['processing', 'pending']:
                            analytics['active_progress'] += 1
                        
                        # Step performance
                        steps = progress_data.get('steps', [])
                        for step in steps:
                            step_name = step['name']
                            if step_name not in analytics['step_performance']:
                                analytics['step_performance'][step_name] = {
                                    'total': 0,
                                    'completed': 0,
                                    'failed': 0,
                                    'avg_time': 0
                                }
                            
                            analytics['step_performance'][step_name]['total'] += 1
                            if step['status'] == 'completed':
                                analytics['step_performance'][step_name]['completed'] += 1
                            elif step['status'] == 'failed':
                                analytics['step_performance'][step_name]['failed'] += 1
                        
                        # User activity
                        user_id = progress_data.get('user_id')
                        if user_id:
                            analytics['user_activity'][user_id] = analytics['user_activity'].get(user_id, 0) + 1
            
            # Calculate average completion time
            if completion_times:
                analytics['avg_completion_time'] = sum(completion_times) / len(completion_times)
            
            # Calculate success rates
            if analytics['total_progress'] > 0:
                analytics['success_rate'] = analytics['completed_progress'] / analytics['total_progress']
                analytics['failure_rate'] = analytics['failed_progress'] / analytics['total_progress']
            else:
                analytics['success_rate'] = 0
                analytics['failure_rate'] = 0
            
            return analytics
            
        except Exception as e:
            logger.error(f"Error getting progress analytics: {str(e)}")
            return {}
    
    def ping(self) -> bool:
        """Health check for the service"""
        try:
            if self.redis_client:
                self.redis_client.ping()
            return True
        except Exception as e:
            logger.error(f"Progress service health check failed: {str(e)}")
            return False 