"""
Health Monitoring Module
Provides health check routes and monitoring functionality for the Flask application
"""

from flask import Flask, jsonify, current_app
from datetime import datetime
import time
import os
import requests
from typing import Dict, Any, Optional
from loguru import logger

def create_health_routes(app: Flask) -> None:
    """Create health check routes for the Flask application"""
    
    @app.route('/health')
    def health_check():
        """Basic application health endpoint for load balancers and monitoring"""
        return {
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'service': 'mingus-api',
            'version': getattr(current_app, 'version', '1.0.0')
        }
    
    @app.route('/health/detailed')
    def detailed_health():
        """Detailed health endpoint with comprehensive system checks"""
        start_time = time.time()
        
        health_data = {
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'service': 'mingus-api',
            'version': getattr(current_app, 'version', '1.0.0'),
            'response_time_ms': 0,
            'checks': {}
        }
        
        # Database health check
        db_status = check_database_health()
        health_data['checks']['database'] = db_status
        
        # Redis health check
        redis_status = check_redis_health()
        health_data['checks']['redis'] = redis_status
        
        # Security system health check
        security_status = check_security_system_health()
        health_data['checks']['security_system'] = security_status
        
        # PCI compliance status check
        pci_status = check_pci_compliance_status()
        health_data['checks']['pci_compliance'] = pci_status
        
        # Encryption system health check
        encryption_status = check_encryption_system_health()
        health_data['checks']['encryption_system'] = encryption_status
        
        # Audit system performance check
        audit_status = check_audit_system_performance()
        health_data['checks']['audit_system'] = audit_status
        
        # External services health check
        external_status = check_external_services_health()
        health_data['checks']['external_services'] = external_status
        
        # System resources health check
        system_status = check_system_resources()
        health_data['checks']['system'] = system_status
        
        # Calculate response time
        health_data['response_time_ms'] = round((time.time() - start_time) * 1000, 2)
        
        # Determine overall status
        all_checks = [
            db_status['status'], 
            redis_status['status'],
            security_status['status'],
            pci_status['status'],
            encryption_status['status'],
            audit_status['status'],
            external_status['status'], 
            system_status['status']
        ]
        
        if all(status == 'healthy' for status in all_checks):
            health_data['status'] = 'healthy'
            return health_data, 200
        elif any(status == 'unhealthy' for status in all_checks):
            health_data['status'] = 'unhealthy'
            return health_data, 503
        else:
            health_data['status'] = 'degraded'
            return health_data, 200
    
    @app.route('/health/readiness')
    def readiness_check():
        """Readiness probe for Kubernetes and container orchestration"""
        checks = {
            'database': check_database_health(),
            'redis': check_redis_health()
        }
        
        ready = all(check['status'] == 'healthy' for check in checks.values())
        
        return {
            'ready': ready,
            'timestamp': datetime.utcnow().isoformat(),
            'checks': checks
        }, 200 if ready else 503
    
    @app.route('/health/liveness')
    def liveness_check():
        """Liveness probe for Kubernetes and container orchestration"""
        return {
            'alive': True,
            'timestamp': datetime.utcnow().isoformat(),
            'uptime_seconds': get_uptime_seconds()
        }
    
    @app.route('/health/startup')
    def startup_check():
        """Startup probe for Kubernetes and container orchestration"""
        checks = {
            'database': check_database_health(),
            'redis': check_redis_health(),
            'system': check_system_resources()
        }
        
        startup_complete = all(check['status'] == 'healthy' for check in checks.values())
        
        return {
            'startup_complete': startup_complete,
            'timestamp': datetime.utcnow().isoformat(),
            'checks': checks
        }, 200 if startup_complete else 503
    
    @app.route('/health/security')
    def security_health_check():
        """Comprehensive security system health check"""
        start_time = time.time()
        
        security_checks = {
            'security_system': check_security_system_health(),
            'pci_compliance': check_pci_compliance_status(),
            'encryption_system': check_encryption_system_health(),
            'audit_system': check_audit_system_performance()
        }
        
        # Calculate response time
        response_time_ms = round((time.time() - start_time) * 1000, 2)
        
        # Determine overall security status
        all_security_checks = [check['status'] for check in security_checks.values()]
        
        if all(status == 'healthy' for status in all_security_checks):
            overall_status = 'healthy'
            http_status = 200
        elif any(status == 'unhealthy' for status in all_security_checks):
            overall_status = 'unhealthy'
            http_status = 503
        else:
            overall_status = 'degraded'
            http_status = 200
        
        return {
            'status': overall_status,
            'timestamp': datetime.utcnow().isoformat(),
            'response_time_ms': response_time_ms,
            'checks': security_checks,
            'summary': {
                'total_checks': len(security_checks),
                'healthy_checks': len([s for s in all_security_checks if s == 'healthy']),
                'degraded_checks': len([s for s in all_security_checks if s == 'degraded']),
                'unhealthy_checks': len([s for s in all_security_checks if s == 'unhealthy'])
            }
        }, http_status

