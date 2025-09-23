# Daily Outlook Notification System

## Overview

The Daily Outlook Notification System provides comprehensive push notification support for the Mingus Personal Finance Application. It includes scheduled daily outlook notifications, personalized content, timezone-aware delivery, and rich notification features with action buttons and deep linking.

## Features

### 🚀 Core Features
- **Daily Outlook Push Notifications** - Scheduled notifications for personalized daily insights
- **Custom Timing Preferences** - Different notification times for weekdays vs weekends
- **Timezone-Aware Delivery** - Intelligent scheduling based on user's timezone
- **Rich Notifications** - Action buttons, previews, and interactive elements
- **Deep Linking** - Direct navigation to specific app sections
- **Engagement Tracking** - Comprehensive analytics on notification interactions

### 📱 Notification Types
- **Daily Outlook** - Personalized daily insights and actions
- **Streak Milestones** - Celebration of user achievements
- **Recovery Notifications** - Gentle reminders for missed days
- **Reminder Notifications** - Custom user-set reminders

### 🎯 Personalization
- **Balance Score Integration** - Notifications reflect user's daily balance score
- **Streak Tracking** - Milestone celebrations and motivation
- **Cultural Relevance** - African American professional focus
- **Content Preview** - Rich previews of daily insights
- **Action Buttons** - Quick actions directly from notifications

## Architecture

### Frontend Components

#### 1. NotificationService (`frontend/src/services/notificationService.ts`)
- Push notification subscription management
- Permission handling and request
- Preference management
- Interaction tracking
- Test notification functionality

#### 2. NotificationSettings (`frontend/src/components/NotificationSettings.tsx`)
- User preference configuration
- Permission management
- Test notification controls
- Timezone selection
- Notification channel preferences

#### 3. RichNotification (`frontend/src/components/RichNotification.tsx`)
- Interactive notification display
- Action button handling
- Engagement tracking
- Balance score visualization
- Streak information display

#### 4. Service Worker (`public/sw.js`)
- Push notification handling
- Background sync
- Notification interaction tracking
- Offline functionality

### Backend Components

#### 1. NotificationService (`backend/services/notification_service.py`)
- Scheduled notification delivery
- Personalized content generation
- Multi-channel delivery (push, email, SMS)
- Analytics and tracking
- Template management

#### 2. Database Models (`backend/models/notification_models.py`)
- `UserNotificationPreferences` - User notification settings
- `PushSubscription` - Push notification endpoints
- `NotificationDelivery` - Delivery tracking
- `NotificationInteraction` - Interaction analytics
- `NotificationTemplate` - Reusable templates

#### 3. API Endpoints (`backend/api/notification_api.py`)
- Subscription management
- Preference updates
- Interaction tracking
- Analytics reporting
- Template management

## Database Schema

