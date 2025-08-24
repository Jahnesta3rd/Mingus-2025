"""
Bank Connection Flow API Routes for MINGUS

This module provides comprehensive API endpoints for the bank connection flow:
- Secure and intuitive bank account linking experience
- Subscription tier integration with upgrade prompts
- Step-by-step flow management
- Plaid integration with MFA and verification handling
- Progress tracking and analytics
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from flask import Blueprint, request, jsonify, current_app, session
from sqlalchemy.orm import Session
import uuid

from backend.middleware.auth import require_auth
from backend.banking.connection_flow import BankConnectionFlowService
from backend.utils.auth_decorators import handle_api_errors
from backend.services.analytics_service import AnalyticsService

logger = logging.getLogger(__name__)

# Create Blueprint
bank_connection_flow_bp = Blueprint('bank_connection_flow', __name__, url_prefix='/api/bank-connection')

def get_connection_flow_service() -> BankConnectionFlowService:
    """Get bank connection flow service instance"""
    db_session = current_app.db.session
    return BankConnectionFlowService(db_session)

def get_analytics_service() -> AnalyticsService:
    """Get analytics service instance"""
    db_session = current_app.db.session
    return AnalyticsService(db_session)

# ============================================================================
# CONNECTION FLOW MANAGEMENT
# ============================================================================

@bank_connection_flow_bp.route('/start', methods=['POST'])
@require_auth
@handle_api_errors
def start_connection_flow():
    """Start a new bank connection flow"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'User not authenticated'}), 401
        
        # Get request data
        data = request.get_json() or {}
        
        # Get connection flow service
        flow_service = get_connection_flow_service()
        analytics_service = get_analytics_service()
        
        # Start connection flow
        result = flow_service.start_connection_flow(str(user_id))
        
        if not result.success:
            return jsonify({
                'success': False,
                'error': result.error_message
            }), 400
        
        # Track flow start
        analytics_service.track_event(
            user_id=str(user_id),
            event_type="bank_connection_flow_started",
            properties={
                "session_id": result.session_id,
                "step": result.next_step.value if result.next_step else None
            }
        )
        
        response_data = {
            'success': True,
            'session_id': result.session_id,
            'next_step': result.next_step.value if result.next_step else None,
            'current_state': result.current_state.value if result.current_state else None,
            'data': result.data,
            'upgrade_prompt': result.upgrade_prompt
        }
        
        return jsonify(response_data), 200
        
    except Exception as e:
        logger.error(f"Error starting connection flow: {e}")
        return jsonify({'error': 'Failed to start connection flow'}), 500

@bank_connection_flow_bp.route('/<session_id>/proceed', methods=['POST'])
@require_auth
@handle_api_errors
def proceed_to_next_step(session_id: str):
    """Proceed to the next step in the connection flow"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'User not authenticated'}), 401
        
        # Get request data
        data = request.get_json() or {}
        step_data = data.get('step_data', {})
        
        # Get connection flow service
        flow_service = get_connection_flow_service()
        analytics_service = get_analytics_service()
        
        # Proceed to next step
        result = flow_service.proceed_to_next_step(session_id, step_data)
        
        if not result.success:
            return jsonify({
                'success': False,
                'error': result.error_message
            }), 400
        
        # Track step progression
        analytics_service.track_event(
            user_id=str(user_id),
            event_type="bank_connection_step_completed",
            properties={
                "session_id": session_id,
                "next_step": result.next_step.value if result.next_step else None,
                "current_state": result.current_state.value if result.current_state else None
            }
        )
        
        response_data = {
            'success': True,
            'session_id': result.session_id,
            'next_step': result.next_step.value if result.next_step else None,
            'current_state': result.current_state.value if result.current_state else None,
            'data': result.data,
            'upgrade_prompt': result.upgrade_prompt,
            'redirect_url': result.redirect_url
        }
        
        return jsonify(response_data), 200
        
    except Exception as e:
        logger.error(f"Error proceeding to next step for session {session_id}: {e}")
        return jsonify({'error': 'Failed to proceed to next step'}), 500

@bank_connection_flow_bp.route('/<session_id>/plaid-success', methods=['POST'])
@require_auth
@handle_api_errors
def handle_plaid_success(session_id: str):
    """Handle Plaid Link success"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'User not authenticated'}), 401
        
        # Get request data
        data = request.get_json()
        if not data or 'public_token' not in data:
            return jsonify({'error': 'Public token is required'}), 400
        
        public_token = data['public_token']
        metadata = data.get('metadata', {})
        
        # Get connection flow service
        flow_service = get_connection_flow_service()
        analytics_service = get_analytics_service()
        
        # Handle Plaid success
        result = flow_service.handle_plaid_success(session_id, public_token, metadata)
        
        if not result.success:
            return jsonify({
                'success': False,
                'error': result.error_message
            }), 400
        
        # Track Plaid success
        analytics_service.track_event(
            user_id=str(user_id),
            event_type="plaid_link_success",
            properties={
                "session_id": session_id,
                "institution_name": metadata.get('institution', {}).get('name'),
                "accounts_count": len(metadata.get('accounts', [])),
                "requires_mfa": metadata.get('requires_mfa', False)
            }
        )
        
        response_data = {
            'success': True,
            'session_id': result.session_id,
            'next_step': result.next_step.value if result.next_step else None,
            'current_state': result.current_state.value if result.current_state else None,
            'data': result.data,
            'redirect_url': result.redirect_url
        }
        
        return jsonify(response_data), 200
        
    except Exception as e:
        logger.error(f"Error handling Plaid success for session {session_id}: {e}")
        return jsonify({'error': 'Failed to process bank connection'}), 500