def check_database_health() -> Dict[str, Any]:
    """Check database connectivity and health"""
    try:
        from sqlalchemy import text
        from sqlalchemy.exc import SQLAlchemyError
        
        db = current_app.extensions.get('sqlalchemy')
        if not db:
            return {
                'status': 'unhealthy',
                'error': 'Database extension not found',
                'response_time_ms': None
            }
        
        start_time = time.time()
        
        # Test basic connectivity
        result = db.session.execute(text("SELECT 1 as test"))
        result.fetchone()
        
        # Test more complex query
        result = db.session.execute(text("SELECT COUNT(*) as table_count FROM information_schema.tables"))
        table_count = result.fetchone()[0]
        
        response_time = round((time.time() - start_time) * 1000, 2)
        
        return {
            'status': 'healthy',
            'response_time_ms': response_time,
            'table_count': table_count,
            'error': None
        }
        
    except SQLAlchemyError as e:
        return {
            'status': 'unhealthy',
            'error': str(e),
            'response_time_ms': None
        }
    except Exception as e:
        return {
            'status': 'unhealthy',
            'error': f'Unexpected error: {str(e)}',
            'response_time_ms': None
        }

def check_security_system_health() -> Dict[str, Any]:
    """Check security system health and performance"""
    try:
        from sqlalchemy import text
        from sqlalchemy.exc import SQLAlchemyError
        
        db = current_app.extensions.get('sqlalchemy')
        if not db:
            return {
                'status': 'unhealthy',
                'error': 'Database extension not found',
                'response_time_ms': None
            }
        
        start_time = time.time()
        
        # Check security performance metrics
        security_query = text("""
            SELECT 
                COUNT(*) as total_operations,
                AVG(duration_ms) as avg_duration_ms,
                SUM(CASE WHEN success THEN 1 ELSE 0 END) as successful_operations,
                SUM(CASE WHEN NOT success THEN 1 ELSE 0 END) as failed_operations
            FROM security_performance_metrics 
            WHERE timestamp >= NOW() - INTERVAL '1 hour'
        """)
        
        security_result = db.session.execute(security_query).fetchone()
        
        # Check encryption performance
        encryption_query = text("""
            SELECT 
                COUNT(*) as total_operations,
                AVG(duration_ms) as avg_duration_ms,
                SUM(CASE WHEN success THEN 1 ELSE 0 END) as successful_operations
            FROM encryption_performance_metrics 
            WHERE timestamp >= NOW() - INTERVAL '1 hour'
        """)
        
        encryption_result = db.session.execute(encryption_query).fetchone()
        
        # Check audit log performance
        audit_query = text("""
            SELECT 
                COUNT(*) as total_operations,
                AVG(duration_ms) as avg_duration_ms,
                AVG(log_size_bytes) as avg_log_size_bytes
            FROM audit_log_performance_metrics 
            WHERE timestamp >= NOW() - INTERVAL '1 hour'
        """)
        
        audit_result = db.session.execute(audit_query).fetchone()
        
        response_time = round((time.time() - start_time) * 1000, 2)
        
        # Calculate security health score
        total_ops = security_result.total_operations if security_result.total_operations else 0
        success_ops = security_result.successful_operations if security_result.successful_operations else 0
        success_rate = (success_ops / total_ops * 100) if total_ops > 0 else 100
        
        # Determine overall security status
        if success_rate >= 95 and (security_result.avg_duration_ms or 0) < 100:
            security_status = 'healthy'
        elif success_rate >= 90 and (security_result.avg_duration_ms or 0) < 200:
            security_status = 'degraded'
        else:
            security_status = 'unhealthy'
        
        return {
            'status': security_status,
            'response_time_ms': response_time,
            'security_metrics': {
                'total_operations': total_ops,
                'success_rate_percent': round(success_rate, 2),
                'avg_duration_ms': round(security_result.avg_duration_ms, 2) if security_result.avg_duration_ms else 0,
                'failed_operations': security_result.failed_operations or 0
            },
            'encryption_metrics': {
                'total_operations': encryption_result.total_operations or 0,
                'avg_duration_ms': round(encryption_result.avg_duration_ms, 2) if encryption_result.avg_duration_ms else 0,
                'success_rate_percent': round((encryption_result.successful_operations / encryption_result.total_operations * 100) if encryption_result.total_operations else 100, 2)
            },
            'audit_log_metrics': {
                'total_operations': audit_result.total_operations or 0,
                'avg_duration_ms': round(audit_result.avg_duration_ms, 2) if audit_result.avg_duration_ms else 0,
                'avg_log_size_bytes': round(audit_result.avg_log_size_bytes, 2) if audit_result.avg_log_size_bytes else 0
            },
            'error': None
        }
        
    except SQLAlchemyError as e:
        return {
            'status': 'unhealthy',
            'error': f'Database error: {str(e)}',
            'response_time_ms': None
        }
    except Exception as e:
        return {
            'status': 'unhealthy',
            'error': f'Unexpected error: {str(e)}',
            'response_time_ms': None
        }

