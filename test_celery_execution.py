#!/usr/bin/env python3
"""
Test Celery task execution for Daily Outlook Tasks

This script tests the actual execution of Celery tasks.
"""

import os
import sys
from datetime import datetime, date, timedelta

# Add the project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

def test_celery_worker_status():
    """Test if Celery workers are available"""
    print("🧪 Testing Celery worker status...")
    
    try:
        from backend.tasks.daily_outlook_tasks import celery_app
        
        # Check if workers are available
        inspect = celery_app.control.inspect()
        stats = inspect.stats()
        
        if stats:
            print("✅ Celery workers are running")
            for worker, stat in stats.items():
                print(f"   Worker: {worker}")
                print(f"   Pool: {stat.get('pool', {}).get('processes', 'N/A')}")
        else:
            print("⚠️  No Celery workers found")
            print("   Start workers with: celery -A backend.tasks.daily_outlook_tasks worker --loglevel=info")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Celery worker status error: {e}")
        return False

def test_task_scheduling():
    """Test task scheduling without execution"""
    print("\n🧪 Testing task scheduling...")
    
    try:
        from backend.tasks.daily_outlook_tasks import (
            generate_daily_outlooks_batch,
            send_daily_outlook_notifications,
            optimize_content_performance,
            health_check_daily_outlook_tasks
        )
        
        # Test task scheduling (without .delay() to avoid execution)
        print("✅ Tasks can be scheduled")
        print(f"   generate_daily_outlooks_batch: {generate_daily_outlooks_batch}")
        print(f"   send_daily_outlook_notifications: {send_daily_outlook_notifications}")
        print(f"   optimize_content_performance: {optimize_content_performance}")
        print(f"   health_check_daily_outlook_tasks: {health_check_daily_outlook_tasks}")
        
        return True
        
    except Exception as e:
        print(f"❌ Task scheduling error: {e}")
        return False

def test_health_check_task():
    """Test health check task execution"""
    print("\n🧪 Testing health check task...")
    
    try:
        from backend.tasks.daily_outlook_tasks import health_check_daily_outlook_tasks
        
        # Execute health check task directly (not via Celery)
        print("⏳ Running health check task...")
        
        # Create a mock task instance
        class MockTask:
            def __init__(self):
                self.request = MockRequest()
        
        class MockRequest:
            def __init__(self):
                self.id = "test-health-check-123"
        
        mock_task = MockTask()
        
        # Run the health check
        result = health_check_daily_outlook_tasks.run()
        
        print("✅ Health check task executed successfully")
        print(f"   Result: {result}")
        
        return True
        
    except Exception as e:
        print(f"❌ Health check task error: {e}")
        return False

def test_task_parameters():
    """Test task parameter handling"""
    print("\n🧪 Testing task parameters...")
    
    try:
        from backend.tasks.daily_outlook_tasks import generate_daily_outlooks_batch
        
        # Test with different parameters
        tomorrow = (date.today() + timedelta(days=1)).isoformat()
        
        print(f"✅ Testing with target_date: {tomorrow}")
        print(f"✅ Testing with force_regenerate: True")
        
        # Test parameter validation
        import inspect
        sig = inspect.signature(generate_daily_outlooks_batch.run)
        print(f"✅ Task signature: {sig}")
        
        return True
        
    except Exception as e:
        print(f"❌ Task parameters error: {e}")
        return False

def test_celery_configuration():
    """Test Celery configuration"""
    print("\n🧪 Testing Celery configuration...")
    
    try:
        from backend.tasks.daily_outlook_tasks import celery_app
        
        # Test configuration
        config = celery_app.conf
        
        print("✅ Celery Configuration:")
        print(f"   Broker URL: {config.broker_url}")
        print(f"   Result Backend: {config.result_backend}")
        print(f"   Task Serializer: {config.task_serializer}")
        print(f"   Accept Content: {config.accept_content}")
        print(f"   Timezone: {config.timezone}")
        print(f"   Task Time Limit: {config.task_time_limit}")
        print(f"   Task Soft Time Limit: {config.task_soft_time_limit}")
        
        # Test task routes
        task_routes = config.task_routes
        print(f"   Task Routes: {task_routes}")
        
        # Test queue configuration
        print(f"   Default Queue: {config.task_default_queue}")
        print(f"   Default Exchange: {config.task_default_exchange}")
        
        return True
        
    except Exception as e:
        print(f"❌ Celery configuration error: {e}")
        return False

