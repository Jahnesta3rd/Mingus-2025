"""
Two-Factor Authentication Routes for MINGUS
Handles 2FA setup, verification, backup codes, and recovery
"""

from flask import Blueprint, request, jsonify, current_app, session
from functools import wraps
import logging
from datetime import datetime

from backend.middleware.auth import require_auth
from backend.services.two_factor_service import TwoFactorService
from backend.middleware.rate_limit_decorators import rate_limit

logger = logging.getLogger(__name__)

two_factor_bp = Blueprint('two_factor', __name__, url_prefix='/api/2fa')

def get_2fa_service():
    """Get 2FA service instance"""
    return TwoFactorService(current_app.db_session_factory)

def require_2fa_setup(f):
    """Decorator to require 2FA setup completion"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'Authentication required'}), 401
        
        # Check if 2FA is set up
        service = get_2fa_service()
        status = service.get_2fa_status(user_id)
        
        if not status.get('setup_completed'):
            return jsonify({
                'error': 'Two-factor authentication not set up',
                'message': 'Please complete 2FA setup before accessing this endpoint'
            }), 403
        
        return f(*args, **kwargs)
    return decorated_function

@two_factor_bp.route('/setup', methods=['POST'])
@require_auth
@rate_limit('2fa_setup', max_requests=5, window=300)  # 5 attempts per 5 minutes
def setup_2fa():
    """
    Set up two-factor authentication
    
    POST /api/2fa/setup
    Body: {}
    
    Returns:
        - TOTP secret for manual entry
        - QR code for authenticator apps
        - Backup codes for recovery
    """
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'Authentication required'}), 401
        
        service = get_2fa_service()
        result = service.setup_2fa(user_id, request)
        
        if result['success']:
            # Store setup data in session for verification
            session['2fa_setup_data'] = {
                'totp_secret': result['totp_secret'],
                'qr_code': result['qr_code'],
                'backup_codes': result['backup_codes'],
                'setup_timestamp': datetime.utcnow().isoformat()
            }
            
            return jsonify({
                'success': True,
                'message': result['message'],
                'qr_code': result['qr_code'],
                'totp_uri': result['totp_uri'],
                'backup_codes': result['backup_codes'],
                'next_step': 'Verify with authenticator app or enter TOTP code'
            })
        else:
            return jsonify({
                'success': False,
                'error': result['error']
            }), 400
            
    except Exception as e:
        logger.error(f"Error in 2FA setup: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to set up two-factor authentication'
        }), 500

@two_factor_bp.route('/verify', methods=['POST'])
@require_auth
@rate_limit('2fa_verify', max_requests=10, window=300)  # 10 attempts per 5 minutes
def verify_2fa():
    """
    Verify TOTP code to complete 2FA setup or authenticate
    
    POST /api/2fa/verify
    Body: {
        "totp_code": "123456"
    }
    
    Returns:
        - Success/failure status
        - 2FA enabled status
    """
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'Authentication required'}), 401
        
        data = request.get_json()
        if not data or 'totp_code' not in data:
            return jsonify({
                'success': False,
                'error': 'TOTP code is required'
            }), 400
        
        totp_code = data['totp_code'].strip()
        if not totp_code or len(totp_code) != 6:
            return jsonify({
                'success': False,
                'error': 'Invalid TOTP code format'
            }), 400
        
        service = get_2fa_service()
        result = service.verify_totp(user_id, totp_code, request)
        
        if result['success']:
            # Clear setup data from session
            session.pop('2fa_setup_data', None)
            
            # Mark 2FA as verified in session
            session['2fa_verified'] = True
            
            return jsonify({
                'success': True,
                'message': result['message'],
                'is_enabled': result['is_enabled'],
                'next_step': 'Two-factor authentication is now active'
            })
        else:
            return jsonify({
                'success': False,
                'error': result['error'],
                'remaining_attempts': result.get('remaining_attempts', 0)
            }), 400
            
    except Exception as e:
        logger.error(f"Error in 2FA verification: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to verify two-factor authentication'
        }), 500

@two_factor_bp.route('/backup-code', methods=['POST'])
@require_auth
@rate_limit('2fa_backup', max_requests=5, window=300)  # 5 attempts per 5 minutes
def verify_backup_code():
    """
    Verify backup code for 2FA recovery
    
    POST /api/2fa/backup-code
    Body: {
        "backup_code": "ABCD-1234-EFGH-5678"
    }
    
    Returns:
        - Success/failure status
        - 2FA enabled status
    """
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'Authentication required'}), 401
        
        data = request.get_json()
        if not data or 'backup_code' not in data:
            return jsonify({
                'success': False,
                'error': 'Backup code is required'
            }), 400
        
        backup_code = data['backup_code'].strip()
        if not backup_code:
            return jsonify({
                'success': False,
                'error': 'Invalid backup code format'
            }), 400
        
        service = get_2fa_service()
        result = service.verify_backup_code(user_id, backup_code, request)
        
        if result['success']:
            # Mark 2FA as verified in session
            session['2fa_verified'] = True
            
            return jsonify({
                'success': True,
                'message': result['message'],
                'is_enabled': result['is_enabled'],
                'next_step': 'Access granted using backup code'
            })
        else:
            return jsonify({
                'success': False,
                'error': result['error'],
                'remaining_attempts': result.get('remaining_attempts', 0)
            }), 400
            
    except Exception as e:
        logger.error(f"Error in backup code verification: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to verify backup code'
        }), 500

@two_factor_bp.route('/sms/send', methods=['POST'])
@require_auth
@rate_limit('2fa_sms_send', max_requests=3, window=3600)  # 3 SMS per hour
def send_sms_fallback():
    """
    Send SMS fallback code for 2FA
    
    POST /api/2fa/sms/send
    Body: {}
    
    Returns:
        - Success/failure status
        - Phone number (masked)
    """
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'Authentication required'}), 401
        
        service = get_2fa_service()
        result = service.send_sms_fallback(user_id, request)
        
        if result['success']:
            return jsonify({
                'success': True,
                'message': result['message'],
                'phone_number': result['phone_number'],
                'next_step': 'Enter the SMS code to verify'
            })
        else:
            return jsonify({
                'success': False,
                'error': result['error'],
                'details': result.get('details', '')
            }), 400
            
    except Exception as e:
        logger.error(f"Error sending SMS fallback: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to send SMS fallback'
        }), 500

@two_factor_bp.route('/sms/verify', methods=['POST'])
@require_auth
@rate_limit('2fa_sms_verify', max_requests=5, window=300)  # 5 attempts per 5 minutes
def verify_sms_code():
    """
    Verify SMS fallback code
    
    POST /api/2fa/sms/verify
    Body: {
        "sms_code": "123456"
    }
    
    Returns:
        - Success/failure status
        - 2FA enabled status
    """
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'Authentication required'}), 401
        
        data = request.get_json()
        if not data or 'sms_code' not in data:
            return jsonify({
                'success': False,
                'error': 'SMS code is required'
            }), 400
        
        sms_code = data['sms_code'].strip()
        if not sms_code or len(sms_code) != 6:
            return jsonify({
                'success': False,
                'error': 'Invalid SMS code format'
            }), 400
        
        service = get_2fa_service()
        result = service.verify_sms_code(user_id, sms_code, request)
        
        if result['success']:
            # Mark 2FA as verified in session
            session['2fa_verified'] = True
            
            return jsonify({
                'success': True,
                'message': result['message'],
                'is_enabled': result['is_enabled'],
                'next_step': 'Access granted using SMS code'
            })
        else:
            return jsonify({
                'success': False,
                'error': result['error'],
                'remaining_attempts': result.get('remaining_attempts', 0)
            }), 400
            
    except Exception as e:
        logger.error(f"Error in SMS code verification: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to verify SMS code'
        }), 500

@two_factor_bp.route('/status', methods=['GET'])
@require_auth
def get_2fa_status():
    """
    Get 2FA status for current user
    
    GET /api/2fa/status
    
    Returns:
        - 2FA enabled status
        - Setup completion status
        - SMS fallback status
        - Backup codes remaining
    """
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'Authentication required'}), 401
        
        service = get_2fa_service()
        status = service.get_2fa_status(user_id)
        
        return jsonify({
            'success': True,
            'status': status
        })
        
    except Exception as e:
        logger.error(f"Error getting 2FA status: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to get 2FA status'
        }), 500

@two_factor_bp.route('/disable', methods=['POST'])
@require_auth
@require_2fa_setup
@rate_limit('2fa_disable', max_requests=3, window=3600)  # 3 attempts per hour
def disable_2fa():
    """
    Disable two-factor authentication
    
    POST /api/2fa/disable
    Body: {}
    
    Returns:
        - Success/failure status
    """
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'Authentication required'}), 401
        
        # Require additional verification (could be password or backup code)
        data = request.get_json() or {}
        verification_method = data.get('verification_method', 'password')
        
        if verification_method == 'password':
            # Verify current password
            password = data.get('password')
            if not password:
                return jsonify({
                    'success': False,
                    'error': 'Password required to disable 2FA'
                }), 400
            
            # This would typically verify the password
            # For now, we'll proceed (in production, add password verification)
            pass
        
        service = get_2fa_service()
        result = service.disable_2fa(user_id, request)
        
        if result['success']:
            # Clear 2FA verification from session
            session.pop('2fa_verified', None)
            
            return jsonify({
                'success': True,
                'message': result['message'],
                'next_step': 'Two-factor authentication has been disabled'
            })
        else:
            return jsonify({
                'success': False,
                'error': result['error']
            }), 400
            
    except Exception as e:
        logger.error(f"Error disabling 2FA: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to disable two-factor authentication'
        }), 500

@two_factor_bp.route('/recovery/request', methods=['POST'])
@require_auth
@rate_limit('2fa_recovery_request', max_requests=2, window=86400)  # 2 requests per day
def request_2fa_recovery():
    """
    Request 2FA recovery for lost device
    
    POST /api/2fa/recovery/request
    Body: {
        "recovery_method": "sms|email|admin",
        "reason": "Lost device description"
    }
    
    Returns:
        - Success/failure status
        - Recovery request ID
    """
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'Authentication required'}), 401
        
        data = request.get_json()
        if not data or 'recovery_method' not in data:
            return jsonify({
                'success': False,
                'error': 'Recovery method is required'
            }), 400
        
        recovery_method = data['recovery_method']
        if recovery_method not in ['sms', 'email', 'admin']:
            return jsonify({
                'success': False,
                'error': 'Invalid recovery method'
            }), 400
        
        # For now, return a placeholder response
        # In production, this would create a recovery request
        return jsonify({
            'success': True,
            'message': 'Recovery request submitted successfully',
            'recovery_request_id': f'req_{user_id}_{datetime.utcnow().strftime("%Y%m%d%H%M%S")}',
            'next_step': 'Recovery request is under review'
        })
        
    except Exception as e:
        logger.error(f"Error requesting 2FA recovery: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to submit recovery request'
        }), 500

@two_factor_bp.route('/setup/qr', methods=['GET'])
@require_auth
def get_setup_qr():
    """
    Get QR code for 2FA setup (if setup is in progress)
    
    GET /api/2fa/setup/qr
    
    Returns:
        - QR code data
        - Setup instructions
    """
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'Authentication required'}), 401
        
        # Check if setup is in progress
        setup_data = session.get('2fa_setup_data')
        if not setup_data:
            return jsonify({
                'success': False,
                'error': 'No 2FA setup in progress'
            }), 400
        
        return jsonify({
            'success': True,
            'qr_code': setup_data['qr_code'],
            'totp_uri': setup_data.get('totp_uri', ''),
            'setup_timestamp': setup_data['setup_timestamp'],
            'instructions': [
                '1. Open your authenticator app (Google Authenticator, Authy, etc.)',
                '2. Scan the QR code or manually enter the TOTP secret',
                '3. Enter the 6-digit code from your app to verify',
                '4. Save your backup codes in a secure location'
            ]
        })
        
    except Exception as e:
        logger.error(f"Error getting setup QR: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to get setup QR code'
        }), 500

@two_factor_bp.route('/setup/backup-codes', methods=['GET'])
@require_auth
def get_setup_backup_codes():
    """
    Get backup codes for 2FA setup (if setup is in progress)
    
    GET /api/2fa/setup/backup-codes
    
    Returns:
        - List of backup codes
        - Usage instructions
    """
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'Authentication required'}), 401
        
        # Check if setup is in progress
        setup_data = session.get('2fa_setup_data')
        if not setup_data:
            return jsonify({
                'success': False,
                'error': 'No 2FA setup in progress'
            }), 400
        
        return jsonify({
            'success': True,
            'backup_codes': setup_data['backup_codes'],
            'setup_timestamp': setup_data['setup_timestamp'],
            'instructions': [
                'Save these backup codes in a secure location',
                'Each code can only be used once',
                'Use these codes if you lose access to your authenticator app',
                'Keep them separate from your main device'
            ]
        })
        
    except Exception as e:
        logger.error(f"Error getting backup codes: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to get backup codes'
        }), 500

# Error handlers for the blueprint
@two_factor_bp.errorhandler(429)
def rate_limit_exceeded(error):
    """Handle rate limit exceeded errors"""
    return jsonify({
        'success': False,
        'error': 'Rate limit exceeded',
        'message': 'Too many requests. Please try again later.',
        'retry_after': getattr(error, 'retry_after', 60)
    }), 429

@two_factor_bp.errorhandler(500)
def internal_error(error):
    """Handle internal server errors"""
    logger.error(f"Internal error in 2FA routes: {error}")
    return jsonify({
        'success': False,
        'error': 'Internal server error',
        'message': 'An unexpected error occurred. Please try again later.'
    }), 500
