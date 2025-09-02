import React, { useState, useEffect } from 'react';
import { 
  TwoFactorSettings as TwoFactorSettingsType,
  TwoFactorDevice,
  DeviceManagementProps,
  BackupCodeDisplayProps,
  BiometricAuthProps,
  OfflineIndicatorProps,
  ErrorDisplayProps,
  SuccessDisplayProps
} from '@/types/twoFactor';

interface TwoFactorSettingsProps {
  settings: TwoFactorSettingsType;
  onUpdateSettings: (settings: Partial<TwoFactorSettingsType>) => Promise<void>;
  onEnableTwoFactor: () => Promise<void>;
  onDisableTwoFactor: () => Promise<void>;
  onGenerateBackupCodes: () => Promise<string[]>;
  onRegenerateBackupCodes: () => Promise<string[]>;
  onAddDevice: (device: Omit<TwoFactorDevice, 'id' | 'lastUsed'>) => Promise<void>;
  onRemoveDevice: (deviceId: string) => Promise<void>;
  onTrustDevice: (deviceId: string) => Promise<void>;
  onEnableBiometric?: () => Promise<void>;
  onDisableBiometric?: () => Promise<void>;
  biometricAvailable?: boolean;
  biometricEnabled?: boolean;
  isOffline?: boolean;
  lastSync?: string;
}