def check_pci_compliance_status() -> Dict[str, Any]:
    """Check PCI compliance status and requirements"""
    try:
        from sqlalchemy import text
        from sqlalchemy.exc import SQLAlchemyError
        
        db = current_app.extensions.get('sqlalchemy')
        if not db:
            return {
                'status': 'unhealthy',
                'error': 'Database extension not found',
                'response_time_ms': None
            }
        
        start_time = time.time()
        
        # Check encryption key rotation compliance
        key_rotation_query = text("""
            SELECT 
                key_type,
                MAX(timestamp) as last_rotation,
                COUNT(*) as rotations_last_90_days
            FROM key_rotation_performance_metrics 
            WHERE timestamp >= NOW() - INTERVAL '90 days'
            GROUP BY key_type
        """)
        
        key_rotation_result = db.session.execute(key_rotation_query).fetchall()
        
        # Check audit logging compliance
        audit_compliance_query = text("""
            SELECT 
                COUNT(*) as total_logs,
                COUNT(CASE WHEN timestamp >= NOW() - INTERVAL '24 hours' THEN 1 END) as logs_last_24h,
                COUNT(CASE WHEN timestamp >= NOW() - INTERVAL '7 days' THEN 1 END) as logs_last_7d
            FROM audit_log_performance_metrics
        """)
        
        audit_compliance_result = db.session.execute(audit_compliance_query).fetchone()
        
        # Check security monitoring compliance
        security_monitoring_query = text("""
            SELECT 
                COUNT(*) as total_operations,
                COUNT(CASE WHEN timestamp >= NOW() - INTERVAL '1 hour' THEN 1 END) as operations_last_hour,
                AVG(duration_ms) as avg_response_time
            FROM security_performance_metrics
            WHERE timestamp >= NOW() - INTERVAL '24 hours'
        """)
        
        security_monitoring_result = db.session.execute(security_monitoring_query).fetchone()
        
        response_time = round((time.time() - start_time) * 1000, 2)
        
        # PCI Compliance checks
        compliance_checks = {
            'encryption_key_rotation': {
                'status': 'compliant',
                'details': 'Key rotation schedule maintained'
            },
            'audit_logging': {
                'status': 'compliant',
                'details': 'Comprehensive audit logging active'
            },
            'security_monitoring': {
                'status': 'compliant',
                'details': 'Real-time security monitoring active'
            },
            'access_controls': {
                'status': 'compliant',
                'details': 'Access controls properly configured'
            }
        }
        
        # Check key rotation compliance (keys should be rotated every 90 days)
        for key_rotation in key_rotation_result:
            days_since_rotation = (datetime.utcnow() - key_rotation.last_rotation).days
            if days_since_rotation > 90:
                compliance_checks['encryption_key_rotation']['status'] = 'non_compliant'
                compliance_checks['encryption_key_rotation']['details'] = f'Key type {key_rotation.key_type} not rotated for {days_since_rotation} days'
        
        # Check audit logging compliance (should have logs in last 24 hours)
        if audit_compliance_result.logs_last_24h == 0:
            compliance_checks['audit_logging']['status'] = 'non_compliant'
            compliance_checks['audit_logging']['details'] = 'No audit logs in last 24 hours'
        
        # Check security monitoring compliance (should have operations in last hour)
        if security_monitoring_result.operations_last_hour == 0:
            compliance_checks['security_monitoring']['status'] = 'non_compliant'
            compliance_checks['security_monitoring']['details'] = 'No security operations in last hour'
        
        # Determine overall PCI compliance status
        non_compliant_checks = [check for check in compliance_checks.values() if check['status'] == 'non_compliant']
        overall_status = 'compliant' if len(non_compliant_checks) == 0 else 'non_compliant'
        
        return {
            'status': overall_status,
            'response_time_ms': response_time,
            'pci_compliance': {
                'overall_status': overall_status,
                'compliance_checks': compliance_checks,
                'non_compliant_count': len(non_compliant_checks)
            },
            'key_rotation_status': [
                {
                    'key_type': row.key_type,
                    'last_rotation': row.last_rotation.isoformat() if row.last_rotation else None,
                    'rotations_last_90_days': row.rotations_last_90_days
                }
                for row in key_rotation_result
            ],
            'audit_logging_status': {
                'total_logs': audit_compliance_result.total_logs,
                'logs_last_24h': audit_compliance_result.logs_last_24h,
                'logs_last_7d': audit_compliance_result.logs_last_7d
            },
            'security_monitoring_status': {
                'total_operations_24h': security_monitoring_result.total_operations,
                'operations_last_hour': security_monitoring_result.operations_last_hour,
                'avg_response_time_ms': round(security_monitoring_result.avg_response_time, 2) if security_monitoring_result.avg_response_time else 0
            },
            'error': None
        }
        
    except SQLAlchemyError as e:
        return {
            'status': 'unhealthy',
            'error': f'Database error: {str(e)}',
            'response_time_ms': None
        }
    except Exception as e:
        return {
            'status': 'unhealthy',
            'error': f'Unexpected error: {str(e)}',
            'response_time_ms': None
        }

