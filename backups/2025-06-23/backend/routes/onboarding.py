"""
Onboarding routes blueprint
"""

from flask import Blueprint, request, jsonify, session, current_app
from loguru import logger

onboarding_bp = Blueprint('onboarding', __name__)

@onboarding_bp.route('/start', methods=['POST'])
def start_onboarding():
    """Start onboarding process for a user"""
    try:
        user_id = session.get('user_id')
        
        if not user_id:
            return jsonify({'error': 'Not authenticated'}), 401
        
        # Create onboarding record
        onboarding_record = current_app.onboarding_service.create_onboarding_record({
            'user_id': user_id,
            'current_step': 'welcome'
        })
        
        if onboarding_record:
            return jsonify({
                'success': True,
                'message': 'Onboarding started successfully',
                'onboarding_record': onboarding_record
            }), 201
        else:
            return jsonify({'error': 'Failed to start onboarding'}), 500
            
    except Exception as e:
        logger.error(f"Start onboarding error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@onboarding_bp.route('/profile', methods=['POST'])
def create_profile():
    """Create user profile during onboarding"""
    try:
        user_id = session.get('user_id')
        
        if not user_id:
            return jsonify({'error': 'Not authenticated'}), 401
        
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Create user profile
        profile_data = {
            'user_id': user_id,
            'monthly_income': data.get('monthly_income'),
            'income_frequency': data.get('income_frequency'),
            'primary_income_source': data.get('primary_income_source'),
            'age_range': data.get('age_range'),
            'location_state': data.get('location_state'),
            'location_city': data.get('location_city'),
            'household_size': data.get('household_size'),
            'employment_status': data.get('employment_status'),
            'current_savings': data.get('current_savings'),
            'current_debt': data.get('current_debt'),
            'credit_score_range': data.get('credit_score_range')
        }
        
        profile = current_app.onboarding_service.create_user_profile(profile_data)
        
        if profile:
            # Update onboarding progress
            current_app.onboarding_service.update_onboarding_progress(
                user_id=user_id,
                step_name='profile',
                is_completed=True,
                responses=data
            )
            
            return jsonify({
                'success': True,
                'message': 'Profile created successfully',
                'profile': profile
            }), 201
        else:
            return jsonify({'error': 'Failed to create profile'}), 500
            
    except Exception as e:
        logger.error(f"Create profile error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@onboarding_bp.route('/goals', methods=['POST'])
def set_goals():
    """Set financial goals during onboarding"""
    try:
        user_id = session.get('user_id')
        
        if not user_id:
            return jsonify({'error': 'Not authenticated'}), 401
        
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Update profile with goals
        goals_data = {
            'primary_goal': data.get('primary_goal'),
            'goal_amount': data.get('goal_amount'),
            'goal_timeline_months': data.get('goal_timeline_months')
        }
        
        updated_profile = current_app.onboarding_service.update_user_profile(user_id, goals_data)
        
        if updated_profile:
            # Update onboarding progress
            current_app.onboarding_service.update_onboarding_progress(
                user_id=user_id,
                step_name='goals',
                is_completed=True,
                responses=data
            )
            
            return jsonify({
                'success': True,
                'message': 'Goals set successfully',
                'profile': updated_profile
            }), 200
        else:
            return jsonify({'error': 'Failed to update profile with goals'}), 500
            
    except Exception as e:
        logger.error(f"Set goals error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@onboarding_bp.route('/preferences', methods=['POST'])
def set_preferences():
    """Set user preferences during onboarding"""
    try:
        user_id = session.get('user_id')
        
        if not user_id:
            return jsonify({'error': 'Not authenticated'}), 401
        
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Update profile with preferences
        preferences_data = {
            'risk_tolerance': data.get('risk_tolerance'),
            'investment_experience': data.get('investment_experience')
        }
        
        updated_profile = current_app.onboarding_service.update_user_profile(user_id, preferences_data)
        
        if updated_profile:
            # Update onboarding progress
            current_app.onboarding_service.update_onboarding_progress(
                user_id=user_id,
                step_name='preferences',
                is_completed=True,
                responses=data
            )
            
            return jsonify({
                'success': True,
                'message': 'Preferences set successfully',
                'profile': updated_profile
            }), 200
        else:
            return jsonify({'error': 'Failed to update profile with preferences'}), 500
            
    except Exception as e:
        logger.error(f"Set preferences error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@onboarding_bp.route('/expenses', methods=['POST'])
def set_expenses():
    """Set expense categories during onboarding"""
    try:
        user_id = session.get('user_id')
        
        if not user_id:
            return jsonify({'error': 'Not authenticated'}), 401
        
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        expense_categories = data.get('expense_categories', {})
        
        # Update profile with expense categories
        updated_profile = current_app.onboarding_service.update_user_profile(user_id, {
            'expense_categories': expense_categories
        })
        
        if updated_profile:
            return jsonify({
                'success': True,
                'message': 'Expense categories updated successfully',
                'profile': updated_profile
            }), 200
        else:
            return jsonify({'error': 'Failed to update expense categories'}), 500
            
    except Exception as e:
        logger.error(f"Set expenses error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@onboarding_bp.route('/complete', methods=['POST'])
def complete_onboarding():
    """Complete onboarding process"""
    try:
        user_id = session.get('user_id')
        
        if not user_id:
            return jsonify({'error': 'Not authenticated'}), 401
        
        data = request.get_json() or {}
        
        # Mark profile as complete
        current_app.onboarding_service.update_user_profile(user_id, {'is_complete': True})
        
        # Update onboarding progress to complete
        current_app.onboarding_service.update_onboarding_progress(
            user_id=user_id,
            step_name='complete',
            is_completed=True,
            responses=data
        )
        
        return jsonify({
            'success': True,
            'message': 'Onboarding completed successfully'
        }), 200
        
    except Exception as e:
        logger.error(f"Complete onboarding error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@onboarding_bp.route('/progress', methods=['GET'])
def get_onboarding_progress():
    """Get onboarding progress for current user"""
    try:
        user_id = session.get('user_id')
        
        if not user_id:
            return jsonify({'error': 'Not authenticated'}), 401
        
        progress = current_app.onboarding_service.get_onboarding_progress(user_id)
        profile = current_app.onboarding_service.get_user_profile(user_id)
        
        if progress:
            return jsonify({
                'success': True,
                'progress': progress,
                'profile': profile
            }), 200
        else:
            return jsonify({'error': 'Onboarding progress not found'}), 404
            
    except Exception as e:
        logger.error(f"Get onboarding progress error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@onboarding_bp.route('/progress/<user_id>', methods=['GET'])
def get_user_onboarding_progress(user_id):
    """Get onboarding progress for a specific user (admin only)"""
    try:
        # Check if current user is admin or the same user
        current_user_id = session.get('user_id')
        
        if not current_user_id:
            return jsonify({'error': 'Not authenticated'}), 401
        
        # For now, allow users to see their own progress
        # In production, you might want to add admin checks
        if current_user_id != user_id:
            return jsonify({'error': 'Unauthorized'}), 403
        
        progress = current_app.onboarding_service.get_onboarding_progress(user_id)
        profile = current_app.onboarding_service.get_user_profile(user_id)
        
        if progress:
            return jsonify({
                'success': True,
                'progress': progress,
                'profile': profile
            }), 200
        else:
            return jsonify({'error': 'Onboarding progress not found'}), 404
            
    except Exception as e:
        logger.error(f"Get user onboarding progress error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@onboarding_bp.route('/step/<step_name>', methods=['POST'])
def update_step(step_name):
    """Update a specific onboarding step"""
    try:
        user_id = session.get('user_id')
        
        if not user_id:
            return jsonify({'error': 'Not authenticated'}), 401
        
        data = request.get_json() or {}
        
        # Update onboarding progress for the step
        updated_progress = current_app.onboarding_service.update_onboarding_progress(
            user_id=user_id,
            step_name=step_name,
            is_completed=data.get('completed', True),
            responses=data.get('responses', {})
        )
        
        if updated_progress:
            return jsonify({
                'success': True,
                'message': f'Step {step_name} updated successfully',
                'progress': updated_progress
            }), 200
        else:
            return jsonify({'error': 'Failed to update step'}), 500
            
    except Exception as e:
        logger.error(f"Update step error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500 