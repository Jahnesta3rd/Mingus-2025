import React, { useState, useRef, useEffect, forwardRef } from 'react';
import PhoneInput from 'react-phone-number-input';
import 'react-phone-number-input/style.css';

export interface PhoneNumberInputProps {
  value?: string;
  onChange?: (value: string) => void;
  onBlur?: () => void;
  onFocus?: () => void;
  placeholder?: string;
  label?: string;
  error?: string;
  disabled?: boolean;
  loading?: boolean;
  required?: boolean;
  className?: string;
  id?: string;
  name?: string;
  'aria-describedby'?: string;
  'aria-invalid'?: boolean;
  'aria-required'?: boolean;
}

export const PhoneNumberInput = forwardRef<HTMLDivElement, PhoneNumberInputProps>(
  (
    {
      value,
      onChange,
      onBlur,
      onFocus,
      placeholder = 'Enter phone number',
      label,
      error,
      disabled = false,
      loading = false,
      required = false,
      className = '',
      id,
      name,
      'aria-describedby': ariaDescribedby,
      'aria-invalid': ariaInvalid,
      'aria-required': ariaRequired,
    },
    ref
  ) => {
    const [isFocused, setIsFocused] = useState(false);
    const [isValid, setIsValid] = useState<boolean | null>(null);
    const [validationMessage, setValidationMessage] = useState('');
    const inputRef = useRef<HTMLInputElement>(null);
    const errorId = id ? `${id}-error` : 'phone-error';
    const descriptionId = id ? `${id}-description` : 'phone-description';

    // Validation function
    const validatePhoneNumber = (phoneValue: string | undefined) => {
      if (!phoneValue) {
        if (required) {
          setIsValid(false);
          setValidationMessage('Phone number is required');
          return false;
        }
        setIsValid(null);
        setValidationMessage('');
        return true;
      }

      // Basic validation for US phone numbers
      const cleanNumber = phoneValue.replace(/\D/g, '');
      
      if (cleanNumber.length < 10) {
        setIsValid(false);
        setValidationMessage('Phone number must be at least 10 digits');
        return false;
      }

      if (cleanNumber.length > 15) {
        setIsValid(false);
        setValidationMessage('Phone number is too long');
        return false;
      }

      // Check if it's a valid US number format
      const usNumberPattern = /^1?[2-9]\d{2}[2-9]\d{6}$/;
      if (!usNumberPattern.test(cleanNumber)) {
        setIsValid(false);
        setValidationMessage('Please enter a valid US phone number');
        return false;
      }

      setIsValid(true);
      setValidationMessage('');
      return true;
    };

    // Handle value changes
    const handleChange = (newValue: string | undefined) => {
      const isValidNumber = validatePhoneNumber(newValue);
      onChange?.(newValue || '');
      
      // Trigger validation on change
      if (newValue !== value) {
        validatePhoneNumber(newValue);
      }
    };

    // Handle focus events
    const handleFocus = () => {
      setIsFocused(true);
      onFocus?.();
    };

    // Handle blur events
    const handleBlur = () => {
      setIsFocused(false);
      validatePhoneNumber(value);
      onBlur?.();
    };

    // Handle key navigation
    const handleKeyDown = (event: React.KeyboardEvent) => {
      if (event.key === 'Enter') {
        event.preventDefault();
        inputRef.current?.blur();
      }
    };

    // Focus management for accessibility
    useEffect(() => {
      if (error && inputRef.current) {
        inputRef.current.setAttribute('aria-invalid', 'true');
      }
    }, [error]);

    // Determine input state classes
    const getInputStateClasses = () => {
      let baseClasses = 'w-full px-3 py-2.5 bg-gray-800 border rounded-lg text-white placeholder-gray-400 transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent';
      
      if (disabled || loading) {
        baseClasses += ' opacity-50 cursor-not-allowed bg-gray-700';
      } else if (error || (isValid === false)) {
        baseClasses += ' border-red-500 focus:ring-red-500';
      } else if (isValid === true) {
        baseClasses += ' border-green-500';
      } else if (isFocused) {
        baseClasses += ' border-gray-400';
      } else {
        baseClasses += ' border-gray-600';
      }

      return baseClasses;
    };

    // Determine container state classes
    const getContainerStateClasses = () => {
      let baseClasses = 'relative';
      
      if (disabled || loading) {
        baseClasses += ' opacity-50';
      }

      return baseClasses;
    };

    return (
      <div 
        ref={ref}
        className={`${getContainerStateClasses()} ${className}`}
        data-testid="phone-number-input"
      >
        {/* Label */}
        {label && (
          <label 
            htmlFor={id}
            className="block text-base font-medium text-gray-200 mb-2"
          >
            {label}
            {required && <span className="text-red-500 ml-1">*</span>}
          </label>
        )}

        {/* Input Container */}
        <div className="relative">
          {/* Loading Spinner */}
          {loading && (
            <div className="absolute right-3 top-1/2 transform -translate-y-1/2 z-10">
              <div className="animate-spin rounded-full h-4 w-4 border-2 border-gray-400 border-t-green-500"></div>
            </div>
          )}

          {/* Phone Input */}
          <PhoneInput
            international
            defaultCountry="US"
            value={value}
            onChange={handleChange}
            onFocus={handleFocus}
            onBlur={handleBlur}
            onKeyDown={handleKeyDown}
            disabled={disabled || loading}
            placeholder={placeholder}
            id={id}
            name={name}
            className={getInputStateClasses()}
            aria-describedby={`${errorId} ${descriptionId}`}
            aria-invalid={ariaInvalid || error || isValid === false}
            aria-required={ariaRequired || required}
            ref={inputRef}
            style={{
              backgroundColor: 'transparent',
              border: 'none',
              outline: 'none',
              boxShadow: 'none',
            }}
          />

          {/* Validation Icon */}
          {!loading && !disabled && (
            <div className="absolute right-3 top-1/2 transform -translate-y-1/2 pointer-events-none">
              {isValid === true && (
                <svg 
                  className="w-4 h-4 text-green-500" 
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
              )}
              {isValid === false && (
                <svg 
                  className="w-4 h-4 text-red-500" 
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
              )}
            </div>
          )}
        </div>

        {/* Error Message */}
        {(error || (isValid === false && validationMessage)) && (
          <div 
            id={errorId}
            className="mt-2 text-base text-red-500 flex items-center"
            role="alert"
            aria-live="polite"
          >
            <svg 
              className="w-4 h-4 mr-1 flex-shrink-0" 
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
            {error || validationMessage}
          </div>
        )}

        {/* Helper Text */}
        <div 
          id={descriptionId}
          className="mt-1 text-base text-gray-400"
        >
          Enter your phone number in any format. We'll automatically format it for you.
        </div>

        {/* Screen Reader Only - Status Announcement */}
        <div className="sr-only" aria-live="polite">
          {loading && 'Loading phone number input'}
          {disabled && 'Phone number input is disabled'}
          {isValid === true && 'Phone number is valid'}
          {isValid === false && `Phone number error: ${error || validationMessage}`}
        </div>
      </div>
    );
  }
);