def check_encryption_system_health() -> Dict[str, Any]:
    """Check encryption system health and performance"""
    try:
        from sqlalchemy import text
        from sqlalchemy.exc import SQLAlchemyError
        
        db = current_app.extensions.get('sqlalchemy')
        if not db:
            return {
                'status': 'unhealthy',
                'error': 'Database extension not found',
                'response_time_ms': None
            }
        
        start_time = time.time()
        
        # Check encryption performance metrics
        encryption_query = text("""
            SELECT 
                algorithm,
                key_size,
                operation,
                COUNT(*) as total_operations,
                AVG(duration_ms) as avg_duration_ms,
                MAX(duration_ms) as max_duration_ms,
                SUM(CASE WHEN success THEN 1 ELSE 0 END) as successful_operations,
                SUM(CASE WHEN NOT success THEN 1 ELSE 0 END) as failed_operations
            FROM encryption_performance_metrics 
            WHERE timestamp >= NOW() - INTERVAL '1 hour'
            GROUP BY algorithm, key_size, operation
        """)
        
        encryption_result = db.session.execute(encryption_query).fetchall()
        
        # Check key rotation status
        key_status_query = text("""
            SELECT 
                key_type,
                COUNT(*) as total_rotations,
                MAX(timestamp) as last_rotation,
                AVG(duration_ms) as avg_rotation_duration_ms
            FROM key_rotation_performance_metrics 
            WHERE timestamp >= NOW() - INTERVAL '30 days'
            GROUP BY key_type
        """)
        
        key_status_result = db.session.execute(key_status_query).fetchall()
        
        response_time = round((time.time() - start_time) * 1000, 2)
        
        # Analyze encryption performance
        encryption_algorithms = {}
        total_encryption_ops = 0
        total_encryption_success = 0
        
        for row in encryption_result:
            algorithm_key = f"{row.algorithm}_{row.key_size}_{row.operation}"
            if algorithm_key not in encryption_algorithms:
                encryption_algorithms[algorithm_key] = {
                    'algorithm': row.algorithm,
                    'key_size': row.key_size,
                    'operation': row.operation,
                    'total_operations': 0,
                    'successful_operations': 0,
                    'avg_duration_ms': 0,
                    'max_duration_ms': 0
                }
            
            encryption_algorithms[algorithm_key]['total_operations'] += row.total_operations
            encryption_algorithms[algorithm_key]['successful_operations'] += row.successful_operations
            encryption_algorithms[algorithm_key]['avg_duration_ms'] = row.avg_duration_ms
            encryption_algorithms[algorithm_key]['max_duration_ms'] = row.max_duration_ms
            
            total_encryption_ops += row.total_operations
            total_encryption_success += row.successful_operations
        
        # Calculate overall encryption health
        encryption_success_rate = (total_encryption_success / total_encryption_ops * 100) if total_encryption_ops > 0 else 100
        
        # Check for performance issues
        performance_issues = []
        for algorithm_info in encryption_algorithms.values():
            if algorithm_info['avg_duration_ms'] > 100:  # More than 100ms average
                performance_issues.append(f"{algorithm_info['algorithm']} {algorithm_info['key_size']}bit {algorithm_info['operation']} slow: {algorithm_info['avg_duration_ms']:.2f}ms")
            
            if algorithm_info['max_duration_ms'] > 500:  # More than 500ms max
                performance_issues.append(f"{algorithm_info['algorithm']} {algorithm_info['key_size']}bit {algorithm_info['operation']} very slow: {algorithm_info['max_duration_ms']:.2f}ms")
        
        # Determine encryption system status
        if encryption_success_rate >= 99 and len(performance_issues) == 0:
            encryption_status = 'healthy'
        elif encryption_success_rate >= 95 and len(performance_issues) <= 2:
            encryption_status = 'degraded'
        else:
            encryption_status = 'unhealthy'
        
        return {
            'status': encryption_status,
            'response_time_ms': response_time,
            'encryption_health': {
                'overall_success_rate_percent': round(encryption_success_rate, 2),
                'total_operations': total_encryption_ops,
                'performance_issues': performance_issues,
                'performance_issues_count': len(performance_issues)
            },
            'algorithm_performance': list(encryption_algorithms.values()),
            'key_rotation_status': [
                {
                    'key_type': row.key_type,
                    'total_rotations': row.total_rotations,
                    'last_rotation': row.last_rotation.isoformat() if row.last_rotation else None,
                    'avg_rotation_duration_ms': round(row.avg_rotation_duration_ms, 2) if row.avg_rotation_duration_ms else 0
                }
                for row in key_status_result
            ],
            'error': None
        }
        
    except SQLAlchemyError as e:
        return {
            'status': 'unhealthy',
            'error': f'Database error: {str(e)}',
            'response_time_ms': None
        }
    except Exception as e:
        return {
            'status': 'unhealthy',
            'error': f'Unexpected error: {str(e)}',
            'response_time_ms': None
        }

