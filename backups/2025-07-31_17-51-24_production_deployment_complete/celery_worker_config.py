"""
Celery Worker Configuration and Monitoring for MINGUS Communication System
Worker settings, monitoring, health checks, and performance optimization
"""

import os
import logging
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from collections import defaultdict

from celery import Celery, current_app
from celery.worker.control import Panel
from celery.utils.log import get_task_logger
from celery.events.state import State
from celery.events.snapshot import Snapshot

logger = get_task_logger(__name__)


@dataclass
class WorkerMetrics:
    """Worker performance metrics"""
    worker_id: str
    active_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    retried_tasks: int = 0
    avg_task_time: float = 0.0
    total_task_time: float = 0.0
    memory_usage: float = 0.0
    cpu_usage: float = 0.0
    queue_depth: Dict[str, int] = field(default_factory=dict)
    last_heartbeat: Optional[datetime] = None
    status: str = 'unknown'
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


class CeleryWorkerManager:
    """
    Celery worker management and monitoring
    Provides worker configuration, health checks, and performance monitoring
    """
    
    def __init__(self, celery_app: Celery = None):
        self.celery_app = celery_app or current_app
        self.workers = {}
        self.metrics = {}
        self.monitoring_enabled = True
        self.health_check_interval = 60  # 1 minute
        self._monitor_thread = None
        self._stop_monitoring = threading.Event()
        self._lock = threading.Lock()
        
        # Performance tracking
        self.performance_stats = {
            'total_tasks_processed': 0,
            'total_task_time': 0.0,
            'average_task_time': 0.0,
            'failed_tasks': 0,
            'retried_tasks': 0,
            'queue_backlog': defaultdict(int)
        }
        
        if self.celery_app:
            self._setup_worker_control()
    
    def _setup_worker_control(self):
        """Setup worker control panel and event monitoring"""
        try:
            # Setup event monitoring
            self.state = State()
            self.snapshot = Snapshot(self.state)
            
            # Register control commands
            self._register_control_commands()
            
            logger.info("Celery worker manager initialized successfully")
            
        except Exception as e:
            logger.error(f"Error setting up worker control: {e}")
    
    def _register_control_commands(self):
        """Register custom control commands for workers"""
        
        @Panel.register
        def worker_stats(state):
            """Get worker statistics"""
            return {
                'active_workers': len(state.active_workers),
                'active_tasks': len(state.active_tasks),
                'total_tasks': len(state.tasks),
                'workers': [
                    {
                        'id': worker.id,
                        'hostname': worker.hostname,
                        'pid': worker.pid,
                        'status': worker.status,
                        'active_tasks': len(worker.active_tasks),
                        'processed_tasks': worker.processed,
                        'load_average': worker.load_average
                    }
                    for worker in state.active_workers.values()
                ]
            }
        
        @Panel.register
        def queue_stats(state):
            """Get queue statistics"""
            return {
                'queues': self._get_queue_stats(),
                'backlog': dict(self.performance_stats['queue_backlog'])
            }
        
        @Panel.register
        def worker_health_check(state):
            """Perform worker health check"""
            return self._perform_health_check()
    
    def _get_queue_stats(self) -> Dict[str, Any]:
        """Get queue statistics"""
        try:
            # Get queue information from broker
            inspect = self.celery_app.control.inspect()
            
            stats = {}
            
            # Active tasks
            active = inspect.active()
            if active:
                for worker, tasks in active.items():
                    for task in tasks:
                        queue = task.get('delivery_info', {}).get('routing_key', 'unknown')
                        if queue not in stats:
                            stats[queue] = {'active': 0, 'reserved': 0, 'scheduled': 0}
                        stats[queue]['active'] += 1
            
            # Reserved tasks
            reserved = inspect.reserved()
            if reserved:
                for worker, tasks in reserved.items():
                    for task in tasks:
                        queue = task.get('delivery_info', {}).get('routing_key', 'unknown')
                        if queue not in stats:
                            stats[queue] = {'active': 0, 'reserved': 0, 'scheduled': 0}
                        stats[queue]['reserved'] += 1
            
            # Scheduled tasks
            scheduled = inspect.scheduled()
            if scheduled:
                for worker, tasks in scheduled.items():
                    for task in tasks:
                        queue = task.get('delivery_info', {}).get('routing_key', 'unknown')
                        if queue not in stats:
                            stats[queue] = {'active': 0, 'reserved': 0, 'scheduled': 0}
                        stats[queue]['scheduled'] += 1
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting queue stats: {e}")
            return {}
    
    def _perform_health_check(self) -> Dict[str, Any]:
        """Perform comprehensive health check"""
        try:
            health_status = {
                'status': 'healthy',
                'workers': {},
                'queues': {},
                'broker': {},
                'errors': []
            }
            
            # Check workers
            inspect = self.celery_app.control.inspect()
            
            # Active workers
            active_workers = inspect.active()
            if active_workers:
                for worker_id, tasks in active_workers.items():
                    health_status['workers'][worker_id] = {
                        'status': 'active',
                        'active_tasks': len(tasks),
                        'last_seen': datetime.utcnow().isoformat()
                    }
            else:
                health_status['status'] = 'degraded'
                health_status['errors'].append('No active workers found')
            
            # Check queues
            queue_stats = self._get_queue_stats()
            for queue_name, stats in queue_stats.items():
                total_tasks = stats.get('active', 0) + stats.get('reserved', 0) + stats.get('scheduled', 0)
                health_status['queues'][queue_name] = {
                    'total_tasks': total_tasks,
                    'active': stats.get('active', 0),
                    'reserved': stats.get('reserved', 0),
                    'scheduled': stats.get('scheduled', 0),
                    'status': 'healthy' if total_tasks < 100 else 'backlogged'
                }
                
                if total_tasks > 1000:
                    health_status['status'] = 'degraded'
                    health_status['errors'].append(f'Queue {queue_name} has high backlog: {total_tasks} tasks')
            
            # Check broker connection
            try:
                # Test broker connection
                self.celery_app.connection().ensure_connection(max_retries=1)
                health_status['broker'] = {
                    'status': 'connected',
                    'last_check': datetime.utcnow().isoformat()
                }
            except Exception as e:
                health_status['broker'] = {
                    'status': 'disconnected',
                    'error': str(e),
                    'last_check': datetime.utcnow().isoformat()
                }
                health_status['status'] = 'unhealthy'
                health_status['errors'].append(f'Broker connection failed: {e}')
            
            return health_status
            
        except Exception as e:
            logger.error(f"Error performing health check: {e}")
            return {
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
    
    def get_worker_config(self, worker_type: str = 'default') -> Dict[str, Any]:
        """
        Get worker configuration for specific type
        
        Args:
            worker_type: Type of worker (default, sms, email, analytics, optimization)
        
        Returns:
            Worker configuration
        """
        base_config = {
            'concurrency': int(os.environ.get('CELERY_WORKER_CONCURRENCY', 4)),
            'max_tasks_per_child': int(os.environ.get('CELERY_WORKER_MAX_TASKS_PER_CHILD', 1000)),
            'prefetch_multiplier': int(os.environ.get('CELERY_WORKER_PREFETCH_MULTIPLIER', 1)),
            'disable_rate_limits': os.environ.get('CELERY_WORKER_DISABLE_RATE_LIMITS', 'false').lower() == 'true',
            'log_level': os.environ.get('CELERY_WORKER_LOG_LEVEL', 'INFO'),
            'loglevel': os.environ.get('CELERY_WORKER_LOG_LEVEL', 'INFO'),
        }
        
        if worker_type == 'sms':
            return {
                **base_config,
                'concurrency': int(os.environ.get('SMS_WORKER_CONCURRENCY', 2)),
                'queues': 'sms_critical,sms_daily',
                'hostname': 'sms-worker@%h',
                'max_tasks_per_child': int(os.environ.get('SMS_WORKER_MAX_TASKS_PER_CHILD', 500)),
                'prefetch_multiplier': 1,
            }
        
        elif worker_type == 'email':
            return {
                **base_config,
                'concurrency': int(os.environ.get('EMAIL_WORKER_CONCURRENCY', 3)),
                'queues': 'email_reports,email_education',
                'hostname': 'email-worker@%h',
                'max_tasks_per_child': int(os.environ.get('EMAIL_WORKER_MAX_TASKS_PER_CHILD', 750)),
                'prefetch_multiplier': 2,
            }
        
        elif worker_type == 'analytics':
            return {
                **base_config,
                'concurrency': int(os.environ.get('ANALYTICS_WORKER_CONCURRENCY', 2)),
                'queues': 'analytics',
                'hostname': 'analytics-worker@%h',
                'max_tasks_per_child': int(os.environ.get('ANALYTICS_WORKER_MAX_TASKS_PER_CHILD', 250)),
                'prefetch_multiplier': 1,
            }
        
        elif worker_type == 'optimization':
            return {
                **base_config,
                'concurrency': int(os.environ.get('OPTIMIZATION_WORKER_CONCURRENCY', 1)),
                'queues': 'optimization',
                'hostname': 'optimization-worker@%h',
                'max_tasks_per_child': int(os.environ.get('OPTIMIZATION_WORKER_MAX_TASKS_PER_CHILD', 100)),
                'prefetch_multiplier': 1,
            }
        
        else:  # default
            return {
                **base_config,
                'queues': 'mingus_tasks,communication_tasks,monitoring',
                'hostname': 'mingus-worker@%h',
            }
    
    def start_worker_monitoring(self):
        """Start worker monitoring"""
        if self._monitor_thread and self._monitor_thread.is_alive():
            return
        
        self._stop_monitoring.clear()
        self._monitor_thread = threading.Thread(target=self._monitor_workers, daemon=True)
        self._monitor_thread.start()
        logger.info("Worker monitoring started")
    
    def stop_worker_monitoring(self):
        """Stop worker monitoring"""
        self._stop_monitoring.set()
        if self._monitor_thread:
            self._monitor_thread.join(timeout=5)
        logger.info("Worker monitoring stopped")
    
    def _monitor_workers(self):
        """Monitor workers in background thread"""
        while not self._stop_monitoring.wait(self.health_check_interval):
            try:
                # Update worker metrics
                self._update_worker_metrics()
                
                # Perform health checks
                health_status = self._perform_health_check()
                
                # Log health status
                if health_status['status'] != 'healthy':
                    logger.warning(f"Worker health check failed: {health_status}")
                
                # Update performance stats
                self._update_performance_stats()
                
            except Exception as e:
                logger.error(f"Error in worker monitoring: {e}")
    
    def _update_worker_metrics(self):
        """Update worker metrics"""
        try:
            inspect = self.celery_app.control.inspect()
            
            # Get active workers
            active_workers = inspect.active()
            if active_workers:
                for worker_id, tasks in active_workers.items():
                    if worker_id not in self.metrics:
                        self.metrics[worker_id] = WorkerMetrics(worker_id=worker_id)
                    
                    metrics = self.metrics[worker_id]
                    metrics.active_tasks = len(tasks)
                    metrics.last_heartbeat = datetime.utcnow()
                    metrics.status = 'active'
                    metrics.updated_at = datetime.utcnow()
            
            # Get stats
            stats = inspect.stats()
            if stats:
                for worker_id, worker_stats in stats.items():
                    if worker_id in self.metrics:
                        metrics = self.metrics[worker_id]
                        metrics.completed_tasks = worker_stats.get('total', {}).get('completed', 0)
                        metrics.failed_tasks = worker_stats.get('total', {}).get('failed', 0)
                        metrics.retried_tasks = worker_stats.get('total', {}).get('retried', 0)
                        
                        # Calculate average task time
                        if metrics.completed_tasks > 0:
                            total_time = worker_stats.get('total', {}).get('time', 0)
                            metrics.avg_task_time = total_time / metrics.completed_tasks
                            metrics.total_task_time = total_time
                        
                        # Get memory and CPU usage if available
                        if 'mem' in worker_stats:
                            metrics.memory_usage = worker_stats['mem']['rss'] / 1024 / 1024  # MB
                        if 'cpu' in worker_stats:
                            metrics.cpu_usage = worker_stats['cpu']['user'] + worker_stats['cpu']['system']
            
            # Update queue depth
            queue_stats = self._get_queue_stats()
            for queue_name, stats in queue_stats.items():
                total_tasks = stats.get('active', 0) + stats.get('reserved', 0) + stats.get('scheduled', 0)
                self.performance_stats['queue_backlog'][queue_name] = total_tasks
                
                # Update worker metrics with queue information
                for worker_id in self.metrics:
                    if worker_id not in self.metrics[worker_id].queue_depth:
                        self.metrics[worker_id].queue_depth[queue_name] = total_tasks
            
        except Exception as e:
            logger.error(f"Error updating worker metrics: {e}")
    
    def _update_performance_stats(self):
        """Update performance statistics"""
        try:
            # Calculate total tasks processed
            total_processed = sum(metrics.completed_tasks for metrics in self.metrics.values())
            total_failed = sum(metrics.failed_tasks for metrics in self.metrics.values())
            total_retried = sum(metrics.retried_tasks for metrics in self.metrics.values())
            total_time = sum(metrics.total_task_time for metrics in self.metrics.values())
            
            self.performance_stats.update({
                'total_tasks_processed': total_processed,
                'total_task_time': total_time,
                'average_task_time': total_time / max(total_processed, 1),
                'failed_tasks': total_failed,
                'retried_tasks': total_retried
            })
            
        except Exception as e:
            logger.error(f"Error updating performance stats: {e}")
    
    def get_worker_metrics(self, worker_id: str = None) -> Dict[str, Any]:
        """Get worker metrics"""
        with self._lock:
            if worker_id:
                return {worker_id: self.metrics.get(worker_id)}
            return self.metrics.copy()
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics"""
        with self._lock:
            return self.performance_stats.copy()
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get worker health status"""
        return self._perform_health_check()
    
    def restart_worker(self, worker_id: str) -> bool:
        """Restart a specific worker"""
        try:
            self.celery_app.control.broadcast('pool_restart', arguments={'reload': True})
            logger.info(f"Restart command sent to worker {worker_id}")
            return True
        except Exception as e:
            logger.error(f"Error restarting worker {worker_id}: {e}")
            return False
    
    def shutdown_worker(self, worker_id: str) -> bool:
        """Shutdown a specific worker"""
        try:
            self.celery_app.control.broadcast('shutdown')
            logger.info(f"Shutdown command sent to worker {worker_id}")
            return True
        except Exception as e:
            logger.error(f"Error shutting down worker {worker_id}: {e}")
            return False


# Global worker manager instance
worker_manager = CeleryWorkerManager()


def get_worker_manager() -> CeleryWorkerManager:
    """Get the global worker manager"""
    return worker_manager


def init_worker_manager(celery_app: Celery = None):
    """Initialize the global worker manager"""
    global worker_manager
    worker_manager = CeleryWorkerManager(celery_app)
    return worker_manager


def get_worker_config(worker_type: str = 'default') -> Dict[str, Any]:
    """Get worker configuration for specific type"""
    manager = get_worker_manager()
    return manager.get_worker_config(worker_type)


def get_worker_health_status() -> Dict[str, Any]:
    """Get worker health status"""
    manager = get_worker_manager()
    return manager.get_health_status()


def get_worker_metrics(worker_id: str = None) -> Dict[str, Any]:
    """Get worker metrics"""
    manager = get_worker_manager()
    return manager.get_worker_metrics(worker_id)


def get_performance_stats() -> Dict[str, Any]:
    """Get performance statistics"""
    manager = get_worker_manager()
    return manager.get_performance_stats()


def start_worker_monitoring():
    """Start worker monitoring"""
    manager = get_worker_manager()
    manager.start_worker_monitoring()


def stop_worker_monitoring():
    """Stop worker monitoring"""
    manager = get_worker_manager()
    manager.stop_worker_monitoring()


# Worker startup scripts
def create_worker_startup_script(worker_type: str = 'default', output_file: str = None):
    """
    Create worker startup script
    
    Args:
        worker_type: Type of worker
        output_file: Output file path (optional)
    """
    config = get_worker_config(worker_type)
    
    script_content = f"""#!/bin/bash
# Celery Worker Startup Script for {worker_type} worker
# Generated on {datetime.utcnow().isoformat()}

# Environment variables
export CELERY_BROKER_URL="{os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/0')}"
export CELERY_RESULT_BACKEND="{os.environ.get('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')}"
export FLASK_ENV="{os.environ.get('FLASK_ENV', 'development')}"

# Worker configuration
WORKER_CONCURRENCY={config['concurrency']}
WORKER_QUEUES="{config.get('queues', 'mingus_tasks')}"
WORKER_HOSTNAME="{config.get('hostname', 'mingus-worker@%h')}"
WORKER_MAX_TASKS_PER_CHILD={config['max_tasks_per_child']}
WORKER_PREFETCH_MULTIPLIER={config['prefetch_multiplier']}

# Start worker
celery -A backend.celery_config.celery_app worker \\
    --loglevel={config['log_level']} \\
    --concurrency=$WORKER_CONCURRENCY \\
    --queues=$WORKER_QUEUES \\
    --hostname=$WORKER_HOSTNAME \\
    --max-tasks-per-child=$WORKER_MAX_TASKS_PER_CHILD \\
    --prefetch-multiplier=$WORKER_PREFETCH_MULTIPLIER \\
    --without-gossip \\
    --without-mingle \\
    --without-heartbeat
"""
    
    if output_file:
        with open(output_file, 'w') as f:
            f.write(script_content)
        os.chmod(output_file, 0o755)
        logger.info(f"Worker startup script created: {output_file}")
    
    return script_content


def create_beat_startup_script(output_file: str = None):
    """
    Create Celery Beat startup script
    
    Args:
        output_file: Output file path (optional)
    """
    script_content = f"""#!/bin/bash
# Celery Beat Startup Script
# Generated on {datetime.utcnow().isoformat()}

# Environment variables
export CELERY_BROKER_URL="{os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/0')}"
export CELERY_RESULT_BACKEND="{os.environ.get('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')}"
export FLASK_ENV="{os.environ.get('FLASK_ENV', 'development')}"

# Start Celery Beat
celery -A backend.celery_config.celery_app beat \\
    --loglevel=INFO \\
    --scheduler=celery.beat.PersistentScheduler \\
    --schedule=/tmp/celerybeat-schedule \\
    --pidfile=/tmp/celerybeat.pid
"""
    
    if output_file:
        with open(output_file, 'w') as f:
            f.write(script_content)
        os.chmod(output_file, 0o755)
        logger.info(f"Beat startup script created: {output_file}")
    
    return script_content


# Export main functions and classes
__all__ = [
    'CeleryWorkerManager',
    'WorkerMetrics',
    'worker_manager',
    'get_worker_manager',
    'init_worker_manager',
    'get_worker_config',
    'get_worker_health_status',
    'get_worker_metrics',
    'get_performance_stats',
    'start_worker_monitoring',
    'stop_worker_monitoring',
    'create_worker_startup_script',
    'create_beat_startup_script'
] 