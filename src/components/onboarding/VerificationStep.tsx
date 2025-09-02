import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { VerificationCodeInput } from '../common/VerificationCodeInput';
import { PhoneNumberInput } from '../common/PhoneNumberInput';

interface VerificationStepProps {
  userId?: string;
}

const VerificationStep: React.FC<VerificationStepProps> = ({ userId }) => {
  const [phoneNumber, setPhoneNumber] = useState('');
  const [verificationCode, setVerificationCode] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);
  const [step, setStep] = useState<'phone' | 'verification'>('phone');
  const [resendCountdown, setResendCountdown] = useState(0);
  const navigate = useNavigate();

  // Handle countdown for resend button
  useEffect(() => {
    if (resendCountdown > 0) {
      const timer = setTimeout(() => setResendCountdown(resendCountdown - 1), 1000);
      return () => clearTimeout(timer);
    }
  }, [resendCountdown]);

  const handlePhoneSubmit = async () => {
    if (!phoneNumber) {
      setError('Please enter your phone number');
      return;
    }

    setIsLoading(true);
    setError('');

    try {
      const response = await fetch('/api/onboarding/send-verification', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
          phoneNumber,
          userId 
        }),
      });

      if (response.ok) {
        setStep('verification');
        setResendCountdown(60); // 60 second countdown
      } else {
        const errorData = await response.json();
        setError(errorData.error || 'Failed to send verification code');
      }
    } catch (error) {
      setError('Network error. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleVerificationComplete = async (code: string) => {
    setIsLoading(true);
    setError('');

    try {
      const response = await fetch('/api/onboarding/verify-phone', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
          phoneNumber,
          code,
          userId 
        }),
      });

      if (response.ok) {
        setSuccess(true);
        // Navigate to next step after a brief delay
        setTimeout(() => {
          navigate('/onboarding/preferences');
        }, 1500);
      } else {
        const errorData = await response.json();
        setError(errorData.error || 'Invalid verification code');
      }
    } catch (error) {
      setError('Network error. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleResendCode = async () => {
    if (resendCountdown > 0) return;

    setIsLoading(true);
    setError('');

    try {
      const response = await fetch('/api/onboarding/resend-verification', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
          phoneNumber,
          userId 
        }),
      });

      if (response.ok) {
        setResendCountdown(60);
        setError('');
      } else {
        const errorData = await response.json();
        setError(errorData.error || 'Failed to resend code');
      }
    } catch (error) {
      setError('Network error. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleSkip = () => {
    navigate('/onboarding/preferences');
  };

  return (
    <div className="min-h-screen bg-[var(--bg-primary)] flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        {/* Progress Header */}
        <div className="bg-[var(--bg-secondary)] border border-[var(--border-color)] rounded-lg p-6 mb-6">
          <div className="flex items-center justify-between mb-4">
            <h1 className="text-xl font-semibold text-[var(--text-primary)]" className="text-4xl font-bold text-gray-900 mb-6">Verify Your Phone</h1>
            <span className="text-base leading-relaxed text-[var(--text-muted)]">Step 3 of 7</span>
          </div>
          <div className="w-full bg-[var(--border-color)] rounded-full h-2">
            <div className="bg-[var(--accent-green)] h-2 rounded-full" style={{ width: '43%' }}></div>
          </div>
        </div>

        <div className="bg-[var(--bg-secondary)] border border-[var(--border-color)] rounded-lg p-6">
          {error && (
            <div className="mb-4 p-3 bg-red-900/20 border border-red-500/30 rounded-lg">
              <p className="text-red-400 text-base leading-relaxed">{error}</p>
            </div>
          )}

          {success && (
            <div className="mb-4 p-3 bg-green-900/20 border border-green-500/30 rounded-lg">
              <p className="text-green-400 text-base leading-relaxed">Phone verified successfully! Redirecting...</p>
            </div>
          )}

          {step === 'phone' ? (
            <div className="space-y-6">
              <div className="text-center">
                <div className="text-4xl mb-4">📱</div>
                <h2 className="text-lg font-semibold text-[var(--text-primary)] mb-2" className="text-2xl font-semibold text-gray-800 mb-4">
                  Verify Your Phone Number
                </h2>
                <p className="text-[var(--text-secondary)] text-base leading-relaxed">
                  We'll send you a verification code to secure your account
                </p>
              </div>

              <PhoneNumberInput
                value={phoneNumber}
                onChange={setPhoneNumber}
                label="Phone Number"
                placeholder="Enter your phone number"
                required
                error={error}
                disabled={isLoading}
              />

              <div className="space-y-3">
                <button
                  onClick={handlePhoneSubmit}
                  disabled={isLoading || !phoneNumber}
                  className="w-full px-6 py-3 bg-[var(--accent-green)] text-white rounded-lg font-medium hover:bg-[var(--accent-green)]/90 disabled:opacity-50 disabled:cursor-not-allowed transition-colors duration-200 flex items-center justify-center"
                >
                  {isLoading ? (
                    <>
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                      Sending Code...
                    </>
                  ) : (
                    'Send Verification Code'
                  )}
                </button>

                <button
                  onClick={handleSkip}
                  className="w-full px-6 py-3 text-[var(--text-secondary)] border border-[var(--border-color)] rounded-lg hover:bg-[var(--bg-primary)] transition-colors"
                >
                  Skip for now
                </button>
              </div>
            </div>
          ) : (
            <div className="space-y-6">
              <div className="text-center">
                <div className="text-4xl mb-4">🔐</div>
                <h2 className="text-lg font-semibold text-[var(--text-primary)] mb-2" className="text-2xl font-semibold text-gray-800 mb-4">
                  Enter Verification Code
                </h2>
                <p className="text-[var(--text-secondary)] text-base leading-relaxed">
                  We sent a 6-digit code to {phoneNumber}
                </p>
              </div>

              <VerificationCodeInput
                length={6}
                onComplete={handleVerificationComplete}
                loading={isLoading}
                error={error}
                success={success}
                disabled={isLoading}
                autoFocus={true}
                className="mb-4"
              />

              <div className="space-y-3">
                <button
                  onClick={handleResendCode}
                  disabled={resendCountdown > 0 || isLoading}
                  className="w-full px-6 py-3 text-[var(--text-secondary)] border border-[var(--border-color)] rounded-lg hover:bg-[var(--bg-primary)] disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  {resendCountdown > 0 
                    ? `Resend code in ${resendCountdown}s` 
                    : 'Resend Code'
                  }
                </button>

                <button
                  onClick={() => setStep('phone')}
                  className="w-full px-6 py-3 text-[var(--text-secondary)] border border-[var(--border-color)] rounded-lg hover:bg-[var(--bg-primary)] transition-colors"
                >
                  Change Phone Number
                </button>

                <button
                  onClick={handleSkip}
                  className="w-full px-6 py-3 text-[var(--text-secondary)] border border-[var(--border-color)] rounded-lg hover:bg-[var(--bg-primary)] transition-colors"
                >
                  Skip for now
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Help Text */}
        <div className="mt-4 text-center">
          <p className="text-[var(--text-muted)] text-base leading-relaxed">
            Your phone number helps us keep your account secure and send important updates
          </p>
        </div>
      </div>
    </div>
  );
};

export default VerificationStep; 