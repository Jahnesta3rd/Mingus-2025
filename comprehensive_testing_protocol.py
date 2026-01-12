#!/usr/bin/env python3
"""
Comprehensive Testing Protocol for Mingus Application
Tests: Server Status, Database, Redis, Backend API, Frontend Build, Nginx, STRIPE
"""

import os
import sys
import json
import time
import subprocess
from datetime import datetime
from typing import Dict, List, Any, Optional
from urllib.parse import quote_plus

# Try to import optional dependencies
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    print("Warning: 'requests' module not available. Server and API tests will be skipped.")

try:
    import psycopg2
    PSYCOPG2_AVAILABLE = True
except ImportError:
    PSYCOPG2_AVAILABLE = False
    print("Warning: 'psycopg2' module not available. Database tests will be skipped.")

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    print("Warning: 'redis' module not available. Redis tests will be skipped.")

try:
    import stripe
    STRIPE_AVAILABLE = True
except ImportError:
    STRIPE_AVAILABLE = False
    print("Warning: 'stripe' module not available. STRIPE tests will be skipped.")

# Color codes for terminal output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

class TestResult:
    def __init__(self, name: str, status: str, message: str = "", details: Dict = None):
        self.name = name
        self.status = status  # "PASS", "FAIL", "WARN"
        self.message = message
        self.details = details or {}
        self.timestamp = datetime.now().isoformat()

    def __str__(self):
        status_color = Colors.GREEN if self.status == "PASS" else Colors.RED if self.status == "FAIL" else Colors.YELLOW
        return f"{status_color}{self.status}{Colors.RESET} - {self.name}: {self.message}"

