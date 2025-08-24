"""
Security Utilities
Authorization and access control utilities for API endpoints
"""

from functools import wraps
from flask import request, jsonify, g, current_app
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request
import logging
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)

def require_financial_access(f):
    """
    Decorator to require financial data access permissions
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            # Verify JWT token
            verify_jwt_in_request()
            current_user_id = get_jwt_identity()
            
            # Check if user has financial access
            if not has_financial_access(current_user_id):
                return jsonify({
                    'error': 'FinancialAccessError',
                    'message': 'Financial data access not granted',
                    'details': 'Please complete financial onboarding to access this feature'
                }), 403
            
            return f(*args, **kwargs)
            
        except Exception as e:
            logger.error(f"Financial access check error: {str(e)}")
            return jsonify({
                'error': 'AuthorizationError',
                'message': 'Authorization check failed'
            }), 401
    
    return decorated_function

def require_admin_access(f):
    """
    Decorator to require admin access
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            # Verify JWT token
            verify_jwt_in_request()
            current_user_id = get_jwt_identity()
            
            # Check if user is admin
            if not is_admin(current_user_id):
                return jsonify({
                    'error': 'AdminAccessError',
                    'message': 'Admin access required',
                    'details': 'This endpoint requires administrator privileges'
                }), 403
            
            return f(*args, **kwargs)
            
        except Exception as e:
            logger.error(f"Admin access check error: {str(e)}")
            return jsonify({
                'error': 'AuthorizationError',
                'message': 'Authorization check failed'
            }), 401
    
    return decorated_function

def require_premium_access(f):
    """
    Decorator to require premium subscription access
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            # Verify JWT token
            verify_jwt_in_request()
            current_user_id = get_jwt_identity()
            
            # Check if user has premium access
            if not has_premium_access(current_user_id):
                return jsonify({
                    'error': 'PremiumAccessError',
                    'message': 'Premium subscription required',
                    'details': 'This feature requires a premium subscription'
                }), 403
            
            return f(*args, **kwargs)
            
        except Exception as e:
            logger.error(f"Premium access check error: {str(e)}")
            return jsonify({
                'error': 'AuthorizationError',
                'message': 'Authorization check failed'
            }), 401
    
    return decorated_function

def require_verification(f):
    """
    Decorator to require email verification
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            # Verify JWT token
            verify_jwt_in_request()
            current_user_id = get_jwt_identity()
            
            # Check if user email is verified
            if not is_email_verified(current_user_id):
                return jsonify({
                    'error': 'VerificationError',
                    'message': 'Email verification required',
                    'details': 'Please verify your email address to access this feature'
                }), 403
            
            return f(*args, **kwargs)
            
        except Exception as e:
            logger.error(f"Verification check error: {str(e)}")
            return jsonify({
                'error': 'AuthorizationError',
                'message': 'Authorization check failed'
            }), 401
    
    return decorated_function

def require_2fa(f):
    """
    Decorator to require two-factor authentication
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            # Verify JWT token
            verify_jwt_in_request()
            current_user_id = get_jwt_identity()
            
            # Check if 2FA is enabled and verified
            if not is_2fa_verified(current_user_id):
                return jsonify({
                    'error': 'TwoFactorError',
                    'message': 'Two-factor authentication required',
                    'details': 'Please complete two-factor authentication'
                }), 403
            
            return f(*args, **kwargs)
            
        except Exception as e:
            logger.error(f"2FA check error: {str(e)}")
            return jsonify({
                'error': 'AuthorizationError',
                'message': 'Authorization check failed'
            }), 401
    
    return decorated_function

def check_resource_ownership(resource_type: str, resource_id_param: str = 'id'):
    """
    Decorator to check if user owns the resource they're trying to access
    
    Args:
        resource_type: Type of resource (e.g., 'transaction', 'budget')
        resource_id_param: Name of the parameter containing the resource ID
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                # Verify JWT token
                verify_jwt_in_request()
                current_user_id = get_jwt_identity()
                
                # Get resource ID from kwargs
                resource_id = kwargs.get(resource_id_param)
                if not resource_id:
                    return jsonify({
                        'error': 'ResourceError',
                        'message': f'{resource_type} ID not provided'
                    }), 400
                
                # Check resource ownership
                if not owns_resource(current_user_id, resource_type, resource_id):
                    return jsonify({
                        'error': 'ResourceAccessError',
                        'message': f'Access denied to {resource_type}',
                        'details': f'You do not have permission to access this {resource_type}'
                    }), 403
                
                return f(*args, **kwargs)
                
            except Exception as e:
                logger.error(f"Resource ownership check error: {str(e)}")
                return jsonify({
                    'error': 'AuthorizationError',
                    'message': 'Authorization check failed'
                }), 401
        
        return decorated_function
    return decorator

