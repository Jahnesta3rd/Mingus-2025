from flask import Blueprint, jsonify, request, render_template
from security.integrations import (
    SecurityIntegrations, AlertConfig, DigitalOceanConfig, 
    LogAggregationConfig, IncidentResponseConfig, AlertPriority, 
    IncidentSeverity, IncidentStatus
)
import json
from datetime import datetime
import os

# Create Blueprint for integration routes
integration_bp = Blueprint('security_integrations', __name__, url_prefix='/security/integrations')

# Initialize integrations with configuration from environment variables
def get_integration_configs():
    """Get integration configurations from environment variables"""
    
    # Alert configuration
    alert_config = AlertConfig(
        email_enabled=os.getenv('ALERT_EMAIL_ENABLED', 'true').lower() == 'true',
        sms_enabled=os.getenv('ALERT_SMS_ENABLED', 'true').lower() == 'true',
        slack_enabled=os.getenv('ALERT_SLACK_ENABLED', 'false').lower() == 'true',
        webhook_enabled=os.getenv('ALERT_WEBHOOK_ENABLED', 'false').lower() == 'true',
        pagerduty_enabled=os.getenv('ALERT_PAGERDUTY_ENABLED', 'false').lower() == 'true',
        
        # Email settings
        smtp_server=os.getenv('SMTP_SERVER', 'smtp.gmail.com'),
        smtp_port=int(os.getenv('SMTP_PORT', '587')),
        smtp_username=os.getenv('SMTP_USERNAME', ''),
        smtp_password=os.getenv('SMTP_PASSWORD', ''),
        alert_email_recipients=os.getenv('ALERT_EMAIL_RECIPIENTS', '').split(',') if os.getenv('ALERT_EMAIL_RECIPIENTS') else [],
        
        # SMS settings
        twilio_account_sid=os.getenv('TWILIO_ACCOUNT_SID', ''),
        twilio_auth_token=os.getenv('TWILIO_AUTH_TOKEN', ''),
        twilio_phone_number=os.getenv('TWILIO_PHONE_NUMBER', ''),
        alert_sms_recipients=os.getenv('ALERT_SMS_RECIPIENTS', '').split(',') if os.getenv('ALERT_SMS_RECIPIENTS') else [],
        
        # Slack settings
        slack_webhook_url=os.getenv('SLACK_WEBHOOK_URL', ''),
        slack_channel=os.getenv('SLACK_CHANNEL', '#security-alerts'),
        
        # Webhook settings
        webhook_url=os.getenv('WEBHOOK_URL', ''),
        webhook_headers=json.loads(os.getenv('WEBHOOK_HEADERS', '{}')),
        
        # PagerDuty settings
        pagerduty_api_key=os.getenv('PAGERDUTY_API_KEY', ''),
        pagerduty_service_id=os.getenv('PAGERDUTY_SERVICE_ID', '')
    )
    
    # Digital Ocean configuration
    digital_ocean_config = DigitalOceanConfig(
        api_token=os.getenv('DIGITALOCEAN_API_TOKEN', ''),
        droplet_ids=os.getenv('DIGITALOCEAN_DROPLET_IDS', '').split(',') if os.getenv('DIGITALOCEAN_DROPLET_IDS') else [],
        monitoring_enabled=os.getenv('DIGITALOCEAN_MONITORING_ENABLED', 'true').lower() == 'true',
        metrics_interval=int(os.getenv('DIGITALOCEAN_METRICS_INTERVAL', '300')),
        alert_thresholds=json.loads(os.getenv('DIGITALOCEAN_ALERT_THRESHOLDS', '{"cpu_percent": 80, "memory_percent": 85, "disk_percent": 90}'))
    )
    
    # Log aggregation configuration
    log_config = LogAggregationConfig(
        enabled=os.getenv('LOG_AGGREGATION_ENABLED', 'true').lower() == 'true',
        log_sources=os.getenv('LOG_SOURCES', 'application,security,system').split(','),
        aggregation_interval=int(os.getenv('LOG_AGGREGATION_INTERVAL', '60')),
        retention_days=int(os.getenv('LOG_RETENTION_DAYS', '30')),
        analysis_enabled=os.getenv('LOG_ANALYSIS_ENABLED', 'true').lower() == 'true',
        anomaly_detection=os.getenv('LOG_ANOMALY_DETECTION', 'true').lower() == 'true'
    )
    
    # Incident response configuration
    incident_config = IncidentResponseConfig(
        enabled=os.getenv('INCIDENT_RESPONSE_ENABLED', 'true').lower() == 'true',
        auto_escalation=os.getenv('INCIDENT_AUTO_ESCALATION', 'true').lower() == 'true',
        escalation_threshold=int(os.getenv('INCIDENT_ESCALATION_THRESHOLD', '3')),
        response_team=os.getenv('INCIDENT_RESPONSE_TEAM', '').split(',') if os.getenv('INCIDENT_RESPONSE_TEAM') else [],
        playbooks=json.loads(os.getenv('INCIDENT_PLAYBOOKS', '{"critical": "critical_incident_playbook", "high": "high_incident_playbook"}')),
        notification_channels=os.getenv('INCIDENT_NOTIFICATION_CHANNELS', 'email,sms').split(',')
    )
    
    return alert_config, digital_ocean_config, log_config, incident_config

