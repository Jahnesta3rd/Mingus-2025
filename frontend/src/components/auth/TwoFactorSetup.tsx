import React, { useState, useEffect, useRef } from 'react';
import { 
  TwoFactorSetup as TwoFactorSetupType,
  TwoFactorSetupStep,
  TwoFactorSetupFlow,
  QRCodeScannerProps,
  TOTPInputProps,
  BackupCodeDisplayProps,
  BiometricAuthProps,
  OfflineIndicatorProps,
  ProgressIndicatorProps,
  ErrorDisplayProps,
  SuccessDisplayProps
} from '@/types/twoFactor';

interface TwoFactorSetupProps {
  onComplete: (setup: TwoFactorSetupType) => void;
  onCancel: () => void;
  initialSetup?: Partial<TwoFactorSetupType>;
}

const TwoFactorSetup: React.FC<TwoFactorSetupProps> = ({
  onComplete,
  onCancel,
  initialSetup
}) => {
  const [currentStep, setCurrentStep] = useState(0);
  const [setup, setSetup] = useState<TwoFactorSetupType>({
    secret: '',
    qrCodeUrl: '',
    backupCodes: [],
    isEnabled: false,
    setupComplete: false,
    ...initialSetup
  });
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [verificationCode, setVerificationCode] = useState('');
  const [showManualEntry, setShowManualEntry] = useState(false);
  const [showQRScanner, setShowQRScanner] = useState(false);

  const steps: TwoFactorSetupStep[] = [
    {
      id: 'welcome',
      title: 'Welcome to Two-Factor Authentication',
      description: 'Let\'s set up an extra layer of security for your account',
      isComplete: false,
      isActive: currentStep === 0,
      component: WelcomeStep
    },
    {
      id: 'qr-setup',
      title: 'Scan QR Code',
      description: 'Use your authenticator app to scan this code',
      isComplete: false,
      isActive: currentStep === 1,
      component: QRSetupStep
    },
    {
      id: 'verification',
      title: 'Verify Setup',
      description: 'Enter the code from your authenticator app',
      isComplete: false,
      isActive: currentStep === 2,
      component: VerificationStep
    },
    {
      id: 'backup-codes',
      title: 'Backup Codes',
      description: 'Save these codes in case you lose access to your device',
      isComplete: false,
      isActive: currentStep === 3,
      component: BackupCodesStep
    },
    {
      id: 'completion',
      title: 'Setup Complete',
      description: 'Your two-factor authentication is now active',
      isComplete: false,
      isActive: currentStep === 4,
      component: CompletionStep
    }
  ];

  useEffect(() => {
    if (currentStep === 1) {
      generateQRCode();
    }
  }, [currentStep]);

  const generateQRCode = async () => {
    try {
      setIsLoading(true);
      setError(null);
      
      // Simulate API call to generate secret and QR code
      const response = await fetch('/api/2fa/setup', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });
      
      if (response.ok) {
        const data = await response.json();
        setSetup(prev => ({
          ...prev,
          secret: data.secret,
          qrCodeUrl: data.qrCodeUrl
        }));
      } else {
        throw new Error('Failed to generate QR code');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to generate QR code');
    } finally {
      setIsLoading(false);
    }
  };

  const generateBackupCodes = async () => {
    try {
      setIsLoading(true);
      setError(null);
      
      // Simulate API call to generate backup codes
      const response = await fetch('/api/2fa/backup-codes', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });
      
      if (response.ok) {
        const data = await response.json();
        setSetup(prev => ({
          ...prev,
          backupCodes: data.backupCodes
        }));
      } else {
        throw new Error('Failed to generate backup codes');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to generate backup codes');
    } finally {
      setIsLoading(false);
    }
  };

  const verifyCode = async (code: string) => {
    try {
      setIsLoading(true);
      setError(null);
      
      // Simulate API call to verify the code
      const response = await fetch('/api/2fa/verify', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ code, secret: setup.secret }),
      });
      
      if (response.ok) {
        const data = await response.json();
        if (data.verified) {
          setVerificationCode(code);
          return true;
        } else {
          setError('Invalid verification code. Please try again.');
          return false;
        }
      } else {
        throw new Error('Verification failed');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Verification failed');
      return false;
    } finally {
      setIsLoading(false);
    }
  };

  const handleNext = async () => {
    if (currentStep === 2) {
      // Verification step - verify the code first
      const isValid = await verifyCode(verificationCode);
      if (!isValid) return;
    }
    
    if (currentStep === 3) {
      // Generate backup codes if not already generated
      if (setup.backupCodes.length === 0) {
        await generateBackupCodes();
      }
    }
    
    if (currentStep === 4) {
      // Final step - complete setup
      const completedSetup = { ...setup, isEnabled: true, setupComplete: true };
      onComplete(completedSetup);
      return;
    }
    
    setCurrentStep(prev => prev + 1);
    setError(null);
  };

  const handlePrevious = () => {
    if (currentStep > 0) {
      setCurrentStep(prev => prev - 1);
      setError(null);
    }
  };

  const canProceed = () => {
    switch (currentStep) {
      case 0: return true; // Welcome step
      case 1: return setup.qrCodeUrl !== ''; // QR setup step
      case 2: return verificationCode.length === 6; // Verification step
      case 3: return setup.backupCodes.length > 0; // Backup codes step
      case 4: return true; // Completion step
      default: return false;
    }
  };

  const resetSetup = () => {
    setSetup({
      secret: '',
      qrCodeUrl: '',
      backupCodes: [],
      isEnabled: false,
      setupComplete: false
    });
    setVerificationCode('');
    setCurrentStep(0);
    setError(null);
  };

  if (isLoading && currentStep === 1) {
    return (
      <div className="flex items-center justify-center min-h-64">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Generating your QR code...</p>
        </div>
      </div>
    );
  }

  const CurrentStepComponent = steps[currentStep].component;

  return (
    <div className="max-w-2xl mx-auto bg-white rounded-lg shadow-lg overflow-hidden">
      {/* Header */}
      <div className="bg-gradient-to-r from-blue-600 to-purple-600 px-6 py-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-white">Two-Factor Authentication Setup</h1>
            <p className="text-blue-100 mt-1">Secure your account with an extra layer of protection</p>
          </div>
          <button
            onClick={onCancel}
            className="text-white hover:text-blue-100 transition-colors"
            aria-label="Cancel setup"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      </div>

      {/* Progress Indicator */}
      <ProgressIndicator
        current={currentStep + 1}
        total={steps.length}
        steps={steps.map(s => s.title)}
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

      {/* Current Step Content */}
      <div className="p-6">
        <CurrentStepComponent
          setup={setup}
          verificationCode={verificationCode}
          setVerificationCode={setVerificationCode}
          showManualEntry={showManualEntry}
          setShowManualEntry={setShowManualEntry}
          showQRScanner={showQRScanner}
          setShowQRScanner={setShowQRScanner}
          onVerifyCode={verifyCode}
          onGenerateBackupCodes={generateBackupCodes}
          isLoading={isLoading}
        />
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
            onClick={resetSetup}
            className="px-4 py-2 text-gray-600 hover:text-gray-800 transition-colors"
          >
            Start Over
          </button>
          
          <button
            onClick={handleNext}
            disabled={!canProceed() || isLoading}
            className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {currentStep === steps.length - 1 ? 'Complete Setup' : 'Next'}
          </button>
        </div>
      </div>
    </div>
  );
};

