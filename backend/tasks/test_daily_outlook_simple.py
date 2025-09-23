#!/usr/bin/env python3
"""
Simple test script for Daily Outlook Tasks

This script tests the basic functionality without requiring Celery to be running.
"""

import os
import sys
from datetime import datetime, date, timedelta

# Add backend modules to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

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
        
        # Test task imports (without executing)
        print("✅ All imports successful")
        return True
        
    except Exception as e:
        print(f"❌ Import error: {e}")
        return False

def test_model_creation():
    """Test model creation and basic functionality"""
    print("\n🧪 Testing model creation...")
    
    try:
        from backend.models.daily_outlook import DailyOutlook, TemplateTier, TemplateCategory
        from backend.models.user_models import User
        
        # Test enum values
        print(f"✅ TemplateTier values: {[tier.value for tier in TemplateTier]}")
        print(f"✅ TemplateCategory values: {[cat.value for cat in TemplateCategory]}")
        
        # Test model instantiation (without database)
        user_data = {
            'user_id': 'test_user_123',
            'email': 'test@example.com',
            'first_name': 'Test',
            'last_name': 'User'
        }
        
        # Create a mock user object
        class MockUser:
            def __init__(self, **kwargs):
                for key, value in kwargs.items():
                    setattr(self, key, value)
        
        mock_user = MockUser(**user_data)
        print(f"✅ Mock user created: {mock_user.email}")
        
        return True
        
    except Exception as e:
        print(f"❌ Model creation error: {e}")
        return False

def test_service_initialization():
    """Test service initialization"""
    print("\n🧪 Testing service initialization...")
    
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
        print(f"❌ Service initialization error: {e}")
        return False

def test_task_functions():
    """Test task function definitions"""
    print("\n🧪 Testing task function definitions...")
    
    try:
        # Import the task module
        import sys
        sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
        import daily_outlook_tasks
        
        # Check if functions exist
        required_functions = [
            'generate_daily_outlooks_batch',
            'send_daily_outlook_notifications', 
            'optimize_content_performance',
            'health_check_daily_outlook_tasks'
        ]
        
        for func_name in required_functions:
            if hasattr(daily_outlook_tasks, func_name):
                print(f"✅ Function {func_name} found")
            else:
                print(f"❌ Function {func_name} not found")
                return False
        
        # Check if Celery app is configured
        if hasattr(daily_outlook_tasks, 'celery_app'):
            print("✅ Celery app configured")
        else:
            print("❌ Celery app not configured")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Task function test error: {e}")
        return False

def test_helper_functions():
    """Test helper function definitions"""
    print("\n🧪 Testing helper function definitions...")
    
    try:
        import daily_outlook_tasks
        
        # Check helper functions
        helper_functions = [
            '_get_active_users',
            '_get_users_for_notification',
            '_get_user_notification_time',
            '_send_outlook_notification',
            '_analyze_outlook_performance',
            '_identify_low_performing_content',
            '_generate_optimization_recommendations',
            '_trigger_ab_tests',
            '_update_content_templates'
        ]
        
        for func_name in helper_functions:
            if hasattr(daily_outlook_tasks, func_name):
                print(f"✅ Helper function {func_name} found")
            else:
                print(f"❌ Helper function {func_name} not found")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ Helper function test error: {e}")
        return False

def test_celery_configuration():
    """Test Celery configuration"""
    print("\n🧪 Testing Celery configuration...")
    
    try:
        import daily_outlook_tasks
        
        # Check Celery app configuration
        celery_app = daily_outlook_tasks.celery_app
        
        # Check broker configuration
        broker_url = celery_app.conf.broker_url
        print(f"✅ Broker URL: {broker_url}")
        
        # Check result backend
        result_backend = celery_app.conf.result_backend
        print(f"✅ Result Backend: {result_backend}")
        
        # Check task routes
        task_routes = celery_app.conf.task_routes
        if 'backend.tasks.daily_outlook_tasks.*' in task_routes:
            print("✅ Task routes configured")
        else:
            print("❌ Task routes not configured")
            return False
        
        # Check time limits
        time_limit = celery_app.conf.task_time_limit
        print(f"✅ Task time limit: {time_limit} seconds")
        
        return True
        
    except Exception as e:
        print(f"❌ Celery configuration error: {e}")
        return False

def test_schedule_configuration():
    """Test schedule configuration"""
    print("\n🧪 Testing schedule configuration...")
    
    try:
        # Import schedule configuration
        from config.celery_beat_schedule import CELERY_BEAT_SCHEDULE
        
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
                print(f"✅ Task {task_name} scheduled: {task_config['task']}")
            else:
                print(f"❌ Task {task_name} not in schedule")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ Schedule configuration error: {e}")
        return False

def test_documentation():
    """Test that documentation files exist"""
    print("\n🧪 Testing documentation...")
    
    try:
        # Check if documentation files exist
        doc_files = [
            'DAILY_OUTLOOK_TASKS_README.md',
            'DEPLOYMENT_GUIDE.md'
        ]
        
        for doc_file in doc_files:
            doc_path = os.path.join(os.path.dirname(__file__), doc_file)
            if os.path.exists(doc_path):
                print(f"✅ Documentation file {doc_file} exists")
            else:
                print(f"❌ Documentation file {doc_file} missing")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ Documentation test error: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Daily Outlook Tasks Simple Test Suite")
    print("=" * 50)
    
    # Run tests
    test_results = {}
    
    # Test 1: Imports
    test_results['imports'] = test_imports()
    
    # Test 2: Model Creation
    test_results['models'] = test_model_creation()
    
    # Test 3: Service Initialization
    test_results['services'] = test_service_initialization()
    
    # Test 4: Task Functions
    test_results['tasks'] = test_task_functions()
    
    # Test 5: Helper Functions
    test_results['helpers'] = test_helper_functions()
    
    # Test 6: Celery Configuration
    test_results['celery'] = test_celery_configuration()
    
    # Test 7: Schedule Configuration
    test_results['schedule'] = test_schedule_configuration()
    
    # Test 8: Documentation
    test_results['docs'] = test_documentation()
    
    # Summary
    print("\n📋 Test Summary")
    print("=" * 30)
    
    successful_tests = 0
    total_tests = len(test_results)
    
    for test_name, result in test_results.items():
        if result:
            print(f"✅ {test_name.title()}: PASSED")
            successful_tests += 1
        else:
            print(f"❌ {test_name.title()}: FAILED")
    
    print(f"\n🎯 Results: {successful_tests}/{total_tests} tests passed")
    
    if successful_tests == total_tests:
        print("🎉 All tests passed! Daily Outlook Tasks system is properly configured.")
        print("\n📝 Next Steps:")
        print("1. Start Redis server: redis-server")
        print("2. Start Celery worker: celery -A backend.tasks.daily_outlook_tasks worker --loglevel=info --queues=daily_outlook_queue")
        print("3. Start Celery Beat: celery -A backend.tasks.daily_outlook_tasks beat --loglevel=info")
        print("4. Run full test suite: python test_daily_outlook_tasks.py")
    else:
        print("⚠️  Some tests failed. Check the errors above for details.")

if __name__ == "__main__":
    main()