class ComprehensiveTester:
    def __init__(self):
        self.results: List[TestResult] = []
        self.base_url = os.environ.get('BASE_URL', 'http://localhost:5000')
        self.db_config = {
            'host': os.environ.get('DB_HOST', 'localhost'),
            'port': os.environ.get('DB_PORT', '5432'),
            'database': os.environ.get('DB_NAME', 'mingus_db'),
            'user': os.environ.get('DB_USER', 'mingus_user'),
            'password': os.environ.get('DB_PASSWORD', 'MingusApp2026!')
        }
        self.redis_config = {
            'host': os.environ.get('REDIS_HOST', 'localhost'),
            'port': int(os.environ.get('REDIS_PORT', '6379')),
            'password': os.environ.get('REDIS_PASSWORD'),
            'db': int(os.environ.get('REDIS_DB', '0'))
        }
        self.stripe_config = {
            'secret_key': os.environ.get('STRIPE_SECRET_KEY') or os.environ.get('STRIPE_TEST_SECRET_KEY'),
            'publishable_key': os.environ.get('STRIPE_PUBLISHABLE_KEY') or os.environ.get('STRIPE_TEST_PUBLISHABLE_KEY')
        }

    def log_result(self, result: TestResult):
        """Log test result"""
        self.results.append(result)
        print(result)

    def test_server_status(self) -> TestResult:
        """Test server status endpoints"""
        print(f"\n{Colors.BOLD}{Colors.BLUE}Testing Server Status...{Colors.RESET}")
        
        if not REQUESTS_AVAILABLE:
            return TestResult(
                "Server Status",
                "WARN",
                "Skipped - 'requests' module not installed",
                {'suggestion': 'Install with: pip install requests'}
            )
        
        try:
            # Test /health endpoint
            health_url = f"{self.base_url}/health"
            response = requests.get(health_url, timeout=5)
            
            if response.status_code == 200:
                health_data = response.json()
                if health_data.get('status') == 'healthy':
                    # Test /api/status endpoint
                    status_url = f"{self.base_url}/api/status"
                    status_response = requests.get(status_url, timeout=5)
                    
                    if status_response.status_code == 200:
                        status_data = status_response.json()
                        return TestResult(
                            "Server Status",
                            "PASS",
                            "Both /health and /api/status endpoints responding correctly",
                            {
                                'health_status': health_data.get('status'),
                                'api_status': status_data.get('status'),
                                'services': health_data.get('services', {}),
                                'endpoints': status_data.get('endpoints', {})
                            }
                        )
                    else:
                        return TestResult(
                            "Server Status",
                            "WARN",
                            f"/health works but /api/status returned {status_response.status_code}",
                            {'health_status': 'healthy', 'api_status_code': status_response.status_code}
                        )
                else:
                    return TestResult(
                        "Server Status",
                        "FAIL",
                        f"Health check returned status: {health_data.get('status')}",
                        health_data
                    )
            else:
                return TestResult(
                    "Server Status",
                    "FAIL",
                    f"Health endpoint returned status code {response.status_code}",
                    {'status_code': response.status_code, 'response': response.text[:200]}
                )
        except requests.exceptions.ConnectionError:
            return TestResult(
                "Server Status",
                "FAIL",
                f"Could not connect to server at {self.base_url}",
                {'error': 'Connection refused'}
            )
        except Exception as e:
            return TestResult(
                "Server Status",
                "FAIL",
                f"Error testing server status: {str(e)}",
                {'error': str(e)}
            )

    def test_database_connection(self) -> TestResult:
        """Test database connection"""
        print(f"\n{Colors.BOLD}{Colors.BLUE}Testing Database Connection...{Colors.RESET}")
        
        if not PSYCOPG2_AVAILABLE:
            return TestResult(
                "Database Connection",
                "WARN",
                "Skipped - 'psycopg2' module not installed",
                {'suggestion': 'Install with: pip install psycopg2-binary'}
            )
        
        try:
            conn = psycopg2.connect(
                host=self.db_config['host'],
                port=self.db_config['port'],
                database=self.db_config['database'],
                user=self.db_config['user'],
                password=self.db_config['password'],
                connect_timeout=5
            )
            
            # Test basic query
            cursor = conn.cursor()
            cursor.execute("SELECT version();")
            version = cursor.fetchone()[0]
            
            # Test database operations
            cursor.execute("SELECT current_database(), current_user;")
            db_info = cursor.fetchone()
            
            # Test table access
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                LIMIT 5;
            """)
            tables = [row[0] for row in cursor.fetchall()]
            
            cursor.close()
            conn.close()
            
            return TestResult(
                "Database Connection",
                "PASS",
                f"Successfully connected to PostgreSQL database",
                {
                    'database': db_info[0],
                    'user': db_info[1],
                    'version': version.split(',')[0],
                    'tables_found': len(tables),
                    'sample_tables': tables
                }
            )
        except psycopg2.OperationalError as e:
            return TestResult(
                "Database Connection",
                "FAIL",
                f"Database connection failed: {str(e)}",
                {'error': str(e), 'config': {k: v for k, v in self.db_config.items() if k != 'password'}}
            )
        except Exception as e:
            return TestResult(
                "Database Connection",
                "FAIL",
                f"Error testing database: {str(e)}",
                {'error': str(e)}
            )

    def test_redis_service(self) -> TestResult:
        """Test Redis service"""
        print(f"\n{Colors.BOLD}{Colors.BLUE}Testing Redis Service...{Colors.RESET}")
        
        if not REDIS_AVAILABLE:
            return TestResult(
                "Redis Service",
                "WARN",
                "Skipped - 'redis' module not installed",
                {'suggestion': 'Install with: pip install redis'}
            )
        
        try:
            # Create Redis connection
            redis_client = redis.Redis(
                host=self.redis_config['host'],
                port=self.redis_config['port'],
                password=self.redis_config['password'],
                db=self.redis_config['db'],
                socket_connect_timeout=5,
                decode_responses=True
            )
            
            # Test connection
            ping_result = redis_client.ping()
            if not ping_result:
                return TestResult(
                    "Redis Service",
                    "FAIL",
                    "Redis PING command failed",
                    {}
                )
            
            # Test basic operations
            test_key = "mingus_test_key"
            test_value = f"test_value_{int(time.time())}"
            
            redis_client.set(test_key, test_value, ex=60)  # Expire in 60 seconds
            retrieved_value = redis_client.get(test_key)
            
            if retrieved_value == test_value:
                # Get Redis info
                info = redis_client.info()
                redis_client.delete(test_key)  # Cleanup
                
                return TestResult(
                    "Redis Service",
                    "PASS",
                    "Redis service is operational",
                    {
                        'version': info.get('redis_version'),
                        'connected_clients': info.get('connected_clients'),
                        'used_memory_human': info.get('used_memory_human'),
                        'keyspace': info.get('db0', 'N/A')
                    }
                )
            else:
                return TestResult(
                    "Redis Service",
                    "FAIL",
                    "Redis read/write test failed",
                    {'expected': test_value, 'got': retrieved_value}
                )
        except redis.ConnectionError as e:
            return TestResult(
                "Redis Service",
                "FAIL",
                f"Could not connect to Redis: {str(e)}",
                {'error': str(e), 'config': {k: v for k, v in self.redis_config.items() if k != 'password'}}
            )
        except Exception as e:
            return TestResult(
                "Redis Service",
                "FAIL",
                f"Error testing Redis: {str(e)}",
                {'error': str(e)}
            )

    def test_backend_api(self) -> TestResult:
        """Test backend API endpoints"""
        print(f"\n{Colors.BOLD}{Colors.BLUE}Testing Backend API...{Colors.RESET}")
        
        if not REQUESTS_AVAILABLE:
            return TestResult(
                "Backend API",
                "WARN",
                "Skipped - 'requests' module not installed",
                {'suggestion': 'Install with: pip install requests'}
            )
        
        endpoints_tested = []
        endpoints_failed = []
        
        # Test various API endpoints
        test_endpoints = [
            ('/api/status', 'GET'),
            ('/health', 'GET'),
        ]
        
        for endpoint, method in test_endpoints:
            try:
                url = f"{self.base_url}{endpoint}"
                if method == 'GET':
                    response = requests.get(url, timeout=5)
                else:
                    response = requests.request(method, url, timeout=5)
                
                if response.status_code in [200, 201]:
                    endpoints_tested.append({
                        'endpoint': endpoint,
                        'method': method,
                        'status': response.status_code
                    })
                else:
                    endpoints_failed.append({
                        'endpoint': endpoint,
                        'method': method,
                        'status': response.status_code,
                        'error': response.text[:100]
                    })
            except Exception as e:
                endpoints_failed.append({
                    'endpoint': endpoint,
                    'method': method,
                    'error': str(e)
                })
        
        if len(endpoints_failed) == 0:
            return TestResult(
                "Backend API",
                "PASS",
                f"All {len(endpoints_tested)} endpoints tested successfully",
                {'endpoints_tested': endpoints_tested}
            )
        elif len(endpoints_tested) > 0:
            return TestResult(
                "Backend API",
                "WARN",
                f"{len(endpoints_tested)} endpoints passed, {len(endpoints_failed)} failed",
                {
                    'endpoints_tested': endpoints_tested,
                    'endpoints_failed': endpoints_failed
                }
            )
        else:
            return TestResult(
                "Backend API",
                "FAIL",
                f"All {len(endpoints_failed)} endpoints failed",
                {'endpoints_failed': endpoints_failed}
            )

    def test_frontend_build(self) -> TestResult:
        """Test frontend build process"""
        print(f"\n{Colors.BOLD}{Colors.BLUE}Testing Frontend Build...{Colors.RESET}")
        
        frontend_dir = os.path.join(os.path.dirname(__file__), 'frontend')
        
        if not os.path.exists(frontend_dir):
            return TestResult(
                "Frontend Build",
                "WARN",
                "Frontend directory not found",
                {'frontend_dir': frontend_dir}
            )
        
        # Check if package.json exists
        package_json = os.path.join(frontend_dir, 'package.json')
        if not os.path.exists(package_json):
            return TestResult(
                "Frontend Build",
                "FAIL",
                "package.json not found in frontend directory",
                {'frontend_dir': frontend_dir}
            )
        
        # Check if node_modules exists (dependencies installed)
        node_modules = os.path.join(frontend_dir, 'node_modules')
        if not os.path.exists(node_modules):
            return TestResult(
                "Frontend Build",
                "WARN",
                "node_modules not found - dependencies may not be installed",
                {'suggestion': 'Run: cd frontend && npm install'}
            )
        
        # Try to run build command
        try:
            result = subprocess.run(
                ['npm', 'run', 'build'],
                cwd=frontend_dir,
                capture_output=True,
                text=True,
                timeout=120
            )
            
            if result.returncode == 0:
                # Check if dist directory was created
                dist_dir = os.path.join(frontend_dir, 'dist')
                if os.path.exists(dist_dir):
                    dist_files = len([f for f in os.listdir(dist_dir) if os.path.isfile(os.path.join(dist_dir, f))])
                    return TestResult(
                        "Frontend Build",
                        "PASS",
                        "Frontend build completed successfully",
                        {
                            'build_output': result.stdout[-500:],  # Last 500 chars
                            'dist_files': dist_files
                        }
                    )
                else:
                    return TestResult(
                        "Frontend Build",
                        "WARN",
                        "Build command succeeded but dist directory not found",
                        {'build_output': result.stdout[-500:]}
                    )
            else:
                return TestResult(
                    "Frontend Build",
                    "FAIL",
                    f"Build command failed with return code {result.returncode}",
                    {
                        'stdout': result.stdout[-500:],
                        'stderr': result.stderr[-500:]
                    }
                )
        except subprocess.TimeoutExpired:
            return TestResult(
                "Frontend Build",
                "FAIL",
                "Build command timed out after 120 seconds",
                {}
            )
        except FileNotFoundError:
            return TestResult(
                "Frontend Build",
                "FAIL",
                "npm command not found - Node.js may not be installed",
                {}
            )
        except Exception as e:
            return TestResult(
                "Frontend Build",
                "FAIL",
                f"Error running build: {str(e)}",
                {'error': str(e)}
            )

    def test_nginx_service(self) -> TestResult:
        """Test Nginx service"""
        print(f"\n{Colors.BOLD}{Colors.BLUE}Testing Nginx Service...{Colors.RESET}")
        
        try:
            # Check if nginx is running
            result = subprocess.run(
                ['systemctl', 'is-active', 'nginx'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            is_active = result.returncode == 0 and result.stdout.strip() == 'active'
            
            # Check nginx configuration
            config_result = subprocess.run(
                ['nginx', '-t'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            config_valid = config_result.returncode == 0
            
            # Check if nginx is listening on port 80
            port_check = subprocess.run(
                ['ss', '-tlnp'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            listening_on_80 = ':80' in port_check.stdout if port_check.returncode == 0 else False
            
            if is_active and config_valid:
                return TestResult(
                    "Nginx Service",
                    "PASS",
                    "Nginx is running and configuration is valid",
                    {
                        'status': 'active',
                        'config_valid': config_valid,
                        'listening_on_80': listening_on_80,
                        'config_output': config_result.stdout
                    }
                )
            elif is_active:
                return TestResult(
                    "Nginx Service",
                    "WARN",
                    "Nginx is running but configuration test failed",
                    {
                        'status': 'active',
                        'config_valid': False,
                        'config_error': config_result.stderr
                    }
                )
            else:
                return TestResult(
                    "Nginx Service",
                    "FAIL",
                    "Nginx service is not active",
                    {
                        'status': result.stdout.strip() if result.returncode == 0 else 'unknown',
                        'suggestion': 'Run: sudo systemctl start nginx'
                    }
                )
        except FileNotFoundError:
            # Try alternative method (macOS doesn't have systemctl)
            try:
                # Check if nginx process is running
                result = subprocess.run(
                    ['pgrep', '-f', 'nginx'],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                
                if result.returncode == 0:
                    return TestResult(
                        "Nginx Service",
                        "WARN",
                        "Nginx process found but systemctl not available (may be macOS)",
                        {'processes': result.stdout.strip().split('\n')}
                    )
                else:
                    return TestResult(
                        "Nginx Service",
                        "WARN",
                        "Could not verify Nginx status (systemctl not available)",
                        {'note': 'This may be macOS - manual verification required'}
                    )
            except Exception as e:
                return TestResult(
                    "Nginx Service",
                    "WARN",
                    f"Could not test Nginx service: {str(e)}",
                    {'error': str(e), 'note': 'Manual verification may be required'}
                )
        except Exception as e:
            return TestResult(
                "Nginx Service",
                "FAIL",
                f"Error testing Nginx: {str(e)}",
                {'error': str(e)}
            )

    def test_stripe_keys(self) -> TestResult:
        """Test STRIPE test keys"""
        print(f"\n{Colors.BOLD}{Colors.BLUE}Testing STRIPE Test Keys...{Colors.RESET}")
        
        if not STRIPE_AVAILABLE:
            return TestResult(
                "STRIPE Test Keys",
                "WARN",
                "Skipped - 'stripe' module not installed",
                {'suggestion': 'Install with: pip install stripe'}
            )
        
        try:
            if not self.stripe_config['secret_key']:
                return TestResult(
                    "STRIPE Test Keys",
                    "FAIL",
                    "STRIPE_SECRET_KEY or STRIPE_TEST_SECRET_KEY not found in environment",
                    {'note': 'Set STRIPE_TEST_SECRET_KEY environment variable'}
                )
            
            if not self.stripe_config['publishable_key']:
                return TestResult(
                    "STRIPE Test Keys",
                    "WARN",
                    "STRIPE_PUBLISHABLE_KEY or STRIPE_TEST_PUBLISHABLE_KEY not found",
                    {'secret_key_present': True}
                )
            
            # Test secret key
            stripe.api_key = self.stripe_config['secret_key']
            
            # Check if it's a test key
            is_test_key = self.stripe_config['secret_key'].startswith('sk_test_')
            
            # Try to retrieve account information
            account = stripe.Account.retrieve()
            
            return TestResult(
                "STRIPE Test Keys",
                "PASS",
                f"STRIPE keys are valid ({'TEST' if is_test_key else 'LIVE'} mode)",
                {
                    'secret_key_present': True,
                    'publishable_key_present': bool(self.stripe_config['publishable_key']),
                    'key_type': 'TEST' if is_test_key else 'LIVE',
                    'account_id': account.id if hasattr(account, 'id') else 'N/A',
                    'account_type': account.type if hasattr(account, 'type') else 'N/A'
                }
            )
        except stripe.error.AuthenticationError:
            return TestResult(
                "STRIPE Test Keys",
                "FAIL",
                "STRIPE secret key authentication failed - invalid key",
                {}
            )
        except stripe.error.APIConnectionError:
            return TestResult(
                "STRIPE Test Keys",
                "WARN",
                "Could not connect to STRIPE API - network issue",
                {}
            )
        except Exception as e:
            return TestResult(
                "STRIPE Test Keys",
                "FAIL",
                f"Error testing STRIPE keys: {str(e)}",
                {'error': str(e)}
            )

    def run_all_tests(self):
        """Run all tests"""
        print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.BLUE}MINGUS COMPREHENSIVE TESTING PROTOCOL{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}")
        print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        # Run all tests
        self.log_result(self.test_server_status())
        self.log_result(self.test_database_connection())
        self.log_result(self.test_redis_service())
        self.log_result(self.test_backend_api())
        self.log_result(self.test_frontend_build())
        self.log_result(self.test_nginx_service())
        self.log_result(self.test_stripe_keys())
        
        # Print summary
        self.print_summary()

    def print_summary(self):
        """Print test summary"""
        print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}")
        print(f"{Colors.BOLD}TEST SUMMARY{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}\n")
        
        passed = sum(1 for r in self.results if r.status == "PASS")
        failed = sum(1 for r in self.results if r.status == "FAIL")
        warnings = sum(1 for r in self.results if r.status == "WARN")
        total = len(self.results)
        
        print(f"Total Tests: {total}")
        print(f"{Colors.GREEN}Passed: {passed}{Colors.RESET}")
        print(f"{Colors.RED}Failed: {failed}{Colors.RESET}")
        print(f"{Colors.YELLOW}Warnings: {warnings}{Colors.RESET}\n")
        
        if failed > 0:
            print(f"{Colors.RED}{Colors.BOLD}Failed Tests:{Colors.RESET}")
            for result in self.results:
                if result.status == "FAIL":
                    print(f"  - {result.name}: {result.message}")
        
        if warnings > 0:
            print(f"\n{Colors.YELLOW}{Colors.BOLD}Warnings:{Colors.RESET}")
            for result in self.results:
                if result.status == "WARN":
                    print(f"  - {result.name}: {result.message}")
        
        # Save results to JSON file
        results_file = f"test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(results_file, 'w') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'summary': {
                    'total': total,
                    'passed': passed,
                    'failed': failed,
                    'warnings': warnings
                },
                'results': [
                    {
                        'name': r.name,
                        'status': r.status,
                        'message': r.message,
                        'details': r.details,
                        'timestamp': r.timestamp
                    }
                    for r in self.results
                ]
            }, f, indent=2)
        
        print(f"\n{Colors.BLUE}Detailed results saved to: {results_file}{Colors.RESET}")
        print(f"Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

if __name__ == "__main__":
    tester = ComprehensiveTester()
    tester.run_all_tests()
