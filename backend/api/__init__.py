# Import all API blueprints for easy registration
from .recommendation_engine_endpoints import recommendation_engine_api
from .resume_endpoints import resume_api
from .advanced_resume_endpoints import advanced_resume_api
from .job_matching_endpoints import job_matching_api
from .three_tier_endpoints import three_tier_api
from .profile_endpoints import profile_api
from .assessment_endpoints import assessment_api
from .meme_endpoints import meme_api
from .daily_outlook_api import daily_outlook_api
from .analytics_endpoints import analytics_bp
from .unified_risk_analytics_api import risk_analytics_api
from .subscription_endpoints import subscription_bp
from .activity_endpoints import activity_bp
from .user_endpoints import user_bp
from .career_endpoints import career_bp

# List of all API blueprints
API_BLUEPRINTS = [
    recommendation_engine_api,
    resume_api,
    advanced_resume_api,
    job_matching_api,
    three_tier_api,
    profile_api,
    assessment_api,
    meme_api,
    daily_outlook_api,
    analytics_bp,
    risk_analytics_api,
    subscription_bp,
    activity_bp,
    user_bp,
    career_bp
]

def register_all_apis(app):
    """Register all API blueprints with the Flask app"""
    for blueprint in API_BLUEPRINTS:
        app.register_blueprint(blueprint)
    
    return app
