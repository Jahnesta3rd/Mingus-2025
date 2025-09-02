"""
Real-time System Health Monitoring for Mingus Financial Application
Comprehensive health checks and monitoring for production systems
"""

import os
import time
import psutil
import threading
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from collections import defaultdict, deque
import logging
import json
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

# Flask imports
try:
    from flask import current_app, jsonify, request
    FLASK_AVAILABLE = True
except ImportError:
    FLASK_AVAILABLE = False

# Database imports
try:
    from sqlalchemy import create_engine, text
    from sqlalchemy.exc import SQLAlchemyError
    SQLALCHEMY_AVAILABLE = True
except ImportError:
    SQLALCHEMY_AVAILABLE = False

# Redis imports
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

# Celery imports
try:
    from celery import Celery
    CELERY_AVAILABLE = True
except ImportError:
    CELERY_AVAILABLE = False

logger = logging.getLogger(__name__)

@dataclass
class HealthMetric:
    """Individual health metric"""
    name: str
    value: Any
    unit: str = ""
    status: str = "unknown"  # healthy, warning, critical, unknown
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class SystemHealth:
    """Overall system health status"""
    overall_status: str = "unknown"
    overall_score: float = 0.0
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metrics: Dict[str, HealthMetric] = field(default_factory=dict)
    alerts: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)

