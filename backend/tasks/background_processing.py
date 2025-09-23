#!/usr/bin/env python3
"""
Mingus Application - Background Processing Module
Comprehensive background processing for Daily Outlook system performance
"""

import asyncio
import logging
from datetime import datetime, date, timedelta
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass
from enum import Enum
import json
import time
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import redis
from celery import Celery
from celery.schedules import crontab
import psutil
import gc

# Configure logging
logger = logging.getLogger(__name__)

class TaskPriority(Enum):
    """Task priority levels"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4

@dataclass
class BackgroundTask:
    """Background task definition"""
    task_id: str
    task_type: str
    priority: TaskPriority
    payload: Dict[str, Any]
    created_at: datetime
    scheduled_for: Optional[datetime] = None
    max_retries: int = 3
    retry_count: int = 0
    status: str = 'pending'

class CacheWarmingScheduler:
    """
    Intelligent cache warming scheduler
    
    Features:
    - Predictive cache warming based on user patterns
    - Tier-based warming strategies
    - Resource-aware scheduling
    - Performance monitoring
    """
    
    def __init__(self, redis_client, db_session):
        """
        Initialize cache warming scheduler
        
        Args:
            redis_client: Redis client for cache operations
            db_session: Database session
        """
        self.redis = redis_client
        self.db = db_session
        self.warming_stats = {
            'total_warmed': 0,
            'successful_warming': 0,
            'failed_warming': 0,
            'avg_warming_time': 0.0
        }
    
    async def schedule_daily_outlook_warming(self, target_date: date = None):
        """
        Schedule daily outlook cache warming
        
        Args:
            target_date: Date to warm cache for (defaults to tomorrow)
        """
        if target_date is None:
            target_date = date.today() + timedelta(days=1)
        
        logger.info(f"Scheduling daily outlook cache warming for {target_date}")
        
        try:
            # Get active users for warming
            active_users = await self._get_active_users()
            
            # Group users by tier for tier-based warming
            users_by_tier = self._group_users_by_tier(active_users)
            
            # Schedule warming tasks by tier
            for tier, users in users_by_tier.items():
                await self._schedule_tier_warming(tier, users, target_date)
            
            logger.info(f"Scheduled cache warming for {len(active_users)} users")
            
        except Exception as e:
            logger.error(f"Error scheduling daily outlook warming: {e}")
    
    async def _get_active_users(self) -> List[Dict[str, Any]]:
        """Get active users for cache warming"""
        try:
            # Get users active in last 30 days
            query = """
                SELECT u.id, u.tier, u.location, u.created_at,
                       COUNT(do.id) as outlook_count,
                       MAX(do.created_at) as last_outlook
                FROM users u
                LEFT JOIN daily_outlooks do ON u.id = do.user_id
                WHERE u.created_at >= :cutoff_date
                GROUP BY u.id, u.tier, u.location, u.created_at
                HAVING COUNT(do.id) > 0 OR u.created_at >= :recent_cutoff
                ORDER BY u.created_at DESC
                LIMIT 1000
            """
            
            cutoff_date = datetime.now() - timedelta(days=30)
            recent_cutoff = datetime.now() - timedelta(days=7)
            
            result = self.db.execute(query, {
                'cutoff_date': cutoff_date,
                'recent_cutoff': recent_cutoff
            })
            
            return [dict(row._mapping) for row in result.fetchall()]
            
        except Exception as e:
            logger.error(f"Error getting active users: {e}")
            return []
    
    def _group_users_by_tier(self, users: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Group users by tier"""
        users_by_tier = defaultdict(list)
        for user in users:
            tier = user.get('tier', 'budget')
            users_by_tier[tier].append(user)
        return users_by_tier
    
    async def _schedule_tier_warming(self, tier: str, users: List[Dict[str, Any]], target_date: date):
        """Schedule cache warming for users in a specific tier"""
        logger.info(f"Scheduling cache warming for {len(users)} {tier} users")
        
        # Tier-based warming strategies
        warming_config = {
            'budget': {'batch_size': 50, 'delay_between_batches': 2},
            'mid_tier': {'batch_size': 30, 'delay_between_batches': 1},
            'professional': {'batch_size': 20, 'delay_between_batches': 0.5}
        }
        
        config = warming_config.get(tier, warming_config['budget'])
        batch_size = config['batch_size']
        delay = config['delay_between_batches']
        
        # Process users in batches
        for i in range(0, len(users), batch_size):
            batch = users[i:i + batch_size]
            await self._warm_user_batch(batch, target_date)
            
            # Add delay between batches to prevent resource exhaustion
            if i + batch_size < len(users):
                await asyncio.sleep(delay)
    
    async def _warm_user_batch(self, users: List[Dict[str, Any]], target_date: date):
        """Warm cache for a batch of users"""
        start_time = time.time()
        
        try:
            # Warm daily outlook cache for each user
            for user in users:
                await self._warm_user_daily_outlook(user['id'], target_date)
            
            # Update warming statistics
            warming_time = time.time() - start_time
            self.warming_stats['total_warmed'] += len(users)
            self.warming_stats['successful_warming'] += len(users)
            self.warming_stats['avg_warming_time'] = (
                (self.warming_stats['avg_warming_time'] * (self.warming_stats['successful_warming'] - len(users)) + warming_time) 
                / self.warming_stats['successful_warming']
            )
            
            logger.info(f"Warmed cache for {len(users)} users in {warming_time:.2f}s")
            
        except Exception as e:
            logger.error(f"Error warming user batch: {e}")
            self.warming_stats['failed_warming'] += len(users)
    
    async def _warm_user_daily_outlook(self, user_id: int, target_date: date):
        """Warm daily outlook cache for a specific user"""
        try:
            # Generate daily outlook content (this would call the actual service)
            from backend.services.daily_outlook_content_service import DailyOutlookContentService
            from backend.services.cache_manager import cache_manager, CacheStrategy
            
            content_service = DailyOutlookContentService()
            daily_outlook = content_service.generate_daily_outlook(user_id)
            
            # Cache the generated content
            cache_key = f"{user_id}:{target_date.isoformat()}"
            cache_manager.set(
                CacheStrategy.DAILY_OUTLOOK,
                str(user_id),
                daily_outlook,
                {"date": target_date.isoformat()}
            )
            
            logger.debug(f"Warmed daily outlook cache for user {user_id}")
            
        except Exception as e:
            logger.error(f"Error warming daily outlook for user {user_id}: {e}")

