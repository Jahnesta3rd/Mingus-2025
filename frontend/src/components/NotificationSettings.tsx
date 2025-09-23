import React, { useState, useEffect } from 'react';
import { 
  BellIcon, 
  ClockIcon, 
  SpeakerWaveIcon, 
  DevicePhoneMobileIcon,
  EnvelopeIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
  SunIcon,
  MoonIcon
} from '@heroicons/react/24/outline';
import NotificationService, { NotificationPreferences } from '../services/notificationService';

interface NotificationSettingsProps {
  userId: string;
  className?: string;
}

const NotificationSettings: React.FC<NotificationSettingsProps> = ({
  userId,
  className = ''
}) => {
  const [preferences, setPreferences] = useState<NotificationPreferences>({
    dailyOutlookEnabled: true,
    weekdayTime: '06:45',
    weekendTime: '08:30',
    timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
    soundEnabled: true,
    vibrationEnabled: true,
    richNotifications: true,
    actionButtons: true
  });
  
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [permissionStatus, setPermissionStatus] = useState<'granted' | 'denied' | 'not-determined' | 'provisional'>('not-determined');
  const [testNotificationSent, setTestNotificationSent] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const notificationService = NotificationService.getInstance();

  useEffect(() => {
    loadPreferences();
    checkPermissionStatus();
  }, [userId]);

  const loadPreferences = async () => {
    try {
      setLoading(true);
      const prefs = await notificationService.getNotificationPreferences();
      if (prefs) {
        setPreferences(prefs);
      }
    } catch (err) {
      console.error('Error loading notification preferences:', err);
      setError('Failed to load notification preferences');
    } finally {
      setLoading(false);
    }
  };

  const checkPermissionStatus = async () => {
    try {
      const permission = await notificationService.requestPermission();
      setPermissionStatus(permission.status);
    } catch (err) {
      console.error('Error checking permission status:', err);
    }
  };

  const handlePreferenceChange = (key: keyof NotificationPreferences, value: any) => {
    setPreferences(prev => ({
      ...prev,
      [key]: value
    }));
  };

  const handleSavePreferences = async () => {
    try {
      setSaving(true);
      setError(null);
      
      const success = await notificationService.updateNotificationPreferences(preferences);
      if (success) {
        // Show success message
        setTestNotificationSent(true);
        setTimeout(() => setTestNotificationSent(false), 3000);
      } else {
        setError('Failed to save notification preferences');
      }
    } catch (err) {
      console.error('Error saving notification preferences:', err);
      setError('Failed to save notification preferences');
    } finally {
      setSaving(false);
    }
  };

  const handleRequestPermission = async () => {
    try {
      const permission = await notificationService.requestPermission();
      setPermissionStatus(permission.status);
      
      if (permission.granted) {
        // Subscribe to push notifications
        await notificationService.subscribeToDailyOutlookNotifications(preferences);
      }
    } catch (err) {
      console.error('Error requesting permission:', err);
      setError('Failed to request notification permission');
    }
  };

  const handleSendTestNotification = async () => {
    try {
      const success = await notificationService.sendTestNotification();
      if (success) {
        setTestNotificationSent(true);
        setTimeout(() => setTestNotificationSent(false), 3000);
      } else {
        setError('Failed to send test notification');
      }
    } catch (err) {
      console.error('Error sending test notification:', err);
      setError('Failed to send test notification');
    }
  };

  const handleUnsubscribe = async () => {
    try {
      await notificationService.unsubscribeFromNotifications();
      setPermissionStatus('denied');
    } catch (err) {
      console.error('Error unsubscribing from notifications:', err);
      setError('Failed to unsubscribe from notifications');
    }
  };

  if (loading) {
    return (
      <div className={`bg-white rounded-lg shadow-sm border border-gray-200 p-6 ${className}`}>
        <div className="animate-pulse">
          <div className="h-6 bg-gray-200 rounded w-1/3 mb-4"></div>
          <div className="space-y-3">
            <div className="h-4 bg-gray-200 rounded w-1/2"></div>
            <div className="h-4 bg-gray-200 rounded w-3/4"></div>
            <div className="h-4 bg-gray-200 rounded w-1/2"></div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className={`bg-white rounded-lg shadow-sm border border-gray-200 p-6 ${className}`}>
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center space-x-3">
          <BellIcon className="h-6 w-6 text-blue-600" />
          <h2 className="text-xl font-semibold text-gray-900">Notification Settings</h2>
        </div>
        {testNotificationSent && (
          <div className="flex items-center space-x-2 text-green-600">
            <CheckCircleIcon className="h-5 w-5" />
            <span className="text-sm font-medium">Test sent!</span>
          </div>
        )}
      </div>

      {error && (
        <div className="mb-6 bg-red-50 border border-red-200 rounded-md p-4">
          <div className="flex">
            <ExclamationTriangleIcon className="h-5 w-5 text-red-400" />
            <div className="ml-3">
              <p className="text-sm text-red-700">{error}</p>
            </div>
          </div>
        </div>
      )}

      {/* Permission Status */}
      <div className="mb-6">
        <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
          <div className="flex items-center space-x-3">
            <DevicePhoneMobileIcon className="h-5 w-5 text-gray-600" />
            <div>
              <p className="text-sm font-medium text-gray-900">Push Notifications</p>
              <p className="text-sm text-gray-600">
                {permissionStatus === 'granted' ? 'Enabled' : 
                 permissionStatus === 'denied' ? 'Disabled' : 
                 'Permission required'}
              </p>
            </div>
          </div>
          <div className="flex items-center space-x-2">
            {permissionStatus === 'granted' ? (
              <button
                onClick={handleUnsubscribe}
                className="text-sm text-red-600 hover:text-red-700 font-medium"
              >
                Disable
              </button>
            ) : (
              <button
                onClick={handleRequestPermission}
                className="text-sm text-blue-600 hover:text-blue-700 font-medium"
              >
                Enable
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Daily Outlook Notifications */}
      <div className="mb-6">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-3">
            <SunIcon className="h-5 w-5 text-yellow-500" />
            <div>
              <h3 className="text-lg font-medium text-gray-900">Daily Outlook</h3>
              <p className="text-sm text-gray-600">Get your personalized daily insights</p>
            </div>
          </div>
          <label className="relative inline-flex items-center cursor-pointer">
            <input
              type="checkbox"
              checked={preferences.dailyOutlookEnabled}
              onChange={(e) => handlePreferenceChange('dailyOutlookEnabled', e.target.checked)}
              className="sr-only peer"
            />
            <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
          </label>
        </div>

        {preferences.dailyOutlookEnabled && (
          <div className="ml-8 space-y-4">
            {/* Notification Times */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  <ClockIcon className="h-4 w-4 inline mr-2" />
                  Weekday Time
                </label>
                <input
                  type="time"
                  value={preferences.weekdayTime}
                  onChange={(e) => handlePreferenceChange('weekdayTime', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  <MoonIcon className="h-4 w-4 inline mr-2" />
                  Weekend Time
                </label>
                <input
                  type="time"
                  value={preferences.weekendTime}
                  onChange={(e) => handlePreferenceChange('weekendTime', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
            </div>

            {/* Timezone */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Timezone
              </label>
              <select
                value={preferences.timezone}
                onChange={(e) => handlePreferenceChange('timezone', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="America/New_York">Eastern Time (ET)</option>
                <option value="America/Chicago">Central Time (CT)</option>
                <option value="America/Denver">Mountain Time (MT)</option>
                <option value="America/Los_Angeles">Pacific Time (PT)</option>
                <option value="UTC">UTC</option>
              </select>
            </div>
          </div>
        )}
      </div>

      {/* Notification Preferences */}
      <div className="mb-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">Notification Preferences</h3>
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <SpeakerWaveIcon className="h-5 w-5 text-gray-600" />
              <div>
                <p className="text-sm font-medium text-gray-900">Sound</p>
                <p className="text-sm text-gray-600">Play notification sounds</p>
              </div>
            </div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={preferences.soundEnabled}
                onChange={(e) => handlePreferenceChange('soundEnabled', e.target.checked)}
                className="sr-only peer"
              />
              <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
            </label>
          </div>

          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <DevicePhoneMobileIcon className="h-5 w-5 text-gray-600" />
              <div>
                <p className="text-sm font-medium text-gray-900">Vibration</p>
                <p className="text-sm text-gray-600">Vibrate on notifications</p>
              </div>
            </div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={preferences.vibrationEnabled}
                onChange={(e) => handlePreferenceChange('vibrationEnabled', e.target.checked)}
                className="sr-only peer"
              />
              <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
            </label>
          </div>

          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <BellIcon className="h-5 w-5 text-gray-600" />
              <div>
                <p className="text-sm font-medium text-gray-900">Rich Notifications</p>
                <p className="text-sm text-gray-600">Show preview content and actions</p>
              </div>
            </div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={preferences.richNotifications}
                onChange={(e) => handlePreferenceChange('richNotifications', e.target.checked)}
                className="sr-only peer"
              />
              <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
            </label>
          </div>

          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <EnvelopeIcon className="h-5 w-5 text-gray-600" />
              <div>
                <p className="text-sm font-medium text-gray-900">Action Buttons</p>
                <p className="text-sm text-gray-600">Show quick action buttons</p>
              </div>
            </div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={preferences.actionButtons}
                onChange={(e) => handlePreferenceChange('actionButtons', e.target.checked)}
                className="sr-only peer"
              />
              <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
            </label>
          </div>
        </div>
      </div>

      {/* Test Notification */}
      <div className="mb-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">Test Notifications</h3>
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-blue-900">Send Test Notification</p>
              <p className="text-sm text-blue-700">Test your notification settings with a sample notification</p>
            </div>
            <button
              onClick={handleSendTestNotification}
              disabled={!preferences.dailyOutlookEnabled || permissionStatus !== 'granted'}
              className="px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Send Test
            </button>
          </div>
        </div>
      </div>

      {/* Save Button */}
      <div className="flex items-center justify-end space-x-3">
        <button
          onClick={loadPreferences}
          className="px-4 py-2 text-gray-700 bg-gray-100 hover:bg-gray-200 text-sm font-medium rounded-md focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2"
        >
          Reset
        </button>
        <button
          onClick={handleSavePreferences}
          disabled={saving}
          className="px-6 py-2 bg-blue-600 text-white text-sm font-medium rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {saving ? 'Saving...' : 'Save Preferences'}
        </button>
      </div>
    </div>
  );
};

export default NotificationSettings;
