import React, { useState } from 'react';
import {
  ActiveSessions,
  SessionAlert,
  SessionSettings,
  DeviceManagement,
  SecurityDashboard,
  Session,
  Device,
  SessionAlert as SessionAlertType,
  SessionSettings as SessionSettingsType,
  SecurityDashboard as SecurityDashboardType,
  SessionStats
} from './index';

const Demo: React.FC = () => {
  const [activeComponent, setActiveComponent] = useState<'sessions' | 'alerts' | 'settings' | 'devices' | 'dashboard'>('dashboard');
  const [selectedSessions, setSelectedSessions] = useState<string[]>([]);
  const [selectedDevices, setSelectedDevices] = useState<string[]>([]);
  const [showAddDeviceModal, setShowAddDeviceModal] = useState(false);

  // Sample data for demonstration
  const sampleSessions: Session[] = [
    {
      id: '1',
      userId: 'user123',
      deviceId: 'device1',
      deviceName: 'iPhone 13 Pro',
      deviceType: 'mobile',
      deviceModel: 'iPhone 13 Pro',
      browser: 'Safari',
      browserVersion: '15.0',
      operatingSystem: 'iOS',
      osVersion: '15.0',
      ipAddress: '192.168.1.100',
      location: {
        country: 'United States',
        region: 'California',
        city: 'San Francisco',
        latitude: 37.7749,
        longitude: -122.4194,
        timezone: 'America/Los_Angeles',
        isp: 'Comcast',
        isVpn: false,
        isProxy: false,
        isTor: false,
        riskScore: 15
      },
      userAgent: 'Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X)',
      isActive: true,
      isTrusted: true,
      isCurrentSession: true,
      lastActivity: new Date().toISOString(),
      createdAt: new Date(Date.now() - 3600000).toISOString(),
      expiresAt: new Date(Date.now() + 7200000).toISOString(),
      sessionDuration: 60,
      activityCount: 25,
      lastActivityType: 'action',
      securityScore: 85,
      riskLevel: 'low',
      flags: [],
      metadata: {}
    },
    {
      id: '2',
      userId: 'user123',
      deviceId: 'device2',
      deviceName: 'MacBook Pro',
      deviceType: 'desktop',
      deviceModel: 'MacBook Pro 16"',
      browser: 'Chrome',
      browserVersion: '96.0.4664.110',
      operatingSystem: 'macOS',
      osVersion: '12.0.1',
      ipAddress: '192.168.1.101',
      location: {
        country: 'United States',
        region: 'California',
        city: 'San Francisco',
        latitude: 37.7749,
        longitude: -122.4194,
        timezone: 'America/Los_Angeles',
        isp: 'Comcast',
        isVpn: false,
        isProxy: false,
        isTor: false,
        riskScore: 20
      },
      userAgent: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 12_0_1)',
      isActive: true,
      isTrusted: true,
      isCurrentSession: false,
      lastActivity: new Date(Date.now() - 1800000).toISOString(),
      createdAt: new Date(Date.now() - 7200000).toISOString(),
      expiresAt: new Date(Date.now() + 10800000).toISOString(),
      sessionDuration: 120,
      activityCount: 45,
      lastActivityType: 'action',
      securityScore: 90,
      riskLevel: 'low',
      flags: [],
      metadata: {}
    },
    {
      id: '3',
      userId: 'user123',
      deviceId: 'device3',
      deviceName: 'Unknown Device',
      deviceType: 'other',
      browser: 'Firefox',
      browserVersion: '95.0',
      operatingSystem: 'Windows',
      osVersion: '10',
      ipAddress: '203.0.113.45',
      location: {
        country: 'Germany',
        region: 'Berlin',
        city: 'Berlin',
        latitude: 52.5200,
        longitude: 13.4050,
        timezone: 'Europe/Berlin',
        isp: 'Deutsche Telekom',
        isVpn: true,
        isProxy: true,
        isTor: false,
        riskScore: 75
      },
      userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:95.0)',
      isActive: true,
      isTrusted: false,
      isCurrentSession: false,
      lastActivity: new Date(Date.now() - 300000).toISOString(),
      createdAt: new Date(Date.now() - 600000).toISOString(),
      expiresAt: new Date(Date.now() + 3600000).toISOString(),
      sessionDuration: 10,
      activityCount: 3,
      lastActivityType: 'login',
      securityScore: 45,
      riskLevel: 'high',
      flags: [
        {
          type: 'vpn_detected',
          severity: 'medium',
          description: 'VPN connection detected',
          timestamp: new Date().toISOString(),
          isResolved: false
        },
        {
          type: 'unusual_location',
          severity: 'high',
          description: 'Login from unusual location',
          timestamp: new Date().toISOString(),
          isResolved: false
        }
      ],
      metadata: {}
    }
  ];

  const sampleDevices: Device[] = [
    {
      id: 'device1',
      userId: 'user123',
      name: 'iPhone 13 Pro',
      type: 'mobile',
      model: 'iPhone 13 Pro',
      manufacturer: 'Apple',
      operatingSystem: 'iOS',
      osVersion: '15.0',
      browser: 'Safari',
      browserVersion: '15.0',
      fingerprint: 'abc123def456',
      isTrusted: true,
      isActive: true,
      trustLevel: 'verified',
      trustScore: 95,
      lastUsed: new Date().toISOString(),
      createdAt: new Date(Date.now() - 2592000000).toISOString(),
      lastIpAddress: '192.168.1.100',
      lastLocation: {
        country: 'United States',
        region: 'California',
        city: 'San Francisco',
        latitude: 37.7749,
        longitude: -122.4194,
        timezone: 'America/Los_Angeles',
        isp: 'Comcast',
        isVpn: false,
        isProxy: false,
        isTor: false,
        riskScore: 15
      },
      usageCount: 150,
      securityEvents: [],
      metadata: {}
    },
    {
      id: 'device2',
      userId: 'user123',
      name: 'MacBook Pro',
      type: 'desktop',
      model: 'MacBook Pro 16"',
      manufacturer: 'Apple',
      operatingSystem: 'macOS',
      osVersion: '12.0.1',
      browser: 'Chrome',
      browserVersion: '96.0.4664.110',
      fingerprint: 'def456ghi789',
      isTrusted: true,
      isActive: true,
      trustLevel: 'trusted',
      trustScore: 90,
      lastUsed: new Date(Date.now() - 1800000).toISOString(),
      createdAt: new Date(Date.now() - 7776000000).toISOString(),
      lastIpAddress: '192.168.1.101',
      lastLocation: {
        country: 'United States',
        region: 'California',
        city: 'San Francisco',
        latitude: 37.7749,
        longitude: -122.4194,
        timezone: 'America/Los_Angeles',
        isp: 'Comcast',
        isVpn: false,
        isProxy: false,
        isTor: false,
        riskScore: 20
      },
      usageCount: 300,
      securityEvents: [],
      metadata: {}
    }
  ];

  const sampleAlerts: SessionAlertType[] = [
    {
      id: 'alert1',
      type: 'suspicious_activity',
      severity: 'high',
      title: 'Unusual Login Location',
      message: 'Login detected from Germany',
      description: 'Your account was accessed from Berlin, Germany, which is unusual for your typical login pattern.',
      timestamp: new Date(Date.now() - 300000).toISOString(),
      isRead: false,
      isResolved: false,
      requiresAction: true,
      actionRequired: 'verify_device',
      affectedSessions: ['3'],
      affectedDevices: ['device3'],
      location: {
        country: 'Germany',
        region: 'Berlin',
        city: 'Berlin',
        latitude: 52.5200,
        longitude: 13.4050,
        timezone: 'Europe/Berlin',
        isp: 'Deutsche Telekom',
        isVpn: true,
        isProxy: true,
        isTor: false,
        riskScore: 75
      },
      ipAddress: '203.0.113.45',
      deviceId: 'device3',
      sessionId: '3',
      metadata: {}
    },
    {
      id: 'alert2',
      type: 'new_device',
      severity: 'medium',
      title: 'New Device Detected',
      message: 'Unknown device accessed your account',
      description: 'A new device (Windows/Firefox) has been used to access your account.',
      timestamp: new Date(Date.now() - 600000).toISOString(),
      isRead: true,
      isResolved: false,
      requiresAction: true,
      actionRequired: 'review_activity',
      affectedSessions: ['3'],
      affectedDevices: ['device3'],
      deviceId: 'device3',
      sessionId: '3',
      metadata: {}
    }
  ];

  const sampleSettings: SessionSettingsType = {
    maxConcurrentSessions: 5,
    sessionTimeoutMinutes: 120,
    idleTimeoutMinutes: 30,
    requireReauthForSensitiveActions: true,
    enableLocationTracking: true,
    enableDeviceFingerprinting: true,
    enableBehavioralAnalysis: true,
    enableVpnDetection: true,
    enableTorDetection: true,
    enableSuspiciousActivityAlerts: true,
    enableSessionHistory: true,
    maxSessionHistoryDays: 90,
    trustedDeviceExpiryDays: 365,
    securityScoreThreshold: 70,
    autoTerminateSuspiciousSessions: true,
    notificationPreferences: {
      email: true,
      push: true,
      sms: false,
      inApp: true,
      suspiciousActivity: true,
      newDeviceLogin: true,
      locationChange: true,
      sessionTimeout: true,
      securityScoreChange: true
    }
  };

  const sampleDashboard: SecurityDashboardType = {
    overallSecurityScore: 82,
    riskLevel: 'medium',
    activeSessions: 3,
    trustedDevices: 2,
    suspiciousActivities: 1,
    securityEvents: [],
    recentAlerts: sampleAlerts,
    locationAnomalies: 1,
    deviceAnomalies: 1,
    lastSecurityReview: new Date(Date.now() - 604800000).toISOString(),
    nextSecurityReview: new Date(Date.now() + 2592000000).toISOString(),
    recommendations: [
      {
        id: 'rec1',
        type: 'review_devices',
        priority: 'high',
        title: 'Review Untrusted Device',
        description: 'Review and verify the device that accessed your account from Germany',
        impact: 'High - Potential security risk',
        effort: 'low',
        isImplemented: false,
        metadata: {}
      }
    ],
    trends: [
      {
        date: new Date(Date.now() - 86400000).toISOString(),
        securityScore: 85,
        activeSessions: 2,
        securityEvents: 0,
        suspiciousActivities: 0,
        locationAnomalies: 0,
        deviceAnomalies: 0
      },
      {
        date: new Date().toISOString(),
        securityScore: 82,
        activeSessions: 3,
        securityEvents: 1,
        suspiciousActivities: 1,
        locationAnomalies: 1,
        deviceAnomalies: 1
      }
    ]
  };

  const sampleStats: SessionStats = {
    totalSessions: 3,
    activeSessions: 3,
    trustedSessions: 2,
    suspiciousSessions: 1,
    terminatedSessions: 0,
    averageSessionDuration: 63,
    sessionsByDeviceType: {
      mobile: 1,
      desktop: 1,
      other: 1
    },
    sessionsByLocation: {
      'San Francisco': 2,
      'Berlin': 1
    },
    sessionsByRiskLevel: {
      low: 2,
      high: 1
    }
  };

  // Mock handlers
  const handleTerminateSession = async (sessionId: string, reason?: string) => {
    console.log('Terminating session:', sessionId, 'reason:', reason);
    // Simulate API delay
    await new Promise(resolve => setTimeout(resolve, 1000));
    alert(`Session ${sessionId} terminated successfully`);
  };

  const handleTerminateMultipleSessions = async (sessionIds: string[], reason?: string) => {
    console.log('Terminating multiple sessions:', sessionIds, 'reason:', reason);
    await new Promise(resolve => setTimeout(resolve, 1000));
    alert(`${sessionIds.length} sessions terminated successfully`);
  };

  const handleTrustSession = async (sessionId: string) => {
    console.log('Trusting session:', sessionId);
    await new Promise(resolve => setTimeout(resolve, 1000));
    alert(`Session ${sessionId} trusted successfully`);
  };

  const handleUntrustSession = async (sessionId: string) => {
    console.log('Untrusting session:', sessionId);
    await new Promise(resolve => setTimeout(resolve, 1000));
    alert(`Session ${sessionId} untrusted successfully`);
  };

  const handleMarkAlertAsRead = async (alertId: string) => {
    console.log('Marking alert as read:', alertId);
    await new Promise(resolve => setTimeout(resolve, 1000));
    alert(`Alert ${alertId} marked as read`);
  };

  const handleResolveAlert = async (alertId: string, resolutionNote?: string) => {
    console.log('Resolving alert:', alertId, 'note:', resolutionNote);
    await new Promise(resolve => setTimeout(resolve, 1000));
    alert(`Alert ${alertId} resolved successfully`);
  };

  const handleDismissAlert = async (alertId: string) => {
    console.log('Dismissing alert:', alertId);
    await new Promise(resolve => setTimeout(resolve, 1000));
    alert(`Alert ${alertId} dismissed`);
  };

  const handleUpdateSettings = async (updates: Partial<SessionSettingsType>) => {
    console.log('Updating settings:', updates);
    await new Promise(resolve => setTimeout(resolve, 1000));
    alert('Settings updated successfully');
  };

  const handleResetToDefaults = async () => {
    console.log('Resetting settings to defaults');
    await new Promise(resolve => setTimeout(resolve, 1000));
    alert('Settings reset to defaults');
  };

  const handleAddDevice = async (device: any) => {
    console.log('Adding device:', device);
    await new Promise(resolve => setTimeout(resolve, 1000));
    alert('Device added successfully');
  };

  const handleRemoveDevice = async (deviceId: string) => {
    console.log('Removing device:', deviceId);
    await new Promise(resolve => setTimeout(resolve, 1000));
    alert(`Device ${deviceId} removed successfully`);
  };

  const handleTrustDevice = async (deviceId: string) => {
    console.log('Trusting device:', deviceId);
    await new Promise(resolve => setTimeout(resolve, 1000));
    alert(`Device ${deviceId} trusted successfully`);
  };

  const handleUntrustDevice = async (deviceId: string) => {
    console.log('Untrusting device:', deviceId);
    await new Promise(resolve => setTimeout(resolve, 1000));
    alert(`Device ${deviceId} untrusted successfully`);
  };

  const handleUpdateDevice = async (deviceId: string, updates: Partial<Device>) => {
    console.log('Updating device:', deviceId, 'updates:', updates);
    await new Promise(resolve => setTimeout(resolve, 1000));
    alert(`Device ${deviceId} updated successfully`);
  };

  const handleRefresh = async () => {
    console.log('Refreshing dashboard');
    await new Promise(resolve => setTimeout(resolve, 1000));
    alert('Dashboard refreshed');
  };

  const handleViewDetails = (type: 'sessions' | 'devices' | 'alerts' | 'events') => {
    console.log('Viewing details for:', type);
    setActiveComponent(type === 'sessions' ? 'sessions' : type === 'devices' ? 'devices' : 'alerts');
  };

  const renderComponent = () => {
    switch (activeComponent) {
      case 'sessions':
        return (
          <ActiveSessions
            sessions={sampleSessions}
            onTerminateSession={handleTerminateSession}
            onTerminateMultipleSessions={handleTerminateMultipleSessions}
            onTrustSession={handleTrustSession}
            onUntrustSession={handleUntrustSession}
            onSelectSession={(sessionId, selected) => {
              if (selected) {
                setSelectedSessions(prev => [...prev, sessionId]);
              } else {
                setSelectedSessions(prev => prev.filter(id => id !== sessionId));
              }
            }}
            onSelectAllSessions={(selected) => {
              if (selected) {
                setSelectedSessions(sampleSessions.map(s => s.id));
              } else {
                setSelectedSessions([]);
              }
            }}
            selectedSessions={selectedSessions}
            isLoading={false}
            filters={{}}
            onUpdateFilters={() => {}}
            stats={sampleStats}
          />
        );
      case 'alerts':
        return (
          <SessionAlert
            alerts={sampleAlerts}
            onMarkAsRead={handleMarkAlertAsRead}
            onResolve={handleResolveAlert}
            onDismiss={handleDismissAlert}
            onTakeAction={(alert) => {
              console.log('Taking action on alert:', alert);
              alert(`Taking action on ${alert.title}`);
            }}
            isLoading={false}
            unreadCount={1}
          />
        );
      case 'settings':
        return (
          <SessionSettings
            settings={sampleSettings}
            onUpdateSettings={handleUpdateSettings}
            onResetToDefaults={handleResetToDefaults}
            isLoading={false}
            hasChanges={false}
          />
        );
      case 'devices':
        return (
          <DeviceManagement
            devices={sampleDevices}
            onAddDevice={handleAddDevice}
            onRemoveDevice={handleRemoveDevice}
            onTrustDevice={handleTrustDevice}
            onUntrustDevice={handleUntrustDevice}
            onUpdateDevice={handleUpdateDevice}
            onSelectDevice={(deviceId, selected) => {
              if (selected) {
                setSelectedDevices(prev => [...prev, deviceId]);
              } else {
                setSelectedDevices(prev => prev.filter(id => id !== deviceId));
              }
            }}
            onSelectAllDevices={(selected) => {
              if (selected) {
                setSelectedDevices(sampleDevices.map(d => d.id));
              } else {
                setSelectedDevices([]);
              }
            }}
            selectedDevices={selectedDevices}
            isLoading={false}
            showAddDeviceModal={showAddDeviceModal}
            onShowAddDeviceModal={setShowAddDeviceModal}
          />
        );
      case 'dashboard':
        return (
          <SecurityDashboard
            dashboard={sampleDashboard}
            stats={sampleStats}
            recentAlerts={sampleAlerts}
            onRefresh={handleRefresh}
            onViewDetails={handleViewDetails}
            isLoading={false}
            lastUpdated={new Date().toISOString()}
          />
        );
      default:
        return null;
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">
            Session Management System Demo
          </h1>
          <p className="text-xl text-gray-600 max-w-3xl mx-auto">
            Interactive demonstration of the Mingus advanced session management implementation. 
            Explore each component to see the full range of security features and functionality.
          </p>
        </div>

        {/* Navigation */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 mb-8">
          <div className="px-6 py-4">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Component Selector</h2>
            <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
              <button
                onClick={() => setActiveComponent('dashboard')}
                className={`px-4 py-3 rounded-lg text-sm font-medium transition-colors ${
                  activeComponent === 'dashboard'
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                <div className="flex items-center justify-center space-x-2">
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                  </svg>
                  <span>Dashboard</span>
                </div>
              </button>

              <button
                onClick={() => setActiveComponent('sessions')}
                className={`px-4 py-3 rounded-lg text-sm font-medium transition-colors ${
                  activeComponent === 'sessions'
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                <div className="flex items-center justify-center space-x-2">
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                  </svg>
                  <span>Sessions</span>
                </div>
              </button>

              <button
                onClick={() => setActiveComponent('alerts')}
                className={`px-4 py-3 rounded-lg text-sm font-medium transition-colors ${
                  activeComponent === 'alerts'
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                <div className="flex items-center justify-center space-x-2">
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-7.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.34 16.5c-.77.833.192 2.5 1.732 2.5z" />
                  </svg>
                  <span>Alerts</span>
                </div>
              </button>

              <button
                onClick={() => setActiveComponent('devices')}
                className={`px-4 py-3 rounded-lg text-sm font-medium transition-colors ${
                  activeComponent === 'devices'
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                <div className="flex items-center justify-center space-x-2">
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                  </svg>
                  <span>Devices</span>
                </div>
              </button>

              <button
                onClick={() => setActiveComponent('settings')}
                className={`px-4 py-3 rounded-lg text-sm font-medium transition-colors ${
                  activeComponent === 'settings'
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                <div className="flex items-center justify-center space-x-2">
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                  </svg>
                  <span>Settings</span>
                </div>
              </button>
            </div>
          </div>
        </div>

        {/* Component Display */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200">
          <div className="px-6 py-4 border-b border-gray-200">
            <h2 className="text-xl font-semibold text-gray-900">
              {activeComponent === 'dashboard' && 'Security Dashboard'}
              {activeComponent === 'sessions' && 'Active Sessions Management'}
              {activeComponent === 'alerts' && 'Security Alerts & Notifications'}
              {activeComponent === 'devices' && 'Device Management'}
              {activeComponent === 'settings' && 'Session Settings & Preferences'}
            </h2>
            <p className="text-gray-600 mt-1">
              {activeComponent === 'dashboard' && 'Monitor your account security status and get personalized recommendations'}
              {activeComponent === 'sessions' && 'View and manage your active sessions across all devices'}
              {activeComponent === 'alerts' && 'Review and respond to security notifications and suspicious activity'}
              {activeComponent === 'devices' && 'Manage your trusted devices and monitor device security'}
              {activeComponent === 'settings' && 'Configure your session preferences and security settings'}
            </p>
          </div>
          
          <div className="p-6">
            {renderComponent()}
          </div>
        </div>

        {/* Demo Information */}
        <div className="mt-8 bg-blue-50 border border-blue-200 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-blue-900 mb-3">Demo Information</h3>
          <div className="text-blue-800 text-sm space-y-2">
            <p><strong>Note:</strong> This is a demonstration environment. All API calls are simulated.</p>
            <p><strong>Sample Data:</strong> The demo uses realistic sample data to showcase functionality.</p>
            <p><strong>Interactions:</strong> All buttons and actions are functional and will show success messages.</p>
            <p><strong>Security Features:</strong> Risk assessment, location tracking, and device fingerprinting are simulated.</p>
            <p><strong>Real-time Updates:</strong> WebSocket integration would provide live updates in production.</p>
          </div>
        </div>

        {/* Features Overview */}
        <div className="mt-8 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center mb-4">
              <svg className="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
              </svg>
            </div>
            <h3 className="text-lg font-semibold text-gray-900 mb-2">Enterprise Security</h3>
            <p className="text-gray-600 text-sm">
              Built with enterprise-grade security features including device fingerprinting, location tracking, and behavioral analysis.
            </p>
          </div>

          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center mb-4">
              <svg className="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.207A1 1 0 013 6.5V4z" />
              </svg>
            </div>
            <h3 className="text-lg font-semibold text-gray-900 mb-2">Mobile Optimized</h3>
            <p className="text-gray-600 text-sm">
              Responsive design with touch-friendly interactions and mobile-specific UX patterns for security-conscious users.
            </p>
          </div>

          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center mb-4">
              <svg className="w-6 h-6 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
            </div>
            <h3 className="text-lg font-semibold text-gray-900 mb-2">Real-time Monitoring</h3>
            <p className="text-gray-600 text-sm">
              Live session updates, security alerts, and real-time threat detection with WebSocket integration.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Demo;
