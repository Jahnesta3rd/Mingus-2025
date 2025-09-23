import { Platform } from 'react-native';

export interface NotificationPreferences {
  dailyOutlookEnabled: boolean;
  weekdayTime: string; // HH:MM format
  weekendTime: string; // HH:MM format
  timezone: string;
  soundEnabled: boolean;
  vibrationEnabled: boolean;
  richNotifications: boolean;
  actionButtons: boolean;
}

export interface DailyOutlookNotification {
  id: string;
  title: string;
  message: string;
  preview: string;
  balanceScore: number;
  streakCount: number;
  actionUrl: string;
  scheduledTime: string;
  isDelivered: boolean;
  deliveredAt?: string;
  clickedAt?: string;
  actionTaken?: string;
}

export interface NotificationPermission {
  granted: boolean;
  canRequest: boolean;
  status: 'granted' | 'denied' | 'not-determined' | 'provisional';
}

class NotificationService {
  private static instance: NotificationService;
  private serviceWorkerRegistration: ServiceWorkerRegistration | null = null;
  private pushSubscription: PushSubscription | null = null;

  private constructor() {
    this.initializeServiceWorker();
  }

  public static getInstance(): NotificationService {
    if (!NotificationService.instance) {
      NotificationService.instance = new NotificationService();
    }
    return NotificationService.instance;
  }

  private async initializeServiceWorker(): Promise<void> {
    if ('serviceWorker' in navigator) {
      try {
        this.serviceWorkerRegistration = await navigator.serviceWorker.register('/sw.js');
        console.log('Service Worker registered successfully');
      } catch (error) {
        console.error('Service Worker registration failed:', error);
      }
    }
  }

  /**
   * Request notification permissions from the user
   */
  public async requestPermission(): Promise<NotificationPermission> {
    if (!('Notification' in window)) {
      return {
        granted: false,
        canRequest: false,
        status: 'denied'
      };
    }

    if (Notification.permission === 'granted') {
      return {
        granted: true,
        canRequest: false,
        status: 'granted'
      };
    }

    if (Notification.permission === 'denied') {
      return {
        granted: false,
        canRequest: false,
        status: 'denied'
      };
    }

    try {
      const permission = await Notification.requestPermission();
      return {
        granted: permission === 'granted',
        canRequest: permission === 'default',
        status: permission as 'granted' | 'denied' | 'not-determined' | 'provisional'
      };
    } catch (error) {
      console.error('Error requesting notification permission:', error);
      return {
        granted: false,
        canRequest: false,
        status: 'denied'
      };
    }
  }

