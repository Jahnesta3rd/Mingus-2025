import React, { useState, useEffect } from 'react';
import { 
  TwoFactorRecovery as TwoFactorRecoveryType,
  BackupCodeDisplayProps,
  ErrorDisplayProps,
  SuccessDisplayProps,
  OfflineIndicatorProps,
  ProgressIndicatorProps
} from '@/types/twoFactor';

interface TwoFactorRecoveryProps {
  onRecover: (backupCode: string) => Promise<boolean>;
  onGenerateNewCodes: () => Promise<string[]>;
  onContactSupport: () => void;
  recovery: TwoFactorRecoveryType;
  isOffline?: boolean;
  lastSync?: string;
  maxAttempts?: number;
}

const TwoFactorRecovery: React.FC<TwoFactorRecoveryProps> = ({
  onRecover,
  onGenerateNewCodes,
  onContactSupport,
  recovery,
  isOffline = false,
  lastSync = '',
  maxAttempts = 5
}) => {
  const [currentStep, setCurrentStep] = useState(0);
  const [backupCode, setBackupCode] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [attempts, setAttempts] = useState(0);
  const [showNewCodes, setShowNewCodes] = useState(false);
  const [newCodes, setNewCodes] = useState<string[]>([]);
  const [showContactSupport, setShowContactSupport] = useState(false);

  const steps = [
    'Verify Identity',
    'Enter Backup Code',
    'Account Recovery',
    'Generate New Codes',
    'Recovery Complete'
  ];

  useEffect(() => {
    if (recovery.remainingCodes === 0) {
      setCurrentStep(3); // Skip to generate new codes step
    }
  }, [recovery.remainingCodes]);

  const handleRecovery = async () => {
    if (!backupCode.trim()) {
      setError('Please enter a backup code');
      return;
    }

    if (attempts >= maxAttempts) {
      setError('Maximum recovery attempts exceeded. Please contact support.');
      return;
    }

    try {
      setIsLoading(true);
      setError(null);
      
      const success = await onRecover(backupCode.trim());
      
      if (success) {
        setSuccess('Backup code verified successfully!');
        setAttempts(0);
        setCurrentStep(2);
      } else {
        setAttempts(prev => prev + 1);
        setError('Invalid backup code. Please try again.');
        setBackupCode('');
        
        if (attempts + 1 >= maxAttempts) {
          setError('Maximum recovery attempts exceeded. Your account has been temporarily locked for security reasons.');
        }
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Recovery failed. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleGenerateNewCodes = async () => {
    try {
      setIsLoading(true);
      setError(null);
      
      const codes = await onGenerateNewCodes();
      setNewCodes(codes);
      setShowNewCodes(true);
      setSuccess('New backup codes generated successfully!');
      setCurrentStep(4);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to generate new backup codes');
    } finally {
      setIsLoading(false);
    }
  };

  const handleNext = () => {
    if (currentStep < steps.length - 1) {
      setCurrentStep(prev => prev + 1);
      setError(null);
      setSuccess(null);
    }
  };

  const handlePrevious = () => {
    if (currentStep > 0) {
      setCurrentStep(prev => prev - 1);
      setError(null);
      setSuccess(null);
    }
  };

  const canProceed = () => {
    switch (currentStep) {
      case 0: return true; // Identity verification
      case 1: return backupCode.trim().length > 0; // Backup code input
      case 2: return true; // Account recovery
      case 3: return true; // Generate new codes
      case 4: return true; // Recovery complete
      default: return false;
    }
  };

  const renderStepContent = () => {
    switch (currentStep) {
      case 0:
        return <IdentityVerificationStep />;
      case 1:
        return (
          <BackupCodeInputStep
            backupCode={backupCode}
            setBackupCode={setBackupCode}
            onRecover={handleRecovery}
            isLoading={isLoading}
            attempts={attempts}
            maxAttempts={maxAttempts}
            remainingCodes={recovery.remainingCodes}
          />
        );
      case 2:
        return (
          <AccountRecoveryStep
            onGenerateNewCodes={handleGenerateNewCodes}
            onContactSupport={() => setShowContactSupport(true)}
            isLoading={isLoading}
          />
        );
      case 3:
        return (
          <GenerateNewCodesStep
            onGenerate={handleGenerateNewCodes}
            isLoading={isLoading}
            canGenerate={recovery.canGenerateNew}
            lastGenerated={recovery.lastGenerated}
          />
        );
      case 4:
        return (
          <RecoveryCompleteStep
            newCodes={newCodes}
            showNewCodes={showNewCodes}
          />
        );
      default:
        return null;
    }
  };

  return (
    <div className="max-w-2xl mx-auto bg-white rounded-lg shadow-lg overflow-hidden">
      {/* Header */}
      <div className="bg-gradient-to-r from-orange-600 to-red-600 px-6 py-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-white">Account Recovery</h1>
            <p className="text-orange-100 mt-1">Regain access to your account using backup codes</p>
          </div>
          <div className="w-12 h-12 bg-white bg-opacity-20 rounded-full flex items-center justify-center">
            <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
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

      {/* Progress Indicator */}
      <ProgressIndicator
        current={currentStep + 1}
        total={steps.length}
        steps={steps}
        showLabels={true}
      />

      {/* Error Display */}
      {error && (
        <ErrorDisplay
          error={error}
          onRetry={() => setError(null)}
          onDismiss={() => setError(null)}
        />
      )}

      {/* Success Display */}
      {success && (
        <SuccessDisplay
          message={success}
          onContinue={() => setSuccess(null)}
          onDismiss={() => setSuccess(null)}
          showAnimation={true}
        />
      )}

      {/* Step Content */}
      <div className="p-6">
        {renderStepContent()}
      </div>

      {/* Navigation */}
      <div className="bg-gray-50 px-6 py-4 flex justify-between">
        <button
          onClick={handlePrevious}
          disabled={currentStep === 0}
          className="px-4 py-2 text-gray-600 hover:text-gray-800 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          Previous
        </button>
        
        <div className="flex space-x-3">
          <button
            onClick={() => setShowContactSupport(true)}
            className="px-4 py-2 text-gray-600 hover:text-gray-800 transition-colors"
          >
            Contact Support
          </button>
          
          {currentStep < steps.length - 1 && (
            <button
              onClick={handleNext}
              disabled={!canProceed() || isLoading}
              className="px-6 py-2 bg-orange-600 text-white rounded-lg hover:bg-orange-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              Next
            </button>
          )}
        </div>
      </div>

      {/* Contact Support Modal */}
      {showContactSupport && (
        <ContactSupportModal
          onClose={() => setShowContactSupport(false)}
          onContactSupport={onContactSupport}
        />
      )}
    </div>
  );
};

// Step Components
const IdentityVerificationStep: React.FC = () => (
  <div className="text-center space-y-6">
    <div className="w-24 h-24 mx-auto bg-orange-100 rounded-full flex items-center justify-center">
      <svg className="w-12 h-12 text-orange-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
      </svg>
    </div>
    
    <div>
      <h2 className="text-2xl font-bold text-gray-900 mb-2">Verify Your Identity</h2>
      <p className="text-gray-600 leading-relaxed">
        Before we can help you recover your account, we need to verify your identity. 
        This helps protect your account from unauthorized access.
      </p>
    </div>

    <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 text-left">
      <h3 className="font-semibold text-blue-900 mb-2">What you'll need:</h3>
      <ul className="text-blue-800 space-y-1 text-sm">
        <li>• Access to your registered email address</li>
        <li>• One of your backup codes (if available)</li>
        <li>• Government-issued ID (may be required)</li>
        <li>• Recent account activity details</li>
      </ul>
    </div>

    <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 text-left">
      <h3 className="font-semibold text-yellow-900 mb-2">Important:</h3>
      <p className="text-yellow-800 text-sm">
        Account recovery can take 24-48 hours for security verification. 
        We'll contact you via email with updates on your recovery request.
      </p>
    </div>
  </div>
);

const BackupCodeInputStep: React.FC<{
  backupCode: string;
  setBackupCode: (code: string) => void;
  onRecover: () => Promise<void>;
  isLoading: boolean;
  attempts: number;
  maxAttempts: number;
  remainingCodes: number;
}> = ({ backupCode, setBackupCode, onRecover, isLoading, attempts, maxAttempts, remainingCodes }) => (
  <div className="space-y-6">
    <div className="text-center">
      <h2 className="text-2xl font-bold text-gray-900 mb-2">Enter Backup Code</h2>
      <p className="text-gray-600">
        Enter one of your backup codes to verify your identity and recover your account
      </p>
    </div>

    <div className="max-w-md mx-auto">
      <div className="mb-4">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Backup Code
        </label>
        <input
          type="text"
          value={backupCode}
          onChange={(e) => setBackupCode(e.target.value)}
          placeholder="Enter your backup code"
          className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:border-orange-500 focus:outline-none text-center font-mono text-lg"
          disabled={isLoading}
          autoFocus={true}
        />
      </div>

      <button
        onClick={onRecover}
        disabled={!backupCode.trim() || isLoading}
        className="w-full px-6 py-3 bg-orange-600 text-white rounded-lg hover:bg-orange-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
      >
        {isLoading ? 'Verifying...' : 'Verify Code'}
      </button>
    </div>

    {attempts > 0 && (
      <div className="text-center text-sm text-gray-600">
        Attempts remaining: {maxAttempts - attempts}
      </div>
    )}

    <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
      <h3 className="font-semibold text-yellow-900 mb-2">Remaining Backup Codes:</h3>
      <p className="text-yellow-800 text-sm">
        You have {remainingCodes} backup codes remaining. 
        {remainingCodes === 0 && ' You\'ll need to generate new codes after recovery.'}
      </p>
    </div>

    <div className="bg-red-50 border border-red-200 rounded-lg p-4">
      <h3 className="font-semibold text-red-900 mb-2">Important Security Notes:</h3>
      <ul className="text-red-800 text-sm space-y-1">
        <li>• Each backup code can only be used once</li>
        <li>• After using a backup code, it will be invalidated</li>
        <li>• If you don't have backup codes, contact support</li>
        <li>• Recovery may require additional verification</li>
      </ul>
    </div>
  </div>
);

const AccountRecoveryStep: React.FC<{
  onGenerateNewCodes: () => Promise<void>;
  onContactSupport: () => void;
  isLoading: boolean;
}> = ({ onGenerateNewCodes, onContactSupport, isLoading }) => (
  <div className="text-center space-y-6">
    <div className="w-24 h-24 mx-auto bg-green-100 rounded-full flex items-center justify-center">
      <svg className="w-12 h-12 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
      </svg>
    </div>
    
    <div>
      <h2 className="text-2xl font-bold text-gray-900 mb-2">Account Recovery Successful!</h2>
      <p className="text-gray-600 leading-relaxed">
        Your identity has been verified and your account is now accessible. 
        We recommend generating new backup codes and reviewing your security settings.
      </p>
    </div>

    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      <button
        onClick={onGenerateNewCodes}
        disabled={isLoading}
        className="p-6 bg-blue-50 border border-blue-200 rounded-lg hover:bg-blue-100 transition-colors disabled:opacity-50"
      >
        <svg className="w-12 h-12 text-blue-600 mx-auto mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 100 4m0-4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 100 4m0-4v2m0-6V4" />
        </svg>
        <h3 className="font-semibold text-blue-900 mb-1">Generate New Backup Codes</h3>
        <p className="text-blue-700 text-sm">Create new backup codes to replace the used ones</p>
      </button>

      <button
        onClick={onContactSupport}
        className="p-6 bg-green-50 border border-green-200 rounded-lg hover:bg-green-100 transition-colors"
      >
        <svg className="w-12 h-12 text-green-600 mx-auto mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M18.364 5.636l-3.536 3.536m0 5.656l3.536 3.536M9.172 9.172L5.636 5.636m3.536 9.192L5.636 18.364M12 2.25a9.75 9.75 0 100 19.5 9.75 9.75 0 000-19.5z" />
        </svg>
        <h3 className="font-semibold text-green-900 mb-1">Review Security Settings</h3>
        <p className="text-green-700 text-sm">Update your 2FA preferences and device settings</p>
      </button>
    </div>

    <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
      <h3 className="font-semibold text-blue-900 mb-2">Next Steps:</h3>
      <ul className="text-blue-800 space-y-1 text-sm">
        <li>• Generate new backup codes for future use</li>
        <li>• Review and update your security settings</li>
        <li>• Consider re-enabling two-factor authentication</li>
        <li>• Update your contact information if needed</li>
      </ul>
    </div>
  </div>
);

const GenerateNewCodesStep: React.FC<{
  onGenerate: () => Promise<void>;
  isLoading: boolean;
  canGenerate: boolean;
  lastGenerated: string;
}> = ({ onGenerate, isLoading, canGenerate, lastGenerated }) => (
  <div className="space-y-6">
    <div className="text-center">
      <h2 className="text-2xl font-bold text-gray-900 mb-2">Generate New Backup Codes</h2>
      <p className="text-gray-600">
        Create new backup codes to replace the ones you've used during recovery
      </p>
    </div>

    {!canGenerate && (
      <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 text-center">
        <svg className="w-12 h-12 text-yellow-400 mx-auto mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-7.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.34 16.5c-.77.833.192 2.5 1.732 2.5z" />
        </svg>
        <h3 className="font-semibold text-yellow-900 mb-2">Generation Temporarily Unavailable</h3>
        <p className="text-yellow-800 text-sm">
          New backup codes can be generated after {new Date(lastGenerated).toLocaleDateString()}. 
          This is a security measure to prevent abuse.
        </p>
      </div>
    )}

    {canGenerate && (
      <div className="text-center">
        <button
          onClick={onGenerate}
          disabled={isLoading}
          className="px-8 py-4 bg-orange-600 text-white rounded-lg hover:bg-orange-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors text-lg font-medium"
        >
          {isLoading ? 'Generating...' : 'Generate New Backup Codes'}
        </button>
        
        <p className="text-gray-500 text-sm mt-3">
          Last generated: {new Date(lastGenerated).toLocaleString()}
        </p>
      </div>
    )}

    <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
      <h3 className="font-semibold text-blue-900 mb-2">About New Backup Codes:</h3>
      <ul className="text-blue-800 space-y-1 text-sm">
        <li>• New codes will replace all existing backup codes</li>
        <li>• Old codes will be invalidated immediately</li>
        <li>• Store new codes securely in a safe location</li>
        <li>• Consider printing or downloading them</li>
      </ul>
    </div>
  </div>
);

const RecoveryCompleteStep: React.FC<{
  newCodes: string[];
  showNewCodes: boolean;
}> = ({ newCodes, showNewCodes }) => (
  <div className="text-center space-y-6">
    <div className="w-24 h-24 mx-auto bg-green-100 rounded-full flex items-center justify-center">
      <svg className="w-12 h-12 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
      </svg>
    </div>
    
    <div>
      <h2 className="text-2xl font-bold text-gray-900 mb-2">Recovery Complete!</h2>
      <p className="text-gray-600 leading-relaxed">
        Congratulations! Your account has been successfully recovered and you now have new backup codes. 
        Your account is secure and ready to use.
      </p>
    </div>

    {showNewCodes && newCodes.length > 0 && (
      <div className="bg-green-50 border border-green-200 rounded-lg p-4">
        <h3 className="font-semibold text-green-900 mb-3">Your New Backup Codes:</h3>
        <BackupCodeDisplay
          codes={newCodes}
          onCopy={(code) => navigator.clipboard.writeText(code)}
          onDownload={() => {
            const blob = new Blob([newCodes.join('\n')], { type: 'text/plain' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'mingus-new-backup-codes.txt';
            a.click();
            URL.revokeObjectURL(url);
          }}
          onPrint={() => window.print()}
          showRegenerate={false}
        />
      </div>
    )}

    <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
      <h3 className="font-semibold text-blue-900 mb-2">What to do next:</h3>
      <ul className="text-blue-800 space-y-1 text-sm">
        <li>• Save your new backup codes in a secure location</li>
        <li>• Consider re-enabling two-factor authentication</li>
        <li>• Review your account security settings</li>
        <li>• Update your contact information if needed</li>
      </ul>
    </div>

    <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
      <h3 className="font-semibold text-yellow-900 mb-2">Security Reminder:</h3>
      <p className="text-yellow-800 text-sm">
        Keep your backup codes safe and don't share them with anyone. 
        They provide access to your account and should be treated like a password.
      </p>
    </div>
  </div>
);

// Modal Components
const ContactSupportModal: React.FC<{
  onClose: () => void;
  onContactSupport: () => void;
}> = ({ onClose, onContactSupport }) => (
  <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
    <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
      <div className="text-center">
        <div className="w-16 h-16 mx-auto bg-blue-100 rounded-full flex items-center justify-center mb-4">
          <svg className="w-8 h-8 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M18.364 5.636l-3.536 3.536m0 5.656l3.536 3.536M9.172 9.172L5.636 5.636m3.536 9.192L5.636 18.364M12 2.25a9.75 9.75 0 100 19.5 9.75 9.75 0 000-19.5z" />
          </svg>
        </div>
        
        <h3 className="text-lg font-semibold text-gray-900 mb-2">
          Need Additional Help?
        </h3>
        <p className="text-gray-600 mb-6">
          Our support team is here to help you with account recovery. 
          They can assist with additional verification or alternative recovery methods.
        </p>
        
        <div className="flex space-x-3">
          <button
            onClick={onClose}
            className="flex-1 px-4 py-2 text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={() => {
              onContactSupport();
              onClose();
            }}
            className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            Contact Support
          </button>
        </div>
      </div>
    </div>
  </div>
);

// Placeholder components (these would be implemented separately)
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

const ProgressIndicator: React.FC<ProgressIndicatorProps> = ({ current, total, steps, showLabels }) => (
  <div className="bg-gray-50 px-6 py-4">
    <div className="flex items-center justify-between">
      {steps.map((step, index) => (
        <div key={index} className="flex items-center">
          <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${
            index < current 
              ? 'bg-orange-600 text-white' 
              : index === current 
                ? 'bg-orange-200 text-orange-800' 
                : 'bg-gray-200 text-gray-500'
          }`}>
            {index < current ? '✓' : index + 1}
          </div>
          {showLabels && (
            <span className={`ml-2 text-sm ${
              index < current ? 'text-orange-600 font-medium' : 'text-gray-500'
            }`}>
              {step}
            </span>
          )}
          {index < steps.length - 1 && (
            <div className={`w-16 h-0.5 mx-4 ${
              index < current ? 'bg-orange-600' : 'bg-gray-200'
            }`} />
          )}
        </div>
      ))}
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

const ErrorDisplay: React.FC<ErrorDisplayProps> = ({ error, onRetry, onDismiss }) => (
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
          {onRetry && (
            <button
              onClick={onRetry}
              className="text-red-800 hover:text-red-600 transition-colors mr-2 text-sm"
            >
              Retry
            </button>
          )}
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

const SuccessDisplay: React.FC<SuccessDisplayProps> = ({ message, onContinue, onDismiss, showAnimation }) => (
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
          {onContinue && (
            <button
              onClick={onContinue}
              className="text-green-800 hover:text-green-600 transition-colors mr-2 text-sm"
            >
              Continue
            </button>
          )}
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

export default TwoFactorRecovery;
