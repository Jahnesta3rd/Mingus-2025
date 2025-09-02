import React, { useState, useEffect, useCallback } from 'react';
import { PhoneNumberInput } from '../PhoneNumberInput';
import { VerificationCodeInput } from '../VerificationCodeInput';

interface SmartResendVerificationProps {
  onVerificationSuccess: (phoneNumber: string) => void;
  onBack: () => void;
  initialPhoneNumber?: string;
}

interface VerificationStatus {
  has_active_verification: boolean;
  can_send_code: boolean;
  cooldown_remaining: number;
  resend_count: number;
  max_resends: number;
  attempts_used: number;
  max_attempts: number;
  code_expires_at: string;
  attempt_history: Array<{
    id: string;
    sent_at: string;
    attempts: number;
    status: string;
    resend_count: number;
    created_at: string;
  }>;
  suggest_alternative: boolean;
  can_change_phone: boolean;
}

interface AnalyticsData {
  event_type: string;
  event_data: any;
  created_at: string;
}

export const SmartResendVerification: React.FC<SmartResendVerificationProps> = ({
  onVerificationSuccess,
  onBack,
  initialPhoneNumber = ''
}) => {
  const [phoneNumber, setPhoneNumber] = useState(initialPhoneNumber);
  const [verificationCode, setVerificationCode] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [countdown, setCountdown] = useState(0);
  const [verificationStatus, setVerificationStatus] = useState<VerificationStatus | null>(null);
  const [showChangePhone, setShowChangePhone] = useState(false);
  const [newPhoneNumber, setNewPhoneNumber] = useState('');
  const [analytics, setAnalytics] = useState<AnalyticsData[]>([]);

  // Progressive delay configuration
  const resendDelays = [60, 120, 300]; // 1min, 2min, 5min

  // Countdown timer effect
  useEffect(() => {
    let interval: NodeJS.Timeout;
    
    if (countdown > 0) {
      interval = setInterval(() => {
        setCountdown(prev => {
          if (prev <= 1) {
            return 0;
          }
          return prev - 1;
        });
      }, 1000);
    }

    return () => {
      if (interval) clearInterval(interval);
    };
  }, [countdown]);

  // Load verification status on mount
  useEffect(() => {
    if (phoneNumber) {
      loadVerificationStatus();
      loadAnalytics();
    }
  }, [phoneNumber]);

  const loadVerificationStatus = useCallback(async () => {
    try {
      const response = await fetch(`/api/onboarding/verification-status?phone_number=${encodeURIComponent(phoneNumber)}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        const status = await response.json();
        setVerificationStatus(status);
        
        // Set countdown if there's an active cooldown
        if (status.cooldown_remaining > 0) {
          setCountdown(status.cooldown_remaining);
        }
      }
    } catch (error) {
      console.error('Error loading verification status:', error);
    }
  }, [phoneNumber]);

  const loadAnalytics = useCallback(async () => {
    try {
      const response = await fetch('/api/onboarding/verification-analytics', {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        const data = await response.json();
        setAnalytics(data.analytics || []);
      }
    } catch (error) {
      console.error('Error loading analytics:', error);
    }
  }, []);

  const sendVerificationCode = async () => {
    if (!phoneNumber) {
      setError('Please enter a phone number');
      return;
    }

    setIsLoading(true);
    setError('');
    setSuccess('');

    try {
      const response = await fetch('/api/onboarding/send-verification', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ phone_number: phoneNumber }),
      });

      const data = await response.json();

      if (data.success) {
        setSuccess(data.message);
        setCountdown(data.next_resend_delay || 60);
        loadVerificationStatus();
        loadAnalytics();
      } else {
        setError(data.error);
        
        // Handle cooldown
        if (data.cooldown_remaining) {
          setCountdown(data.cooldown_remaining);
        }
      }
    } catch (error) {
      setError('Failed to send verification code. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const resendVerificationCode = async () => {
    if (countdown > 0) return;

    setIsLoading(true);
    setError('');
    setSuccess('');

    try {
      const response = await fetch('/api/onboarding/resend-verification', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ phone_number: phoneNumber }),
      });

      const data = await response.json();

      if (data.success) {
        setSuccess(data.message);
        setCountdown(data.next_resend_delay || 60);
        loadVerificationStatus();
        loadAnalytics();
      } else {
        setError(data.error);
        
        // Handle cooldown
        if (data.cooldown_remaining) {
          setCountdown(data.cooldown_remaining);
        }
      }
    } catch (error) {
      setError('Failed to resend verification code. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const verifyCode = async () => {
    if (!verificationCode || verificationCode.length !== 6) {
      setError('Please enter a valid 6-digit verification code');
      return;
    }

    setIsLoading(true);
    setError('');
    setSuccess('');

    try {
      const response = await fetch('/api/onboarding/verify-phone', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          phone_number: phoneNumber,
          verification_code: verificationCode,
        }),
      });

      const data = await response.json();

      if (data.success) {
        setSuccess(data.message);
        onVerificationSuccess(phoneNumber);
      } else {
        setError(data.error);
        setVerificationCode('');
      }
    } catch (error) {
      setError('Failed to verify code. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const changePhoneNumber = async () => {
    if (!newPhoneNumber) {
      setError('Please enter a new phone number');
      return;
    }

    setIsLoading(true);
    setError('');
    setSuccess('');

    try {
      const response = await fetch('/api/onboarding/change-phone', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          old_phone_number: phoneNumber,
          new_phone_number: newPhoneNumber,
        }),
      });

      const data = await response.json();

      if (data.success) {
        setPhoneNumber(newPhoneNumber);
        setNewPhoneNumber('');
        setShowChangePhone(false);
        setSuccess(data.message);
        setVerificationCode('');
        setCountdown(0);
        loadVerificationStatus();
        loadAnalytics();
      } else {
        setError(data.error);
      }
    } catch (error) {
      setError('Failed to change phone number. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const formatTime = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const getResendButtonText = (): string => {
    if (countdown > 0) {
      return `Resend in ${formatTime(countdown)}`;
    }
    
    if (verificationStatus?.resend_count === 0) {
      return 'Send Code';
    }
    
    const resendCount = verificationStatus?.resend_count || 0;
    const maxResends = verificationStatus?.max_resends || 3;
    
    if (resendCount >= maxResends) {
      return 'Max Resends Reached';
    }
    
    return `Resend Code (${resendCount}/${maxResends})`;
  };

  const isResendDisabled = (): boolean => {
    return countdown > 0 || 
           isLoading || 
           (verificationStatus?.resend_count || 0) >= (verificationStatus?.max_resends || 3);
  };

  return (
    <div className="smart-resend-verification">
      <div className="verification-header">
        <button 
          onClick={onBack}
          className="back-button font-semibold text-lg"
          disabled={isLoading}
        >
          ← Back
        </button>
        <h2 className="text-2xl font-semibold text-gray-800 mb-4">Verify Your Phone Number</h2>
        <p className="verification-subtitle">
          We'll send a verification code to your phone number
        </p>
      </div>

      <div className="verification-content">
        {/* Phone Number Input */}
        <div className="phone-input-section">
          <label htmlFor="phone-number">Phone Number</label>
          <PhoneNumberInput
            id="phone-number"
            value={phoneNumber}
            onChange={setPhoneNumber}
            disabled={isLoading}
            placeholder="Enter your phone number"
          />
          
          {verificationStatus?.can_change_phone && (
            <button
              onClick={() => setShowChangePhone(!showChangePhone)}
              className="change-phone-button font-semibold text-lg"
              disabled={isLoading}
            >
              Change Phone Number
            </button>
          )}
        </div>

        {/* Change Phone Number Modal */}
        {showChangePhone && (
          <div className="change-phone-modal">
            <div className="modal-content">
              <h3 className="text-xl font-semibold text-gray-800 mb-3">Change Phone Number</h3>
              <PhoneNumberInput
                value={newPhoneNumber}
                onChange={setNewPhoneNumber}
                disabled={isLoading}
                placeholder="Enter new phone number"
              />
              <div className="modal-actions">
                <button
                  onClick={changePhoneNumber}
                  disabled={isLoading || !newPhoneNumber}
                  className="primary-button font-semibold text-lg"
                >
                  {isLoading ? 'Changing...' : 'Change Phone'}
                </button>
                <button
                  onClick={() => setShowChangePhone(false)}
                  disabled={isLoading}
                  className="secondary-button font-semibold text-lg"
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Send/Resend Button */}
        <div className="send-code-section">
          <button
            onClick={verificationStatus?.resend_count === 0 ? sendVerificationCode : resendVerificationCode}
            disabled={isResendDisabled()}
            className={`send-code-button ${isResendDisabled() ? 'disabled' : ''}`}
          >
            {isLoading ? 'Sending...' : getResendButtonText()}
          </button>
          
          {countdown > 0 && (
            <div className="countdown-timer">
              <div className="countdown-circle">
                <span>{formatTime(countdown)}</span>
              </div>
            </div>
          )}
        </div>

        {/* Status Messages */}
        {success && (
          <div className="success-message">
            {success}
          </div>
        )}

        {error && (
          <div className="error-message">
            {error}
          </div>
        )}

        {/* Alternative Contact Suggestion */}
        {verificationStatus?.suggest_alternative && (
          <div className="alternative-contact">
            <p>Having trouble receiving SMS?</p>
            <ul>
              <li>Check your phone's signal strength</li>
              <li>Verify the phone number is correct</li>
              <li>Try email verification instead</li>
              <li>Contact support for assistance</li>
            </ul>
          </div>
        )}

        {/* Verification Code Input */}
        {verificationStatus?.has_active_verification && (
          <div className="code-input-section">
            <label htmlFor="verification-code">Enter Verification Code</label>
            <VerificationCodeInput
              id="verification-code"
              value={verificationCode}
              onChange={setVerificationCode}
              onComplete={verifyCode}
              disabled={isLoading}
              length={6}
            />
            
            <button
              onClick={verifyCode}
              disabled={isLoading || verificationCode.length !== 6}
              className="verify-button font-semibold text-lg"
            >
              {isLoading ? 'Verifying...' : 'Verify Code'}
            </button>
          </div>
        )}

        {/* Attempt History */}
        {verificationStatus?.attempt_history && verificationStatus.attempt_history.length > 0 && (
          <div className="attempt-history">
            <h4>Recent Attempts</h4>
            <div className="history-list">
              {verificationStatus.attempt_history.slice(0, 5).map((attempt) => (
                <div key={attempt.id} className="history-item">
                  <span className="attempt-time">
                    {new Date(attempt.sent_at).toLocaleTimeString()}
                  </span>
                  <span className={`attempt-status ${attempt.status}`}>
                    {attempt.status}
                  </span>
                  <span className="attempt-count">
                    {attempt.attempts} attempts
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Analytics Summary */}
        {analytics.length > 0 && (
          <div className="analytics-summary">
            <h4>Verification Activity</h4>
            <div className="analytics-stats">
              <div className="stat">
                <span className="stat-label">Total Events:</span>
                <span className="stat-value">{analytics.length}</span>
              </div>
              <div className="stat">
                <span className="stat-label">Last Activity:</span>
                <span className="stat-value">
                  {new Date(analytics[0]?.created_at).toLocaleString()}
                </span>
              </div>
            </div>
          </div>
        )}
      </div>

      <style jsx>{`
        .smart-resend-verification {
          max-width: 500px;
          margin: 0 auto;
          padding: 2rem;
          background: var(--mingus-bg-secondary);
          border-radius: 12px;
          box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
        }

        .verification-header {
          text-align: center;
          margin-bottom: 2rem;
        }

        .verification-header h2 {
          color: var(--mingus-text-primary);
          margin: 1rem 0 0.5rem 0;
          font-size: 1.5rem;
          font-weight: 600;
        }

        .verification-subtitle {
          color: var(--mingus-text-secondary);
          font-size: 0.9rem;
          margin: 0;
        }

        .back-button {
          position: absolute;
          top: 1rem;
          left: 1rem;
          background: none;
          border: none;
          color: var(--mingus-accent);
          cursor: pointer;
          font-size: 0.9rem;
          padding: 0.5rem;
          border-radius: 6px;
          transition: background-color 0.2s;
        }

        .back-button:hover:not(:disabled) {
          background: var(--mingus-bg-hover);
        }

        .back-button:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }

        .verification-content {
          display: flex;
          flex-direction: column;
          gap: 1.5rem;
        }

        .phone-input-section {
          display: flex;
          flex-direction: column;
          gap: 0.5rem;
        }

        .phone-input-section label {
          color: var(--mingus-text-primary);
          font-weight: 500;
          font-size: 0.9rem;
        }

        .change-phone-button {
          background: none;
          border: 1px solid var(--mingus-accent);
          color: var(--mingus-accent);
          padding: 0.5rem 1rem;
          border-radius: 6px;
          cursor: pointer;
          font-size: 0.8rem;
          transition: all 0.2s;
          align-self: flex-start;
        }

        .change-phone-button:hover:not(:disabled) {
          background: var(--mingus-accent);
          color: white;
        }

        .change-phone-modal {
          position: fixed;
          top: 0;
          left: 0;
          right: 0;
          bottom: 0;
          background: rgba(0, 0, 0, 0.5);
          display: flex;
          align-items: center;
          justify-content: center;
          z-index: 1000;
        }

        .modal-content {
          background: var(--mingus-bg-secondary);
          padding: 2rem;
          border-radius: 12px;
          min-width: 300px;
          display: flex;
          flex-direction: column;
          gap: 1rem;
        }

        .modal-content h3 {
          color: var(--mingus-text-primary);
          margin: 0 0 1rem 0;
        }

        .modal-actions {
          display: flex;
          gap: 1rem;
          margin-top: 1rem;
        }

        .send-code-section {
          display: flex;
          align-items: center;
          gap: 1rem;
          justify-content: center;
        }

        .send-code-button {
          background: var(--mingus-accent);
          color: white;
          border: none;
          padding: 0.75rem 1.5rem;
          border-radius: 8px;
          cursor: pointer;
          font-weight: 500;
          transition: all 0.2s;
          min-width: 150px;
        }

        .send-code-button:hover:not(:disabled) {
          background: var(--mingus-accent-hover);
          transform: translateY(-1px);
        }

        .send-code-button.disabled {
          background: var(--mingus-bg-tertiary);
          color: var(--mingus-text-secondary);
          cursor: not-allowed;
          transform: none;
        }

        .countdown-timer {
          display: flex;
          align-items: center;
          justify-content: center;
        }

        .countdown-circle {
          width: 50px;
          height: 50px;
          border: 2px solid var(--mingus-accent);
          border-radius: 50%;
          display: flex;
          align-items: center;
          justify-content: center;
          font-weight: 600;
          color: var(--mingus-accent);
          font-size: 0.8rem;
        }

        .success-message {
          background: var(--mingus-success-bg);
          color: var(--mingus-success-text);
          padding: 0.75rem;
          border-radius: 6px;
          font-size: 0.9rem;
        }

        .error-message {
          background: var(--mingus-error-bg);
          color: var(--mingus-error-text);
          padding: 0.75rem;
          border-radius: 6px;
          font-size: 0.9rem;
        }

        .alternative-contact {
          background: var(--mingus-warning-bg);
          color: var(--mingus-warning-text);
          padding: 1rem;
          border-radius: 6px;
          font-size: 0.9rem;
        }

        .alternative-contact p {
          margin: 0 0 0.5rem 0;
          font-weight: 500;
        }

        .alternative-contact ul {
          margin: 0;
          padding-left: 1.5rem;
        }

        .alternative-contact li {
          margin: 0.25rem 0;
        }

        .code-input-section {
          display: flex;
          flex-direction: column;
          gap: 1rem;
        }

        .code-input-section label {
          color: var(--mingus-text-primary);
          font-weight: 500;
          font-size: 0.9rem;
        }

        .verify-button {
          background: var(--mingus-success);
          color: white;
          border: none;
          padding: 0.75rem 1.5rem;
          border-radius: 8px;
          cursor: pointer;
          font-weight: 500;
          transition: all 0.2s;
        }

        .verify-button:hover:not(:disabled) {
          background: var(--mingus-success-hover);
          transform: translateY(-1px);
        }

        .verify-button:disabled {
          background: var(--mingus-bg-tertiary);
          color: var(--mingus-text-secondary);
          cursor: not-allowed;
          transform: none;
        }

        .attempt-history {
          background: var(--mingus-bg-tertiary);
          padding: 1rem;
          border-radius: 8px;
        }

        .attempt-history h4 {
          color: var(--mingus-text-primary);
          margin: 0 0 1rem 0;
          font-size: 0.9rem;
        }

        .history-list {
          display: flex;
          flex-direction: column;
          gap: 0.5rem;
        }

        .history-item {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 0.5rem;
          background: var(--mingus-bg-secondary);
          border-radius: 4px;
          font-size: 0.8rem;
        }

        .attempt-time {
          color: var(--mingus-text-secondary);
        }

        .attempt-status {
          padding: 0.25rem 0.5rem;
          border-radius: 4px;
          font-size: 0.7rem;
          font-weight: 500;
        }

        .attempt-status.pending {
          background: var(--mingus-warning-bg);
          color: var(--mingus-warning-text);
        }

        .attempt-status.verified {
          background: var(--mingus-success-bg);
          color: var(--mingus-success-text);
        }

        .attempt-status.expired {
          background: var(--mingus-error-bg);
          color: var(--mingus-error-text);
        }

        .attempt-count {
          color: var(--mingus-text-secondary);
        }

        .analytics-summary {
          background: var(--mingus-bg-tertiary);
          padding: 1rem;
          border-radius: 8px;
        }

        .analytics-summary h4 {
          color: var(--mingus-text-primary);
          margin: 0 0 1rem 0;
          font-size: 0.9rem;
        }

        .analytics-stats {
          display: flex;
          flex-direction: column;
          gap: 0.5rem;
        }

        .stat {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 0.5rem;
          background: var(--mingus-bg-secondary);
          border-radius: 4px;
          font-size: 0.8rem;
        }

        .stat-label {
          color: var(--mingus-text-secondary);
        }

        .stat-value {
          color: var(--mingus-text-primary);
          font-weight: 500;
        }

        .primary-button {
          background: var(--mingus-accent);
          color: white;
          border: none;
          padding: 0.75rem 1.5rem;
          border-radius: 8px;
          cursor: pointer;
          font-weight: 500;
          transition: all 0.2s;
        }

        .primary-button:hover:not(:disabled) {
          background: var(--mingus-accent-hover);
        }

        .secondary-button {
          background: var(--mingus-bg-tertiary);
          color: var(--mingus-text-primary);
          border: 1px solid var(--mingus-border);
          padding: 0.75rem 1.5rem;
          border-radius: 8px;
          cursor: pointer;
          font-weight: 500;
          transition: all 0.2s;
        }

        .secondary-button:hover:not(:disabled) {
          background: var(--mingus-bg-hover);
        }
      `}</style>
    </div>
  );
}; 