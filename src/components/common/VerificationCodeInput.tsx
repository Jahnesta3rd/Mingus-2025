import React, { useState, useRef, useEffect, useCallback } from 'react';

export interface VerificationCodeInputProps {
  length?: number;
  onComplete?: (code: string) => void;
  onCodeChange?: (code: string) => void;
  loading?: boolean;
  error?: string;
  success?: boolean;
  disabled?: boolean;
  autoFocus?: boolean;
  className?: string;
  id?: string;
  'aria-describedby'?: string;
  'aria-invalid'?: boolean;
}

export const VerificationCodeInput: React.FC<VerificationCodeInputProps> = ({
  length = 6,
  onComplete,
  onCodeChange,
  loading = false,
  error,
  success = false,
  disabled = false,
  autoFocus = true,
  className = '',
  id,
  'aria-describedby': ariaDescribedby,
  'aria-invalid': ariaInvalid,
}) => {
  const [code, setCode] = useState<string[]>(new Array(length).fill(''));
  const [focusedIndex, setFocusedIndex] = useState<number>(0);
  const inputRefs = useRef<(HTMLInputElement | null)[]>([]);
  const containerRef = useRef<HTMLDivElement>(null);
  const errorId = id ? `${id}-error` : 'verification-error';
  const descriptionId = id ? `${id}-description` : 'verification-description';

  // Initialize input refs array
  useEffect(() => {
    inputRefs.current = inputRefs.current.slice(0, length);
  }, [length]);

  // Auto-focus first input on mount
  useEffect(() => {
    if (autoFocus && !disabled && inputRefs.current[0]) {
      inputRefs.current[0]?.focus();
    }
  }, [autoFocus, disabled]);

  // Haptic feedback for mobile devices
  const triggerHapticFeedback = useCallback(() => {
    if ('vibrate' in navigator) {
      navigator.vibrate(50); // Short vibration
    }
  }, []);

  // Handle input change
  const handleInputChange = useCallback((index: number, value: string) => {
    if (disabled || loading) return;

    // Only allow digits
    const digit = value.replace(/\D/g, '').slice(0, 1);
    
    if (digit) {
      triggerHapticFeedback();
      
      const newCode = [...code];
      newCode[index] = digit;
      setCode(newCode);
      
      // Notify parent of code change
      const codeString = newCode.join('');
      onCodeChange?.(codeString);
      
      // Auto-advance to next field
      if (index < length - 1) {
        setFocusedIndex(index + 1);
        setTimeout(() => {
          inputRefs.current[index + 1]?.focus();
        }, 10);
      } else {
        // All fields filled, trigger completion
        if (codeString.length === length) {
          onComplete?.(codeString);
        }
      }
    }
  }, [code, length, disabled, loading, onCodeChange, onComplete, triggerHapticFeedback]);

  // Handle keydown events
  const handleKeyDown = useCallback((index: number, event: React.KeyboardEvent<HTMLInputElement>) => {
    if (disabled || loading) return;

    if (event.key === 'Backspace') {
      event.preventDefault();
      
      if (code[index]) {
        // Clear current field
        const newCode = [...code];
        newCode[index] = '';
        setCode(newCode);
        onCodeChange?.(newCode.join(''));
      } else if (index > 0) {
        // Move to previous field and clear it
        const newCode = [...code];
        newCode[index - 1] = '';
        setCode(newCode);
        setFocusedIndex(index - 1);
        onCodeChange?.(newCode.join(''));
        setTimeout(() => {
          inputRefs.current[index - 1]?.focus();
        }, 10);
      }
    } else if (event.key === 'ArrowLeft' && index > 0) {
      event.preventDefault();
      setFocusedIndex(index - 1);
      inputRefs.current[index - 1]?.focus();
    } else if (event.key === 'ArrowRight' && index < length - 1) {
      event.preventDefault();
      setFocusedIndex(index + 1);
      inputRefs.current[index + 1]?.focus();
    } else if (event.key === 'Enter') {
      event.preventDefault();
      const codeString = code.join('');
      if (codeString.length === length) {
        onComplete?.(codeString);
      }
    }
  }, [code, length, disabled, loading, onCodeChange, onComplete]);

  // Handle paste functionality
  const handlePaste = useCallback((event: React.ClipboardEvent) => {
    if (disabled || loading) return;

    event.preventDefault();
    const pastedData = event.clipboardData.getData('text');
    const digits = pastedData.replace(/\D/g, '').slice(0, length);
    
    if (digits.length > 0) {
      triggerHapticFeedback();
      
      const newCode = [...code];
      digits.split('').forEach((digit, index) => {
        if (index < length) {
          newCode[index] = digit;
        }
      });
      
      setCode(newCode);
      const codeString = newCode.join('');
      onCodeChange?.(codeString);
      
      // Focus last filled field or first empty field
      const lastFilledIndex = Math.min(digits.length - 1, length - 1);
      setFocusedIndex(lastFilledIndex);
      setTimeout(() => {
        inputRefs.current[lastFilledIndex]?.focus();
      }, 10);
      
      // Auto-submit if all fields are filled
      if (codeString.length === length) {
        onComplete?.(codeString);
      }
    }
  }, [code, length, disabled, loading, onCodeChange, onComplete, triggerHapticFeedback]);

  // Handle focus events
  const handleFocus = useCallback((index: number) => {
    if (!disabled && !loading) {
      setFocusedIndex(index);
      // Select all text when focusing
      setTimeout(() => {
        inputRefs.current[index]?.select();
      }, 10);
    }
  }, [disabled, loading]);

  // Handle click events for better mobile experience
  const handleClick = useCallback((index: number) => {
    if (!disabled && !loading) {
      setFocusedIndex(index);
      inputRefs.current[index]?.focus();
    }
  }, [disabled, loading]);

  // Reset code when error occurs
  useEffect(() => {
    if (error) {
      setCode(new Array(length).fill(''));
      setFocusedIndex(0);
      setTimeout(() => {
        inputRefs.current[0]?.focus();
      }, 100);
    }
  }, [error, length]);

  // Determine input state classes
  const getInputStateClasses = (index: number) => {
    let baseClasses = 'w-12 h-12 text-center text-lg font-semibold bg-[var(--bg-secondary)] border-2 rounded-lg transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-[var(--accent-green)] focus:border-transparent text-[var(--text-primary)] placeholder-[var(--text-muted)]';
    
    if (disabled || loading) {
      baseClasses += ' opacity-50 cursor-not-allowed bg-[var(--bg-secondary)] border-[var(--border-color)]';
    } else if (error) {
      baseClasses += ' border-[var(--accent-danger)] focus:ring-[var(--accent-danger)]';
    } else if (success) {
      baseClasses += ' border-[var(--accent-green)] focus:ring-[var(--accent-green)]';
    } else if (focusedIndex === index) {
      baseClasses += ' border-[var(--accent-green)]';
    } else if (code[index]) {
      baseClasses += ' border-[var(--border-color)]';
    } else {
      baseClasses += ' border-[var(--border-color)]';
    }

    return baseClasses;
  };

  // Determine container state classes
  const getContainerStateClasses = () => {
    let baseClasses = 'flex items-center justify-center space-x-2 relative';
    
    if (disabled || loading) {
      baseClasses += ' opacity-50';
    }

    return baseClasses;
  };

  return (
    <div 
      ref={containerRef}
      className={`${getContainerStateClasses()} ${className}`}
      data-testid="verification-code-input"
    >
      {/* Hidden input for paste functionality */}
      <input
        type="text"
        className="sr-only"
        onPaste={handlePaste}
        tabIndex={-1}
        aria-hidden="true"
      />

      {/* Individual digit inputs */}
      {code.map((digit, index) => (
        <input
          key={index}
          ref={(el) => (inputRefs.current[index] = el)}
          type="text"
          inputMode="numeric"
          pattern="[0-9]*"
          maxLength={1}
          value={digit}
          onChange={(e) => handleInputChange(index, e.target.value)}
          onKeyDown={(e) => handleKeyDown(index, e)}
          onFocus={() => handleFocus(index)}
          onClick={() => handleClick(index)}
          disabled={disabled || loading}
          className={getInputStateClasses(index)}
          id={id ? `${id}-${index}` : `verification-${index}`}
          aria-describedby={`${errorId} ${descriptionId}`}
          aria-invalid={ariaInvalid || !!error}
          aria-label={`Verification code digit ${index + 1}`}
          data-index={index}
        />
      ))}

      {/* Loading indicator */}
      {loading && (
        <div className="absolute right-0 top-0 transform translate-x-full ml-4">
          <div className="animate-spin rounded-full h-6 w-6 border-2 border-gray-400 border-t-green-500"></div>
        </div>
      )}

      {/* Success indicator */}
      {success && !loading && (
        <div className="absolute right-0 top-0 transform translate-x-full ml-4">
          <svg 
            className="w-6 h-6 text-green-500" 
            fill="currentColor" 
            viewBox="0 0 20 20"
            aria-hidden="true"
          >
            <path 
              fillRule="evenodd" 
              d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" 
              clipRule="evenodd" 
            />
          </svg>
        </div>
      )}

      {/* Error indicator */}
      {error && !loading && (
        <div className="absolute right-0 top-0 transform translate-x-full ml-4">
          <svg 
            className="w-6 h-6 text-red-500" 
            fill="currentColor" 
            viewBox="0 0 20 20"
            aria-hidden="true"
          >
            <path 
              fillRule="evenodd" 
              d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" 
              clipRule="evenodd" 
            />
          </svg>
        </div>
      )}

      {/* Error Message */}
      {error && (
        <div 
          id={errorId}
          className="absolute top-full left-0 right-0 mt-2 text-base leading-relaxed text-red-500 text-center"
          role="alert"
          aria-live="polite"
        >
          {error}
        </div>
      )}

      {/* Helper Text */}
      <div 
        id={descriptionId}
        className="absolute top-full left-0 right-0 mt-8 text-base leading-relaxed text-gray-400 text-center"
      >
        Enter the {length}-digit verification code sent to your device
      </div>

      {/* Screen Reader Only - Status Announcement */}
      <div className="sr-only" aria-live="polite">
        {loading && 'Verifying code'}
        {success && 'Verification successful'}
        {error && `Verification error: ${error}`}
        {code.join('').length === length && 'All digits entered'}
      </div>
    </div>
  );
}; 