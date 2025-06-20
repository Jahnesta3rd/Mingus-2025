"""
Example integration of OnboardingService with Flask application
"""

from flask import Flask, request, jsonify, session
from backend.services.onboarding_service import OnboardingService
from backend.services.user_service import UserService
import os
from loguru import logger

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'your-secret-key-here')

# Database configuration
DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql://username:password@localhost/mingus_db')

# Initialize services
user_service = UserService(DATABASE_URL)
onboarding_service = OnboardingService(None, DATABASE_URL)  # None for supabase_client since we're using SQLAlchemy

@app.route('/api/onboarding/start', methods=['POST'])
def start_onboarding():
    """Start onboarding process for a user"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        
        if not user_id:
            return jsonify({'error': 'User ID is required'}), 400
        
        # Create onboarding record
        onboarding_record = onboarding_service.create_onboarding_record({
            'user_id': user_id,
            'current_step': 'welcome'
        })
        
        if onboarding_record:
            return jsonify({
                'success': True,
                'onboarding_record': onboarding_record
            }), 201
        else:
            return jsonify({'error': 'Failed to create onboarding record'}), 500
            
    except Exception as e:
        logger.error(f"Error starting onboarding: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/onboarding/profile', methods=['POST'])
def create_profile():
    """Create user profile during onboarding"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        
        if not user_id:
            return jsonify({'error': 'User ID is required'}), 400
        
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
        
        profile = onboarding_service.create_user_profile(profile_data)
        
        if profile:
            # Update onboarding progress
            onboarding_service.update_onboarding_progress(
                user_id=user_id,
                step_name='profile',
                is_completed=True,
                responses=data
            )
            
            return jsonify({
                'success': True,
                'profile': profile
            }), 201
        else:
            return jsonify({'error': 'Failed to create profile'}), 500
            
    except Exception as e:
        logger.error(f"Error creating profile: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/onboarding/goals', methods=['POST'])
def set_goals():
    """Set financial goals during onboarding"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        
        if not user_id:
            return jsonify({'error': 'User ID is required'}), 400
        
        # Update profile with goals
        goals_data = {
            'primary_goal': data.get('primary_goal'),
            'goal_amount': data.get('goal_amount'),
            'goal_timeline_months': data.get('goal_timeline_months')
        }
        
        updated_profile = onboarding_service.update_user_profile(user_id, goals_data)
        
        if updated_profile:
            # Update onboarding progress
            onboarding_service.update_onboarding_progress(
                user_id=user_id,
                step_name='goals',
                is_completed=True,
                responses=data
            )
            
            return jsonify({
                'success': True,
                'profile': updated_profile
            }), 200
        else:
            return jsonify({'error': 'Failed to update profile with goals'}), 500
            
    except Exception as e:
        logger.error(f"Error setting goals: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/onboarding/preferences', methods=['POST'])
def set_preferences():
    """Set user preferences during onboarding"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        
        if not user_id:
            return jsonify({'error': 'User ID is required'}), 400
        
        # Update profile with preferences
        preferences_data = {
            'risk_tolerance': data.get('risk_tolerance'),
            'investment_experience': data.get('investment_experience')
        }
        
        updated_profile = onboarding_service.update_user_profile(user_id, preferences_data)
        
        if updated_profile:
            # Update onboarding progress
            onboarding_service.update_onboarding_progress(
                user_id=user_id,
                step_name='preferences',
                is_completed=True,
                responses=data
            )
            
            return jsonify({
                'success': True,
                'profile': updated_profile
            }), 200
        else:
            return jsonify({'error': 'Failed to update profile with preferences'}), 500
            
    except Exception as e:
        logger.error(f"Error setting preferences: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/onboarding/complete', methods=['POST'])
def complete_onboarding():
    """Complete onboarding process"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        
        if not user_id:
            return jsonify({'error': 'User ID is required'}), 400
        
        # Mark profile as complete
        onboarding_service.update_user_profile(user_id, {'is_complete': True})
        
        # Update onboarding progress to complete
        onboarding_service.update_onboarding_progress(
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
        logger.error(f"Error completing onboarding: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/onboarding/progress/<user_id>', methods=['GET'])
def get_onboarding_progress(user_id):
    """Get onboarding progress for a user"""
    try:
        progress = onboarding_service.get_onboarding_progress(user_id)
        profile = onboarding_service.get_user_profile(user_id)
        
        if progress:
            return jsonify({
                'success': True,
                'progress': progress,
                'profile': profile
            }), 200
        else:
            return jsonify({'error': 'Onboarding progress not found'}), 404
            
    except Exception as e:
        logger.error(f"Error getting onboarding progress: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/onboarding/expenses', methods=['POST'])
def set_expenses():
    """Set expense categories during onboarding"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        expense_categories = data.get('expense_categories', {})
        
        if not user_id:
            return jsonify({'error': 'User ID is required'}), 400
        
        # Update profile with expense categories
        updated_profile = onboarding_service.update_user_profile(user_id, {
            'expense_categories': expense_categories
        })
        
        if updated_profile:
            return jsonify({
                'success': True,
                'profile': updated_profile
            }), 200
        else:
            return jsonify({'error': 'Failed to update expense categories'}), 500
            
    except Exception as e:
        logger.error(f"Error setting expenses: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

# Example usage in registration flow
@app.route('/api/register', methods=['POST'])
def register_user():
    """Register new user and start onboarding"""
    try:
        data = request.get_json()
        
        # Create user account
        user_data = {
            'email': data.get('email'),
            'password': data.get('password'),
            'full_name': data.get('full_name'),
            'phone_number': data.get('phone_number')
        }
        
        user = user_service.create_user(user_data)
        
        if user:
            user_id = user['id']
            
            # Start onboarding process
            onboarding_record = onboarding_service.create_onboarding_record({
                'user_id': user_id,
                'current_step': 'welcome'
            })
            
            # Create initial profile
            profile = onboarding_service.create_user_profile({
                'user_id': user_id
            })
            
            return jsonify({
                'success': True,
                'user': user,
                'onboarding_record': onboarding_record,
                'profile': profile
            }), 201
        else:
            return jsonify({'error': 'Failed to create user account'}), 500
            
    except Exception as e:
        logger.error(f"Error registering user: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5002) 