// Step Components
const WelcomeStep: React.FC<{
  setup: TwoFactorSetupType;
}> = ({ setup }) => (
  <div className="text-center space-y-6">
    <div className="w-24 h-24 mx-auto bg-blue-100 rounded-full flex items-center justify-center">
      <svg className="w-12 h-12 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
      </svg>
    </div>
    
    <div>
      <h2 className="text-2xl font-bold text-gray-900 mb-2">Welcome to Two-Factor Authentication</h2>
      <p className="text-gray-600 leading-relaxed">
        Two-factor authentication adds an extra layer of security to your account by requiring 
        a second form of verification in addition to your password. This helps protect your 
        financial information even if someone gets access to your password.
      </p>
    </div>

    <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 text-left">
      <h3 className="font-semibold text-blue-900 mb-2">What you'll need:</h3>
      <ul className="text-blue-800 space-y-1 text-sm">
        <li>• A smartphone with an authenticator app (Google Authenticator, Authy, etc.)</li>
        <li>• Access to your phone during setup</li>
        <li>• A few minutes to complete the process</li>
      </ul>
    </div>

    <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 text-left">
      <h3 className="font-semibold text-yellow-900 mb-2">Important:</h3>
      <p className="text-yellow-800 text-sm">
        Once enabled, you'll need your authenticator app to sign in to your account. 
        Make sure to save your backup codes in a safe place.
      </p>
    </div>
  </div>
);

