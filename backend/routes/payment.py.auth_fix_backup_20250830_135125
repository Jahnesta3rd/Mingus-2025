"""
MINGUS Application - Payment Routes
==================================

API routes for payment processing and subscription management.

Features:
- Customer management endpoints
- Subscription creation and management
- Payment processing
- Webhook handling
- Billing and invoice management

Author: MINGUS Development Team
Date: January 2025
"""

import os
import logging
import uuid
from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
from werkzeug.exceptions import BadRequest, Unauthorized, InternalServerError
from typing import Dict, Any, Optional

from ..payment.stripe_integration import StripeService, SubscriptionTier
from ..payment.payment_models import PaymentError, PaymentStatus
from ..services.user_service import UserService
from ..middleware.auth import require_auth
from ..utils.auth_decorators import admin_required
from ..config.stripe import validate_stripe_environment, get_stripe_environment_info
from ..security.stripe_security import get_stripe_security_manager

# Configure logging
logger = logging.getLogger(__name__)

# Create blueprint
payment_bp = Blueprint('payment', __name__, url_prefix='/api/payment')

# Initialize services
stripe_service = None
user_service = None


def init_payment_services():
    """Initialize payment services."""
    global stripe_service, user_service, security_manager
    
    if stripe_service is None:
        stripe_service = StripeService()
    
    if user_service is None:
        user_service = UserService()
    
    if security_manager is None:
        security_manager = get_stripe_security_manager()


@payment_bp.before_request
def before_request():
    """Initialize services before each request."""
    init_payment_services()


# =====================================================
# CUSTOMER MANAGEMENT ENDPOINTS
# =====================================================

