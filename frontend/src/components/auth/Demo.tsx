import React, { useState } from 'react';
import {
  TwoFactorSetup,
  TwoFactorVerification,
  TwoFactorSettings,
  TwoFactorRecovery,
  TwoFactorSetupType,
  TwoFactorSettingsType,
  TwoFactorRecoveryType
} from './index';

const Demo: React.FC = () => {
  const [activeComponent, setActiveComponent] = useState<'setup' | 'verification' | 'settings' | 'recovery'>('setup');
  const [demoData, setDemoData] = useState({
    setup: {
      secret: '',
      qrCodeUrl: '',
      backupCodes: [],
      isEnabled: false,
      setupComplete: false
    },
    settings: {
      isEnabled: true,
      totpEnabled: true,
      smsEnabled: false,
      backupCodesEnabled: true,
      lastUpdated: new Date().toISOString(),
      devices: [
        {
          id: '1',
          name: 'iPhone 12',
          type: 'mobile' as const,
          lastUsed: new Date().toISOString(),
          isTrusted: true
        },
        {
          id: '2',
          name: 'Work Laptop',
          type: 'desktop' as const,
          lastUsed: new Date(Date.now() - 86400000).toISOString(),
          isTrusted: false
        }
      ]
    },
    recovery: {
      backupCodes: ['ABC123', 'DEF456', 'GHI789'],
      usedCodes: ['XYZ999'],
      remainingCodes: 3,
      canGenerateNew: true,
      lastGenerated: new Date().toISOString()
    }
  });

  const handleSetupComplete = (setup: TwoFactorSetupType) => {
    console.log('Setup completed:', setup);
    setDemoData(prev => ({ ...prev, setup }));
    alert('2FA Setup completed successfully!');
  };

  const handleVerification = async (code: string, method: 'totp' | 'sms' | 'backup') => {
    console.log('Verifying code:', code, 'method:', method);
    // Simulate API delay
    await new Promise(resolve => setTimeout(resolve, 1000));
    
    // For demo purposes, accept any 6-digit code
    if (code.length === 6 && /^\d+$/.test(code)) {
      return true;
    }
    return false;
  };

  const handleResendCode = async () => {
    console.log('Resending SMS code...');
    await new Promise(resolve => setTimeout(resolve, 1000));
    alert('SMS code sent successfully!');
  };

  const handleUpdateSettings = async (updates: Partial<TwoFactorSettingsType>) => {
    console.log('Updating settings:', updates);
    setDemoData(prev => ({
      ...prev,
      settings: { ...prev.settings, ...updates }
    }));
  };

  const handleEnableTwoFactor = async () => {
    console.log('Enabling 2FA...');
    await new Promise(resolve => setTimeout(resolve, 1000));
    setDemoData(prev => ({
      ...prev,
      settings: { ...prev.settings, isEnabled: true }
    }));
  };

  const handleDisableTwoFactor = async () => {
    console.log('Disabling 2FA...');
    await new Promise(resolve => setTimeout(resolve, 1000));
    setDemoData(prev => ({
      ...prev,
      settings: { ...prev.settings, isEnabled: false }
    }));
  };

  const handleGenerateBackupCodes = async () => {
    console.log('Generating backup codes...');
    await new Promise(resolve => setTimeout(resolve, 1000));
    const newCodes = Array.from({ length: 8 }, (_, i) => 
      Math.random().toString(36).substring(2, 8).toUpperCase()
    );
    setDemoData(prev => ({
      ...prev,
      settings: { ...prev.settings, backupCodesEnabled: true }
    }));
    return newCodes;
  };

  const handleRegenerateBackupCodes = async () => {
    console.log('Regenerating backup codes...');
    await new Promise(resolve => setTimeout(resolve, 1000));
    const newCodes = Array.from({ length: 8 }, (_, i) => 
      Math.random().toString(36).substring(2, 8).toUpperCase()
    );
    return newCodes;
  };

  const handleAddDevice = async (device: any) => {
    console.log('Adding device:', device);
    const newDevice = {
      ...device,
      id: Date.now().toString(),
      lastUsed: new Date().toISOString(),
      isTrusted: false
    };
    setDemoData(prev => ({
      ...prev,
      settings: {
        ...prev.settings,
        devices: [...prev.settings.devices, newDevice]
      }
    }));
  };

  const handleRemoveDevice = async (deviceId: string) => {
    console.log('Removing device:', deviceId);
    setDemoData(prev => ({
      ...prev,
      settings: {
        ...prev.settings,
        devices: prev.settings.devices.filter(d => d.id !== deviceId)
      }
    }));
  };

  const handleTrustDevice = async (deviceId: string) => {
    console.log('Trusting device:', deviceId);
    setDemoData(prev => ({
      ...prev,
      settings: {
        ...prev.settings,
        devices: prev.settings.devices.map(d => 
          d.id === deviceId ? { ...d, isTrusted: true } : d
        )
      }
    }));
  };

  const handleRecover = async (backupCode: string) => {
    console.log('Recovering with code:', backupCode);
    await new Promise(resolve => setTimeout(resolve, 1000));
    
    // For demo purposes, accept any backup code
    if (backupCode.trim().length > 0) {
      return true;
    }
    return false;
  };

  const handleGenerateNewCodes = async () => {
    console.log('Generating new recovery codes...');
    await new Promise(resolve => setTimeout(resolve, 1000));
    const newCodes = Array.from({ length: 8 }, (_, i) => 
      Math.random().toString(36).substring(2, 8).toUpperCase()
    );
    return newCodes;
  };

  const handleContactSupport = () => {
    console.log('Contacting support...');
    alert('Support contact form would open here');
  };

  const renderComponent = () => {
    switch (activeComponent) {
      case 'setup':
        return (
          <TwoFactorSetup
            onComplete={handleSetupComplete}
            onCancel={() => console.log('Setup cancelled')}
            initialSetup={demoData.setup}
          />
        );
      case 'verification':
        return (
          <TwoFactorVerification
            onVerify={handleVerification}
            onCancel={() => console.log('Verification cancelled')}
            onResendCode={handleResendCode}
            maxAttempts={5}
            biometricAvailable={true}
            biometricEnabled={true}
          />
        );
      case 'settings':
        return (
          <TwoFactorSettings
            settings={demoData.settings}
            onUpdateSettings={handleUpdateSettings}
            onEnableTwoFactor={handleEnableTwoFactor}
            onDisableTwoFactor={handleDisableTwoFactor}
            onGenerateBackupCodes={handleGenerateBackupCodes}
            onRegenerateBackupCodes={handleRegenerateBackupCodes}
            onAddDevice={handleAddDevice}
            onRemoveDevice={handleRemoveDevice}
            onTrustDevice={handleTrustDevice}
            biometricAvailable={true}
            biometricEnabled={false}
          />
        );
      case 'recovery':
        return (
          <TwoFactorRecovery
            recovery={demoData.recovery}
            onRecover={handleRecover}
            onGenerateNewCodes={handleGenerateNewCodes}
            onContactSupport={handleContactSupport}
            maxAttempts={5}
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
            Two-Factor Authentication Components Demo
          </h1>
          <p className="text-xl text-gray-600 max-w-3xl mx-auto">
            Interactive demonstration of the Mingus 2FA implementation. 
            Explore each component to see the full range of features and functionality.
          </p>
        </div>

        {/* Navigation */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 mb-8">
          <div className="px-6 py-4">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Component Selector</h2>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              <button
                onClick={() => setActiveComponent('setup')}
                className={`px-4 py-3 rounded-lg text-sm font-medium transition-colors ${
                  activeComponent === 'setup'
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                <div className="flex items-center justify-center space-x-2">
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 100 4m0-4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 100 4m0-4v2m0-6V4" />
                  </svg>
                  <span>Setup</span>
                </div>
              </button>

              <button
                onClick={() => setActiveComponent('verification')}
                className={`px-4 py-3 rounded-lg text-sm font-medium transition-colors ${
                  activeComponent === 'verification'
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                <div className="flex items-center justify-center space-x-2">
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                  </svg>
                  <span>Verification</span>
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
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                  </svg>
                  <span>Settings</span>
                </div>
              </button>

              <button
                onClick={() => setActiveComponent('recovery')}
                className={`px-4 py-3 rounded-lg text-sm font-medium transition-colors ${
                  activeComponent === 'recovery'
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                <div className="flex items-center justify-center space-x-2">
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                  </svg>
                  <span>Recovery</span>
                </div>
              </button>
            </div>
          </div>
        </div>

        {/* Component Display */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200">
          <div className="px-6 py-4 border-b border-gray-200">
            <h2 className="text-xl font-semibold text-gray-900">
              {activeComponent === 'setup' && 'Two-Factor Authentication Setup'}
              {activeComponent === 'verification' && 'Two-Factor Authentication Verification'}
              {activeComponent === 'settings' && 'Two-Factor Authentication Settings'}
              {activeComponent === 'recovery' && 'Account Recovery'}
            </h2>
            <p className="text-gray-600 mt-1">
              {activeComponent === 'setup' && 'Complete the 2FA setup process with QR codes and backup codes'}
              {activeComponent === 'verification' && 'Verify your identity using TOTP, SMS, or backup codes'}
              {activeComponent === 'settings' && 'Manage your 2FA preferences and trusted devices'}
              {activeComponent === 'recovery' && 'Recover your account using backup codes'}
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
            <p><strong>TOTP Verification:</strong> Enter any 6-digit number to simulate successful verification.</p>
            <p><strong>Backup Codes:</strong> Enter any text to simulate successful recovery.</p>
            <p><strong>Settings:</strong> Changes are stored locally and will reset on page refresh.</p>
            <p><strong>Biometric:</strong> Biometric authentication is simulated and always succeeds.</p>
          </div>
        </div>

        {/* Features Overview */}
        <div className="mt-8 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center mb-4">
              <svg className="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
              </svg>
            </div>
            <h3 className="text-lg font-semibold text-gray-900 mb-2">Security First</h3>
            <p className="text-gray-600 text-sm">
              Built with security best practices including rate limiting, attempt tracking, and secure code generation.
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
              Responsive design with touch-friendly interactions and mobile-specific UX patterns.
            </p>
          </div>

          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center mb-4">
              <svg className="w-6 h-6 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
            </div>
            <h3 className="text-lg font-semibold text-gray-900 mb-2">Accessibility</h3>
            <p className="text-gray-600 text-sm">
              WCAG 2.1 compliant with screen reader support, keyboard navigation, and high contrast design.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Demo;
