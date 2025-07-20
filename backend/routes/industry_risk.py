"""
Industry Risk Assessment API Routes
Provides endpoints for comprehensive industry risk analysis including NAICS mapping,
employment trends, automation risks, and career advancement insights.
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from typing import Dict, Any, Optional
import logging
from loguru import logger

from ..ml.industry_risk_assessment import (
    get_industry_risk_assessor,
    assess_industry_risk,
    get_industry_comparison,
    get_target_demographic_insights
)
from ..optimization.external_data_cache_manager import (
    get_external_cache_manager,
    DataType,
    SubscriptionTier
)
from ..models.user import User
from ..services.audit_service import audit_log

# Create blueprint
industry_risk_bp = Blueprint('industry_risk', __name__)

@industry_risk_bp.route('/api/industry-risk-assessment', methods=['POST'])
@jwt_required()
def industry_risk_assessment():
    """
    Get comprehensive industry risk assessment
    
    Expected JSON payload:
    {
        "industry_name": "Technology",
        "job_title": "Software Engineer",
        "location": "San Francisco, CA"
    }
    
    Returns comprehensive risk analysis including:
    - NAICS mapping
    - Employment trends
    - Automation/AI risks
    - Economic sensitivity
    - Geographic factors
    - Career advancement insights
    """
    try:
        # Get current user
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        if not user:
            return jsonify({"error": "User not found"}), 404
        
        # Parse request data
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        industry_name = data.get('industry_name', '').strip()
        job_title = data.get('job_title', '').strip()
        location = data.get('location', '').strip()
        
        if not industry_name:
            return jsonify({"error": "Industry name is required"}), 400
        
        # Get user's subscription tier
        subscription_tier = SubscriptionTier.PREMIUM  # Default for now
        if hasattr(user, 'subscription_tier'):
            try:
                subscription_tier = SubscriptionTier(user.subscription_tier)
            except ValueError:
                subscription_tier = SubscriptionTier.FREE
        
        # Check cache first
        cache_manager = get_external_cache_manager()
        cache_key = f"industry_risk:{industry_name}:{job_title}:{location}"
        cached_result = cache_manager.get_external_data(
            DataType.JOB_SECURITY_SCORE,
            cache_key,
            subscription_tier
        )
        
        if cached_result:
            logger.info(f"Returning cached industry risk assessment for {industry_name}")
            audit_log(
                user_id=user_id,
                action="industry_risk_assessment_cache_hit",
                details={
                    "industry_name": industry_name,
                    "job_title": job_title,
                    "location": location
                }
            )
            return jsonify(cached_result)
        
        # Get fresh assessment
        logger.info(f"Generating fresh industry risk assessment for {industry_name}")
        
        # Get industry risk assessor
        assessor = get_industry_risk_assessor()
        
        # Perform comprehensive risk assessment
        risk_assessment = assessor.get_comprehensive_risk_assessment(
            industry_name=industry_name,
            job_title=job_title,
            location=location
        )
        
        if "error" in risk_assessment:
            return jsonify(risk_assessment), 400
        
        # Add user-specific insights
        risk_assessment["user_insights"] = {
            "subscription_tier": subscription_tier.value,
            "target_demographic": True,  # African American professionals 25-35
            "personalized_recommendations": _get_personalized_recommendations(
                risk_assessment, user, subscription_tier
            )
        }
        
        # Cache the result
        cache_manager.set_external_data(
            DataType.JOB_SECURITY_SCORE,
            cache_key,
            risk_assessment,
            "industry_risk_assessor",
            subscription_tier,
            ttl_override=3600  # 1 hour cache
        )
        
        # Audit log
        audit_log(
            user_id=user_id,
            action="industry_risk_assessment",
            details={
                "industry_name": industry_name,
                "job_title": job_title,
                "location": location,
                "risk_score": risk_assessment.get("overall_risk_score", 0),
                "risk_level": risk_assessment.get("overall_risk_level", "unknown")
            }
        )
        
        return jsonify(risk_assessment)
        
    except Exception as e:
        logger.error(f"Error in industry risk assessment: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@industry_risk_bp.route('/api/industry-comparison', methods=['POST'])
@jwt_required()
def industry_comparison():
    """
    Compare multiple industries
    
    Expected JSON payload:
    {
        "industries": ["Technology", "Healthcare", "Finance"]
    }
    
    Returns comparison analysis of multiple industries
    """
    try:
        # Get current user
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        if not user:
            return jsonify({"error": "User not found"}), 404
        
        # Parse request data
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        industries = data.get('industries', [])
        if not industries or not isinstance(industries, list):
            return jsonify({"error": "Industries list is required"}), 400
        
        if len(industries) < 2:
            return jsonify({"error": "At least 2 industries required for comparison"}), 400
        
        if len(industries) > 5:
            return jsonify({"error": "Maximum 5 industries allowed for comparison"}), 400
        
        # Get industry risk assessor
        assessor = get_industry_risk_assessor()
        
        # Map industries to NAICS codes
        naics_codes = []
        industry_mappings = {}
        
        for industry in industries:
            naics_code = assessor.map_industry_to_naics(industry)
            if naics_code:
                naics_codes.append(naics_code)
                industry_mappings[naics_code] = industry
            else:
                logger.warning(f"Could not map industry '{industry}' to NAICS code")
        
        if len(naics_codes) < 2:
            return jsonify({"error": "Could not map enough industries to NAICS codes"}), 400
        
        # Get comparison
        comparison = assessor.get_industry_comparison(naics_codes)
        
        # Add industry names to comparison
        for naics_code in comparison["comparisons"]:
            comparison["comparisons"][naics_code]["original_name"] = industry_mappings.get(naics_code, "")
        
        # Audit log
        audit_log(
            user_id=user_id,
            action="industry_comparison",
            details={
                "industries": industries,
                "naics_codes": naics_codes,
                "comparison_count": len(naics_codes)
            }
        )
        
        return jsonify(comparison)
        
    except Exception as e:
        logger.error(f"Error in industry comparison: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@industry_risk_bp.route('/api/target-demographic-insights', methods=['GET'])
@jwt_required()
def target_demographic_insights():
    """
    Get insights specifically for African American professionals aged 25-35
    
    Returns:
    - High growth industries
    - Low risk industries  
    - High advancement industries
    - Diversity-friendly industries
    - Recommendations
    """
    try:
        # Get current user
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        if not user:
            return jsonify({"error": "User not found"}), 404
        
        # Get insights
        insights = get_target_demographic_insights()
        
        # Add user-specific context
        insights["user_context"] = {
            "age_group": "25-35",
            "demographic": "African American",
            "professional_level": "Early to mid-career",
            "recommendations_count": len(insights.get("recommendations", []))
        }
        
        # Audit log
        audit_log(
            user_id=user_id,
            action="target_demographic_insights",
            details={
                "insights_requested": True,
                "high_growth_count": len(insights.get("high_growth_industries", [])),
                "low_risk_count": len(insights.get("low_risk_industries", [])),
                "high_advancement_count": len(insights.get("high_advancement_industries", []))
            }
        )
        
        return jsonify(insights)
        
    except Exception as e:
        logger.error(f"Error in target demographic insights: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@industry_risk_bp.route('/api/industry-risk-factors/<naics_code>', methods=['GET'])
@jwt_required()
def industry_risk_factors(naics_code: str):
    """
    Get detailed risk factors for a specific NAICS code
    
    Args:
        naics_code: NAICS code for the industry
        
    Returns detailed risk factor analysis
    """
    try:
        # Get current user
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        if not user:
            return jsonify({"error": "User not found"}), 404
        
        # Validate NAICS code format
        if not naics_code or len(naics_code) != 6 or not naics_code.isdigit():
            return jsonify({"error": "Invalid NAICS code format"}), 400
        
        # Get industry risk assessor
        assessor = get_industry_risk_assessor()
        
        # Get detailed analysis
        profile = assessor.get_industry_risk_profile(naics_code)
        if not profile:
            return jsonify({"error": "Industry profile not found"}), 404
        
        # Get detailed analyses
        employment_trends = assessor.analyze_employment_trends(naics_code)
        automation_risk = assessor.assess_automation_risk(naics_code)
        economic_sensitivity = assessor.analyze_economic_sensitivity(naics_code)
        geographic_factors = assessor.analyze_geographic_factors(naics_code)
        career_insights = assessor.get_career_advancement_insights(naics_code)
        
        detailed_analysis = {
            "naics_code": naics_code,
            "industry_name": profile.industry_name,
            "risk_level": profile.risk_level.value,
            "overall_score": profile.overall_score,
            "employment_trends": employment_trends,
            "automation_risk": automation_risk,
            "economic_sensitivity": economic_sensitivity,
            "geographic_factors": geographic_factors,
            "career_advancement": career_insights,
            "risk_factors": profile.risk_factors,
            "positive_indicators": profile.positive_indicators,
            "recommendations": profile.recommendations,
            "last_updated": profile.last_updated.isoformat(),
            "confidence_level": profile.confidence_level,
            "data_sources": profile.data_sources
        }
        
        # Audit log
        audit_log(
            user_id=user_id,
            action="industry_risk_factors",
            details={
                "naics_code": naics_code,
                "industry_name": profile.industry_name,
                "risk_score": profile.overall_score
            }
        )
        
        return jsonify(detailed_analysis)
        
    except Exception as e:
        logger.error(f"Error in industry risk factors: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@industry_risk_bp.route('/api/industry-automation-analysis', methods=['POST'])
@jwt_required()
def industry_automation_analysis():
    """
    Get detailed automation risk analysis for industry and job title
    
    Expected JSON payload:
    {
        "industry_name": "Technology",
        "job_title": "Data Entry Clerk"
    }
    
    Returns detailed automation risk analysis
    """
    try:
        # Get current user
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        if not user:
            return jsonify({"error": "User not found"}), 404
        
        # Parse request data
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        industry_name = data.get('industry_name', '').strip()
        job_title = data.get('job_title', '').strip()
        
        if not industry_name:
            return jsonify({"error": "Industry name is required"}), 400
        
        # Get industry risk assessor
        assessor = get_industry_risk_assessor()
        
        # Map to NAICS code
        naics_code = assessor.map_industry_to_naics(industry_name, job_title)
        if not naics_code:
            return jsonify({"error": "Industry not found in database"}), 404
        
        # Get detailed automation analysis
        automation_analysis = assessor.assess_automation_risk(naics_code, job_title)
        
        if not automation_analysis:
            return jsonify({"error": "Automation analysis not available"}), 404
        
        # Add job-specific insights
        automation_analysis["job_context"] = {
            "industry_name": industry_name,
            "job_title": job_title,
            "naics_code": naics_code,
            "analysis_type": "automation_risk"
        }
        
        # Audit log
        audit_log(
            user_id=user_id,
            action="industry_automation_analysis",
            details={
                "industry_name": industry_name,
                "job_title": job_title,
                "naics_code": naics_code,
                "automation_risk_score": automation_analysis.get("automation_risk_score", 0)
            }
        )
        
        return jsonify(automation_analysis)
        
    except Exception as e:
        logger.error(f"Error in industry automation analysis: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

def _get_personalized_recommendations(risk_assessment: Dict[str, Any], user: User, subscription_tier: SubscriptionTier) -> Dict[str, Any]:
    """Get personalized recommendations based on user profile and risk assessment"""
    
    recommendations = {
        "immediate_actions": [],
        "skill_development": [],
        "career_planning": [],
        "risk_mitigation": []
    }
    
    overall_score = risk_assessment.get("overall_risk_score", 50)
    automation_risk = risk_assessment.get("automation_risk", {}).get("automation_risk_score", 50)
    advancement_opportunities = risk_assessment.get("career_advancement", {}).get("advancement_opportunities", 50)
    
    # Immediate actions based on risk level
    if overall_score > 60:
        recommendations["immediate_actions"].extend([
            "Consider upskilling in emerging technologies",
            "Build emergency savings fund",
            "Network with professionals in more stable industries"
        ])
    elif overall_score > 40:
        recommendations["immediate_actions"].extend([
            "Monitor industry trends regularly",
            "Develop transferable skills",
            "Build strong professional relationships"
        ])
    else:
        recommendations["immediate_actions"].extend([
            "Continue current career development path",
            "Focus on specialization in your field",
            "Mentor others in your industry"
        ])
    
    # Skill development recommendations
    if automation_risk > 60:
        recommendations["skill_development"].extend([
            "Learn AI/ML tools and technologies",
            "Develop creative problem-solving skills",
            "Focus on human-centric skills (leadership, communication)",
            "Consider roles that manage AI systems"
        ])
    elif automation_risk > 40:
        recommendations["skill_development"].extend([
            "Enhance analytical and decision-making capabilities",
            "Develop expertise in areas requiring human judgment",
            "Stay updated on industry-specific technologies"
        ])
    else:
        recommendations["skill_development"].extend([
            "Continue developing specialized expertise",
            "Focus on innovation and creative thinking",
            "Build domain-specific knowledge"
        ])
    
    # Career planning recommendations
    if advancement_opportunities > 75:
        recommendations["career_planning"].extend([
            "Set clear advancement goals and timelines",
            "Seek mentorship from senior professionals",
            "Take on leadership opportunities",
            "Consider specialized certifications"
        ])
    elif advancement_opportunities > 50:
        recommendations["career_planning"].extend([
            "Identify growth areas in your current role",
            "Build relationships with decision-makers",
            "Develop cross-functional skills",
            "Consider lateral moves for skill development"
        ])
    else:
        recommendations["career_planning"].extend([
            "Explore opportunities in related industries",
            "Consider entrepreneurship or consulting",
            "Focus on building transferable skills",
            "Network outside your current industry"
        ])
    
    # Risk mitigation strategies
    recommendations["risk_mitigation"] = risk_assessment.get("automation_risk", {}).get("mitigation_strategies", [])
    
    # Add subscription tier specific recommendations
    if subscription_tier == SubscriptionTier.ENTERPRISE:
        recommendations["immediate_actions"].append("Access premium industry reports and analysis")
        recommendations["career_planning"].append("Utilize executive coaching and mentorship programs")
    elif subscription_tier == SubscriptionTier.PREMIUM:
        recommendations["immediate_actions"].append("Access detailed industry trend reports")
        recommendations["skill_development"].append("Enroll in premium skill development courses")
    
    return recommendations

# Register blueprint with app
def init_industry_risk_routes(app):
    """Initialize industry risk routes with Flask app"""
    app.register_blueprint(industry_risk_bp)
    logger.info("Industry risk assessment routes registered") 