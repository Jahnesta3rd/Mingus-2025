# Import all API blueprints for easy registration
from .recommendation_engine_endpoints import recommendation_engine_api
from .resume_endpoints import resume_api
from .advanced_resume_endpoints import advanced_resume_api
from .job_matching_endpoints import job_matching_api
from .three_tier_endpoints import three_tier_api
from .profile_endpoints import profile_api
from .assessment_endpoints import assessment_api
from .meme_endpoints import meme_api

# List of all API blueprints
API_BLUEPRINTS = [
    recommendation_engine_api,
    resume_api,
    advanced_resume_api,
    job_matching_api,
    three_tier_api,
    profile_api,
    assessment_api,
    meme_api
]

def register_all_apis(app):
    """Register all API blueprints with the Flask app"""
    for blueprint in API_BLUEPRINTS:
        app.register_blueprint(blueprint)
    
    return app
