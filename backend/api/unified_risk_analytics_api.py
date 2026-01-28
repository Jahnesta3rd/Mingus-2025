#!/usr/bin/env python3
"""
Unified Risk Analytics API for Career Protection System

This module provides a comprehensive unified API layer that connects all risk analytics
components with the existing job recommendation system, providing seamless integration
for risk-triggered workflows.

Features:
- Core risk analytics endpoints with full tracking
- Real-time risk monitoring and alert APIs
- Risk dashboard data APIs for frontend integration
- Risk-based recommendation triggering with analytics
- A/B testing integration for risk optimization
- WebSocket integration for real-time updates
- Performance optimization and caching
"""

import asyncio
import json
import logging
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum

from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
from functools import wraps
import sqlite3

# Import existing risk analytics components
from ..analytics.risk_analytics_integration import (
    RiskAnalyticsIntegration,
    RiskAssessmentData,
    RiskRecommendationData,
    RiskOutcomeData,
    RiskEventType,
    RiskLevel
)
from ..analytics.risk_analytics_tracker import RiskAnalyticsTracker
from ..analytics.risk_ab_testing_framework import RiskABTestFramework
from ..analytics.risk_predictive_analytics import RiskPredictiveAnalytics
from ..analytics.risk_success_dashboard import RiskSuccessDashboard
from ..analytics.risk_performance_monitor import RiskPerformanceMonitor

# Import existing recommendation components
from ..utils.mingus_job_recommendation_engine import MingusJobRecommendationEngine
from ..utils.three_tier_job_selector import ThreeTierJobSelector

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create blueprint
risk_analytics_api = Blueprint('risk_analytics', __name__, url_prefix='/api/risk')

class RiskAnalyticsAPI:
    """
    Unified Risk Analytics API class that orchestrates all risk-analytics integrations.
    
    This class provides a single interface for all risk-related operations including
    assessment, monitoring, recommendations, and analytics tracking.
    """
    
    def __init__(self, db_path: str = "backend/analytics/risk_analytics.db"):
        """Initialize the unified risk analytics API"""
        self.db_path = db_path
        
        # Initialize core risk analytics components
        self.risk_analyzer = RiskAnalyticsIntegration(db_path)
        self.risk_tracker = RiskAnalyticsTracker(db_path)
        self.ab_testing = RiskABTestFramework(db_path)
        self.predictive_analytics = RiskPredictiveAnalytics(db_path)
        self.success_dashboard = RiskSuccessDashboard(db_path)
        # RiskPerformanceMonitor doesn't take db_path parameter on server
        try:
            self.performance_monitor = RiskPerformanceMonitor(db_path)
        except TypeError:
            # Fallback for server version that doesn't accept db_path
            self.performance_monitor = RiskPerformanceMonitor()
        
        # Initialize recommendation components
        self.recommendation_engine = MingusJobRecommendationEngine()
        self.three_tier_selector = ThreeTierJobSelector()
        
        # Initialize database
        self._init_database()
        
        logger.info("RiskAnalyticsAPI initialized successfully")
    
    def _init_database(self):
        """Initialize database tables for risk analytics API"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Risk assessment history table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS risk_assessment_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    overall_risk_score REAL NOT NULL,
                    ai_replacement_risk REAL,
                    layoff_risk REAL,
                    industry_risk REAL,
                    primary_risk_factor TEXT,
                    risk_triggers TEXT, -- JSON
                    assessment_type TEXT DEFAULT 'user_requested',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Risk-triggered recommendations table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS risk_triggered_recommendations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    risk_assessment_id INTEGER,
                    recommendation_id TEXT NOT NULL,
                    trigger_type TEXT NOT NULL,
                    risk_score REAL NOT NULL,
                    recommendation_tier TEXT,
                    success_probability REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (risk_assessment_id) REFERENCES risk_assessment_history (id)
                )
            ''')
            
            # Risk monitoring alerts table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS risk_monitoring_alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    alert_type TEXT NOT NULL,
                    risk_level TEXT NOT NULL,
                    message TEXT NOT NULL,
                    acknowledged BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    acknowledged_at TIMESTAMP
                )
            ''')
            
            # Risk A/B test assignments table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS risk_ab_test_assignments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    test_id TEXT NOT NULL,
                    variant TEXT NOT NULL,
                    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(user_id, test_id)
                )
            ''')
            
            # Create indexes for performance
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_risk_assessment_user_id ON risk_assessment_history(user_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_risk_assessment_created_at ON risk_assessment_history(created_at)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_risk_recommendations_user_id ON risk_triggered_recommendations(user_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_risk_alerts_user_id ON risk_monitoring_alerts(user_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_risk_alerts_acknowledged ON risk_monitoring_alerts(acknowledged)')
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Failed to initialize risk analytics database: {e}")
            raise

# Initialize the API instance
risk_api = RiskAnalyticsAPI()

# =====================================================
# AUTHENTICATION AND AUTHORIZATION DECORATORS
# =====================================================

def require_risk_auth(f):
    """Decorator for risk analytics endpoints requiring authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check if user is authenticated
        if not current_user.is_authenticated:
            return jsonify({'error': 'Authentication required'}), 401
        
        # Check if user has access to risk analytics
        if not hasattr(current_user, 'risk_analytics_access') or not current_user.risk_analytics_access:
            return jsonify({'error': 'Risk analytics access required'}), 403
        
        return f(*args, **kwargs)
    return decorated_function

