#!/usr/bin/env python3
"""
Mingus Application - Database Models Package
SQLAlchemy models for the Mingus financial application
"""

from .database import db
from .user_models import User
from .vehicle_models import Vehicle, MaintenancePrediction, CommuteScenario, MSAGasPrice
from .housing_models import HousingSearch, HousingScenario, UserHousingPreferences, CommuteRouteCache, HousingType
from .daily_outlook import DailyOutlook, UserRelationshipStatus, DailyOutlookTemplate, RelationshipStatus, TemplateTier, TemplateCategory
from .notification_models import (
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

__all__ = [
    'db',
    'User', 
    'Vehicle',
    'MaintenancePrediction', 
    'CommuteScenario',
    'MSAGasPrice',
    'HousingSearch',
    'HousingScenario',
    'UserHousingPreferences',
    'CommuteRouteCache',
    'HousingType',
    'DailyOutlook',
    'UserRelationshipStatus',
    'DailyOutlookTemplate',
    'RelationshipStatus',
    'TemplateTier',
    'TemplateCategory',
    'UserNotificationPreferences',
    'PushSubscription',
    'NotificationDelivery',
    'NotificationInteraction',
    'NotificationTemplate',
    'NotificationChannel',
    'NotificationType',
    'DeliveryStatus',
    'InteractionType'
]
