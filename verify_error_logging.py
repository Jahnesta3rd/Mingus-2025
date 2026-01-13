#!/usr/bin/env python3
"""
Verify Error Logging and Monitoring Setup
Comprehensive verification script to ensure error logging and monitoring is properly configured and working
"""

import os
import sys
import json
import traceback
from pathlib import Path

# Add backend to path
sys.path.insert(0, os.path.dirname(__file__))

def print_header(text):
    """Print formatted header"""
    print(f"\n{'='*70}")
    print(f"{text}")
    print(f"{'='*70}\n")

def check_mark(condition):
    """Return checkmark or X"""
    return "✅" if condition else "❌"

def verify_error_monitor_module():
    """Verify error monitor module exists and is importable"""
    print_header("1. Verifying Error Monitor Module")
    
    results = {
        'module_exists': False,
        'class_exists': False,
        'functions_exist': False,
        'imports_work': False
    }
    
    # Check if file exists
    error_monitor_path = Path('backend/monitoring/error_monitor.py')
    if error_monitor_path.exists():
        print(f"{check_mark(True)} Error monitor module file exists")
        results['module_exists'] = True
    else:
        print(f"{check_mark(False)} Error monitor module file NOT found")
        return results
    
    # Try to import
    try:
        from backend.monitoring.error_monitor import (
            ErrorMonitor,
            get_error_monitor,
            ErrorSeverity,
            ErrorCategory
        )
        print(f"{check_mark(True)} Error monitor imports successfully")
        results['imports_work'] = True
        
        # Check class exists
        if ErrorMonitor:
            print(f"{check_mark(True)} ErrorMonitor class exists")
            results['class_exists'] = True
        
        # Check functions exist
        if get_error_monitor:
            print(f"{check_mark(True)} get_error_monitor function exists")
            results['functions_exist'] = True
        
        # Check enums
        print(f"{check_mark(True)} ErrorSeverity enum: {[s.value for s in ErrorSeverity]}")
        print(f"{check_mark(True)} ErrorCategory enum: {[c.value for c in ErrorCategory]}")
        
    except Exception as e:
        print(f"{check_mark(False)} Failed to import error monitor: {e}")
        traceback.print_exc()
    
    return results

def verify_app_integration():
    """Verify error monitor is integrated into app.py"""
    print_header("2. Verifying App Integration")
    
    results = {
        'imported': False,
        'initialized': False,
        'error_handlers': False,
        'endpoints': False
    }
    
    app_path = Path('app.py')
    if not app_path.exists():
        print(f"{check_mark(False)} app.py not found")
        return results
    
    # Read app.py
    with open(app_path, 'r') as f:
        app_content = f.read()
    
    # Check imports
    if 'from backend.monitoring.error_monitor import' in app_content:
        print(f"{check_mark(True)} Error monitor imported in app.py")
        results['imported'] = True
    else:
        print(f"{check_mark(False)} Error monitor NOT imported in app.py")
    
    # Check initialization
    if 'error_monitor = get_error_monitor()' in app_content:
        print(f"{check_mark(True)} Error monitor initialized in app.py")
        results['initialized'] = True
    else:
        print(f"{check_mark(False)} Error monitor NOT initialized in app.py")
    
    # Check error handlers
    error_handler_patterns = [
        '@app.errorhandler',
        'error_monitor.log_error',
        'handle_exception'
    ]
    handlers_found = sum(1 for pattern in error_handler_patterns if pattern in app_content)
    if handlers_found >= 2:
        print(f"{check_mark(True)} Error handlers configured ({handlers_found} patterns found)")
        results['error_handlers'] = True
    else:
        print(f"{check_mark(False)} Error handlers may be incomplete ({handlers_found} patterns found)")
    
    # Check API endpoints
    endpoint_patterns = [
        '/api/errors/stats',
        '/api/errors',
        '/api/errors/health'
    ]
    endpoints_found = sum(1 for pattern in endpoint_patterns if pattern in app_content)
    if endpoints_found >= 2:
        print(f"{check_mark(True)} Error API endpoints configured ({endpoints_found} endpoints found)")
        results['endpoints'] = True
    else:
        print(f"{check_mark(False)} Error API endpoints may be incomplete ({endpoints_found} endpoints found)")
    
    return results

