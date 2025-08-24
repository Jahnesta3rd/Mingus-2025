"""
Comprehensive Integration Dashboard
Unified dashboard for Digital Ocean monitoring, alerting, log aggregation, and incident response
"""

import os
import json
import time
import threading
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict
from loguru import logger
from flask import Blueprint, jsonify, request
from flask_cors import CORS

# Import our enhanced systems
from .digital_ocean_monitor import EnhancedDigitalOceanMonitor, DigitalOceanMonitoringConfig
from .enhanced_alerting import EnhancedAlertManager, AlertConfig, AlertPriority, AlertChannel
from .enhanced_log_aggregator import EnhancedLogAggregator, LogAggregationConfig
from .enhanced_incident_response import EnhancedSecurityIncidentManager, IncidentResponseConfig, IncidentSeverity, IncidentStatus

# Create Flask blueprint
integration_bp = Blueprint('integration', __name__, url_prefix='/api/integration')
CORS(integration_bp)

@dataclass
class IntegrationDashboardConfig:
    """Integration dashboard configuration"""
    refresh_interval: int = 30  # seconds
    enable_real_time_updates: bool = True
    enable_websockets: bool = True
    dashboard_timeout: int = 300  # seconds
    max_history_items: int = 1000

class IntegrationDashboard:
    """Comprehensive integration dashboard"""
    
    def __init__(self, config: IntegrationDashboardConfig):
        self.config = config
        self.dashboard_data = {}
        self.last_update = None
        self.update_thread = None
        self.running = False
        
        # Initialize all systems
        self.digital_ocean_monitor = None
        self.alert_manager = None
        self.log_aggregator = None
        self.incident_manager = None
        
        self._initialize_systems()
        self._start_update_thread()
    
    def _initialize_systems(self):
        """Initialize all integration systems"""
        try:
            # Initialize Digital Ocean monitoring
            do_config = DigitalOceanMonitoringConfig(
                api_token=os.getenv('DIGITALOCEAN_API_TOKEN', ''),
                monitoring_enabled=os.getenv('DIGITALOCEAN_MONITORING_ENABLED', 'true').lower() == 'true',
                metrics_interval=int(os.getenv('DIGITALOCEAN_METRICS_INTERVAL', '300')),
                alert_thresholds=json.loads(os.getenv('DIGITALOCEAN_ALERT_THRESHOLDS', '{"cpu_percent": 80, "memory_percent": 85, "disk_percent": 90}'))
            )
            self.digital_ocean_monitor = EnhancedDigitalOceanMonitor(do_config)
            
            # Initialize alert manager
            alert_config = AlertConfig(
                email_enabled=os.getenv('ALERT_EMAIL_ENABLED', 'true').lower() == 'true',
                smtp_server=os.getenv('SMTP_SERVER', 'smtp.gmail.com'),
                smtp_port=int(os.getenv('SMTP_PORT', '587')),
                smtp_username=os.getenv('SMTP_USERNAME', ''),
                smtp_password=os.getenv('SMTP_PASSWORD', ''),
                from_email=os.getenv('ALERT_FROM_EMAIL', 'alerts@mingus.com'),
                to_emails=os.getenv('ALERT_TO_EMAILS', '').split(',') if os.getenv('ALERT_TO_EMAILS') else [],
                
                sms_enabled=os.getenv('ALERT_SMS_ENABLED', 'true').lower() == 'true',
                twilio_account_sid=os.getenv('TWILIO_ACCOUNT_SID', ''),
                twilio_auth_token=os.getenv('TWILIO_AUTH_TOKEN', ''),
                twilio_phone_number=os.getenv('TWILIO_PHONE_NUMBER', ''),
                to_phone_numbers=os.getenv('ALERT_TO_PHONES', '').split(',') if os.getenv('ALERT_TO_PHONES') else [],
                
                slack_enabled=os.getenv('ALERT_SLACK_ENABLED', 'true').lower() == 'true',
                slack_webhook_url=os.getenv('SLACK_WEBHOOK_URL', ''),
                slack_channel=os.getenv('SLACK_CHANNEL', '#alerts'),
                
                discord_enabled=os.getenv('ALERT_DISCORD_ENABLED', 'true').lower() == 'true',
                discord_webhook_url=os.getenv('DISCORD_WEBHOOK_URL', ''),
                
                teams_enabled=os.getenv('ALERT_TEAMS_ENABLED', 'true').lower() == 'true',
                teams_webhook_url=os.getenv('TEAMS_WEBHOOK_URL', ''),
                
                webhook_enabled=os.getenv('ALERT_WEBHOOK_ENABLED', 'true').lower() == 'true',
                webhook_url=os.getenv('WEBHOOK_URL', ''),
                webhook_headers=json.loads(os.getenv('WEBHOOK_HEADERS', '{}')),
                
                pagerduty_enabled=os.getenv('ALERT_PAGERDUTY_ENABLED', 'true').lower() == 'true',
                pagerduty_api_key=os.getenv('PAGERDUTY_API_KEY', ''),
                pagerduty_service_id=os.getenv('PAGERDUTY_SERVICE_ID', ''),
                
                opsgenie_enabled=os.getenv('ALERT_OPSGENIE_ENABLED', 'true').lower() == 'true',
                opsgenie_api_key=os.getenv('OPSGENIE_API_KEY', ''),
                opsgenie_team=os.getenv('OPSGENIE_TEAM', ''),
                
                telegram_enabled=os.getenv('ALERT_TELEGRAM_ENABLED', 'true').lower() == 'true',
                telegram_bot_token=os.getenv('TELEGRAM_BOT_TOKEN', ''),
                telegram_chat_id=os.getenv('TELEGRAM_CHAT_ID', '')
            )
            self.alert_manager = EnhancedAlertManager(alert_config)
            
            # Initialize log aggregator
            log_config = LogAggregationConfig(
                enabled=os.getenv('LOG_AGGREGATION_ENABLED', 'true').lower() == 'true',
                log_sources=os.getenv('LOG_SOURCES', 'application,security,system').split(','),
                aggregation_interval=int(os.getenv('LOG_AGGREGATION_INTERVAL', '60')),
                retention_days=int(os.getenv('LOG_RETENTION_DAYS', '30')),
                analysis_enabled=os.getenv('LOG_ANALYSIS_ENABLED', 'true').lower() == 'true',
                anomaly_detection=os.getenv('LOG_ANOMALY_DETECTION', 'true').lower() == 'true',
                pattern_detection=os.getenv('LOG_PATTERN_DETECTION', 'true').lower() == 'true',
                security_analysis=os.getenv('LOG_SECURITY_ANALYSIS', 'true').lower() == 'true',
                performance_analysis=os.getenv('LOG_PERFORMANCE_ANALYSIS', 'true').lower() == 'true',
                compliance_analysis=os.getenv('LOG_COMPLIANCE_ANALYSIS', 'true').lower() == 'true'
            )
            self.log_aggregator = EnhancedLogAggregator(log_config)
            
            # Initialize incident manager
            incident_config = IncidentResponseConfig(
                enabled=os.getenv('INCIDENT_RESPONSE_ENABLED', 'true').lower() == 'true',
                auto_escalation=os.getenv('INCIDENT_AUTO_ESCALATION', 'true').lower() == 'true',
                escalation_threshold=int(os.getenv('INCIDENT_ESCALATION_THRESHOLD', '3')),
                response_team=os.getenv('INCIDENT_RESPONSE_TEAM', '').split(',') if os.getenv('INCIDENT_RESPONSE_TEAM') else [],
                escalation_team=os.getenv('INCIDENT_ESCALATION_TEAM', '').split(',') if os.getenv('INCIDENT_ESCALATION_TEAM') else [],
                notification_channels=os.getenv('INCIDENT_NOTIFICATION_CHANNELS', 'email,slack').split(','),
                
                email_enabled=os.getenv('INCIDENT_EMAIL_ENABLED', 'true').lower() == 'true',
                smtp_server=os.getenv('INCIDENT_SMTP_SERVER', 'smtp.gmail.com'),
                smtp_port=int(os.getenv('INCIDENT_SMTP_PORT', '587')),
                smtp_username=os.getenv('INCIDENT_SMTP_USERNAME', ''),
                smtp_password=os.getenv('INCIDENT_SMTP_PASSWORD', ''),
                from_email=os.getenv('INCIDENT_FROM_EMAIL', 'incidents@mingus.com'),
                
                slack_enabled=os.getenv('INCIDENT_SLACK_ENABLED', 'true').lower() == 'true',
                slack_webhook_url=os.getenv('INCIDENT_SLACK_WEBHOOK_URL', ''),
                slack_channel=os.getenv('INCIDENT_SLACK_CHANNEL', '#incidents')
            )
            self.incident_manager = EnhancedSecurityIncidentManager(incident_config)
            
            logger.info("All integration systems initialized successfully")
        
        except Exception as e:
            logger.error(f"Error initializing integration systems: {e}")
    
    def _start_update_thread(self):
        """Start dashboard update thread"""
        if self.running:
            return
        
        self.running = True
        self.update_thread = threading.Thread(target=self._update_dashboard, daemon=True)
        self.update_thread.start()
        logger.info("Integration dashboard update thread started")
    
    def _update_dashboard(self):
        """Update dashboard data"""
        while self.running:
            try:
                self.dashboard_data = self._collect_dashboard_data()
                self.last_update = datetime.utcnow()
                time.sleep(self.config.refresh_interval)
            except Exception as e:
                logger.error(f"Error updating dashboard: {e}")
                time.sleep(60)  # Wait 1 minute before retrying
    
    def _collect_dashboard_data(self) -> Dict[str, Any]:
        """Collect comprehensive dashboard data"""
        try:
            dashboard_data = {
                "timestamp": datetime.utcnow().isoformat(),
                "overall_status": "healthy",
                "systems": {},
                "alerts": {},
                "incidents": {},
                "logs": {},
                "performance": {},
                "security": {}
            }
            
            # Digital Ocean monitoring data
            if self.digital_ocean_monitor:
                try:
                    do_health = self.digital_ocean_monitor.get_system_health()
                    dashboard_data["systems"]["digital_ocean"] = {
                        "status": do_health.get("overall_status", "unknown"),
                        "droplets": len(do_health.get("droplets", [])),
                        "total_alerts": do_health.get("total_alerts", 0),
                        "health_score": self._calculate_overall_health_score(do_health)
                    }
                except Exception as e:
                    logger.error(f"Error getting Digital Ocean data: {e}")
                    dashboard_data["systems"]["digital_ocean"] = {"status": "error", "error": str(e)}
            
            # Alert manager data
            if self.alert_manager:
                try:
                    alert_stats = self.alert_manager.get_alert_stats(hours=24)
                    dashboard_data["alerts"] = {
                        "total_alerts": alert_stats.get("total_alerts", 0),
                        "by_priority": alert_stats.get("by_priority", {}),
                        "by_status": alert_stats.get("by_status", {}),
                        "delivery_stats": alert_stats.get("delivery_stats", {})
                    }
                except Exception as e:
                    logger.error(f"Error getting alert data: {e}")
                    dashboard_data["alerts"] = {"error": str(e)}
            
            # Log aggregator data
            if self.log_aggregator:
                try:
                    log_stats = self.log_aggregator.get_log_statistics(hours=24)
                    dashboard_data["logs"] = {
                        "total_logs": log_stats.get("total_logs", 0),
                        "by_level": log_stats.get("logs_by_level", {}),
                        "by_source": log_stats.get("logs_by_source", {}),
                        "security_events": log_stats.get("security_events", 0),
                        "anomalies": log_stats.get("anomalies", 0),
                        "performance_alerts": log_stats.get("performance_alerts", 0)
                    }
                    
                    # Get recent security events
                    security_events = self.log_aggregator.get_security_events(hours=6)
                    dashboard_data["security"]["recent_events"] = security_events[:10]  # Last 10 events
                    
                    # Get recent anomalies
                    anomalies = self.log_aggregator.get_anomalies(hours=6)
                    dashboard_data["security"]["recent_anomalies"] = anomalies[:10]  # Last 10 anomalies
                
                except Exception as e:
                    logger.error(f"Error getting log data: {e}")
                    dashboard_data["logs"] = {"error": str(e)}
            
            # Incident manager data
            if self.incident_manager:
                try:
                    incident_stats = self.incident_manager.get_incident_statistics(days=7)
                    dashboard_data["incidents"] = {
                        "total_incidents": incident_stats.get("total_incidents", 0),
                        "by_severity": incident_stats.get("by_severity", {}),
                        "by_status": incident_stats.get("by_status", {}),
                        "by_type": incident_stats.get("by_type", {}),
                        "active_incidents": incident_stats.get("active_incidents", 0)
                    }
                    
                    # Get active incidents
                    active_incidents = self.incident_manager.get_active_incidents()
                    dashboard_data["incidents"]["active_incidents_list"] = [
                        {
                            "id": incident.id,
                            "title": incident.title,
                            "severity": incident.severity.value,
                            "status": incident.status.value,
                            "created_at": incident.created_at.isoformat(),
                            "assigned_to": incident.assigned_to
                        }
                        for incident in active_incidents[:10]  # Last 10 active incidents
                    ]
                
                except Exception as e:
                    logger.error(f"Error getting incident data: {e}")
                    dashboard_data["incidents"] = {"error": str(e)}
            
            # Calculate overall status
            dashboard_data["overall_status"] = self._calculate_overall_status(dashboard_data)
            
            # Performance metrics
            dashboard_data["performance"] = {
                "response_time": self._get_average_response_time(),
                "uptime": self._get_system_uptime(),
                "error_rate": self._get_error_rate(),
                "throughput": self._get_throughput()
            }
            
            return dashboard_data
        
        except Exception as e:
            logger.error(f"Error collecting dashboard data: {e}")
            return {"error": str(e), "timestamp": datetime.utcnow().isoformat()}
    
    def _calculate_overall_status(self, dashboard_data: Dict[str, Any]) -> str:
        """Calculate overall system status"""
        try:
            # Check for critical issues
            if dashboard_data.get("incidents", {}).get("active_incidents", 0) > 5:
                return "critical"
            
            # Check for high severity incidents
            high_severity_incidents = dashboard_data.get("incidents", {}).get("by_severity", {}).get("high", 0)
            if high_severity_incidents > 2:
                return "critical"
            
            # Check Digital Ocean status
            do_status = dashboard_data.get("systems", {}).get("digital_ocean", {}).get("status", "unknown")
            if do_status == "critical":
                return "critical"
            
            # Check for high alert volume
            total_alerts = dashboard_data.get("alerts", {}).get("total_alerts", 0)
            if total_alerts > 50:
                return "warning"
            
            # Check for security events
            security_events = dashboard_data.get("logs", {}).get("security_events", 0)
            if security_events > 10:
                return "warning"
            
            # Check for anomalies
            anomalies = dashboard_data.get("logs", {}).get("anomalies", 0)
            if anomalies > 5:
                return "warning"
            
            return "healthy"
        
        except Exception as e:
            logger.error(f"Error calculating overall status: {e}")
            return "unknown"
    
    def _calculate_overall_health_score(self, do_health: Dict[str, Any]) -> float:
        """Calculate overall health score from Digital Ocean data"""
        try:
            if not do_health.get("droplets"):
                return 0.0
            
            total_score = 0.0
            total_droplets = len(do_health["droplets"])
            
            for droplet in do_health["droplets"]:
                total_score += droplet.get("health_score", 0.0)
            
            return total_score / total_droplets if total_droplets > 0 else 0.0
        
        except Exception as e:
            logger.error(f"Error calculating health score: {e}")
            return 0.0
    
    def _get_average_response_time(self) -> float:
        """Get average response time"""
        # This would integrate with actual performance monitoring
        return 250.0  # Placeholder
    
    def _get_system_uptime(self) -> float:
        """Get system uptime percentage"""
        # This would integrate with actual uptime monitoring
        return 99.95  # Placeholder
    
    def _get_error_rate(self) -> float:
        """Get error rate percentage"""
        # This would integrate with actual error monitoring
        return 0.05  # Placeholder
    
    def _get_throughput(self) -> float:
        """Get system throughput"""
        # This would integrate with actual throughput monitoring
        return 1500.0  # Placeholder
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get current dashboard data"""
        return self.dashboard_data
    
    def process_security_event(self, event: Dict[str, Any]):
        """Process security event through all systems"""
        try:
            # Log aggregation
            if self.log_aggregator:
                self.log_aggregator.aggregate_logs([event])
            
            # Check for critical events that need alerts
            if event.get('severity') in ['critical', 'high']:
                if self.alert_manager:
                    priority = AlertPriority.HIGH if event.get('severity') == 'high' else AlertPriority.CRITICAL
                    self.alert_manager.send_alert(
                        priority,
                        f"Security Event: {event.get('event_type', 'Unknown')}",
                        event,
                        [AlertChannel.EMAIL, AlertChannel.SLACK]
                    )
            
            # Check for incident creation
            if event.get('severity') == 'critical':
                if self.incident_manager:
                    incident_type = self._map_event_to_incident_type(event.get('event_type', 'unknown'))
                    self.incident_manager.create_incident(
                        f"Critical Security Event: {event.get('event_type', 'Unknown')}",
                        event.get('message', 'Critical security event detected'),
                        IncidentSeverity.CRITICAL,
                        incident_type,
                        event
                    )
        
        except Exception as e:
            logger.error(f"Error processing security event: {e}")
    
    def _map_event_to_incident_type(self, event_type: str) -> str:
        """Map event type to incident type"""
        mapping = {
            "sql_injection": "application_attack",
            "xss_attack": "application_attack",
            "ddos_attack": "ddos_attack",
            "malware_detected": "malware_infection",
            "unauthorized_access": "unauthorized_access",
            "data_breach": "data_breach",
            "phishing_attack": "phishing_attack",
            "insider_threat": "insider_threat",
            "system_compromise": "system_compromise",
            "network_intrusion": "network_intrusion"
        }
        return mapping.get(event_type, "security_breach")

# Global dashboard instance
_dashboard = None

def get_integration_dashboard() -> IntegrationDashboard:
    """Get global integration dashboard instance"""
    global _dashboard
    
    if _dashboard is None:
        config = IntegrationDashboardConfig()
        _dashboard = IntegrationDashboard(config)
    
    return _dashboard

# Flask routes
@integration_bp.route('/dashboard')
def get_dashboard():
    """Get comprehensive dashboard data"""
    try:
        dashboard = get_integration_dashboard()
        return jsonify({
            'status': 'success',
            'data': dashboard.get_dashboard_data(),
            'timestamp': datetime.utcnow().isoformat()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@integration_bp.route('/digitalocean/health')
def digital_ocean_health():
    """Get Digital Ocean health"""
    try:
        dashboard = get_integration_dashboard()
        if dashboard.digital_ocean_monitor:
            health = dashboard.digital_ocean_monitor.get_system_health()
            return jsonify({
                'status': 'success',
                'data': health,
                'timestamp': datetime.utcnow().isoformat()
            })
        else:
            return jsonify({'error': 'Digital Ocean monitoring not enabled'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@integration_bp.route('/alerts/send', methods=['POST'])
def send_alert():
    """Send alert"""
    try:
        data = request.get_json()
        dashboard = get_integration_dashboard()
        
        if dashboard.alert_manager:
            priority = AlertPriority(data.get('priority', 'medium'))
            message = data.get('message', '')
            details = data.get('details', {})
            channels = [AlertChannel(ch) for ch in data.get('channels', ['email'])]
            
            alert_id = dashboard.alert_manager.send_alert(priority, message, details, channels)
            
            return jsonify({
                'status': 'success',
                'data': {'alert_id': alert_id},
                'timestamp': datetime.utcnow().isoformat()
            })
        else:
            return jsonify({'error': 'Alert manager not enabled'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@integration_bp.route('/alerts/stats')
def alert_stats():
    """Get alert statistics"""
    try:
        dashboard = get_integration_dashboard()
        if dashboard.alert_manager:
            hours = request.args.get('hours', 24, type=int)
            stats = dashboard.alert_manager.get_alert_stats(hours=hours)
            return jsonify({
                'status': 'success',
                'data': stats,
                'timestamp': datetime.utcnow().isoformat()
            })
        else:
            return jsonify({'error': 'Alert manager not enabled'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@integration_bp.route('/logs/aggregate', methods=['POST'])
def aggregate_logs():
    """Aggregate logs"""
    try:
        data = request.get_json()
        logs = data.get('logs', [])
        
        dashboard = get_integration_dashboard()
        if dashboard.log_aggregator:
            dashboard.log_aggregator.aggregate_logs(logs)
            
            return jsonify({
                'status': 'success',
                'data': {'logs_processed': len(logs)},
                'timestamp': datetime.utcnow().isoformat()
            })
        else:
            return jsonify({'error': 'Log aggregator not enabled'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@integration_bp.route('/logs/stats')
def log_stats():
    """Get log statistics"""
    try:
        dashboard = get_integration_dashboard()
        if dashboard.log_aggregator:
            hours = request.args.get('hours', 24, type=int)
            stats = dashboard.log_aggregator.get_log_statistics(hours=hours)
            return jsonify({
                'status': 'success',
                'data': stats,
                'timestamp': datetime.utcnow().isoformat()
            })
        else:
            return jsonify({'error': 'Log aggregator not enabled'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@integration_bp.route('/incidents/create', methods=['POST'])
def create_incident():
    """Create incident"""
    try:
        data = request.get_json()
        dashboard = get_integration_dashboard()
        
        if dashboard.incident_manager:
            title = data.get('title', '')
            description = data.get('description', '')
            severity = IncidentSeverity(data.get('severity', 'medium'))
            incident_type = data.get('incident_type', 'security_breach')
            source_alert = data.get('source_alert', None)
            
            incident_id = dashboard.incident_manager.create_incident(
                title, description, severity, incident_type, source_alert
            )
            
            return jsonify({
                'status': 'success',
                'data': {'incident_id': incident_id},
                'timestamp': datetime.utcnow().isoformat()
            })
        else:
            return jsonify({'error': 'Incident manager not enabled'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@integration_bp.route('/incidents/stats')
def incident_stats():
    """Get incident statistics"""
    try:
        dashboard = get_integration_dashboard()
        if dashboard.incident_manager:
            days = request.args.get('days', 7, type=int)
            stats = dashboard.incident_manager.get_incident_statistics(days=days)
            return jsonify({
                'status': 'success',
                'data': stats,
                'timestamp': datetime.utcnow().isoformat()
            })
        else:
            return jsonify({'error': 'Incident manager not enabled'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@integration_bp.route('/security/event', methods=['POST'])
def process_security_event():
    """Process security event"""
    try:
        data = request.get_json()
        dashboard = get_integration_dashboard()
        
        dashboard.process_security_event(data)
        
        return jsonify({
            'status': 'success',
            'data': {'event_processed': True},
            'timestamp': datetime.utcnow().isoformat()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@integration_bp.route('/status')
def integration_status():
    """Get integration status"""
    try:
        dashboard = get_integration_dashboard()
        
        status = {
            'digital_ocean_monitoring': dashboard.digital_ocean_monitor is not None,
            'alert_manager': dashboard.alert_manager is not None,
            'log_aggregator': dashboard.log_aggregator is not None,
            'incident_manager': dashboard.incident_manager is not None,
            'dashboard_running': dashboard.running,
            'last_update': dashboard.last_update.isoformat() if dashboard.last_update else None
        }
        
        return jsonify({
            'status': 'success',
            'data': status,
            'timestamp': datetime.utcnow().isoformat()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@integration_bp.route('/health')
def health_check():
    """Health check for integrations"""
    try:
        dashboard = get_integration_dashboard()
        dashboard_data = dashboard.get_dashboard_data()
        
        overall_status = dashboard_data.get('overall_status', 'unknown')
        
        if overall_status == 'healthy':
            return jsonify({'status': 'healthy'}), 200
        elif overall_status == 'warning':
            return jsonify({'status': 'warning'}), 200
        else:
            return jsonify({'status': 'unhealthy'}), 503
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500

def register_integration_routes(app):
    """Register integration routes with Flask app"""
    app.register_blueprint(integration_bp)
    logger.info("Integration routes registered") 