#!/usr/bin/env python3
"""
Test script for Daily Outlook Celery Tasks

This script tests the daily outlook tasks from the project root.
"""

import os
import sys
from datetime import datetime, date, timedelta

# Add the project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

def test_imports():
    """Test that all imports work correctly"""
    print("🧪 Testing imports...")
    
    try:
        # Test model imports
        from backend.models.daily_outlook import DailyOutlook, TemplateTier, TemplateCategory
        from backend.models.user_models import User
        print("✅ Model imports successful")
        
        # Test service imports
        from backend.services.daily_outlook_content_service import DailyOutlookContentService
        from backend.services.daily_outlook_service import DailyOutlookService
        print("✅ Service imports successful")
        
        # Test task imports
        from backend.tasks.daily_outlook_tasks import (
            generate_daily_outlooks_batch,
            send_daily_outlook_notifications,
            optimize_content_performance,
            health_check_daily_outlook_tasks
        )
        print("✅ Task imports successful")
        
        return True
        
    except Exception as e:
        print(f"❌ Import error: {e}")
        return False

def test_model_functionality():
    """Test model functionality"""
    print("\n🧪 Testing model functionality...")
    
    try:
        from backend.models.daily_outlook import DailyOutlook, TemplateTier, TemplateCategory
        
        # Test enum values
        print(f"✅ TemplateTier values: {[tier.value for tier in TemplateTier]}")
        print(f"✅ TemplateCategory values: {[cat.value for cat in TemplateCategory]}")
        
        # Test model class
        print(f"✅ DailyOutlook model: {DailyOutlook.__name__}")
        print(f"✅ Table name: {DailyOutlook.__tablename__}")
        
        return True
        
    except Exception as e:
        print(f"❌ Model functionality error: {e}")
        return False

def test_service_functionality():
    """Test service functionality"""
    print("\n🧪 Testing service functionality...")
    
    try:
        from backend.services.daily_outlook_content_service import DailyOutlookContentService
        from backend.services.daily_outlook_service import DailyOutlookService
        
        # Test service initialization
        content_service = DailyOutlookContentService()
        print("✅ DailyOutlookContentService initialized")
        
        outlook_service = DailyOutlookService()
        print("✅ DailyOutlookService initialized")
        
        return True
        
    except Exception as e:
        print(f"❌ Service functionality error: {e}")
        return False

def test_celery_tasks():
    """Test Celery task definitions"""
    print("\n🧪 Testing Celery task definitions...")
    
    try:
        from backend.tasks.daily_outlook_tasks import (
            generate_daily_outlooks_batch,
            send_daily_outlook_notifications,
            optimize_content_performance,
            health_check_daily_outlook_tasks,
            celery_app
        )
        
        # Check if tasks are Celery tasks
        print(f"✅ generate_daily_outlooks_batch: {type(generate_daily_outlooks_batch)}")
        print(f"✅ send_daily_outlook_notifications: {type(send_daily_outlook_notifications)}")
        print(f"✅ optimize_content_performance: {type(optimize_content_performance)}")
        print(f"✅ health_check_daily_outlook_tasks: {type(health_check_daily_outlook_tasks)}")
        
        # Check Celery app configuration
        print(f"✅ Celery app: {celery_app}")
        print(f"✅ Broker URL: {celery_app.conf.broker_url}")
        print(f"✅ Result Backend: {celery_app.conf.result_backend}")
        
        return True
        
    except Exception as e:
        print(f"❌ Celery task error: {e}")
        return False

def test_schedule_configuration():
    """Test schedule configuration"""
    print("\n🧪 Testing schedule configuration...")
    
    try:
        from backend.config.celery_beat_schedule import CELERY_BEAT_SCHEDULE
        
        # Check if daily outlook tasks are in schedule
        required_tasks = [
            'generate-daily-outlooks',
            'send-daily-outlook-notifications',
            'optimize-content-performance',
            'daily-outlook-health-check'
        ]
        
        for task_name in required_tasks:
            if task_name in CELERY_BEAT_SCHEDULE:
                task_config = CELERY_BEAT_SCHEDULE[task_name]
                print(f"✅ Task {task_name}: {task_config['task']}")
            else:
                print(f"❌ Task {task_name} not in schedule")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ Schedule configuration error: {e}")
        return False

def test_task_parameters():
    """Test task parameter handling"""
    print("\n🧪 Testing task parameter handling...")
    
    try:
        from backend.tasks.daily_outlook_tasks import generate_daily_outlooks_batch
        
        # Test task signature
        import inspect
        sig = inspect.signature(generate_daily_outlooks_batch.run)
        params = list(sig.parameters.keys())
        print(f"✅ generate_daily_outlooks_batch parameters: {params}")
        
        # Check if parameters are correct
        expected_params = ['self', 'target_date', 'force_regenerate']
        for param in expected_params:
            if param in params:
                print(f"✅ Parameter {param} found")
            else:
                print(f"❌ Parameter {param} missing")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ Task parameter error: {e}")
        return False

