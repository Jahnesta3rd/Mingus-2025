#!/usr/bin/env python3
"""
Mingus Application - Notification Models
SQLAlchemy models for notification preferences, delivery tracking, and analytics
"""

from datetime import datetime
from enum import Enum
from typing import Dict, Any, Optional
from .database import db
from sqlalchemy import JSON, Index, CheckConstraint

class NotificationChannel(Enum):
    PUSH = "push"
    EMAIL = "email"
    SMS = "sms"

class NotificationType(Enum):
    DAILY_OUTLOOK = "daily_outlook"
    STREAK_MILESTONE = "streak_milestone"
    RECOVERY = "recovery"
    REMINDER = "reminder"

class DeliveryStatus(Enum):
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    BOUNCED = "bounced"

class InteractionType(Enum):
    CLICKED = "clicked"
    DISMISSED = "dismissed"
    ACTION_TAKEN = "action_taken"
    VIEWED = "viewed"

class UserNotificationPreferences(db.Model):
    """
    User notification preferences model for storing user's notification settings
    """
    __tablename__ = 'user_notification_preferences'
    
    # Primary key (user_id is the primary key since it's one-to-one)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    
    # Daily Outlook notification settings
    daily_outlook_enabled = db.Column(db.Boolean, default=True, nullable=False)
    weekday_time = db.Column(db.Time, default=datetime.strptime('06:45', '%H:%M').time(), nullable=False)
    weekend_time = db.Column(db.Time, default=datetime.strptime('08:30', '%H:%M').time(), nullable=False)
    
    # Notification channels
    push_enabled = db.Column(db.Boolean, default=True, nullable=False)
    email_enabled = db.Column(db.Boolean, default=True, nullable=False)
    sms_enabled = db.Column(db.Boolean, default=False, nullable=False)
    
    # Notification preferences
    sound_enabled = db.Column(db.Boolean, default=True, nullable=False)
    vibration_enabled = db.Column(db.Boolean, default=True, nullable=False)
    rich_notifications = db.Column(db.Boolean, default=True, nullable=False)
    action_buttons = db.Column(db.Boolean, default=True, nullable=False)
    
    # Timezone
    timezone = db.Column(db.String(50), default='UTC', nullable=False)
    
    # Advanced preferences
    quiet_hours_start = db.Column(db.Time, nullable=True)
    quiet_hours_end = db.Column(db.Time, nullable=True)
    max_notifications_per_day = db.Column(db.Integer, default=5, nullable=False)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    user = db.relationship('User', backref='notification_preferences', uselist=False)
    
    # Indexes and constraints
    __table_args__ = (
        Index('idx_notification_prefs_timezone', 'timezone'),
        CheckConstraint('max_notifications_per_day >= 0', name='check_positive_max_notifications'),
    )
    
    def __repr__(self):
        return f'<UserNotificationPreferences {self.user_id}>'
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            'user_id': self.user_id,
            'daily_outlook_enabled': self.daily_outlook_enabled,
            'weekday_time': self.weekday_time.strftime('%H:%M') if self.weekday_time else None,
            'weekend_time': self.weekend_time.strftime('%H:%M') if self.weekend_time else None,
            'push_enabled': self.push_enabled,
            'email_enabled': self.email_enabled,
            'sms_enabled': self.sms_enabled,
            'sound_enabled': self.sound_enabled,
            'vibration_enabled': self.vibration_enabled,
            'rich_notifications': self.rich_notifications,
            'action_buttons': self.action_buttons,
            'timezone': self.timezone,
            'quiet_hours_start': self.quiet_hours_start.strftime('%H:%M') if self.quiet_hours_start else None,
            'quiet_hours_end': self.quiet_hours_end.strftime('%H:%M') if self.quiet_hours_end else None,
            'max_notifications_per_day': self.max_notifications_per_day,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class PushSubscription(db.Model):
    """
    Push notification subscription model for storing user's push notification endpoints
    """
    __tablename__ = 'push_subscriptions'
    
    # Primary key
    id = db.Column(db.Integer, primary_key=True)
    
    # Foreign key to users table
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    
    # Push subscription data
    endpoint = db.Column(db.Text, nullable=False)
    p256dh_key = db.Column(db.Text, nullable=False)
    auth_key = db.Column(db.Text, nullable=False)
    
    # Subscription metadata
    user_agent = db.Column(db.String(500), nullable=True)
    ip_address = db.Column(db.String(45), nullable=True)
    
    # Status
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    last_used = db.Column(db.DateTime, nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    user = db.relationship('User', backref='push_subscriptions')
    
    # Indexes
    __table_args__ = (
        Index('idx_push_subscriptions_user_active', 'user_id', 'is_active'),
        Index('idx_push_subscriptions_endpoint', 'endpoint'),
    )
    
    def __repr__(self):
        return f'<PushSubscription {self.id}: {self.user_id}>'
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'endpoint': self.endpoint,
            'p256dh_key': self.p256dh_key,
            'auth_key': self.auth_key,
            'user_agent': self.user_agent,
            'ip_address': self.ip_address,
            'is_active': self.is_active,
            'last_used': self.last_used.isoformat() if self.last_used else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class NotificationDelivery(db.Model):
    """
    Notification delivery tracking model for tracking sent notifications
    """
    __tablename__ = 'notification_deliveries'
    
    # Primary key
    id = db.Column(db.Integer, primary_key=True)
    
    # Foreign key to users table
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    
    # Notification details
    notification_id = db.Column(db.String(255), nullable=False, index=True)
    notification_type = db.Column(db.Enum(NotificationType), nullable=False, index=True)
    channel = db.Column(db.Enum(NotificationChannel), nullable=False, index=True)
    
    # Content
    title = db.Column(db.String(255), nullable=False)
    message = db.Column(db.Text, nullable=False)
    action_url = db.Column(db.String(500), nullable=True)
    
    # Delivery tracking
    scheduled_time = db.Column(db.DateTime, nullable=False, index=True)
    sent_at = db.Column(db.DateTime, nullable=True)
    delivered_at = db.Column(db.DateTime, nullable=True)
    clicked_at = db.Column(db.DateTime, nullable=True)
    
    # Status and metadata
    status = db.Column(db.Enum(DeliveryStatus), default=DeliveryStatus.PENDING, nullable=False, index=True)
    error_message = db.Column(db.Text, nullable=True)
    delivery_metadata = db.Column(JSON, nullable=True)
    
    # Engagement tracking
    is_opened = db.Column(db.Boolean, default=False, nullable=False)
    action_taken = db.Column(db.String(100), nullable=True)
    engagement_data = db.Column(JSON, nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    user = db.relationship('User', backref='notification_deliveries')
    
    # Indexes
    __table_args__ = (
        Index('idx_notification_deliveries_user_status', 'user_id', 'status'),
        Index('idx_notification_deliveries_scheduled_time', 'scheduled_time'),
        Index('idx_notification_deliveries_type_channel', 'notification_type', 'channel'),
    )
    
    def __repr__(self):
        return f'<NotificationDelivery {self.id}: {self.user_id} - {self.notification_type.value}>'
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'notification_id': self.notification_id,
            'notification_type': self.notification_type.value,
            'channel': self.channel.value,
            'title': self.title,
            'message': self.message,
            'action_url': self.action_url,
            'scheduled_time': self.scheduled_time.isoformat() if self.scheduled_time else None,
            'sent_at': self.sent_at.isoformat() if self.sent_at else None,
            'delivered_at': self.delivered_at.isoformat() if self.delivered_at else None,
            'clicked_at': self.clicked_at.isoformat() if self.clicked_at else None,
            'status': self.status.value,
            'error_message': self.error_message,
            'delivery_metadata': self.delivery_metadata,
            'is_opened': self.is_opened,
            'action_taken': self.action_taken,
            'engagement_data': self.engagement_data,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class NotificationInteraction(db.Model):
    """
    Notification interaction tracking model for tracking user interactions with notifications
    """
    __tablename__ = 'notification_interactions'
    
    # Primary key
    id = db.Column(db.Integer, primary_key=True)
    
    # Foreign key to notification_deliveries table
    delivery_id = db.Column(db.Integer, db.ForeignKey('notification_deliveries.id'), nullable=False, index=True)
    
    # Interaction details
    interaction_type = db.Column(db.Enum(InteractionType), nullable=False, index=True)
    interaction_data = db.Column(JSON, nullable=True)
    
    # Device and session info
    user_agent = db.Column(db.String(500), nullable=True)
    ip_address = db.Column(db.String(45), nullable=True)
    session_id = db.Column(db.String(255), nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    delivery = db.relationship('NotificationDelivery', backref='interactions')
    
    # Indexes
    __table_args__ = (
        Index('idx_notification_interactions_delivery_type', 'delivery_id', 'interaction_type'),
        Index('idx_notification_interactions_created_at', 'created_at'),
    )
    
    def __repr__(self):
        return f'<NotificationInteraction {self.id}: {self.delivery_id} - {self.interaction_type.value}>'
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'delivery_id': self.delivery_id,
            'interaction_type': self.interaction_type.value,
            'interaction_data': self.interaction_data,
            'user_agent': self.user_agent,
            'ip_address': self.ip_address,
            'session_id': self.session_id,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class NotificationTemplate(db.Model):
    """
    Notification template model for storing reusable notification templates
    """
    __tablename__ = 'notification_templates'
    
    # Primary key
    id = db.Column(db.Integer, primary_key=True)
    
    # Template details
    name = db.Column(db.String(100), nullable=False, unique=True)
    notification_type = db.Column(db.Enum(NotificationType), nullable=False, index=True)
    channel = db.Column(db.Enum(NotificationChannel), nullable=False, index=True)
    
    # Template content
    title_template = db.Column(db.String(255), nullable=False)
    message_template = db.Column(db.Text, nullable=False)
    
    # Template variables
    variables = db.Column(JSON, nullable=True)
    
    # Template settings
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    priority = db.Column(db.String(20), default='normal', nullable=False)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Indexes
    __table_args__ = (
        Index('idx_notification_templates_type_channel', 'notification_type', 'channel'),
        Index('idx_notification_templates_active', 'is_active'),
    )
    
    def __repr__(self):
        return f'<NotificationTemplate {self.id}: {self.name}>'
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'name': self.name,
            'notification_type': self.notification_type.value,
            'channel': self.channel.value,
            'title_template': self.title_template,
            'message_template': self.message_template,
            'variables': self.variables,
            'is_active': self.is_active,
            'priority': self.priority,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
