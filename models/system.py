"""
MINGUS Application - System Models
==================================

SQLAlchemy models for system management and notifications.

Models:
- SystemAlert: System-wide alerts and notifications
- ImportantDate: Important dates and reminder management
- NotificationPreference: User notification preferences

Author: MINGUS Development Team
Date: January 2025
"""

import uuid
from datetime import datetime, timezone, date, time
from sqlalchemy import Column, String, Boolean, Integer, DateTime, Date, Time, Numeric, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship, validates
from sqlalchemy.sql import func
from . import Base


class SystemAlert(Base):
    """System-wide alerts and notifications."""
    
    __tablename__ = 'system_alerts'
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Alert information
    alert_type = Column(String(50), nullable=False)  # security, performance, maintenance, user
    severity = Column(String(20), nullable=False)  # low, medium, high, critical
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    
    # User association
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), index=True)
    
    # Status tracking
    is_read = Column(Boolean, default=False)
    read_at = Column(DateTime(timezone=True))
    action_required = Column(Boolean, default=False)
    action_taken = Column(Boolean, default=False)
    action_notes = Column(Text)
    
    # Expiration
    expires_at = Column(DateTime(timezone=True))
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User")
    
    # Validation
    @validates('alert_type')
    def validate_alert_type(self, key, alert_type):
        """Validate alert type."""
        valid_types = ['security', 'performance', 'maintenance', 'user', 'billing', 'feature']
        if alert_type not in valid_types:
            raise ValueError(f"Alert type must be one of: {valid_types}")
        return alert_type
    
    @validates('severity')
    def validate_severity(self, key, severity):
        """Validate alert severity."""
        valid_severities = ['low', 'medium', 'high', 'critical']
        if severity not in valid_severities:
            raise ValueError(f"Severity must be one of: {valid_severities}")
        return severity
    
    # Properties
    @property
    def is_expired(self):
        """Check if alert has expired."""
        if not self.expires_at:
            return False
        return datetime.now(timezone.utc) > self.expires_at
    
    @property
    def is_active(self):
        """Check if alert is active (not read and not expired)."""
        return not self.is_read and not self.is_expired
    
    @property
    def days_until_expiry(self):
        """Calculate days until expiry."""
        if not self.expires_at:
            return None
        delta = self.expires_at - datetime.now(timezone.utc)
        return max(0, delta.days)
    
    @property
    def age_days(self):
        """Calculate age of alert in days."""
        if not self.created_at:
            return None
        delta = datetime.now(timezone.utc) - self.created_at
        return delta.days
    
    @property
    def priority_score(self):
        """Calculate priority score based on severity and age."""
        severity_scores = {'low': 1, 'medium': 2, 'high': 3, 'critical': 4}
        base_score = severity_scores.get(self.severity, 1)
        
        # Increase score for unread alerts
        if not self.is_read:
            base_score += 1
        
        # Increase score for action required
        if self.action_required:
            base_score += 2
        
        # Decrease score for older alerts
        if self.age_days and self.age_days > 7:
            base_score = max(1, base_score - 1)
        
        return base_score
    
    # Methods
    def mark_as_read(self):
        """Mark alert as read."""
        self.is_read = True
        self.read_at = datetime.now(timezone.utc)
    
    def mark_action_taken(self, action_notes=None):
        """Mark action as taken."""
        self.action_taken = True
        if action_notes:
            self.action_notes = action_notes
    
    def to_dict(self):
        """Convert system alert to dictionary."""
        return {
            'id': str(self.id),
            'alert_type': self.alert_type,
            'severity': self.severity,
            'title': self.title,
            'message': self.message,
            'user_id': str(self.user_id) if self.user_id else None,
            'is_read': self.is_read,
            'read_at': self.read_at.isoformat() if self.read_at else None,
            'action_required': self.action_required,
            'action_taken': self.action_taken,
            'action_notes': self.action_notes,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'is_expired': self.is_expired,
            'is_active': self.is_active,
            'days_until_expiry': self.days_until_expiry,
            'age_days': self.age_days,
            'priority_score': self.priority_score,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f"<SystemAlert(id={self.id}, type='{self.alert_type}', severity='{self.severity}', title='{self.title}')>"


class ImportantDate(Base):
    """Important dates and reminder management."""
    
    __tablename__ = 'important_dates'
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign key
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Date information
    date_name = Column(String(255), nullable=False)
    date_type = Column(String(50), nullable=False)  # financial, health, career, personal
    date_value = Column(Date, nullable=False, index=True)
    
    # Reminder settings
    reminder_days = Column(Integer, default=7)  # days before to send reminder
    is_recurring = Column(Boolean, default=False)
    recurrence_pattern = Column(String(100))  # yearly, monthly, weekly
    
    # Additional information
    description = Column(Text)
    is_active = Column(Boolean, default=True)
    
    # Reminder tracking
    last_reminder_sent = Column(DateTime(timezone=True))
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User")
    
    # Validation
    @validates('date_type')
    def validate_date_type(self, key, date_type):
        """Validate date type."""
        valid_types = ['financial', 'health', 'career', 'personal', 'family', 'legal']
        if date_type not in valid_types:
            raise ValueError(f"Date type must be one of: {valid_types}")
        return date_type
    
    @validates('reminder_days')
    def validate_reminder_days(self, key, days):
        """Validate reminder days."""
        if days < 0:
            raise ValueError("Reminder days cannot be negative")
        return days
    
    @validates('recurrence_pattern')
    def validate_recurrence_pattern(self, key, pattern):
        """Validate recurrence pattern."""
        if pattern:
            valid_patterns = ['yearly', 'monthly', 'weekly', 'daily']
            if pattern not in valid_patterns:
                raise ValueError(f"Recurrence pattern must be one of: {valid_patterns}")
        return pattern
    
    # Properties
    @property
    def is_overdue(self):
        """Check if date is overdue."""
        return date.today() > self.date_value
    
    @property
    def days_until_due(self):
        """Calculate days until due date."""
        delta = self.date_value - date.today()
        return max(0, delta.days)
    
    @property
    def days_overdue(self):
        """Calculate days overdue."""
        if not self.is_overdue:
            return 0
        return (date.today() - self.date_value).days
    
    @property
    def should_send_reminder(self):
        """Check if reminder should be sent."""
        if not self.is_active:
            return False
        
        days_until = self.days_until_due
        return days_until <= self.reminder_days and days_until >= 0
    
    @property
    def next_occurrence(self):
        """Calculate next occurrence for recurring dates."""
        if not self.is_recurring or not self.date_value:
            return None
        
        today = date.today()
        next_date = self.date_value
        
        while next_date <= today:
            if self.recurrence_pattern == 'yearly':
                next_date = next_date.replace(year=next_date.year + 1)
            elif self.recurrence_pattern == 'monthly':
                # Simple monthly increment (doesn't handle month boundaries perfectly)
                if next_date.month == 12:
                    next_date = next_date.replace(year=next_date.year + 1, month=1)
                else:
                    next_date = next_date.replace(month=next_date.month + 1)
            elif self.recurrence_pattern == 'weekly':
                from datetime import timedelta
                next_date = next_date + timedelta(days=7)
            elif self.recurrence_pattern == 'daily':
                from datetime import timedelta
                next_date = next_date + timedelta(days=1)
        
        return next_date
    
    # Methods
    def mark_reminder_sent(self):
        """Mark reminder as sent."""
        self.last_reminder_sent = datetime.now(timezone.utc)
    
    def update_next_occurrence(self):
        """Update date to next occurrence for recurring dates."""
        if self.is_recurring and self.next_occurrence:
            self.date_value = self.next_occurrence
    
    def to_dict(self):
        """Convert important date to dictionary."""
        return {
            'id': str(self.id),
            'user_id': str(self.user_id),
            'date_name': self.date_name,
            'date_type': self.date_type,
            'date_value': self.date_value.isoformat() if self.date_value else None,
            'reminder_days': self.reminder_days,
            'is_recurring': self.is_recurring,
            'recurrence_pattern': self.recurrence_pattern,
            'description': self.description,
            'is_active': self.is_active,
            'last_reminder_sent': self.last_reminder_sent.isoformat() if self.last_reminder_sent else None,
            'is_overdue': self.is_overdue,
            'days_until_due': self.days_until_due,
            'days_overdue': self.days_overdue,
            'should_send_reminder': self.should_send_reminder,
            'next_occurrence': self.next_occurrence.isoformat() if self.next_occurrence else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f"<ImportantDate(id={self.id}, user_id={self.user_id}, name='{self.date_name}', date={self.date_value})>"


class NotificationPreference(Base):
    """User notification preferences."""
    
    __tablename__ = 'notification_preferences'
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign key
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Notification type
    notification_type = Column(String(50), nullable=False)  # email, sms, push, in_app
    
    # Channel preferences
    email_enabled = Column(Boolean, default=True)
    sms_enabled = Column(Boolean, default=False)
    push_enabled = Column(Boolean, default=True)
    
    # Frequency settings
    frequency = Column(String(20), default='immediate')  # immediate, daily, weekly
    
    # Quiet hours
    quiet_hours_start = Column(Time)
    quiet_hours_end = Column(Time)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User")
    
    # Constraints
    __table_args__ = (
        # Ensure unique notification type per user
        ('uq_user_notification_type', 'user_id', 'notification_type'),
    )
    
    # Validation
    @validates('notification_type')
    def validate_notification_type(self, key, notification_type):
        """Validate notification type."""
        valid_types = ['email', 'sms', 'push', 'in_app', 'financial', 'health', 'career', 'system']
        if notification_type not in valid_types:
            raise ValueError(f"Notification type must be one of: {valid_types}")
        return notification_type
    
    @validates('frequency')
    def validate_frequency(self, key, frequency):
        """Validate frequency."""
        valid_frequencies = ['immediate', 'daily', 'weekly', 'monthly']
        if frequency not in valid_frequencies:
            raise ValueError(f"Frequency must be one of: {valid_frequencies}")
        return frequency
    
    # Properties
    @property
    def is_enabled(self):
        """Check if any notification channel is enabled."""
        return self.email_enabled or self.sms_enabled or self.push_enabled
    
    @property
    def enabled_channels(self):
        """Get list of enabled notification channels."""
        channels = []
        if self.email_enabled:
            channels.append('email')
        if self.sms_enabled:
            channels.append('sms')
        if self.push_enabled:
            channels.append('push')
        return channels
    
    @property
    def is_quiet_hours(self):
        """Check if current time is within quiet hours."""
        if not self.quiet_hours_start or not self.quiet_hours_end:
            return False
        
        now = datetime.now().time()
        start = self.quiet_hours_start
        end = self.quiet_hours_end
        
        if start <= end:
            # Same day quiet hours (e.g., 22:00 to 08:00)
            return start <= now <= end
        else:
            # Overnight quiet hours (e.g., 22:00 to 08:00)
            return now >= start or now <= end
    
    @property
    def can_send_notification(self):
        """Check if notification can be sent (enabled and not quiet hours)."""
        return self.is_enabled and not self.is_quiet_hours
    
    # Methods
    def enable_channel(self, channel):
        """Enable a specific notification channel."""
        if channel == 'email':
            self.email_enabled = True
        elif channel == 'sms':
            self.sms_enabled = True
        elif channel == 'push':
            self.push_enabled = True
    
    def disable_channel(self, channel):
        """Disable a specific notification channel."""
        if channel == 'email':
            self.email_enabled = False
        elif channel == 'sms':
            self.sms_enabled = False
        elif channel == 'push':
            self.push_enabled = False
    
    def set_quiet_hours(self, start_time, end_time):
        """Set quiet hours."""
        self.quiet_hours_start = start_time
        self.quiet_hours_end = end_time
    
    def to_dict(self):
        """Convert notification preference to dictionary."""
        return {
            'id': str(self.id),
            'user_id': str(self.user_id),
            'notification_type': self.notification_type,
            'email_enabled': self.email_enabled,
            'sms_enabled': self.sms_enabled,
            'push_enabled': self.push_enabled,
            'frequency': self.frequency,
            'quiet_hours_start': self.quiet_hours_start.isoformat() if self.quiet_hours_start else None,
            'quiet_hours_end': self.quiet_hours_end.isoformat() if self.quiet_hours_end else None,
            'is_enabled': self.is_enabled,
            'enabled_channels': self.enabled_channels,
            'is_quiet_hours': self.is_quiet_hours,
            'can_send_notification': self.can_send_notification,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f"<NotificationPreference(id={self.id}, user_id={self.user_id}, type='{self.notification_type}', enabled={self.is_enabled})>" 