PhoneNumberInput.displayName = 'PhoneNumberInput';

// Custom CSS for react-phone-number-input to match Mingus theme
const phoneInputStyles = `
  .PhoneInput {
    position: relative;
  }

  .PhoneInputCountry {
    position: absolute;
    top: 0;
    bottom: 0;
    left: 0;
    z-index: 1;
    display: flex;
    align-items: center;
    padding: 0 0.75rem;
    background-color: transparent;
  }

  .PhoneInputCountrySelect {
    position: absolute;
    top: 0;
    left: 0;
    height: 100%;
    width: 100%;
    z-index: 1;
    border: 0;
    opacity: 0;
    cursor: pointer;
    background-color: transparent;
  }

  .PhoneInputCountryIcon {
    width: 1.5rem;
    height: 1.125rem;
    border-radius: 0.125rem;
  }

  .PhoneInputCountrySelectArrow {
    display: block;
    content: '';
    width: 0.3125rem;
    height: 0.3125rem;
    margin-left: 0.5rem;
    border-style: solid;
    border-color: #9CA3AF;
    border-top-width: 0.125rem;
    border-right-width: 0.125rem;
    border-bottom-width: 0;
    border-left-width: 0;
    transform: rotate(135deg);
  }

  .PhoneInputInput {
    width: 100%;
    padding: 0.625rem 0.75rem 0.625rem 3.5rem;
    background-color: transparent;
    border: none;
    outline: none;
    color: #FFFFFF;
    font-size: 1rem;
    line-height: 1.5;
  }

  .PhoneInputInput::placeholder {
    color: #9CA3AF;
  }

  .PhoneInputInput:focus {
    outline: none;
  }

  /* Dark theme overrides */
  .PhoneInputInput {
    background-color: #1F2937;
    border: 1px solid #374151;
    border-radius: 0.5rem;
    transition: all 0.2s ease;
  }

  .PhoneInputInput:focus {
    border-color: #10B981;
    box-shadow: 0 0 0 2px rgba(16, 185, 129, 0.2);
  }

  .PhoneInputInput.error {
    border-color: #EF4444;
  }

  .PhoneInputInput.success {
    border-color: #10B981;
  }

  .PhoneInputInput:disabled {
    opacity: 0.5;
    cursor: not-allowed;
    background-color: #374151;
  }
`;

// Inject styles
if (typeof document !== 'undefined') {
  const styleElement = document.createElement('style');
  styleElement.textContent = phoneInputStyles;
  document.head.appendChild(styleElement);
} 