# Initialize integrations
alert_config, digital_ocean_config, log_config, incident_config = get_integration_configs()
integrations = SecurityIntegrations(alert_config, digital_ocean_config, log_config, incident_config)

@integration_bp.route('/')
def integrations_home():
    """Main integrations page"""
    try:
        status = integrations.get_integration_status()
        return render_template('security_integrations.html', status=status)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Digital Ocean Monitoring Routes
@integration_bp.route('/digitalocean/health')
def digital_ocean_health():
    """Get Digital Ocean system health"""
    try:
        health_data = integrations.digital_ocean_monitor.get_system_health()
        return jsonify({
            'status': 'success',
            'data': health_data,
            'timestamp': datetime.utcnow().isoformat()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@integration_bp.route('/digitalocean/droplets')
def digital_ocean_droplets():
    """Get all Digital Ocean droplets"""
    try:
        droplets = integrations.digital_ocean_monitor.get_all_droplets()
        return jsonify({
            'status': 'success',
            'data': droplets,
            'count': len(droplets),
            'timestamp': datetime.utcnow().isoformat()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@integration_bp.route('/digitalocean/droplet/<droplet_id>/metrics')
def digital_ocean_droplet_metrics(droplet_id):
    """Get metrics for specific droplet"""
    try:
        metrics = integrations.digital_ocean_monitor.get_droplet_metrics(droplet_id)
        alerts = integrations.digital_ocean_monitor.check_metrics_thresholds(metrics)
        
        return jsonify({
            'status': 'success',
            'data': {
                'droplet_id': droplet_id,
                'metrics': metrics,
                'alerts': alerts,
                'health_score': integrations.digital_ocean_monitor._calculate_health_score(metrics, alerts)
            },
            'timestamp': datetime.utcnow().isoformat()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Alert Management Routes
@integration_bp.route('/alerts/send', methods=['POST'])
def send_alert():
    """Send security alert"""
    try:
        data = request.get_json()
        
        priority = AlertPriority(data.get('priority', 'medium'))
        message = data.get('message', '')
        details = data.get('details', {})
        channels = data.get('channels', ['email', 'sms'])
        
        integrations.alert_manager.send_alert(priority, message, details, channels)
        
        return jsonify({
            'status': 'success',
            'message': 'Alert sent successfully',
            'timestamp': datetime.utcnow().isoformat()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@integration_bp.route('/alerts/history')
def alert_history():
    """Get alert history"""
    try:
        limit = request.args.get('limit', 100, type=int)
        history = integrations.alert_manager.get_alert_history(limit)
        
        return jsonify({
            'status': 'success',
            'data': history,
            'count': len(history),
            'timestamp': datetime.utcnow().isoformat()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@integration_bp.route('/alerts/stats')
def alert_statistics():
    """Get alert statistics"""
    try:
        stats = integrations.alert_manager.get_alert_stats()
        
        return jsonify({
            'status': 'success',
            'data': stats,
            'timestamp': datetime.utcnow().isoformat()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Log Aggregation Routes
@integration_bp.route('/logs/aggregate', methods=['POST'])
def aggregate_logs():
    """Aggregate logs from various sources"""
    try:
        data = request.get_json()
        logs = data.get('logs', [])
        
        integrations.log_aggregator.aggregate_logs(logs)
        
        return jsonify({
            'status': 'success',
            'message': f'Successfully aggregated {len(logs)} logs',
            'timestamp': datetime.utcnow().isoformat()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@integration_bp.route('/logs/stats')
def log_statistics():
    """Get log aggregation statistics"""
    try:
        hours = request.args.get('hours', 24, type=int)
        stats = integrations.log_aggregator.get_log_statistics(hours)
        
        return jsonify({
            'status': 'success',
            'data': stats,
            'timestamp': datetime.utcnow().isoformat()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@integration_bp.route('/logs/analysis')
def log_analysis():
    """Get log analysis results"""
    try:
        hours = request.args.get('hours', 24, type=int)
        analysis = integrations.log_aggregator.get_log_statistics(hours)
        
        return jsonify({
            'status': 'success',
            'data': analysis,
            'timestamp': datetime.utcnow().isoformat()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Incident Response Routes
@integration_bp.route('/incidents/create', methods=['POST'])
def create_incident():
    """Create new security incident"""
    try:
        data = request.get_json()
        
        title = data.get('title', '')
        description = data.get('description', '')
        severity = IncidentSeverity(data.get('severity', 'medium'))
        source_alert = data.get('source_alert', None)
        
        incident_id = integrations.incident_manager.create_incident(
            title, description, severity, source_alert
        )
        
        return jsonify({
            'status': 'success',
            'data': {
                'incident_id': incident_id,
                'title': title,
                'severity': severity.value
            },
            'timestamp': datetime.utcnow().isoformat()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@integration_bp.route('/incidents/<incident_id>')
def get_incident(incident_id):
    """Get incident by ID"""
    try:
        incident = integrations.incident_manager.get_incident(incident_id)
        
        if not incident:
            return jsonify({'error': 'Incident not found'}), 404
        
        return jsonify({
            'status': 'success',
            'data': incident,
            'timestamp': datetime.utcnow().isoformat()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@integration_bp.route('/incidents/<incident_id>/status', methods=['PUT'])
def update_incident_status(incident_id):
    """Update incident status"""
    try:
        data = request.get_json()
        
        status = IncidentStatus(data.get('status', 'open'))
        user_id = data.get('user_id', None)
        resolution = data.get('resolution', None)
        
        success = integrations.incident_manager.update_incident_status(
            incident_id, status, user_id, resolution
        )
        
        if not success:
            return jsonify({'error': 'Incident not found'}), 404
        
        return jsonify({
            'status': 'success',
            'message': f'Incident status updated to {status.value}',
            'timestamp': datetime.utcnow().isoformat()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@integration_bp.route('/incidents/<incident_id>/assign', methods=['PUT'])
def assign_incident(incident_id):
    """Assign incident to team member"""
    try:
        data = request.get_json()
        
        assigned_to = data.get('assigned_to', '')
        user_id = data.get('user_id', None)
        
        success = integrations.incident_manager.assign_incident(
            incident_id, assigned_to, user_id
        )
        
        if not success:
            return jsonify({'error': 'Incident not found'}), 404
        
        return jsonify({
            'status': 'success',
            'message': f'Incident assigned to {assigned_to}',
            'timestamp': datetime.utcnow().isoformat()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@integration_bp.route('/incidents/<incident_id>/events', methods=['POST'])
def add_incident_event(incident_id):
    """Add event to incident timeline"""
    try:
        data = request.get_json()
        
        event_type = data.get('event_type', '')
        description = data.get('description', '')
        user_id = data.get('user_id', None)
        metadata = data.get('metadata', None)
        
        integrations.incident_manager.add_incident_event(
            incident_id, event_type, description, user_id, metadata
        )
        
        return jsonify({
            'status': 'success',
            'message': 'Event added to incident timeline',
            'timestamp': datetime.utcnow().isoformat()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@integration_bp.route('/incidents/active')
def active_incidents():
    """Get all active incidents"""
    try:
        incidents = integrations.incident_manager.get_active_incidents()
        
        return jsonify({
            'status': 'success',
            'data': incidents,
            'count': len(incidents),
            'timestamp': datetime.utcnow().isoformat()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@integration_bp.route('/incidents/stats')
def incident_statistics():
    """Get incident statistics"""
    try:
        stats = integrations.incident_manager.get_incident_statistics()
        
        return jsonify({
            'status': 'success',
            'data': stats,
            'timestamp': datetime.utcnow().isoformat()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Integration Status Routes
@integration_bp.route('/status')
def integration_status():
    """Get status of all integrations"""
    try:
        status = integrations.get_integration_status()
        
        return jsonify({
            'status': 'success',
            'data': status,
            'timestamp': datetime.utcnow().isoformat()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@integration_bp.route('/status/health')
def integration_health():
    """Get health check for integrations"""
    try:
        status = integrations.get_integration_status()
        
        # Determine overall health
        overall_health = 'healthy'
        issues = []
        
        # Check each integration
        for integration_name, integration_status in status.items():
            if not integration_status.get('enabled', True):
                continue
            
            if integration_name == 'digital_ocean_monitor':
                health = integration_status.get('health', {})
                if health.get('overall_status') == 'error':
                    overall_health = 'unhealthy'
                    issues.append(f"Digital Ocean monitoring error: {health.get('error', 'Unknown error')}")
            
            elif integration_name == 'alert_manager':
                stats = integration_status.get('stats', {})
                if stats.get('total_alerts', 0) > 100:  # High alert volume
                    issues.append(f"High alert volume: {stats.get('total_alerts')} alerts")
            
            elif integration_name == 'log_aggregator':
                stats = integration_status.get('stats', {})
                if stats.get('total_logs', 0) == 0:  # No logs being processed
                    issues.append("No logs being processed")
            
            elif integration_name == 'incident_manager':
                stats = integration_status.get('stats', {})
                active_incidents = stats.get('active_incidents', 0)
                if active_incidents > 10:  # Too many active incidents
                    overall_health = 'warning'
                    issues.append(f"High number of active incidents: {active_incidents}")
        
        return jsonify({
            'status': 'success',
            'data': {
                'overall_health': overall_health,
                'issues': issues,
                'integrations': status
            },
            'timestamp': datetime.utcnow().isoformat()
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'data': {
                'overall_health': 'unhealthy',
                'issues': [f"Integration error: {str(e)}"],
                'integrations': {}
            },
            'timestamp': datetime.utcnow().isoformat()
        }), 500

# Configuration Routes
@integration_bp.route('/config')
def get_integration_config():
    """Get current integration configuration"""
    try:
        config = {
            'alert_config': {
                'email_enabled': alert_config.email_enabled,
                'sms_enabled': alert_config.sms_enabled,
                'slack_enabled': alert_config.slack_enabled,
                'webhook_enabled': alert_config.webhook_enabled,
                'pagerduty_enabled': alert_config.pagerduty_enabled,
                'smtp_server': alert_config.smtp_server,
                'smtp_port': alert_config.smtp_port,
                'alert_email_recipients': alert_config.alert_email_recipients,
                'alert_sms_recipients': alert_config.alert_sms_recipients,
                'slack_channel': alert_config.slack_channel,
                'webhook_url': alert_config.webhook_url,
            },
            'digital_ocean_config': {
                'monitoring_enabled': digital_ocean_config.monitoring_enabled,
                'metrics_interval': digital_ocean_config.metrics_interval,
                'alert_thresholds': digital_ocean_config.alert_thresholds,
                'droplet_count': len(digital_ocean_config.droplet_ids or [])
            },
            'log_config': {
                'enabled': log_config.enabled,
                'log_sources': log_config.log_sources,
                'aggregation_interval': log_config.aggregation_interval,
                'retention_days': log_config.retention_days,
                'analysis_enabled': log_config.analysis_enabled,
                'anomaly_detection': log_config.anomaly_detection
            },
            'incident_config': {
                'enabled': incident_config.enabled,
                'auto_escalation': incident_config.auto_escalation,
                'escalation_threshold': incident_config.escalation_threshold,
                'response_team': incident_config.response_team,
                'playbooks': incident_config.playbooks,
                'notification_channels': incident_config.notification_channels
            }
        }
        
        return jsonify({
            'status': 'success',
            'data': config,
            'timestamp': datetime.utcnow().isoformat()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Test Routes
@integration_bp.route('/test/alert', methods=['POST'])
def test_alert():
    """Test alert functionality"""
    try:
        data = request.get_json()
        
        priority = AlertPriority(data.get('priority', 'medium'))
        message = data.get('message', 'Test alert from MINGUS Security System')
        channels = data.get('channels', ['email'])
        
        integrations.alert_manager.send_alert(priority, message, {}, channels)
        
        return jsonify({
            'status': 'success',
            'message': 'Test alert sent successfully',
            'timestamp': datetime.utcnow().isoformat()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@integration_bp.route('/test/digitalocean')
def test_digital_ocean():
    """Test Digital Ocean integration"""
    try:
        health = integrations.digital_ocean_monitor.get_system_health()
        
        return jsonify({
            'status': 'success',
            'data': health,
            'message': 'Digital Ocean integration test completed',
            'timestamp': datetime.utcnow().isoformat()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@integration_bp.route('/test/logs', methods=['POST'])
def test_log_aggregation():
    """Test log aggregation"""
    try:
        test_logs = [
            {
                'timestamp': datetime.utcnow().isoformat(),
                'source': 'test',
                'level': 'info',
                'message': 'Test log message',
                'metadata': {'test': True}
            }
        ]
        
        integrations.log_aggregator.aggregate_logs(test_logs)
        
        return jsonify({
            'status': 'success',
            'message': 'Test logs aggregated successfully',
            'timestamp': datetime.utcnow().isoformat()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@integration_bp.route('/test/incident')
def test_incident():
    """Test incident creation"""
    try:
        incident_id = integrations.incident_manager.create_incident(
            'Test Security Incident',
            'This is a test incident for integration testing',
            IncidentSeverity.MEDIUM
        )
        
        return jsonify({
            'status': 'success',
            'data': {
                'incident_id': incident_id,
                'message': 'Test incident created successfully'
            },
            'timestamp': datetime.utcnow().isoformat()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Register blueprint with Flask app
def register_integration_routes(app):
    """Register integration routes with Flask app"""
    app.register_blueprint(integration_bp)
    return app 