# Daily Outlook Notification System - Testing Guide

## 🧪 Testing Overview

This guide provides comprehensive instructions for testing the Daily Outlook notification system. The system includes both frontend and backend components that need to be tested to ensure proper functionality.

## 🚀 Quick Start Testing

### 1. Frontend Testing

Navigate to the notification test suite:
```
http://localhost:3000/notification-test
```

This will open the comprehensive test interface where you can:
- Run all tests automatically
- Test individual components
- View real-time results
- Debug issues

### 2. Backend Testing

Run the backend test suite:
```bash
cd backend
python test_notification_system.py
```

## 📱 Frontend Testing

### Browser Compatibility Testing

#### Test 1: Browser Support Check
1. Open the test suite at `/notification-test`
2. Check the "Browser Support" status
3. Verify that your browser supports:
   - Notifications API
   - Service Worker
   - Push Manager

**Expected Result**: ✅ Browser Support: Notifications are supported

#### Test 2: Permission Request
1. Click "Test Permission" button
2. Browser should prompt for notification permission
3. Grant permission when prompted

**Expected Result**: ✅ Permission Test: Permission result: granted

#### Test 3: Push Subscription
1. Click "Test Subscription" button
2. System should subscribe to push notifications
3. Check subscription status

**Expected Result**: ✅ Subscription Test: Subscription successful

#### Test 4: Test Notification
1. Click "Send Test Notification" button
2. You should receive a test notification
3. Click on the notification to test deep linking

**Expected Result**: ✅ Test Notification: Test notification sent

#### Test 5: Preferences Management
1. Click "Test Preferences" button
2. System should load and save preferences
3. Check that preferences are persisted

**Expected Result**: ✅ Preferences Test: Preferences loaded

### Manual Testing Scenarios

#### Scenario 1: First-Time User Setup
1. Clear browser data (localStorage, cookies)
2. Navigate to `/settings` → Notifications tab
3. Enable Daily Outlook notifications
4. Set custom times (e.g., 7:00 AM weekdays, 9:00 AM weekends)
5. Grant notification permission
6. Send test notification

**Expected Result**: User receives test notification at specified time

#### Scenario 2: Notification Settings
1. Go to Settings → Notifications
2. Toggle different options:
   - Sound enabled/disabled
   - Vibration enabled/disabled
   - Rich notifications enabled/disabled
   - Action buttons enabled/disabled
3. Save preferences
4. Send test notification

**Expected Result**: Notification behavior changes based on settings

#### Scenario 3: Timezone Testing
1. Change system timezone
2. Update notification preferences
3. Set different notification times
4. Test scheduling

**Expected Result**: Notifications scheduled according to user's timezone

## 🔧 Backend Testing

### Database Model Testing

#### Test 1: Model Creation
```bash
cd backend
python -c "
from backend.models.notification_models import UserNotificationPreferences
prefs = UserNotificationPreferences(user_id=1, daily_outlook_enabled=True)
print('✅ Model creation successful')
"
```

#### Test 2: Model Serialization
```bash
python -c "
from backend.models.notification_models import UserNotificationPreferences
prefs = UserNotificationPreferences(user_id=1, daily_outlook_enabled=True)
prefs_dict = prefs.to_dict()
print('✅ Model serialization successful')
print(f'Keys: {list(prefs_dict.keys())}')
"
```

### Service Testing

#### Test 1: Notification Service
```bash
python -c "
from backend.services.notification_service import NotificationService
service = NotificationService()
print('✅ Notification service initialized')
print(f'Default preferences: {service.default_preferences}')
"
```

#### Test 2: Content Generation
```bash
python -c "
from backend.services.notification_service import NotificationService
service = NotificationService()

# Mock user and outlook
class MockUser:
    first_name = 'Test'
    email = 'test@example.com'

class MockOutlook:
    balance_score = 85
    streak_count = 5
    primary_insight = 'Great progress!'
    date = '2024-01-15'

user = MockUser()
outlook = MockOutlook()
preferences = {'daily_outlook_enabled': True}

content = service.create_daily_outlook_notification(user, outlook, preferences)
print('✅ Content generation successful')
print(f'Title: {content.title}')
print(f'Message: {content.message}')
"
```

### API Testing

#### Test 1: Health Check
```bash
curl -X GET http://localhost:5000/api/notifications/preferences \
  -H "Authorization: Bearer test-token" \
  -H "Content-Type: application/json"
```

#### Test 2: Subscription Test
```bash
curl -X POST http://localhost:5000/api/notifications/subscribe \
  -H "Authorization: Bearer test-token" \
  -H "Content-Type: application/json" \
  -d '{
    "subscription": {
      "endpoint": "https://fcm.googleapis.com/fcm/send/test",
      "keys": {
        "p256dh": "test-key",
        "auth": "test-auth"
      }
    },
    "preferences": {
      "dailyOutlookEnabled": true,
      "weekdayTime": "06:45",
      "weekendTime": "08:30"
    }
  }'
```

#### Test 3: Test Notification
```bash
curl -X POST http://localhost:5000/api/notifications/test \
  -H "Authorization: Bearer test-token" \
  -H "Content-Type: application/json"
```

## 🎯 Integration Testing

### End-to-End Testing

#### Test 1: Complete Notification Flow
1. **Setup**: User subscribes to notifications
2. **Scheduling**: System schedules daily outlook notification
3. **Delivery**: Notification is sent at scheduled time
4. **Interaction**: User clicks notification
5. **Tracking**: System tracks interaction
6. **Analytics**: System updates engagement metrics

