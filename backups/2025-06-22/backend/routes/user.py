"""
User routes blueprint
"""

from flask import Blueprint, request, jsonify, session, current_app
from loguru import logger

user_bp = Blueprint('user', __name__)

@user_bp.route('/me', methods=['GET'])
def get_current_user():
    """Get current user information"""
    try:
        user_id = session.get('user_id')
        
        if not user_id:
            return jsonify({'error': 'Not authenticated'}), 401
        
        # Get user data
        user = current_app.user_service.get_user_by_id(user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        return jsonify({
            'success': True,
            'user': user
        }), 200
        
    except Exception as e:
        logger.error(f"Get current user error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@user_bp.route('/me', methods=['PUT'])
def update_current_user():
    """Update current user information"""
    try:
        user_id = session.get('user_id')
        
        if not user_id:
            return jsonify({'error': 'Not authenticated'}), 401
        
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Update user data
        updated_user = current_app.user_service.update_user(user_id, data)
        
        if updated_user:
            return jsonify({
                'success': True,
                'message': 'User updated successfully',
                'user': updated_user
            }), 200
        else:
            return jsonify({'error': 'Failed to update user'}), 500
            
    except Exception as e:
        logger.error(f"Update current user error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@user_bp.route('/profile', methods=['GET'])
def get_user_profile():
    """Get current user profile"""
    try:
        user_id = session.get('user_id')
        
        if not user_id:
            return jsonify({'error': 'Not authenticated'}), 401
        
        # Get user profile
        profile = current_app.onboarding_service.get_user_profile(user_id)
        
        if profile:
            return jsonify({
                'success': True,
                'profile': profile
            }), 200
        else:
            return jsonify({'error': 'Profile not found'}), 404
            
    except Exception as e:
        logger.error(f"Get user profile error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@user_bp.route('/profile', methods=['PUT'])
def update_user_profile():
    """Update current user profile"""
    try:
        user_id = session.get('user_id')
        
        if not user_id:
            return jsonify({'error': 'Not authenticated'}), 401
        
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Update user profile
        updated_profile = current_app.onboarding_service.update_user_profile(user_id, data)
        
        if updated_profile:
            return jsonify({
                'success': True,
                'message': 'Profile updated successfully',
                'profile': updated_profile
            }), 200
        else:
            return jsonify({'error': 'Failed to update profile'}), 500
            
    except Exception as e:
        logger.error(f"Update user profile error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@user_bp.route('/onboarding', methods=['GET'])
def get_user_onboarding():
    """Get current user onboarding progress"""
    try:
        user_id = session.get('user_id')
        
        if not user_id:
            return jsonify({'error': 'Not authenticated'}), 401
        
        # Get onboarding progress
        progress = current_app.onboarding_service.get_onboarding_progress(user_id)
        
        if progress:
            return jsonify({
                'success': True,
                'onboarding': progress
            }), 200
        else:
            return jsonify({'error': 'Onboarding progress not found'}), 404
            
    except Exception as e:
        logger.error(f"Get user onboarding error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@user_bp.route('/dashboard', methods=['GET'])
def get_user_dashboard():
    """Get user dashboard data"""
    try:
        user_id = session.get('user_id')
        
        if not user_id:
            return jsonify({'error': 'Not authenticated'}), 401
        
        # Get all user data
        user = current_app.user_service.get_user_by_id(user_id)
        profile = current_app.onboarding_service.get_user_profile(user_id)
        onboarding_progress = current_app.onboarding_service.get_onboarding_progress(user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        return jsonify({
            'success': True,
            'dashboard': {
                'user': user,
                'profile': profile,
                'onboarding_progress': onboarding_progress
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Get user dashboard error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@user_bp.route('/deactivate', methods=['POST'])
def deactivate_user():
    """Deactivate current user account"""
    try:
        user_id = session.get('user_id')
        
        if not user_id:
            return jsonify({'error': 'Not authenticated'}), 401
        
        # Deactivate user
        success = current_app.user_service.deactivate_user(user_id)
        
        if success:
            # Clear session
            session.clear()
            
            return jsonify({
                'success': True,
                'message': 'Account deactivated successfully'
            }), 200
        else:
            return jsonify({'error': 'Failed to deactivate account'}), 500
            
    except Exception as e:
        logger.error(f"Deactivate user error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@user_bp.route('/search', methods=['GET'])
def search_users():
    """Search users (admin only)"""
    try:
        user_id = session.get('user_id')
        
        if not user_id:
            return jsonify({'error': 'Not authenticated'}), 401
        
        # For now, this is a placeholder for admin functionality
        # In production, you would add admin role checks here
        
        query = request.args.get('q', '')
        limit = int(request.args.get('limit', 10))
        
        # This would be implemented in the UserService
        # users = current_app.user_service.search_users(query, limit)
        
        return jsonify({
            'success': True,
            'message': 'Search functionality not implemented yet',
            'query': query,
            'limit': limit
        }), 200
        
    except Exception as e:
        logger.error(f"Search users error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@user_bp.route('/stats', methods=['GET'])
def get_user_stats():
    """Get user statistics (admin only)"""
    try:
        user_id = session.get('user_id')
        
        if not user_id:
            return jsonify({'error': 'Not authenticated'}), 401
        
        # For now, this is a placeholder for admin functionality
        # In production, you would add admin role checks here
        
        return jsonify({
            'success': True,
            'message': 'Statistics functionality not implemented yet'
        }), 200
        
    except Exception as e:
        logger.error(f"Get user stats error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500 