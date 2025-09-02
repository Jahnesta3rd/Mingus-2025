"""
Analytics API Routes for AI Calculator
API endpoints for tracking events, dashboard data, and business intelligence.
"""

from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta
import logging

from backend.analytics.ai_calculator_analytics import ai_calculator_analytics, EventType, RiskLevel
from backend.analytics.ai_calculator_dashboard import ai_calculator_dashboard
from backend.analytics.ai_calculator_ab_testing import ai_calculator_ab_testing
from backend.analytics.ai_calculator_performance import ai_calculator_performance
from backend.analytics.ai_calculator_business_intelligence import ai_calculator_bi
from backend.utils.auth import require_auth
from backend.utils.validation import validate_json_schema

logger = logging.getLogger(__name__)

analytics_bp = Blueprint('analytics', __name__, url_prefix='/api/analytics')

# Event tracking schema
EVENT_SCHEMA = {
    "type": "object",
    "properties": {
        "event_type": {"type": "string", "enum": [
            "ai_calculator_opened",
            "calculator_step_completed", 
            "assessment_submitted",
            "conversion_offer_viewed",
            "paid_upgrade_clicked",
            "calculator_error",
            "performance_metric"
        ]},
        "session_id": {"type": "string"},
        "timestamp": {"type": "string", "format": "date-time"},
        "source": {"type": "string"},
        "medium": {"type": "string"},
        "campaign": {"type": "string"},
        "step_number": {"type": "integer"},
        "time_on_step": {"type": "number"},
        "job_title": {"type": "string"},
        "industry": {"type": "string"},
        "risk_level": {"type": "string", "enum": ["low", "medium", "high", "critical"]},
        "assessment_completion_time": {"type": "number"},
        "error_message": {"type": "string"},
        "performance_metric": {"type": "string"},
        "metric_value": {"type": "number"}
    },
    "required": ["event_type", "session_id", "timestamp"]
}

