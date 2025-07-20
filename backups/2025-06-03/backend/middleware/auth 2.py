from functools import wraps
from flask import request, jsonify, current_app
import jwt
from loguru import logger

def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({"error": "No authorization token provided"}), 401

        try:
            # Extract token from Bearer token
            token = auth_header.split(' ')[1]

            # In test mode, accept any token with 'test-user' as subject
            if current_app.config.get('TESTING'):
                try:
                    decoded = jwt.decode(token, options={"verify_signature": False})
                    if decoded.get('sub') == 'test-user':
                        request.user_id = 'test-user'
                        return f(*args, **kwargs)
                except jwt.InvalidTokenError:
                    pass

            # For production, verify the token properly
            decoded = jwt.decode(
                token,
                current_app.config.get('JWT_SECRET_KEY', 'your-secret-key'),
                algorithms=['HS256']
            )
            request.user_id = decoded['sub']
            return f(*args, **kwargs)

        except jwt.ExpiredSignatureError:
            logger.error("JWT token has expired")
            return jsonify({"error": "Token has expired"}), 401
        except jwt.InvalidTokenError as e:
            logger.error(f"JWT validation error: {str(e)}")
            return jsonify({"error": "Invalid token"}), 401

    return decorated 