### UserNotificationPreferences
```sql
CREATE TABLE user_notification_preferences (
    user_id INTEGER PRIMARY KEY,
    daily_outlook_enabled BOOLEAN DEFAULT TRUE,
    weekday_time TIME DEFAULT '06:45',
    weekend_time TIME DEFAULT '08:30',
    push_enabled BOOLEAN DEFAULT TRUE,
    email_enabled BOOLEAN DEFAULT TRUE,
    sms_enabled BOOLEAN DEFAULT FALSE,
    sound_enabled BOOLEAN DEFAULT TRUE,
    vibration_enabled BOOLEAN DEFAULT TRUE,
    rich_notifications BOOLEAN DEFAULT TRUE,
    action_buttons BOOLEAN DEFAULT TRUE,
    timezone VARCHAR(50) DEFAULT 'UTC',
    quiet_hours_start TIME,
    quiet_hours_end TIME,
    max_notifications_per_day INTEGER DEFAULT 5,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### PushSubscription
```sql
CREATE TABLE push_subscriptions (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    endpoint TEXT NOT NULL,
    p256dh_key TEXT NOT NULL,
    auth_key TEXT NOT NULL,
    user_agent VARCHAR(500),
    ip_address VARCHAR(45),
    is_active BOOLEAN DEFAULT TRUE,
    last_used TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### NotificationDelivery
```sql
CREATE TABLE notification_deliveries (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    notification_id VARCHAR(255) NOT NULL,
    notification_type VARCHAR(50) NOT NULL,
    channel VARCHAR(20) NOT NULL,
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    action_url VARCHAR(500),
    scheduled_time TIMESTAMP NOT NULL,
    sent_at TIMESTAMP,
    delivered_at TIMESTAMP,
    clicked_at TIMESTAMP,
    status VARCHAR(20) DEFAULT 'pending',
    error_message TEXT,
    delivery_metadata JSON,
    is_opened BOOLEAN DEFAULT FALSE,
    action_taken VARCHAR(100),
    engagement_data JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Setup and Configuration

### 1. Environment Variables

```bash
# VAPID Keys for Web Push
VAPID_PRIVATE_KEY=your_vapid_private_key
VAPID_PUBLIC_KEY=your_vapid_public_key

# FCM Configuration (for Android)
FCM_SERVER_KEY=your_fcm_server_key

# APNS Configuration (for iOS)
APNS_CERTIFICATE_PATH=/path/to/apns_cert.pem
APNS_KEY_ID=your_apns_key_id
APNS_TEAM_ID=your_apns_team_id

# Notification Settings
NOTIFICATION_ENABLED=true
DEFAULT_WEEKDAY_TIME=06:45
DEFAULT_WEEKEND_TIME=08:30
```

### 2. Frontend Setup

1. **Register Service Worker**
```javascript
// In your main app file
if ('serviceWorker' in navigator) {
  navigator.serviceWorker.register('/sw.js');
}
```

2. **Initialize Notification Service**
```javascript
import NotificationService from './services/notificationService';

const notificationService = NotificationService.getInstance();
```

3. **Request Permissions**
```javascript
const permission = await notificationService.requestPermission();
if (permission.granted) {
  await notificationService.subscribeToDailyOutlookNotifications(preferences);
}
```

### 3. Backend Setup

1. **Install Dependencies**
```bash
pip install pywebpush celery redis pytz
```

2. **Database Migration**
```python
# Run database migrations to create notification tables
flask db upgrade
```

3. **Register API Blueprint**
```python
from backend.api.notification_api import notification_bp
app.register_blueprint(notification_bp)
```

## Usage Examples

### Frontend Usage

#### Subscribe to Notifications
```javascript
const notificationService = NotificationService.getInstance();

// Request permission
const permission = await notificationService.requestPermission();

if (permission.granted) {
  // Subscribe with preferences
  const success = await notificationService.subscribeToDailyOutlookNotifications({
    dailyOutlookEnabled: true,
    weekdayTime: '06:45',
    weekendTime: '08:30',
    timezone: 'America/New_York',
    soundEnabled: true,
    vibrationEnabled: true,
    richNotifications: true,
    actionButtons: true
  });
}
```

#### Update Preferences
```javascript
const success = await notificationService.updateNotificationPreferences({
  weekdayTime: '07:00',
  weekendTime: '09:00',
  soundEnabled: false
});
```

#### Send Test Notification
```javascript
const success = await notificationService.sendTestNotification();
```

### Backend Usage

#### Schedule Daily Outlook Notifications
```python
from backend.services.notification_service import NotificationService

notification_service = NotificationService()

# Schedule notifications for today
result = notification_service.schedule_daily_outlook_notifications()

# Schedule for specific date
result = notification_service.schedule_daily_outlook_notifications(
    target_date=date(2024, 1, 15)
)
```

#### Create Personalized Notification
```python
# Get user and outlook
user = User.query.get(user_id)
outlook = DailyOutlook.query.filter_by(user_id=user_id, date=target_date).first()

# Create notification content
content = notification_service.create_daily_outlook_notification(
    user, outlook, preferences
)

# Send notification
success = notification_service.send_push_notification(
    user_id, content, push_subscription
)
```

## API Endpoints

### Notification Management
- `POST /api/notifications/subscribe` - Subscribe to push notifications
- `POST /api/notifications/unsubscribe` - Unsubscribe from notifications
- `GET /api/notifications/preferences` - Get notification preferences
- `PUT /api/notifications/preferences` - Update notification preferences

### Testing and Analytics
- `POST /api/notifications/test` - Send test notification
- `POST /api/notifications/track` - Track notification interaction
- `GET /api/notifications/history` - Get notification history
- `GET /api/notifications/stats` - Get notification statistics

### Scheduling
- `POST /api/notifications/schedule` - Schedule daily outlook notifications

## Rich Notification Features

### Action Buttons
```javascript
const notification = {
  title: "Your Daily Outlook is Ready! 🌅",
  body: "Good morning! Your personalized insights await.",
  actions: [
    {
      action: "view_outlook",
      title: "View Outlook",
      icon: "/icons/view-icon.png"
    },
    {
      action: "quick_action",
      title: "Quick Action",
      icon: "/icons/action-icon.png"
    }
  ]
};
```

### Deep Linking
```javascript
const notification = {
  title: "Daily Outlook Ready",
  body: "Check your balance score and insights",
  data: {
    url: "/daily-outlook/2024-01-15",
    screen: "DailyOutlook",
    params: {
      date: "2024-01-15",
      user_id: "123"
    }
  }
};
```

### Rich Content Preview
```javascript
const notification = {
  title: "🌟 Excellent day ahead, John!",
  body: "Your balance score is 85/100. Today's insight: Focus on your investment portfolio...",
  icon: "/icons/icon-192x192.png",
  badge: "/icons/badge-72x72.png",
  image: "/images/daily-outlook-preview.png"
};
```

## Analytics and Tracking

### Interaction Types
- `clicked` - User clicked on notification
- `dismissed` - User dismissed notification
- `action_taken` - User took a specific action
- `viewed` - User viewed the notification

### Metrics Tracked
- Total notifications sent
- Delivery rates by channel
- Click-through rates
- Action completion rates
- User engagement patterns
- Timezone-based performance

### Analytics API
```javascript
// Get notification statistics
const stats = await notificationService.getNotificationStats();
console.log(stats);
// {
//   totalSent: 150,
//   totalDelivered: 145,
//   totalClicked: 89,
//   clickRate: 61.38,
//   deliveryRate: 96.67
// }
```

## Security Considerations

### Data Protection
- All notification data is encrypted in transit
- User preferences are stored securely
- Push subscription data is protected
- Analytics data is anonymized

### Privacy Controls
- Users can disable all notifications
- Granular control over notification types
- Quiet hours support
- Maximum daily notification limits

### Authentication
- All API endpoints require authentication
- Push subscriptions are user-specific
- Notification delivery is user-scoped

## Performance Optimization

### Caching
- Service worker caches notification data
- Background sync for offline functionality
- Efficient notification queuing

### Delivery Optimization
- Timezone-aware scheduling
- Batch processing for efficiency
- Retry logic for failed deliveries
- Rate limiting to prevent spam

### Analytics Optimization
- Asynchronous tracking
- Batch analytics updates
- Efficient database queries
- Indexed database tables

## Troubleshooting

### Common Issues

#### Notifications Not Received
1. Check browser notification permissions
2. Verify service worker registration
3. Check push subscription status
4. Validate VAPID keys

#### Permission Denied
1. Clear browser data and retry
2. Check browser notification settings
3. Verify HTTPS requirement
4. Check service worker support

#### Delivery Failures
1. Check push subscription validity
2. Verify notification service configuration
3. Check network connectivity
4. Review error logs

### Debug Tools
- Browser developer tools
- Service worker debugging
- Network tab for API calls
- Console logs for errors

## Future Enhancements

### Planned Features
- **Smart Scheduling** - AI-powered optimal notification timing
- **A/B Testing** - Content optimization through testing
- **Advanced Analytics** - Machine learning insights
- **Multi-language Support** - Internationalization
- **Voice Notifications** - Audio notification support

### Integration Opportunities
- **Calendar Integration** - Schedule-based notifications
- **Weather Integration** - Weather-aware content
- **Location Services** - Location-based notifications
- **Wearable Support** - Smartwatch notifications

## Support and Maintenance

### Monitoring
- Notification delivery rates
- User engagement metrics
- System performance
- Error rates and patterns

### Maintenance Tasks
- Regular database cleanup
- Performance optimization
- Security updates
- Feature enhancements

### Support Channels
- User documentation
- Developer guides
- API documentation
- Community forums

---

This notification system provides a comprehensive solution for Daily Outlook push notifications with rich features, analytics, and user control. It integrates seamlessly with the existing Mingus application architecture and provides a foundation for future notification enhancements.