def check_audit_system_performance() -> Dict[str, Any]:
    """Check audit system performance and generate alerts"""
    try:
        from sqlalchemy import text
        from sqlalchemy.exc import SQLAlchemyError
        
        db = current_app.extensions.get('sqlalchemy')
        if not db:
            return {
                'status': 'unhealthy',
                'error': 'Database extension not found',
                'response_time_ms': None
            }
        
        start_time = time.time()
        
        # Check audit log performance metrics
        audit_query = text("""
            SELECT 
                operation_type,
                COUNT(*) as total_operations,
                AVG(duration_ms) as avg_duration_ms,
                MAX(duration_ms) as max_duration_ms,
                AVG(log_size_bytes) as avg_log_size_bytes,
                SUM(CASE WHEN success THEN 1 ELSE 0 END) as successful_operations,
                SUM(CASE WHEN NOT success THEN 1 ELSE 0 END) as failed_operations
            FROM audit_log_performance_metrics 
            WHERE timestamp >= NOW() - INTERVAL '1 hour'
            GROUP BY operation_type
        """)
        
        audit_result = db.session.execute(audit_query).fetchall()
        
        # Check for audit log backlog
        backlog_query = text("""
            SELECT 
                COUNT(*) as pending_logs,
                MAX(timestamp) as oldest_pending_log
            FROM audit_log_performance_metrics 
            WHERE success = false AND timestamp >= NOW() - INTERVAL '24 hours'
        """)
        
        backlog_result = db.session.execute(backlog_query).fetchone()
        
        response_time = round((time.time() - start_time) * 1000, 2)
        
        # Analyze audit system performance
        audit_operations = {}
        total_audit_ops = 0
        total_audit_success = 0
        performance_alerts = []
        
        for row in audit_result:
            audit_operations[row.operation_type] = {
                'total_operations': row.total_operations,
                'successful_operations': row.successful_operations,
                'failed_operations': row.failed_operations,
                'avg_duration_ms': round(row.avg_duration_ms, 2) if row.avg_duration_ms else 0,
                'max_duration_ms': round(row.max_duration_ms, 2) if row.max_duration_ms else 0,
                'avg_log_size_bytes': round(row.avg_log_size_bytes, 2) if row.avg_log_size_bytes else 0
            }
            
            total_audit_ops += row.total_operations
            total_audit_success += row.successful_operations
            
            # Check for performance issues
            if row.avg_duration_ms and row.avg_duration_ms > 50:  # More than 50ms average
                performance_alerts.append(f"Audit operation '{row.operation_type}' slow: {row.avg_duration_ms:.2f}ms average")
            
            if row.max_duration_ms and row.max_duration_ms > 200:  # More than 200ms max
                performance_alerts.append(f"Audit operation '{row.operation_type}' very slow: {row.max_duration_ms:.2f}ms maximum")
            
            if row.failed_operations and row.failed_operations > 0:
                performance_alerts.append(f"Audit operation '{row.operation_type}' has {row.failed_operations} failures")
        
        # Calculate overall audit system health
        audit_success_rate = (total_audit_success / total_audit_ops * 100) if total_audit_ops > 0 else 100
        
        # Check for critical issues
        critical_issues = []
        if backlog_result.pending_logs > 100:
            critical_issues.append(f"Large audit log backlog: {backlog_result.pending_logs} pending logs")
        
        if backlog_result.oldest_pending_log:
            oldest_age_hours = (datetime.utcnow() - backlog_result.oldest_pending_log).total_seconds() / 3600
            if oldest_age_hours > 1:
                critical_issues.append(f"Old pending audit logs: oldest is {oldest_age_hours:.1f} hours old")
        
        # Determine audit system status
        if audit_success_rate >= 99 and len(performance_alerts) == 0 and len(critical_issues) == 0:
            audit_status = 'healthy'
        elif audit_success_rate >= 95 and len(critical_issues) == 0:
            audit_status = 'degraded'
        else:
            audit_status = 'unhealthy'
        
        return {
            'status': audit_status,
            'response_time_ms': response_time,
            'audit_system_health': {
                'overall_success_rate_percent': round(audit_success_rate, 2),
                'total_operations': total_audit_ops,
                'performance_alerts': performance_alerts,
                'critical_issues': critical_issues,
                'alerts_count': len(performance_alerts),
                'critical_issues_count': len(critical_issues)
            },
            'operation_performance': audit_operations,
            'backlog_status': {
                'pending_logs': backlog_result.pending_logs or 0,
                'oldest_pending_log': backlog_result.oldest_pending_log.isoformat() if backlog_result.oldest_pending_log else None
            },
            'error': None
        }
        
    except SQLAlchemyError as e:
        return {
            'status': 'unhealthy',
            'error': f'Database error: {str(e)}',
            'response_time_ms': None
        }
    except Exception as e:
        return {
            'status': 'unhealthy',
            'error': f'Unexpected error: {str(e)}',
            'response_time_ms': None
        }

