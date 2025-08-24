#!/usr/bin/env python3
"""
MINGUS Article Library - Celery Management Script
================================================
Comprehensive management script for Celery workers, tasks, and monitoring
"""

import os
import sys
import subprocess
import argparse
import json
import time
from typing import List, Dict, Any, Optional

# Add the project root to the Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

def run_command(command: List[str], background: bool = False) -> subprocess.Popen:
    """
    Run a command and return the process
    
    Args:
        command: Command to run
        background: Whether to run in background
        
    Returns:
        Process object
    """
    if background:
        return subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    else:
        return subprocess.run(command, capture_output=True, text=True)

def check_redis_connection() -> bool:
    """Check if Redis is running and accessible"""
    try:
        result = run_command(['redis-cli', 'ping'])
        return result.returncode == 0 and result.stdout.strip() == 'PONG'
    except FileNotFoundError:
        print("❌ Redis CLI not found. Please install Redis.")
        return False

def start_worker(queue_name: str = None, concurrency: int = 4, loglevel: str = 'INFO', background: bool = False):
    """
    Start a Celery worker
    
    Args:
        queue_name: Queue to work on
        concurrency: Number of worker processes
        loglevel: Logging level
        background: Run in background
    """
    if not check_redis_connection():
        print("❌ Redis is not running. Please start Redis first.")
        return
    
    command = [
        sys.executable, 'backend/celery_worker.py', 'worker',
        '--concurrency', str(concurrency),
        '--loglevel', loglevel
    ]
    
    if queue_name:
        command.extend(['--queue', queue_name])
    
    print(f"🚀 Starting Celery worker...")
    print(f"   Queue: {queue_name or 'all'}")
    print(f"   Concurrency: {concurrency}")
    print(f"   Log level: {loglevel}")
    
    if background:
        process = run_command(command, background=True)
        print(f"✅ Worker started in background (PID: {process.pid})")
        return process
    else:
        result = run_command(command)
        if result.returncode == 0:
            print("✅ Worker completed successfully")
        else:
            print(f"❌ Worker failed: {result.stderr}")

def start_beat(background: bool = False):
    """Start Celery beat scheduler"""
    if not check_redis_connection():
        print("❌ Redis is not running. Please start Redis first.")
        return
    
    command = [sys.executable, 'backend/celery_worker.py', 'beat']
    
    print("⏰ Starting Celery beat scheduler...")
    
    if background:
        process = run_command(command, background=True)
        print(f"✅ Beat scheduler started in background (PID: {process.pid})")
        return process
    else:
        result = run_command(command)
        if result.returncode == 0:
            print("✅ Beat scheduler completed successfully")
        else:
            print(f"❌ Beat scheduler failed: {result.stderr}")

def start_flower(background: bool = False):
    """Start Flower monitoring"""
    if not check_redis_connection():
        print("❌ Redis is not running. Please start Redis first.")
        return
    
    command = [sys.executable, 'backend/celery_worker.py', 'flower']
    
    print("🌸 Starting Flower monitoring...")
    print("   Access at: http://localhost:5555")
    
    if background:
        process = run_command(command, background=True)
        print(f"✅ Flower started in background (PID: {process.pid})")
        return process
    else:
        result = run_command(command)
        if result.returncode == 0:
            print("✅ Flower completed successfully")
        else:
            print(f"❌ Flower failed: {result.stderr}")

def list_tasks() -> List[Dict[str, Any]]:
    """List all available Celery tasks"""
    try:
        from backend.celery_app import celery
        
        tasks = []
        for task_name, task in celery.tasks.items():
            if task_name.startswith('backend.celery_app.'):
                tasks.append({
                    'name': task_name,
                    'queue': getattr(task, 'queue', 'default'),
                    'rate_limit': getattr(task, 'rate_limit', None),
                    'time_limit': getattr(task, 'time_limit', None),
                })
        
        return tasks
    except ImportError as e:
        print(f"❌ Error importing Celery app: {e}")
        return []

def get_task_status(task_id: str) -> Dict[str, Any]:
    """Get the status of a specific task"""
    try:
        from backend.celery_app import get_task_status as celery_get_status
        return celery_get_status(task_id)
    except ImportError as e:
        print(f"❌ Error importing Celery app: {e}")
        return {'error': str(e)}

def inspect_workers() -> Dict[str, Any]:
    """Inspect Celery workers"""
    try:
        from backend.celery_app import celery
        
        inspector = celery.control.inspect()
        
        stats = inspector.stats()
        active_tasks = inspector.active()
        registered_tasks = inspector.registered()
        
        return {
            'stats': stats,
            'active_tasks': active_tasks,
            'registered_tasks': registered_tasks
        }
    except ImportError as e:
        print(f"❌ Error importing Celery app: {e}")
        return {}

def purge_queues():
    """Purge all Celery queues"""
    if not check_redis_connection():
        print("❌ Redis is not running. Please start Redis first.")
        return
    
    try:
        from backend.celery_app import celery
        celery.control.purge()
        print("✅ All queues purged successfully")
    except ImportError as e:
        print(f"❌ Error importing Celery app: {e}")

def show_queue_stats():
    """Show queue statistics"""
    if not check_redis_connection():
        print("❌ Redis is not running. Please start Redis first.")
        return
    
    try:
        import redis
        
        r = redis.Redis(host='localhost', port=6379, db=0)
        
        queues = ['article_processing', 'email_processing', 'ai_classification', 
                 'analytics', 'cleanup', 'recommendations']
        
        print("📊 Queue Statistics:")
        print("-" * 50)
        
        for queue in queues:
            length = r.llen(f'celery:{queue}')
            print(f"{queue:20} | {length:5} tasks")
        
        print("-" * 50)
        
    except ImportError:
        print("❌ Redis Python client not installed")
    except Exception as e:
        print(f"❌ Error getting queue stats: {e}")

