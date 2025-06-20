from functools import wraps
from flask import request, jsonify, current_app, session
import logging

logger = logging.getLogger(__name__)

def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        # Check if user is logged in via session
        if not session.get('user_id'):
            logger.error("No session found - user not logged in")
            return jsonify({"error": "Authentication required"}), 401
            
        try:
            # Get user info from session
            user_id = session.get('user_id')
            email = session.get('email')
            
            if not user_id or not email:
                logger.error("Invalid session data")
                return jsonify({"error": "Invalid session"}), 401
                
            # Add user info to request context
            request.user = {
                'id': user_id,
                'email': email
            }
            
            logger.debug(f"Session validated for user {email}")
            return f(*args, **kwargs)
            
        except Exception as e:
            logger.error(f"Session validation error: {str(e)}")
            return jsonify({"error": "Session validation failed"}), 401
            
    return decorated 