#!/usr/bin/env python3
"""
Content Optimization API Endpoints
REST API endpoints for A/B testing and content optimization
"""

import logging
from datetime import datetime, date
from typing import Dict, List, Optional, Any
from flask import Blueprint, request, jsonify, current_app
from sqlalchemy import and_, or_, desc
from sqlalchemy.orm import sessionmaker

from backend.models.database import db
from backend.models.content_optimization_models import (
    ABTest, UserAssignment, TestInteraction, VariantMetric, 
    TestResult, UserSegment, ContentTemplate, ContentVariation,
    PerformanceThreshold, OptimizationRule, ContentPerformance,
    AnalyticsEvent
)
from backend.services.content_optimization_service import (
    ContentOptimizationService, TestType, TestStatus, VariantType, MetricType
)
from backend.services.daily_outlook_content_service import DailyOutlookContentService
from backend.auth.decorators import require_auth, require_admin

logger = logging.getLogger(__name__)

# Create blueprint
content_optimization_bp = Blueprint('content_optimization', __name__, url_prefix='/api/content-optimization')

# Initialize services
content_optimization_service = ContentOptimizationService()
daily_outlook_service = DailyOutlookContentService()

@content_optimization_bp.route('/ab-tests', methods=['GET'])
@require_auth
def get_ab_tests():
    """Get all A/B tests"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        status = request.args.get('status')
        
        query = ABTest.query
        
        if status:
            query = query.filter(ABTest.status == status)
        
        tests = query.order_by(desc(ABTest.created_at)).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'success': True,
            'tests': [test.to_dict() for test in tests.items],
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': tests.total,
                'pages': tests.pages
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting A/B tests: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@content_optimization_bp.route('/ab-tests', methods=['POST'])
@require_admin
def create_ab_test():
    """Create a new A/B test"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['test_name', 'test_type', 'description', 'variants', 'target_segments', 'success_metrics']
        for field in required_fields:
            if field not in data:
                return jsonify({'success': False, 'error': f'Missing required field: {field}'}), 400
        
        # Create test using service
        test_id = content_optimization_service.create_ab_test(
            test_name=data['test_name'],
            test_type=TestType(data['test_type']),
            description=data['description'],
            variants=data['variants'],
            target_segments=data['target_segments'],
            success_metrics=[MetricType(m) for m in data['success_metrics']],
            duration_days=data.get('duration_days', 14),
            traffic_allocation=data.get('traffic_allocation', 0.5)
        )
        
        return jsonify({
            'success': True,
            'test_id': test_id,
            'message': 'A/B test created successfully'
        })
        
    except Exception as e:
        logger.error(f"Error creating A/B test: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@content_optimization_bp.route('/ab-tests/<test_id>', methods=['GET'])
@require_auth
def get_ab_test(test_id):
    """Get specific A/B test details"""
    try:
        test = ABTest.query.filter_by(test_id=test_id).first()
        if not test:
            return jsonify({'success': False, 'error': 'Test not found'}), 404
        
        return jsonify({
            'success': True,
            'test': test.to_dict()
        })
        
    except Exception as e:
        logger.error(f"Error getting A/B test {test_id}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@content_optimization_bp.route('/ab-tests/<test_id>/start', methods=['POST'])
@require_admin
def start_ab_test(test_id):
    """Start an A/B test"""
    try:
        success = content_optimization_service.start_ab_test(test_id)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'A/B test started successfully'
            })
        else:
            return jsonify({'success': False, 'error': 'Failed to start test'}), 500
            
    except Exception as e:
        logger.error(f"Error starting A/B test {test_id}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@content_optimization_bp.route('/ab-tests/<test_id>/pause', methods=['POST'])
@require_admin
def pause_ab_test(test_id):
    """Pause an A/B test"""
    try:
        test = ABTest.query.filter_by(test_id=test_id).first()
        if not test:
            return jsonify({'success': False, 'error': 'Test not found'}), 404
        
        test.status = TestStatus.PAUSED.value
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'A/B test paused successfully'
        })
        
    except Exception as e:
        logger.error(f"Error pausing A/B test {test_id}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@content_optimization_bp.route('/ab-tests/<test_id>/end', methods=['POST'])
@require_admin
def end_ab_test(test_id):
    """End an A/B test"""
    try:
        test = ABTest.query.filter_by(test_id=test_id).first()
        if not test:
            return jsonify({'success': False, 'error': 'Test not found'}), 404
        
        test.status = TestStatus.COMPLETED.value
        test.ended_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'A/B test ended successfully'
        })
        
    except Exception as e:
        logger.error(f"Error ending A/B test {test_id}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@content_optimization_bp.route('/ab-tests/<test_id>/results', methods=['GET'])
@require_auth
def get_ab_test_results(test_id):
    """Get A/B test results with statistical analysis"""
    try:
        test_result = content_optimization_service.get_test_results(test_id)
        
        if not test_result:
            return jsonify({'success': False, 'error': 'Test results not found'}), 404
        
        return jsonify({
            'success': True,
            'results': {
                'test_id': test_result.test_id,
                'winner_variant': test_result.winner_variant,
                'is_statistically_significant': test_result.is_statistically_significant,
                'confidence_level': test_result.confidence_level,
                'effect_size': test_result.effect_size,
                'recommendations': test_result.recommendations,
                'metrics': [
                    {
                        'variant_id': metric.variant_id,
                        'users_exposed': metric.users_exposed,
                        'users_engaged': metric.users_engaged,
                        'conversions': metric.conversions,
                        'revenue_impact': metric.revenue_impact,
                        'engagement_rate': metric.engagement_rate,
                        'conversion_rate': metric.conversion_rate,
                        'statistical_significance': metric.statistical_significance,
                        'confidence_interval': metric.confidence_interval,
                        'p_value': metric.p_value
                    }
                    for metric in test_result.metrics
                ]
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting A/B test results {test_id}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@content_optimization_bp.route('/ab-tests/<test_id>/dashboard', methods=['GET'])
@require_auth
def get_ab_test_dashboard(test_id):
    """Get comprehensive test performance dashboard"""
    try:
        dashboard_data = content_optimization_service.get_test_performance_dashboard(test_id)
        
        return jsonify({
            'success': True,
            'dashboard': dashboard_data
        })
        
    except Exception as e:
        logger.error(f"Error getting A/B test dashboard {test_id}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@content_optimization_bp.route('/ab-tests/<test_id>/assign-user', methods=['POST'])
@require_auth
def assign_user_to_test(test_id):
    """Assign current user to a test variant"""
    try:
        user_id = request.json.get('user_id') or request.user.id
        
        variant_id = content_optimization_service.assign_user_to_variant(user_id, test_id)
        
        if variant_id:
            return jsonify({
                'success': True,
                'variant_id': variant_id,
                'message': 'User assigned to test variant'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'User not eligible for this test'
            })
            
    except Exception as e:
        logger.error(f"Error assigning user to test {test_id}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@content_optimization_bp.route('/ab-tests/<test_id>/track-interaction', methods=['POST'])
@require_auth
def track_test_interaction(test_id):
    """Track user interaction with test content"""
    try:
        data = request.get_json()
        user_id = data.get('user_id') or request.user.id
        interaction_type = data.get('interaction_type')
        interaction_data = data.get('interaction_data', {})
        
        success = content_optimization_service.track_user_interaction(
            user_id, test_id, interaction_type, interaction_data
        )
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Interaction tracked successfully'
            })
        else:
            return jsonify({'success': False, 'error': 'Failed to track interaction'}), 500
            
    except Exception as e:
        logger.error(f"Error tracking interaction for test {test_id}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@content_optimization_bp.route('/user-segments', methods=['GET'])
@require_auth
def get_user_segments():
    """Get available user segments"""
    try:
        segments = content_optimization_service.create_user_segments()
        
        return jsonify({
            'success': True,
            'segments': [
                {
                    'segment_id': segment.segment_id,
                    'segment_name': segment.segment_name,
                    'criteria': segment.criteria,
                    'description': segment.description,
                    'user_count': segment.user_count
                }
                for segment in segments
            ]
        })
        
    except Exception as e:
        logger.error(f"Error getting user segments: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@content_optimization_bp.route('/content-variations', methods=['POST'])
@require_admin
def create_content_variations():
    """Create content variations for A/B testing"""
    try:
        data = request.get_json()
        base_content = data.get('base_content')
        variation_type = TestType(data.get('variation_type'))
        num_variations = data.get('num_variations', 3)
        
        variations = content_optimization_service.create_content_variations(
            base_content, variation_type, num_variations
        )
        
        return jsonify({
            'success': True,
            'variations': [
                {
                    'variant_id': v.variant_id,
                    'variant_name': v.variant_name,
                    'variant_type': v.variant_type.value,
                    'content_config': v.content_config,
                    'weight': v.weight,
                    'is_control': v.is_control
                }
                for v in variations
            ]
        })
        
    except Exception as e:
        logger.error(f"Error creating content variations: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@content_optimization_bp.route('/optimize-content', methods=['POST'])
@require_admin
def optimize_content():
    """Apply winning configuration from completed tests"""
    try:
        data = request.get_json()
        test_id = data.get('test_id')
        
        success = content_optimization_service.optimize_content_based_on_results(test_id)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Content optimized based on test results'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'No significant results to apply'
            })
            
    except Exception as e:
        logger.error(f"Error optimizing content: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@content_optimization_bp.route('/analytics/events', methods=['POST'])
@require_auth
def track_analytics_event():
    """Track analytics events for A/B testing"""
    try:
        data = request.get_json()
        user_id = data.get('user_id') or request.user.id
        test_id = data.get('test_id')
        variant_id = data.get('variant_id')
        event_type = data.get('event_type')
        event_data = data.get('event_data', {})
        session_id = data.get('session_id')
        
        # Create analytics event
        event = AnalyticsEvent(
            user_id=user_id,
            test_id=test_id,
            variant_id=variant_id,
            event_type=event_type,
            event_data=event_data,
            session_id=session_id
        )
        
        db.session.add(event)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Analytics event tracked successfully'
        })
        
    except Exception as e:
        logger.error(f"Error tracking analytics event: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@content_optimization_bp.route('/analytics/performance', methods=['GET'])
@require_auth
def get_performance_analytics():
    """Get performance analytics for content optimization"""
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        test_id = request.args.get('test_id')
        
        # Build query
        query = ContentPerformance.query
        
        if start_date:
            query = query.filter(ContentPerformance.date >= datetime.fromisoformat(start_date))
        if end_date:
            query = query.filter(ContentPerformance.date <= datetime.fromisoformat(end_date))
        if test_id:
            query = query.filter(ContentPerformance.test_id == test_id)
        
        performances = query.order_by(desc(ContentPerformance.date)).all()
        
        return jsonify({
            'success': True,
            'performances': [
                {
                    'content_id': p.content_id,
                    'content_type': p.content_type,
                    'user_id': p.user_id,
                    'variant_id': p.variant_id,
                    'test_id': p.test_id,
                    'engagement_score': p.engagement_score,
                    'conversion_rate': p.conversion_rate,
                    'time_spent': p.time_spent,
                    'click_through_rate': p.click_through_rate,
                    'revenue_impact': p.revenue_impact,
                    'date': p.date.isoformat()
                }
                for p in performances
            ]
        })
        
    except Exception as e:
        logger.error(f"Error getting performance analytics: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@content_optimization_bp.route('/thresholds', methods=['GET'])
@require_auth
def get_performance_thresholds():
    """Get performance thresholds for automated optimization"""
    try:
        thresholds = PerformanceThreshold.query.filter_by(is_active=True).all()
        
        return jsonify({
            'success': True,
            'thresholds': [
                {
                    'id': t.id,
                    'threshold_name': t.threshold_name,
                    'metric_type': t.metric_type,
                    'threshold_value': t.threshold_value,
                    'comparison_operator': t.comparison_operator,
                    'action_type': t.action_type
                }
                for t in thresholds
            ]
        })
        
    except Exception as e:
        logger.error(f"Error getting performance thresholds: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@content_optimization_bp.route('/thresholds', methods=['POST'])
@require_admin
def create_performance_threshold():
    """Create a new performance threshold"""
    try:
        data = request.get_json()
        
        threshold = PerformanceThreshold(
            threshold_name=data['threshold_name'],
            metric_type=data['metric_type'],
            threshold_value=data['threshold_value'],
            comparison_operator=data['comparison_operator'],
            action_type=data['action_type']
        )
        
        db.session.add(threshold)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Performance threshold created successfully'
        })
        
    except Exception as e:
        logger.error(f"Error creating performance threshold: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@content_optimization_bp.route('/optimization-rules', methods=['GET'])
@require_auth
def get_optimization_rules():
    """Get automated optimization rules"""
    try:
        rules = OptimizationRule.query.filter_by(is_active=True).all()
        
        return jsonify({
            'success': True,
            'rules': [
                {
                    'id': r.id,
                    'rule_name': r.rule_name,
                    'rule_type': r.rule_type,
                    'conditions': r.conditions,
                    'actions': r.actions,
                    'priority': r.priority
                }
                for r in rules
            ]
        })
        
    except Exception as e:
        logger.error(f"Error getting optimization rules: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@content_optimization_bp.route('/optimization-rules', methods=['POST'])
@require_admin
def create_optimization_rule():
    """Create a new optimization rule"""
    try:
        data = request.get_json()
        
        rule = OptimizationRule(
            rule_name=data['rule_name'],
            rule_type=data['rule_type'],
            conditions=data['conditions'],
            actions=data['actions'],
            priority=data.get('priority', 1)
        )
        
        db.session.add(rule)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Optimization rule created successfully'
        })
        
    except Exception as e:
        logger.error(f"Error creating optimization rule: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# Add methods to models for serialization
def add_model_methods():
    """Add to_dict methods to models"""
    
    def ab_test_to_dict(self):
        return {
            'test_id': self.test_id,
            'test_name': self.test_name,
            'test_type': self.test_type,
            'description': self.description,
            'status': self.status,
            'variants': self.variants,
            'target_segments': self.target_segments,
            'success_metrics': self.success_metrics,
            'duration_days': self.duration_days,
            'traffic_allocation': self.traffic_allocation,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'ended_at': self.ended_at.isoformat() if self.ended_at else None
        }
    
    ABTest.to_dict = ab_test_to_dict
