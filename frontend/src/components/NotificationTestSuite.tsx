import React, { useState, useEffect } from 'react';
import { 
  BellIcon, 
  CheckCircleIcon, 
  XCircleIcon, 
  ClockIcon,
  DevicePhoneMobileIcon,
  ExclamationTriangleIcon,
  PlayIcon,
  StopIcon,
  EyeIcon,
  ChartBarIcon
} from '@heroicons/react/24/outline';
import NotificationService, { NotificationPreferences } from '../services/notificationService';

interface NotificationTestSuiteProps {
  className?: string;
}

const NotificationTestSuite: React.FC<NotificationTestSuiteProps> = ({ className = '' }) => {
  const [testResults, setTestResults] = useState<Array<{
    test: string;
    status: 'pending' | 'running' | 'passed' | 'failed';
    message: string;
    timestamp: string;
  }>>([]);
  
  const [isRunning, setIsRunning] = useState(false);
  const [permissionStatus, setPermissionStatus] = useState<string>('unknown');
  const [subscriptionStatus, setSubscriptionStatus] = useState<string>('unknown');
  const [preferences, setPreferences] = useState<NotificationPreferences | null>(null);
  
  const notificationService = NotificationService.getInstance();

  useEffect(() => {
    initializeTests();
  }, []);

  const initializeTests = async () => {
    try {
      // Check if notifications are supported
      const supported = notificationService.isSupported();
      addTestResult('Browser Support', supported ? 'passed' : 'failed', 
        supported ? 'Notifications are supported' : 'Notifications not supported');
      
      // Check permission status
      const permission = await notificationService.requestPermission();
      setPermissionStatus(permission.status);
      addTestResult('Permission Status', permission.granted ? 'passed' : 'failed',
        `Permission status: ${permission.status}`);
      
      // Get preferences
      const prefs = await notificationService.getNotificationPreferences();
      setPreferences(prefs);
      addTestResult('Load Preferences', prefs ? 'passed' : 'failed',
        prefs ? 'Preferences loaded successfully' : 'Failed to load preferences');
      
    } catch (error) {
      addTestResult('Initialization', 'failed', `Error: ${error}`);
    }
  };

  const addTestResult = (test: string, status: 'pending' | 'running' | 'passed' | 'failed', message: string) => {
    setTestResults(prev => [...prev, {
      test,
      status,
      message,
      timestamp: new Date().toLocaleTimeString()
    }]);
  };

  const runAllTests = async () => {
    setIsRunning(true);
    setTestResults([]);
    
    try {
      // Test 1: Browser Support
      addTestResult('Browser Support', 'running', 'Checking browser support...');
      const supported = notificationService.isSupported();
      addTestResult('Browser Support', supported ? 'passed' : 'failed', 
        supported ? 'Notifications are supported' : 'Notifications not supported');
      
      // Test 2: Permission Request
      addTestResult('Permission Request', 'running', 'Requesting notification permission...');
      const permission = await notificationService.requestPermission();
      setPermissionStatus(permission.status);
      addTestResult('Permission Request', permission.granted ? 'passed' : 'failed',
        `Permission status: ${permission.status}`);
      
      // Test 3: Subscription
      if (permission.granted) {
        addTestResult('Push Subscription', 'running', 'Subscribing to push notifications...');
        const defaultPrefs: NotificationPreferences = {
          dailyOutlookEnabled: true,
          weekdayTime: '06:45',
          weekendTime: '08:30',
          timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
          soundEnabled: true,
          vibrationEnabled: true,
          richNotifications: true,
          actionButtons: true
        };
        
        const subscribed = await notificationService.subscribeToDailyOutlookNotifications(defaultPrefs);
        setSubscriptionStatus(subscribed ? 'subscribed' : 'failed');
        addTestResult('Push Subscription', subscribed ? 'passed' : 'failed',
          subscribed ? 'Successfully subscribed to push notifications' : 'Failed to subscribe');
      }
      
      // Test 4: Preferences Management
      addTestResult('Preferences Management', 'running', 'Testing preferences...');
      const testPrefs: Partial<NotificationPreferences> = {
        weekdayTime: '07:00',
        weekendTime: '09:00',
        soundEnabled: false
      };
      
      const prefsUpdated = await notificationService.updateNotificationPreferences(testPrefs);
      addTestResult('Preferences Management', prefsUpdated ? 'passed' : 'failed',
        prefsUpdated ? 'Preferences updated successfully' : 'Failed to update preferences');
      
      // Test 5: Test Notification
      addTestResult('Test Notification', 'running', 'Sending test notification...');
      const testSent = await notificationService.sendTestNotification();
      addTestResult('Test Notification', testSent ? 'passed' : 'failed',
        testSent ? 'Test notification sent successfully' : 'Failed to send test notification');
      
      // Test 6: Analytics
      addTestResult('Analytics', 'running', 'Testing analytics...');
      const stats = await notificationService.getNotificationStats();
      addTestResult('Analytics', stats ? 'passed' : 'failed',
        stats ? 'Analytics loaded successfully' : 'Failed to load analytics');
      
      // Test 7: History
      addTestResult('Notification History', 'running', 'Loading notification history...');
      const history = await notificationService.getNotificationHistory(10, 0);
      addTestResult('Notification History', 'passed',
        `Loaded ${history.length} notification records`);
      
    } catch (error) {
      addTestResult('Test Suite', 'failed', `Test suite error: ${error}`);
    } finally {
      setIsRunning(false);
    }
  };

  const runIndividualTest = async (testName: string) => {
    try {
      switch (testName) {
        case 'permission':
          addTestResult('Permission Test', 'running', 'Testing permission...');
          const permission = await notificationService.requestPermission();
          addTestResult('Permission Test', permission.granted ? 'passed' : 'failed',
            `Permission result: ${permission.status}`);
          break;
          
        case 'subscription':
          addTestResult('Subscription Test', 'running', 'Testing subscription...');
          const defaultPrefs: NotificationPreferences = {
            dailyOutlookEnabled: true,
            weekdayTime: '06:45',
            weekendTime: '08:30',
            timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
            soundEnabled: true,
            vibrationEnabled: true,
            richNotifications: true,
            actionButtons: true
          };
          const subscribed = await notificationService.subscribeToDailyOutlookNotifications(defaultPrefs);
          addTestResult('Subscription Test', subscribed ? 'passed' : 'failed',
            subscribed ? 'Subscription successful' : 'Subscription failed');
          break;
          
        case 'test-notification':
          addTestResult('Test Notification', 'running', 'Sending test notification...');
          const testSent = await notificationService.sendTestNotification();
          addTestResult('Test Notification', testSent ? 'passed' : 'failed',
            testSent ? 'Test notification sent' : 'Test notification failed');
          break;
          
        case 'preferences':
          addTestResult('Preferences Test', 'running', 'Testing preferences...');
          const testPrefs = await notificationService.getNotificationPreferences();
          addTestResult('Preferences Test', testPrefs ? 'passed' : 'failed',
            testPrefs ? 'Preferences loaded' : 'Preferences failed');
          break;
      }
    } catch (error) {
      addTestResult(testName, 'failed', `Error: ${error}`);
    }
  };

  const clearResults = () => {
    setTestResults([]);
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'passed':
        return <CheckCircleIcon className="h-5 w-5 text-green-500" />;
      case 'failed':
        return <XCircleIcon className="h-5 w-5 text-red-500" />;
      case 'running':
        return <div className="h-5 w-5 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />;
      default:
        return <ClockIcon className="h-5 w-5 text-gray-400" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'passed':
        return 'bg-green-50 border-green-200 text-green-800';
      case 'failed':
        return 'bg-red-50 border-red-200 text-red-800';
      case 'running':
        return 'bg-blue-50 border-blue-200 text-blue-800';
      default:
        return 'bg-gray-50 border-gray-200 text-gray-800';
    }
  };

  return (
    <div className={`bg-white rounded-lg shadow-sm border border-gray-200 p-6 ${className}`}>
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center space-x-3">
          <BellIcon className="h-6 w-6 text-blue-600" />
          <div>
            <h2 className="text-xl font-semibold text-gray-900">Notification Test Suite</h2>
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
            disabled={isRunning}
            className="px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isRunning ? (
              <>
                <div className="h-4 w-4 border-2 border-white border-t-transparent rounded-full animate-spin inline-block mr-2" />
                Running Tests...
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
        <div className="bg-gray-50 rounded-lg p-4">
          <div className="flex items-center space-x-2">
            <DevicePhoneMobileIcon className="h-5 w-5 text-gray-600" />
            <div>
              <p className="text-sm font-medium text-gray-900">Permission</p>
              <p className="text-sm text-gray-600 capitalize">{permissionStatus}</p>
            </div>
          </div>
        </div>
        <div className="bg-gray-50 rounded-lg p-4">
          <div className="flex items-center space-x-2">
            <BellIcon className="h-5 w-5 text-gray-600" />
            <div>
              <p className="text-sm font-medium text-gray-900">Subscription</p>
              <p className="text-sm text-gray-600 capitalize">{subscriptionStatus}</p>
            </div>
          </div>
        </div>
        <div className="bg-gray-50 rounded-lg p-4">
          <div className="flex items-center space-x-2">
            <ChartBarIcon className="h-5 w-5 text-gray-600" />
            <div>
              <p className="text-sm font-medium text-gray-900">Tests Run</p>
              <p className="text-sm text-gray-600">{testResults.length}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Individual Test Buttons */}
      <div className="mb-6">
        <h3 className="text-lg font-medium text-gray-900 mb-3">Individual Tests</h3>
        <div className="flex flex-wrap gap-2">
          <button
            onClick={() => runIndividualTest('permission')}
            className="px-3 py-2 bg-gray-100 text-gray-700 text-sm font-medium rounded-md hover:bg-gray-200 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2"
          >
            Test Permission
          </button>
          <button
            onClick={() => runIndividualTest('subscription')}
            className="px-3 py-2 bg-gray-100 text-gray-700 text-sm font-medium rounded-md hover:bg-gray-200 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2"
          >
            Test Subscription
          </button>
          <button
            onClick={() => runIndividualTest('test-notification')}
            className="px-3 py-2 bg-gray-100 text-gray-700 text-sm font-medium rounded-md hover:bg-gray-200 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2"
          >
            Send Test Notification
          </button>
          <button
            onClick={() => runIndividualTest('preferences')}
            className="px-3 py-2 bg-gray-100 text-gray-700 text-sm font-medium rounded-md hover:bg-gray-200 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2"
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
          <div className="space-y-3">
            {testResults.map((result, index) => (
              <div
                key={index}
                className={`p-4 rounded-lg border ${getStatusColor(result.status)}`}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    {getStatusIcon(result.status)}
                    <div>
                      <p className="font-medium">{result.test}</p>
                      <p className="text-sm opacity-75">{result.message}</p>
                    </div>
                  </div>
                  <span className="text-xs opacity-75">{result.timestamp}</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Debug Information */}
      <div className="mt-6 pt-6 border-t border-gray-200">
        <h3 className="text-lg font-medium text-gray-900 mb-3">Debug Information</h3>
        <div className="bg-gray-50 rounded-lg p-4">
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="font-medium">Browser Support:</span>
              <span className={notificationService.isSupported() ? 'text-green-600' : 'text-red-600'}>
                {notificationService.isSupported() ? 'Yes' : 'No'}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="font-medium">Service Worker:</span>
              <span className={navigator.serviceWorker ? 'text-green-600' : 'text-red-600'}>
                {navigator.serviceWorker ? 'Available' : 'Not Available'}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="font-medium">Push Manager:</span>
              <span className={navigator.serviceWorker && 'PushManager' in window ? 'text-green-600' : 'text-red-600'}>
                {navigator.serviceWorker && 'PushManager' in window ? 'Available' : 'Not Available'}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="font-medium">Current Time:</span>
              <span>{new Date().toLocaleString()}</span>
            </div>
            <div className="flex justify-between">
              <span className="font-medium">User Agent:</span>
              <span className="text-xs truncate max-w-xs">{navigator.userAgent}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default NotificationTestSuite;