def require_admin_access(f):
    """Decorator for admin-only risk analytics endpoints"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return jsonify({'error': 'Authentication required'}), 401
        
        if not hasattr(current_user, 'is_admin') or not current_user.is_admin:
            return jsonify({'error': 'Admin access required'}), 403
        
        return f(*args, **kwargs)
    return decorated_function

# =====================================================
# CORE RISK ANALYTICS ENDPOINTS
# =====================================================

@risk_analytics_api.route('/assess-and-track', methods=['POST'])
@require_risk_auth
async def assess_risk_with_full_tracking():
    """Comprehensive risk assessment with analytics tracking"""
    try:
        data = request.get_json()
        
        # Get user profile for risk assessment
        user_profile = current_user.get_profile_dict() if hasattr(current_user, 'get_profile_dict') else {}
        
        # Perform risk assessment with performance monitoring
        start_time = time.time()
        risk_analysis = await risk_api.risk_analyzer.calculate_comprehensive_risk_score(user_profile)
        assessment_time = time.time() - start_time
        
        # Track analytics for risk assessment
        await risk_api.risk_analyzer.track_risk_assessment_completed(
            user_id=current_user.id,
            risk_data=risk_analysis,
            assessment_time=assessment_time
        )
        
        # Check if recommendations should be triggered
        recommendations = None
        if risk_analysis.get('overall_risk', 0) >= 0.5:  # Medium risk threshold
            recommendations = await risk_api.recommendation_engine.trigger_proactive_recommendations(
                current_user, risk_analysis
            )
            
            # Track risk-triggered recommendations
            await risk_api.risk_analyzer.track_risk_triggered_recommendation(
                user_id=current_user.id,
                risk_data=risk_analysis,
                recommendations=recommendations
            )
        
        # Update user's risk history
        conn = sqlite3.connect(risk_api.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO risk_assessment_history 
            (user_id, overall_risk_score, ai_replacement_risk, layoff_risk, industry_risk, 
             primary_risk_factor, risk_triggers, assessment_type)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            current_user.id,
            risk_analysis.get('overall_risk', 0),
            risk_analysis.get('risk_breakdown', {}).get('ai_displacement_probability', 0),
            risk_analysis.get('risk_breakdown', {}).get('layoff_probability', 0),
            risk_analysis.get('risk_breakdown', {}).get('industry_risk_level', 0),
            risk_analysis.get('risk_triggers', [{}])[0].get('factor') if risk_analysis.get('risk_triggers') else None,
            json.dumps(risk_analysis.get('risk_triggers', [])),
            'user_requested'
        ))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'risk_analysis': risk_analysis,
            'recommendations_triggered': recommendations is not None,
            'recommendations': recommendations,
            'analytics_tracked': True,
            'assessment_performance': {
                'processing_time': assessment_time,
                'meets_targets': assessment_time < 3.0
            }
        })
        
    except Exception as e:
        logger.error(f"Risk assessment with tracking failed: {e}")
        return jsonify({'error': 'Risk assessment failed'}), 500

@risk_analytics_api.route('/dashboard/<int:user_id>', methods=['GET'])
@require_risk_auth
async def get_risk_analytics_dashboard(user_id):
    """Comprehensive risk dashboard with analytics"""
    try:
        # Verify user access
        if current_user.id != user_id and not (hasattr(current_user, 'is_admin') and current_user.is_admin):
            return jsonify({'error': 'Unauthorized'}), 403
        
        # Generate comprehensive dashboard
        dashboard_data = await risk_api.success_dashboard.generate_career_protection_report()
        
        # Add user-specific risk trends
        conn = sqlite3.connect(risk_api.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT created_at, overall_risk_score, primary_risk_factor, risk_triggers
            FROM risk_assessment_history 
            WHERE user_id = ? 
            ORDER BY created_at DESC 
            LIMIT 12
        ''', (str(user_id),))
        
        risk_trends = []
        for row in cursor.fetchall():
            risk_trends.append({
                'date': row[0],
                'risk_score': float(row[1]),
                'primary_factor': row[2],
                'triggers': json.loads(row[3]) if row[3] else []
            })
        
        # Get performance metrics
        performance_metrics = await risk_api.performance_monitor.get_user_risk_performance(user_id)
        
        # Check for active A/B tests
        active_experiments = await risk_api.ab_testing.get_user_active_experiments(user_id)
        
        conn.close()
        
        return jsonify({
            'user_id': user_id,
            'career_protection_metrics': dashboard_data,
            'risk_trends': risk_trends,
            'performance_data': performance_metrics,
            'active_experiments': active_experiments,
            'dashboard_generated_at': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Risk dashboard generation failed: {e}")
        return jsonify({'error': 'Dashboard generation failed'}), 500

@risk_analytics_api.route('/trigger-recommendations', methods=['POST'])
@require_risk_auth
async def trigger_risk_based_recommendations():
    """Trigger risk-based recommendations with tracking"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['risk_data', 'recommendation_tiers']
        if not all(field in data for field in required_fields):
            return jsonify({'error': 'Missing required fields'}), 400
        
        # Generate risk-triggered recommendations
        recommendations = await risk_api.three_tier_selector.generate_tiered_recommendations(
            risk_data=data['risk_data'],
            user_id=current_user.id,
            tiers=data.get('recommendation_tiers', ['conservative', 'optimal', 'stretch'])
        )
        
        # Track the recommendations
        await risk_api.risk_analyzer.track_risk_recommendation_triggered(
            user_id=current_user.id,
            risk_data=data['risk_data'],
            recommendations=recommendations
        )
        
        return jsonify({
            'success': True,
            'recommendations': recommendations,
            'analytics_tracked': True,
            'triggered_at': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Risk-based recommendation triggering failed: {e}")
        return jsonify({'error': 'Recommendation triggering failed'}), 500

@risk_analytics_api.route('/analytics/effectiveness', methods=['GET'])
@require_risk_auth
async def get_career_protection_effectiveness():
    """Get career protection effectiveness metrics"""
    try:
        days = request.args.get('days', 30, type=int)
        
        # Get effectiveness metrics
        effectiveness_metrics = await risk_api.success_dashboard.generate_career_protection_report()
        
        # Get prediction accuracy
        prediction_accuracy = await risk_api.risk_analyzer.get_prediction_accuracy_report()
        
        # Get user engagement metrics
        engagement_metrics = await risk_api.risk_tracker.get_user_engagement_metrics(
            user_id=current_user.id,
            days=days
        )
        
        return jsonify({
            'success': True,
            'effectiveness_metrics': effectiveness_metrics,
            'prediction_accuracy': prediction_accuracy,
            'engagement_metrics': engagement_metrics,
            'analysis_period_days': days
        })
        
    except Exception as e:
        logger.error(f"Effectiveness metrics retrieval failed: {e}")
        return jsonify({'error': 'Effectiveness metrics retrieval failed'}), 500

@risk_analytics_api.route('/outcome/track', methods=['POST'])
@require_risk_auth
async def track_risk_intervention_outcome():
    """Track outcomes from risk-based interventions"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['outcome_type', 'original_risk_score', 'intervention_date']
        if not all(field in data for field in required_fields):
            return jsonify({'error': 'Missing required fields'}), 400
        
        # Track success story
        success_story = await risk_api.success_dashboard.track_user_success_story(
            user_id=current_user.id,
            success_type=data['outcome_type'],
            outcome_data=data
        )
        
        # Update risk prediction accuracy
        if 'actual_outcome' in data:
            await risk_api.risk_analyzer.measure_risk_prediction_accuracy(
                user_id=current_user.id,
                predicted_risk=data['original_risk_score'],
                actual_outcome=data['actual_outcome']
            )
        
        # Track in A/B testing if user was in experiment
        if 'experiment_variant' in data:
            await risk_api.ab_testing.track_experiment_outcome(
                user_id=current_user.id,
                experiment_type='risk_intervention',
                variant=data['experiment_variant'],
                outcome=data['outcome_type']
            )
        
        return jsonify({
            'success': True,
            'outcome_tracked': True,
            'success_story_id': success_story.get('id'),
            'analytics_updated': True
        })
        
    except Exception as e:
        logger.error(f"Risk outcome tracking failed: {e}")
        return jsonify({'error': 'Outcome tracking failed'}), 500

# =====================================================
# REAL-TIME RISK MONITORING ENDPOINTS
# =====================================================

@risk_analytics_api.route('/monitor/status', methods=['GET'])
@require_risk_auth
async def get_risk_system_health():
    """Real-time risk system health monitoring"""
    try:
        # Get system health metrics
        health_metrics = await risk_api.performance_monitor.get_risk_system_health()
        
        # Get active risk alerts
        conn = sqlite3.connect(risk_api.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT COUNT(*) FROM risk_monitoring_alerts 
            WHERE user_id = ? AND acknowledged = FALSE
        ''', (current_user.id,))
        
        active_alerts = cursor.fetchone()[0]
        conn.close()
        
        return jsonify({
            'success': True,
            'system_health': health_metrics,
            'active_alerts': active_alerts,
            'monitoring_status': 'active',
            'last_updated': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Risk system health monitoring failed: {e}")
        return jsonify({'error': 'System health monitoring failed'}), 500

@risk_analytics_api.route('/alert/trigger', methods=['POST'])
@require_risk_auth
async def trigger_risk_alert():
    """Trigger risk alerts with analytics tracking"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['alert_type', 'risk_level', 'message']
        if not all(field in data for field in required_fields):
            return jsonify({'error': 'Missing required fields'}), 400
        
        # Create risk alert
        conn = sqlite3.connect(risk_api.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO risk_monitoring_alerts 
            (user_id, alert_type, risk_level, message)
            VALUES (?, ?, ?, ?)
        ''', (
            current_user.id,
            data['alert_type'],
            data['risk_level'],
            data['message']
        ))
        
        conn.commit()
        conn.close()
        
        # Track alert analytics
        await risk_api.risk_analyzer.track_risk_alert_sent(
            user_id=current_user.id,
            alert_type=data['alert_type'],
            risk_level=data['risk_level']
        )
        
        return jsonify({
            'success': True,
            'alert_triggered': True,
            'alert_id': cursor.lastrowid,
            'analytics_tracked': True
        })
        
    except Exception as e:
        logger.error(f"Risk alert triggering failed: {e}")
        return jsonify({'error': 'Alert triggering failed'}), 500

@risk_analytics_api.route('/trends/live', methods=['GET'])
@require_risk_auth
async def get_live_risk_trends():
    """Live risk trend data for dashboard"""
    try:
        # Get live risk trends
        live_trends = await risk_api.predictive_analytics.get_live_risk_trends()
        
        # Get user-specific trend data
        user_trends = await risk_api.risk_tracker.get_user_risk_trends(
            user_id=current_user.id,
            days=7
        )
        
        return jsonify({
            'success': True,
            'live_trends': live_trends,
            'user_trends': user_trends,
            'generated_at': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Live risk trends retrieval failed: {e}")
        return jsonify({'error': 'Live trends retrieval failed'}), 500

@risk_analytics_api.route('/predictions/active', methods=['GET'])
@require_risk_auth
async def get_active_risk_predictions():
    """Active risk predictions requiring attention"""
    try:
        # Get active predictions
        active_predictions = await risk_api.predictive_analytics.get_active_predictions(
            user_id=current_user.id
        )
        
        return jsonify({
            'success': True,
            'active_predictions': active_predictions,
            'prediction_count': len(active_predictions),
            'generated_at': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Active risk predictions retrieval failed: {e}")
        return jsonify({'error': 'Active predictions retrieval failed'}), 500

# =====================================================
# RISK A/B TESTING INTEGRATION ENDPOINTS
# =====================================================

@risk_analytics_api.route('/experiments/active', methods=['GET'])
@require_risk_auth
async def get_active_risk_experiments():
    """Active risk-related A/B tests"""
    try:
        # Get active experiments
        active_experiments = await risk_api.ab_testing.get_user_active_experiments(
            user_id=current_user.id
        )
        
        return jsonify({
            'success': True,
            'active_experiments': active_experiments,
            'experiment_count': len(active_experiments)
        })
        
    except Exception as e:
        logger.error(f"Active risk experiments retrieval failed: {e}")
        return jsonify({'error': 'Active experiments retrieval failed'}), 500

@risk_analytics_api.route('/experiments/assign', methods=['POST'])
@require_risk_auth
async def assign_user_to_risk_experiment():
    """Assign user to risk experiment variant"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['test_id', 'variant']
        if not all(field in data for field in required_fields):
            return jsonify({'error': 'Missing required fields'}), 400
        
        # Assign user to experiment
        assignment = await risk_api.ab_testing.assign_user_to_experiment(
            user_id=current_user.id,
            test_id=data['test_id'],
            variant=data['variant']
        )
        
        return jsonify({
            'success': True,
            'assignment_created': assignment,
            'test_id': data['test_id'],
            'variant': data['variant']
        })
        
    except Exception as e:
        logger.error(f"Risk experiment assignment failed: {e}")
        return jsonify({'error': 'Experiment assignment failed'}), 500

@risk_analytics_api.route('/experiments/outcome', methods=['POST'])
@require_risk_auth
async def track_risk_experiment_outcome():
    """Track experiment outcome for risk tests"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['test_id', 'outcome_type', 'outcome_data']
        if not all(field in data for field in required_fields):
            return jsonify({'error': 'Missing required fields'}), 400
        
        # Track experiment outcome
        outcome_tracked = await risk_api.ab_testing.track_experiment_outcome(
            user_id=current_user.id,
            test_id=data['test_id'],
            outcome_type=data['outcome_type'],
            outcome_data=data['outcome_data']
        )
        
        return jsonify({
            'success': True,
            'outcome_tracked': outcome_tracked,
            'test_id': data['test_id']
        })
        
    except Exception as e:
        logger.error(f"Risk experiment outcome tracking failed: {e}")
        return jsonify({'error': 'Experiment outcome tracking failed'}), 500

# =====================================================
# ADMIN ENDPOINTS
# =====================================================

@risk_analytics_api.route('/analytics/admin/comprehensive', methods=['GET'])
@require_admin_access
async def get_comprehensive_risk_analytics():
    """Admin endpoint for comprehensive risk analytics"""
    try:
        # Generate comprehensive analytics report
        analytics_report = {
            'career_protection_effectiveness': await risk_api.success_dashboard.generate_career_protection_report(),
            'system_performance': await risk_api.performance_monitor.get_comprehensive_performance_report(),
            'ab_test_results': await risk_api.ab_testing.get_all_active_test_results(),
            'prediction_accuracy': await risk_api.risk_analyzer.get_prediction_accuracy_report(),
            'roi_analysis': await risk_api.success_dashboard.generate_roi_analysis(),
            'user_success_stories': await risk_api.success_dashboard.get_recent_success_stories(),
            'system_health': await risk_api.performance_monitor.get_risk_system_health()
        }
        
        return jsonify({
            'success': True,
            'comprehensive_analytics': analytics_report,
            'report_generated_at': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Comprehensive analytics generation failed: {e}")
        return jsonify({'error': 'Analytics generation failed'}), 500

# =====================================================
# HEALTH CHECK ENDPOINT
# =====================================================

@risk_analytics_api.route('/dashboard-state', methods=['GET', 'OPTIONS'])
def get_dashboard_state():
    """Get dashboard state for career protection dashboard"""
    if request.method == 'OPTIONS':
        return jsonify({}), 200
    
    try:
        # Return default dashboard state
        # In production, this would fetch actual user risk data
        return jsonify({
            'current_risk_level': 'watchful',
            'recommendations_unlocked': True
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting dashboard state: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@risk_analytics_api.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for risk analytics API"""
    try:
        return jsonify({
            'status': 'healthy',
            'service': 'unified_risk_analytics_api',
            'timestamp': datetime.utcnow().isoformat(),
            'version': '1.0.0',
            'components': {
                'risk_analyzer': 'active',
                'risk_tracker': 'active',
                'ab_testing': 'active',
                'predictive_analytics': 'active',
                'success_dashboard': 'active',
                'performance_monitor': 'active'
            }
        })
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 500