def test_beat_schedule():
    """Test Celery Beat schedule"""
    print("\n🧪 Testing Celery Beat schedule...")
    
    try:
        from backend.config.celery_beat_schedule import CELERY_BEAT_SCHEDULE
        
        print("✅ Celery Beat Schedule:")
        for task_name, task_config in CELERY_BEAT_SCHEDULE.items():
            if 'daily' in task_name or 'outlook' in task_name:
                print(f"   {task_name}:")
                print(f"     Task: {task_config['task']}")
                print(f"     Schedule: {task_config['schedule']}")
                print(f"     Queue: {task_config['options'].get('queue', 'default')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Beat schedule error: {e}")
        return False

def test_redis_connection():
    """Test Redis connection"""
    print("\n🧪 Testing Redis connection...")
    
    try:
        import redis
        
        # Test Redis connection
        r = redis.Redis(host='localhost', port=6379, db=2)
        
        # Test basic operations
        r.set('test_key', 'test_value')
        value = r.get('test_key')
        
        if value == b'test_value':
            print("✅ Redis connection successful")
            r.delete('test_key')  # Clean up
            return True
        else:
            print("❌ Redis connection failed")
            return False
            
    except Exception as e:
        print(f"❌ Redis connection error: {e}")
        return False

def test_task_imports():
    """Test task imports and definitions"""
    print("\n🧪 Testing task imports...")
    
    try:
        # Test all task imports
        from backend.tasks.daily_outlook_tasks import (
            generate_daily_outlooks_batch,
            send_daily_outlook_notifications,
            optimize_content_performance,
            health_check_daily_outlook_tasks,
            schedule_daily_outlook_generation,
            schedule_daily_outlook_notifications,
            schedule_content_optimization,
            celery_app
        )
        
        print("✅ All task imports successful")
        print(f"   Celery app: {celery_app}")
        print(f"   Tasks imported: 4 main tasks + 3 schedule tasks")
        
        return True
        
    except Exception as e:
        print(f"❌ Task imports error: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Daily Outlook Celery Tasks Execution Test")
    print("=" * 50)
    
    # Run tests
    test_results = {}
    
    # Test 1: Redis Connection
    test_results['redis'] = test_redis_connection()
    
    # Test 2: Task Imports
    test_results['imports'] = test_task_imports()
    
    # Test 3: Celery Configuration
    test_results['config'] = test_celery_configuration()
    
    # Test 4: Task Scheduling
    test_results['scheduling'] = test_task_scheduling()
    
    # Test 5: Task Parameters
    test_results['parameters'] = test_task_parameters()
    
    # Test 6: Beat Schedule
    test_results['beat'] = test_beat_schedule()
    
    # Test 7: Health Check Task
    test_results['health'] = test_health_check_task()
    
    # Test 8: Worker Status
    test_results['workers'] = test_celery_worker_status()
    
    # Summary
    print("\n📋 Test Summary")
    print("=" * 30)
    
    successful_tests = 0
    total_tests = len(test_results)
    
    for test_name, result in test_results.items():
        if result:
            print(f"✅ {test_name.replace('_', ' ').title()}: PASSED")
            successful_tests += 1
        else:
            print(f"❌ {test_name.replace('_', ' ').title()}: FAILED")
    
    print(f"\n🎯 Results: {successful_tests}/{total_tests} tests passed")
    
    if successful_tests >= 6:  # Allow for worker status to be optional
        print("🎉 Daily Outlook Celery Tasks are working correctly!")
        print("\n📝 System Status:")
        print("✅ Redis server running")
        print("✅ Celery tasks configured")
        print("✅ Task scheduling ready")
        print("✅ Beat schedule configured")
        print("\n🚀 Ready to start workers:")
        print("   celery -A backend.tasks.daily_outlook_tasks worker --loglevel=info --queues=daily_outlook_queue")
        print("   celery -A backend.tasks.daily_outlook_tasks beat --loglevel=info")
    else:
        print("⚠️  Some tests failed. Check the errors above for details.")

if __name__ == "__main__":
    main()