@payment_bp.route('/customers', methods=['POST'])
@login_required
def create_customer():
    """
    Create a new Stripe customer for the current user.
    
    Request body:
    {
        "name": "John Doe",
        "phone": "+1234567890",
        "metadata": {"user_id": "uuid"}
    }
    
    Returns:
    {
        "success": true,
        "customer": {
            "id": "cus_xxx",
            "email": "user@example.com",
            "name": "John Doe",
            ...
        }
    }
    """
    try:
        data = request.get_json() or {}
        
        # Get user information
        user = current_user
        if not user or not user.email:
            raise Unauthorized("User not authenticated or email not found")
        
        # Create customer metadata
        metadata = data.get('metadata', {})
        metadata.update({
            'user_id': str(user.id),
            'mingus_user': 'true'
        })
        
        # Get request information for security
        user_id = str(user.id)
        source_ip = request.remote_addr
        user_agent = request.headers.get('User-Agent', '')
        request_id = request.headers.get('X-Request-ID', str(uuid.uuid4()))
        
        # Create Stripe customer with enhanced security
        customer = stripe_service.create_customer(
            email=user.email,
            name=data.get('name'),
            phone=data.get('phone'),
            metadata=metadata,
            user_id=user_id,
            source_ip=source_ip,
            user_agent=user_agent,
            request_id=request_id
        )
        
        # Update user with Stripe customer ID
        user_service.update_user_stripe_customer_id(user.id, customer.id)
        
        logger.info(f"Created Stripe customer {customer.id} for user {user.id}")
        
        # Add security headers
        response = jsonify({
            'success': True,
            'customer': customer.to_dict()
        }), 201
        
        # Add security headers
        security_headers = security_manager.get_security_headers()
        rate_limit_headers = security_manager.get_rate_limit_headers('customer', user_id)
        
        for key, value in {**security_headers, **rate_limit_headers}.items():
            response[0].headers[key] = value
        
        return response
        
    except Exception as e:
        logger.error(f"Failed to create customer: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@payment_bp.route('/customers/me', methods=['GET'])
@login_required
def get_my_customer():
    """
    Get the current user's Stripe customer information.
    
    Returns:
    {
        "success": true,
        "customer": {
            "id": "cus_xxx",
            "email": "user@example.com",
            ...
        }
    }
    """
    try:
        user = current_user
        if not user.stripe_customer_id:
            return jsonify({
                'success': False,
                'error': 'No Stripe customer found for this user'
            }), 404
        
        customer = stripe_service.get_customer(user.stripe_customer_id)
        
        return jsonify({
            'success': True,
            'customer': customer.to_dict()
        })
        
    except Exception as e:
        logger.error(f"Failed to get customer: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@payment_bp.route('/customers/me', methods=['PUT'])
@login_required
def update_my_customer():
    """
    Update the current user's Stripe customer information.
    
    Request body:
    {
        "name": "John Doe",
        "phone": "+1234567890",
        "address": {...}
    }
    
    Returns:
    {
        "success": true,
        "customer": {
            "id": "cus_xxx",
            "email": "user@example.com",
            ...
        }
    }
    """
    try:
        user = current_user
        if not user.stripe_customer_id:
            return jsonify({
                'success': False,
                'error': 'No Stripe customer found for this user'
            }), 404
        
        data = request.get_json() or {}
        update_fields = {}
        
        # Extract allowed fields
        if 'name' in data:
            update_fields['name'] = data['name']
        if 'phone' in data:
            update_fields['phone'] = data['phone']
        if 'address' in data:
            update_fields['address'] = data['address']
        if 'metadata' in data:
            update_fields['metadata'] = data['metadata']
        
        if not update_fields:
            raise BadRequest("No valid fields to update")
        
        customer = stripe_service.update_customer(user.stripe_customer_id, **update_fields)
        
        return jsonify({
            'success': True,
            'customer': customer.to_dict()
        })
        
    except Exception as e:
        logger.error(f"Failed to update customer: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# =====================================================
# SUBSCRIPTION MANAGEMENT ENDPOINTS
# =====================================================

@payment_bp.route('/subscriptions/tiers', methods=['GET'])
def get_subscription_tiers():
    """
    Get all available subscription tiers.
    
    Returns:
    {
        "success": true,
        "tiers": {
            "budget": {
                "name": "Budget Tier",
                "price_monthly": 1500,
                "price_yearly": 14400,
                "features": {...},
                "limits": {...},
                "description": "..."
            },
            ...
        }
    }
    """
    try:
        tiers = stripe_service.get_all_tiers()
        
        tiers_data = {}
        for tier, config in tiers.items():
            tiers_data[tier.value] = {
                'name': config.name,
                'price_monthly': config.price_monthly,
                'price_yearly': config.price_yearly,
                'features': config.features,
                'limits': config.limits,
                'description': config.description
            }
        
        return jsonify({
            'success': True,
            'tiers': tiers_data
        })
        
    except Exception as e:
        logger.error(f"Failed to get subscription tiers: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@payment_bp.route('/subscriptions', methods=['POST'])
@login_required
def create_subscription():
    """
    Create a new subscription for the current user.
    
    Request body:
    {
        "tier": "budget",
        "billing_cycle": "monthly",
        "trial_days": 7,
        "payment_method_id": "pm_xxx"
    }
    
    Returns:
    {
        "success": true,
        "subscription": {
            "id": "sub_xxx",
            "status": "active",
            ...
        }
    }
    """
    try:
        user = current_user
        if not user.stripe_customer_id:
            return jsonify({
                'success': False,
                'error': 'No Stripe customer found. Please create a customer first.'
            }), 400
        
        data = request.get_json() or {}
        
        # Validate required fields
        if 'tier' not in data:
            raise BadRequest("Subscription tier is required")
        
        try:
            tier = SubscriptionTier(data['tier'])
        except ValueError:
            raise BadRequest(f"Invalid subscription tier: {data['tier']}")
        
        billing_cycle = data.get('billing_cycle', 'monthly')
        if billing_cycle not in ['monthly', 'yearly']:
            raise BadRequest("Billing cycle must be 'monthly' or 'yearly'")
        
        trial_days = data.get('trial_days')
        payment_method_id = data.get('payment_method_id')
        
        # Attach payment method if provided
        if payment_method_id:
            stripe_service.attach_payment_method(user.stripe_customer_id, payment_method_id)
        
        # Create subscription
        subscription = stripe_service.create_subscription(
            customer_id=user.stripe_customer_id,
            tier=tier,
            billing_cycle=billing_cycle,
            trial_days=trial_days,
            metadata={
                'user_id': str(user.id),
                'tier': tier.value,
                'billing_cycle': billing_cycle
            }
        )
        
        logger.info(f"Created subscription {subscription.id} for user {user.id}")
        
        return jsonify({
            'success': True,
            'subscription': subscription.to_dict()
        }), 201
        
    except Exception as e:
        logger.error(f"Failed to create subscription: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@payment_bp.route('/subscriptions/me', methods=['GET'])
@login_required
def get_my_subscriptions():
    """
    Get all subscriptions for the current user.
    
    Returns:
    {
        "success": true,
        "subscriptions": [
            {
                "id": "sub_xxx",
                "status": "active",
                ...
            }
        ]
    }
    """
    try:
        user = current_user
        if not user.stripe_customer_id:
            return jsonify({
                'success': True,
                'subscriptions': []
            })
        
        subscriptions = stripe_service.get_customer_subscriptions(user.stripe_customer_id)
        
        return jsonify({
            'success': True,
            'subscriptions': [sub.to_dict() for sub in subscriptions]
        })
        
    except Exception as e:
        logger.error(f"Failed to get subscriptions: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@payment_bp.route('/subscriptions/<subscription_id>', methods=['GET'])
@login_required
def get_subscription(subscription_id: str):
    """
    Get a specific subscription.
    
    Args:
        subscription_id: Stripe subscription ID
        
    Returns:
    {
        "success": true,
        "subscription": {
            "id": "sub_xxx",
            "status": "active",
            ...
        }
    }
    """
    try:
        subscription = stripe_service.get_subscription(subscription_id)
        
        # Verify ownership
        user = current_user
        if subscription.customer_id != user.stripe_customer_id:
            raise Unauthorized("Access denied to this subscription")
        
        return jsonify({
            'success': True,
            'subscription': subscription.to_dict()
        })
        
    except Exception as e:
        logger.error(f"Failed to get subscription {subscription_id}: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@payment_bp.route('/subscriptions/<subscription_id>', methods=['PUT'])
@login_required
def update_subscription(subscription_id: str):
    """
    Update a subscription (change tier or billing cycle).
    
    Args:
        subscription_id: Stripe subscription ID
        
    Request body:
    {
        "tier": "mid_tier",
        "billing_cycle": "yearly"
    }
    
    Returns:
    {
        "success": true,
        "subscription": {
            "id": "sub_xxx",
            "status": "active",
            ...
        }
    }
    """
    try:
        data = request.get_json() or {}
        
        if 'tier' not in data:
            raise BadRequest("Subscription tier is required")
        
        try:
            tier = SubscriptionTier(data['tier'])
        except ValueError:
            raise BadRequest(f"Invalid subscription tier: {data['tier']}")
        
        billing_cycle = data.get('billing_cycle', 'monthly')
        if billing_cycle not in ['monthly', 'yearly']:
            raise BadRequest("Billing cycle must be 'monthly' or 'yearly'")
        
        # Verify ownership before updating
        user = current_user
        current_subscription = stripe_service.get_subscription(subscription_id)
        if current_subscription.customer_id != user.stripe_customer_id:
            raise Unauthorized("Access denied to this subscription")
        
        subscription = stripe_service.update_subscription(
            subscription_id=subscription_id,
            tier=tier,
            billing_cycle=billing_cycle
        )
        
        logger.info(f"Updated subscription {subscription_id} to {tier.value}")
        
        return jsonify({
            'success': True,
            'subscription': subscription.to_dict()
        })
        
    except Exception as e:
        logger.error(f"Failed to update subscription {subscription_id}: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@payment_bp.route('/subscriptions/<subscription_id>/cancel', methods=['POST'])
@login_required
def cancel_subscription(subscription_id: str):
    """
    Cancel a subscription.
    
    Args:
        subscription_id: Stripe subscription ID
        
    Request body:
    {
        "at_period_end": true
    }
    
    Returns:
    {
        "success": true,
        "subscription": {
            "id": "sub_xxx",
            "status": "active",
            "cancel_at_period_end": true,
            ...
        }
    }
    """
    try:
        data = request.get_json() or {}
        at_period_end = data.get('at_period_end', True)
        
        # Verify ownership before canceling
        user = current_user
        current_subscription = stripe_service.get_subscription(subscription_id)
        if current_subscription.customer_id != user.stripe_customer_id:
            raise Unauthorized("Access denied to this subscription")
        
        subscription = stripe_service.cancel_subscription(
            subscription_id=subscription_id,
            at_period_end=at_period_end
        )
        
        logger.info(f"Cancelled subscription {subscription_id}")
        
        return jsonify({
            'success': True,
            'subscription': subscription.to_dict()
        })
        
    except Exception as e:
        logger.error(f"Failed to cancel subscription {subscription_id}: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# =====================================================
# PAYMENT PROCESSING ENDPOINTS
# =====================================================

@payment_bp.route('/payment-intents', methods=['POST'])
@login_required
def create_payment_intent():
    """
    Create a payment intent for one-time payments.
    
    Request body:
    {
        "amount": 1500,
        "currency": "usd",
        "description": "Payment for premium features"
    }
    
    Returns:
    {
        "success": true,
        "payment_intent": {
            "id": "pi_xxx",
            "client_secret": "pi_xxx_secret_xxx",
            ...
        }
    }
    """
    try:
        data = request.get_json() or {}
        
        if 'amount' not in data:
            raise BadRequest("Amount is required")
        
        amount = int(data['amount'])
        if amount <= 0:
            raise BadRequest("Amount must be positive")
        
        currency = data.get('currency', 'usd')
        description = data.get('description')
        
        # Add user metadata
        metadata = data.get('metadata', {})
        metadata.update({
            'user_id': str(current_user.id),
            'user_email': current_user.email
        })
        
        # Use customer ID if available
        customer_id = None
        if current_user.stripe_customer_id:
            customer_id = current_user.stripe_customer_id
        
        payment_intent = stripe_service.create_payment_intent(
            amount=amount,
            currency=currency,
            customer_id=customer_id,
            description=description,
            metadata=metadata
        )
        
        return jsonify({
            'success': True,
            'payment_intent': payment_intent.to_dict()
        }), 201
        
    except Exception as e:
        logger.error(f"Failed to create payment intent: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@payment_bp.route('/payment-methods', methods=['GET'])
@login_required
def get_payment_methods():
    """
    Get payment methods for the current user.
    
    Returns:
    {
        "success": true,
        "payment_methods": [
            {
                "id": "pm_xxx",
                "type": "card",
                "card_brand": "visa",
                "card_last4": "4242",
                ...
            }
        ]
    }
    """
    try:
        user = current_user
        if not user.stripe_customer_id:
            return jsonify({
                'success': True,
                'payment_methods': []
            })
        
        payment_methods = stripe_service.get_payment_methods(user.stripe_customer_id)
        
        return jsonify({
            'success': True,
            'payment_methods': [pm.to_dict() for pm in payment_methods]
        })
        
    except Exception as e:
        logger.error(f"Failed to get payment methods: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@payment_bp.route('/payment-methods', methods=['POST'])
@login_required
def attach_payment_method():
    """
    Attach a payment method to the current user's customer.
    
    Request body:
    {
        "payment_method_id": "pm_xxx"
    }
    
    Returns:
    {
        "success": true,
        "payment_method": {
            "id": "pm_xxx",
            "type": "card",
            ...
        }
    }
    """
    try:
        data = request.get_json() or {}
        
        if 'payment_method_id' not in data:
            raise BadRequest("Payment method ID is required")
        
        user = current_user
        if not user.stripe_customer_id:
            return jsonify({
                'success': False,
                'error': 'No Stripe customer found. Please create a customer first.'
            }), 400
        
        payment_method = stripe_service.attach_payment_method(
            user.stripe_customer_id,
            data['payment_method_id']
        )
        
        return jsonify({
            'success': True,
            'payment_method': payment_method.to_dict()
        }), 201
        
    except Exception as e:
        logger.error(f"Failed to attach payment method: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@payment_bp.route('/payment-methods/<payment_method_id>', methods=['DELETE'])
@login_required
def detach_payment_method(payment_method_id: str):
    """
    Detach a payment method from the current user's customer.
    
    Args:
        payment_method_id: Stripe payment method ID
        
    Returns:
    {
        "success": true,
        "message": "Payment method detached successfully"
    }
    """
    try:
        stripe_service.detach_payment_method(payment_method_id)
        
        return jsonify({
            'success': True,
            'message': 'Payment method detached successfully'
        })
        
    except Exception as e:
        logger.error(f"Failed to detach payment method {payment_method_id}: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# =====================================================
# BILLING AND INVOICE ENDPOINTS
# =====================================================

@payment_bp.route('/invoices', methods=['GET'])
@login_required
def get_invoices():
    """
    Get invoices for the current user.
    
    Query parameters:
    - limit: Maximum number of invoices to return (default: 10)
    
    Returns:
    {
        "success": true,
        "invoices": [
            {
                "id": "in_xxx",
                "amount_due": 1500,
                "status": "paid",
                ...
            }
        ]
    }
    """
    try:
        user = current_user
        if not user.stripe_customer_id:
            return jsonify({
                'success': True,
                'invoices': []
            })
        
        limit = request.args.get('limit', 10, type=int)
        invoices = stripe_service.get_customer_invoices(user.stripe_customer_id, limit)
        
        return jsonify({
            'success': True,
            'invoices': [invoice.to_dict() for invoice in invoices]
        })
        
    except Exception as e:
        logger.error(f"Failed to get invoices: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@payment_bp.route('/invoices/<invoice_id>', methods=['GET'])
@login_required
def get_invoice(invoice_id: str):
    """
    Get a specific invoice.
    
    Args:
        invoice_id: Stripe invoice ID
        
    Returns:
    {
        "success": true,
        "invoice": {
            "id": "in_xxx",
            "amount_due": 1500,
            "status": "paid",
            ...
        }
    }
    """
    try:
        invoice = stripe_service.get_invoice(invoice_id)
        
        # Verify ownership
        user = current_user
        if invoice.customer_id != user.stripe_customer_id:
            raise Unauthorized("Access denied to this invoice")
        
        return jsonify({
            'success': True,
            'invoice': invoice.to_dict()
        })
        
    except Exception as e:
        logger.error(f"Failed to get invoice {invoice_id}: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# =====================================================
# WEBHOOK ENDPOINTS
# =====================================================

@payment_bp.route('/webhooks/stripe', methods=['POST'])
def stripe_webhook():
    """
    Handle Stripe webhook events.
    
    This endpoint receives webhook events from Stripe and processes them
    to keep the application state in sync with Stripe.
    
    Returns:
    {
        "success": true,
        "message": "Webhook processed successfully"
    }
    """
    try:
        payload = request.get_data()
        signature = request.headers.get('Stripe-Signature')
        
        if not signature:
            raise BadRequest("Missing Stripe signature")
        
        # Get request information for security
        source_ip = request.remote_addr
        user_agent = request.headers.get('User-Agent', '')
        request_id = request.headers.get('X-Request-ID', str(uuid.uuid4()))
        timestamp = request.headers.get('Stripe-Signature-Timestamp')
        
        # Enhanced webhook processing with security validation
        event = stripe_service.handle_webhook(
            payload, signature, source_ip, user_agent, request_id, timestamp
        )
        
        logger.info(f"Processed webhook event: {event['type']}")
        
        # Add security headers
        response = jsonify({
            'success': True,
            'message': 'Webhook processed successfully'
        })
        
        security_headers = security_manager.get_security_headers()
        for key, value in security_headers.items():
            response.headers[key] = value
        
        return response
        
    except Exception as e:
        logger.error(f"Webhook processing failed: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400


# =====================================================
# STRIPE CUSTOMER PORTAL ENDPOINTS
# =====================================================

@payment_bp.route('/portal/session', methods=['POST'])
@login_required
def create_portal_session():
    """
    Create a Stripe Customer Portal session with return handling and custom branding.
    
    Request body:
    {
        "return_url": "https://mingus.com/dashboard/billing",
        "configuration_id": "bpc_xxx",
        "workflow_type": "payment_update|billing_review|subscription_management|cancellation_process|profile_update",
        "custom_branding": {
            "company_name": "MINGUS",
            "logo_url": "https://mingus.com/logo.png",
            "primary_color": "#2563eb",
            "secondary_color": "#1e40af"
        }
    }
    
    Returns:
    {
        "success": true,
        "portal_session": {
            "id": "bps_xxx",
            "url": "https://billing.stripe.com/session/xxx",
            "expires_at": "2025-01-15T10:30:00Z",
            "return_url": "https://mingus.com/dashboard/billing"
        }
    }
    """
    try:
        data = request.get_json() or {}
        
        # Get user's customer ID
        user = current_user
        customer_result = stripe_service.get_customer_by_user_id(user.id)
        
        if not customer_result['success']:
            return jsonify({
                'success': False,
                'error': 'Customer not found'
            }), 404
        
        customer_id = customer_result['customer']['id']
        
        # Extract portal session parameters
        return_url = data.get('return_url', f"{current_app.config['BASE_URL']}/dashboard/billing")
        configuration_id = data.get('configuration_id')
        workflow_type = data.get('workflow_type')
        custom_branding = data.get('custom_branding', {})
        
        # Create portal session based on workflow type
        if workflow_type:
            session_result = stripe_service.create_portal_integration_workflow(
                customer_id=customer_id,
                workflow_type=workflow_type,
                return_url=return_url
            )
        else:
            session_result = stripe_service.create_stripe_portal_session(
                customer_id=customer_id,
                return_url=return_url,
                configuration_id=configuration_id
            )
        
        if not session_result['success']:
            return jsonify({
                'success': False,
                'error': session_result['error']
            }), 400
        
        # Apply custom branding if provided
        if custom_branding:
            branding_result = stripe_service.apply_custom_portal_branding(
                session_result['portal_session']['id'],
                custom_branding
            )
            if not branding_result['success']:
                logger.warning(f"Failed to apply custom branding: {branding_result['error']}")
        
        return jsonify({
            'success': True,
            'portal_session': session_result['portal_session']
        })
        
    except Exception as e:
        logger.error(f"Error creating portal session: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@payment_bp.route('/portal/return', methods=['GET'])
@login_required
def handle_portal_return():
    """
    Handle return from Stripe Customer Portal with synchronized data.
    
    Query parameters:
    - session_id: Portal session ID
    - action: Action performed in portal (payment_updated, subscription_changed, etc.)
    - customer_id: Stripe customer ID
    
    Returns:
    {
        "success": true,
        "message": "Portal return handled successfully",
        "synchronized_data": {
            "customer_updated": true,
            "subscription_changed": false,
            "payment_method_updated": true,
            "changes": [...]
        }
    }
    """
    try:
        # Get query parameters
        session_id = request.args.get('session_id')
        action = request.args.get('action', 'unknown')
        customer_id = request.args.get('customer_id')
        
        if not session_id or not customer_id:
            return jsonify({
                'success': False,
                'error': 'Missing required parameters'
            }), 400
        
        # Get user's customer ID
        user = current_user
        user_customer_result = stripe_service.get_customer_by_user_id(user.id)
        
        if not user_customer_result['success']:
            return jsonify({
                'success': False,
                'error': 'Customer not found'
            }), 404
        
        user_customer_id = user_customer_result['customer']['id']
        
        # Verify customer ID matches
        if user_customer_id != customer_id:
            return jsonify({
                'success': False,
                'error': 'Customer ID mismatch'
            }), 403
        
        # Synchronize data from Stripe
        sync_result = stripe_service.synchronize_portal_data(
            customer_id=customer_id,
            session_id=session_id,
            action=action
        )
        
        if not sync_result['success']:
            return jsonify({
                'success': False,
                'error': sync_result['error']
            }), 500
        
        # Log portal return event
        logger.info(f"Portal return handled for user {user.id}, action: {action}")
        
        return jsonify({
            'success': True,
            'message': 'Portal return handled successfully',
            'synchronized_data': sync_result['synchronized_data'],
            'redirect_url': sync_result.get('redirect_url', '/dashboard/billing')
        })
        
    except Exception as e:
        logger.error(f"Error handling portal return: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@payment_bp.route('/portal/configuration', methods=['GET'])
@admin_required
def get_portal_configurations():
    """
    Get all available Stripe Customer Portal configurations.
    
    Returns:
    {
        "success": true,
        "configurations": [
            {
                "id": "bpc_xxx",
                "name": "MINGUS Customer Portal",
                "business_profile": {...},
                "features": {...},
                "is_default": true
            }
        ]
    }
    """
    try:
        configs_result = stripe_service.get_portal_configurations()
        
        if not configs_result['success']:
            return jsonify({
                'success': False,
                'error': configs_result['error']
            }), 400
        
        return jsonify({
            'success': True,
            'configurations': configs_result['configurations']
        })
        
    except Exception as e:
        logger.error(f"Error getting portal configurations: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@payment_bp.route('/portal/configuration', methods=['POST'])
@admin_required
def create_portal_configuration():
    """
    Create a custom Stripe Customer Portal configuration with branding.
    
    Request body:
    {
        "name": "MINGUS Enhanced Portal",
        "business_profile": {
            "headline": "MINGUS Financial Management",
            "privacy_policy_url": "https://mingus.com/privacy",
            "terms_of_service_url": "https://mingus.com/terms",
            "support_url": "https://mingus.com/support"
        },
        "features": {
            "customer_update": {
                "enabled": true,
                "allowed_updates": ["address", "shipping", "tax_id"]
            },
            "subscription_cancel": {
                "enabled": true,
                "cancellation_reason": {
                    "enabled": true,
                    "options": ["too_expensive", "missing_features", "other"]
                }
            }
        },
        "branding": {
            "company_name": "MINGUS",
            "logo_url": "https://mingus.com/logo.png",
            "primary_color": "#2563eb",
            "secondary_color": "#1e40af"
        }
    }
    
    Returns:
    {
        "success": true,
        "configuration": {
            "id": "bpc_xxx",
            "name": "MINGUS Enhanced Portal",
            "business_profile": {...},
            "features": {...}
        }
    }
    """
    try:
        data = request.get_json() or {}
        
        # Extract configuration parameters
        name = data.get('name', 'MINGUS Customer Portal')
        business_profile = data.get('business_profile', {})
        features = data.get('features', {})
        branding = data.get('branding', {})
        
        # Create portal configuration
        config_result = stripe_service.create_portal_configuration(
            configuration_name=name,
            features=features
        )
        
        if not config_result['success']:
            return jsonify({
                'success': False,
                'error': config_result['error']
            }), 400
        
        # Apply custom branding if provided
        if branding and config_result['configuration']['id']:
            branding_result = stripe_service.apply_custom_portal_branding(
                config_result['configuration']['id'],
                branding
            )
            if not branding_result['success']:
                logger.warning(f"Failed to apply custom branding: {branding_result['error']}")
        
        return jsonify({
            'success': True,
            'configuration': config_result['configuration']
        })
        
    except Exception as e:
        logger.error(f"Error creating portal configuration: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@payment_bp.route('/portal/configuration/<configuration_id>', methods=['PUT'])
@admin_required
def update_portal_configuration(configuration_id: str):
    """
    Update an existing Stripe Customer Portal configuration.
    
    Request body:
    {
        "business_profile": {...},
        "features": {...},
        "branding": {...}
    }
    
    Returns:
    {
        "success": true,
        "configuration": {
            "id": "bpc_xxx",
            "name": "Updated Portal Configuration",
            "business_profile": {...},
            "features": {...}
        }
    }
    """
    try:
        data = request.get_json() or {}
        
        # Update configuration
        update_result = stripe_service.update_portal_configuration(
            configuration_id=configuration_id,
            updates=data
        )
        
        if not update_result['success']:
            return jsonify({
                'success': False,
                'error': update_result['error']
            }), 400
        
        return jsonify({
            'success': True,
            'configuration': update_result['configuration']
        })
        
    except Exception as e:
        logger.error(f"Error updating portal configuration: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@payment_bp.route('/portal/analytics', methods=['GET'])
@admin_required
def get_portal_analytics():
    """
    Get analytics and insights for Stripe Customer Portal usage.
    
    Query parameters:
    - start_date: Start date for analytics (YYYY-MM-DD)
    - end_date: End date for analytics (YYYY-MM-DD)
    - customer_id: Specific customer ID (optional)
    
    Returns:
    {
        "success": true,
        "analytics": {
            "total_sessions": 150,
            "unique_customers": 89,
            "most_used_features": [...],
            "session_duration_stats": {...},
            "return_rate": 0.85
        }
    }
    """
    try:
        # Get query parameters
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        customer_id = request.args.get('customer_id')
        
        # Get portal analytics
        analytics_result = stripe_service.get_portal_analytics(
            start_date=start_date,
            end_date=end_date,
            customer_id=customer_id
        )
        
        if not analytics_result['success']:
            return jsonify({
                'success': False,
                'error': analytics_result['error']
            }), 400
        
        return jsonify({
            'success': True,
            'analytics': analytics_result['analytics']
        })
        
    except Exception as e:
        logger.error(f"Error getting portal analytics: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@payment_bp.route('/portal/webhook', methods=['POST'])
def handle_portal_webhook():
    """
    Handle Stripe Customer Portal webhook events for data synchronization.
    
    This endpoint receives webhook events from Stripe when customers
    make changes in the Customer Portal and synchronizes the data
    with the local database.
    
    Returns:
    {
        "success": true,
        "message": "Portal webhook processed successfully"
    }
    """
    try:
        payload = request.get_data()
        signature = request.headers.get('Stripe-Signature')
        
        if not signature:
            raise BadRequest("Missing Stripe signature")
        
        # Get request information for security
        source_ip = request.remote_addr
        user_agent = request.headers.get('User-Agent', '')
        request_id = request.headers.get('X-Request-ID', str(uuid.uuid4()))
        timestamp = request.headers.get('Stripe-Signature-Timestamp')
        
        # Process portal webhook
        event = stripe_service.handle_portal_webhook(
            payload, signature, source_ip, user_agent, request_id, timestamp
        )
        
        logger.info(f"Processed portal webhook event: {event['type']}")
        
        # Add security headers
        response = jsonify({
            'success': True,
            'message': 'Portal webhook processed successfully'
        })
        
        security_headers = security_manager.get_security_headers()
        for key, value in security_headers.items():
            response.headers[key] = value
        
        return response
        
    except Exception as e:
        logger.error(f"Portal webhook processing failed: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400


# =====================================================
# UTILITY ENDPOINTS
# =====================================================

@payment_bp.route('/config', methods=['GET'])
def get_payment_config():
    """
    Get payment configuration for client-side integration.
    
    Returns:
    {
        "success": true,
        "config": {
            "publishable_key": "pk_xxx",
            "currency": "usd",
            "payment_method_types": ["card", "bank_account"]
        }
    }
    """
    try:
        config = {
            'publishable_key': stripe_service.get_publishable_key(),
            'currency': stripe_service.config.currency,
            'payment_method_types': ['card', 'bank_account'],
            'automatic_payment_methods': ['card', 'link']
        }
        
        return jsonify({
            'success': True,
            'config': config
        })
        
    except Exception as e:
        logger.error(f"Failed to get payment config: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@payment_bp.route('/environment', methods=['GET'])
@admin_required
def get_stripe_environment():
    """
    Get Stripe environment information (admin only).
    
    Returns:
    {
        "success": true,
        "environment": {
            "environment": "test",
            "is_test_mode": true,
            "is_live_mode": false,
            "currency": "usd",
            "webhook_endpoint": "...",
            "price_ids_configured": {...},
            "is_configured": true,
            "missing_configuration": []
        }
    }
    """
    try:
        environment_info = get_stripe_environment_info()
        
        return jsonify({
            'success': True,
            'environment': environment_info
        })
        
    except Exception as e:
        logger.error(f"Failed to get Stripe environment: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@payment_bp.route('/validate', methods=['GET'])
@admin_required
def validate_stripe_setup():
    """
    Validate Stripe configuration (admin only).
    
    Returns:
    {
        "success": true,
        "validation": {
            "environment": "test",
            "is_configured": true,
            "missing_configuration": [],
            "price_ids_configured": {...},
            "warnings": []
        }
    }
    """
    try:
        validation = validate_stripe_environment()
        
        return jsonify({
            'success': True,
            'validation': validation
        })
        
    except Exception as e:
        logger.error(f"Failed to validate Stripe setup: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@payment_bp.route('/proration', methods=['POST'])
@login_required
def calculate_proration():
    """
    Calculate proration for subscription changes.
    
    Request body:
    {
        "subscription_id": "sub_xxx",
        "new_price_id": "price_xxx",
        "proration_date": 1234567890
    }
    
    Returns:
    {
        "success": true,
        "proration": {
            "total": 500,
            "subtotal": 500,
            "tax": 0,
            "lines": [...]
        }
    }
    """
    try:
        data = request.get_json() or {}
        
        if 'subscription_id' not in data or 'new_price_id' not in data:
            raise BadRequest("Subscription ID and new price ID are required")
        
        subscription_id = data['subscription_id']
        new_price_id = data['new_price_id']
        proration_date = data.get('proration_date')
        
        # Verify ownership
        user = current_user
        current_subscription = stripe_service.get_subscription(subscription_id)
        if current_subscription.customer_id != user.stripe_customer_id:
            raise Unauthorized("Access denied to this subscription")
        
        proration = stripe_service.calculate_proration(
            subscription_id=subscription_id,
            new_price_id=new_price_id,
            proration_date=proration_date
        )
        
        return jsonify({
            'success': True,
            'proration': proration
        })
        
    except Exception as e:
        logger.error(f"Failed to calculate proration: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# =====================================================
# ADMIN ENDPOINTS
# =====================================================

@payment_bp.route('/admin/refunds', methods=['POST'])
@admin_required
def create_refund():
    """
    Create a refund for a payment (admin only).
    
    Request body:
    {
        "payment_intent_id": "pi_xxx",
        "amount": 1000,
        "reason": "customer_requested"
    }
    
    Returns:
    {
        "success": true,
        "refund": {
            "id": "re_xxx",
            "amount": 1000,
            "status": "succeeded",
            ...
        }
    }
    """
    try:
        data = request.get_json() or {}
        
        if 'payment_intent_id' not in data:
            raise BadRequest("Payment intent ID is required")
        
        payment_intent_id = data['payment_intent_id']
        amount = data.get('amount')
        reason = data.get('reason')
        metadata = data.get('metadata', {})
        
        refund = stripe_service.create_refund(
            payment_intent_id=payment_intent_id,
            amount=amount,
            reason=reason,
            metadata=metadata
        )
        
        logger.info(f"Created refund {refund['id']} for payment intent {payment_intent_id}")
        
        return jsonify({
            'success': True,
            'refund': refund
        }), 201
        
    except Exception as e:
        logger.error(f"Failed to create refund: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500 