def verify_logging_setup():
    """Verify logging configuration"""
    print_header("3. Verifying Logging Setup")
    
    results = {
        'log_dir_exists': False,
        'log_files_created': False,
        'log_config_valid': False
    }
    
    # Check log directory
    log_dir = Path('logs')
    if log_dir.exists():
        print(f"{check_mark(True)} Log directory exists: {log_dir.absolute()}")
        results['log_dir_exists'] = True
    else:
        print(f"{check_mark(False)} Log directory does not exist (will be created on first error)")
        results['log_dir_exists'] = False
    
    # Check for log files (may not exist if no errors yet)
    log_files = ['app.log', 'errors.log', 'errors.json.log']
    existing_logs = []
    for log_file in log_files:
        log_path = log_dir / log_file
        if log_path.exists():
            size = log_path.stat().st_size
            print(f"{check_mark(True)} {log_file} exists ({size} bytes)")
            existing_logs.append(log_file)
        else:
            print(f"{check_mark(False)} {log_file} does not exist yet (normal if no errors logged)")
    
    if existing_logs:
        results['log_files_created'] = True
    
    # Verify logging configuration in error monitor
    try:
        from backend.monitoring.error_monitor import ErrorMonitor
        
        # Create a test instance to verify logging setup
        test_monitor = ErrorMonitor(log_dir='logs', enable_sentry=False)
        
        if hasattr(test_monitor, 'app_logger') and hasattr(test_monitor, 'error_logger'):
            print(f"{check_mark(True)} Logging handlers configured correctly")
            results['log_config_valid'] = True
        else:
            print(f"{check_mark(False)} Logging handlers may be missing")
            
    except Exception as e:
        print(f"{check_mark(False)} Failed to verify logging config: {e}")
    
    return results

def verify_error_monitor_functionality():
    """Test error monitor functionality"""
    print_header("4. Testing Error Monitor Functionality")
    
    results = {
        'can_create_instance': False,
        'can_log_error': False,
        'can_get_stats': False,
        'categorization_works': False
    }
    
    try:
        from backend.monitoring.error_monitor import (
            ErrorMonitor,
            ErrorSeverity,
            ErrorCategory
        )
        
        # Create instance
        monitor = ErrorMonitor(log_dir='logs', enable_sentry=False)
        print(f"{check_mark(True)} ErrorMonitor instance created")
        results['can_create_instance'] = True
        
        # Test error logging
        test_error = ValueError("Test error for verification")
        error_log = monitor.log_error(
            error=test_error,
            severity=ErrorSeverity.MEDIUM,
            category=ErrorCategory.VALIDATION,
            context={'test': True}
        )
        
        if error_log:
            print(f"{check_mark(True)} Error logging works (logged: {error_log.error_type})")
            results['can_log_error'] = True
        else:
            print(f"{check_mark(False)} Error logging returned None")
        
        # Test stats
        stats = monitor.get_error_stats(hours=1)
        if isinstance(stats, dict) and 'total' in stats:
            print(f"{check_mark(True)} Error statistics retrieval works (total: {stats['total']})")
            results['can_get_stats'] = True
        else:
            print(f"{check_mark(False)} Error statistics structure invalid")
        
        # Test categorization
        db_error = Exception("Database connection failed")
        category = monitor.categorize_error(db_error)
        if category == ErrorCategory.DATABASE:
            print(f"{check_mark(True)} Error categorization works (categorized as: {category.value})")
            results['categorization_works'] = True
        else:
            print(f"{check_mark(False)} Error categorization may not work correctly")
        
    except Exception as e:
        print(f"{check_mark(False)} Error testing functionality: {e}")
        traceback.print_exc()
    
    return results

def verify_environment_config():
    """Verify environment configuration"""
    print_header("5. Verifying Environment Configuration")
    
    results = {
        'env_example_exists': False,
        'config_vars_documented': False
    }
    
    # Check env.example
    env_example = Path('env.example')
    if env_example.exists():
        print(f"{check_mark(True)} env.example exists")
        results['env_example_exists'] = True
        
        with open(env_example, 'r') as f:
            env_content = f.read()
        
        # Check for error monitoring config vars
        config_vars = [
            'LOG_DIR',
            'ENABLE_SENTRY',
            'SENTRY_DSN',
            'MAX_ERROR_HISTORY',
            'ERROR_ALERT_CRITICAL_PER_HOUR',
            'ERROR_ALERT_HIGH_PER_HOUR',
            'ERROR_ALERT_TOTAL_PER_HOUR'
        ]
        
        found_vars = [var for var in config_vars if var in env_content]
        print(f"{check_mark(len(found_vars) > 0)} Error monitoring config vars documented ({len(found_vars)}/{len(config_vars)})")
        
        if len(found_vars) >= 5:
            results['config_vars_documented'] = True
    else:
        print(f"{check_mark(False)} env.example not found")
    
    # Check actual environment
    print("\nCurrent environment variables:")
    env_vars = {
        'LOG_DIR': os.environ.get('LOG_DIR', 'not set (default: logs)'),
        'ENABLE_SENTRY': os.environ.get('ENABLE_SENTRY', 'not set (default: false)'),
        'SENTRY_DSN': 'set' if os.environ.get('SENTRY_DSN') else 'not set',
        'MAX_ERROR_HISTORY': os.environ.get('MAX_ERROR_HISTORY', 'not set (default: 10000)')
    }
    
    for var, value in env_vars.items():
        print(f"  {var}: {value}")
    
    return results

