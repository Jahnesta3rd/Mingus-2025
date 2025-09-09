#!/usr/bin/env python3
"""
Meme Analytics API for Mingus Personal Finance App

Flask API endpoints for the meme analytics system, providing:
- Event tracking endpoints
- Dashboard data endpoints
- Report generation endpoints
- CSV export endpoints
- Alert management endpoints
"""

from flask import Flask, request, jsonify, send_file, render_template_string
from flask_cors import CORS
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import os
from pathlib import Path

# Import our analytics system
from meme_analytics_system import MemeAnalyticsSystem, AnalyticsEvent, UserDemographics

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for frontend integration

# Initialize analytics system
analytics = MemeAnalyticsSystem()

# =====================================================
# ANALYTICS EVENT TRACKING ENDPOINTS
# =====================================================

@app.route('/api/analytics/track-event', methods=['POST'])
def track_analytics_event():
    """Track an analytics event"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['user_id', 'session_id', 'meme_id', 'event_type']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Create analytics event
        event = AnalyticsEvent(
            user_id=data['user_id'],
            session_id=data['session_id'],
            meme_id=data['meme_id'],
            event_type=data['event_type'],
            time_spent_seconds=data.get('time_spent_seconds', 0),
            user_agent=request.headers.get('User-Agent', ''),
            ip_address=request.remote_addr,
            referrer=request.headers.get('Referer', ''),
            device_type=data.get('device_type', ''),
            browser=data.get('browser', ''),
            os=data.get('os', ''),
            screen_resolution=data.get('screen_resolution', ''),
            additional_data=json.dumps(data.get('additional_data', {}))
        )
        
        # Track the event
        success = analytics.track_event(event)
        
        if success:
            return jsonify({'status': 'success', 'message': 'Event tracked successfully'})
        else:
            return jsonify({'error': 'Failed to track event'}), 500
            
    except Exception as e:
        logger.error(f"Error tracking event: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/analytics/user-demographics', methods=['POST'])
def update_user_demographics():
    """Update user demographics"""
    try:
        data = request.get_json()
        
        if 'user_id' not in data:
            return jsonify({'error': 'Missing required field: user_id'}), 400
        
        # Create demographics object
        demographics = UserDemographics(
            user_id=data['user_id'],
            age_range=data.get('age_range', ''),
            gender=data.get('gender', ''),
            income_range=data.get('income_range', ''),
            education_level=data.get('education_level', ''),
            location_state=data.get('location_state', ''),
            location_country=data.get('location_country', 'US')
        )
        
        # Update demographics
        success = analytics.add_user_demographics(demographics)
        
        if success:
            return jsonify({'status': 'success', 'message': 'Demographics updated successfully'})
        else:
            return jsonify({'error': 'Failed to update demographics'}), 500
            
    except Exception as e:
        logger.error(f"Error updating demographics: {e}")
        return jsonify({'error': 'Internal server error'}), 500

# =====================================================
# DASHBOARD DATA ENDPOINTS
# =====================================================

@app.route('/api/analytics/dashboard/daily-engagement', methods=['GET'])
def get_daily_engagement():
    """Get daily engagement rates"""
    try:
        days = request.args.get('days', 30, type=int)
        data = analytics.get_daily_engagement_rates(days)
        
        if data.empty:
            return jsonify({'data': [], 'message': 'No data available'})
        
        # Convert to JSON-serializable format
        result = data.to_dict('records')
        return jsonify({'data': result, 'days': days})
        
    except Exception as e:
        logger.error(f"Error getting daily engagement: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/analytics/dashboard/category-performance', methods=['GET'])
def get_category_performance():
    """Get category performance metrics"""
    try:
        days = request.args.get('days', 30, type=int)
        data = analytics.get_category_performance(days)
        
        if data.empty:
            return jsonify({'data': [], 'message': 'No data available'})
        
        # Convert to JSON-serializable format
        result = data.to_dict('records')
        return jsonify({'data': result, 'days': days})
        
    except Exception as e:
        logger.error(f"Error getting category performance: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/analytics/dashboard/performance-metrics', methods=['GET'])
def get_performance_metrics():
    """Get overall performance metrics"""
    try:
        days = request.args.get('days', 30, type=int)
        metrics = analytics.get_performance_metrics(days)
        
        if not metrics:
            return jsonify({'data': {}, 'message': 'No data available'})
        
        return jsonify({'data': metrics, 'days': days})
        
    except Exception as e:
        logger.error(f"Error getting performance metrics: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/analytics/dashboard/user-retention', methods=['GET'])
def get_user_retention():
    """Get user retention analysis"""
    try:
        days = request.args.get('days', 30, type=int)
        data = analytics.get_user_retention_analysis(days)
        
        if not data:
            return jsonify({'data': {}, 'message': 'No data available'})
        
        return jsonify({'data': data, 'days': days})
        
    except Exception as e:
        logger.error(f"Error getting user retention: {e}")
        return jsonify({'error': 'Internal server error'}), 500

# =====================================================
# ALERT MANAGEMENT ENDPOINTS
# =====================================================

@app.route('/api/analytics/alerts', methods=['GET'])
def get_alerts():
    """Get current alerts"""
    try:
        alerts = analytics.check_alerts()
        return jsonify({'alerts': alerts, 'count': len(alerts)})
        
    except Exception as e:
        logger.error(f"Error getting alerts: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/analytics/alerts/create', methods=['POST'])
def create_alert():
    """Create a new alert"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['type', 'severity', 'title', 'description']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Create the alert
        success = analytics.create_alert(data)
        
        if success:
            return jsonify({'status': 'success', 'message': 'Alert created successfully'})
        else:
            return jsonify({'error': 'Failed to create alert'}), 500
            
    except Exception as e:
        logger.error(f"Error creating alert: {e}")
        return jsonify({'error': 'Internal server error'}), 500