def test_task():
    """Test Celery task execution"""
    if not check_redis_connection():
        print("❌ Redis is not running. Please start Redis first.")
        return
    
    try:
        from backend.celery_app import celery
        
        # Test a simple task
        result = celery.send_task('backend.celery_app.cleanup_expired_cache')
        print(f"✅ Test task submitted: {result.id}")
        
        # Wait for result
        print("⏳ Waiting for task completion...")
        task_result = result.get(timeout=30)
        print(f"✅ Task completed: {task_result}")
        
    except ImportError as e:
        print(f"❌ Error importing Celery app: {e}")
    except Exception as e:
        print(f"❌ Error testing task: {e}")

def create_supervisor_config():
    """Create supervisor configuration for Celery processes"""
    config = """[program:mingus-celery-worker]
command=python manage_celery.py worker --background
directory=/path/to/mingus/project
user=mingus
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/mingus/celery-worker.log

[program:mingus-celery-beat]
command=python manage_celery.py beat --background
directory=/path/to/mingus/project
user=mingus
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/mingus/celery-beat.log

[program:mingus-flower]
command=python manage_celery.py flower --background
directory=/path/to/mingus/project
user=mingus
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/mingus/flower.log

[group:mingus-celery]
programs=mingus-celery-worker,mingus-celery-beat,mingus-flower
"""
    
    with open('supervisor-celery.conf', 'w') as f:
        f.write(config)
    
    print("✅ Supervisor configuration created: supervisor-celery.conf")
    print("📝 Please update the paths and user in the configuration file")

def create_systemd_service():
    """Create systemd service files for Celery processes"""
    worker_service = """[Unit]
Description=MINGUS Article Library Celery Worker
After=network.target redis.service

[Service]
Type=simple
User=mingus
Group=mingus
WorkingDirectory=/path/to/mingus/project
Environment=PATH=/path/to/mingus/venv/bin
ExecStart=/path/to/mingus/venv/bin/python manage_celery.py worker
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
"""
    
    beat_service = """[Unit]
Description=MINGUS Article Library Celery Beat
After=network.target redis.service

[Service]
Type=simple
User=mingus
Group=mingus
WorkingDirectory=/path/to/mingus/project
Environment=PATH=/path/to/mingus/venv/bin
ExecStart=/path/to/mingus/venv/bin/python manage_celery.py beat
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
"""
    
    with open('mingus-celery-worker.service', 'w') as f:
        f.write(worker_service)
    
    with open('mingus-celery-beat.service', 'w') as f:
        f.write(beat_service)
    
    print("✅ Systemd service files created:")
    print("   - mingus-celery-worker.service")
    print("   - mingus-celery-beat.service")
    print("📝 Please update the paths and user in the service files")

def main():
    parser = argparse.ArgumentParser(description='MINGUS Article Library Celery Management')
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Worker command
    worker_parser = subparsers.add_parser('worker', help='Start Celery worker')
    worker_parser.add_argument('--queue', '-q', 
                              choices=['article_processing', 'email_processing', 'ai_classification', 
                                      'analytics', 'cleanup', 'recommendations'],
                              help='Queue to work on')
    worker_parser.add_argument('--concurrency', '-c', type=int, default=4,
                              help='Number of worker processes')
    worker_parser.add_argument('--loglevel', '-l', default='INFO',
                              choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                              help='Logging level')
    worker_parser.add_argument('--background', '-b', action='store_true',
                              help='Run in background')
    
    # Beat command
    beat_parser = subparsers.add_parser('beat', help='Start Celery beat scheduler')
    beat_parser.add_argument('--background', '-b', action='store_true',
                            help='Run in background')
    
    # Flower command
    flower_parser = subparsers.add_parser('flower', help='Start Flower monitoring')
    flower_parser.add_argument('--background', '-b', action='store_true',
                              help='Run in background')
    
    # Other commands
    subparsers.add_parser('tasks', help='List available tasks')
    subparsers.add_parser('status', help='Show worker status')
    subparsers.add_parser('queues', help='Show queue statistics')
    subparsers.add_parser('purge', help='Purge all queues')
    subparsers.add_parser('test', help='Test task execution')
    subparsers.add_parser('supervisor', help='Create supervisor configuration')
    subparsers.add_parser('systemd', help='Create systemd service files')
    
    # Task status command
    status_parser = subparsers.add_parser('task-status', help='Get task status')
    status_parser.add_argument('task_id', help='Task ID to check')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    if args.command == 'worker':
        start_worker(args.queue, args.concurrency, args.loglevel, args.background)
    elif args.command == 'beat':
        start_beat(args.background)
    elif args.command == 'flower':
        start_flower(args.background)
    elif args.command == 'tasks':
        tasks = list_tasks()
        if tasks:
            print("📋 Available Tasks:")
            print("-" * 80)
            for task in tasks:
                print(f"{task['name']:40} | {task['queue']:15} | {task['rate_limit'] or 'No limit'}")
        else:
            print("❌ No tasks found")
    elif args.command == 'status':
        status = inspect_workers()
        if status:
            print("🔍 Worker Status:")
            print(json.dumps(status, indent=2))
        else:
            print("❌ No workers found")
    elif args.command == 'queues':
        show_queue_stats()
    elif args.command == 'purge':
        purge_queues()
    elif args.command == 'test':
        test_task()
    elif args.command == 'task-status':
        status = get_task_status(args.task_id)
        print("📊 Task Status:")
        print(json.dumps(status, indent=2))
    elif args.command == 'supervisor':
        create_supervisor_config()
    elif args.command == 'systemd':
        create_systemd_service()

if __name__ == '__main__':
    main()