def has_financial_access(user_id: int) -> bool:
    """
    Check if user has financial data access
    
    Args:
        user_id: User ID
        
    Returns:
        True if user has financial access, False otherwise
    """
    try:
        # Import here to avoid circular imports
        from ..services.auth_service import AuthService
        
        auth_service = AuthService()
        user = auth_service.get_user_by_id(user_id)
        
        if not user:
            return False
        
        # Check if user has completed financial onboarding
        return user.financial_onboarding_completed or user.is_admin
        
    except Exception as e:
        logger.error(f"Error checking financial access: {str(e)}")
        return False

def is_admin(user_id: int) -> bool:
    """
    Check if user is an admin
    
    Args:
        user_id: User ID
        
    Returns:
        True if user is admin, False otherwise
    """
    try:
        from ..services.auth_service import AuthService
        
        auth_service = AuthService()
        user = auth_service.get_user_by_id(user_id)
        
        if not user:
            return False
        
        return user.is_admin
        
    except Exception as e:
        logger.error(f"Error checking admin status: {str(e)}")
        return False

def has_premium_access(user_id: int) -> bool:
    """
    Check if user has premium subscription access
    
    Args:
        user_id: User ID
        
    Returns:
        True if user has premium access, False otherwise
    """
    try:
        from ..services.auth_service import AuthService
        
        auth_service = AuthService()
        user = auth_service.get_user_by_id(user_id)
        
        if not user:
            return False
        
        # Check if user has active premium subscription
        return user.has_premium_subscription or user.is_admin
        
    except Exception as e:
        logger.error(f"Error checking premium access: {str(e)}")
        return False

def is_email_verified(user_id: int) -> bool:
    """
    Check if user email is verified
    
    Args:
        user_id: User ID
        
    Returns:
        True if email is verified, False otherwise
    """
    try:
        from ..services.auth_service import AuthService
        
        auth_service = AuthService()
        user = auth_service.get_user_by_id(user_id)
        
        if not user:
            return False
        
        return user.email_verified
        
    except Exception as e:
        logger.error(f"Error checking email verification: {str(e)}")
        return False

def is_2fa_verified(user_id: int) -> bool:
    """
    Check if user has completed 2FA verification
    
    Args:
        user_id: User ID
        
    Returns:
        True if 2FA is verified, False otherwise
    """
    try:
        from ..services.auth_service import AuthService
        
        auth_service = AuthService()
        user = auth_service.get_user_by_id(user_id)
        
        if not user:
            return False
        
        # Check if 2FA is enabled and verified for this session
        return user.two_factor_enabled and getattr(g, 'two_factor_verified', False)
        
    except Exception as e:
        logger.error(f"Error checking 2FA verification: {str(e)}")
        return False

def owns_resource(user_id: int, resource_type: str, resource_id: int) -> bool:
    """
    Check if user owns the specified resource
    
    Args:
        user_id: User ID
        resource_type: Type of resource
        resource_id: Resource ID
        
    Returns:
        True if user owns the resource, False otherwise
    """
    try:
        if resource_type == 'transaction':
            from ..services.financial_service import FinancialService
            financial_service = FinancialService()
            transaction = financial_service.get_transaction(resource_id, user_id)
            return transaction is not None
            
        elif resource_type == 'budget':
            from ..services.financial_service import FinancialService
            financial_service = FinancialService()
            budget = financial_service.get_budget(resource_id, user_id)
            return budget is not None
            
        elif resource_type == 'account':
            from ..services.financial_service import FinancialService
            financial_service = FinancialService()
            account = financial_service.get_account(resource_id, user_id)
            return account is not None
            
        elif resource_type == 'user':
            # Users can only access their own profile
            return user_id == resource_id
            
        else:
            logger.warning(f"Unknown resource type: {resource_type}")
            return False
            
    except Exception as e:
        logger.error(f"Error checking resource ownership: {str(e)}")
        return False