def verify_test_files():
    """Verify test files exist"""
    print_header("6. Verifying Test Files")
    
    results = {
        'test_file_exists': False,
        'test_comprehensive': False
    }
    
    test_files = [
        'test_error_monitoring.py',
        'test_error_monitoring_unit.py'
    ]
    
    for test_file in test_files:
        test_path = Path(test_file)
        if test_path.exists():
            print(f"{check_mark(True)} {test_file} exists")
            results['test_file_exists'] = True
            
            # Check if it's comprehensive
            with open(test_path, 'r') as f:
                content = f.read()
                if len(content) > 1000:  # Reasonable size
                    print(f"{check_mark(True)} {test_file} appears comprehensive ({len(content)} chars)")
                    results['test_comprehensive'] = True
        else:
            print(f"{check_mark(False)} {test_file} not found")
    
    return results

def verify_documentation():
    """Verify documentation exists"""
    print_header("7. Verifying Documentation")
    
    results = {
        'docs_exist': False
    }
    
    doc_files = [
        'ERROR_MONITORING_IMPLEMENTATION.md',
        'ERROR_MONITORING_GUIDE.md',
        'ERROR_TESTING_GUIDE.md'
    ]
    
    found_docs = []
    for doc_file in doc_files:
        doc_path = Path(doc_file)
        if doc_path.exists():
            print(f"{check_mark(True)} {doc_file} exists")
            found_docs.append(doc_file)
        else:
            print(f"{check_mark(False)} {doc_file} not found")
    
    if found_docs:
        results['docs_exist'] = True
        print(f"\nFound {len(found_docs)}/{len(doc_files)} documentation files")
    
    return results

def print_summary(all_results):
    """Print verification summary"""
    print_header("Verification Summary")
    
    total_checks = 0
    passed_checks = 0
    
    for category, results in all_results.items():
        print(f"\n{category}:")
        for check, passed in results.items():
            status = check_mark(passed)
            print(f"  {status} {check}")
            total_checks += 1
            if passed:
                passed_checks += 1
    
    print(f"\n{'='*70}")
    print(f"Overall: {passed_checks}/{total_checks} checks passed")
    print(f"Success Rate: {(passed_checks/total_checks*100) if total_checks > 0 else 0:.1f}%")
    print(f"{'='*70}\n")
    
    # Overall assessment
    if passed_checks == total_checks:
        print("✅ ERROR LOGGING AND MONITORING IS FULLY SET UP AND CONFIGURED")
    elif passed_checks >= total_checks * 0.8:
        print("⚠️  ERROR LOGGING AND MONITORING IS MOSTLY SET UP (minor issues)")
    else:
        print("❌ ERROR LOGGING AND MONITORING HAS SIGNIFICANT ISSUES")
    
    # Recommendations
    print("\nRecommendations:")
    print("1. Run the application and generate some errors to verify logging works")
    print("2. Check logs/ directory for error log files")
    print("3. Test API endpoints: /api/errors/stats, /api/errors, /api/errors/health")
    print("4. Run test_error_monitoring.py to verify end-to-end functionality")
    if not os.environ.get('SENTRY_DSN'):
        print("5. Consider setting up Sentry for production error tracking")

def main():
    """Run all verification checks"""
    print("\n" + "="*70)
    print("ERROR LOGGING AND MONITORING VERIFICATION")
    print("="*70)
    
    all_results = {}
    
    # Run all checks
    all_results['Module Verification'] = verify_error_monitor_module()
    all_results['App Integration'] = verify_app_integration()
    all_results['Logging Setup'] = verify_logging_setup()
    all_results['Functionality'] = verify_error_monitor_functionality()
    all_results['Environment Config'] = verify_environment_config()
    all_results['Test Files'] = verify_test_files()
    all_results['Documentation'] = verify_documentation()
    
    # Print summary
    print_summary(all_results)

if __name__ == '__main__':
    main()
