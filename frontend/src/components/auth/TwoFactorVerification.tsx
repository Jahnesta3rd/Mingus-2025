import React, { useState, useEffect, useRef } from 'react';
import { 
  TwoFactorVerification as TwoFactorVerificationType,
  TOTPInputProps,
  BiometricAuthProps,
  OfflineIndicatorProps,
  ErrorDisplayProps,
  SuccessDisplayProps
} from '@/types/twoFactor';

interface TwoFactorVerificationProps {
  onVerify: (code: string, method: 'totp' | 'sms' | 'backup') => Promise<boolean>;
  onCancel: () => void;
  onResendCode?: () => Promise<void>;
  onUseBackupCode?: () => void;
  onUseBiometric?: () => Promise<boolean>;
  maxAttempts?: number;
  isOffline?: boolean;
  lastSync?: string;
  biometricAvailable?: boolean;
  biometricEnabled?: boolean;
}

const TwoFactorVerification: React.FC<TwoFactorVerificationProps> = ({
  onVerify,
  onCancel,
  onResendCode,
  onUseBackupCode,
  onUseBiometric,
  maxAttempts = 5,
  isOffline = false,
  lastSync = '',
  biometricAvailable = false,
  biometricEnabled = false
}) => {
  const [verificationCode, setVerificationCode] = useState('');
  const [method, setMethod] = useState<'totp' | 'sms' | 'backup'>('totp');
  const [attempts, setAttempts] = useState(0);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [showBackupInput, setShowBackupInput] = useState(false);
  const [backupCode, setBackupCode] = useState('');
  const [smsCode, setSmsCode] = useState('');
  const [countdown, setCountdown] = useState(0);
  const [canResend, setCanResend] = useState(true);

  const totpInputRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (countdown > 0) {
      const timer = setTimeout(() => setCountdown(countdown - 1), 1000);
      return () => clearTimeout(timer);
    } else {
      setCanResend(true);
    }
  }, [countdown]);

  useEffect(() => {
    if (method === 'totp' && totpInputRef.current) {
      const firstInput = totpInputRef.current.querySelector('input');
      if (firstInput) firstInput.focus();
    }
  }, [method]);

  const handleVerify = async (code: string, verificationMethod: 'totp' | 'sms' | 'backup' = method) => {
    if (attempts >= maxAttempts) {
      setError('Maximum verification attempts exceeded. Please try again later.');
      return false;
    }

    try {
      setIsLoading(true);
      setError(null);
      
      const isValid = await onVerify(code, verificationMethod);
      
      if (isValid) {
        setSuccess('Verification successful!');
        setAttempts(0);
        return true;
      } else {
        setAttempts(prev => prev + 1);
        setError(`Invalid ${verificationMethod === 'totp' ? 'TOTP' : verificationMethod === 'sms' ? 'SMS' : 'backup'} code. Please try again.`);
        
        if (attempts + 1 >= maxAttempts) {
          setError('Maximum verification attempts exceeded. Your account has been temporarily locked for security reasons.');
        }
        
        return false;
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Verification failed. Please try again.');
      return false;
    } finally {
      setIsLoading(false);
    }
  };

  const handleResendCode = async () => {
    if (!onResendCode || !canResend) return;
    
    try {
      setIsLoading(true);
      setError(null);
      
      await onResendCode();
      setCountdown(60); // 60 second cooldown
      setCanResend(false);
      setSuccess('Verification code sent successfully!');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to resend code. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleBiometricAuth = async () => {
    if (!onUseBiometric) return;
    
    try {
      setIsLoading(true);
      setError(null);
      
      const success = await onUseBiometric();
      if (success) {
        setSuccess('Biometric authentication successful!');
        return true;
      } else {
        setError('Biometric authentication failed. Please use a verification code instead.');
        return false;
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Biometric authentication failed.');
      return false;
    } finally {
      setIsLoading(false);
    }
  };

  const switchToMethod = (newMethod: 'totp' | 'sms' | 'backup') => {
    setMethod(newMethod);
    setError(null);
    setSuccess(null);
    setVerificationCode('');
    setSmsCode('');
    setBackupCode('');
    setShowBackupInput(false);
  };

  const renderMethodContent = () => {
    switch (method) {
      case 'totp':
        return (
          <div className="space-y-6">
            <div className="text-center">
              <h2 className="text-2xl font-bold text-gray-900 mb-2">Enter Verification Code</h2>
              <p className="text-gray-600">
                Enter the 6-digit code from your authenticator app
              </p>
            </div>

            <div className="flex justify-center" ref={totpInputRef}>
              <TOTPInput
                length={6}
                value={verificationCode}
                onChange={setVerificationCode}
                onComplete={(code) => handleVerify(code, 'totp')}
                autoFocus={true}
                disabled={isLoading}
                error={error}
              />
            </div>

            {attempts > 0 && (
              <div className="text-center text-sm text-gray-600">
                Attempts remaining: {maxAttempts - attempts}
              </div>
            )}
          </div>
        );

      case 'sms':
        return (
          <div className="space-y-6">
            <div className="text-center">
              <h2 className="text-2xl font-bold text-gray-900 mb-2">SMS Verification</h2>
              <p className="text-gray-600">
                Enter the 6-digit code sent to your phone
              </p>
            </div>

            <div className="flex justify-center">
              <TOTPInput
                length={6}
                value={smsCode}
                onChange={setSmsCode}
                onComplete={(code) => handleVerify(code, 'sms')}
                autoFocus={true}
                disabled={isLoading}
                error={error}
              />
            </div>

            <div className="text-center">
              <button
                onClick={handleResendCode}
                disabled={!canResend || isLoading}
                className="text-blue-600 hover:text-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {canResend ? 'Resend Code' : `Resend in ${countdown}s`}
              </button>
            </div>

            {attempts > 0 && (
              <div className="text-center text-sm text-gray-600">
                Attempts remaining: {maxAttempts - attempts}
              </div>
            )}
          </div>
        );

      case 'backup':
        return (
          <div className="space-y-6">
            <div className="text-center">
              <h2 className="text-2xl font-bold text-gray-900 mb-2">Backup Code</h2>
              <p className="text-gray-600">
                Enter one of your backup codes to access your account
              </p>
            </div>

            <div className="max-w-md mx-auto">
              <input
                type="text"
                value={backupCode}
                onChange={(e) => setBackupCode(e.target.value)}
                placeholder="Enter backup code"
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:border-blue-500 focus:outline-none text-center font-mono text-lg"
                disabled={isLoading}
                autoFocus={true}
              />
            </div>

            <div className="text-center">
              <button
                onClick={() => handleVerify(backupCode, 'backup')}
                disabled={!backupCode.trim() || isLoading}
                className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {isLoading ? 'Verifying...' : 'Verify Backup Code'}
              </button>
            </div>

            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
              <h3 className="font-semibold text-yellow-900 mb-2">Important:</h3>
              <p className="text-yellow-800 text-sm">
                Each backup code can only be used once. After using a backup code, 
                it will be invalidated and you'll need to generate new ones.
              </p>
            </div>
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <div className="max-w-md mx-auto bg-white rounded-lg shadow-lg overflow-hidden">
      {/* Header */}
      <div className="bg-gradient-to-r from-blue-600 to-purple-600 px-6 py-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-xl font-bold text-white">Two-Factor Authentication</h1>
            <p className="text-blue-100 text-sm mt-1">Verify your identity to continue</p>
          </div>
          <button
            onClick={onCancel}
            className="text-white hover:text-blue-100 transition-colors"
            aria-label="Cancel verification"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
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

      {/* Method Selection */}
      <div className="p-6">
        <div className="flex space-x-2 mb-6">
          <button
            onClick={() => switchToMethod('totp')}
            className={`flex-1 py-2 px-4 rounded-lg text-sm font-medium transition-colors ${
              method === 'totp'
                ? 'bg-blue-600 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            <svg className="w-4 h-4 inline mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            App
          </button>
          
          <button
            onClick={() => switchToMethod('sms')}
            className={`flex-1 py-2 px-4 rounded-lg text-sm font-medium transition-colors ${
              method === 'sms'
                ? 'bg-blue-600 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            <svg className="w-4 h-4 inline mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z" />
            </svg>
            SMS
          </button>
          
          <button
            onClick={() => switchToMethod('backup')}
            className={`flex-1 py-2 px-4 rounded-lg text-sm font-medium transition-colors ${
              method === 'backup'
                ? 'bg-blue-600 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            <svg className="w-4 h-4 inline mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            Backup
          </button>
        </div>

        {/* Method Content */}
        {renderMethodContent()}

        {/* Biometric Authentication */}
        {biometricAvailable && biometricEnabled && (
          <div className="mt-6 pt-6 border-t border-gray-200">
            <div className="text-center">
              <p className="text-gray-600 text-sm mb-3">Or use biometric authentication</p>
              <button
                onClick={handleBiometricAuth}
                disabled={isLoading}
                className="px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                <svg className="w-5 h-5 inline mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                </svg>
                Use Biometric
              </button>
            </div>
          </div>
        )}

        {/* Help Section */}
        <div className="mt-6 pt-6 border-t border-gray-200">
          <div className="text-center">
            <button
              onClick={onCancel}
              className="text-gray-600 hover:text-gray-800 transition-colors text-sm"
            >
              Need help? Contact Support
            </button>
          </div>
        </div>
      </div>

      {/* Loading Overlay */}
      {isLoading && (
        <div className="absolute inset-0 bg-white bg-opacity-75 flex items-center justify-center">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
            <p className="text-gray-600">Verifying...</p>
          </div>
        </div>
      )}
    </div>
  );
};

// Enhanced TOTP Input Component
const TOTPInput: React.FC<TOTPInputProps> = ({ 
  length, 
  value, 
  onChange, 
  onComplete, 
  autoFocus, 
  disabled, 
  error 
}) => {
  const inputRefs = useRef<(HTMLInputElement | null)[]>([]);

  useEffect(() => {
    if (autoFocus && inputRefs.current[0]) {
      inputRefs.current[0].focus();
    }
  }, [autoFocus]);

  const handleChange = (index: number, inputValue: string) => {
    if (inputValue.length > 1) return; // Prevent multiple characters
    
    const newValue = value.split('');
    newValue[index] = inputValue;
    const result = newValue.join('');
    onChange(result);
    
    // Auto-advance to next input
    if (inputValue && index < length - 1) {
      const nextInput = inputRefs.current[index + 1];
      if (nextInput) nextInput.focus();
    }
    
    // Check if complete
    if (result.length === length) {
      onComplete(result);
    }
  };

  const handleKeyDown = (index: number, e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Backspace' && !value[index] && index > 0) {
      const prevInput = inputRefs.current[index - 1];
      if (prevInput) prevInput.focus();
    }
  };

  const handlePaste = (e: React.ClipboardEvent) => {
    e.preventDefault();
    const pastedData = e.clipboardData.getData('text');
    const numbers = pastedData.replace(/\D/g, '').slice(0, length);
    
    if (numbers.length === length) {
      onChange(numbers);
      onComplete(numbers);
      // Focus last input
      const lastInput = inputRefs.current[length - 1];
      if (lastInput) lastInput.focus();
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex justify-center space-x-2">
        {Array.from({ length }, (_, i) => (
          <input
            key={i}
            ref={(el) => inputRefs.current[i] = el}
            type="text"
            maxLength={1}
            value={value[i] || ''}
            onChange={(e) => handleChange(i, e.target.value)}
            onKeyDown={(e) => handleKeyDown(i, e)}
            onPaste={handlePaste}
            className={`w-12 h-12 text-center text-lg font-mono border-2 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-opacity-50 disabled:opacity-50 transition-colors ${
              error 
                ? 'border-red-500 focus:border-red-500' 
                : 'border-gray-300 focus:border-blue-500'
            }`}
            autoFocus={autoFocus && i === 0}
            disabled={disabled}
            inputMode="numeric"
            pattern="[0-9]*"
            aria-label={`Digit ${i + 1} of ${length}`}
          />
        ))}
      </div>
      
      {error && (
        <div className="text-center text-sm text-red-600">
          {error}
        </div>
      )}
    </div>
  );
};

// Placeholder components (these would be implemented separately)
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

export default TwoFactorVerification;
