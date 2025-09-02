import React, { useState, useEffect } from 'react';
import {
  SessionSettingsProps,
  SessionSettings as SessionSettingsType,
  NotificationPreferences
} from '@/types/sessionManagement';

const SessionSettings: React.FC<SessionSettingsProps> = ({
  settings,
  onUpdateSettings,
  onResetToDefaults,
  isLoading,
  hasChanges
}) => {
  const [localSettings, setLocalSettings] = useState<SessionSettingsType>(settings);
  const [activeTab, setActiveTab] = useState<'general' | 'security' | 'notifications' | 'advanced'>('general');
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [showResetConfirm, setShowResetConfirm] = useState(false);

  useEffect(() => {
    setLocalSettings(settings);
  }, [settings]);

  const handleSettingChange = (key: keyof SessionSettingsType, value: any) => {
    setLocalSettings(prev => ({
      ...prev,
      [key]: value
    }));
  };

  const handleNotificationChange = (key: keyof NotificationPreferences, value: boolean) => {
    setLocalSettings(prev => ({
      ...prev,
      notificationPreferences: {
        ...prev.notificationPreferences,
        [key]: value
      }
    }));
  };

  const handleSave = async () => {
    await onUpdateSettings(localSettings);
  };

  const handleReset = async () => {
    await onResetToDefaults();
    setShowResetConfirm(false);
  };

  const getSecurityScoreColor = (score: number) => {
    if (score >= 80) return 'text-green-600';
    if (score >= 60) return 'text-yellow-600';
    if (score >= 40) return 'text-orange-600';
    return 'text-red-600';
  };

  const getSecurityScoreLabel = (score: number) => {
    if (score >= 80) return 'Excellent';
    if (score >= 60) return 'Good';
    if (score >= 40) return 'Fair';
    return 'Poor';
  };

  const tabs = [
    { id: 'general', label: 'General', icon: 'settings' },
    { id: 'security', label: 'Security', icon: 'shield' },
    { id: 'notifications', label: 'Notifications', icon: 'bell' },
    { id: 'advanced', label: 'Advanced', icon: 'cog' }
  ];

  const getTabIcon = (icon: string) => {
    switch (icon) {
      case 'settings':
        return (
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
          </svg>
        );
      case 'shield':
        return (
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
          </svg>
        );
      case 'bell':
        return (
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-5 5v-5zM4.83 19.172A4 4 0 015 16h3a4 4 0 004-4V9a4 4 0 00-4-4H5a4 4 0 00-4 4v3a4 4 0 003.17 3.828z" />
          </svg>
        );
      case 'cog':
        return (
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
          </svg>
        );
      default:
        return null;
    }
  };

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="animate-pulse">
          <div className="h-8 bg-gray-200 rounded w-1/3 mb-4"></div>
          <div className="space-y-4">
            {[...Array(6)].map((_, i) => (
              <div key={i} className="h-4 bg-gray-200 rounded w-full"></div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Session Settings</h2>
          <p className="text-gray-600 mt-1">
            Configure your session preferences and security settings
          </p>
        </div>
        
        <div className="mt-4 sm:mt-0 flex items-center space-x-3">
          <button
            onClick={() => setShowResetConfirm(true)}
            className="px-4 py-2 text-gray-600 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
          >
            Reset to Defaults
          </button>
          
          <button
            onClick={handleSave}
            disabled={!hasChanges || isLoading}
            className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {isLoading ? 'Saving...' : 'Save Changes'}
          </button>
        </div>
      </div>

      {/* Security Score Overview */}
      <div className="bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200 rounded-lg p-6">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-semibold text-blue-900 mb-2">Security Score</h3>
            <p className="text-blue-700 text-sm">
              Your current security configuration score based on enabled features and settings
            </p>
          </div>
          
          <div className="text-center">
            <div className={`text-4xl font-bold ${getSecurityScoreColor(localSettings.securityScoreThreshold)}`}>
              {localSettings.securityScoreThreshold}
            </div>
            <div className="text-sm text-blue-600 font-medium">
              {getSecurityScoreLabel(localSettings.securityScoreThreshold)}
            </div>
          </div>
        </div>
      </div>

      {/* Tab Navigation */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`py-2 px-1 border-b-2 font-medium text-sm flex items-center space-x-2 ${
                activeTab === tab.id
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              {getTabIcon(tab.icon)}
              <span>{tab.label}</span>
            </button>
          ))}
        </nav>
      </div>

      {/* Tab Content */}
      <div className="space-y-6">
        {/* General Settings */}
        {activeTab === 'general' && (
          <div className="space-y-6">
            <div className="bg-white rounded-lg border border-gray-200 p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Session Management</h3>
              
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Maximum Concurrent Sessions
                  </label>
                  <div className="flex items-center space-x-4">
                    <input
                      type="range"
                      min="1"
                      max="10"
                      value={localSettings.maxConcurrentSessions}
                      onChange={(e) => handleSettingChange('maxConcurrentSessions', parseInt(e.target.value))}
                      className="flex-1 h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
                    />
                    <span className="text-sm font-medium text-gray-900 w-12 text-center">
                      {localSettings.maxConcurrentSessions}
                    </span>
                  </div>
                  <p className="text-sm text-gray-500 mt-1">
                    Limit the number of active sessions across all your devices
                  </p>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Session Timeout (minutes)
                  </label>
                  <div className="flex items-center space-x-4">
                    <input
                      type="range"
                      min="15"
                      max="480"
                      step="15"
                      value={localSettings.sessionTimeoutMinutes}
                      onChange={(e) => handleSettingChange('sessionTimeoutMinutes', parseInt(e.target.value))}
                      className="flex-1 h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
                    />
                    <span className="text-sm font-medium text-gray-900 w-16 text-center">
                      {localSettings.sessionTimeoutMinutes}m
                    </span>
                  </div>
                  <p className="text-sm text-gray-500 mt-1">
                    Automatically log out inactive sessions after this time
                  </p>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Idle Timeout (minutes)
                  </label>
                  <div className="flex items-center space-x-4">
                    <input
                      type="range"
                      min="5"
                      max="120"
                      step="5"
                      value={localSettings.idleTimeoutMinutes}
                      onChange={(e) => handleSettingChange('idleTimeoutMinutes', parseInt(e.target.value))}
                      className="flex-1 h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
                    />
                    <span className="text-sm font-medium text-gray-900 w-16 text-center">
                      {localSettings.idleTimeoutMinutes}m
                    </span>
                  </div>
                  <p className="text-sm text-gray-500 mt-1">
                    Log out sessions that have been idle for this duration
                  </p>
                </div>

                <div className="flex items-center justify-between">
                  <div>
                    <label className="text-sm font-medium text-gray-700">
                      Require Re-authentication for Sensitive Actions
                    </label>
                    <p className="text-sm text-gray-500 mt-1">
                      Prompt for password or 2FA when accessing financial data or making changes
                    </p>
                  </div>
                  <input
                    type="checkbox"
                    checked={localSettings.requireReauthForSensitiveActions}
                    onChange={(e) => handleSettingChange('requireReauthForSensitiveActions', e.target.checked)}
                    className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                  />
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Security Settings */}
        {activeTab === 'security' && (
          <div className="space-y-6">
            <div className="bg-white rounded-lg border border-gray-200 p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Security Features</h3>
              
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <label className="text-sm font-medium text-gray-700">
                      Location Tracking
                    </label>
                    <p className="text-sm text-gray-500 mt-1">
                      Monitor and alert on unusual login locations
                    </p>
                  </div>
                  <input
                    type="checkbox"
                    checked={localSettings.enableLocationTracking}
                    onChange={(e) => handleSettingChange('enableLocationTracking', e.target.checked)}
                    className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                  />
                </div>

                <div className="flex items-center justify-between">
                  <div>
                    <label className="text-sm font-medium text-gray-700">
                      Device Fingerprinting
                    </label>
                    <p className="text-sm text-gray-500 mt-1">
                      Create unique device profiles for enhanced security
                    </p>
                  </div>
                  <input
                    type="checkbox"
                    checked={localSettings.enableDeviceFingerprinting}
                    onChange={(e) => handleSettingChange('enableDeviceFingerprinting', e.target.checked)}
                    className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                  />
                </div>

                <div className="flex items-center justify-between">
                  <div>
                    <label className="text-sm font-medium text-gray-700">
                      Behavioral Analysis
                    </label>
                    <p className="text-sm text-gray-500 mt-1">
                      Detect unusual patterns in your account usage
                    </p>
                  </div>
                  <input
                    type="checkbox"
                    checked={localSettings.enableBehavioralAnalysis}
                    onChange={(e) => handleSettingChange('enableBehavioralAnalysis', e.target.checked)}
                    className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                  />
                </div>

                <div className="flex items-center justify-between">
                  <div>
                    <label className="text-sm font-medium text-gray-700">
                      VPN Detection
                    </label>
                    <p className="text-sm text-gray-500 mt-1">
                      Alert when sessions use VPN or proxy services
                    </p>
                  </div>
                  <input
                    type="checkbox"
                    checked={localSettings.enableVpnDetection}
                    onChange={(e) => handleSettingChange('enableVpnDetection', e.target.checked)}
                    className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                  />
                </div>

                <div className="flex items-center justify-between">
                  <div>
                    <label className="text-sm font-medium text-gray-700">
                      Tor Network Detection
                    </label>
                    <p className="text-sm text-gray-500 mt-1">
                      Identify sessions using the Tor anonymity network
                    </p>
                  </div>
                  <input
                    type="checkbox"
                    checked={localSettings.enableTorDetection}
                    onChange={(e) => handleSettingChange('enableTorDetection', e.target.checked)}
                    className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                  />
                </div>

                <div className="flex items-center justify-between">
                  <div>
                    <label className="text-sm font-medium text-gray-700">
                      Auto-terminate Suspicious Sessions
                    </label>
                    <p className="text-sm text-gray-500 mt-1">
                      Automatically end sessions with high risk scores
                    </p>
                  </div>
                  <input
                    type="checkbox"
                    checked={localSettings.autoTerminateSuspiciousSessions}
                    onChange={(e) => handleSettingChange('autoTerminateSuspiciousSessions', e.target.checked)}
                    className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                  />
                </div>
              </div>
            </div>

            <div className="bg-white rounded-lg border border-gray-200 p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Session History</h3>
              
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <label className="text-sm font-medium text-gray-700">
                      Enable Session History
                    </label>
                    <p className="text-sm text-gray-500 mt-1">
                      Keep detailed logs of all session activities
                    </p>
                  </div>
                  <input
                    type="checkbox"
                    checked={localSettings.enableSessionHistory}
                    onChange={(e) => handleSettingChange('enableSessionHistory', e.target.checked)}
                    className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                  />
                </div>

                {localSettings.enableSessionHistory && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      History Retention (days)
                    </label>
                    <div className="flex items-center space-x-4">
                      <input
                        type="range"
                        min="7"
                        max="365"
                        step="7"
                        value={localSettings.maxSessionHistoryDays}
                        onChange={(e) => handleSettingChange('maxSessionHistoryDays', parseInt(e.target.value))}
                        className="flex-1 h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
                      />
                      <span className="text-sm font-medium text-gray-900 w-16 text-center">
                        {localSettings.maxSessionHistoryDays}d
                      </span>
                    </div>
                    <p className="text-sm text-gray-500 mt-1">
                      How long to keep session history records
                    </p>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Notification Settings */}
        {activeTab === 'notifications' && (
          <div className="space-y-6">
            <div className="bg-white rounded-lg border border-gray-200 p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Notification Channels</h3>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="flex items-center justify-between">
                  <div>
                    <label className="text-sm font-medium text-gray-700">Email</label>
                    <p className="text-sm text-gray-500">Receive alerts via email</p>
                  </div>
                  <input
                    type="checkbox"
                    checked={localSettings.notificationPreferences.email}
                    onChange={(e) => handleNotificationChange('email', e.target.checked)}
                    className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                  />
                </div>

                <div className="flex items-center justify-between">
                  <div>
                    <label className="text-sm font-medium text-gray-700">Push Notifications</label>
                    <p className="text-sm text-gray-500">In-app push notifications</p>
                  </div>
                  <input
                    type="checkbox"
                    checked={localSettings.notificationPreferences.push}
                    onChange={(e) => handleNotificationChange('push', e.target.checked)}
                    className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                  />
                </div>

                <div className="flex items-center justify-between">
                  <div>
                    <label className="text-sm font-medium text-gray-700">SMS</label>
                    <p className="text-sm text-gray-500">Text message alerts</p>
                  </div>
                  <input
                    type="checkbox"
                    checked={localSettings.notificationPreferences.sms}
                    onChange={(e) => handleNotificationChange('sms', e.target.checked)}
                    className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                  />
                </div>

                <div className="flex items-center justify-between">
                  <div>
                    <label className="text-sm font-medium text-gray-700">In-App</label>
                    <p className="text-sm text-gray-500">Display alerts within the app</p>
                  </div>
                  <input
                    type="checkbox"
                    checked={localSettings.notificationPreferences.inApp}
                    onChange={(e) => handleNotificationChange('inApp', e.target.checked)}
                    className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                  />
                </div>
              </div>
            </div>

            <div className="bg-white rounded-lg border border-gray-200 p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Alert Types</h3>
              
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <label className="text-sm font-medium text-gray-700">Suspicious Activity</label>
                    <p className="text-sm text-gray-500">Unusual login patterns or behavior</p>
                  </div>
                  <input
                    type="checkbox"
                    checked={localSettings.notificationPreferences.suspiciousActivity}
                    onChange={(e) => handleNotificationChange('suspiciousActivity', e.target.checked)}
                    className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                  />
                </div>

                <div className="flex items-center justify-between">
                  <div>
                    <label className="text-sm font-medium text-gray-700">New Device Login</label>
                    <p className="text-sm text-gray-500">First-time access from unknown devices</p>
                  </div>
                  <input
                    type="checkbox"
                    checked={localSettings.notificationPreferences.newDeviceLogin}
                    onChange={(e) => handleNotificationChange('newDeviceLogin', e.target.checked)}
                    className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                  />
                </div>

                <div className="flex items-center justify-between">
                  <div>
                    <label className="text-sm font-medium text-gray-700">Location Changes</label>
                    <p className="text-sm text-gray-500">Login from new geographic locations</p>
                  </div>
                  <input
                    type="checkbox"
                    checked={localSettings.notificationPreferences.locationChange}
                    onChange={(e) => handleNotificationChange('locationChange', e.target.checked)}
                    className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                  />
                </div>

                <div className="flex items-center justify-between">
                  <div>
                    <label className="text-sm font-medium text-gray-700">Session Timeout</label>
                    <p className="text-sm text-gray-500">When sessions expire or are terminated</p>
                  </div>
                  <input
                    type="checkbox"
                    checked={localSettings.notificationPreferences.sessionTimeout}
                    onChange={(e) => handleNotificationChange('sessionTimeout', e.target.checked)}
                    className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                  />
                </div>

                <div className="flex items-center justify-between">
                  <div>
                    <label className="text-sm font-medium text-gray-700">Security Score Changes</label>
                    <p className="text-sm text-gray-500">Significant changes in account security</p>
                  </div>
                  <input
                    type="checkbox"
                    checked={localSettings.notificationPreferences.securityScoreChange}
                    onChange={(e) => handleNotificationChange('securityScoreChange', e.target.checked)}
                    className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                  />
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Advanced Settings */}
        {activeTab === 'advanced' && (
          <div className="space-y-6">
            <div className="bg-white rounded-lg border border-gray-200 p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Advanced Configuration</h3>
              
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Security Score Threshold
                  </label>
                  <div className="flex items-center space-x-4">
                    <input
                      type="range"
                      min="0"
                      max="100"
                      step="5"
                      value={localSettings.securityScoreThreshold}
                      onChange={(e) => handleSettingChange('securityScoreThreshold', parseInt(e.target.value))}
                      className="flex-1 h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
                    />
                    <span className="text-sm font-medium text-gray-900 w-16 text-center">
                      {localSettings.securityScoreThreshold}
                    </span>
                  </div>
                  <p className="text-sm text-gray-500 mt-1">
                    Minimum security score required for normal account access
                  </p>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Trusted Device Expiry (days)
                  </label>
                  <div className="flex items-center space-x-4">
                    <input
                      type="range"
                      min="30"
                      max="365"
                      step="30"
                      value={localSettings.trustedDeviceExpiryDays}
                      onChange={(e) => handleSettingChange('trustedDeviceExpiryDays', parseInt(e.target.value))}
                      className="flex-1 h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
                    />
                    <span className="text-sm font-medium text-gray-900 w-16 text-center">
                      {localSettings.trustedDeviceExpiryDays}d
                    </span>
                  </div>
                  <p className="text-sm text-gray-500 mt-1">
                    How long devices remain trusted before requiring re-verification
                  </p>
                </div>

                <div className="flex items-center justify-between">
                  <div>
                    <label className="text-sm font-medium text-gray-700">
                      Enable Suspicious Activity Alerts
                    </label>
                    <p className="text-sm text-gray-500 mt-1">
                      Receive notifications for potential security threats
                    </p>
                  </div>
                  <input
                    type="checkbox"
                    checked={localSettings.enableSuspiciousActivityAlerts}
                    onChange={(e) => handleSettingChange('enableSuspiciousActivityAlerts', e.target.checked)}
                    className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                  />
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Reset Confirmation Modal */}
      {showResetConfirm && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
            <div className="mt-3 text-center">
              <div className="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-yellow-100">
                <svg className="h-6 w-6 text-yellow-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-7.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.34 16.5c-.77.833.192 2.5 1.732 2.5z" />
                </svg>
              </div>
              <h3 className="text-lg font-medium text-gray-900 mt-4">Reset Settings?</h3>
              <p className="text-sm text-gray-500 mt-2">
                This will restore all session settings to their default values. This action cannot be undone.
              </p>
              <div className="flex items-center justify-center space-x-3 mt-4">
                <button
                  onClick={() => setShowResetConfirm(false)}
                  className="px-4 py-2 text-gray-600 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
                >
                  Cancel
                </button>
                <button
                  onClick={handleReset}
                  className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
                >
                  Reset
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default SessionSettings;