# =====================================================
# REPORT GENERATION ENDPOINTS
# =====================================================

@app.route('/api/analytics/reports/generate', methods=['GET'])
def generate_report():
    """Generate analytics report"""
    try:
        days = request.args.get('days', 30, type=int)
        report = analytics.generate_report(days)
        
        return jsonify({
            'report': report,
            'days': days,
            'generated_at': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error generating report: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/analytics/reports/charts', methods=['GET'])
def generate_charts():
    """Generate dashboard charts"""
    try:
        output_dir = request.args.get('output_dir', 'analytics_charts')
        success = analytics.create_dashboard_charts(output_dir)
        
        if success:
            return jsonify({
                'status': 'success',
                'message': 'Charts generated successfully',
                'output_dir': output_dir
            })
        else:
            return jsonify({'error': 'Failed to generate charts'}), 500
            
    except Exception as e:
        logger.error(f"Error generating charts: {e}")
        return jsonify({'error': 'Internal server error'}), 500

# =====================================================
# CSV EXPORT ENDPOINTS
# =====================================================

@app.route('/api/analytics/export/daily-engagement', methods=['GET'])
def export_daily_engagement():
    """Export daily engagement data to CSV"""
    try:
        days = request.args.get('days', 30, type=int)
        data = analytics.get_daily_engagement_rates(days)
        
        if data.empty:
            return jsonify({'error': 'No data available for export'}), 404
        
        filename = f"daily_engagement_{days}days_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        filepath = Path(filename)
        
        success = analytics.export_to_csv(data, str(filepath))
        
        if success:
            return send_file(
                str(filepath),
                as_attachment=True,
                download_name=filename,
                mimetype='text/csv'
            )
        else:
            return jsonify({'error': 'Failed to export data'}), 500
            
    except Exception as e:
        logger.error(f"Error exporting daily engagement: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/analytics/export/category-performance', methods=['GET'])
def export_category_performance():
    """Export category performance data to CSV"""
    try:
        days = request.args.get('days', 30, type=int)
        data = analytics.get_category_performance(days)
        
        if data.empty:
            return jsonify({'error': 'No data available for export'}), 404
        
        filename = f"category_performance_{days}days_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        filepath = Path(filename)
        
        success = analytics.export_to_csv(data, str(filepath))
        
        if success:
            return send_file(
                str(filepath),
                as_attachment=True,
                download_name=filename,
                mimetype='text/csv'
            )
        else:
            return jsonify({'error': 'Failed to export data'}), 500
            
    except Exception as e:
        logger.error(f"Error exporting category performance: {e}")
        return jsonify({'error': 'Internal server error'}), 500

# =====================================================
# SIMPLE ADMIN DASHBOARD
# =====================================================

@app.route('/api/analytics/dashboard', methods=['GET'])
def analytics_dashboard():
    """Simple HTML dashboard for analytics"""
    
    dashboard_html = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Meme Analytics Dashboard</title>
        <style>
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                margin: 0;
                padding: 20px;
                background-color: #f5f5f5;
            }
            .container {
                max-width: 1200px;
                margin: 0 auto;
                background: white;
                border-radius: 8px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                padding: 30px;
            }
            h1 {
                color: #333;
                text-align: center;
                margin-bottom: 30px;
            }
            .metrics-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                gap: 20px;
                margin-bottom: 30px;
            }
            .metric-card {
                background: #f8f9fa;
                padding: 20px;
                border-radius: 8px;
                border-left: 4px solid #007bff;
            }
            .metric-value {
                font-size: 2em;
                font-weight: bold;
                color: #007bff;
            }
            .metric-label {
                color: #666;
                margin-top: 5px;
            }
            .section {
                margin-bottom: 30px;
            }
            .section h2 {
                color: #333;
                border-bottom: 2px solid #007bff;
                padding-bottom: 10px;
            }
            table {
                width: 100%;
                border-collapse: collapse;
                margin-top: 15px;
            }
            th, td {
                padding: 12px;
                text-align: left;
                border-bottom: 1px solid #ddd;
            }
            th {
                background-color: #f8f9fa;
                font-weight: 600;
            }
            .alert {
                padding: 15px;
                margin: 10px 0;
                border-radius: 4px;
                border-left: 4px solid;
            }
            .alert-high {
                background-color: #f8d7da;
                border-color: #dc3545;
                color: #721c24;
            }
            .alert-medium {
                background-color: #fff3cd;
                border-color: #ffc107;
                color: #856404;
            }
            .alert-low {
                background-color: #d1ecf1;
                border-color: #17a2b8;
                color: #0c5460;
            }
            .refresh-btn {
                background: #007bff;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 4px;
                cursor: pointer;
                margin-bottom: 20px;
            }
            .refresh-btn:hover {
                background: #0056b3;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🎭 Meme Analytics Dashboard</h1>
            
            <button class="refresh-btn" onclick="loadDashboard()">🔄 Refresh Data</button>
            
            <div class="section">
                <h2>📊 Key Metrics (Last 30 Days)</h2>
                <div class="metrics-grid" id="metrics-grid">
                    <!-- Metrics will be loaded here -->
                </div>
            </div>
            
            <div class="section">
                <h2>📈 Category Performance</h2>
                <table id="category-table">
                    <thead>
                        <tr>
                            <th>Category</th>
                            <th>Views</th>
                            <th>Skip Rate</th>
                            <th>Continue Rate</th>
                            <th>Unique Users</th>
                        </tr>
                    </thead>
                    <tbody>
                        <!-- Data will be loaded here -->
                    </tbody>
                </table>
            </div>
            
            <div class="section">
                <h2>⚠️ Active Alerts</h2>
                <div id="alerts-container">
                    <!-- Alerts will be loaded here -->
                </div>
            </div>
            
            <div class="section">
                <h2>📋 Quick Actions</h2>
                <p>
                    <a href="/api/analytics/export/daily-engagement" target="_blank">📥 Export Daily Engagement CSV</a> |
                    <a href="/api/analytics/export/category-performance" target="_blank">📥 Export Category Performance CSV</a> |
                    <a href="/api/analytics/reports/generate" target="_blank">📄 Generate Full Report</a>
                </p>
            </div>
        </div>
        
        <script>
            async function loadDashboard() {
                try {
                    // Load performance metrics
                    const metricsResponse = await fetch('/api/analytics/dashboard/performance-metrics');
                    const metricsData = await metricsResponse.json();
                    
                    if (metricsData.data) {
                        displayMetrics(metricsData.data);
                    }
                    
                    // Load category performance
                    const categoryResponse = await fetch('/api/analytics/dashboard/category-performance');
                    const categoryData = await categoryResponse.json();
                    
                    if (categoryData.data) {
                        displayCategoryPerformance(categoryData.data);
                    }
                    
                    // Load alerts
                    const alertsResponse = await fetch('/api/analytics/alerts');
                    const alertsData = await alertsResponse.json();
                    
                    if (alertsData.alerts) {
                        displayAlerts(alertsData.alerts);
                    }
                    
                } catch (error) {
                    console.error('Error loading dashboard:', error);
                }
            }
            
            function displayMetrics(metrics) {
                const grid = document.getElementById('metrics-grid');
                grid.innerHTML = `
                    <div class="metric-card">
                        <div class="metric-value">${metrics.total_views?.toLocaleString() || 0}</div>
                        <div class="metric-label">Total Views</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">${metrics.unique_users?.toLocaleString() || 0}</div>
                        <div class="metric-label">Unique Users</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">${metrics.skip_rate?.toFixed(1) || 0}%</div>
                        <div class="metric-label">Skip Rate</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">${metrics.continue_rate?.toFixed(1) || 0}%</div>
                        <div class="metric-label">Continue Rate</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">${metrics.avg_time_spent?.toFixed(1) || 0}s</div>
                        <div class="metric-label">Avg Time Spent</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">${metrics.total_sessions?.toLocaleString() || 0}</div>
                        <div class="metric-label">Total Sessions</div>
                    </div>
                `;
            }
            
            function displayCategoryPerformance(categories) {
                const tbody = document.querySelector('#category-table tbody');
                tbody.innerHTML = categories.map(cat => `
                    <tr>
                        <td>${cat.category}</td>
                        <td>${cat.total_views?.toLocaleString() || 0}</td>
                        <td>${cat.skip_rate?.toFixed(1) || 0}%</td>
                        <td>${cat.continue_rate?.toFixed(1) || 0}%</td>
                        <td>${cat.unique_users?.toLocaleString() || 0}</td>
                    </tr>
                `).join('');
            }
            
            function displayAlerts(alerts) {
                const container = document.getElementById('alerts-container');
                
                if (alerts.length === 0) {
                    container.innerHTML = '<p>✅ No active alerts</p>';
                    return;
                }
                
                container.innerHTML = alerts.map(alert => `
                    <div class="alert alert-${alert.severity}">
                        <strong>${alert.title}</strong><br>
                        ${alert.description}<br>
                        <small>Type: ${alert.type} | Severity: ${alert.severity}</small>
                    </div>
                `).join('');
            }
            
            // Load dashboard on page load
            loadDashboard();
        </script>
    </body>
    </html>
    """
    
    return dashboard_html

# =====================================================
# HEALTH CHECK ENDPOINT
# =====================================================

@app.route('/api/analytics/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'meme-analytics-api',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0'
    })

# =====================================================
# ERROR HANDLERS
# =====================================================

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

# =====================================================
# MAIN APPLICATION
# =====================================================

if __name__ == '__main__':
    # Create necessary directories
    Path('analytics_charts').mkdir(exist_ok=True)
    
    # Run the Flask app
    app.run(
        host='0.0.0.0',
        port=5001,
        debug=True,
        threaded=True
    )
