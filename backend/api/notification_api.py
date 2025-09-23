#!/usr/bin/env python3
"""
Mingus Notification API

REST API endpoints for notification management including:
- Push notification subscriptions
- Notification preferences
- Notification delivery tracking
- Analytics and reporting
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from flask import Blueprint, request, jsonify, current_app
from sqlalchemy import and_, or_, desc, func
from werkzeug.exceptions import BadRequest, Unauthorized, NotFound

# Local imports
from backend.models.database import db
from backend.models.user_models import User
from backend.models.notification_models import (
    UserNotificationPreferences,
    PushSubscription,
    NotificationDelivery,
    NotificationInteraction,
    NotificationTemplate,
    NotificationChannel,
    NotificationType,
    DeliveryStatus,
    InteractionType
)
from backend.services.notification_service import NotificationService

logger = logging.getLogger(__name__)

# Create Blueprint
notification_bp = Blueprint('notifications', __name__, url_prefix='/api/notifications')

# Initialize notification service
notification_service = NotificationService()

@notification_bp.route('/subscribe', methods=['POST'])
def subscribe_to_notifications():
    """
    Subscribe user to push notifications
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Get user from token (in real implementation)
        user_id = get_user_from_token()  # This would be implemented based on your auth system
        
        subscription_data = data.get('subscription')
        preferences = data.get('preferences', {})
        
        if not subscription_data:
            return jsonify({'error': 'Subscription data required'}), 400
        
        # Store push subscription
        push_subscription = PushSubscription(
            user_id=user_id,
            endpoint=subscription_data.get('endpoint'),
            p256dh_key=subscription_data.get('keys', {}).get('p256dh'),
            auth_key=subscription_data.get('keys', {}).get('auth'),
            user_agent=request.headers.get('User-Agent'),
            ip_address=request.remote_addr
        )
        
        db.session.add(push_subscription)
        
        # Update notification preferences
        prefs = UserNotificationPreferences.query.filter_by(user_id=user_id).first()
        if not prefs:
            prefs = UserNotificationPreferences(user_id=user_id)
            db.session.add(prefs)
        
        # Update preferences from request
        for key, value in preferences.items():
            if hasattr(prefs, key):
                setattr(prefs, key, value)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Successfully subscribed to notifications',
            'subscription_id': push_subscription.id
        })
        
    except Exception as e:
        logger.error(f"Error subscribing to notifications: {e}")
        db.session.rollback()
        return jsonify({'error': 'Failed to subscribe to notifications'}), 500

@notification_bp.route('/unsubscribe', methods=['POST'])
def unsubscribe_from_notifications():
    """
    Unsubscribe user from push notifications
    """
    try:
        user_id = get_user_from_token()
        
        # Deactivate all push subscriptions for user
        PushSubscription.query.filter_by(user_id=user_id, is_active=True).update({
            'is_active': False,
            'updated_at': datetime.utcnow()
        })
        
        # Update notification preferences
        prefs = UserNotificationPreferences.query.filter_by(user_id=user_id).first()
        if prefs:
            prefs.push_enabled = False
            prefs.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Successfully unsubscribed from notifications'
        })
        
    except Exception as e:
        logger.error(f"Error unsubscribing from notifications: {e}")
        db.session.rollback()
        return jsonify({'error': 'Failed to unsubscribe from notifications'}), 500

@notification_bp.route('/preferences', methods=['GET'])
def get_notification_preferences():
    """
    Get user's notification preferences
    """
    try:
        user_id = get_user_from_token()
        
        prefs = UserNotificationPreferences.query.filter_by(user_id=user_id).first()
        if not prefs:
            # Return default preferences
            return jsonify(notification_service.default_preferences)
        
        return jsonify(prefs.to_dict())
        
    except Exception as e:
        logger.error(f"Error getting notification preferences: {e}")
        return jsonify({'error': 'Failed to get notification preferences'}), 500