const TwoFactorSettings: React.FC<TwoFactorSettingsProps> = ({
  settings,
  onUpdateSettings,
  onEnableTwoFactor,
  onDisableTwoFactor,
  onGenerateBackupCodes,
  onRegenerateBackupCodes,
  onAddDevice,
  onRemoveDevice,
  onTrustDevice,
  onEnableBiometric,
  onDisableBiometric,
  biometricAvailable = false,
  biometricEnabled = false,
  isOffline = false,
  lastSync = ''
}) => {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [showBackupCodes, setShowBackupCodes] = useState(false);
  const [showAddDevice, setShowAddDevice] = useState(false);
  const [showDisableConfirm, setShowDisableConfirm] = useState(false);
  const [newDevice, setNewDevice] = useState({
    name: '',
    type: 'other' as const
  });
  const [backupCodes, setBackupCodes] = useState<string[]>([]);

  const handleEnableTwoFactor = async () => {
    try {
      setIsLoading(true);
      setError(null);
      
      await onEnableTwoFactor();
      setSuccess('Two-factor authentication enabled successfully!');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to enable two-factor authentication');
    } finally {
      setIsLoading(false);
    }
  };

  const handleDisableTwoFactor = async () => {
    try {
      setIsLoading(true);
      setError(null);
      
      await onDisableTwoFactor();
      setSuccess('Two-factor authentication disabled successfully!');
      setShowDisableConfirm(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to disable two-factor authentication');
    } finally {
      setIsLoading(false);
    }
  };

  const handleGenerateBackupCodes = async () => {
    try {
      setIsLoading(true);
      setError(null);
      
      const codes = await onGenerateBackupCodes();
      setBackupCodes(codes);
      setShowBackupCodes(true);
      setSuccess('Backup codes generated successfully!');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to generate backup codes');
    } finally {
      setIsLoading(false);
    }
  };

  const handleRegenerateBackupCodes = async () => {
    try {
      setIsLoading(true);
      setError(null);
      
      const codes = await onRegenerateBackupCodes();
      setBackupCodes(codes);
      setShowBackupCodes(true);
      setSuccess('Backup codes regenerated successfully!');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to regenerate backup codes');
    } finally {
      setIsLoading(false);
    }
  };

  const handleAddDevice = async () => {
    if (!newDevice.name.trim()) {
      setError('Please enter a device name');
      return;
    }

    try {
      setIsLoading(true);
      setError(null);
      
      await onAddDevice({
        name: newDevice.name.trim(),
        type: newDevice.type,
        isTrusted: false
      });
      
      setNewDevice({ name: '', type: 'other' });
      setShowAddDevice(false);
      setSuccess('Device added successfully!');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to add device');
    } finally {
      setIsLoading(false);
    }
  };

  const handleRemoveDevice = async (deviceId: string) => {
    try {
      setIsLoading(true);
      setError(null);
      
      await onRemoveDevice(deviceId);
      setSuccess('Device removed successfully!');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to remove device');
    } finally {
      setIsLoading(false);
    }
  };

  const handleTrustDevice = async (deviceId: string) => {
    try {
      setIsLoading(true);
      setError(null);
      
      await onTrustDevice(deviceId);
      setSuccess('Device trusted successfully!');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to trust device');
    } finally {
      setIsLoading(false);
    }
  };

  const handleBiometricToggle = async () => {
    try {
      setIsLoading(true);
      setError(null);
      
      if (biometricEnabled && onDisableBiometric) {
        await onDisableBiometric();
        setSuccess('Biometric authentication disabled successfully!');
      } else if (!biometricEnabled && onEnableBiometric) {
        await onEnableBiometric();
        setSuccess('Biometric authentication enabled successfully!');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to toggle biometric authentication');
    } finally {
      setIsLoading(false);
    }
  };

  const clearMessages = () => {
    setError(null);
    setSuccess(null);
  };

  useEffect(() => {
    const timer = setTimeout(clearMessages, 5000);
    return () => clearTimeout(timer);
  }, [error, success]);

  return (
    <div className="max-w-4xl mx-auto bg-white rounded-lg shadow-lg overflow-hidden">
      {/* Header */}
      <div className="bg-gradient-to-r from-blue-600 to-purple-600 px-6 py-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-white">Two-Factor Authentication Settings</h1>
            <p className="text-blue-100 mt-1">Manage your account security preferences</p>
          </div>
          <div className="flex items-center space-x-3">
            <div className={`px-3 py-1 rounded-full text-sm font-medium ${
              settings.isEnabled 
                ? 'bg-green-100 text-green-800' 
                : 'bg-red-100 text-red-800'
            }`}>
              {settings.isEnabled ? 'Enabled' : 'Disabled'}
            </div>
          </div>
        </div>
      </div>

      {/* Offline Indicator */}
      {isOffline && (
        <OfflineIndicator
          isOffline={isOffline}
          lastSync={lastSync}
          onRetry={() => window.location.reload()}
        />
      )}

      {/* Error Display */}
      {error && (
        <ErrorDisplay
          error={error}
          onDismiss={() => setError(null)}
        />
      )}

      {/* Success Display */}
      {success && (
        <SuccessDisplay
          message={success}
          onDismiss={() => setSuccess(null)}
          showAnimation={true}
        />
      )}

      {/* Main Content */}
      <div className="p-6 space-y-8">
        {/* Status Section */}
        <div className="bg-gray-50 rounded-lg p-6">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-xl font-semibold text-gray-900 mb-2">
                Two-Factor Authentication Status
              </h2>
              <p className="text-gray-600">
                {settings.isEnabled 
                  ? 'Your account is protected with two-factor authentication.'
                  : 'Enable two-factor authentication to add an extra layer of security to your account.'
                }
              </p>
            </div>
            <div className="flex items-center space-x-3">
              {!settings.isEnabled ? (
                <button
                  onClick={handleEnableTwoFactor}
                  disabled={isLoading}
                  className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  {isLoading ? 'Enabling...' : 'Enable 2FA'}
                </button>
              ) : (
                <button
                  onClick={() => setShowDisableConfirm(true)}
                  disabled={isLoading}
                  className="px-6 py-3 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  Disable 2FA
                </button>
              )}
            </div>
          </div>

          {settings.isEnabled && (
            <div className="mt-4 grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="bg-white p-4 rounded-lg border">
                <div className="flex items-center">
                  <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center mr-3">
                    <svg className="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                  </div>
                  <div>
                    <p className="font-medium text-gray-900">TOTP</p>
                    <p className="text-sm text-gray-500">
                      {settings.totpEnabled ? 'Active' : 'Inactive'}
                    </p>
                  </div>
                </div>
              </div>

              <div className="bg-white p-4 rounded-lg border">
                <div className="flex items-center">
                  <div className="w-10 h-10 bg-green-100 rounded-full flex items-center justify-center mr-3">
                    <svg className="w-5 h-5 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z" />
                    </svg>
                  </div>
                  <div>
                    <p className="font-medium text-gray-900">SMS</p>
                    <p className="text-sm text-gray-500">
                      {settings.smsEnabled ? 'Active' : 'Inactive'}
                    </p>
                  </div>
                </div>
              </div>

              <div className="bg-white p-4 rounded-lg border">
                <div className="flex items-center">
                  <div className="w-10 h-10 bg-purple-100 rounded-full flex items-center justify-center mr-3">
                    <svg className="w-5 h-5 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                  </div>
                  <div>
                    <p className="font-medium text-gray-900">Backup Codes</p>
                    <p className="text-sm text-gray-500">
                      {settings.backupCodesEnabled ? 'Active' : 'Inactive'}
                    </p>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Biometric Authentication */}
        {biometricAvailable && (
          <div className="bg-gray-50 rounded-lg p-6">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-xl font-semibold text-gray-900 mb-2">
                  Biometric Authentication
                </h2>
                <p className="text-gray-600">
                  Use your fingerprint or face ID for quick and secure access
                </p>
              </div>
              <div className="flex items-center space-x-3">
                <div className={`px-3 py-1 rounded-full text-sm font-medium ${
                  biometricEnabled 
                    ? 'bg-green-100 text-green-800' 
                    : 'bg-gray-100 text-gray-800'
                }`}>
                  {biometricEnabled ? 'Enabled' : 'Disabled'}
                </div>
                <button
                  onClick={handleBiometricToggle}
                  disabled={isLoading}
                  className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                    biometricEnabled
                      ? 'bg-red-600 text-white hover:bg-red-700'
                      : 'bg-blue-600 text-white hover:bg-blue-700'
                  } disabled:opacity-50 disabled:cursor-not-allowed`}
                >
                  {isLoading ? 'Updating...' : biometricEnabled ? 'Disable' : 'Enable'}
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Backup Codes Section */}
        <div className="bg-gray-50 rounded-lg p-6">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-xl font-semibold text-gray-900">Backup Codes</h2>
              <p className="text-gray-600">
                Generate backup codes to access your account if you lose your authenticator device
              </p>
            </div>
            <div className="flex space-x-3">
              <button
                onClick={handleGenerateBackupCodes}
                disabled={isLoading}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {isLoading ? 'Generating...' : 'Generate Codes'}
              </button>
              <button
                onClick={handleRegenerateBackupCodes}
                disabled={isLoading}
                className="px-4 py-2 bg-yellow-600 text-white rounded-lg hover:bg-yellow-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                Regenerate
              </button>
            </div>
          </div>

          {showBackupCodes && backupCodes.length > 0 && (
            <div className="mt-4">
              <BackupCodeDisplay
                codes={backupCodes}
                onCopy={(code) => navigator.clipboard.writeText(code)}
                onDownload={() => {
                  const blob = new Blob([backupCodes.join('\n')], { type: 'text/plain' });
                  const url = URL.createObjectURL(blob);
                  const a = document.createElement('a');
                  a.href = url;
                  a.download = 'mingus-backup-codes.txt';
                  a.click();
                  URL.revokeObjectURL(url);
                }}
                onPrint={() => window.print()}
                showRegenerate={false}
              />
            </div>
          )}
        </div>

        {/* Device Management */}
        <div className="bg-gray-50 rounded-lg p-6">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-xl font-semibold text-gray-900">Trusted Devices</h2>
              <p className="text-gray-600">
                Manage devices that can access your account without additional verification
              </p>
            </div>
            <button
              onClick={() => setShowAddDevice(true)}
              className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
            >
              Add Device
            </button>
          </div>

          <DeviceManagement
            devices={settings.devices}
            onAddDevice={onAddDevice}
            onRemoveDevice={handleRemoveDevice}
            onTrustDevice={handleTrustDevice}
          />
        </div>

        {/* Last Updated */}
        <div className="text-center text-sm text-gray-500">
          Last updated: {new Date(settings.lastUpdated).toLocaleString()}
        </div>
      </div>

      {/* Modals */}
      {showDisableConfirm && (
        <DisableConfirmationModal
          onConfirm={handleDisableTwoFactor}
          onCancel={() => setShowDisableConfirm(false)}
          isLoading={isLoading}
        />
      )}

      {showAddDevice && (
        <AddDeviceModal
          device={newDevice}
          onDeviceChange={setNewDevice}
          onAdd={handleAddDevice}
          onCancel={() => setShowAddDevice(false)}
          isLoading={isLoading}
        />
      )}
    </div>
  );
};

// Modal Components
const DisableConfirmationModal: React.FC<{
  onConfirm: () => void;
  onCancel: () => void;
  isLoading: boolean;
}> = ({ onConfirm, onCancel, isLoading }) => (
  <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
    <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
      <div className="text-center">
        <div className="w-16 h-16 mx-auto bg-red-100 rounded-full flex items-center justify-center mb-4">
          <svg className="w-8 h-8 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-7.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.34 16.5c-.77.833.192 2.5 1.732 2.5z" />
          </svg>
        </div>
        
        <h3 className="text-lg font-semibold text-gray-900 mb-2">
          Disable Two-Factor Authentication?
        </h3>
        <p className="text-gray-600 mb-6">
          This will remove the extra security layer from your account. 
          You'll only need your password to sign in.
        </p>
        
        <div className="flex space-x-3">
          <button
            onClick={onCancel}
            disabled={isLoading}
            className="flex-1 px-4 py-2 text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 disabled:opacity-50 transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={onConfirm}
            disabled={isLoading}
            className="flex-1 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {isLoading ? 'Disabling...' : 'Disable 2FA'}
          </button>
        </div>
      </div>
    </div>
  </div>
);

const AddDeviceModal: React.FC<{
  device: { name: string; type: 'mobile' | 'desktop' | 'tablet' | 'other' };
  onDeviceChange: (device: { name: string; type: 'mobile' | 'desktop' | 'tablet' | 'other' }) => void;
  onAdd: () => void;
  onCancel: () => void;
  isLoading: boolean;
}> = ({ device, onDeviceChange, onAdd, onCancel, isLoading }) => (
  <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
    <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">Add Trusted Device</h3>
      
      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Device Name
          </label>
          <input
            type="text"
            value={device.name}
            onChange={(e) => onDeviceChange({ ...device, name: e.target.value })}
            placeholder="e.g., iPhone 12, Work Laptop"
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:border-blue-500 focus:outline-none"
          />
        </div>
        
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Device Type
          </label>
          <select
            value={device.type}
            onChange={(e) => onDeviceChange({ ...device, type: e.target.value as any })}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:border-blue-500 focus:outline-none"
          >
            <option value="mobile">Mobile Phone</option>
            <option value="desktop">Desktop Computer</option>
            <option value="tablet">Tablet</option>
            <option value="other">Other</option>
          </select>
        </div>
      </div>
      
      <div className="flex space-x-3 mt-6">
        <button
          onClick={onCancel}
          disabled={isLoading}
          className="flex-1 px-4 py-2 text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 disabled:opacity-50 transition-colors"
        >
          Cancel
        </button>
        <button
          onClick={onAdd}
          disabled={isLoading || !device.name.trim()}
          className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {isLoading ? 'Adding...' : 'Add Device'}
        </button>
      </div>
    </div>
  </div>
);

// Placeholder components (these would be implemented separately)
const DeviceManagement: React.FC<DeviceManagementProps> = ({ devices, onRemoveDevice, onTrustDevice }) => (
  <div className="space-y-3">
    {devices.length === 0 ? (
      <div className="text-center py-8 text-gray-500">
        <svg className="w-12 h-12 mx-auto mb-3 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
        </svg>
        <p>No trusted devices yet</p>
        <p className="text-sm">Add a device to skip 2FA verification on trusted devices</p>
      </div>
    ) : (
      devices.map((device) => (
        <div key={device.id} className="bg-white p-4 rounded-lg border flex items-center justify-between">
          <div className="flex items-center">
            <div className={`w-10 h-10 rounded-full flex items-center justify-center mr-3 ${
              device.type === 'mobile' ? 'bg-blue-100' :
              device.type === 'desktop' ? 'bg-green-100' :
              device.type === 'tablet' ? 'bg-purple-100' : 'bg-gray-100'
            }`}>
              <svg className={`w-5 h-5 ${
                device.type === 'mobile' ? 'text-blue-600' :
                device.type === 'desktop' ? 'text-green-600' :
                device.type === 'tablet' ? 'text-purple-600' : 'text-gray-600'
              }`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
              </svg>
            </div>
            <div>
              <p className="font-medium text-gray-900">{device.name}</p>
              <p className="text-sm text-gray-500">
                {device.type} • Last used: {new Date(device.lastUsed).toLocaleDateString()}
              </p>
            </div>
          </div>
          
          <div className="flex items-center space-x-2">
            {!device.isTrusted && (
              <button
                onClick={() => onTrustDevice(device.id)}
                className="px-3 py-1 text-xs bg-blue-100 text-blue-800 rounded-full hover:bg-blue-200 transition-colors"
              >
                Trust
              </button>
            )}
            <button
              onClick={() => onRemoveDevice(device.id)}
              className="px-3 py-1 text-xs bg-red-100 text-red-800 rounded-full hover:bg-red-200 transition-colors"
            >
              Remove
            </button>
          </div>
        </div>
      ))
    )}
  </div>
);

const BackupCodeDisplay: React.FC<BackupCodeDisplayProps> = ({ codes, onCopy, onDownload, onPrint }) => (
  <div className="space-y-4">
    <div className="grid grid-cols-2 gap-3">
      {codes.map((code, index) => (
        <div key={index} className="bg-white p-3 rounded-lg border">
          <div className="flex items-center justify-between">
            <code className="font-mono text-gray-800">{code}</code>
            <button
              onClick={() => onCopy(code)}
              className="ml-2 text-blue-600 hover:text-blue-700 transition-colors"
              aria-label={`Copy code ${index + 1}`}
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
              </svg>
            </button>
          </div>
        </div>
      ))}
    </div>
    
    <div className="flex justify-center space-x-3">
      <button
        onClick={onDownload}
        className="px-4 py-2 text-blue-600 border border-blue-600 rounded-lg hover:bg-blue-50 transition-colors"
      >
        Download Codes
      </button>
      <button
        onClick={onPrint}
        className="px-4 py-2 text-green-600 border border-green-600 rounded-lg hover:bg-green-50 transition-colors"
      >
        Print Codes
      </button>
    </div>
  </div>
);

const OfflineIndicator: React.FC<OfflineIndicatorProps> = ({ isOffline, lastSync, onRetry }) => (
  <div className="bg-yellow-50 border border-yellow-200 px-6 py-3">
    <div className="flex items-center justify-between">
      <div className="flex items-center">
        <svg className="h-5 w-5 text-yellow-400 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-7.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.34 16.5c-.77.833.192 2.5 1.732 2.5z" />
        </svg>
        <span className="text-sm text-yellow-800">
          You're currently offline. Last sync: {lastSync}
        </span>
      </div>
      <button
        onClick={onRetry}
        className="text-yellow-800 hover:text-yellow-600 transition-colors text-sm font-medium"
      >
        Retry
      </button>
    </div>
  </div>
);

const ErrorDisplay: React.FC<ErrorDisplayProps> = ({ error, onDismiss }) => (
  <div className="bg-red-50 border border-red-200 px-6 py-3">
    <div className="flex items-start">
      <div className="flex-shrink-0">
        <svg className="h-5 w-5 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      </div>
      <div className="ml-3 flex-1">
        <p className="text-sm text-red-800">{error}</p>
      </div>
      <div className="ml-auto pl-3">
        <div className="-mx-1.5 -my-1.5">
          {onDismiss && (
            <button
              onClick={onDismiss}
              className="text-red-800 hover:text-red-600 transition-colors text-sm"
            >
              Dismiss
            </button>
          )}
        </div>
      </div>
    </div>
  </div>
);

const SuccessDisplay: React.FC<SuccessDisplayProps> = ({ message, onDismiss, showAnimation }) => (
  <div className="bg-green-50 border border-green-200 px-6 py-3">
    <div className="flex items-start">
      <div className="flex-shrink-0">
        <svg className="h-5 w-5 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
        </svg>
      </div>
      <div className="ml-3 flex-1">
        <p className="text-sm text-green-800">{message}</p>
      </div>
      <div className="ml-auto pl-3">
        <div className="-mx-1.5 -my-1.5">
          {onDismiss && (
            <button
              onClick={onDismiss}
              className="text-green-800 hover:text-green-600 transition-colors text-sm"
            >
              Dismiss
            </button>
          )}
        </div>
      </div>
    </div>
  </div>
);

export default TwoFactorSettings;