const QRSetupStep: React.FC<{
  setup: TwoFactorSetupType;
  showManualEntry: boolean;
  setShowManualEntry: (show: boolean) => void;
  showQRScanner: boolean;
  setShowQRScanner: (show: boolean) => void;
}> = ({ setup, showManualEntry, setShowManualEntry, showQRScanner, setShowQRScanner }) => (
  <div className="space-y-6">
    <div className="text-center">
      <h2 className="text-2xl font-bold text-gray-900 mb-2">Set Up Your Authenticator App</h2>
      <p className="text-gray-600">
        Scan the QR code below with your authenticator app, or enter the code manually
      </p>
    </div>

    {!showManualEntry && !showQRScanner && (
      <div className="space-y-4">
        {/* QR Code Display */}
        <div className="flex justify-center">
          <div className="bg-white p-4 rounded-lg border-2 border-gray-200">
            {setup.qrCodeUrl ? (
              <img 
                src={setup.qrCodeUrl} 
                alt="QR Code for 2FA setup" 
                className="w-48 h-48"
              />
            ) : (
              <div className="w-48 h-48 bg-gray-100 rounded flex items-center justify-center">
                <div className="text-center text-gray-500">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-400 mx-auto mb-2"></div>
                  <p className="text-sm">Generating QR code...</p>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex justify-center space-x-4">
          <button
            onClick={() => setShowManualEntry(true)}
            className="px-4 py-2 text-blue-600 border border-blue-600 rounded-lg hover:bg-blue-50 transition-colors"
          >
            Enter Code Manually
          </button>
          
          <button
            onClick={() => setShowQRScanner(true)}
            className="px-4 py-2 text-green-600 border border-green-600 rounded-lg hover:bg-green-50 transition-colors"
          >
            Scan with Camera
          </button>
        </div>
      </div>
    )}

    {/* Manual Entry */}
    {showManualEntry && (
      <div className="space-y-4">
        <div className="text-center">
          <h3 className="text-lg font-semibold text-gray-900 mb-2">Manual Entry</h3>
          <p className="text-gray-600 text-sm">
            Enter this code manually in your authenticator app:
          </p>
        </div>
        
        <div className="bg-gray-50 p-4 rounded-lg">
          <div className="flex items-center justify-between">
            <code className="text-lg font-mono text-gray-800 bg-white px-3 py-2 rounded border">
              {setup.secret}
            </code>
            <button
              onClick={() => navigator.clipboard.writeText(setup.secret)}
              className="ml-3 px-3 py-2 text-blue-600 hover:text-blue-700 transition-colors"
              aria-label="Copy secret to clipboard"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
              </svg>
            </button>
          </div>
        </div>

        <div className="text-center">
          <button
            onClick={() => setShowManualEntry(false)}
            className="px-4 py-2 text-gray-600 hover:text-gray-800 transition-colors"
          >
            ← Back to QR Code
          </button>
        </div>
      </div>
    )}

    {/* QR Scanner */}
    {showQRScanner && (
      <div className="space-y-4">
        <div className="text-center">
          <h3 className="text-lg font-semibold text-gray-900 mb-2">Camera Scanner</h3>
          <p className="text-gray-600 text-sm">
            Point your camera at the QR code from another device
          </p>
        </div>
        
        <div className="bg-gray-50 p-4 rounded-lg text-center">
          <p className="text-gray-500">Camera scanner component would be implemented here</p>
        </div>

        <div className="text-center">
          <button
            onClick={() => setShowQRScanner(false)}
            className="px-4 py-2 text-gray-600 hover:text-gray-800 transition-colors"
          >
            ← Back to QR Code
          </button>
        </div>
      </div>
    )}

    {/* Instructions */}
    <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
      <h3 className="font-semibold text-blue-900 mb-2">Next Steps:</h3>
      <ol className="text-blue-800 text-sm space-y-1 list-decimal list-inside">
        <li>Open your authenticator app</li>
        <li>Scan the QR code or enter the manual code</li>
        <li>Add the account (usually named "Mingus" or your email)</li>
        <li>Click "Next" when you're ready to verify</li>
      </ol>
    </div>
  </div>
);

const VerificationStep: React.FC<{
  verificationCode: string;
  setVerificationCode: (code: string) => void;
  onVerifyCode: (code: string) => Promise<boolean>;
  isLoading: boolean;
}> = ({ verificationCode, setVerificationCode, onVerifyCode, isLoading }) => (
  <div className="space-y-6">
    <div className="text-center">
      <h2 className="text-2xl font-bold text-gray-900 mb-2">Verify Your Setup</h2>
      <p className="text-gray-600">
        Enter the 6-digit code from your authenticator app to complete the setup
      </p>
    </div>

    <div className="flex justify-center">
      <TOTPInput
        length={6}
        value={verificationCode}
        onChange={setVerificationCode}
        onComplete={onVerifyCode}
        autoFocus={true}
        disabled={isLoading}
      />
    </div>

    {isLoading && (
      <div className="text-center">
        <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600 mx-auto mb-2"></div>
        <p className="text-gray-600 text-sm">Verifying code...</p>
      </div>
    )}

    <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
      <h3 className="font-semibold text-yellow-900 mb-2">Can't see the code?</h3>
      <ul className="text-yellow-800 text-sm space-y-1">
        <li>• Make sure your authenticator app is open</li>
        <li>• Check that you added the correct account</li>
        <li>• Wait for the code to refresh (usually every 30 seconds)</li>
        <li>• Try refreshing the app if needed</li>
      </ul>
    </div>
  </div>
);

const BackupCodesStep: React.FC<{
  setup: TwoFactorSetupType;
  onGenerateBackupCodes: () => Promise<void>;
  isLoading: boolean;
}> = ({ setup, onGenerateBackupCodes, isLoading }) => (
  <div className="space-y-6">
    <div className="text-center">
      <h2 className="text-2xl font-bold text-gray-900 mb-2">Backup Codes</h2>
      <p className="text-gray-600">
        Save these backup codes in a safe place. You can use them to access your account 
        if you lose your authenticator device.
      </p>
    </div>

    {setup.backupCodes.length === 0 ? (
      <div className="text-center">
        <button
          onClick={onGenerateBackupCodes}
          disabled={isLoading}
          className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {isLoading ? 'Generating...' : 'Generate Backup Codes'}
        </button>
      </div>
    ) : (
      <BackupCodeDisplay
        codes={setup.backupCodes}
        onCopy={(code) => navigator.clipboard.writeText(code)}
        onDownload={() => {
          const blob = new Blob([setup.backupCodes.join('\n')], { type: 'text/plain' });
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
    )}

    <div className="bg-red-50 border border-red-200 rounded-lg p-4">
      <h3 className="font-semibold text-red-900 mb-2">Important Security Notes:</h3>
      <ul className="text-red-800 text-sm space-y-1">
        <li>• Store these codes securely - they provide access to your account</li>
        <li>• Don't share them with anyone</li>
        <li>• Consider printing them and storing in a safe location</li>
        <li>• You can regenerate new codes anytime in your settings</li>
      </ul>
    </div>
  </div>
);

const CompletionStep: React.FC<{
  setup: TwoFactorSetupType;
}> = ({ setup }) => (
  <div className="text-center space-y-6">
    <div className="w-24 h-24 mx-auto bg-green-100 rounded-full flex items-center justify-center">
      <svg className="w-12 h-12 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
      </svg>
    </div>
    
    <div>
      <h2 className="text-2xl font-bold text-gray-900 mb-2">Setup Complete!</h2>
      <p className="text-gray-600 leading-relaxed">
        Congratulations! Your two-factor authentication is now active. Your account is now 
        protected with an additional layer of security.
      </p>
    </div>

    <div className="bg-green-50 border border-green-200 rounded-lg p-4 text-left">
      <h3 className="font-semibold text-green-900 mb-2">What happens next:</h3>
      <ul className="text-green-800 space-y-1 text-sm">
        <li>• You'll be asked for a 2FA code every time you sign in</li>
        <li>• Use your authenticator app to generate codes</li>
        <li>• Keep your backup codes safe for emergency access</li>
        <li>• You can manage 2FA settings in your profile</li>
      </ul>
    </div>

    <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
      <h3 className="font-semibold text-blue-900 mb-2">Need help?</h3>
      <p className="text-blue-800 text-sm">
        If you have any issues with two-factor authentication, contact our support team 
        or refer to our help documentation.
      </p>
    </div>
  </div>
);

// Placeholder components (these would be implemented separately)
const TOTPInput: React.FC<TOTPInputProps> = ({ length, value, onChange, onComplete, autoFocus, disabled }) => (
  <div className="flex space-x-2">
    {Array.from({ length }, (_, i) => (
      <input
        key={i}
        type="text"
        maxLength={1}
        value={value[i] || ''}
        onChange={(e) => {
          const newValue = value.split('');
          newValue[i] = e.target.value;
          const result = newValue.join('');
          onChange(result);
          
          if (e.target.value && i < length - 1) {
            const nextInput = e.target.parentElement?.nextElementSibling?.querySelector('input');
            if (nextInput) nextInput.focus();
          }
          
          if (result.length === length) {
            onComplete(result);
          }
        }}
        onKeyDown={(e) => {
          if (e.key === 'Backspace' && !value[i] && i > 0) {
            const prevInput = e.target.parentElement?.previousElementSibling?.querySelector('input');
            if (prevInput) prevInput.focus();
          }
        }}
        className="w-12 h-12 text-center text-lg font-mono border-2 border-gray-300 rounded-lg focus:border-blue-500 focus:outline-none disabled:opacity-50"
        autoFocus={autoFocus && i === 0}
        disabled={disabled}
        inputMode="numeric"
        pattern="[0-9]*"
      />
    ))}
  </div>
);

const BackupCodeDisplay: React.FC<BackupCodeDisplayProps> = ({ codes, onCopy, onDownload, onPrint }) => (
  <div className="space-y-4">
    <div className="grid grid-cols-2 gap-3">
      {codes.map((code, index) => (
        <div key={index} className="bg-gray-50 p-3 rounded-lg border">
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
              ? 'bg-blue-600 text-white' 
              : index === current 
                ? 'bg-blue-200 text-blue-800' 
                : 'bg-gray-200 text-gray-500'
          }`}>
            {index < current ? '✓' : index + 1}
          </div>
          {showLabels && (
            <span className={`ml-2 text-sm ${
              index < current ? 'text-blue-600 font-medium' : 'text-gray-500'
            }`}>
              {step}
            </span>
          )}
          {index < steps.length - 1 && (
            <div className={`w-16 h-0.5 mx-4 ${
              index < current ? 'bg-blue-600' : 'bg-gray-200'
            }`} />
          )}
        </div>
      ))}
    </div>
  </div>
);

const ErrorDisplay: React.FC<ErrorDisplayProps> = ({ error, onRetry, onDismiss }) => (
  <div className="bg-red-50 border border-red-200 rounded-lg p-4 mx-6 mt-4">
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
              className="text-red-800 hover:text-red-600 transition-colors mr-2"
            >
              Retry
            </button>
          )}
          {onDismiss && (
            <button
              onClick={onDismiss}
              className="text-red-800 hover:text-red-600 transition-colors"
            >
              Dismiss
            </button>
          )}
        </div>
      </div>
    </div>
  </div>
);

export default TwoFactorSetup;