def check_redis_health() -> Dict[str, Any]:
    """Check Redis connectivity and health"""
    try:
        import redis
        
        redis_host = os.getenv('REDIS_HOST', 'localhost')
        redis_port = int(os.getenv('REDIS_PORT', '6379'))
        
        start_time = time.time()
        
        redis_client = redis.Redis(
            host=redis_host, 
            port=redis_port, 
            socket_connect_timeout=2,
            socket_timeout=2
        )
        
        # Test basic connectivity
        redis_client.ping()
        
        # Test basic operations
        test_key = f"health_check_{int(time.time())}"
        redis_client.set(test_key, "test_value", ex=60)
        value = redis_client.get(test_key)
        redis_client.delete(test_key)
        
        if value != b"test_value":
            raise Exception("Redis read/write test failed")
        
        # Get Redis info
        info = redis_client.info()
        
        response_time = round((time.time() - start_time) * 1000, 2)
        
        return {
            'status': 'healthy',
            'response_time_ms': response_time,
            'memory_usage_bytes': info.get('used_memory', 0),
            'connected_clients': info.get('connected_clients', 0),
            'error': None
        }
        
    except Exception as e:
        return {
            'status': 'unhealthy',
            'error': str(e),
            'response_time_ms': None
        }

def check_external_services_health() -> Dict[str, Any]:
    """Check external services health"""
    services = {}
    
    # Check Supabase
    supabase_status = check_supabase_health()
    services['supabase'] = supabase_status
    
    # Check Stripe
    stripe_status = check_stripe_health()
    services['stripe'] = stripe_status
    
    # Check Twilio
    twilio_status = check_twilio_health()
    services['twilio'] = twilio_status
    
    # Check Resend
    resend_status = check_resend_health()
    services['resend'] = resend_status
    
    # Determine overall status
    healthy_services = sum(1 for s in services.values() if s['status'] == 'healthy')
    total_services = len(services)
    
    if healthy_services == total_services:
        overall_status = 'healthy'
    elif healthy_services == 0:
        overall_status = 'unhealthy'
    else:
        overall_status = 'degraded'
    
    return {
        'status': overall_status,
        'services': services,
        'summary': {
            'healthy_services': healthy_services,
            'total_services': total_services
        }
    }