@notification_bp.route('/preferences', methods=['PUT'])
def update_notification_preferences():
    """
    Update user's notification preferences
    """
    try:
        user_id = get_user_from_token()
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Get or create preferences
        prefs = UserNotificationPreferences.query.filter_by(user_id=user_id).first()
        if not prefs:
            prefs = UserNotificationPreferences(user_id=user_id)
            db.session.add(prefs)
        
        # Update preferences
        for key, value in data.items():
            if hasattr(prefs, key):
                setattr(prefs, key, value)
        
        prefs.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Preferences updated successfully',
            'preferences': prefs.to_dict()
        })
        
    except Exception as e:
        logger.error(f"Error updating notification preferences: {e}")
        db.session.rollback()
        return jsonify({'error': 'Failed to update notification preferences'}), 500

@notification_bp.route('/test', methods=['POST'])
def send_test_notification():
    """
    Send a test notification to the user
    """
    try:
        user_id = get_user_from_token()
        
        # Get user
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Get user's push subscription
        push_subscription = PushSubscription.query.filter_by(
            user_id=user_id, 
            is_active=True
        ).first()
        
        if not push_subscription:
            return jsonify({'error': 'No active push subscription found'}), 400
        
        # Create test notification content
        test_content = {
            'title': 'Test Notification 🌅',
            'body': f'Hello {user.first_name or "there"}! This is a test notification from Mingus.',
            'icon': '/icons/icon-192x192.png',
            'badge': '/icons/badge-72x72.png',
            'tag': 'test-notification',
            'requireInteraction': True,
            'data': {
                'url': '/daily-outlook',
                'notification_type': 'test',
                'test': True
            },
            'actions': [
                {
                    'action': 'view',
                    'title': 'View App',
                    'icon': '/icons/view-icon.png'
                },
                {
                    'action': 'dismiss',
                    'title': 'Dismiss',
                    'icon': '/icons/dismiss-icon.png'
                }
            ]
        }
        
        # Send test notification
        success = notification_service.send_push_notification(
            user_id, 
            test_content, 
            push_subscription.to_dict()
        )
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Test notification sent successfully'
            })
        else:
            return jsonify({'error': 'Failed to send test notification'}), 500
        
    except Exception as e:
        logger.error(f"Error sending test notification: {e}")
        return jsonify({'error': 'Failed to send test notification'}), 500