@analytics_bp.route('/event', methods=['POST'])
def track_event():
    """Track analytics event"""
    try:
        # Validate request data
        if not validate_json_schema(request.json, EVENT_SCHEMA):
            return jsonify({'error': 'Invalid event data'}), 400
        
        event_data = request.json
        
        # Route to appropriate tracking function based on event type
        event_type = event_data['event_type']
        session_id = event_data['session_id']
        
        if event_type == 'ai_calculator_opened':
            ai_calculator_analytics.track_calculator_opened(
                session_id=session_id,
                source=event_data.get('source', 'direct'),
                medium=event_data.get('medium', 'none'),
                campaign=event_data.get('campaign', 'none')
            )
        
        elif event_type == 'calculator_step_completed':
            ai_calculator_analytics.track_step_completed(
                session_id=session_id,
                step_number=event_data['step_number'],
                time_on_step=event_data['time_on_step']
            )
        
        elif event_type == 'assessment_submitted':
            ai_calculator_analytics.track_assessment_submitted(
                session_id=session_id,
                job_title=event_data['job_title'],
                industry=event_data['industry'],
                risk_level=RiskLevel(event_data['risk_level']),
                assessment_completion_time=event_data['assessment_completion_time']
            )
        
        elif event_type == 'conversion_offer_viewed':
            ai_calculator_analytics.track_conversion_offer_viewed(
                session_id=session_id,
                risk_level=RiskLevel(event_data['risk_level']),
                time_to_view=event_data.get('time_to_view', 0)
            )
        
        elif event_type == 'paid_upgrade_clicked':
            ai_calculator_analytics.track_paid_upgrade_clicked(
                session_id=session_id,
                risk_level=RiskLevel(event_data['risk_level']),
                assessment_completion_time=event_data.get('assessment_completion_time', 0)
            )
        
        elif event_type == 'calculator_error':
            ai_calculator_analytics.track_error(
                error_message=event_data['error_message'],
                session_id=session_id,
                error_type=event_data.get('error_type', 'unknown')
            )
        
        elif event_type == 'performance_metric':
            ai_calculator_analytics.track_performance_metric(
                metric_name=event_data['performance_metric'],
                metric_value=event_data['metric_value'],
                session_id=session_id
            )
        
        return jsonify({'status': 'success'}), 200
        
    except Exception as e:
        logger.error(f"Error tracking event: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@analytics_bp.route('/dashboard/funnel', methods=['GET'])
@require_auth
def get_funnel_data():
    """Get calculator funnel data"""
    try:
        # Get date range from query parameters
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')
        
        if not start_date_str or not end_date_str:
            # Default to last 30 days
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=30)
        else:
            start_date = datetime.fromisoformat(start_date_str)
            end_date = datetime.fromisoformat(end_date_str)
        
        # Get funnel data
        funnel_data = ai_calculator_dashboard.get_calculator_funnel(start_date, end_date)
        
        return jsonify({
            'funnel_data': [{
                'step_number': step.step_number,
                'step_name': step.step_name,
                'total_visitors': step.total_visitors,
                'step_completions': step.step_completions,
                'conversion_rate': step.conversion_rate,
                'dropoff_rate': step.dropoff_rate,
                'avg_time_on_step': step.avg_time_on_step
            } for step in funnel_data]
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting funnel data: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@analytics_bp.route('/dashboard/conversions', methods=['GET'])
@require_auth
def get_conversion_data():
    """Get conversion data by risk level"""
    try:
        # Get date range from query parameters
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')
        
        if not start_date_str or not end_date_str:
            # Default to last 30 days
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=30)
        else:
            start_date = datetime.fromisoformat(start_date_str)
            end_date = datetime.fromisoformat(end_date_str)
        
        # Get conversion data
        conversion_data = ai_calculator_dashboard.get_conversion_rates_by_risk_level(start_date, end_date)
        
        return jsonify({
            'conversion_data': [{
                'risk_level': conv.risk_level,
                'total_assessments': conv.total_assessments,
                'conversion_offers_viewed': conv.conversion_offers_viewed,
                'paid_upgrades_clicked': conv.paid_upgrades_clicked,
                'conversion_rate': conv.conversion_rate,
                'avg_revenue_per_user': conv.avg_revenue_per_user,
                'total_revenue': conv.total_revenue
            } for conv in conversion_data]
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting conversion data: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@analytics_bp.route('/dashboard/popular', methods=['GET'])
@require_auth
def get_popular_data():
    """Get popular job titles and industries"""
    try:
        # Get date range from query parameters
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')
        limit = int(request.args.get('limit', 20))
        
        if not start_date_str or not end_date_str:
            # Default to last 30 days
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=30)
        else:
            start_date = datetime.fromisoformat(start_date_str)
            end_date = datetime.fromisoformat(end_date_str)
        
        # Get popular data
        popular_data = ai_calculator_dashboard.get_popular_job_titles_and_industries(start_date, end_date, limit)
        
        return jsonify(popular_data), 200
        
    except Exception as e:
        logger.error(f"Error getting popular data: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@analytics_bp.route('/dashboard/revenue', methods=['GET'])
@require_auth
def get_revenue_data():
    """Get revenue attribution data"""
    try:
        # Get date range from query parameters
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')
        
        if not start_date_str or not end_date_str:
            # Default to last 30 days
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=30)
        else:
            start_date = datetime.fromisoformat(start_date_str)
            end_date = datetime.fromisoformat(end_date_str)
        
        # Get revenue data
        revenue_data = ai_calculator_dashboard.get_revenue_attribution(start_date, end_date)
        
        return jsonify(revenue_data), 200
        
    except Exception as e:
        logger.error(f"Error getting revenue data: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@analytics_bp.route('/reports/weekly', methods=['GET'])
@require_auth
def get_weekly_report():
    """Get weekly performance report"""
    try:
        # Get week start date from query parameters
        week_start_str = request.args.get('week_start')
        
        if week_start_str:
            week_start = datetime.fromisoformat(week_start_str)
        else:
            # Default to last week
            week_start = datetime.utcnow() - timedelta(days=7)
        
        # Generate weekly report
        report = ai_calculator_bi.generate_weekly_report(week_start)
        
        return jsonify(report), 200
        
    except Exception as e:
        logger.error(f"Error generating weekly report: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@analytics_bp.route('/reports/cohorts', methods=['GET'])
@require_auth
def get_cohort_analysis():
    """Get cohort analysis"""
    try:
        # Get date range from query parameters
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')
        
        if not start_date_str or not end_date_str:
            # Default to last 90 days
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=90)
        else:
            start_date = datetime.fromisoformat(start_date_str)
            end_date = datetime.fromisoformat(end_date_str)
        
        # Get cohort analysis
        cohorts = ai_calculator_bi.analyze_cohorts(start_date, end_date)
        
        return jsonify({
            'cohorts': [{
                'cohort_date': cohort.cohort_date,
                'cohort_size': cohort.cohort_size,
                'retention_1_day': cohort.retention_1_day,
                'retention_7_day': cohort.retention_7_day,
                'retention_30_day': cohort.retention_30_day,
                'conversion_rate': cohort.conversion_rate,
                'avg_revenue_per_user': cohort.avg_revenue_per_user,
                'lifetime_value': cohort.lifetime_value
            } for cohort in cohorts]
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting cohort analysis: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@analytics_bp.route('/reports/ltv', methods=['GET'])
@require_auth
def get_lifetime_value():
    """Get lifetime value analysis"""
    try:
        # Get user segments from query parameters
        segments = request.args.get('segments')
        user_segments = segments.split(',') if segments else None
        
        # Get LTV analysis
        ltv_data = ai_calculator_bi.analyze_lifetime_value(user_segments)
        
        return jsonify({
            'ltv_data': [{
                'user_segment': ltv.user_segment,
                'avg_ltv': ltv.avg_ltv,
                'median_ltv': ltv.median_ltv,
                'ltv_by_risk_level': ltv.ltv_by_risk_level,
                'time_to_break_even': ltv.time_to_break_even,
                'retention_rate': ltv.retention_rate,
                'churn_rate': ltv.churn_rate
            } for ltv in ltv_data]
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting LTV analysis: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@analytics_bp.route('/reports/market-intelligence', methods=['GET'])
@require_auth
def get_market_intelligence():
    """Get market intelligence data"""
    try:
        # Get time period from query parameters
        time_period = int(request.args.get('time_period', 30))
        
        # Get market intelligence
        market_data = ai_calculator_bi.get_market_intelligence(time_period)
        
        return jsonify({
            'market_intelligence': [{
                'job_sector': market.job_sector,
                'total_assessments': market.total_assessments,
                'avg_risk_level': market.avg_risk_level,
                'conversion_rate': market.conversion_rate,
                'concern_level': market.concern_level,
                'growth_trend': market.growth_trend,
                'recommendations': market.recommendations
            } for market in market_data]
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting market intelligence: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@analytics_bp.route('/reports/lead-comparison', methods=['GET'])
@require_auth
def get_lead_comparison():
    """Compare calculator leads vs other sources"""
    try:
        # Get time period from query parameters
        time_period = int(request.args.get('time_period', 30))
        
        # Get lead comparison
        comparison = ai_calculator_bi.compare_calculator_leads_vs_other_sources(time_period)
        
        return jsonify(comparison), 200
        
    except Exception as e:
        logger.error(f"Error getting lead comparison: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@analytics_bp.route('/ab-testing/create', methods=['POST'])
@require_auth
def create_ab_test():
    """Create a new A/B test"""
    try:
        test_config = request.json
        
        if not test_config:
            return jsonify({'error': 'Test configuration required'}), 400
        
        # Create test
        test_id = ai_calculator_ab_testing.create_test(test_config)
        
        return jsonify({'test_id': test_id}), 201
        
    except Exception as e:
        logger.error(f"Error creating A/B test: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@analytics_bp.route('/ab-testing/<test_id>/start', methods=['POST'])
@require_auth
def start_ab_test(test_id):
    """Start an A/B test"""
    try:
        success = ai_calculator_ab_testing.start_test(test_id)
        
        if success:
            return jsonify({'status': 'Test started successfully'}), 200
        else:
            return jsonify({'error': 'Failed to start test'}), 400
        
    except Exception as e:
        logger.error(f"Error starting A/B test: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@analytics_bp.route('/ab-testing/<test_id>/variant', methods=['GET'])
def get_test_variant(test_id):
    """Get test variant for user/session"""
    try:
        user_id = request.args.get('user_id')
        session_id = request.args.get('session_id')
        
        variant = ai_calculator_ab_testing.get_variant(test_id, user_id, session_id)
        
        return jsonify({'variant': variant}), 200
        
    except Exception as e:
        logger.error(f"Error getting test variant: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@analytics_bp.route('/ab-testing/<test_id>/results', methods=['GET'])
@require_auth
def get_test_results(test_id):
    """Get A/B test results"""
    try:
        results = ai_calculator_ab_testing.get_test_results(test_id)
        
        return jsonify(results), 200
        
    except Exception as e:
        logger.error(f"Error getting test results: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@analytics_bp.route('/performance/summary', methods=['GET'])
@require_auth
def get_performance_summary():
    """Get performance summary"""
    try:
        # Get hours from query parameters
        hours = int(request.args.get('hours', 24))
        
        # Get performance summary
        summary = ai_calculator_performance.get_performance_summary(hours)
        
        return jsonify(summary), 200
        
    except Exception as e:
        logger.error(f"Error getting performance summary: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@analytics_bp.route('/performance/start-monitoring', methods=['POST'])
@require_auth
def start_performance_monitoring():
    """Start performance monitoring"""
    try:
        ai_calculator_performance.start_monitoring()
        
        return jsonify({'status': 'Performance monitoring started'}), 200
        
    except Exception as e:
        logger.error(f"Error starting performance monitoring: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@analytics_bp.route('/performance/stop-monitoring', methods=['POST'])
@require_auth
def stop_performance_monitoring():
    """Stop performance monitoring"""
    try:
        ai_calculator_performance.stop_monitoring()
        
        return jsonify({'status': 'Performance monitoring stopped'}), 200
        
    except Exception as e:
        logger.error(f"Error stopping performance monitoring: {e}")
        return jsonify({'error': 'Internal server error'}), 500
