import React, { useState, useEffect } from 'react';
import { 
  BellIcon, 
  CheckCircleIcon, 
  XCircleIcon, 
  PlayIcon,
  StopIcon,
  ExclamationTriangleIcon,
  SunIcon,
  MoonIcon,
  ClockIcon
} from '@heroicons/react/24/outline';
import NotificationService, { NotificationPreferences } from '../services/notificationService';

interface NotificationDemoProps {
  className?: string;
}

const NotificationDemo: React.FC<NotificationDemoProps> = ({ className = '' }) => {
  const [isSupported, setIsSupported] = useState(false);
  const [permissionStatus, setPermissionStatus] = useState<string>('unknown');
  const [isSubscribed, setIsSubscribed] = useState(false);
  const [testResults, setTestResults] = useState<string[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  
  const notificationService = NotificationService.getInstance();

  useEffect(() => {
    initializeDemo();
  }, []);

  const initializeDemo = async () => {
    try {
      // Check browser support
      const supported = notificationService.isSupported();
      setIsSupported(supported);
      addResult(`Browser Support: ${supported ? '✅ Supported' : '❌ Not Supported'}`);
      
      if (supported) {
        // Check permission status
        const permission = await notificationService.requestPermission();
        setPermissionStatus(permission.status);
        addResult(`Permission Status: ${permission.granted ? '✅ Granted' : '❌ Denied'} (${permission.status})`);
      }
    } catch (error) {
      addResult(`❌ Initialization Error: ${error}`);
    }
  };

  const addResult = (message: string) => {
    setTestResults(prev => [...prev, `${new Date().toLocaleTimeString()}: ${message}`]);
  };

  const testPermission = async () => {
    setIsLoading(true);
    try {
      addResult('🔄 Requesting notification permission...');
      const permission = await notificationService.requestPermission();
      setPermissionStatus(permission.status);
      
      if (permission.granted) {
        addResult('✅ Permission granted successfully!');
      } else {
        addResult(`❌ Permission denied: ${permission.status}`);
      }
    } catch (error) {
      addResult(`❌ Permission error: ${error}`);
    } finally {
      setIsLoading(false);
    }
  };

  const testSubscription = async () => {
    setIsLoading(true);
    try {
      addResult('🔄 Subscribing to push notifications...');
      
      const preferences: NotificationPreferences = {
        dailyOutlookEnabled: true,
        weekdayTime: '06:45',
        weekendTime: '08:30',
        timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
        soundEnabled: true,
        vibrationEnabled: true,
        richNotifications: true,
        actionButtons: true
      };
      
      const success = await notificationService.subscribeToDailyOutlookNotifications(preferences);
      
      if (success) {
        setIsSubscribed(true);
        addResult('✅ Successfully subscribed to push notifications!');
      } else {
        addResult('❌ Failed to subscribe to push notifications');
      }
    } catch (error) {
      addResult(`❌ Subscription error: ${error}`);
    } finally {
      setIsLoading(false);
    }
  };

  const sendTestNotification = async () => {
    setIsLoading(true);
    try {
      addResult('🔄 Sending test notification...');
      const success = await notificationService.sendTestNotification();
      
      if (success) {
        addResult('✅ Test notification sent successfully!');
        addResult('📱 Check your browser for the notification');
      } else {
        addResult('❌ Failed to send test notification');
      }
    } catch (error) {
      addResult(`❌ Test notification error: ${error}`);
    } finally {
      setIsLoading(false);
    }
  };

  const testPreferences = async () => {
    setIsLoading(true);
    try {
      addResult('🔄 Testing notification preferences...');
      
      // Test updating preferences
      const testPrefs: Partial<NotificationPreferences> = {
        weekdayTime: '07:00',
        weekendTime: '09:00',
        soundEnabled: false
      };
      
      const success = await notificationService.updateNotificationPreferences(testPrefs);
      
      if (success) {
        addResult('✅ Preferences updated successfully!');
      } else {
        addResult('❌ Failed to update preferences');
      }
      
      // Test getting preferences
      const prefs = await notificationService.getNotificationPreferences();
      if (prefs) {
        addResult(`✅ Preferences loaded: ${JSON.stringify(prefs, null, 2)}`);
      } else {
        addResult('❌ Failed to load preferences');
      }
    } catch (error) {
      addResult(`❌ Preferences error: ${error}`);
    } finally {
      setIsLoading(false);
    }
  };

  const clearResults = () => {
    setTestResults([]);
  };

  const runAllTests = async () => {
    setIsLoading(true);
    clearResults();
    
    try {
      addResult('🚀 Starting comprehensive notification tests...');
      
      // Test 1: Permission
      await testPermission();
      
      // Test 2: Subscription (if permission granted)
      if (permissionStatus === 'granted') {
        await testSubscription();
      }
      
      // Test 3: Test notification
      await sendTestNotification();
      
      // Test 4: Preferences
      await testPreferences();
      
      addResult('🎉 All tests completed!');
    } catch (error) {
      addResult(`❌ Test suite error: ${error}`);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className={`bg-white rounded-lg shadow-sm border border-gray-200 p-6 ${className}`}>
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center space-x-3">
          <BellIcon className="h-6 w-6 text-blue-600" />
          <div>
            <h2 className="text-xl font-semibold text-gray-900">Notification Demo</h2>
            <p className="text-sm text-gray-600">Test the Daily Outlook notification system</p>
          </div>
        </div>
        <div className="flex items-center space-x-2">
          <button
            onClick={clearResults}
            className="px-3 py-1 text-sm text-gray-600 hover:text-gray-800 border border-gray-300 rounded-md"
          >
            Clear Results
          </button>
          <button
            onClick={runAllTests}
            disabled={isLoading}
            className="px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isLoading ? (
              <>
                <div className="h-4 w-4 border-2 border-white border-t-transparent rounded-full animate-spin inline-block mr-2" />
                Testing...
              </>
            ) : (
              <>
                <PlayIcon className="h-4 w-4 inline mr-2" />
                Run All Tests
              </>
            )}
          </button>
        </div>
      </div>

      {/* Status Overview */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <div className={`p-4 rounded-lg ${isSupported ? 'bg-green-50 border-green-200' : 'bg-red-50 border-red-200'} border`}>
          <div className="flex items-center space-x-2">
            <BellIcon className={`h-5 w-5 ${isSupported ? 'text-green-600' : 'text-red-600'}`} />
            <div>
              <p className="text-sm font-medium text-gray-900">Browser Support</p>
              <p className={`text-sm ${isSupported ? 'text-green-600' : 'text-red-600'}`}>
                {isSupported ? 'Supported' : 'Not Supported'}
              </p>
            </div>
          </div>
        </div>
        
        <div className={`p-4 rounded-lg ${
          permissionStatus === 'granted' ? 'bg-green-50 border-green-200' : 
          permissionStatus === 'denied' ? 'bg-red-50 border-red-200' : 
          'bg-yellow-50 border-yellow-200'
        } border`}>
          <div className="flex items-center space-x-2">
            <CheckCircleIcon className={`h-5 w-5 ${
              permissionStatus === 'granted' ? 'text-green-600' : 
              permissionStatus === 'denied' ? 'text-red-600' : 
              'text-yellow-600'
            }`} />
            <div>
              <p className="text-sm font-medium text-gray-900">Permission</p>
              <p className={`text-sm ${
                permissionStatus === 'granted' ? 'text-green-600' : 
                permissionStatus === 'denied' ? 'text-red-600' : 
                'text-yellow-600'
              }`}>
                {permissionStatus === 'granted' ? 'Granted' : 
                 permissionStatus === 'denied' ? 'Denied' : 
                 'Unknown'}
              </p>
            </div>
          </div>
        </div>
        
        <div className={`p-4 rounded-lg ${isSubscribed ? 'bg-green-50 border-green-200' : 'bg-gray-50 border-gray-200'} border`}>
          <div className="flex items-center space-x-2">
            <BellIcon className={`h-5 w-5 ${isSubscribed ? 'text-green-600' : 'text-gray-600'}`} />
            <div>
              <p className="text-sm font-medium text-gray-900">Subscription</p>
              <p className={`text-sm ${isSubscribed ? 'text-green-600' : 'text-gray-600'}`}>
                {isSubscribed ? 'Subscribed' : 'Not Subscribed'}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Individual Test Buttons */}
      <div className="mb-6">
        <h3 className="text-lg font-medium text-gray-900 mb-3">Individual Tests</h3>
        <div className="flex flex-wrap gap-2">
          <button
            onClick={testPermission}
            disabled={isLoading}
            className="px-3 py-2 bg-blue-100 text-blue-700 text-sm font-medium rounded-md hover:bg-blue-200 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50"
          >
            Test Permission
          </button>
          <button
            onClick={testSubscription}
            disabled={isLoading || permissionStatus !== 'granted'}
            className="px-3 py-2 bg-green-100 text-green-700 text-sm font-medium rounded-md hover:bg-green-200 focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-2 disabled:opacity-50"
          >
            Test Subscription
          </button>
          <button
            onClick={sendTestNotification}
            disabled={isLoading}
            className="px-3 py-2 bg-purple-100 text-purple-700 text-sm font-medium rounded-md hover:bg-purple-200 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:ring-offset-2 disabled:opacity-50"
          >
            Send Test Notification
          </button>
          <button
            onClick={testPreferences}
            disabled={isLoading}
            className="px-3 py-2 bg-orange-100 text-orange-700 text-sm font-medium rounded-md hover:bg-orange-200 focus:outline-none focus:ring-2 focus:ring-orange-500 focus:ring-offset-2 disabled:opacity-50"
          >
            Test Preferences
          </button>
        </div>
      </div>

      {/* Test Results */}
      <div>
        <h3 className="text-lg font-medium text-gray-900 mb-3">Test Results</h3>
        {testResults.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            <BellIcon className="h-12 w-12 mx-auto mb-4 text-gray-300" />
            <p>No tests run yet. Click "Run All Tests" to start testing.</p>
          </div>
        ) : (
          <div className="bg-gray-50 rounded-lg p-4 max-h-96 overflow-y-auto">
            <div className="space-y-2">
              {testResults.map((result, index) => (
                <div key={index} className="text-sm font-mono text-gray-700">
                  {result}
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Debug Information */}
      <div className="mt-6 pt-6 border-t border-gray-200">
        <h3 className="text-lg font-medium text-gray-900 mb-3">Debug Information</h3>
        <div className="bg-gray-50 rounded-lg p-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
            <div>
              <p className="font-medium text-gray-700">Browser Information:</p>
              <ul className="mt-1 space-y-1 text-gray-600">
                <li>User Agent: {navigator.userAgent.substring(0, 50)}...</li>
                <li>Platform: {navigator.platform}</li>
                <li>Language: {navigator.language}</li>
                <li>Online: {navigator.onLine ? 'Yes' : 'No'}</li>
              </ul>
            </div>
            <div>
              <p className="font-medium text-gray-700">Notification Support:</p>
              <ul className="mt-1 space-y-1 text-gray-600">
                <li>Notifications API: {'Notification' in window ? '✅' : '❌'}</li>
                <li>Service Worker: {'serviceWorker' in navigator ? '✅' : '❌'}</li>
                <li>Push Manager: {'PushManager' in window ? '✅' : '❌'}</li>
                <li>Current Time: {new Date().toLocaleString()}</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default NotificationDemo;
