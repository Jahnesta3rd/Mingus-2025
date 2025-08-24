#!/usr/bin/env python3
"""
MINGUS Article Library - Celery Worker Configuration
===================================================
Worker configuration for different task queues
"""

import os
import sys
from celery import Celery
from celery.bin.celery import main as celery_main

# Add the project root to the Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

def create_worker_app(queue_name: str = None) -> Celery:
    """
    Create a Celery worker app for a specific queue
    
    Args:
        queue_name: Name of the queue to work on
        
    Returns:
        Configured Celery app
    """
    try:
        from backend.celery_app import make_celery
        from backend.app_factory import create_app
        
        flask_app = create_app()
        celery_app = make_celery(flask_app)
        
        if queue_name:
            celery_app.conf.task_routes = {
                f'backend.tasks.{queue_name}.*': {'queue': queue_name}
            }
        
        return celery_app
        
    except ImportError as e:
        print(f"Error importing Flask app: {e}")
        # Fallback to basic Celery setup
        celery_app = Celery('mingus_article_library')
        celery_app.conf.update(
            broker_url='redis://localhost:6379/0',
            result_backend='redis://localhost:6379/0',
            task_serializer='json',
            result_serializer='json',
            accept_content=['json'],
            timezone='UTC',
            enable_utc=True,
        )
        return celery_app

def start_worker(queue_name: str = None, concurrency: int = 4, loglevel: str = 'INFO'):
    """
    Start a Celery worker
    
    Args:
        queue_name: Queue name to work on (None for all queues)
        concurrency: Number of worker processes
        loglevel: Logging level
    """
    celery_app = create_worker_app(queue_name)
    
    # Prepare worker arguments
    worker_args = [
        'worker',
        '--loglevel=' + loglevel,
        '--concurrency=' + str(concurrency),
        '--pool=prefork',
        '--without-gossip',
        '--without-mingle',
        '--without-heartbeat',
    ]
    
    if queue_name:
        worker_args.extend(['--queues=' + queue_name])
    
    # Set the app
    celery_app.set_default()
    
    # Start the worker
    celery_main(worker_args)

def start_beat():
    """Start Celery beat scheduler"""
    try:
        from backend.celery_app import celery
        from celery.schedules import crontab
        
        # Configure periodic tasks
        celery.conf.beat_schedule = {
            'update-user-recommendations': {
                'task': 'backend.celery_app.update_all_user_recommendations',
                'schedule': crontab(hour=2, minute=0),  # Daily at 2 AM
            },
            'generate-daily-analytics': {
                'task': 'backend.celery_app.generate_daily_analytics_report',
                'schedule': crontab(hour=3, minute=0),  # Daily at 3 AM
            },
            'cleanup-old-articles': {
                'task': 'backend.celery_app.cleanup_old_articles',
                'schedule': crontab(hour=4, minute=0, day_of_week=0),  # Weekly on Sunday at 4 AM
            },
            'cleanup-expired-cache': {
                'task': 'backend.celery_app.cleanup_expired_cache',
                'schedule': crontab(minute=0, hour='*/6'),  # Every 6 hours
            },
        }
        
        # Start beat
        celery_main(['beat', '--loglevel=INFO'])
        
    except ImportError as e:
        print(f"Error importing Celery app: {e}")
        sys.exit(1)

def start_flower():
    """Start Flower monitoring"""
    try:
        from backend.celery_app import celery
        
        # Start Flower
        celery_main([
            'flower',
            '--port=5555',
            '--broker=redis://localhost:6379/0',
            '--result-backend=redis://localhost:6379/0',
            '--loglevel=INFO'
        ])
        
    except ImportError as e:
        print(f"Error importing Celery app: {e}")
        sys.exit(1)

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='MINGUS Article Library Celery Worker')
    parser.add_argument('command', choices=['worker', 'beat', 'flower'], 
                       help='Command to run')
    parser.add_argument('--queue', '-q', 
                       choices=['article_processing', 'email_processing', 'ai_classification', 
                               'analytics', 'cleanup', 'recommendations'],
                       help='Queue to work on (for worker command)')
    parser.add_argument('--concurrency', '-c', type=int, default=4,
                       help='Number of worker processes (default: 4)')
    parser.add_argument('--loglevel', '-l', default='INFO',
                       choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                       help='Logging level (default: INFO)')
    
    args = parser.parse_args()
    
    if args.command == 'worker':
        start_worker(args.queue, args.concurrency, args.loglevel)
    elif args.command == 'beat':
        start_beat()
    elif args.command == 'flower':
        start_flower()
