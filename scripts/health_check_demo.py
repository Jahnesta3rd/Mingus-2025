#!/usr/bin/env python3
"""
Health Check Endpoints Demo Script

This script demonstrates how to use the Mingus Flask application health check endpoints
programmatically for monitoring and deployment validation.

Usage:
    python scripts/health_check_demo.py
"""

import requests
import json
import time
from datetime import datetime
from typing import Dict, Any, Optional

class HealthCheckClient:
    """Client for interacting with health check endpoints"""
    
    def __init__(self, base_url: str = "http://localhost:5003", timeout: int = 10):
        self.base_url = base_url
        self.timeout = timeout
    
    def get_basic_health(self) -> Dict[str, Any]:
        """Get basic application health"""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=self.timeout)
            return {
                'success': response.status_code == 200,
                'status_code': response.status_code,
                'data': response.json() if response.status_code == 200 else None,
                'error': None if response.status_code == 200 else response.text
            }
        except Exception as e:
            return {
                'success': False,
                'status_code': None,
                'data': None,
                'error': str(e)
            }
    
    def get_detailed_health(self) -> Dict[str, Any]:
        """Get detailed application health with comprehensive system checks"""
        try:
            response = requests.get(f"{self.base_url}/health/detailed", timeout=self.timeout)
            return {
                'success': response.status_code == 200,
                'status_code': response.status_code,
                'data': response.json() if response.status_code == 200 else None,
                'error': None if response.status_code == 200 else response.text
            }
        except Exception as e:
            return {
                'success': False,
                'status_code': None,
                'data': None,
                'error': str(e)
            }
    
    def get_database_health(self) -> Dict[str, Any]:
        """Get database health with connection pool monitoring"""
        try:
            response = requests.get(f"{self.base_url}/health/database", timeout=self.timeout)
            return {
                'success': response.status_code == 200,
                'status_code': response.status_code,
                'data': response.json() if response.status_code == 200 else None,
                'error': None if response.status_code == 200 else response.text
            }
        except Exception as e:
            return {
                'success': False,
                'status_code': None,
                'data': None,
                'error': str(e)
            }
    
    def get_redis_health(self) -> Dict[str, Any]:
        """Get Redis health with cache operations and memory monitoring"""
        try:
            response = requests.get(f"{self.base_url}/health/redis", timeout=self.timeout)
            return {
                'success': response.status_code == 200,
                'status_code': response.status_code,
                'data': response.json() if response.status_code == 200 else None,
                'error': None if response.status_code == 200 else response.text
            }
        except Exception as e:
            return {
                'success': False,
                'status_code': None,
                'data': None,
                'error': str(e)
            }
    
    def get_external_services_health(self) -> Dict[str, Any]:
        """Get external services health (Supabase, Stripe, Resend, Twilio)"""
        try:
            response = requests.get(f"{self.base_url}/health/external", timeout=self.timeout)
            return {
                'success': response.status_code == 200,
                'status_code': response.status_code,
                'data': response.json() if response.status_code == 200 else None,
                'error': None if response.status_code == 200 else response.text
            }
        except Exception as e:
            return {
                'success': False,
                'status_code': None,
                'data': None,
                'error': str(e)
            }
    
    def get_standard_health(self) -> Dict[str, Any]:
        """Get standardized health check with consistent response format"""
        try:
            response = requests.get(f"{self.base_url}/health/standard", timeout=self.timeout)
            return {
                'success': response.status_code == 200,
                'status_code': response.status_code,
                'data': response.json() if response.status_code == 200 else None,
                'error': None if response.status_code == 200 else response.text
            }
        except Exception as e:
            return {
                'success': False,
                'status_code': None,
                'data': None,
                'error': str(e)
            }
    
    def get_metrics_health(self) -> Dict[str, Any]:
        """Get health check with comprehensive Prometheus metrics"""
        try:
            response = requests.get(f"{self.base_url}/health/metrics", timeout=self.timeout)
            return {
                'success': response.status_code == 200,
                'status_code': response.status_code,
                'data': response.json() if response.status_code == 200 else None,
                'error': None if response.status_code == 200 else response.text
            }
        except Exception as e:
            return {
                'success': False,
                'status_code': None,
                'data': None,
                'error': str(e)
            }
    
    def get_prometheus_metrics(self) -> Dict[str, Any]:
        """Get raw Prometheus metrics"""
        try:
            response = requests.get(f"{self.base_url}/metrics", timeout=self.timeout)
            return {
                'success': response.status_code == 200,
                'status_code': response.status_code,
                'data': response.text if response.status_code == 200 else None,
                'error': None if response.status_code == 200 else response.text
            }
        except Exception as e:
            return {
                'success': False,
                'status_code': None,
                'data': None,
                'error': str(e)
            }
    
    def get_system_health(self) -> Dict[str, Any]:
        """Get comprehensive system health"""
        try:
            response = requests.get(f"{self.base_url}/api/system/health/", timeout=self.timeout)
            return {
                'success': response.status_code == 200,
                'status_code': response.status_code,
                'data': response.json() if response.status_code == 200 else None,
                'error': None if response.status_code == 200 else response.text
            }
        except Exception as e:
            return {
                'success': False,
                'status_code': None,
                'data': None,
                'error': str(e)
            }
    
    def get_readiness(self) -> Dict[str, Any]:
        """Check if application is ready to serve traffic"""
        try:
            response = requests.get(f"{self.base_url}/api/system/health/readiness", timeout=self.timeout)
            return {
                'success': response.status_code == 200,
                'status_code': response.status_code,
                'data': response.json() if response.status_code == 200 else None,
                'error': None if response.status_code == 200 else response.text
            }
        except Exception as e:
            return {
                'success': False,
                'status_code': None,
                'data': None,
                'error': str(e)
            }
    
    def get_liveness(self) -> Dict[str, Any]:
        """Check if application is alive"""
        try:
            response = requests.get(f"{self.base_url}/api/system/health/liveness", timeout=self.timeout)
            return {
                'success': response.status_code == 200,
                'status_code': response.status_code,
                'data': response.json() if response.status_code == 200 else None,
                'error': None if response.status_code == 200 else response.text
            }
        except Exception as e:
            return {
                'success': False,
                'status_code': None,
                'data': None,
                'error': str(e)
            }
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get health metrics for monitoring systems"""
        try:
            response = requests.get(f"{self.base_url}/api/system/health/metrics", timeout=self.timeout)
            return {
                'success': response.status_code == 200,
                'status_code': response.status_code,
                'data': response.json() if response.status_code == 200 else None,
                'error': None if response.status_code == 200 else response.text
            }
        except Exception as e:
            return {
                'success': False,
                'status_code': None,
                'data': None,
                'error': str(e)
            }

def print_health_status(name: str, result: Dict[str, Any]):
    """Print formatted health status"""
    print(f"\n🔍 {name}")
    print("-" * 40)
    
    if result['success']:
        print(f"✅ Status: Healthy (HTTP {result['status_code']})")
        if result['data']:
            if 'data' in result['data']:
                # System health response
                data = result['data']['data']
                if 'overall_status' in data:
                    print(f"   Overall Status: {data['overall_status']}")
                if 'services' in data:
                    print("   Services:")
                    for service, status in data['services'].items():
                        if isinstance(status, dict) and 'status' in status:
                            print(f"     - {service}: {status['status']}")
            elif 'status' in result['data']:
                # Basic health response
                print(f"   Status: {result['data']['status']}")
            elif 'ready' in result['data']:
                # Readiness response
                print(f"   Ready: {result['data']['ready']}")
            elif 'alive' in result['data']:
                # Liveness response
                print(f"   Alive: {result['data']['alive']}")
    else:
        print(f"❌ Status: Unhealthy")
        if result['error']:
            print(f"   Error: {result['error']}")
        elif result['status_code']:
            print(f"   HTTP Status: {result['status_code']}")

def demo_basic_monitoring():
    """Demonstrate basic monitoring scenario"""
    print("🚀 Basic Application Monitoring Demo")
    print("=" * 50)
    
    client = HealthCheckClient()
    
    # Basic health check
    basic_health = client.get_basic_health()
    print_health_status("Basic Health Check", basic_health)
    
    # Detailed health check
    detailed_health = client.get_detailed_health()
    print_health_status("Detailed Health Check", detailed_health)
    
    # Database health check
    database_health = client.get_database_health()
    print_health_status("Database Health Check", database_health)
    
    # Redis health check
    redis_health = client.get_redis_health()
    print_health_status("Redis Health Check", redis_health)
    
    # External services health check
    external_health = client.get_external_services_health()
    print_health_status("External Services Health Check", external_health)
    
    # System health check
    system_health = client.get_system_health()
    print_health_status("System Health Check", system_health)
    
    # Readiness check
    readiness = client.get_readiness()
    print_health_status("Readiness Check", readiness)
    
    # Liveness check
    liveness = client.get_liveness()
    print_health_status("Liveness Check", liveness)

def demo_kubernetes_deployment():
    """Demonstrate Kubernetes deployment validation"""
    print("\n🐳 Kubernetes Deployment Validation Demo")
    print("=" * 50)
    
    client = HealthCheckClient()
    
    print("1. Checking if application is alive...")
    liveness = client.get_liveness()
    if liveness['success'] and liveness['data']['data']['alive']:
        print("   ✅ Application is alive")
    else:
        print("   ❌ Application is not responding")
        return False
    
    print("2. Checking if application is ready...")
    readiness = client.get_readiness()
    if readiness['success'] and readiness['data']['data']['ready']:
        print("   ✅ Application is ready to serve traffic")
    else:
        print("   ❌ Application is not ready")
        return False
    
    print("3. Checking system health...")
    system_health = client.get_system_health()
    if system_health['success']:
        data = system_health['data']['data']
        if data['overall_status'] == 'healthy':
            print("   ✅ All systems are healthy")
        else:
            print("   ⚠️  Some systems are unhealthy")
            if 'unhealthy_services' in data:
                print(f"      Unhealthy services: {', '.join(data['unhealthy_services'])}")
    else:
        print("   ❌ Could not check system health")
        return False
    
    print("\n🎉 Deployment validation successful!")
    return True

def demo_database_health():
    """Demonstrate database health monitoring"""
    print("\n🗄️ Database Health Monitoring Demo")
    print("=" * 50)
    
    client = HealthCheckClient()
    
    # Get database health
    db_health = client.get_database_health()
    if db_health['success']:
        data = db_health['data']
        print("📊 Database Health Status:")
        print(f"   Overall Status: {data.get('status', 'N/A')}")
        print(f"   Response Time: {data.get('response_time_ms', 'N/A')}ms")
        
        # Connection status
        connection = data.get('connection', {})
        print(f"   Connection: {'🟢' if connection.get('status') == 'healthy' else '🔴'} {connection.get('status', 'N/A')}")
        if connection.get('error'):
            print(f"     Error: {connection.get('error')}")
        
        # Responsiveness status
        responsiveness = data.get('responsiveness', {})
        print(f"   Responsiveness: {'🟢' if responsiveness.get('status') == 'healthy' else '🔴'} {responsiveness.get('status', 'N/A')}")
        if responsiveness.get('table_count'):
            print(f"     Tables: {responsiveness.get('table_count')}")
        if responsiveness.get('error'):
            print(f"     Error: {responsiveness.get('error')}")
        
        # Connection pool status
        pool = data.get('connection_pool', {})
        print(f"   Connection Pool: {'🟢' if pool.get('status') == 'healthy' else '🟡' if pool.get('status') == 'warning' else '🔴'} {pool.get('status', 'N/A')}")
        if pool.get('info'):
            info = pool.get('info', {})
            print(f"     Pool Size: {info.get('pool_size', 'N/A')}")
            print(f"     Checked In: {info.get('checked_in', 'N/A')}")
            print(f"     Checked Out: {info.get('checked_out', 'N/A')}")
            print(f"     Overflow: {info.get('overflow', 'N/A')}")
            print(f"     Invalid: {info.get('invalid', 'N/A')}")
        if pool.get('error'):
            print(f"     Warning: {pool.get('error')}")
    else:
        print("❌ Could not retrieve database health")

def demo_redis_health():
    """Demonstrate Redis health monitoring"""
    print("\n🔴 Redis Health Monitoring Demo")
    print("=" * 50)
    
    client = HealthCheckClient()
    
    # Get Redis health
    redis_health = client.get_redis_health()
    if redis_health['success']:
        data = redis_health['data']
        print("📊 Redis Health Status:")
        print(f"   Overall Status: {data.get('status', 'N/A')}")
        print(f"   Response Time: {data.get('response_time_ms', 'N/A')}ms")
        
        # Connectivity status
        connectivity = data.get('connectivity', {})
        print(f"   Connectivity: {'🟢' if connectivity.get('status') == 'healthy' else '🔴'} {connectivity.get('status', 'N/A')}")
        if connectivity.get('response_time_ms'):
            print(f"     Response Time: {connectivity.get('response_time_ms')}ms")
        if connectivity.get('host'):
            print(f"     Host: {connectivity.get('host')}:{connectivity.get('port')} (DB: {connectivity.get('db')})")
        if connectivity.get('error'):
            print(f"     Error: {connectivity.get('error')}")
        
        # Cache operations status
        cache = data.get('cache_operations', {})
        print(f"   Cache Operations: {'🟢' if cache.get('status') == 'healthy' else '🔴'} {cache.get('status', 'N/A')}")
        if cache.get('response_time_ms'):
            print(f"     Response Time: {cache.get('response_time_ms')}ms")
        if cache.get('error'):
            print(f"     Error: {cache.get('error')}")
        
        # Memory usage status
        memory = data.get('memory_usage', {})
        print(f"   Memory Usage: {'🟢' if memory.get('status') == 'healthy' else '🟡' if memory.get('status') == 'warning' else '🔴'} {memory.get('status', 'N/A')}")
        if memory.get('info'):
            info = memory.get('info', {})
            print(f"     Used Memory: {info.get('used_memory_human', 'N/A')}")
            print(f"     Peak Memory: {info.get('used_memory_peak_human', 'N/A')}")
            print(f"     RSS Memory: {info.get('used_memory_rss_human', 'N/A')}")
            if info.get('memory_usage_percent'):
                print(f"     Memory Usage: {info.get('memory_usage_percent')}%")
            print(f"     Fragmentation: {info.get('mem_fragmentation_ratio', 'N/A')}")
            print(f"     Connected Clients: {info.get('connected_clients', 'N/A')}")
            print(f"     Uptime: {info.get('uptime_in_seconds', 'N/A')} seconds")
            print(f"     Total Commands: {info.get('total_commands_processed', 'N/A')}")
            print(f"     Cache Hit Rate: {info.get('keyspace_hits', 0)} hits, {info.get('keyspace_misses', 0)} misses")
        if memory.get('error'):
            print(f"     Warning: {memory.get('error')}")
    else:
        print("❌ Could not retrieve Redis health")

def demo_external_services_health():
    """Demonstrate external services health monitoring"""
    print("\n🌐 External Services Health Monitoring Demo")
    print("=" * 50)
    
    client = HealthCheckClient()
    
    # Get external services health
    external_health = client.get_external_services_health()
    if external_health['success']:
        data = external_health['data']
        print("📊 External Services Health Status:")
        print(f"   Overall Status: {data.get('status', 'N/A')}")
        print(f"   Response Time: {data.get('response_time_ms', 'N/A')}ms")
        
        # Check each service
        services = data.get('services', {})
        for service_name, service_data in services.items():
            status = service_data.get('status', 'unknown')
            status_icon = '🟢' if status == 'healthy' else '🟡' if status == 'not_configured' else '🔴'
            print(f"   {service_name.title()}: {status_icon} {status}")
            
            if service_data.get('response_time_ms'):
                print(f"     Response Time: {service_data.get('response_time_ms')}ms")
            if service_data.get('error'):
                print(f"     Error: {service_data.get('error')}")
        
        # Summary
        unhealthy_services = data.get('unhealthy_services', [])
        warning_services = data.get('warning_services', [])
        critical_failures = data.get('critical_services_failing', False)
        
        if critical_failures:
            print(f"\n   ⚠️  Critical services failing: {', '.join(unhealthy_services)}")
        elif unhealthy_services:
            print(f"\n   ⚠️  Unhealthy services: {', '.join(unhealthy_services)}")
        if warning_services:
            print(f"\n   ℹ️  Services not configured: {', '.join(warning_services)}")
    else:
        print("❌ Could not retrieve external services health")

def demo_external_services_health():
    """Demonstrate external services health monitoring"""
    print("\n🌐 External Services Health Monitoring Demo")
    print("=" * 50)
    
    client = HealthCheckClient()
    
    # Get external services health
    external_health = client.get_external_services_health()
    if external_health['success']:
        data = external_health['data']
        print("📊 External Services Health Status:")
        print(f"   Overall Status: {data.get('status', 'N/A')}")
        print(f"   Response Time: {data.get('response_time_ms', 'N/A')}ms")
        
        # Summary
        summary = data.get('summary', {})
        print(f"   Summary: {summary.get('healthy_services', 0)} healthy, {summary.get('unhealthy_services', 0)} unhealthy, {summary.get('not_configured_services', 0)} not configured")
        
        # Individual services
        services = data.get('services', {})
        for service_name, service_data in services.items():
            status = service_data.get('status', 'N/A')
            status_icon = '🟢' if status == 'healthy' else '🟡' if status == 'not_configured' else '🔴'
            print(f"   {service_name.replace('_', ' ').title()}: {status_icon} {status}")
            
            if service_data.get('response_time_ms'):
                print(f"     Response Time: {service_data.get('response_time_ms')}ms")
            if service_data.get('error'):
                print(f"     Error: {service_data.get('error')}")
        
        # Unhealthy services
        unhealthy = data.get('unhealthy_services', [])
        if unhealthy:
            print(f"\n   🔴 Unhealthy Services: {', '.join(unhealthy)}")
        
        # Not configured services
        not_configured = data.get('not_configured_services', [])
        if not_configured:
            print(f"\n   🟡 Not Configured Services: {', '.join(not_configured)}")
    else:
        print("❌ Could not retrieve external services health")

def demo_monitoring_integration():
    """Demonstrate monitoring system integration"""
    print("\n📊 Monitoring System Integration Demo")
    print("=" * 50)
    
    client = HealthCheckClient()
    
    # Get metrics
    metrics = client.get_metrics()
    if metrics['success']:
        data = metrics['data']['data']
        print("📈 Health Metrics:")
        print(f"   Database Status: {'🟢' if data.get('mingus_database_status') == 1 else '🔴'}")
        print(f"   Redis Status: {'🟢' if data.get('mingus_redis_status') == 1 else '🔴'}")
        print(f"   Database Response Time: {data.get('mingus_database_response_time_ms', 'N/A')}ms")
        print(f"   Redis Response Time: {data.get('mingus_redis_response_time_ms', 'N/A')}ms")
        print(f"   CPU Usage: {data.get('mingus_cpu_usage_percent', 'N/A')}%")
        print(f"   Memory Usage: {data.get('mingus_memory_usage_percent', 'N/A')}%")
        print(f"   Disk Usage: {data.get('mingus_disk_usage_percent', 'N/A')}%")
        print(f"   Uptime: {data.get('mingus_uptime_seconds', 'N/A')} seconds")
    else:
        print("❌ Could not retrieve metrics")

def demo_continuous_monitoring():
    """Demonstrate continuous monitoring"""
    print("\n🔄 Continuous Monitoring Demo")
    print("=" * 50)
    
    client = HealthCheckClient()
    
    print("Starting continuous monitoring (press Ctrl+C to stop)...")
    print("Time | Basic Health | System Health | Readiness | Liveness")
    print("-" * 70)
    
    try:
        for i in range(10):  # Monitor for 10 iterations
            timestamp = datetime.now().strftime("%H:%M:%S")
            
            # Get all health checks
            basic = client.get_basic_health()
            system = client.get_system_health()
            readiness = client.get_readiness()
            liveness = client.get_liveness()
            
            # Format status indicators
            basic_status = "🟢" if basic['success'] else "🔴"
            system_status = "🟢" if system['success'] and system['data']['data']['overall_status'] == 'healthy' else "🔴"
            readiness_status = "🟢" if readiness['success'] and readiness['data']['data']['ready'] else "🔴"
            liveness_status = "🟢" if liveness['success'] and liveness['data']['data']['alive'] else "🔴"
            
            print(f"{timestamp} | {basic_status}         | {system_status}          | {readiness_status}        | {liveness_status}")
            
            time.sleep(2)  # Check every 2 seconds
            
    except KeyboardInterrupt:
        print("\n⏹️  Monitoring stopped by user")

def demo_standard_health():
    """Demonstrate standardized health check with consistent response format"""
    print("\n📋 Standardized Health Check Demo")
    print("=" * 50)
    
    client = HealthCheckClient()
    
    # Get standardized health
    standard_health = client.get_standard_health()
    if standard_health['success']:
        data = standard_health['data']
        print("📊 Standardized Health Status:")
        print(f"   Overall Status: {data.get('status', 'N/A')}")
        print(f"   Version: {data.get('version', 'N/A')}")
        print(f"   Timestamp: {data.get('timestamp', 'N/A')}")
        
        # Check individual components
        checks = data.get('checks', {})
        for component, check_data in checks.items():
            if component == 'external_apis':
                print(f"   External APIs:")
                for api_name, api_data in check_data.items():
                    status = api_data.get('status', 'unknown')
                    status_icon = '🟢' if status == 'healthy' else '🔴'
                    print(f"     {api_name.title()}: {status_icon} {status}")
            else:
                status = check_data.get('status', 'unknown')
                response_time = check_data.get('response_time', 'N/A')
                status_icon = '🟢' if status == 'healthy' else '🔴'
                print(f"   {component.title()}: {status_icon} {status} ({response_time}ms)")
    else:
        print("❌ Could not retrieve standardized health")
        print(f"Error: {standard_health['error']}")

def demo_metrics_health():
    """Demonstrate health check with comprehensive Prometheus metrics"""
    print("\n📈 Metrics Health Check Demo")
    print("=" * 50)
    
    client = HealthCheckClient()
    
    # Get metrics health
    metrics_health = client.get_metrics_health()
    if metrics_health['success']:
        data = metrics_health['data']
        print("📊 Metrics Health Status:")
        print(f"   Overall Status: {data.get('status', 'N/A')}")
        print(f"   Response Time: {data.get('response_time_ms', 'N/A')}ms")
        print(f"   Version: {data.get('version', 'N/A')}")
        
        # Check individual components with metrics
        checks = data.get('checks', {})
        for component, check_data in checks.items():
            if component == 'external_apis':
                print(f"   External APIs:")
                for api_name, api_data in check_data.items():
                    status = api_data.get('status', 'unknown')
                    response_time = api_data.get('response_time_ms', 'N/A')
                    status_icon = '🟢' if status == 'healthy' else '🔴'
                    print(f"     {api_name.title()}: {status_icon} {status} ({response_time}ms)")
            else:
                status = check_data.get('status', 'unknown')
                response_time = check_data.get('response_time_ms', 'N/A')
                status_icon = '🟢' if status == 'healthy' else '🔴'
                print(f"   {component.title()}: {status_icon} {status} ({response_time}ms)")
        
        # Display metrics
        metrics = data.get('metrics', {})
        if 'system_metrics' in metrics:
            sys_metrics = metrics['system_metrics']
            print(f"\n💻 System Metrics:")
            print(f"   CPU Usage: {sys_metrics.get('cpu_percent', 'N/A')}%")
            print(f"   Memory Usage: {sys_metrics.get('memory_percent', 'N/A')}%")
            print(f"   Disk Usage: {sys_metrics.get('disk_percent', 'N/A')}%")
        
        if 'database_metrics' in metrics:
            db_metrics = metrics['database_metrics']
            print(f"\n🗄️  Database Metrics:")
            print(f"   Connection Pool Size: {db_metrics.get('connection_pool_size', 'N/A')}")
            print(f"   Connections Checked Out: {db_metrics.get('connections_checked_out', 'N/A')}")
        
        if 'redis_metrics' in metrics:
            redis_metrics = metrics['redis_metrics']
            print(f"\n🔴 Redis Metrics:")
            print(f"   Memory Usage: {redis_metrics.get('memory_usage_bytes', 'N/A')} bytes")
            print(f"   Connected Clients: {redis_metrics.get('connected_clients', 'N/A')}")
            print(f"   Total Commands: {redis_metrics.get('total_commands_processed', 'N/A')}")
    else:
        print("❌ Could not retrieve metrics health")
        print(f"Error: {metrics_health['error']}")

def demo_prometheus_metrics():
    """Demonstrate Prometheus metrics endpoint"""
    print("\n📊 Prometheus Metrics Demo")
    print("=" * 50)
    
    client = HealthCheckClient()
    
    # Get raw Prometheus metrics
    metrics = client.get_prometheus_metrics()
    if metrics['success']:
        print("📈 Prometheus Metrics Retrieved Successfully")
        print(f"Response Length: {len(metrics['data'])} characters")
        
        # Parse and display key metrics
        lines = metrics['data'].split('\n')
        print("\n🔍 Key Metrics Found:")
        
        metric_types = {
            'health_check_duration_seconds': 'Health Check Duration',
            'health_check_failures_total': 'Health Check Failures',
            'health_check_status': 'Health Check Status',
            'system_memory_bytes': 'System Memory',
            'system_cpu_percent': 'System CPU',
            'db_connection_pool_size': 'Database Pool Size',
            'redis_memory_bytes': 'Redis Memory'
        }
        
        for line in lines:
            for metric_name, display_name in metric_types.items():
                if line.startswith(metric_name):
                    print(f"   {display_name}: {line}")
                    break
        
        print(f"\n📋 Total Metrics Lines: {len(lines)}")
    else:
        print("❌ Could not retrieve Prometheus metrics")
        print(f"Error: {metrics['error']}")

def main():
    """Main demo function"""
    print("🏥 Mingus Health Check Endpoints Demo")
    print("=" * 60)
    print("This demo shows how to use the health check endpoints")
    print("for monitoring and deployment validation.")
    print()
    
    # Check if server is available
    try:
        response = requests.get("http://localhost:5003/", timeout=5)
        if response.status_code != 200:
            print("❌ Server is running but root endpoint is not responding correctly")
            return
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server at http://localhost:5003")
        print("   Make sure the Flask application is running:")
        print("   python app.py")
        return
    except Exception as e:
        print(f"❌ Error connecting to server: {e}")
        return
    
    print("✅ Server is running and accessible")
    
    # Run demos
    demo_basic_monitoring()
    demo_kubernetes_deployment()
    demo_database_health()
    demo_redis_health()
    demo_external_services_health()
    demo_standard_health()
    demo_metrics_health()
    demo_prometheus_metrics()
    demo_monitoring_integration()
    demo_continuous_monitoring()
    
    print("\n🎉 Demo completed!")
    print("\nFor more information, see: docs/HEALTH_CHECK_ENDPOINTS.md")

if __name__ == "__main__":
    main() 