def get_user_permissions(user_id: int) -> List[str]:
    """
    Get user permissions
    
    Args:
        user_id: User ID
        
    Returns:
        List of permission strings
    """
    try:
        from ..services.auth_service import AuthService
        
        auth_service = AuthService()
        user = auth_service.get_user_by_id(user_id)
        
        if not user:
            return []
        
        permissions = []
        
        # Basic permissions
        permissions.append('read_profile')
        permissions.append('update_profile')
        
        # Financial permissions
        if has_financial_access(user_id):
            permissions.extend([
                'read_transactions',
                'create_transactions',
                'update_transactions',
                'delete_transactions',
                'read_budgets',
                'create_budgets',
                'update_budgets',
                'delete_budgets',
                'read_accounts',
                'create_accounts',
                'update_accounts',
                'delete_accounts',
                'read_analytics',
                'export_data'
            ])
        
        # Premium permissions
        if has_premium_access(user_id):
            permissions.extend([
                'advanced_analytics',
                'priority_support',
                'custom_categories',
                'bulk_operations'
            ])
        
        # Admin permissions
        if is_admin(user_id):
            permissions.extend([
                'admin_dashboard',
                'user_management',
                'system_settings',
                'audit_logs',
                'financial_reports'
            ])
        
        return permissions
        
    except Exception as e:
        logger.error(f"Error getting user permissions: {str(e)}")
        return []

def check_permission(user_id: int, permission: str) -> bool:
    """
    Check if user has specific permission
    
    Args:
        user_id: User ID
        permission: Permission to check
        
    Returns:
        True if user has permission, False otherwise
    """
    permissions = get_user_permissions(user_id)
    return permission in permissions

def require_permission(permission: str):
    """
    Decorator to require specific permission
    
    Args:
        permission: Required permission
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                # Verify JWT token
                verify_jwt_in_request()
                current_user_id = get_jwt_identity()
                
                # Check permission
                if not check_permission(current_user_id, permission):
                    return jsonify({
                        'error': 'PermissionError',
                        'message': f'Permission "{permission}" required',
                        'details': 'You do not have the required permission to access this resource'
                    }), 403
                
                return f(*args, **kwargs)
                
            except Exception as e:
                logger.error(f"Permission check error: {str(e)}")
                return jsonify({
                    'error': 'AuthorizationError',
                    'message': 'Authorization check failed'
                }), 401
        
        return decorated_function
    return decorator

def log_security_event(user_id: int, event_type: str, details: Dict[str, Any] = None):
    """
    Log security-related events
    
    Args:
        user_id: User ID
        event_type: Type of security event
        details: Additional event details
    """
    try:
        from ..services.audit_service import AuditService
        
        audit_service = AuditService()
        audit_service.log_security_event(
            user_id=user_id,
            event_type=event_type,
            details=details or {},
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent', '')
        )
        
    except Exception as e:
        logger.error(f"Error logging security event: {str(e)}")

def validate_api_key(api_key: str) -> bool:
    """
    Validate API key for external integrations
    
    Args:
        api_key: API key to validate
        
    Returns:
        True if API key is valid, False otherwise
    """
    try:
        # Import here to avoid circular imports
        from ..services.auth_service import AuthService
        
        auth_service = AuthService()
        return auth_service.validate_api_key(api_key)
        
    except Exception as e:
        logger.error(f"Error validating API key: {str(e)}")
        return False

def require_api_key(f):
    """
    Decorator to require valid API key
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            # Get API key from header
            api_key = request.headers.get('X-API-Key')
            if not api_key:
                return jsonify({
                    'error': 'APIKeyError',
                    'message': 'API key required',
                    'details': 'Please provide a valid API key in the X-API-Key header'
                }), 401
            
            # Validate API key
            if not validate_api_key(api_key):
                return jsonify({
                    'error': 'APIKeyError',
                    'message': 'Invalid API key',
                    'details': 'The provided API key is invalid or expired'
                }), 401
            
            return f(*args, **kwargs)
            
        except Exception as e:
            logger.error(f"API key validation error: {str(e)}")
            return jsonify({
                'error': 'AuthorizationError',
                'message': 'API key validation failed'
            }), 401
    
    return decorated_function 