@bank_connection_flow_bp.route('/<session_id>/mfa-response', methods=['POST'])
@require_auth
@handle_api_errors
def handle_mfa_response(session_id: str):
    """Handle MFA response"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'User not authenticated'}), 401
        
        # Get request data
        data = request.get_json()
        if not data or 'mfa_answers' not in data:
            return jsonify({'error': 'MFA answers are required'}), 400
        
        mfa_answers = data['mfa_answers']
        
        # Get connection flow service
        flow_service = get_connection_flow_service()
        analytics_service = get_analytics_service()
        
        # Handle MFA response
        result = flow_service.handle_mfa_response(session_id, mfa_answers)
        
        if not result.success:
            return jsonify({
                'success': False,
                'error': result.error_message
            }), 400
        
        # Track MFA completion
        analytics_service.track_event(
            user_id=str(user_id),
            event_type="mfa_completed",
            properties={
                "session_id": session_id,
                "questions_count": len(mfa_answers)
            }
        )
        
        response_data = {
            'success': True,
            'session_id': result.session_id,
            'next_step': result.next_step.value if result.next_step else None,
            'current_state': result.current_state.value if result.current_state else None,
            'data': result.data,
            'redirect_url': result.redirect_url
        }
        
        return jsonify(response_data), 200
        
    except Exception as e:
        logger.error(f"Error handling MFA response for session {session_id}: {e}")
        return jsonify({'error': 'Failed to process MFA response'}), 500

@bank_connection_flow_bp.route('/<session_id>/verification-response', methods=['POST'])
@require_auth
@handle_api_errors
def handle_verification_response(session_id: str):
    """Handle verification response"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'User not authenticated'}), 401
        
        # Get request data
        data = request.get_json()
        if not data or 'verification_data' not in data:
            return jsonify({'error': 'Verification data is required'}), 400
        
        verification_data = data['verification_data']
        
        # Get connection flow service
        flow_service = get_connection_flow_service()
        analytics_service = get_analytics_service()
        
        # Handle verification response
        result = flow_service.handle_verification_response(session_id, verification_data)
        
        if not result.success:
            return jsonify({
                'success': False,
                'error': result.error_message
            }), 400
        
        # Track verification completion
        analytics_service.track_event(
            user_id=str(user_id),
            event_type="verification_completed",
            properties={
                "session_id": session_id,
                "verification_type": verification_data.get('type')
            }
        )
        
        response_data = {
            'success': True,
            'session_id': result.session_id,
            'next_step': result.next_step.value if result.next_step else None,
            'current_state': result.current_state.value if result.current_state else None,
            'data': result.data,
            'redirect_url': result.redirect_url
        }
        
        return jsonify(response_data), 200
        
    except Exception as e:
        logger.error(f"Error handling verification response for session {session_id}: {e}")
        return jsonify({'error': 'Failed to process verification'}), 500

# ============================================================================
# FLOW PROGRESS AND STATUS
# ============================================================================

