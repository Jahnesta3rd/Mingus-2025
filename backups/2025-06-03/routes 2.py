from flask import Blueprint, request, jsonify, render_template, current_app
from backend.models.onboarding import (
    AnonymousOnboardingCreate,
    OnboardingCreate,
    OnboardingUpdate
)
from backend.models.important_dates import ImportantDateCreate, ImportantDateUpdate
from backend.middleware.auth import require_auth
from datetime import datetime
import uuid
from loguru import logger
from pydantic import ValidationError
import asyncio
from app import async_route

api = Blueprint('api', __name__)

def get_client_info():
    """Get client information from the request."""
    session_id = request.cookies.get('session_id')
    if not session_id:
        request_data = request.get_json()
        if isinstance(request_data, dict):
            session_id = request_data.get('session_id')
    if not session_id:
        session_id = str(uuid.uuid4())

    return {
        'ip_address': request.remote_addr,
        'user_agent': request.headers.get('User-Agent', ''),
        'referrer': request.referrer,
        'session_id': session_id
    }

@api.route('/app')
def main_app():
    return render_template('main_app.html')

@api.route('/welcome')
def welcome():
    return render_template('welcome.html')

@api.route('/onboarding')
def onboarding():
    return render_template('onboarding.html')

@api.route('/signup')
def signup_page():
    """Render the signup form."""
    session_id = request.cookies.get('session_id', str(uuid.uuid4()))
    return render_template('signup.html', session_id=session_id)

@api.route('/api/onboarding/anonymous', methods=['POST'])
@async_route
async def create_anonymous_onboarding():
    """Create an anonymous onboarding response."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Empty request body"}), 400
            
        # Get and validate client info
        client_info = get_client_info()
        
        # Combine data with client info
        complete_data = {**data, **client_info}
        
        # Create anonymous onboarding
        validated_data = AnonymousOnboardingCreate(**complete_data)
        result = await current_app.onboarding_service.create_anonymous_onboarding(validated_data)
        
        response = jsonify(result.model_dump())
        
        # Set session cookie if not already set
        if not request.cookies.get('session_id'):
            response.set_cookie(
                'session_id',
                client_info['session_id'],
                max_age=30*24*60*60,  # 30 days
                httponly=True,
                secure=True,
                samesite='Strict'
            )
        
        return response, 201
        
    except ValidationError as e:
        return jsonify({
            "error": "Validation error",
            "details": e.errors()
        }), 400
    except Exception as e:
        logger.error(f"Error creating anonymous onboarding: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@api.route('/api/onboarding/anonymous/<session_id>', methods=['GET'])
@async_route
async def get_anonymous_onboarding(session_id: str):
    """Get anonymous onboarding responses for a session."""
    try:
        result = await current_app.onboarding_service.get_anonymous_onboarding(session_id)
        if not result:
            return jsonify({"error": "No onboarding responses found"}), 404
        return jsonify([response.model_dump() for response in result])
    except Exception as e:
        logger.error(f"Error fetching anonymous onboarding: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@api.route('/api/onboarding/anonymous/convert', methods=['POST'])
@require_auth
@async_route
async def convert_anonymous_to_user():
    """Convert anonymous responses to user responses after signup."""
    try:
        data = request.get_json()
        if not data or 'session_id' not in data:
            return jsonify({"error": "session_id is required"}), 400
            
        result = await current_app.onboarding_service.convert_anonymous_to_user(
            session_id=data['session_id'],
            user_id=request.user_id
        )
        return jsonify(result.model_dump())
    except Exception as e:
        logger.error(f"Error converting anonymous onboarding: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@api.route('/api/onboarding/anonymous/stats', methods=['GET'])
@async_route
async def get_anonymous_onboarding_stats():
    """Get statistics about anonymous onboarding responses."""
    try:
        result = await current_app.onboarding_service.get_anonymous_onboarding_stats()
        return jsonify(result.model_dump())
    except Exception as e:
        logger.error(f"Error fetching anonymous onboarding stats: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@api.route('/api/onboarding/profile', methods=['POST'])
@require_auth
@async_route
async def create_onboarding():
    try:
        data = request.get_json()
        onboarding_data = OnboardingCreate(**data)
        result = await current_app.onboarding_service.create_onboarding_profile(
            request.user_id,
            onboarding_data
        )
        return jsonify(result.model_dump()), 201
    except ValidationError as e:
        return jsonify({"error": "Validation error", "details": e.errors()}), 400
    except Exception as e:
        logger.error(f"Error creating onboarding profile: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@api.route('/api/onboarding/profile', methods=['GET'])
@require_auth
@async_route
async def get_onboarding():
    try:
        result = await current_app.onboarding_service.get_onboarding_profile(request.user_id)
        if not result:
            return jsonify({"error": "Onboarding profile not found"}), 404
        return jsonify(result.model_dump())
    except Exception as e:
        logger.error(f"Error fetching onboarding profile: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@api.route('/api/onboarding/profile', methods=['PUT'])
@require_auth
@async_route
async def update_onboarding():
    try:
        data = request.get_json()
        update_data = OnboardingUpdate(**data)
        result = await current_app.onboarding_service.update_onboarding_profile(
            request.user_id,
            update_data
        )
        return jsonify(result.model_dump())
    except ValidationError as e:
        return jsonify({"error": "Validation error", "details": e.errors()}), 400
    except Exception as e:
        logger.error(f"Error updating onboarding profile: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@api.route('/api/onboarding/status', methods=['GET'])
@require_auth
@async_route
async def check_onboarding_status():
    try:
        result = await current_app.onboarding_service.check_onboarding_status(request.user_id)
        return jsonify(result.model_dump())
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        logger.error(f"Error checking onboarding status: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@api.route('/api/onboarding/stats', methods=['GET'])
@require_auth
@async_route
async def get_onboarding_stats():
    try:
        result = await current_app.onboarding_service.get_onboarding_stats()
        return jsonify(result.model_dump())
    except Exception as e:
        logger.error(f"Error fetching onboarding stats: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500 