class SystemHealthMonitor:
    """Real-time system health monitoring"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.health_history = deque(maxlen=1000)
        self.alert_callbacks: List[Callable] = []
        self.monitoring_active = False
        self.monitor_thread = None
        self.health_checks = {}
        self.setup_default_checks()
        
    def setup_default_checks(self):
        """Setup default health checks"""
        self.register_health_check("system_resources", self.check_system_resources)
        self.register_health_check("database_health", self.check_database_health)
        self.register_health_check("redis_health", self.check_redis_health)
        self.register_health_check("celery_health", self.check_celery_health)
        self.register_health_check("network_health", self.check_network_health)
        self.register_health_check("disk_health", self.check_disk_health)
        self.register_health_check("memory_health", self.check_memory_health)
        self.register_health_check("cpu_health", self.check_cpu_health)
        self.register_health_check("process_health", self.check_process_health)
        self.register_health_check("external_services", self.check_external_services)
        
    def register_health_check(self, name: str, check_func: Callable):
        """Register a health check function"""
        self.health_checks[name] = check_func
        logger.info(f"Registered health check: {name}")
    
    def add_alert_callback(self, callback: Callable):
        """Add alert callback function"""
        self.alert_callbacks.append(callback)
        logger.info("Added alert callback")
    
    def start_monitoring(self, interval: int = 30):
        """Start continuous health monitoring"""
        if self.monitoring_active:
            logger.warning("Monitoring already active")
            return
        
        self.monitoring_active = True
        self.monitor_thread = threading.Thread(
            target=self._monitoring_loop,
            args=(interval,),
            daemon=True
        )
        self.monitor_thread.start()
        logger.info(f"Started health monitoring with {interval}s interval")
    
    def stop_monitoring(self):
        """Stop health monitoring"""
        self.monitoring_active = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        logger.info("Stopped health monitoring")
    
    def _monitoring_loop(self, interval: int):
        """Main monitoring loop"""
        while self.monitoring_active:
            try:
                health_status = self.run_health_checks()
                self.health_history.append(health_status)
                
                # Check for alerts
                if health_status.overall_status in ["warning", "critical"]:
                    self._trigger_alerts(health_status)
                
                time.sleep(interval)
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(interval)
    
    def _trigger_alerts(self, health_status: SystemHealth):
        """Trigger alert callbacks"""
        for callback in self.alert_callbacks:
            try:
                callback(health_status)
            except Exception as e:
                logger.error(f"Error in alert callback: {e}")
    
    def run_health_checks(self) -> SystemHealth:
        """Run all registered health checks"""
        health = SystemHealth()
        start_time = time.time()
        
        # Run health checks in parallel
        with ThreadPoolExecutor(max_workers=10) as executor:
            future_to_check = {
                executor.submit(check_func): name
                for name, check_func in self.health_checks.items()
            }
            
            for future in as_completed(future_to_check):
                check_name = future_to_check[future]
                try:
                    result = future.result(timeout=10)
                    if result:
                        health.metrics[check_name] = result
                except Exception as e:
                    logger.error(f"Health check {check_name} failed: {e}")
                    health.metrics[check_name] = HealthMetric(
                        name=check_name,
                        value=None,
                        status="unknown",
                        metadata={"error": str(e)}
                    )
        
        # Calculate overall health
        self._calculate_overall_health(health)
        health.timestamp = datetime.utcnow()
        
        # Store in history
        self.health_history.append(health)
        
        return health
    
    def _calculate_overall_health(self, health: SystemHealth):
        """Calculate overall health status and score"""
        if not health.metrics:
            health.overall_status = "unknown"
            health.overall_score = 0.0
            return
        
        # Count statuses
        status_counts = defaultdict(int)
        total_score = 0.0
        
        for metric in health.metrics.values():
            status_counts[metric.status] += 1
            
            # Calculate score based on status
            if metric.status == "healthy":
                total_score += 1.0
            elif metric.status == "warning":
                total_score += 0.6
            elif metric.status == "critical":
                total_score += 0.0
            else:
                total_score += 0.3
        
        # Determine overall status
        if status_counts["critical"] > 0:
            health.overall_status = "critical"
        elif status_counts["warning"] > 0:
            health.overall_status = "warning"
        elif status_counts["healthy"] > 0:
            health.overall_status = "healthy"
        else:
            health.overall_status = "unknown"
        
        # Calculate overall score
        health.overall_score = total_score / len(health.metrics)
        
        # Generate recommendations
        self._generate_recommendations(health)
    
    def _generate_recommendations(self, health: SystemHealth):
        """Generate recommendations based on health status"""
        recommendations = []
        
        # System resource recommendations
        if "system_resources" in health.metrics:
            metric = health.metrics["system_resources"]
            if metric.status == "warning":
                recommendations.append("Monitor system resource usage closely")
            elif metric.status == "critical":
                recommendations.append("Immediate action required for system resources")
        
        # Database recommendations
        if "database_health" in health.metrics:
            metric = health.metrics["database_health"]
            if metric.status != "healthy":
                recommendations.append("Review database configuration and connectivity")
        
        # Redis recommendations
        if "redis_health" in health.metrics:
            metric = health.metrics["redis_health"]
            if metric.status != "healthy":
                recommendations.append("Check Redis service and configuration")
        
        # Celery recommendations
        if "celery_health" in health.metrics:
            metric = health.metrics["celery_health"]
            if metric.status != "healthy":
                recommendations.append("Verify Celery worker status and configuration")
        
        health.recommendations = recommendations
    
    def check_system_resources(self) -> HealthMetric:
        """Check overall system resources"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Determine status based on thresholds
            status = "healthy"
            if cpu_percent > 80 or memory.percent > 85 or disk.percent > 90:
                status = "critical"
            elif cpu_percent > 60 or memory.percent > 70 or disk.percent > 80:
                status = "warning"
            
            return HealthMetric(
                name="system_resources",
                value={
                    "cpu_percent": cpu_percent,
                    "memory_percent": memory.percent,
                    "disk_percent": disk.percent
                },
                status=status,
                metadata={
                    "cpu_count": psutil.cpu_count(),
                    "memory_total_gb": round(memory.total / (1024**3), 2),
                    "disk_total_gb": round(disk.total / (1024**3), 2)
                }
            )
            
        except Exception as e:
            logger.error(f"Error checking system resources: {e}")
            return HealthMetric(
                name="system_resources",
                value=None,
                status="unknown",
                metadata={"error": str(e)}
            )
    
    def check_database_health(self) -> HealthMetric:
        """Check database connectivity and health"""
        if not SQLALCHEMY_AVAILABLE:
            return HealthMetric(
                name="database_health",
                value=None,
                status="unknown",
                metadata={"error": "SQLAlchemy not available"}
            )
        
        try:
            # Get database URL from environment or config
            db_url = os.getenv('DATABASE_URL', 'sqlite:///app.db')
            
            # Test connection
            engine = create_engine(db_url, pool_pre_ping=True)
            with engine.connect() as conn:
                result = conn.execute(text("SELECT 1"))
                result.fetchone()
            
            # Check connection pool status if available
            pool_status = "unknown"
            try:
                pool = engine.pool
                pool_status = f"size={pool.size()}, checked_out={pool.checkedout()}"
            except:
                pass
            
            return HealthMetric(
                name="database_health",
                value="connected",
                status="healthy",
                metadata={
                    "database_url": db_url.split('://')[0],
                    "pool_status": pool_status
                }
            )
            
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return HealthMetric(
                name="database_health",
                value="disconnected",
                status="critical",
                metadata={"error": str(e)}
            )
    
    def check_redis_health(self) -> HealthMetric:
        """Check Redis connectivity and health"""
        if not REDIS_AVAILABLE:
            return HealthMetric(
                name="redis_health",
                value=None,
                status="unknown",
                metadata={"error": "Redis not available"}
            )
        
        try:
            redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
            r = redis.from_url(redis_url)
            
            # Test connection
            r.ping()
            
            # Get Redis info
            info = r.info()
            
            return HealthMetric(
                name="redis_health",
                value="connected",
                status="healthy",
                metadata={
                    "redis_version": info.get('redis_version', 'unknown'),
                    "connected_clients": info.get('connected_clients', 0),
                    "used_memory_human": info.get('used_memory_human', 'unknown')
                }
            )
            
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            return HealthMetric(
                name="redis_health",
                value="disconnected",
                status="critical",
                metadata={"error": str(e)}
            )
    
    def check_celery_health(self) -> HealthMetric:
        """Check Celery worker health"""
        if not CELERY_AVAILABLE:
            return HealthMetric(
                name="celery_health",
                value=None,
                status="unknown",
                metadata={"error": "Celery not available"}
            )
        
        try:
            # Check if Celery workers are running
            # This is a simplified check - in production you'd want more sophisticated monitoring
            celery_broker = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379')
            
            # Try to connect to broker
            if 'redis://' in celery_broker:
                r = redis.from_url(celery_broker)
                r.ping()
                broker_status = "connected"
            else:
                broker_status = "unknown"
            
            return HealthMetric(
                name="celery_health",
                value="active",
                status="healthy",
                metadata={
                    "broker_status": broker_status,
                    "broker_url": celery_broker
                }
            )
            
        except Exception as e:
            logger.error(f"Celery health check failed: {e}")
            return HealthMetric(
                name="celery_health",
                value="inactive",
                status="warning",
                metadata={"error": str(e)}
            )
    
    def check_network_health(self) -> HealthMetric:
        """Check network connectivity"""
        try:
            # Test basic network connectivity
            test_urls = [
                "https://httpbin.org/status/200",
                "https://api.github.com",
                "https://www.google.com"
            ]
            
            successful_pings = 0
            response_times = []
            
            for url in test_urls:
                try:
                    start_time = time.time()
                    response = requests.get(url, timeout=5)
                    response_time = time.time() - start_time
                    
                    if response.status_code == 200:
                        successful_pings += 1
                        response_times.append(response_time)
                except:
                    pass
            
            # Calculate success rate and average response time
            success_rate = successful_pings / len(test_urls)
            avg_response_time = sum(response_times) / len(response_times) if response_times else 0
            
            # Determine status
            if success_rate >= 0.8 and avg_response_time < 2.0:
                status = "healthy"
            elif success_rate >= 0.5 and avg_response_time < 5.0:
                status = "warning"
            else:
                status = "critical"
            
            return HealthMetric(
                name="network_health",
                value=f"{successful_pings}/{len(test_urls)} successful",
                status=status,
                metadata={
                    "success_rate": round(success_rate, 2),
                    "avg_response_time_ms": round(avg_response_time * 1000, 2)
                }
            )
            
        except Exception as e:
            logger.error(f"Network health check failed: {e}")
            return HealthMetric(
                name="network_health",
                value="unknown",
                status="unknown",
                metadata={"error": str(e)}
            )
    
    def check_disk_health(self) -> HealthMetric:
        """Check disk usage and health"""
        try:
            disk = psutil.disk_usage('/')
            disk_percent = disk.percent
            
            # Check for disk I/O
            disk_io = psutil.disk_io_counters()
            
            status = "healthy"
            if disk_percent > 90:
                status = "critical"
            elif disk_percent > 80:
                status = "warning"
            
            return HealthMetric(
                name="disk_health",
                value=f"{disk_percent}% used",
                status=status,
                metadata={
                    "total_gb": round(disk.total / (1024**3), 2),
                    "used_gb": round(disk.used / (1024**3), 2),
                    "free_gb": round(disk.free / (1024**3), 2),
                    "read_bytes": disk_io.read_bytes if disk_io else 0,
                    "write_bytes": disk_io.write_bytes if disk_io else 0
                }
            )
            
        except Exception as e:
            logger.error(f"Disk health check failed: {e}")
            return HealthMetric(
                name="disk_health",
                value="unknown",
                status="unknown",
                metadata={"error": str(e)}
            )
    
    def check_memory_health(self) -> HealthMetric:
        """Check memory usage and health"""
        try:
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            
            # Check swap usage
            swap = psutil.swap_memory()
            
            status = "healthy"
            if memory_percent > 90:
                status = "critical"
            elif memory_percent > 80:
                status = "warning"
            
            return HealthMetric(
                name="memory_health",
                value=f"{memory_percent}% used",
                status=status,
                metadata={
                    "total_gb": round(memory.total / (1024**3), 2),
                    "available_gb": round(memory.available / (1024**3), 2),
                    "swap_percent": swap.percent,
                    "swap_total_gb": round(swap.total / (1024**3), 2)
                }
            )
            
        except Exception as e:
            logger.error(f"Memory health check failed: {e}")
            return HealthMetric(
                name="memory_health",
                value="unknown",
                status="unknown",
                metadata={"error": str(e)}
            )
    
    def check_cpu_health(self) -> HealthMetric:
        """Check CPU usage and health"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1, percpu=True)
            cpu_count = psutil.cpu_count()
            cpu_freq = psutil.cpu_freq()
            
            # Calculate average CPU usage
            avg_cpu = sum(cpu_percent) / len(cpu_percent)
            
            status = "healthy"
            if avg_cpu > 90:
                status = "critical"
            elif avg_cpu > 70:
                status = "warning"
            
            return HealthMetric(
                name="cpu_health",
                value=f"{avg_cpu:.1f}% average",
                status=status,
                metadata={
                    "cpu_count": cpu_count,
                    "cpu_freq_mhz": round(cpu_freq.current, 2) if cpu_freq else 0,
                    "per_cpu_usage": [round(p, 1) for p in cpu_percent]
                }
            )
            
        except Exception as e:
            logger.error(f"CPU health check failed: {e}")
            return HealthMetric(
                name="cpu_health",
                value="unknown",
                status="unknown",
                metadata={"error": str(e)}
            )
    
    def check_process_health(self) -> HealthMetric:
        """Check critical process health"""
        try:
            # Check for critical processes
            critical_processes = ['python', 'nginx', 'redis-server', 'postgres']
            running_processes = []
            
            for proc in psutil.process_iter(['pid', 'name', 'status']):
                try:
                    if proc.info['name'] in critical_processes:
                        running_processes.append({
                            'name': proc.info['name'],
                            'pid': proc.info['pid'],
                            'status': proc.info['status']
                        })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            
            # Determine status based on critical process availability
            if len(running_processes) >= 2:
                status = "healthy"
            elif len(running_processes) >= 1:
                status = "warning"
            else:
                status = "critical"
            
            return HealthMetric(
                name="process_health",
                value=f"{len(running_processes)} critical processes running",
                status=status,
                metadata={
                    "running_processes": running_processes,
                    "total_checked": len(critical_processes)
                }
            )
            
        except Exception as e:
            logger.error(f"Process health check failed: {e}")
            return HealthMetric(
                name="process_health",
                value="unknown",
                status="unknown",
                metadata={"error": str(e)}
            )
    
    def check_external_services(self) -> HealthMetric:
        """Check external service dependencies"""
        try:
            # Check external services that the application depends on
            services = {
                "stripe_api": "https://api.stripe.com/v1/account",
                "plaid_api": "https://sandbox.plaid.com/health",
                "email_service": "https://api.resend.com/health"
            }
            
            service_status = {}
            successful_checks = 0
            
            for service_name, url in services.items():
                try:
                    response = requests.get(url, timeout=5)
                    if response.status_code == 200:
                        service_status[service_name] = "healthy"
                        successful_checks += 1
                    else:
                        service_status[service_name] = f"status_{response.status_code}"
                except Exception as e:
                    service_status[service_name] = f"error: {str(e)}"
            
            # Determine overall status
            success_rate = successful_checks / len(services)
            if success_rate >= 0.8:
                status = "healthy"
            elif success_rate >= 0.5:
                status = "warning"
            else:
                status = "critical"
            
            return HealthMetric(
                name="external_services",
                value=f"{successful_checks}/{len(services)} services healthy",
                status=status,
                metadata={
                    "service_status": service_status,
                    "success_rate": round(success_rate, 2)
                }
            )
            
        except Exception as e:
            logger.error(f"External services health check failed: {e}")
            return HealthMetric(
                name="external_services",
                value="unknown",
                status="unknown",
                metadata={"error": str(e)}
            )
    
    def get_current_health(self) -> SystemHealth:
        """Get current health status"""
        if not self.health_history:
            return self.run_health_checks()
        return self.health_history[-1]
    
    def get_health_history(self, hours: int = 24) -> List[SystemHealth]:
        """Get health history for specified time period"""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        return [
            health for health in self.health_history
            if health.timestamp > cutoff_time
        ]
    
    def export_health_data(self, format: str = "json") -> str:
        """Export health data in specified format"""
        current_health = self.get_current_health()
        
        if format.lower() == "json":
            return json.dumps({
                "current_health": {
                    "overall_status": current_health.overall_status,
                    "overall_score": current_health.overall_score,
                    "timestamp": current_health.timestamp.isoformat(),
                    "metrics": {
                        name: {
                            "value": metric.value,
                            "status": metric.status,
                            "unit": metric.unit,
                            "metadata": metric.metadata
                        }
                        for name, metric in current_health.metrics.items()
                    },
                    "alerts": current_health.alerts,
                    "recommendations": current_health.recommendations
                },
                "history_count": len(self.health_history)
            }, indent=2)
        
        return str(current_health)

# Flask integration
if FLASK_AVAILABLE:
    def create_health_routes(app, monitor: SystemHealthMonitor = None):
        """Create Flask health check routes"""
        
        if monitor is None:
            monitor = SystemHealthMonitor()
        
        @app.route('/health/system')
        def system_health():
            """Get current system health status"""
            health = monitor.get_current_health()
            return jsonify({
                "status": health.overall_status,
                "score": health.overall_score,
                "timestamp": health.timestamp.isoformat(),
                "metrics": {
                    name: {
                        "value": metric.value,
                        "status": metric.status,
                        "unit": metric.unit
                    }
                    for name, metric in health.metrics.items()
                },
                "recommendations": health.recommendations
            })
        
        @app.route('/health/system/start', methods=['POST'])
        def start_monitoring():
            """Start health monitoring"""
            try:
                interval = request.json.get('interval', 30) if request.json else 30
                monitor.start_monitoring(interval)
                return jsonify({"message": "Monitoring started", "interval": interval}), 200
            except Exception as e:
                return jsonify({"error": str(e)}), 500
        
        @app.route('/health/system/stop', methods=['POST'])
        def stop_monitoring():
            """Stop health monitoring"""
            try:
                monitor.stop_monitoring()
                return jsonify({"message": "Monitoring stopped"}), 200
            except Exception as e:
                return jsonify({"error": str(e)}), 500
        
        @app.route('/health/system/export')
        def export_health():
            """Export health data"""
            try:
                format_type = request.args.get('format', 'json')
                data = monitor.export_health_data(format_type)
                return jsonify({"data": data, "format": format_type}), 200
            except Exception as e:
                return jsonify({"error": str(e)}), 500

# Standalone usage
if __name__ == "__main__":
    # Example usage
    monitor = SystemHealthMonitor()
    
    # Add alert callback
    def alert_callback(health):
        print(f"ALERT: System health is {health.overall_status} (score: {health.overall_score:.2f})")
        if health.recommendations:
            print("Recommendations:")
            for rec in health.recommendations:
                print(f"  - {rec}")
    
    monitor.add_alert_callback(alert_callback)
    
    # Start monitoring
    monitor.start_monitoring(interval=10)
    
    try:
        # Run for a while
        time.sleep(60)
    except KeyboardInterrupt:
        print("\nStopping monitoring...")
    finally:
        monitor.stop_monitoring()
        
        # Show final health status
        final_health = monitor.get_current_health()
        print(f"\nFinal health status: {final_health.overall_status} (score: {final_health.overall_score:.2f})")
