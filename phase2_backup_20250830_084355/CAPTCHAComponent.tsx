import React, { useEffect, useRef, useState } from 'react';

interface CAPTCHAComponentProps {
  siteKey: string;
  onVerify: (token: string) => void;
  onError: (error: string) => void;
  theme?: 'light' | 'dark';
  size?: 'normal' | 'compact';
  disabled?: boolean;
}

declare global {
  interface Window {
    grecaptcha: {
      ready: (callback: () => void) => void;
      render: (container: string | HTMLElement, options: any) => number;
      reset: (widgetId: number) => void;
      getResponse: (widgetId: number) => string;
    };
  }
}

export const CAPTCHAComponent: React.FC<CAPTCHAComponentProps> = ({
  siteKey,
  onVerify,
  onError,
  theme = 'dark',
  size = 'normal',
  disabled = false
}) => {
  const [widgetId, setWidgetId] = useState<number | null>(null);
  const [isLoaded, setIsLoaded] = useState(false);
  const [isVerified, setIsVerified] = useState(false);
  const captchaRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Load reCAPTCHA script if not already loaded
    if (!window.grecaptcha) {
      const script = document.createElement('script');
      script.src = `https://www.google.com/recaptcha/api.js?render=explicit`;
      script.async = true;
      script.defer = true;
      script.onload = () => setIsLoaded(true);
      script.onerror = () => onError('Failed to load CAPTCHA');
      document.head.appendChild(script);
    } else {
      setIsLoaded(true);
    }

    return () => {
      // Cleanup
      if (widgetId !== null && window.grecaptcha) {
        try {
          window.grecaptcha.reset(widgetId);
        } catch (e) {
          // Widget might already be destroyed
        }
      }
    };
  }, []);

  useEffect(() => {
    if (isLoaded && captchaRef.current && !widgetId && !disabled) {
      window.grecaptcha.ready(() => {
        try {
          const id = window.grecaptcha.render(captchaRef.current!, {
            sitekey: siteKey,
            theme: theme,
            size: size,
            callback: (token: string) => {
              setIsVerified(true);
              onVerify(token);
            },
            'expired-callback': () => {
              setIsVerified(false);
              onError('CAPTCHA expired. Please try again.');
            },
            'error-callback': () => {
              setIsVerified(false);
              onError('CAPTCHA verification failed. Please try again.');
            }
          });
          setWidgetId(id);
        } catch (error) {
          onError('Failed to initialize CAPTCHA');
        }
      });
    }
  }, [isLoaded, siteKey, theme, size, disabled, onVerify, onError]);

  const resetCAPTCHA = () => {
    if (widgetId !== null && window.grecaptcha) {
      window.grecaptcha.reset(widgetId);
      setIsVerified(false);
    }
  };

  if (disabled) {
    return null;
  }

  return (
    <div className="captcha-container">
      <div className="captcha-header">
        <h4>Security Verification</h4>
        <p>Please complete the CAPTCHA to continue</p>
      </div>
      
      <div 
        ref={captchaRef} 
        className="captcha-widget"
        style={{ 
          display: 'flex', 
          justifyContent: 'center',
          margin: '1rem 0'
        }}
      />
      
      {isVerified && (
        <div className="captcha-success">
          <span>✅ Verification completed</span>
        </div>
      )}
      
      <button 
        onClick={resetCAPTCHA}
        className="captcha-reset-button font-semibold text-lg"
        disabled={!isVerified}
      >
        Reset CAPTCHA
      </button>

      <style jsx>{`
        .captcha-container {
          background: var(--mingus-bg-secondary);
          border: 1px solid var(--mingus-border);
          border-radius: 8px;
          padding: 1.5rem;
          margin: 1rem 0;
        }

        .captcha-header {
          text-align: center;
          margin-bottom: 1rem;
        }

        .captcha-header h4 {
          color: var(--mingus-text-primary);
          margin: 0 0 0.5rem 0;
          font-size: 1.1rem;
        }

        .captcha-header p {
          color: var(--mingus-text-secondary);
          margin: 0;
          font-size: 0.9rem;
        }

        .captcha-widget {
          display: flex;
          justify-content: center;
          margin: 1rem 0;
        }

        .captcha-success {
          text-align: center;
          color: var(--mingus-success-text);
          font-weight: 500;
          margin: 1rem 0;
        }

        .captcha-reset-button {
          background: var(--mingus-bg-tertiary);
          color: var(--mingus-text-primary);
          border: 1px solid var(--mingus-border);
          padding: 0.5rem 1rem;
          border-radius: 6px;
          cursor: pointer;
          font-size: 0.9rem;
          transition: all 0.2s;
          width: 100%;
          margin-top: 1rem;
        }

        .captcha-reset-button:hover:not(:disabled) {
          background: var(--mingus-bg-hover);
        }

        .captcha-reset-button:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }
      `}</style>
    </div>
  );
}; 