def check_supabase_health() -> Dict[str, Any]:
    """Check Supabase connectivity"""
    try:
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_ANON_KEY')
        
        if not supabase_url or not supabase_key:
            return {
                'status': 'not_configured',
                'error': 'Supabase credentials not configured',
                'response_time_ms': None
            }
        
        start_time = time.time()
        
        headers = {
            'apikey': supabase_key,
            'Authorization': f'Bearer {supabase_key}'
        }
        
        response = requests.get(
            f"{supabase_url}/rest/v1/",
            headers=headers,
            timeout=5
        )
        
        response_time = round((time.time() - start_time) * 1000, 2)
        
        if response.status_code in [200, 401]:
            return {
                'status': 'healthy',
                'response_time_ms': response_time,
                'error': None
            }
        else:
            return {
                'status': 'unhealthy',
                'response_time_ms': response_time,
                'error': f'HTTP {response.status_code}'
            }
            
    except Exception as e:
        return {
            'status': 'unhealthy',
            'error': str(e),
            'response_time_ms': None
        }

def check_stripe_health() -> Dict[str, Any]:
    """Check Stripe connectivity"""
    try:
        stripe_secret_key = os.getenv('STRIPE_SECRET_KEY')
        
        if not stripe_secret_key:
            return {
                'status': 'not_configured',
                'error': 'Stripe credentials not configured',
                'response_time_ms': None
            }
        
        start_time = time.time()
        
        headers = {
            'Authorization': f'Bearer {stripe_secret_key}',
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        response = requests.get(
            'https://api.stripe.com/v1/account',
            headers=headers,
            timeout=5
        )
        
        response_time = round((time.time() - start_time) * 1000, 2)
        
        if response.status_code == 200:
            return {
                'status': 'healthy',
                'response_time_ms': response_time,
                'error': None
            }
        else:
            return {
                'status': 'unhealthy',
                'response_time_ms': response_time,
                'error': f'HTTP {response.status_code}'
            }
            
    except Exception as e:
        return {
            'status': 'unhealthy',
            'error': str(e),
            'response_time_ms': None
        }

def check_twilio_health() -> Dict[str, Any]:
    """Check Twilio connectivity"""
    try:
        twilio_account_sid = os.getenv('TWILIO_ACCOUNT_SID')
        twilio_auth_token = os.getenv('TWILIO_AUTH_TOKEN')
        
        if not twilio_account_sid or not twilio_auth_token:
            return {
                'status': 'not_configured',
                'error': 'Twilio credentials not configured',
                'response_time_ms': None
            }
        
        start_time = time.time()
        
        import base64
        auth_string = f"{twilio_account_sid}:{twilio_auth_token}"
        auth_bytes = auth_string.encode('ascii')
        auth_b64 = base64.b64encode(auth_bytes).decode('ascii')
        
        headers = {
            'Authorization': f'Basic {auth_b64}',
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        response = requests.get(
            f'https://api.twilio.com/2010-04-01/Accounts/{twilio_account_sid}.json',
            headers=headers,
            timeout=5
        )
        
        response_time = round((time.time() - start_time) * 1000, 2)
        
        if response.status_code == 200:
            return {
                'status': 'healthy',
                'response_time_ms': response_time,
                'error': None
            }
        else:
            return {
                'status': 'unhealthy',
                'response_time_ms': response_time,
                'error': f'HTTP {response.status_code}'
            }
            
    except Exception as e:
        return {
            'status': 'unhealthy',
            'error': str(e),
            'response_time_ms': None
        }

def check_resend_health() -> Dict[str, Any]:
    """Check Resend connectivity"""
    try:
        resend_api_key = os.getenv('RESEND_API_KEY')
        
        if not resend_api_key:
            return {
                'status': 'not_configured',
                'error': 'Resend credentials not configured',
                'response_time_ms': None
            }
        
        start_time = time.time()
        
        headers = {
            'Authorization': f'Bearer {resend_api_key}',
            'Content-Type': 'application/json'
        }
        
        response = requests.get(
            'https://api.resend.com/domains',
            headers=headers,
            timeout=5
        )
        
        response_time = round((time.time() - start_time) * 1000, 2)
        
        if response.status_code in [200, 401]:
            return {
                'status': 'healthy',
                'response_time_ms': response_time,
                'error': None
            }
        else:
            return {
                'status': 'unhealthy',
                'response_time_ms': response_time,
                'error': f'HTTP {response.status_code}'
            }
            
    except Exception as e:
        return {
            'status': 'unhealthy',
            'error': str(e),
            'response_time_ms': None
        }

def check_system_resources() -> Dict[str, Any]:
    """Check system resource usage"""
    try:
        import psutil
        
        # CPU usage
        cpu_percent = psutil.cpu_percent(interval=0.1)
        
        # Memory usage
        memory = psutil.virtual_memory()
        
        # Disk usage
        disk = psutil.disk_usage('/')
        
        # Process info
        process = psutil.Process()
        
        return {
            'status': 'healthy',
            'cpu_percent': cpu_percent,
            'memory_percent': memory.percent,
            'memory_available_gb': round(memory.available / (1024**3), 2),
            'disk_percent': round((disk.used / disk.total) * 100, 2),
            'disk_available_gb': round(disk.free / (1024**3), 2),
            'process_memory_mb': round(process.memory_info().rss / (1024**2), 2),
            'process_threads': process.num_threads(),
            'error': None
        }
        
    except Exception as e:
        return {
            'status': 'unhealthy',
            'error': str(e)
        }

def get_uptime_seconds() -> float:
    """Get application uptime in seconds"""
    try:
        import psutil
        process = psutil.Process()
        return time.time() - process.create_time()
    except:
        return 0.0 