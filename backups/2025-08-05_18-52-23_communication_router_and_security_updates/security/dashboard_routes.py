from flask import Blueprint, jsonify, render_template, request, send_file
from security.dashboard import SecurityDashboard, get_dashboard_json, export_dashboard_report
import json
from datetime import datetime
import io

# Create Blueprint for dashboard routes
dashboard_bp = Blueprint('security_dashboard', __name__, url_prefix='/security/dashboard')

# Initialize dashboard
dashboard = SecurityDashboard()

@dashboard_bp.route('/')
def dashboard_home():
    """Main dashboard page"""
    try:
        dashboard_data = dashboard.generate_dashboard()
        return render_template('security_dashboard.html', dashboard_data=dashboard_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@dashboard_bp.route('/api/metrics')
def get_metrics():
    """Get security metrics as JSON"""
    try:
        dashboard_data = dashboard.generate_dashboard()
        return jsonify({
            'metrics': {
                'total_events': dashboard_data.metrics.total_events,
                'critical_events': dashboard_data.metrics.critical_events,
                'high_risk_events': dashboard_data.metrics.high_risk_events,
                'medium_risk_events': dashboard_data.metrics.medium_risk_events,
                'low_risk_events': dashboard_data.metrics.low_risk_events,
                'active_alerts': dashboard_data.metrics.active_alerts,
                'failed_login_attempts': dashboard_data.metrics.failed_login_attempts,
                'suspicious_activities': dashboard_data.metrics.suspicious_activities,
                'compliance_score': dashboard_data.metrics.compliance_score,
                'system_health_score': dashboard_data.metrics.system_health_score,
                'average_user_risk_score': dashboard_data.metrics.average_user_risk_score,
                'threat_level': dashboard_data.metrics.threat_level.value,
                'security_status': dashboard_data.metrics.security_status.value
            },
            'timestamp': datetime.utcnow().isoformat()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@dashboard_bp.route('/api/recent-events')
def get_recent_events():
    """Get recent security events"""
    try:
        limit = request.args.get('limit', 20, type=int)
        dashboard_data = dashboard.generate_dashboard()
        return jsonify({
            'recent_events': dashboard_data.recent_events[:limit],
            'total_events': len(dashboard_data.recent_events)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@dashboard_bp.route('/api/threat-indicators')
def get_threat_indicators():
    """Get current threat indicators"""
    try:
        dashboard_data = dashboard.generate_dashboard()
        return jsonify({
            'threat_indicators': dashboard_data.threat_indicators,
            'total_threats': len(dashboard_data.threat_indicators)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@dashboard_bp.route('/api/compliance')
def get_compliance_metrics():
    """Get compliance metrics"""
    try:
        dashboard_data = dashboard.generate_dashboard()
        return jsonify({
            'compliance_metrics': dashboard_data.compliance_metrics,
            'overall_score': dashboard_data.compliance_metrics.get('overall_score', 0.0)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@dashboard_bp.route('/api/user-risk-scores')
def get_user_risk_scores():
    """Get user risk scores"""
    try:
        limit = request.args.get('limit', 50, type=int)
        dashboard_data = dashboard.generate_dashboard()
        return jsonify({
            'user_risk_scores': dashboard_data.user_risk_scores[:limit],
            'total_users': len(dashboard_data.user_risk_scores)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@dashboard_bp.route('/api/system-health')
def get_system_health():
    """Get system health metrics"""
    try:
        dashboard_data = dashboard.generate_dashboard()
        return jsonify({
            'system_health': dashboard_data.system_health,
            'overall_health_score': dashboard_data.system_health.get('overall_health_score', 0.0)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@dashboard_bp.route('/api/charts/<chart_type>')
def get_chart(chart_type):
    """Get specific chart as base64 image"""
    try:
        dashboard_data = dashboard.generate_dashboard()
        chart_data = dashboard_data.charts.get(chart_type, '')
        
        if not chart_data:
            return jsonify({'error': 'Chart not found'}), 404
        
        return jsonify({
            'chart_type': chart_type,
            'chart_data': chart_data,
            'timestamp': datetime.utcnow().isoformat()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@dashboard_bp.route('/api/export')
def export_dashboard():
    """Export dashboard data"""
    try:
        format_type = request.args.get('format', 'json')
        if format_type not in ['json', 'html']:
            return jsonify({'error': 'Unsupported format'}), 400
        
        if format_type == 'json':
            dashboard_json = get_dashboard_json(dashboard)
            return jsonify(json.loads(dashboard_json))
        else:
            html_content = export_dashboard_report(dashboard, 'html')
            return html_content, 200, {'Content-Type': 'text/html'}
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@dashboard_bp.route('/api/export/download')
def download_dashboard():
    """Download dashboard report"""
    try:
        format_type = request.args.get('format', 'json')
        if format_type not in ['json', 'html']:
            return jsonify({'error': 'Unsupported format'}), 400
        
        if format_type == 'json':
            dashboard_json = get_dashboard_json(dashboard)
            filename = f"security_dashboard_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
            return send_file(
                io.BytesIO(dashboard_json.encode()),
                mimetype='application/json',
                as_attachment=True,
                download_name=filename
            )
        else:
            html_content = export_dashboard_report(dashboard, 'html')
            filename = f"security_dashboard_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.html"
            return send_file(
                io.BytesIO(html_content.encode()),
                mimetype='text/html',
                as_attachment=True,
                download_name=filename
            )
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@dashboard_bp.route('/api/refresh')
def refresh_dashboard():
    """Refresh dashboard data"""
    try:
        # Force refresh by regenerating dashboard
        dashboard_data = dashboard.generate_dashboard()
        return jsonify({
            'status': 'success',
            'message': 'Dashboard refreshed successfully',
            'timestamp': datetime.utcnow().isoformat()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@dashboard_bp.route('/api/status')
def dashboard_status():
    """Get dashboard status"""
    try:
        return jsonify({
            'status': 'operational',
            'last_update': datetime.utcnow().isoformat(),
            'database_connected': True,
            'charts_available': len(dashboard.generate_dashboard().charts)
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e),
            'last_update': datetime.utcnow().isoformat()
        }), 500

# Real-time dashboard updates (WebSocket support)
@dashboard_bp.route('/api/stream')
def stream_dashboard():
    """Stream real-time dashboard updates"""
    try:
        # This would typically use WebSockets or Server-Sent Events
        # For now, return current data
        dashboard_data = dashboard.generate_dashboard()
        return jsonify({
            'type': 'dashboard_update',
            'data': {
                'metrics': {
                    'total_events': dashboard_data.metrics.total_events,
                    'active_alerts': dashboard_data.metrics.active_alerts,
                    'threat_level': dashboard_data.metrics.threat_level.value,
                    'security_status': dashboard_data.metrics.security_status.value
                },
                'timestamp': datetime.utcnow().isoformat()
            }
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Dashboard configuration
@dashboard_bp.route('/api/config')
def get_dashboard_config():
    """Get dashboard configuration"""
    try:
        return jsonify({
            'chart_cache_duration': dashboard.cache_duration,
            'database_path': dashboard.db_path,
            'supported_formats': ['json', 'html'],
            'available_charts': [
                'event_distribution',
                'threat_trends',
                'user_risk_distribution',
                'compliance_metrics',
                'system_health',
                'geographic_threats'
            ]
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Health check endpoint
@dashboard_bp.route('/health')
def health_check():
    """Health check for dashboard service"""
    try:
        # Test dashboard generation
        dashboard.generate_dashboard()
        return jsonify({
            'status': 'healthy',
            'service': 'security_dashboard',
            'timestamp': datetime.utcnow().isoformat()
        })
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'service': 'security_dashboard',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 500

# Register blueprint with Flask app
def register_dashboard_routes(app):
    """Register dashboard routes with Flask app"""
    app.register_blueprint(dashboard_bp)
    return app 