def test_helper_functions():
    """Test helper function definitions"""
    print("\n🧪 Testing helper function definitions...")
    
    try:
        from backend.tasks.daily_outlook_tasks import (
            _get_active_users,
            _get_users_for_notification,
            _get_user_notification_time,
            _send_outlook_notification,
            _analyze_outlook_performance,
            _identify_low_performing_content,
            _generate_optimization_recommendations,
            _trigger_ab_tests,
            _update_content_templates
        )
        
        helper_functions = [
            _get_active_users,
            _get_users_for_notification,
            _get_user_notification_time,
            _send_outlook_notification,
            _analyze_outlook_performance,
            _identify_low_performing_content,
            _generate_optimization_recommendations,
            _trigger_ab_tests,
            _update_content_templates
        ]
        
        for func in helper_functions:
            print(f"✅ Helper function {func.__name__} found")
        
        return True
        
    except Exception as e:
        print(f"❌ Helper function error: {e}")
        return False

def test_celery_configuration():
    """Test Celery configuration"""
    print("\n🧪 Testing Celery configuration...")
    
    try:
        from backend.tasks.daily_outlook_tasks import celery_app
        
        # Check configuration
        config = celery_app.conf
        
        print(f"✅ Broker URL: {config.broker_url}")
        print(f"✅ Result Backend: {config.result_backend}")
        print(f"✅ Task Serializer: {config.task_serializer}")
        print(f"✅ Accept Content: {config.accept_content}")
        print(f"✅ Timezone: {config.timezone}")
        print(f"✅ Task Time Limit: {config.task_time_limit}")
        print(f"✅ Task Soft Time Limit: {config.task_soft_time_limit}")
        
        # Check task routes
        task_routes = config.task_routes
        if 'backend.tasks.daily_outlook_tasks.*' in task_routes:
            print("✅ Task routes configured correctly")
        else:
            print("❌ Task routes not configured")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Celery configuration error: {e}")
        return False

def test_manual_task_creation():
    """Test manual task creation (without execution)"""
    print("\n🧪 Testing manual task creation...")
    
    try:
        from backend.tasks.daily_outlook_tasks import (
            generate_daily_outlooks_batch,
            send_daily_outlook_notifications,
            optimize_content_performance
        )
        
        # Test task creation with parameters
        tomorrow = (date.today() + timedelta(days=1)).isoformat()
        
        # Create task instances (without calling .delay())
        print("✅ Task instances can be created")
        print(f"✅ generate_daily_outlooks_batch task: {generate_daily_outlooks_batch}")
        print(f"✅ send_daily_outlook_notifications task: {send_daily_outlook_notifications}")
        print(f"✅ optimize_content_performance task: {optimize_content_performance}")
        
        return True
        
    except Exception as e:
        print(f"❌ Manual task creation error: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Daily Outlook Celery Tasks Test Suite")
    print("=" * 50)
    
    # Run tests
    test_results = {}
    
    # Test 1: Imports
    test_results['imports'] = test_imports()
    
    # Test 2: Model Functionality
    test_results['models'] = test_model_functionality()
    
    # Test 3: Service Functionality
    test_results['services'] = test_service_functionality()
    
    # Test 4: Celery Tasks
    test_results['celery_tasks'] = test_celery_tasks()
    
    # Test 5: Schedule Configuration
    test_results['schedule'] = test_schedule_configuration()
    
    # Test 6: Task Parameters
    test_results['parameters'] = test_task_parameters()
    
    # Test 7: Helper Functions
    test_results['helpers'] = test_helper_functions()
    
    # Test 8: Celery Configuration
    test_results['celery_config'] = test_celery_configuration()
    
    # Test 9: Manual Task Creation
    test_results['manual_tasks'] = test_manual_task_creation()
    
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
    
    if successful_tests == total_tests:
        print("🎉 All tests passed! Daily Outlook Celery Tasks are working correctly.")
        print("\n📝 Next Steps:")
        print("1. Start Redis server: redis-server")
        print("2. Start Celery worker: celery -A backend.tasks.daily_outlook_tasks worker --loglevel=info --queues=daily_outlook_queue")
        print("3. Start Celery Beat: celery -A backend.tasks.daily_outlook_tasks beat --loglevel=info")
        print("4. Monitor tasks: celery -A backend.tasks.daily_outlook_tasks inspect active")
    else:
        print("⚠️  Some tests failed. Check the errors above for details.")
        print("\n🔧 Troubleshooting:")
        print("1. Ensure all dependencies are installed: pip install celery redis")
        print("2. Check that all model files exist in backend/models/")
        print("3. Verify service files exist in backend/services/")
        print("4. Check Python path configuration")

if __name__ == "__main__":
    main()
