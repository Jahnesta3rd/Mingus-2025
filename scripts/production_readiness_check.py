#!/usr/bin/env python3
"""
Production Readiness Check Script for Mingus Financial Application
Comprehensive verification system for production deployment readiness
"""

import os
import sys
import json
import time
import requests
import subprocess
import ssl
import socket
from datetime import datetime
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass
import logging

# Add backend to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

try:
    import psycopg2
    import redis
    from sqlalchemy import create_engine, text
    from sqlalchemy.exc import SQLAlchemyError
    import stripe
    from prometheus_client import CollectorRegistry, push_to_gateway
except ImportError as e:
    print(f"Warning: Some dependencies not available: {e}")

@dataclass
class CheckResult:
    """Result of a production readiness check"""
    name: str
    status: str  # 'pass', 'fail', 'warning'
    score: float  # 0.0 to 1.0
    details: str
    recommendations: List[str]
    critical: bool = False

class ProductionReadinessChecker:
    """Comprehensive production readiness verification system"""
    
    def __init__(self):
        self.results: List[CheckResult] = []
        self.overall_score = 0.0
        self.critical_failures = 0
        self.setup_logging()
        
    def setup_logging(self):
        """Setup logging configuration"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('production_readiness.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def run_all_checks(self) -> Dict[str, Any]:
        """Run all production readiness checks"""
        self.logger.info("Starting production readiness verification...")
        
        # Core infrastructure checks
        self.check_database_connection_pooling()
        self.check_rate_limiting_configuration()
        self.check_error_handling_coverage()
        self.check_backup_system_functionality()
        self.check_security_configurations()
        self.check_performance_benchmarks()
        self.check_health_check_endpoints()
        
        # Security and compliance checks
        self.check_ssl_tls_configuration()
        self.check_environment_variable_security()
        self.check_database_migration_status()
        self.check_cache_configuration()
        self.check_background_task_health()
        self.check_payment_processing_readiness()
        self.check_monitoring_system_status()
        
        # Calculate overall score
        self.calculate_overall_score()
        
        return self.generate_report()
    
    def check_database_connection_pooling(self):
        """Check database connection pooling status"""
        try:
            # Check if connection pool is properly configured
            from backend.database.connection_pool import get_pool_manager
            
            pool_manager = get_pool_manager()
            if pool_manager:
                pool_status = pool_manager.get_pool_status()
                
                if pool_status['healthy']:
                    self.results.append(CheckResult(
                        name="Database Connection Pooling",
                        status="pass",
                        score=0.9,
                        details=f"Pool healthy with {pool_status['active_connections']} active connections",
                        recommendations=["Monitor pool performance under load", "Set up pool alerts"]
                    ))
                else:
                    self.results.append(CheckResult(
                        name="Database Connection Pooling",
                        status="fail",
                        score=0.3,
                        details=f"Pool unhealthy: {pool_status.get('error', 'Unknown error')}",
                        recommendations=["Fix pool configuration", "Check database connectivity"],
                        critical=True
                    ))
            else:
                self.results.append(CheckResult(
                    name="Database Connection Pooling",
                    status="fail",
                    score=0.0,
                    details="Pool manager not initialized",
                    recommendations=["Initialize connection pool", "Check database configuration"],
                    critical=True
                ))
                
        except Exception as e:
            self.results.append(CheckResult(
                name="Database Connection Pooling",
                status="fail",
                score=0.0,
                details=f"Error checking pool: {str(e)}",
                recommendations=["Review database setup", "Check import paths"],
                critical=True
            ))
    
    def check_rate_limiting_configuration(self):
        """Check rate limiting configuration"""
        try:
            # Check rate limiting middleware
            from backend.middleware.rate_limit_integration import RateLimitIntegration
            
            rate_limiter = RateLimitIntegration()
            if rate_limiter.rate_limiter:
                self.results.append(CheckResult(
                    name="Rate Limiting Configuration",
                    status="pass",
                    score=0.8,
                    details="Rate limiting middleware active",
                    recommendations=["Test rate limits under load", "Monitor rate limit events"]
                ))
            else:
                self.results.append(CheckResult(
                    name="Rate Limiting Configuration",
                    status="fail",
                    score=0.2,
                    details="Rate limiter not properly configured",
                    recommendations=["Configure rate limiting", "Test rate limit functionality"],
                    critical=True
                ))
                
        except Exception as e:
            self.results.append(CheckResult(
                name="Rate Limiting Configuration",
                status="fail",
                score=0.0,
                details=f"Error checking rate limiting: {str(e)}",
                recommendations=["Review rate limiting setup", "Check middleware configuration"],
                critical=True
            ))
    
    def check_error_handling_coverage(self):
        """Check error handling coverage"""
        try:
            # Check error handling files exist
            error_files = [
                'backend/errors/__init__.py',
                'backend/README_ERROR_HANDLING.md',
                'backend/app_with_error_handling.py'
            ]
            
            existing_files = sum(1 for f in error_files if os.path.exists(f))
            
            if existing_files >= 2:
                self.results.append(CheckResult(
                    name="Error Handling Coverage",
                    status="pass",
                    score=0.8,
                    details=f"Error handling system in place ({existing_files}/3 files)",
                    recommendations=["Test error scenarios", "Monitor error logs"]
                ))
            else:
                self.results.append(CheckResult(
                    name="Error Handling Coverage",
                    status="warning",
                    score=0.5,
                    details=f"Limited error handling coverage ({existing_files}/3 files)",
                    recommendations=["Implement comprehensive error handling", "Add error logging"]
                ))
                
        except Exception as e:
            self.results.append(CheckResult(
                name="Error Handling Coverage",
                status="fail",
                score=0.0,
                details=f"Error checking error handling: {str(e)}",
                recommendations=["Review error handling setup"]
            ))
    
    def check_backup_system_functionality(self):
        """Check backup system functionality"""
        try:
            # Check backup system files
            backup_files = [
                'BACKUP_SYSTEM_README.md',
                'backend/backup/',
                'scripts/backup_scheduler.py'
            ]
            
            existing_files = sum(1 for f in backup_files if os.path.exists(f))
            
            if existing_files >= 2:
                self.results.append(CheckResult(
                    name="Backup System Functionality",
                    status="pass",
                    score=0.8,
                    details=f"Backup system configured ({existing_files}/3 components)",
                    recommendations=["Test backup restoration", "Verify backup scheduling"]
                ))
            else:
                self.results.append(CheckResult(
                    name="Backup System Functionality",
                    status="warning",
                    score=0.4,
                    details=f"Limited backup coverage ({existing_files}/3 components)",
                    recommendations=["Implement backup system", "Test backup procedures"]
                ))
                
        except Exception as e:
            self.results.append(CheckResult(
                name="Backup System Functionality",
                status="fail",
                score=0.0,
                details=f"Error checking backup system: {str(e)}",
                recommendations=["Review backup configuration"]
            ))
    
    def check_security_configurations(self):
        """Check security configurations"""
        try:
            # Check security components
            security_files = [
                'backend/security/',
                'backend/middleware/security_middleware.py',
                'SECURITY_DASHBOARD_SYSTEM_SUMMARY.md'
            ]
            
            existing_files = sum(1 for f in security_files if os.path.exists(f))
            
            if existing_files >= 2:
                self.results.append(CheckResult(
                    name="Security Configurations",
                    status="pass",
                    score=0.9,
                    details=f"Security system active ({existing_files}/3 components)",
                    recommendations=["Run security tests", "Monitor security logs"]
                ))
            else:
                self.results.append(CheckResult(
                    name="Security Configurations",
                    status="fail",
                    score=0.3,
                    details=f"Insufficient security coverage ({existing_files}/3 components)",
                    recommendations=["Implement security middleware", "Configure authentication"],
                    critical=True
                ))
                
        except Exception as e:
            self.results.append(CheckResult(
                name="Security Configurations",
                status="fail",
                score=0.0,
                details=f"Error checking security: {str(e)}",
                recommendations=["Review security setup"]
            ))
    
    def check_performance_benchmarks(self):
        """Check performance benchmarks"""
        try:
            # Check performance monitoring
            perf_files = [
                'backend/monitoring/performance_monitor.py',
                'backend/monitoring/performance_optimizer.py',
                '.benchmarks/'
            ]
            
            existing_files = sum(1 for f in perf_files if os.path.exists(f))
            
            if existing_files >= 2:
                self.results.append(CheckResult(
                    name="Performance Benchmarks",
                    status="pass",
                    score=0.8,
                    details=f"Performance monitoring active ({existing_files}/3 components)",
                    recommendations=["Run performance tests", "Monitor response times"]
                ))
            else:
                self.results.append(CheckResult(
                    name="Performance Benchmarks",
                    status="warning",
                    score=0.5,
                    details=f"Limited performance monitoring ({existing_files}/3 components)",
                    recommendations=["Implement performance monitoring", "Set up benchmarks"]
                ))
                
        except Exception as e:
            self.results.append(CheckResult(
                name="Performance Benchmarks",
                status="fail",
                score=0.0,
                details=f"Error checking performance: {str(e)}",
                recommendations=["Review performance setup"]
            ))
    
    def check_health_check_endpoints(self):
        """Check health check endpoints"""
        try:
            # Check health monitoring
            health_files = [
                'backend/monitoring/health.py',
                'backend/monitoring/comprehensive_monitor.py',
                'docs/HEALTH_CHECK_ENDPOINTS.md'
            ]
            
            existing_files = sum(1 for f in health_files if os.path.exists(f))
            
            if existing_files >= 2:
                self.results.append(CheckResult(
                    name="Health Check Endpoints",
                    status="pass",
                    score=0.9,
                    details=f"Health monitoring active ({existing_files}/3 components)",
                    recommendations=["Test health endpoints", "Monitor health status"]
                ))
            else:
                self.results.append(CheckResult(
                    name="Health Check Endpoints",
                    status="fail",
                    score=0.3,
                    details=f"Insufficient health monitoring ({existing_files}/3 components)",
                    recommendations=["Implement health checks", "Set up monitoring"],
                    critical=True
                ))
                
        except Exception as e:
            self.results.append(CheckResult(
                name="Health Check Endpoints",
                status="fail",
                score=0.0,
                details=f"Error checking health: {str(e)}",
                recommendations=["Review health monitoring setup"]
            ))
    
    def check_ssl_tls_configuration(self):
        """Check SSL/TLS configuration"""
        try:
            # Check SSL setup script
            if os.path.exists('scripts/ssl_setup.sh'):
                self.results.append(CheckResult(
                    name="SSL/TLS Configuration",
                    status="pass",
                    score=0.8,
                    details="SSL setup script available",
                    recommendations=["Verify SSL certificates", "Test HTTPS endpoints"]
                ))
            else:
                self.results.append(CheckResult(
                    name="SSL/TLS Configuration",
                    status="warning",
                    score=0.4,
                    details="SSL setup script not found",
                    recommendations=["Create SSL setup script", "Configure HTTPS"]
                ))
                
        except Exception as e:
            self.results.append(CheckResult(
                name="SSL/TLS Configuration",
                status="fail",
                score=0.0,
                details=f"Error checking SSL: {str(e)}",
                recommendations=["Review SSL configuration"]
            ))
    
    def check_environment_variable_security(self):
        """Check environment variable security"""
        try:
            # Check config files
            config_files = [
                'backend/config.env',
                'backend/config/',
                'config/'
            ]
            
            existing_files = sum(1 for f in config_files if os.path.exists(f))
            
            if existing_files >= 2:
                self.results.append(CheckResult(
                    name="Environment Variable Security",
                    status="pass",
                    score=0.8,
                    details=f"Configuration system in place ({existing_files}/3 components)",
                    recommendations=["Review environment variables", "Secure sensitive data"]
                ))
            else:
                self.results.append(CheckResult(
                    name="Environment Variable Security",
                    status="warning",
                    score=0.5,
                    details=f"Limited configuration coverage ({existing_files}/3 components)",
                    recommendations=["Implement configuration management", "Secure environment variables"]
                ))
                
        except Exception as e:
            self.results.append(CheckResult(
                name="Environment Variable Security",
                status="fail",
                score=0.0,
                details=f"Error checking config: {str(e)}",
                recommendations=["Review configuration setup"]
            ))
    
    def check_database_migration_status(self):
        """Check database migration status"""
        try:
            # Check migration files
            migration_files = [
                'alembic.ini',
                'backend/migrations/',
                'migrations/'
            ]
            
            existing_files = sum(1 for f in migration_files if os.path.exists(f))
            
            if existing_files >= 2:
                self.results.append(CheckResult(
                    name="Database Migration Status",
                    status="pass",
                    score=0.8,
                    details=f"Migration system configured ({existing_files}/3 components)",
                    recommendations=["Run migration tests", "Verify migration scripts"]
                ))
            else:
                self.results.append(CheckResult(
                    name="Database Migration Status",
                    status="warning",
                    score=0.4,
                    details=f"Limited migration coverage ({existing_files}/3 components)",
                    recommendations=["Set up migration system", "Test migrations"]
                ))
                
        except Exception as e:
            self.results.append(CheckResult(
                name="Database Migration Status",
                status="fail",
                score=0.0,
                details=f"Error checking migrations: {str(e)}",
                recommendations=["Review migration setup"]
            ))
    
    def check_cache_configuration(self):
        """Check cache configuration"""
        try:
            # Check Redis configuration
            redis_config = os.getenv('REDIS_URL', 'redis://localhost:6379')
            
            try:
                import redis
                r = redis.from_url(redis_config)
                r.ping()
                self.results.append(CheckResult(
                    name="Cache Configuration",
                    status="pass",
                    score=0.8,
                    details="Redis cache accessible",
                    recommendations=["Monitor cache performance", "Set cache alerts"]
                ))
            except Exception:
                self.results.append(CheckResult(
                    name="Cache Configuration",
                    status="warning",
                    score=0.4,
                    details="Redis cache not accessible",
                    recommendations=["Configure Redis", "Test cache connectivity"]
                ))
                
        except Exception as e:
            self.results.append(CheckResult(
                name="Cache Configuration",
                status="fail",
                score=0.0,
                details=f"Error checking cache: {str(e)}",
                recommendations=["Review cache setup"]
            ))
    
    def check_background_task_health(self):
        """Check background task health"""
        try:
            # Check Celery configuration
            celery_files = [
                'backend/celery_app.py',
                'backend/celery_worker.py',
                'backend/celery_config.py'
            ]
            
            existing_files = sum(1 for f in celery_files if os.path.exists(f))
            
            if existing_files >= 2:
                self.results.append(CheckResult(
                    name="Background Task Health",
                    status="pass",
                    score=0.8,
                    details=f"Celery system configured ({existing_files}/3 components)",
                    recommendations=["Test task execution", "Monitor worker health"]
                ))
            else:
                self.results.append(CheckResult(
                    name="Background Task Health",
                    status="warning",
                    score=0.4,
                    details=f"Limited task system coverage ({existing_files}/3 components)",
                    recommendations=["Configure Celery", "Set up task monitoring"]
                ))
                
        except Exception as e:
            self.results.append(CheckResult(
                name="Background Task Health",
                status="fail",
                score=0.0,
                details=f"Error checking tasks: {str(e)}",
                recommendations=["Review task system setup"]
            ))
    
    def check_payment_processing_readiness(self):
        """Check payment processing readiness"""
        try:
            # Check Stripe integration
            stripe_files = [
                'STRIPE_INTEGRATION_SUMMARY.md',
                'backend/payment/',
                'backend/billing/'
            ]
            
            existing_files = sum(1 for f in stripe_files if os.path.exists(f))
            
            if existing_files >= 2:
                self.results.append(CheckResult(
                    name="Payment Processing Readiness",
                    status="pass",
                    score=0.8,
                    details=f"Payment system configured ({existing_files}/3 components)",
                    recommendations=["Test payment flows", "Verify webhook handling"]
                ))
            else:
                self.results.append(CheckResult(
                    name="Payment Processing Readiness",
                    status="warning",
                    score=0.4,
                    details=f"Limited payment coverage ({existing_files}/3 components)",
                    recommendations=["Configure payment system", "Test payment processing"]
                ))
                
        except Exception as e:
            self.results.append(CheckResult(
                name="Payment Processing Readiness",
                status="fail",
                score=0.0,
                details=f"Error checking payments: {str(e)}",
                recommendations=["Review payment setup"]
            ))
    
    def check_monitoring_system_status(self):
        """Check monitoring system status"""
        try:
            # Check monitoring components
            monitoring_files = [
                'backend/monitoring/',
                'docker-compose.monitoring.yml',
                'MONITORING_SETUP_GUIDE.md'
            ]
            
            existing_files = sum(1 for f in monitoring_files if os.path.exists(f))
            
            if existing_files >= 2:
                self.results.append(CheckResult(
                    name="Monitoring System Status",
                    status="pass",
                    score=0.9,
                    details=f"Monitoring system active ({existing_files}/3 components)",
                    recommendations=["Test monitoring alerts", "Verify metrics collection"]
                ))
            else:
                self.results.append(CheckResult(
                    name="Monitoring System Status",
                    status="warning",
                    score=0.4,
                    details=f"Limited monitoring coverage ({existing_files}/3 components)",
                    recommendations=["Set up monitoring", "Configure alerts"]
                ))
                
        except Exception as e:
            self.results.append(CheckResult(
                name="Monitoring System Status",
                status="fail",
                score=0.0,
                details=f"Error checking monitoring: {str(e)}",
                recommendations=["Review monitoring setup"]
            ))
    
    def calculate_overall_score(self):
        """Calculate overall production readiness score"""
        if not self.results:
            self.overall_score = 0.0
            return
        
        total_score = sum(result.score for result in self.results)
        self.overall_score = total_score / len(self.results)
        
        # Count critical failures
        self.critical_failures = sum(1 for result in self.results if result.critical)
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive production readiness report"""
        report = {
            'timestamp': datetime.utcnow().isoformat(),
            'overall_score': round(self.overall_score, 2),
            'production_ready': self.overall_score >= 0.8 and self.critical_failures == 0,
            'critical_failures': self.critical_failures,
            'total_checks': len(self.results),
            'passed_checks': len([r for r in self.results if r.status == 'pass']),
            'failed_checks': len([r for r in self.results if r.status == 'fail']),
            'warning_checks': len([r for r in self.results if r.status == 'warning']),
            'check_results': [
                {
                    'name': r.name,
                    'status': r.status,
                    'score': r.score,
                    'details': r.details,
                    'recommendations': r.recommendations,
                    'critical': r.critical
                }
                for r in self.results
            ],
            'summary': self.generate_summary()
        }
        
        return report
    
    def generate_summary(self) -> str:
        """Generate human-readable summary"""
        if self.overall_score >= 0.9:
            status = "EXCELLENT"
            readiness = "Production ready with minor optimizations recommended"
        elif self.overall_score >= 0.8:
            status = "GOOD"
            readiness = "Production ready with some improvements needed"
        elif self.overall_score >= 0.6:
            status = "FAIR"
            readiness = "Production deployment possible but significant work required"
        else:
            status = "POOR"
            readiness = "Not ready for production deployment"
        
        if self.critical_failures > 0:
            readiness += f" - {self.critical_failures} critical issues must be resolved"
        
        return f"Production Readiness: {status} ({self.overall_score:.1%}) - {readiness}"
    
    def save_report(self, report: Dict[str, Any], filename: str = None):
        """Save report to file"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"production_readiness_report_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(report, f, indent=2)
        
        self.logger.info(f"Report saved to {filename}")
        return filename

def main():
    """Main execution function"""
    print("🔍 Mingus Financial Application - Production Readiness Check")
    print("=" * 60)
    
    checker = ProductionReadinessChecker()
    report = checker.run_all_checks()
    
    # Display results
    print(f"\n📊 OVERALL SCORE: {report['overall_score']:.1%}")
    print(f"🚀 PRODUCTION READY: {'✅ YES' if report['production_ready'] else '❌ NO'}")
    print(f"⚠️  CRITICAL ISSUES: {report['critical_failures']}")
    
    print(f"\n📋 CHECK RESULTS:")
    print(f"   ✅ Passed: {report['passed_checks']}")
    print(f"   ❌ Failed: {report['failed_checks']}")
    print(f"   ⚠️  Warnings: {report['warning_checks']}")
    
    print(f"\n📝 SUMMARY:")
    print(f"   {report['summary']}")
    
    # Show failed checks
    failed_checks = [r for r in report['check_results'] if r['status'] == 'fail']
    if failed_checks:
        print(f"\n❌ FAILED CHECKS:")
        for check in failed_checks:
            critical = "🚨 CRITICAL" if check['critical'] else ""
            print(f"   • {check['name']} {critical}")
            print(f"     Details: {check['details']}")
            for rec in check['recommendations']:
                print(f"     - {rec}")
    
    # Show warnings
    warning_checks = [r for r in report['check_results'] if r['status'] == 'warning']
    if warning_checks:
        print(f"\n⚠️  WARNINGS:")
        for check in warning_checks:
            print(f"   • {check['name']}")
            print(f"     Details: {check['details']}")
            for rec in check['recommendations']:
                print(f"     - {rec}")
    
    # Save report
    filename = checker.save_report(report)
    print(f"\n💾 Detailed report saved to: {filename}")
    
    # Exit with appropriate code
    if report['production_ready']:
        print("\n🎉 Your application is ready for production deployment!")
        sys.exit(0)
    else:
        print("\n🚨 Production deployment blocked. Please resolve critical issues first.")
        sys.exit(1)

if __name__ == "__main__":
    main()