@bank_connection_flow_bp.route('/<session_id>/progress', methods=['GET'])
@require_auth
@handle_api_errors
def get_flow_progress(session_id: str):
    """Get connection flow progress"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'User not authenticated'}), 401
        
        # Get connection flow service
        flow_service = get_connection_flow_service()
        
        # Get flow progress
        progress = flow_service.get_flow_progress(session_id)
        
        if 'error' in progress:
            return jsonify({
                'success': False,
                'error': progress['error']
            }), 400
        
        return jsonify({
            'success': True,
            'progress': progress
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting flow progress for session {session_id}: {e}")
        return jsonify({'error': 'Failed to get flow progress'}), 500

@bank_connection_flow_bp.route('/<session_id>/status', methods=['GET'])
@require_auth
@handle_api_errors
def get_flow_status(session_id: str):
    """Get connection flow status"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'User not authenticated'}), 401
        
        # Get connection flow service
        flow_service = get_connection_flow_service()
        
        # Get session
        session_obj = flow_service._get_session(session_id)
        if not session_obj:
            return jsonify({
                'success': False,
                'error': 'Session not found or expired'
            }), 404
        
        # Check if session belongs to user
        if session_obj.user_id != str(user_id):
            return jsonify({
                'success': False,
                'error': 'Unauthorized access to session'
            }), 403
        
        status_data = {
            'session_id': session_obj.session_id,
            'current_step': session_obj.current_step.value,
            'current_state': session_obj.current_state.value,
            'institution_name': session_obj.institution_name,
            'accounts_count': len(session_obj.selected_accounts),
            'created_at': session_obj.created_at.isoformat(),
            'updated_at': session_obj.updated_at.isoformat(),
            'expires_at': session_obj.expires_at.isoformat(),
            'has_error': bool(session_obj.error_message),
            'error_message': session_obj.error_message
        }
        
        return jsonify({
            'success': True,
            'status': status_data
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting flow status for session {session_id}: {e}")
        return jsonify({'error': 'Failed to get flow status'}), 500

# ============================================================================
# UPGRADE AND SUBSCRIPTION MANAGEMENT
# ============================================================================

@bank_connection_flow_bp.route('/<session_id>/upgrade', methods=['POST'])
@require_auth
@handle_api_errors
def handle_upgrade_request(session_id: str):
    """Handle upgrade request during connection flow"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'User not authenticated'}), 401
        
        # Get request data
        data = request.get_json()
        if not data or 'upgrade_tier' not in data:
            return jsonify({'error': 'Upgrade tier is required'}), 400
        
        upgrade_tier = data['upgrade_tier']
        start_trial = data.get('start_trial', False)
        
        # Get connection flow service
        flow_service = get_connection_flow_service()
        analytics_service = get_analytics_service()
        
        # Track upgrade request
        analytics_service.track_event(
            user_id=str(user_id),
            event_type="upgrade_requested",
            properties={
                "session_id": session_id,
                "upgrade_tier": upgrade_tier,
                "start_trial": start_trial
            }
        )
        
        # Redirect to billing/upgrade page
        upgrade_url = f"/billing/upgrade?plan={upgrade_tier}&trial={start_trial}&return_url=/bank-connection/{session_id}"
        
        return jsonify({
            'success': True,
            'redirect_url': upgrade_url,
            'message': f'Redirecting to {upgrade_tier} upgrade page'
        }), 200
        
    except Exception as e:
        logger.error(f"Error handling upgrade request for session {session_id}: {e}")
        return jsonify({'error': 'Failed to process upgrade request'}), 500

@bank_connection_flow_bp.route('/<session_id>/skip-upgrade', methods=['POST'])
@require_auth
@handle_api_errors
def skip_upgrade(session_id: str):
    """Skip upgrade and continue with current tier"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'User not authenticated'}), 401
        
        # Get connection flow service
        flow_service = get_connection_flow_service()
        analytics_service = get_analytics_service()
        
        # Track upgrade skip
        analytics_service.track_event(
            user_id=str(user_id),
            event_type="upgrade_skipped",
            properties={
                "session_id": session_id
            }
        )
        
        # Proceed to next step (skip upgrade)
        result = flow_service.proceed_to_next_step(session_id, {'skip_upgrade': True})
        
        if not result.success:
            return jsonify({
                'success': False,
                'error': result.error_message
            }), 400
        
        response_data = {
            'success': True,
            'session_id': result.session_id,
            'next_step': result.next_step.value if result.next_step else None,
            'current_state': result.current_state.value if result.current_state else None,
            'data': result.data,
            'message': 'Continuing with current subscription tier'
        }
        
        return jsonify(response_data), 200
        
    except Exception as e:
        logger.error(f"Error skipping upgrade for session {session_id}: {e}")
        return jsonify({'error': 'Failed to skip upgrade'}), 500

# ============================================================================
# SESSION MANAGEMENT
# ============================================================================

@bank_connection_flow_bp.route('/<session_id>/cancel', methods=['POST'])
@require_auth
@handle_api_errors
def cancel_connection_flow(session_id: str):
    """Cancel connection flow"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'User not authenticated'}), 401
        
        # Get connection flow service
        flow_service = get_connection_flow_service()
        analytics_service = get_analytics_service()
        
        # Get session
        session_obj = flow_service._get_session(session_id)
        if not session_obj:
            return jsonify({
                'success': False,
                'error': 'Session not found or expired'
            }), 404
        
        # Check if session belongs to user
        if session_obj.user_id != str(user_id):
            return jsonify({
                'success': False,
                'error': 'Unauthorized access to session'
            }), 403
        
        # Track flow cancellation
        analytics_service.track_event(
            user_id=str(user_id),
            event_type="bank_connection_flow_cancelled",
            properties={
                "session_id": session_id,
                "current_step": session_obj.current_step.value,
                "current_state": session_obj.current_state.value
            }
        )
        
        # Remove session
        if session_id in flow_service.sessions:
            del flow_service.sessions[session_id]
        
        return jsonify({
            'success': True,
            'message': 'Connection flow cancelled successfully',
            'redirect_url': '/dashboard'
        }), 200
        
    except Exception as e:
        logger.error(f"Error cancelling connection flow for session {session_id}: {e}")
        return jsonify({'error': 'Failed to cancel connection flow'}), 500

@bank_connection_flow_bp.route('/<session_id>/extend', methods=['POST'])
@require_auth
@handle_api_errors
def extend_session(session_id: str):
    """Extend session expiration time"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'User not authenticated'}), 401
        
        # Get connection flow service
        flow_service = get_connection_flow_service()
        
        # Get session
        session_obj = flow_service._get_session(session_id)
        if not session_obj:
            return jsonify({
                'success': False,
                'error': 'Session not found or expired'
            }), 404
        
        # Check if session belongs to user
        if session_obj.user_id != str(user_id):
            return jsonify({
                'success': False,
                'error': 'Unauthorized access to session'
            }), 403
        
        # Extend session by 1 hour
        from datetime import timedelta
        session_obj.expires_at = datetime.utcnow() + timedelta(hours=1)
        session_obj.updated_at = datetime.utcnow()
        
        return jsonify({
            'success': True,
            'message': 'Session extended successfully',
            'new_expires_at': session_obj.expires_at.isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Error extending session {session_id}: {e}")
        return jsonify({'error': 'Failed to extend session'}), 500

# ============================================================================
# UTILITY ENDPOINTS
# ============================================================================

@bank_connection_flow_bp.route('/supported-banks', methods=['GET'])
@require_auth
@handle_api_errors
def get_supported_banks():
    """Get list of supported banks"""
    try:
        # Get connection flow service
        flow_service = get_connection_flow_service()
        
        banks = flow_service._get_supported_banks()
        search_tips = flow_service._get_search_tips()
        
        return jsonify({
            'success': True,
            'banks': banks,
            'search_tips': search_tips,
            'total_count': len(banks)
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting supported banks: {e}")
        return jsonify({'error': 'Failed to get supported banks'}), 500

@bank_connection_flow_bp.route('/connection-benefits', methods=['GET'])
@require_auth
@handle_api_errors
def get_connection_benefits():
    """Get connection benefits information"""
    try:
        # Get connection flow service
        flow_service = get_connection_flow_service()
        
        benefits = flow_service._get_connection_benefits()
        security_info = flow_service._get_security_info()
        
        return jsonify({
            'success': True,
            'benefits': benefits,
            'security_info': security_info
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting connection benefits: {e}")
        return jsonify({'error': 'Failed to get connection benefits'}), 500

@bank_connection_flow_bp.route('/cleanup', methods=['POST'])
@require_auth
@handle_api_errors
def cleanup_expired_sessions():
    """Clean up expired sessions (admin only)"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'User not authenticated'}), 401
        
        # TODO: Add admin check here
        # For now, allow any authenticated user to cleanup
        
        # Get connection flow service
        flow_service = get_connection_flow_service()
        
        # Cleanup expired sessions
        flow_service.cleanup_expired_sessions()
        
        return jsonify({
            'success': True,
            'message': 'Expired sessions cleaned up successfully'
        }), 200
        
    except Exception as e:
        logger.error(f"Error cleaning up expired sessions: {e}")
        return jsonify({'error': 'Failed to cleanup expired sessions'}), 500 