  /**
   * Subscribe to push notifications for Daily Outlook
   */
  public async subscribeToDailyOutlookNotifications(
    preferences: NotificationPreferences
  ): Promise<boolean> {
    try {
      // Check if service worker is available
      if (!this.serviceWorkerRegistration) {
        throw new Error('Service Worker not available');
      }

      // Subscribe to push notifications
      this.pushSubscription = await this.serviceWorkerRegistration.pushManager.subscribe({
        userVisibleOnly: true,
        applicationServerKey: this.urlBase64ToUint8Array(
          process.env.REACT_APP_VAPID_PUBLIC_KEY || ''
        )
      });

      // Send subscription to backend
      const response = await fetch('/api/notifications/subscribe', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('mingus_token')}`,
        },
        body: JSON.stringify({
          subscription: this.pushSubscription,
          preferences: preferences
        })
      });

      if (!response.ok) {
        throw new Error('Failed to subscribe to notifications');
      }

      return true;
    } catch (error) {
      console.error('Error subscribing to notifications:', error);
      return false;
    }
  }

  /**
   * Unsubscribe from push notifications
   */
  public async unsubscribeFromNotifications(): Promise<boolean> {
    try {
      if (this.pushSubscription) {
        await this.pushSubscription.unsubscribe();
        this.pushSubscription = null;
      }

      // Notify backend
      await fetch('/api/notifications/unsubscribe', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('mingus_token')}`,
        }
      });

      return true;
    } catch (error) {
      console.error('Error unsubscribing from notifications:', error);
      return false;
    }
  }

  /**
   * Update notification preferences
   */
  public async updateNotificationPreferences(
    preferences: Partial<NotificationPreferences>
  ): Promise<boolean> {
    try {
      const response = await fetch('/api/notifications/preferences', {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('mingus_token')}`,
        },
        body: JSON.stringify(preferences)
      });

      return response.ok;
    } catch (error) {
      console.error('Error updating notification preferences:', error);
      return false;
    }
  }

  /**
   * Get current notification preferences
   */
  public async getNotificationPreferences(): Promise<NotificationPreferences | null> {
    try {
      const response = await fetch('/api/notifications/preferences', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('mingus_token')}`,
        }
      });

      if (!response.ok) {
        return null;
      }

      return await response.json();
    } catch (error) {
      console.error('Error fetching notification preferences:', error);
      return null;
    }
  }

  /**
   * Send a test notification
   */
  public async sendTestNotification(): Promise<boolean> {
    try {
      const response = await fetch('/api/notifications/test', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('mingus_token')}`,
        }
      });

      return response.ok;
    } catch (error) {
      console.error('Error sending test notification:', error);
      return false;
    }
  }

  /**
   * Track notification interaction
   */
  public async trackNotificationInteraction(
    notificationId: string,
    action: 'clicked' | 'dismissed' | 'action_taken',
    actionData?: any
  ): Promise<void> {
    try {
      await fetch('/api/notifications/track', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('mingus_token')}`,
        },
        body: JSON.stringify({
          notificationId,
          action,
          actionData,
          timestamp: new Date().toISOString()
        })
      });
    } catch (error) {
      console.error('Error tracking notification interaction:', error);
    }
  }

  /**
   * Get notification delivery history
   */
  public async getNotificationHistory(
    limit: number = 50,
    offset: number = 0
  ): Promise<DailyOutlookNotification[]> {
    try {
      const response = await fetch(
        `/api/notifications/history?limit=${limit}&offset=${offset}`,
        {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('mingus_token')}`,
          }
        }
      );

      if (!response.ok) {
        return [];
      }

      return await response.json();
    } catch (error) {
      console.error('Error fetching notification history:', error);
      return [];
    }
  }

  /**
   * Schedule a local notification (for testing/preview)
   */
  public async scheduleLocalNotification(
    notification: Omit<DailyOutlookNotification, 'id' | 'isDelivered' | 'deliveredAt'>
  ): Promise<boolean> {
    try {
      if (!('Notification' in window) || Notification.permission !== 'granted') {
        return false;
      }

      const scheduledTime = new Date(notification.scheduledTime);
      const now = new Date();
      const delay = scheduledTime.getTime() - now.getTime();

      if (delay <= 0) {
        // Send immediately
        this.showLocalNotification(notification);
      } else {
        // Schedule for later
        setTimeout(() => {
          this.showLocalNotification(notification);
        }, delay);
      }

      return true;
    } catch (error) {
      console.error('Error scheduling local notification:', error);
      return false;
    }
  }

  private showLocalNotification(notification: Omit<DailyOutlookNotification, 'id' | 'isDelivered' | 'deliveredAt'>): void {
    const notificationOptions: NotificationOptions = {
      body: notification.message,
      icon: '/icons/icon-192x192.png',
      badge: '/icons/badge-72x72.png',
      tag: 'daily-outlook',
      requireInteraction: true,
      actions: notification.actionButtons ? [
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
      ] : undefined,
      data: {
        url: notification.actionUrl,
        notificationId: `local-${Date.now()}`
      }
    };

    const browserNotification = new Notification(notification.title, notificationOptions);

    browserNotification.onclick = () => {
      this.trackNotificationInteraction(
        notification.data?.notificationId || 'unknown',
        'clicked'
      );
      window.focus();
      window.location.href = notification.actionUrl;
      browserNotification.close();
    };

    // Auto-close after 10 seconds if not interacted with
    setTimeout(() => {
      browserNotification.close();
    }, 10000);
  }

  /**
   * Handle deep linking from notification clicks
   */
  public handleNotificationClick(url: string): void {
    // Navigate to the specified URL
    window.location.href = url;
  }

  /**
   * Check if notifications are supported
   */
  public isSupported(): boolean {
    return 'Notification' in window && 'serviceWorker' in navigator && 'PushManager' in window;
  }

  /**
   * Get notification statistics
   */
  public async getNotificationStats(): Promise<{
    totalSent: number;
    totalDelivered: number;
    totalClicked: number;
    clickRate: number;
    deliveryRate: number;
  } | null> {
    try {
      const response = await fetch('/api/notifications/stats', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('mingus_token')}`,
        }
      });

      if (!response.ok) {
        return null;
      }

      return await response.json();
    } catch (error) {
      console.error('Error fetching notification stats:', error);
      return null;
    }
  }

  /**
   * Utility function to convert VAPID key
   */
  private urlBase64ToUint8Array(base64String: string): Uint8Array {
    const padding = '='.repeat((4 - base64String.length % 4) % 4);
    const base64 = (base64String + padding)
      .replace(/-/g, '+')
      .replace(/_/g, '/');

    const rawData = window.atob(base64);
    const outputArray = new Uint8Array(rawData.length);

    for (let i = 0; i < rawData.length; ++i) {
      outputArray[i] = rawData.charCodeAt(i);
    }
    return outputArray;
  }
}

export default NotificationService;