class AnalyticsPreComputer:
    """
    Pre-computation service for complex analytics
    
    Features:
    - Balance score pre-computation
    - Peer comparison data generation
    - User aggregation calculations
    - Performance trend analysis
    """
    
    def __init__(self, redis_client, db_session):
        """
        Initialize analytics pre-computer
        
        Args:
            redis_client: Redis client for cache operations
            db_session: Database session
        """
        self.redis = redis_client
        self.db = db_session
        self.precompute_stats = {
            'total_precomputed': 0,
            'successful_precompute': 0,
            'failed_precompute': 0,
            'avg_precompute_time': 0.0
        }
    
    async def precompute_balance_scores(self, user_ids: List[int] = None):
        """
        Pre-compute balance scores for users
        
        Args:
            user_ids: Specific user IDs to pre-compute (if None, compute for all active users)
        """
        logger.info("Starting balance score pre-computation")
        
        try:
            if user_ids is None:
                user_ids = await self._get_users_for_precompute()
            
            # Process users in batches
            batch_size = 20
            for i in range(0, len(user_ids), batch_size):
                batch = user_ids[i:i + batch_size]
                await self._precompute_batch_balance_scores(batch)
                
                # Add delay between batches
                if i + batch_size < len(user_ids):
                    await asyncio.sleep(1)
            
            logger.info(f"Completed balance score pre-computation for {len(user_ids)} users")
            
        except Exception as e:
            logger.error(f"Error in balance score pre-computation: {e}")
    
    async def _get_users_for_precompute(self) -> List[int]:
        """Get user IDs for pre-computation"""
        try:
            query = """
                SELECT DISTINCT u.id
                FROM users u
                WHERE u.created_at >= :cutoff_date
                ORDER BY u.id
            """
            
            cutoff_date = datetime.now() - timedelta(days=30)
            result = self.db.execute(query, {'cutoff_date': cutoff_date})
            
            return [row[0] for row in result.fetchall()]
            
        except Exception as e:
            logger.error(f"Error getting users for pre-compute: {e}")
            return []
    
    async def _precompute_batch_balance_scores(self, user_ids: List[int]):
        """Pre-compute balance scores for a batch of users"""
        start_time = time.time()
        
        try:
            # Import services
            from backend.services.daily_outlook_service import DailyOutlookService
            from backend.services.cache_manager import cache_manager, CacheStrategy
            
            daily_outlook_service = DailyOutlookService()
            
            # Pre-compute balance scores
            for user_id in user_ids:
                try:
                    # Calculate balance score
                    balance_score, individual_scores = daily_outlook_service.calculate_balance_score(user_id)
                    
                    # Cache the results
                    cache_data = {
                        'balance_score': balance_score,
                        'individual_scores': individual_scores,
                        'computed_at': datetime.now().isoformat()
                    }
                    
                    cache_manager.set(
                        CacheStrategy.USER_BALANCE_SCORE,
                        str(user_id),
                        cache_data
                    )
                    
                except Exception as e:
                    logger.error(f"Error pre-computing balance score for user {user_id}: {e}")
                    continue
            
            # Update statistics
            precompute_time = time.time() - start_time
            self.precompute_stats['total_precomputed'] += len(user_ids)
            self.precompute_stats['successful_precompute'] += len(user_ids)
            self.precompute_stats['avg_precompute_time'] = (
                (self.precompute_stats['avg_precompute_time'] * (self.precompute_stats['successful_precompute'] - len(user_ids)) + precompute_time) 
                / self.precompute_stats['successful_precompute']
            )
            
            logger.info(f"Pre-computed balance scores for {len(user_ids)} users in {precompute_time:.2f}s")
            
        except Exception as e:
            logger.error(f"Error in batch balance score pre-computation: {e}")
            self.precompute_stats['failed_precompute'] += len(user_ids)
    
    async def precompute_peer_comparison_data(self, target_date: date = None):
        """
        Pre-compute peer comparison data
        
        Args:
            target_date: Date to compute peer data for
        """
        if target_date is None:
            target_date = date.today()
        
        logger.info(f"Pre-computing peer comparison data for {target_date}")
        
        try:
            # Get users grouped by tier and location
            user_groups = await self._get_user_groups_for_peer_comparison()
            
            # Pre-compute peer data for each group
            for group_key, users in user_groups.items():
                await self._precompute_peer_group_data(group_key, users, target_date)
            
            logger.info(f"Completed peer comparison pre-computation for {len(user_groups)} groups")
            
        except Exception as e:
            logger.error(f"Error in peer comparison pre-computation: {e}")
    
    async def _get_user_groups_for_peer_comparison(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get user groups for peer comparison"""
        try:
            query = """
                SELECT u.id, u.tier, u.location, do.balance_score,
                       do.financial_weight, do.wellness_weight,
                       do.relationship_weight, do.career_weight
                FROM users u
                JOIN daily_outlooks do ON u.id = do.user_id
                WHERE do.date = :target_date
                ORDER BY u.tier, u.location, do.balance_score DESC
            """
            
            target_date = date.today()
            result = self.db.execute(query, {'target_date': target_date})
            
            # Group by tier and location
            groups = defaultdict(list)
            for row in result.fetchall():
                group_key = f"{row.tier}:{row.location}"
                groups[group_key].append(dict(row._mapping))
            
            return groups
            
        except Exception as e:
            logger.error(f"Error getting user groups for peer comparison: {e}")
            return {}
    
    async def _precompute_peer_group_data(self, group_key: str, users: List[Dict[str, Any]], target_date: date):
        """Pre-compute peer comparison data for a group"""
        try:
            from backend.services.cache_manager import cache_manager, CacheStrategy
            
            # Calculate peer statistics
            balance_scores = [user['balance_score'] for user in users]
            avg_balance = sum(balance_scores) / len(balance_scores) if balance_scores else 0
            
            peer_data = {
                'group_key': group_key,
                'user_count': len(users),
                'avg_balance_score': avg_balance,
                'min_balance_score': min(balance_scores) if balance_scores else 0,
                'max_balance_score': max(balance_scores) if balance_scores else 0,
                'percentiles': self._calculate_percentiles(balance_scores),
                'computed_at': datetime.now().isoformat()
            }
            
            # Cache peer comparison data
            cache_manager.set(
                CacheStrategy.PEER_COMPARISON,
                group_key,
                peer_data,
                {"date": target_date.isoformat()}
            )
            
            logger.debug(f"Pre-computed peer data for group {group_key}")
            
        except Exception as e:
            logger.error(f"Error pre-computing peer group data for {group_key}: {e}")
    
    def _calculate_percentiles(self, scores: List[float]) -> Dict[str, float]:
        """Calculate percentiles for balance scores"""
        if not scores:
            return {}
        
        sorted_scores = sorted(scores)
        n = len(sorted_scores)
        
        return {
            'p25': sorted_scores[int(n * 0.25)] if n > 0 else 0,
            'p50': sorted_scores[int(n * 0.50)] if n > 0 else 0,
            'p75': sorted_scores[int(n * 0.75)] if n > 0 else 0,
            'p90': sorted_scores[int(n * 0.90)] if n > 0 else 0,
            'p95': sorted_scores[int(n * 0.95)] if n > 0 else 0
        }

class BackgroundTaskScheduler:
    """
    Background task scheduler with priority queue
    
    Features:
    - Priority-based task scheduling
    - Resource monitoring and throttling
    - Task retry logic
    - Performance monitoring
    """
    
    def __init__(self, redis_client, max_workers: int = 4):
        """
        Initialize background task scheduler
        
        Args:
            redis_client: Redis client for task queue
            max_workers: Maximum number of worker threads
        """
        self.redis = redis_client
        self.max_workers = max_workers
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.task_queue = asyncio.Queue()
        self.running_tasks = {}
        self.task_stats = {
            'total_tasks': 0,
            'completed_tasks': 0,
            'failed_tasks': 0,
            'avg_task_time': 0.0
        }
    
    async def schedule_task(self, task: BackgroundTask):
        """
        Schedule a background task
        
        Args:
            task: Background task to schedule
        """
        try:
            # Add task to queue
            await self.task_queue.put(task)
            self.task_stats['total_tasks'] += 1
            
            logger.info(f"Scheduled task {task.task_id} with priority {task.priority.name}")
            
        except Exception as e:
            logger.error(f"Error scheduling task {task.task_id}: {e}")
    
    async def start_scheduler(self):
        """Start the background task scheduler"""
        logger.info("Starting background task scheduler")
        
        # Start worker coroutines
        workers = [
            asyncio.create_task(self._worker(f"worker-{i}"))
            for i in range(self.max_workers)
        ]
        
        # Wait for all workers
        await asyncio.gather(*workers)
    
    async def _worker(self, worker_name: str):
        """Background task worker"""
        logger.info(f"Started worker {worker_name}")
        
        while True:
            try:
                # Get task from queue
                task = await self.task_queue.get()
                
                # Process task
                await self._process_task(task, worker_name)
                
                # Mark task as done
                self.task_queue.task_done()
                
            except Exception as e:
                logger.error(f"Worker {worker_name} error: {e}")
                await asyncio.sleep(1)  # Brief pause before retrying
    
    async def _process_task(self, task: BackgroundTask, worker_name: str):
        """Process a background task"""
        start_time = time.time()
        task_id = task.task_id
        
        try:
            logger.info(f"Processing task {task_id} on {worker_name}")
            
            # Execute task based on type
            if task.task_type == 'cache_warming':
                await self._execute_cache_warming_task(task)
            elif task.task_type == 'analytics_precompute':
                await self._execute_analytics_precompute_task(task)
            elif task.task_type == 'peer_comparison':
                await self._execute_peer_comparison_task(task)
            else:
                logger.warning(f"Unknown task type: {task.task_type}")
                return
            
            # Update task statistics
            task_time = time.time() - start_time
            self.task_stats['completed_tasks'] += 1
            self.task_stats['avg_task_time'] = (
                (self.task_stats['avg_task_time'] * (self.task_stats['completed_tasks'] - 1) + task_time) 
                / self.task_stats['completed_tasks']
            )
            
            logger.info(f"Completed task {task_id} in {task_time:.2f}s")
            
        except Exception as e:
            logger.error(f"Error processing task {task_id}: {e}")
            self.task_stats['failed_tasks'] += 1
            
            # Retry logic
            if task.retry_count < task.max_retries:
                task.retry_count += 1
                task.status = 'retrying'
                await self.schedule_task(task)
                logger.info(f"Retrying task {task_id} (attempt {task.retry_count})")
            else:
                logger.error(f"Task {task_id} failed after {task.max_retries} retries")
    
    async def _execute_cache_warming_task(self, task: BackgroundTask):
        """Execute cache warming task"""
        # Implementation would call cache warming scheduler
        await asyncio.sleep(0.1)  # Simulate work
    
    async def _execute_analytics_precompute_task(self, task: BackgroundTask):
        """Execute analytics pre-computation task"""
        # Implementation would call analytics pre-computer
        await asyncio.sleep(0.1)  # Simulate work
    
    async def _execute_peer_comparison_task(self, task: BackgroundTask):
        """Execute peer comparison task"""
        # Implementation would call peer comparison pre-computer
        await asyncio.sleep(0.1)  # Simulate work
    
    def get_task_statistics(self) -> Dict[str, Any]:
        """Get task processing statistics"""
        return {
            'total_tasks': self.task_stats['total_tasks'],
            'completed_tasks': self.task_stats['completed_tasks'],
            'failed_tasks': self.task_stats['failed_tasks'],
            'success_rate': (
                self.task_stats['completed_tasks'] / self.task_stats['total_tasks'] * 100
                if self.task_stats['total_tasks'] > 0 else 0
            ),
            'avg_task_time': round(self.task_stats['avg_task_time'], 2),
            'queue_size': self.task_queue.qsize(),
            'running_tasks': len(self.running_tasks)
        }
    
    def close(self):
        """Close the task scheduler"""
        if self.executor:
            self.executor.shutdown(wait=True)
        
        logger.info("Background task scheduler closed")

# Celery task definitions for scheduled background processing
def make_celery(app=None):
    """Create Celery instance for background processing"""
    celery = Celery(
        'mingus_background_processing',
        broker='redis://localhost:6379/1',
        backend='redis://localhost:6379/1'
    )
    
    # Configure Celery
    celery.conf.update(
        task_serializer='json',
        accept_content=['json'],
        result_serializer='json',
        timezone='UTC',
        enable_utc=True,
        task_track_started=True,
        task_time_limit=300,  # 5 minutes
        task_soft_time_limit=240,  # 4 minutes
        worker_prefetch_multiplier=1,
        task_acks_late=True
    )
    
    return celery

celery_app = make_celery()

@celery_app.task(bind=True, max_retries=3)
def scheduled_cache_warming(self, target_date_str: str = None):
    """Scheduled cache warming task"""
    try:
        target_date = datetime.strptime(target_date_str, '%Y-%m-%d').date() if target_date_str else date.today() + timedelta(days=1)
        
        # Initialize cache warming scheduler
        from backend.services.cache_manager import cache_manager
        from backend.models.database import db
        
        warming_scheduler = CacheWarmingScheduler(cache_manager.redis_client, db.session)
        
        # Run cache warming
        asyncio.run(warming_scheduler.schedule_daily_outlook_warming(target_date))
        
        return f"Cache warming completed for {target_date}"
        
    except Exception as e:
        logger.error(f"Cache warming task failed: {e}")
        raise self.retry(countdown=60, exc=e)

@celery_app.task(bind=True, max_retries=3)
def scheduled_analytics_precompute(self):
    """Scheduled analytics pre-computation task"""
    try:
        # Initialize analytics pre-computer
        from backend.services.cache_manager import cache_manager
        from backend.models.database import db
        
        analytics_precomputer = AnalyticsPreComputer(cache_manager.redis_client, db.session)
        
        # Run analytics pre-computation
        asyncio.run(analytics_precomputer.precompute_balance_scores())
        asyncio.run(analytics_precomputer.precompute_peer_comparison_data())
        
        return "Analytics pre-computation completed"
        
    except Exception as e:
        logger.error(f"Analytics pre-computation task failed: {e}")
        raise self.retry(countdown=60, exc=e)

# Celery beat schedule for automated background processing
celery_app.conf.beat_schedule = {
    'daily-cache-warming': {
        'task': 'backend.tasks.background_processing.scheduled_cache_warming',
        'schedule': crontab(hour=5, minute=0),  # 5:00 AM UTC daily
        'args': ()
    },
    'analytics-precompute': {
        'task': 'backend.tasks.background_processing.scheduled_analytics_precompute',
        'schedule': crontab(hour=2, minute=0),  # 2:00 AM UTC daily
        'args': ()
    },
    'hourly-cache-refresh': {
        'task': 'backend.tasks.background_processing.scheduled_cache_warming',
        'schedule': crontab(minute=0),  # Every hour
        'args': ()
    }
}
