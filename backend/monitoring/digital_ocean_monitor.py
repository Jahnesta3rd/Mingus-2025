"""
Enhanced Digital Ocean Monitoring Integration
Advanced monitoring for Digital Ocean infrastructure including containers, databases, and load balancers
"""

import os
import json
import time
import requests
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import threading
from collections import defaultdict, deque

logger = logging.getLogger(__name__)

class MonitoringType(Enum):
    """Types of monitoring available"""
    DROPLET = "droplet"
    CONTAINER = "container"
    DATABASE = "database"
    LOAD_BALANCER = "load_balancer"
    KUBERNETES = "kubernetes"
    VOLUME = "volume"

@dataclass
class DigitalOceanMonitoringConfig:
    """Enhanced Digital Ocean monitoring configuration"""
    api_token: str = ""
    monitoring_enabled: bool = True
    metrics_interval: int = 300  # 5 minutes
    alert_thresholds: Dict[str, float] = field(default_factory=lambda: {
        "cpu_percent": 80,
        "memory_percent": 85,
        "disk_percent": 90,
        "network_in": 1000000000,  # 1GB
        "network_out": 1000000000,  # 1GB
        "load_average": 2.0
    })
    
    # Container monitoring
    container_monitoring: bool = True
    container_alert_thresholds: Dict[str, float] = field(default_factory=lambda: {
        "cpu_percent": 75,
        "memory_percent": 80,
        "restart_count": 5
    })
    
    # Database monitoring
    database_monitoring: bool = True
    database_alert_thresholds: Dict[str, float] = field(default_factory=lambda: {
        "connection_count": 100,
        "query_time": 5.0,  # seconds
        "disk_usage": 85
    })
    
    # Load balancer monitoring
    load_balancer_monitoring: bool = True
    load_balancer_alert_thresholds: Dict[str, float] = field(default_factory=lambda: {
        "error_rate": 5.0,  # percentage
        "response_time": 2.0,  # seconds
        "unhealthy_backends": 1
    })

