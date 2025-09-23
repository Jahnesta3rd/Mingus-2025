// Service Worker for Mingus Daily Outlook Notifications
// Handles push notifications, background sync, and notification interactions

const CACHE_NAME = 'mingus-notifications-v1';
const NOTIFICATION_TAG = 'daily-outlook';

// Install event
self.addEventListener('install', (event) => {
  console.log('Service Worker installing...');
  self.skipWaiting();
});

// Activate event
self.addEventListener('activate', (event) => {
  console.log('Service Worker activating...');
  event.waitUntil(
    self.clients.claim()
  );
});

// Push event - handle incoming push notifications
self.addEventListener('push', (event) => {
  console.log('Push event received:', event);
  
  if (!event.data) {
    console.log('Push event but no data');
    return;
  }

  try {
    const data = event.data.json();
    console.log('Push data:', data);
    
    const options = {
      body: data.body || 'Your Daily Outlook is ready!',
      icon: data.icon || '/icons/icon-192x192.png',
      badge: data.badge || '/icons/badge-72x72.png',
      tag: data.tag || NOTIFICATION_TAG,
      requireInteraction: data.requireInteraction || true,
      data: data.data || {},
      actions: data.actions || [
        {
          action: 'view',
          title: 'View Outlook',
          icon: '/icons/view-icon.png'
        },
        {
          action: 'dismiss',
          title: 'Dismiss',
          icon: '/icons/dismiss-icon.png'
        }
      ],
      vibrate: data.vibrate || [200, 100, 200],
      silent: data.silent || false
    };

    event.waitUntil(
      self.registration.showNotification(data.title || 'Daily Outlook', options)
    );
  } catch (error) {
    console.error('Error handling push event:', error);
    
    // Fallback notification
    event.waitUntil(
      self.registration.showNotification('Daily Outlook', {
        body: 'Your Daily Outlook is ready!',
        icon: '/icons/icon-192x192.png',
        tag: NOTIFICATION_TAG
      })
    );
  }
});

// Notification click event
self.addEventListener('notificationclick', (event) => {
  console.log('Notification clicked:', event);
  
  event.notification.close();
  
  const action = event.action;
  const notificationData = event.notification.data || {};
  
  // Track the click
  if (action === 'view' || !action) {
    // Open the app or navigate to the outlook
    event.waitUntil(
      self.clients.matchAll({ type: 'window' }).then((clients) => {
        const url = notificationData.url || '/daily-outlook';
        
        // Check if there's already a window open
        for (const client of clients) {
          if (client.url.includes(url) && 'focus' in client) {
            return client.focus();
          }
        }
        
        // Open a new window
        if (self.clients.openWindow) {
          return self.clients.openWindow(url);
        }
      })
    );
  } else if (action === 'dismiss') {
    // Just close the notification (already closed above)
    console.log('Notification dismissed');
  } else if (action === 'quick_action') {
    // Handle quick action
    event.waitUntil(
      self.clients.matchAll({ type: 'window' }).then((clients) => {
        if (clients.length > 0) {
          clients[0].postMessage({
            type: 'QUICK_ACTION',
            data: notificationData
          });
        }
      })
    );
  }
  
  // Send analytics event
  sendAnalyticsEvent('notification_clicked', {
    action: action || 'view',
    notification_id: notificationData.notification_id,
    timestamp: new Date().toISOString()
  });
});

// Background sync for offline functionality
self.addEventListener('sync', (event) => {
  console.log('Background sync:', event.tag);
  
  if (event.tag === 'notification-sync') {
    event.waitUntil(syncNotifications());
  }
});

// Message event for communication with main thread
self.addEventListener('message', (event) => {
  console.log('Service Worker message:', event.data);
  
  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }
});

// Helper function to sync notifications
async function syncNotifications() {
  try {
    // This would sync any pending notification interactions
    // when the app comes back online
    console.log('Syncing notifications...');
    
    // In a real implementation, this would:
    // 1. Send any pending interaction data to the server
    // 2. Update local storage
    // 3. Handle any queued notifications
    
  } catch (error) {
    console.error('Error syncing notifications:', error);
  }
}

// Helper function to send analytics events
async function sendAnalyticsEvent(eventName, eventData) {
  try {
    // Send analytics event to the server
    const response = await fetch('/api/analytics/events', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        event: eventName,
        data: eventData,
        timestamp: new Date().toISOString(),
        source: 'service_worker'
      })
    });
    
    if (!response.ok) {
      console.error('Failed to send analytics event:', response.status);
    }
  } catch (error) {
    console.error('Error sending analytics event:', error);
  }
}

// Handle notification close event
self.addEventListener('notificationclose', (event) => {
  console.log('Notification closed:', event);
  
  // Track notification dismissal
  sendAnalyticsEvent('notification_dismissed', {
    notification_id: event.notification.data?.notification_id,
    timestamp: new Date().toISOString()
  });
});

// Handle push subscription changes
self.addEventListener('pushsubscriptionchange', (event) => {
  console.log('Push subscription changed:', event);
  
  event.waitUntil(
    // Re-subscribe to push notifications
    self.registration.pushManager.subscribe({
      userVisibleOnly: true,
      applicationServerKey: self.registration.pushManager.getSubscription()
        .then(subscription => subscription.options.applicationServerKey)
    }).then(subscription => {
      // Send new subscription to server
      return fetch('/api/notifications/subscribe', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          subscription: subscription,
          action: 'resubscribe'
        })
      });
    })
  );
});

console.log('Service Worker loaded successfully');