@notification_bp.route('/track', methods=['POST'])
def track_notification_interaction():
    """
    Track notification interaction (click, dismiss, action taken)
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        notification_id = data.get('notification_id')
        action = data.get('action')
        action_data = data.get('actionData')
        timestamp = data.get('timestamp')
        
        if not notification_id or not action:
            return jsonify({'error': 'notification_id and action are required'}), 400
        
        # Find the notification delivery record
        delivery = NotificationDelivery.query.filter_by(
            notification_id=notification_id
        ).first()
        
        if not delivery:
            return jsonify({'error': 'Notification not found'}), 404
        
        # Create interaction record
        interaction = NotificationInteraction(
            delivery_id=delivery.id,
            interaction_type=InteractionType(action),
            interaction_data=action_data,
            user_agent=request.headers.get('User-Agent'),
            ip_address=request.remote_addr,
            session_id=request.headers.get('X-Session-ID')
        )
        
        db.session.add(interaction)
        
        # Update delivery record based on action
        if action == 'clicked':
            delivery.clicked_at = datetime.utcnow()
            delivery.is_opened = True
        elif action == 'action_taken':
            delivery.action_taken = action_data.get('action', 'unknown')
            delivery.clicked_at = datetime.utcnow()
            delivery.is_opened = True
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Interaction tracked successfully'
        })
        
    except Exception as e:
        logger.error(f"Error tracking notification interaction: {e}")
        db.session.rollback()
        return jsonify({'error': 'Failed to track interaction'}), 500

@notification_bp.route('/history', methods=['GET'])
def get_notification_history():
    """
    Get user's notification history
    """
    try:
        user_id = get_user_from_token()
        limit = request.args.get('limit', 50, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        # Get notification deliveries for user
        deliveries = NotificationDelivery.query.filter_by(user_id=user_id)\
            .order_by(desc(NotificationDelivery.created_at))\
            .limit(limit)\
            .offset(offset)\
            .all()
        
        history = [delivery.to_dict() for delivery in deliveries]
        
        return jsonify(history)
        
    except Exception as e:
        logger.error(f"Error getting notification history: {e}")
        return jsonify({'error': 'Failed to get notification history'}), 500

@notification_bp.route('/stats', methods=['GET'])
def get_notification_stats():
    """
    Get notification statistics for the user
    """
    try:
        user_id = get_user_from_token()
        
        # Calculate stats
        total_sent = NotificationDelivery.query.filter_by(user_id=user_id).count()
        total_delivered = NotificationDelivery.query.filter_by(
            user_id=user_id, 
            status=DeliveryStatus.DELIVERED
        ).count()
        total_clicked = NotificationDelivery.query.filter_by(
            user_id=user_id,
            is_opened=True
        ).count()
        
        click_rate = (total_clicked / total_delivered * 100) if total_delivered > 0 else 0
        delivery_rate = (total_delivered / total_sent * 100) if total_sent > 0 else 0
        
        return jsonify({
            'total_sent': total_sent,
            'total_delivered': total_delivered,
            'total_clicked': total_clicked,
            'click_rate': round(click_rate, 2),
            'delivery_rate': round(delivery_rate, 2)
        })
        
    except Exception as e:
        logger.error(f"Error getting notification stats: {e}")
        return jsonify({'error': 'Failed to get notification stats'}), 500

@notification_bp.route('/schedule', methods=['POST'])
def schedule_daily_outlook_notifications():
    """
    Schedule Daily Outlook notifications for all eligible users
    """
    try:
        data = request.get_json() or {}
        target_date = data.get('target_date')
        
        # Schedule notifications
        result = notification_service.schedule_daily_outlook_notifications(target_date)
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error scheduling daily outlook notifications: {e}")
        return jsonify({'error': 'Failed to schedule notifications'}), 500

@notification_bp.route('/templates', methods=['GET'])
def get_notification_templates():
    """
    Get available notification templates
    """
    try:
        templates = NotificationTemplate.query.filter_by(is_active=True).all()
        return jsonify([template.to_dict() for template in templates])
        
    except Exception as e:
        logger.error(f"Error getting notification templates: {e}")
        return jsonify({'error': 'Failed to get notification templates'}), 500

@notification_bp.route('/templates', methods=['POST'])
def create_notification_template():
    """
    Create a new notification template
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        template = NotificationTemplate(
            name=data.get('name'),
            notification_type=NotificationType(data.get('notification_type')),
            channel=NotificationChannel(data.get('channel')),
            title_template=data.get('title_template'),
            message_template=data.get('message_template'),
            variables=data.get('variables'),
            priority=data.get('priority', 'normal')
        )
        
        db.session.add(template)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Template created successfully',
            'template': template.to_dict()
        })
        
    except Exception as e:
        logger.error(f"Error creating notification template: {e}")
        db.session.rollback()
        return jsonify({'error': 'Failed to create template'}), 500

def get_user_from_token():
    """
    Extract user ID from authentication token
    This is a placeholder - implement based on your auth system
    """
    # In a real implementation, this would:
    # 1. Extract token from Authorization header
    # 2. Validate token
    # 3. Return user ID
    
    # For now, return a default user ID
    return 1  # This should be replaced with actual token validation

# Error handlers
@notification_bp.errorhandler(400)
def bad_request(error):
    return jsonify({'error': 'Bad request'}), 400

@notification_bp.errorhandler(401)
def unauthorized(error):
    return jsonify({'error': 'Unauthorized'}), 401

@notification_bp.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404

@notification_bp.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500