class EnhancedDigitalOceanMonitor:
    """Enhanced Digital Ocean monitoring with advanced features"""
    
    def __init__(self, config: DigitalOceanMonitoringConfig):
        self.config = config
        self.base_url = "https://api.digitalocean.com/v2"
        self.headers = {
            "Authorization": f"Bearer {config.api_token}",
            "Content-Type": "application/json"
        }
        self.metrics_cache = defaultdict(lambda: deque(maxlen=100))
        self.last_check = None
        self.monitoring_thread = None
        self.running = False
        
        if config.monitoring_enabled:
            self.start_monitoring()
    
    def start_monitoring(self):
        """Start continuous monitoring"""
        if self.running:
            return
        
        self.running = True
        self.monitoring_thread = threading.Thread(target=self._monitoring_worker, daemon=True)
        self.monitoring_thread.start()
        logger.info("Digital Ocean monitoring started")
    
    def stop_monitoring(self):
        """Stop continuous monitoring"""
        self.running = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5)
        logger.info("Digital Ocean monitoring stopped")
    
    def _monitoring_worker(self):
        """Background monitoring worker"""
        while self.running:
            try:
                self._collect_all_metrics()
                time.sleep(self.config.metrics_interval)
            except Exception as e:
                logger.error(f"Error in monitoring worker: {e}")
                time.sleep(60)  # Wait 1 minute before retrying
    
    def _collect_all_metrics(self):
        """Collect metrics from all monitored resources"""
        try:
            # Collect droplet metrics
            droplets = self.get_all_droplets()
            for droplet in droplets:
                metrics = self.get_droplet_metrics(droplet["id"])
                self.metrics_cache[f"droplet_{droplet['id']}"] = metrics
            
            # Collect container metrics if enabled
            if self.config.container_monitoring:
                containers = self.get_all_containers()
                for container in containers:
                    metrics = self.get_container_metrics(container["id"])
                    self.metrics_cache[f"container_{container['id']}"] = metrics
            
            # Collect database metrics if enabled
            if self.config.database_monitoring:
                databases = self.get_all_databases()
                for database in databases:
                    metrics = self.get_database_metrics(database["id"])
                    self.metrics_cache[f"database_{database['id']}"] = metrics
            
            # Collect load balancer metrics if enabled
            if self.config.load_balancer_monitoring:
                load_balancers = self.get_all_load_balancers()
                for lb in load_balancers:
                    metrics = self.get_load_balancer_metrics(lb["id"])
                    self.metrics_cache[f"load_balancer_{lb['id']}"] = metrics
            
            self.last_check = datetime.utcnow()
            
        except Exception as e:
            logger.error(f"Error collecting metrics: {e}")
    
    def get_droplet_metrics(self, droplet_id: str) -> Dict[str, Any]:
        """Get enhanced metrics for a specific droplet"""
        try:
            url = f"{self.base_url}/monitoring/metrics/droplet/{droplet_id}"
            params = {
                "start": (datetime.utcnow() - timedelta(hours=1)).isoformat(),
                "end": datetime.utcnow().isoformat(),
                "host_id": droplet_id
            }
            
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            # Enhanced metrics processing
            enhanced_metrics = {
                "droplet_id": droplet_id,
                "timestamp": datetime.utcnow().isoformat(),
                "cpu": self._process_cpu_metrics(data.get("data", {}).get("cpu", [])),
                "memory": self._process_memory_metrics(data.get("data", {}).get("memory", [])),
                "disk": self._process_disk_metrics(data.get("data", {}).get("disk", [])),
                "network": self._process_network_metrics(data.get("data", {}).get("network", [])),
                "load": self._process_load_metrics(data.get("data", {}).get("load", []))
            }
            
            return enhanced_metrics
        
        except Exception as e:
            logger.error(f"Error getting droplet metrics: {e}")
            return {"droplet_id": droplet_id, "error": str(e)}
    
    def get_container_metrics(self, container_id: str) -> Dict[str, Any]:
        """Get metrics for a specific container"""
        try:
            url = f"{self.base_url}/apps/{container_id}/metrics"
            params = {
                "start": (datetime.utcnow() - timedelta(hours=1)).isoformat(),
                "end": datetime.utcnow().isoformat()
            }
            
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            return {
                "container_id": container_id,
                "timestamp": datetime.utcnow().isoformat(),
                "cpu_usage": data.get("cpu_usage", 0),
                "memory_usage": data.get("memory_usage", 0),
                "restart_count": data.get("restart_count", 0),
                "status": data.get("status", "unknown")
            }
        
        except Exception as e:
            logger.error(f"Error getting container metrics: {e}")
            return {"container_id": container_id, "error": str(e)}
    
    def get_database_metrics(self, database_id: str) -> Dict[str, Any]:
        """Get metrics for a specific database"""
        try:
            url = f"{self.base_url}/databases/{database_id}/metrics"
            params = {
                "start": (datetime.utcnow() - timedelta(hours=1)).isoformat(),
                "end": datetime.utcnow().isoformat()
            }
            
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            return {
                "database_id": database_id,
                "timestamp": datetime.utcnow().isoformat(),
                "connection_count": data.get("connection_count", 0),
                "query_time": data.get("avg_query_time", 0),
                "disk_usage": data.get("disk_usage_percent", 0),
                "active_connections": data.get("active_connections", 0)
            }
        
        except Exception as e:
            logger.error(f"Error getting database metrics: {e}")
            return {"database_id": database_id, "error": str(e)}
    
    def get_load_balancer_metrics(self, lb_id: str) -> Dict[str, Any]:
        """Get metrics for a specific load balancer"""
        try:
            url = f"{self.base_url}/load_balancers/{lb_id}/metrics"
            params = {
                "start": (datetime.utcnow() - timedelta(hours=1)).isoformat(),
                "end": datetime.utcnow().isoformat()
            }
            
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            return {
                "load_balancer_id": lb_id,
                "timestamp": datetime.utcnow().isoformat(),
                "error_rate": data.get("error_rate", 0),
                "response_time": data.get("avg_response_time", 0),
                "requests_per_second": data.get("requests_per_second", 0),
                "unhealthy_backends": data.get("unhealthy_backends", 0)
            }
        
        except Exception as e:
            logger.error(f"Error getting load balancer metrics: {e}")
            return {"load_balancer_id": lb_id, "error": str(e)}
    
    def get_all_droplets(self) -> List[Dict[str, Any]]:
        """Get all droplets with enhanced information"""
        try:
            url = f"{self.base_url}/droplets"
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            
            droplets = response.json().get("droplets", [])
            
            # Enhanced droplet information
            enhanced_droplets = []
            for droplet in droplets:
                enhanced_droplet = {
                    "id": droplet["id"],
                    "name": droplet["name"],
                    "status": droplet["status"],
                    "region": droplet["region"]["slug"],
                    "size": droplet["size"]["slug"],
                    "image": droplet["image"]["name"],
                    "created_at": droplet["created_at"],
                    "tags": droplet.get("tags", []),
                    "monitoring_enabled": droplet.get("monitoring", False),
                    "backups_enabled": droplet.get("backups", False),
                    "ipv4": droplet.get("networks", {}).get("v4", []),
                    "ipv6": droplet.get("networks", {}).get("v6", [])
                }
                enhanced_droplets.append(enhanced_droplet)
            
            return enhanced_droplets
        
        except Exception as e:
            logger.error(f"Error getting droplets: {e}")
            return []
    
    def get_all_containers(self) -> List[Dict[str, Any]]:
        """Get all containers"""
        try:
            url = f"{self.base_url}/apps"
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            
            apps = response.json().get("apps", [])
            containers = []
            
            for app in apps:
                if app.get("spec", {}).get("services"):
                    for service in app["spec"]["services"]:
                        containers.append({
                            "id": app["id"],
                            "name": app["name"],
                            "service_name": service.get("name", "default"),
                            "status": app.get("live_url") is not None
                        })
            
            return containers
        
        except Exception as e:
            logger.error(f"Error getting containers: {e}")
            return []
    
    def get_all_databases(self) -> List[Dict[str, Any]]:
        """Get all databases"""
        try:
            url = f"{self.base_url}/databases"
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            
            databases = response.json().get("databases", [])
            
            enhanced_databases = []
            for db in databases:
                enhanced_db = {
                    "id": db["id"],
                    "name": db["name"],
                    "engine": db["engine"],
                    "version": db["version"],
                    "status": db["status"],
                    "region": db["region"],
                    "size": db["size"],
                    "created_at": db["created_at"]
                }
                enhanced_databases.append(enhanced_db)
            
            return enhanced_databases
        
        except Exception as e:
            logger.error(f"Error getting databases: {e}")
            return []
    
    def get_all_load_balancers(self) -> List[Dict[str, Any]]:
        """Get all load balancers"""
        try:
            url = f"{self.base_url}/load_balancers"
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            
            load_balancers = response.json().get("load_balancers", [])
            
            enhanced_lbs = []
            for lb in load_balancers:
                enhanced_lb = {
                    "id": lb["id"],
                    "name": lb["name"],
                    "status": lb["status"],
                    "region": lb["region"]["slug"],
                    "ip": lb["ip"],
                    "algorithm": lb["algorithm"],
                    "health_check": lb.get("health_check", {}),
                    "created_at": lb["created_at"]
                }
                enhanced_lbs.append(enhanced_lb)
            
            return enhanced_lbs
        
        except Exception as e:
            logger.error(f"Error getting load balancers: {e}")
            return []
    
    def _process_cpu_metrics(self, cpu_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Process CPU metrics data"""
        if not cpu_data:
            return {"current": 0, "average": 0, "peak": 0}
        
        values = [point.get("value", 0) for point in cpu_data if point.get("value") is not None]
        
        return {
            "current": values[-1] if values else 0,
            "average": sum(values) / len(values) if values else 0,
            "peak": max(values) if values else 0,
            "trend": "increasing" if len(values) > 1 and values[-1] > values[-2] else "stable"
        }
    
    def _process_memory_metrics(self, memory_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Process memory metrics data"""
        if not memory_data:
            return {"current": 0, "average": 0, "peak": 0}
        
        values = [point.get("value", 0) for point in memory_data if point.get("value") is not None]
        
        return {
            "current": values[-1] if values else 0,
            "average": sum(values) / len(values) if values else 0,
            "peak": max(values) if values else 0,
            "trend": "increasing" if len(values) > 1 and values[-1] > values[-2] else "stable"
        }
    
    def _process_disk_metrics(self, disk_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Process disk metrics data"""
        if not disk_data:
            return {"current": 0, "average": 0, "peak": 0}
        
        values = [point.get("value", 0) for point in disk_data if point.get("value") is not None]
        
        return {
            "current": values[-1] if values else 0,
            "average": sum(values) / len(values) if values else 0,
            "peak": max(values) if values else 0,
            "trend": "increasing" if len(values) > 1 and values[-1] > values[-2] else "stable"
        }
    
    def _process_network_metrics(self, network_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Process network metrics data"""
        if not network_data:
            return {"in": 0, "out": 0, "total": 0}
        
        in_values = [point.get("in", 0) for point in network_data if point.get("in") is not None]
        out_values = [point.get("out", 0) for point in network_data if point.get("out") is not None]
        
        return {
            "in": in_values[-1] if in_values else 0,
            "out": out_values[-1] if out_values else 0,
            "total": (in_values[-1] if in_values else 0) + (out_values[-1] if out_values else 0),
            "in_trend": "increasing" if len(in_values) > 1 and in_values[-1] > in_values[-2] else "stable",
            "out_trend": "increasing" if len(out_values) > 1 and out_values[-1] > out_values[-2] else "stable"
        }
    
    def _process_load_metrics(self, load_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Process load average metrics data"""
        if not load_data:
            return {"current": 0, "average": 0, "peak": 0}
        
        values = [point.get("value", 0) for point in load_data if point.get("value") is not None]
        
        return {
            "current": values[-1] if values else 0,
            "average": sum(values) / len(values) if values else 0,
            "peak": max(values) if values else 0,
            "trend": "increasing" if len(values) > 1 and values[-1] > values[-2] else "stable"
        }
    
    def check_metrics_thresholds(self, metrics: Dict[str, Any], resource_type: str = "droplet") -> List[Dict[str, Any]]:
        """Check metrics against configured thresholds"""
        alerts = []
        
        if resource_type == "droplet":
            thresholds = self.config.alert_thresholds
        elif resource_type == "container":
            thresholds = self.config.container_alert_thresholds
        elif resource_type == "database":
            thresholds = self.config.database_alert_thresholds
        elif resource_type == "load_balancer":
            thresholds = self.config.load_balancer_alert_thresholds
        else:
            return alerts
        
        for metric_name, threshold in thresholds.items():
            current_value = self._get_metric_value(metrics, metric_name)
            if current_value is not None and current_value > threshold:
                alerts.append({
                    "resource_type": resource_type,
                    "metric": metric_name,
                    "current_value": current_value,
                    "threshold": threshold,
                    "severity": "critical" if current_value > threshold * 1.5 else "high",
                    "timestamp": datetime.utcnow().isoformat()
                })
        
        return alerts
    
    def _get_metric_value(self, metrics: Dict[str, Any], metric_name: str) -> Optional[float]:
        """Extract metric value from metrics dictionary"""
        if metric_name == "cpu_percent":
            return metrics.get("cpu", {}).get("current", 0)
        elif metric_name == "memory_percent":
            return metrics.get("memory", {}).get("current", 0)
        elif metric_name == "disk_percent":
            return metrics.get("disk", {}).get("current", 0)
        elif metric_name == "network_in":
            return metrics.get("network", {}).get("in", 0)
        elif metric_name == "network_out":
            return metrics.get("network", {}).get("out", 0)
        elif metric_name == "load_average":
            return metrics.get("load", {}).get("current", 0)
        else:
            return metrics.get(metric_name, 0)
    
    def get_system_health(self) -> Dict[str, Any]:
        """Get comprehensive system health assessment"""
        try:
            health_data = {
                "overall_status": "healthy",
                "timestamp": datetime.utcnow().isoformat(),
                "resources": {
                    "droplets": [],
                    "containers": [],
                    "databases": [],
                    "load_balancers": []
                },
                "alerts": [],
                "summary": {
                    "total_resources": 0,
                    "healthy_resources": 0,
                    "warning_resources": 0,
                    "critical_resources": 0
                }
            }
            
            # Check droplets
            droplets = self.get_all_droplets()
            for droplet in droplets:
                droplet_health = self._assess_droplet_health(droplet)
                health_data["resources"]["droplets"].append(droplet_health)
                health_data["alerts"].extend(droplet_health.get("alerts", []))
            
            # Check containers if enabled
            if self.config.container_monitoring:
                containers = self.get_all_containers()
                for container in containers:
                    container_health = self._assess_container_health(container)
                    health_data["resources"]["containers"].append(container_health)
                    health_data["alerts"].extend(container_health.get("alerts", []))
            
            # Check databases if enabled
            if self.config.database_monitoring:
                databases = self.get_all_databases()
                for database in databases:
                    database_health = self._assess_database_health(database)
                    health_data["resources"]["databases"].append(database_health)
                    health_data["alerts"].extend(database_health.get("alerts", []))
            
            # Check load balancers if enabled
            if self.config.load_balancer_monitoring:
                load_balancers = self.get_all_load_balancers()
                for lb in load_balancers:
                    lb_health = self._assess_load_balancer_health(lb)
                    health_data["resources"]["load_balancers"].append(lb_health)
                    health_data["alerts"].extend(lb_health.get("alerts", []))
            
            # Calculate summary
            self._calculate_health_summary(health_data)
            
            # Determine overall status
            critical_alerts = [alert for alert in health_data["alerts"] if alert["severity"] == "critical"]
            high_alerts = [alert for alert in health_data["alerts"] if alert["severity"] == "high"]
            
            if critical_alerts:
                health_data["overall_status"] = "critical"
            elif high_alerts:
                health_data["overall_status"] = "warning"
            elif health_data["summary"]["warning_resources"] > 0:
                health_data["overall_status"] = "warning"
            else:
                health_data["overall_status"] = "healthy"
            
            return health_data
        
        except Exception as e:
            logger.error(f"Error getting system health: {e}")
            return {"overall_status": "error", "error": str(e)}
    
    def _assess_droplet_health(self, droplet: Dict[str, Any]) -> Dict[str, Any]:
        """Assess health of a specific droplet"""
        try:
            metrics = self.get_droplet_metrics(droplet["id"])
            alerts = self.check_metrics_thresholds(metrics, "droplet")
            
            health_score = self._calculate_health_score(metrics, alerts)
            
            return {
                "id": droplet["id"],
                "name": droplet["name"],
                "status": droplet["status"],
                "health_score": health_score,
                "metrics": metrics,
                "alerts": alerts,
                "health_status": self._get_health_status(health_score)
            }
        
        except Exception as e:
            logger.error(f"Error assessing droplet health: {e}")
            return {
                "id": droplet["id"],
                "name": droplet["name"],
                "status": "error",
                "health_score": 0,
                "error": str(e)
            }
    
    def _assess_container_health(self, container: Dict[str, Any]) -> Dict[str, Any]:
        """Assess health of a specific container"""
        try:
            metrics = self.get_container_metrics(container["id"])
            alerts = self.check_metrics_thresholds(metrics, "container")
            
            health_score = self._calculate_health_score(metrics, alerts)
            
            return {
                "id": container["id"],
                "name": container["name"],
                "service_name": container.get("service_name"),
                "status": container["status"],
                "health_score": health_score,
                "metrics": metrics,
                "alerts": alerts,
                "health_status": self._get_health_status(health_score)
            }
        
        except Exception as e:
            logger.error(f"Error assessing container health: {e}")
            return {
                "id": container["id"],
                "name": container["name"],
                "status": "error",
                "health_score": 0,
                "error": str(e)
            }
    
    def _assess_database_health(self, database: Dict[str, Any]) -> Dict[str, Any]:
        """Assess health of a specific database"""
        try:
            metrics = self.get_database_metrics(database["id"])
            alerts = self.check_metrics_thresholds(metrics, "database")
            
            health_score = self._calculate_health_score(metrics, alerts)
            
            return {
                "id": database["id"],
                "name": database["name"],
                "engine": database["engine"],
                "status": database["status"],
                "health_score": health_score,
                "metrics": metrics,
                "alerts": alerts,
                "health_status": self._get_health_status(health_score)
            }
        
        except Exception as e:
            logger.error(f"Error assessing database health: {e}")
            return {
                "id": database["id"],
                "name": database["name"],
                "status": "error",
                "health_score": 0,
                "error": str(e)
            }
    
    def _assess_load_balancer_health(self, lb: Dict[str, Any]) -> Dict[str, Any]:
        """Assess health of a specific load balancer"""
        try:
            metrics = self.get_load_balancer_metrics(lb["id"])
            alerts = self.check_metrics_thresholds(metrics, "load_balancer")
            
            health_score = self._calculate_health_score(metrics, alerts)
            
            return {
                "id": lb["id"],
                "name": lb["name"],
                "status": lb["status"],
                "health_score": health_score,
                "metrics": metrics,
                "alerts": alerts,
                "health_status": self._get_health_status(health_score)
            }
        
        except Exception as e:
            logger.error(f"Error assessing load balancer health: {e}")
            return {
                "id": lb["id"],
                "name": lb["name"],
                "status": "error",
                "health_score": 0,
                "error": str(e)
            }
    
    def _calculate_health_score(self, metrics: Dict[str, Any], alerts: List[Dict[str, Any]]) -> float:
        """Calculate health score based on metrics and alerts"""
        base_score = 100.0
        
        # Deduct points for alerts
        for alert in alerts:
            if alert["severity"] == "critical":
                base_score -= 30
            elif alert["severity"] == "high":
                base_score -= 15
            elif alert["severity"] == "medium":
                base_score -= 5
        
        # Deduct points for high resource usage
        if metrics.get("cpu", {}).get("current", 0) > 90:
            base_score -= 20
        elif metrics.get("cpu", {}).get("current", 0) > 80:
            base_score -= 10
        
        if metrics.get("memory", {}).get("current", 0) > 90:
            base_score -= 20
        elif metrics.get("memory", {}).get("current", 0) > 80:
            base_score -= 10
        
        if metrics.get("disk", {}).get("current", 0) > 95:
            base_score -= 25
        elif metrics.get("disk", {}).get("current", 0) > 90:
            base_score -= 15
        
        return max(0.0, base_score)
    
    def _get_health_status(self, health_score: float) -> str:
        """Get health status based on health score"""
        if health_score >= 90:
            return "excellent"
        elif health_score >= 75:
            return "good"
        elif health_score >= 50:
            return "fair"
        elif health_score >= 25:
            return "poor"
        else:
            return "critical"
    
    def _calculate_health_summary(self, health_data: Dict[str, Any]):
        """Calculate health summary statistics"""
        total_resources = 0
        healthy_resources = 0
        warning_resources = 0
        critical_resources = 0
        
        for resource_type in ["droplets", "containers", "databases", "load_balancers"]:
            for resource in health_data["resources"][resource_type]:
                total_resources += 1
                health_status = resource.get("health_status", "unknown")
                
                if health_status in ["excellent", "good"]:
                    healthy_resources += 1
                elif health_status in ["fair", "poor"]:
                    warning_resources += 1
                elif health_status == "critical":
                    critical_resources += 1
        
        health_data["summary"] = {
            "total_resources": total_resources,
            "healthy_resources": healthy_resources,
            "warning_resources": warning_resources,
            "critical_resources": critical_resources
        }
    
    def get_metrics_history(self, resource_id: str, hours: int = 24) -> Dict[str, Any]:
        """Get metrics history for a resource"""
        try:
            cache_key = f"droplet_{resource_id}"
            if cache_key in self.metrics_cache:
                history = list(self.metrics_cache[cache_key])
                return {
                    "resource_id": resource_id,
                    "history": history,
                    "hours": hours,
                    "count": len(history)
                }
            else:
                return {"resource_id": resource_id, "history": [], "error": "No history available"}
        
        except Exception as e:
            logger.error(f"Error getting metrics history: {e}")
            return {"resource_id": resource_id, "error": str(e)}
    
    def get_performance_trends(self, resource_id: str, days: int = 7) -> Dict[str, Any]:
        """Get performance trends for a resource"""
        try:
            # This would typically query historical data from a time-series database
            # For now, we'll return a placeholder structure
            return {
                "resource_id": resource_id,
                "days": days,
                "trends": {
                    "cpu": {"trend": "stable", "change_percent": 2.5},
                    "memory": {"trend": "increasing", "change_percent": 8.3},
                    "disk": {"trend": "stable", "change_percent": 1.2},
                    "network": {"trend": "decreasing", "change_percent": -5.1}
                }
            }
        
        except Exception as e:
            logger.error(f"Error getting performance trends: {e}")
            return {"resource_id": resource_id, "error": str(e)}

# Factory function for creating monitoring configuration
def create_digital_ocean_monitoring_config(
    api_token: str = None,
    monitoring_enabled: bool = True,
    metrics_interval: int = 300,
    alert_thresholds: Dict[str, float] = None
) -> DigitalOceanMonitoringConfig:
    """Create Digital Ocean monitoring configuration"""
    
    if api_token is None:
        api_token = os.getenv('DIGITALOCEAN_API_TOKEN', '')
    
    if alert_thresholds is None:
        alert_thresholds = {
            "cpu_percent": 80,
            "memory_percent": 85,
            "disk_percent": 90,
            "network_in": 1000000000,
            "network_out": 1000000000,
            "load_average": 2.0
        }
    
    return DigitalOceanMonitoringConfig(
        api_token=api_token,
        monitoring_enabled=monitoring_enabled,
        metrics_interval=metrics_interval,
        alert_thresholds=alert_thresholds
    )

# Global monitor instance
_digital_ocean_monitor = None

def get_digital_ocean_monitor() -> EnhancedDigitalOceanMonitor:
    """Get global Digital Ocean monitor instance"""
    global _digital_ocean_monitor
    
    if _digital_ocean_monitor is None:
        config = create_digital_ocean_monitoring_config()
        _digital_ocean_monitor = EnhancedDigitalOceanMonitor(config)
    
    return _digital_ocean_monitor 