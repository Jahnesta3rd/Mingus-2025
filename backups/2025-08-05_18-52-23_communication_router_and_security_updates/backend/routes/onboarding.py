from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
from sqlalchemy.orm import Session
from backend.services.onboarding_service import OnboardingService
from backend.middleware.security import validate_financial_data
import logging

logger = logging.getLogger(__name__)

onboarding_bp = Blueprint('onboarding', __name__, url_prefix='/api/onboarding')

@onboarding_bp.route('/status', methods=['GET'])
@login_required
def get_onboarding_status():
    """Get user's onboarding status"""
    try:
        db = current_app.extensions['sqlalchemy'].db
        onboarding_service = OnboardingService(db)
        
        status = onboarding_service.get_onboarding_status(current_user.id)
        
        return jsonify({
            'success': True,
            'status': status
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting onboarding status: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@onboarding_bp.route('/step/<int:step>', methods=['POST'])
@login_required
@validate_financial_data
def complete_onboarding_step(step):
    """Complete an onboarding step"""
    try:
        data = request.get_json()
        db = current_app.extensions['sqlalchemy'].db
        onboarding_service = OnboardingService(db)
        
        result = onboarding_service.complete_step(
            current_user.id, 
            step, 
            data
        )
        
        return jsonify({
            'success': True,
            'result': result,
            'message': f'Step {step} completed successfully'
        }), 200
        
    except ValueError as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400
    except Exception as e:
        logger.error(f"Error completing onboarding step: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@onboarding_bp.route('/complete', methods=['POST'])
@login_required
def complete_onboarding():
    """Complete the entire onboarding process"""
    try:
        db = current_app.extensions['sqlalchemy'].db
        onboarding_service = OnboardingService(db)
        
        result = onboarding_service.complete_onboarding(current_user.id)
        
        return jsonify({
            'success': True,
            'result': result,
            'message': 'Onboarding completed successfully'
        }), 200
        
    except Exception as e:
        logger.error(f"Error completing onboarding: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500