#### Test 2: Multi-User Testing
1. Create multiple test users
2. Set different notification preferences
3. Schedule notifications for all users
4. Verify timezone handling
5. Check delivery rates

#### Test 3: Error Handling
1. Test with invalid subscription data
2. Test with network failures
3. Test with permission denied
4. Verify graceful error handling

## 📊 Performance Testing

### Load Testing

#### Test 1: Notification Scheduling
```bash
# Test scheduling for multiple users
python -c "
from backend.services.notification_service import NotificationService
import time

service = NotificationService()
start_time = time.time()

# Simulate scheduling for 1000 users
for i in range(1000):
    result = service.schedule_daily_outlook_notifications()
    
end_time = time.time()
print(f'✅ Scheduled 1000 notifications in {end_time - start_time:.2f} seconds')
"
```

#### Test 2: Database Performance
```bash
# Test database query performance
python -c "
from backend.models.notification_models import NotificationDelivery
import time

start_time = time.time()
deliveries = NotificationDelivery.query.limit(1000).all()
end_time = time.time()

print(f'✅ Queried 1000 records in {end_time - start_time:.2f} seconds')
"
```

## 🐛 Debugging Guide

### Common Issues and Solutions

#### Issue 1: Notifications Not Received
**Symptoms**: User doesn't receive notifications
**Debug Steps**:
1. Check browser notification permissions
2. Verify service worker registration
3. Check push subscription status
4. Review browser console for errors

**Solutions**:
```javascript
// Check service worker status
navigator.serviceWorker.getRegistrations().then(registrations => {
  console.log('Service workers:', registrations);
});

// Check notification permission
console.log('Notification permission:', Notification.permission);

// Check push subscription
navigator.serviceWorker.ready.then(registration => {
  registration.pushManager.getSubscription().then(subscription => {
    console.log('Push subscription:', subscription);
  });
});
```

#### Issue 2: Permission Denied
**Symptoms**: Permission request fails
**Debug Steps**:
1. Check if notifications are blocked in browser settings
2. Verify HTTPS requirement
3. Check browser compatibility

**Solutions**:
```javascript
// Request permission with error handling
Notification.requestPermission().then(permission => {
  if (permission === 'granted') {
    console.log('Permission granted');
  } else {
    console.log('Permission denied:', permission);
  }
}).catch(error => {
  console.error('Permission error:', error);
});
```

#### Issue 3: Service Worker Issues
**Symptoms**: Service worker not working
**Debug Steps**:
1. Check service worker registration
2. Verify service worker file exists
3. Check browser developer tools

**Solutions**:
```javascript
// Register service worker with error handling
if ('serviceWorker' in navigator) {
  navigator.serviceWorker.register('/sw.js')
    .then(registration => {
      console.log('Service worker registered:', registration);
    })
    .catch(error => {
      console.error('Service worker registration failed:', error);
    });
}
```

### Debug Tools

#### Browser Developer Tools
1. **Application Tab**: Check service worker status
2. **Console Tab**: View error messages
3. **Network Tab**: Monitor API calls
4. **Storage Tab**: Check localStorage data

#### Backend Debugging
```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Test notification service
from backend.services.notification_service import NotificationService
service = NotificationService()

# Check service status
print(f"Service initialized: {service is not None}")
print(f"Default preferences: {service.default_preferences}")
```

## 📈 Analytics Testing

### Engagement Tracking

#### Test 1: Click Tracking
1. Send test notification
2. Click on notification
3. Check analytics data

```bash
# Check interaction tracking
curl -X POST http://localhost:5000/api/notifications/track \
  -H "Authorization: Bearer test-token" \
  -H "Content-Type: application/json" \
  -d '{
    "notification_id": "test-123",
    "action": "clicked",
    "actionData": {"url": "/daily-outlook"}
  }'
```

#### Test 2: Analytics Dashboard
1. Generate multiple notifications
2. Track various interactions
3. Check analytics endpoint

```bash
# Get notification statistics
curl -X GET http://localhost:5000/api/notifications/stats \
  -H "Authorization: Bearer test-token"
```

## 🔒 Security Testing

### Authentication Testing
1. Test API endpoints without authentication
2. Verify token validation
3. Check user-specific data access

### Data Privacy Testing
1. Verify notification data encryption
2. Test user preference privacy
3. Check analytics data anonymization

## 📱 Mobile Testing

### iOS Testing
1. Test on Safari browser
2. Verify APNS integration
3. Check notification display

### Android Testing
1. Test on Chrome browser
2. Verify FCM integration
3. Check notification actions

## 🚀 Production Testing

### Pre-Deployment Checklist
- [ ] All unit tests pass
- [ ] Integration tests pass
- [ ] Performance tests pass
- [ ] Security tests pass
- [ ] Mobile compatibility verified
- [ ] Error handling tested
- [ ] Analytics working
- [ ] Database migrations complete

### Deployment Testing
1. Deploy to staging environment
2. Run full test suite
3. Test with real users
4. Monitor performance metrics
5. Check error rates

## 📞 Support and Troubleshooting

### Getting Help
1. Check the test suite results
2. Review browser console errors
3. Check backend logs
4. Verify database connectivity
5. Test network connectivity

### Reporting Issues
When reporting issues, include:
- Browser type and version
- Operating system
- Test results from the test suite
- Console error messages
- Steps to reproduce

---

This testing guide ensures comprehensive validation of the Daily Outlook notification system. Follow these steps to verify that all components are working correctly before deploying to production.
