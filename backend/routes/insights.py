"""
Insights API Routes
Provides endpoints for accessing unified insights and recommendations
"""

from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
import logging
from datetime import datetime

from ..services.unified_insights_service import UnifiedInsightsService

logger = logging.getLogger(__name__)

insights_bp = Blueprint('insights', __name__)
insights_service = UnifiedInsightsService()

@insights_bp.route('/api/insights', methods=['GET'])
@login_required
def get_user_insights():
    """
    Get comprehensive insights for the current user
    Query parameters:
    - limit: Number of insights to return (default: 10, max: 50)
    """
    try:
        user_id = current_user.id
        limit = min(int(request.args.get('limit', 10)), 50)  # Cap at 50
        
        insights = insights_service.get_user_insights(user_id, limit=limit)
        
        if "error" in insights:
            return jsonify({"error": insights["error"]}), 500
        
        return jsonify(insights), 200
        
    except Exception as e:
        logger.error(f"Error getting user insights: {str(e)}")
        return jsonify({"error": "Failed to get insights"}), 500

@insights_bp.route('/api/insights/priority', methods=['GET'])
@login_required
def get_priority_insights():
    """
    Get top priority insights that require immediate attention
    Query parameters:
    - limit: Number of priority insights to return (default: 5, max: 10)
    """
    try:
        user_id = current_user.id
        limit = min(int(request.args.get('limit', 5)), 10)  # Cap at 10
        
        priority_insights = insights_service.get_priority_insights(user_id, limit=limit)
        
        # Convert dataclass objects to dictionaries
        insights_data = [insight.__dict__ for insight in priority_insights]
        
        return jsonify({
            "priority_insights": insights_data,
            "count": len(insights_data)
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting priority insights: {str(e)}")
        return jsonify({"error": "Failed to get priority insights"}), 500

@insights_bp.route('/api/insights/recommendations', methods=['GET'])
@login_required
def get_recommendations():
    """
    Get actionable recommendations for insights
    Query parameters:
    - insight_id: Optional specific insight ID to get recommendations for
    """
    try:
        user_id = current_user.id
        insight_id = request.args.get('insight_id')
        
        recommendations = insights_service.get_insight_recommendations(user_id, insight_id)
        
        # Convert dataclass objects to dictionaries
        recommendations_data = [rec.__dict__ for rec in recommendations]
        
        return jsonify({
            "recommendations": recommendations_data,
            "count": len(recommendations_data)
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting recommendations: {str(e)}")
        return jsonify({"error": "Failed to get recommendations"}), 500

@insights_bp.route('/api/insights/dashboard', methods=['GET'])
@login_required
def get_insights_dashboard():
    """
    Get comprehensive dashboard data including insights, recommendations, and metrics
    """
    try:
        user_id = current_user.id
        
        dashboard_data = insights_service.get_insights_dashboard(user_id)
        
        if "error" in dashboard_data:
            return jsonify({"error": dashboard_data["error"]}), 500
        
        return jsonify(dashboard_data), 200
        
    except Exception as e:
        logger.error(f"Error getting insights dashboard: {str(e)}")
        return jsonify({"error": "Failed to get dashboard"}), 500

@insights_bp.route('/api/insights/categories/<category>', methods=['GET'])
@login_required
def get_insights_by_category(category):
    """
    Get insights filtered by category
    Path parameters:
    - category: One of 'career', 'financial', 'health', 'relationship', 'emergency'
    Query parameters:
    - limit: Number of insights to return (default: 10, max: 20)
    """
    try:
        user_id = current_user.id
        limit = min(int(request.args.get('limit', 10)), 20)
        
        # Get all insights and filter by category
        all_insights = insights_service.get_user_insights(user_id, limit=50)
        
        if "error" in all_insights:
            return jsonify({"error": all_insights["error"]}), 500
        
        # Filter insights by category
        category_insights = [
            insight for insight in all_insights["insights"]
            if insight.get("category") == category
        ]
        
        # Limit results
        category_insights = category_insights[:limit]
        
        return jsonify({
            "insights": category_insights,
            "category": category,
            "count": len(category_insights)
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting insights by category: {str(e)}")
        return jsonify({"error": "Failed to get category insights"}), 500

@insights_bp.route('/api/insights/summary', methods=['GET'])
@login_required
def get_insights_summary():
    """
    Get summary statistics for user insights
    """
    try:
        user_id = current_user.id
        
        insights = insights_service.get_user_insights(user_id, limit=50)
        
        if "error" in insights:
            return jsonify({"error": insights["error"]}), 500
        
        summary = insights.get("summary", {})
        categories = insights.get("categories", {})
        severity_distribution = insights.get("severity_distribution", {})
        
        return jsonify({
            "summary": summary,
            "high_priority_count": summary.get("high_priority_count", 0),
            "critical_insights": summary.get("critical_insights", 0),
            "actionable_insights": summary.get("actionable_insights", 0),
            "categories": categories,
            "severity_distribution": severity_distribution,
            "total_insights": insights.get("total_count", 0)
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting insights summary: {str(e)}")
        return jsonify({"error": "Failed to get insights summary"}), 500

@insights_bp.route('/api/insights/job-security', methods=['GET'])
@login_required
def get_job_security_insights():
    """
    Get job security insights with empowering language and optimization strategies
    """
    try:
        user_id = current_user.id
        
        job_security_insights = insights_service.get_job_security_insights(user_id)
        
        if "error" in job_security_insights:
            return jsonify({"error": job_security_insights["error"]}), 500
        
        return jsonify(job_security_insights), 200
        
    except Exception as e:
        logger.error(f"Error getting job security insights: {str(e)}")
        return jsonify({"error": "Failed to get job security insights"}), 500

@insights_bp.route('/api/insights/emergency-fund', methods=['GET'])
@login_required
def get_emergency_fund_insights():
    """
    Get personalized emergency fund recommendations and cash flow insights
    """
    try:
        user_id = current_user.id
        
        emergency_fund_insights = insights_service.get_emergency_fund_insights(user_id)
        
        if "error" in emergency_fund_insights:
            return jsonify({"error": emergency_fund_insights["error"]}), 500
        
        return jsonify(emergency_fund_insights), 200
        
    except Exception as e:
        logger.error(f"Error getting emergency fund insights: {str(e)}")
        return jsonify({"error": "Failed to get emergency fund insights"}), 500

@insights_bp.route('/api/insights/health-relationships', methods=['GET'])
@login_required
def get_health_relationship_insights():
    """
    Get health and relationship awareness insights
    """
    try:
        user_id = current_user.id
        
        health_relationship_insights = insights_service.get_health_relationship_insights(user_id)
        
        if "error" in health_relationship_insights:
            return jsonify({"error": health_relationship_insights["error"]}), 500
        
        return jsonify(health_relationship_insights), 200
        
    except Exception as e:
        logger.error(f"Error getting health relationship insights: {str(e)}")
        return jsonify({"error": "Failed to get health relationship insights"}), 500

@insights_bp.route('/api/insights/enhanced-dashboard', methods=['GET'])
@login_required
def get_enhanced_insights_dashboard():
    """
    Get comprehensive dashboard data including all enhanced insights
    """
    try:
        user_id = current_user.id
        
        # Get all enhanced insights
        job_security = insights_service.get_job_security_insights(user_id)
        emergency_fund = insights_service.get_emergency_fund_insights(user_id)
        health_relationships = insights_service.get_health_relationship_insights(user_id)
        
        # Get existing dashboard data
        dashboard_data = insights_service.get_insights_dashboard(user_id)
        
        # Combine all data
        enhanced_dashboard = {
            "job_security": job_security if "error" not in job_security else None,
            "emergency_fund": emergency_fund if "error" not in emergency_fund else None,
            "health_relationships": health_relationships if "error" not in health_relationships else None,
            "existing_dashboard": dashboard_data if "error" not in dashboard_data else None,
            "last_updated": datetime.now().isoformat()
        }
        
        return jsonify(enhanced_dashboard), 200
        
    except Exception as e:
        logger.error(f"Error getting enhanced insights dashboard: {str(e)}")
        return jsonify({"error": "Failed to get enhanced dashboard"}), 500 