// components/onboarding/OnboardingStep.tsx
import React, { useState, useEffect } from 'react';
import { OnboardingStep as OnboardingStepType } from '../../types/user';
import { FormField } from '../forms/FormField';
import { FormValidation } from '../forms/FormValidation';
import { FormActions } from '../forms/FormActions';

interface OnboardingStepProps {
  step: OnboardingStepType;
  data: Record<string, any>;
  onNext: (data: Record<string, any>) => void;
  onPrevious: () => void;
  onSkip?: () => void;
  isFirst: boolean;
  isLast: boolean;
  isLoading?: boolean;
  canProceed?: boolean;
  validation?: {
    isValid: boolean;
    errors: Array<{ field: string; message: string; code: string }>;
    warnings: Array<{ field: string; message: string; code: string }>;
  };
}

export const OnboardingStep: React.FC<OnboardingStepProps> = ({
  step,
  data,
  onNext,
  onPrevious,
  onSkip,
  isFirst,
  isLast,
  isLoading = false,
  canProceed = true,
  validation
}) => {
  const [formData, setFormData] = useState(data);
  const [localErrors, setLocalErrors] = useState<Record<string, string>>({});
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Update local form data when prop changes
  useEffect(() => {
    setFormData(data);
  }, [data]);

  // Convert validation errors to local format
  useEffect(() => {
    if (validation?.errors) {
      const errorMap: Record<string, string> = {};
      validation.errors.forEach(error => {
        errorMap[error.field] = error.message;
      });
      setLocalErrors(errorMap);
    }
  }, [validation]);

  const handleFieldChange = (name: string, value: any) => {
    setFormData(prev => ({ ...prev, [name]: value }));
    
    // Clear local error when user starts typing
    if (localErrors[name]) {
      setLocalErrors(prev => ({ ...prev, [name]: '' }));
    }
  };

  const validateForm = () => {
    const newErrors: Record<string, string> = {};

    step.fields.forEach(field => {
      const value = formData[field.name];
      
      // Check required fields
      if (field.required && (!value || value === '' || value === null || value === undefined)) {
        newErrors[field.name] = `${field.label} is required`;
        return;
      }

      // Skip validation if field is empty and not required
      if (!value || value === '' || value === null || value === undefined) {
        return;
      }

      // Validate based on field type and validation rules
      if (field.validation) {
        const { min, max, pattern, message } = field.validation;
        
        if (min !== undefined) {
          if (typeof value === 'number' && value < min) {
            newErrors[field.name] = message || `Minimum value is ${min}`;
          }
        }
        
        if (max !== undefined) {
          if (typeof value === 'number' && value > max) {
            newErrors[field.name] = message || `Maximum value is ${max}`;
          }
        }
        
        if (pattern && typeof value === 'string') {
          const regex = new RegExp(pattern);
          if (!regex.test(value)) {
            newErrors[field.name] = message || 'Invalid format';
          }
        }
      }

      // Type-specific validations
      switch (field.type) {
        case 'email':
          if (typeof value === 'string' && !isValidEmail(value)) {
            newErrors[field.name] = 'Please enter a valid email address';
          }
          break;

        case 'tel':
          if (typeof value === 'string' && !isValidPhoneNumber(value)) {
            newErrors[field.name] = 'Please enter a valid phone number';
          }
          break;

        case 'currency':
          if (typeof value === 'number' && value < 0) {
            newErrors[field.name] = 'Amount cannot be negative';
          }
          break;
      }
    });

    setLocalErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const isValidEmail = (email: string): boolean => {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
  };

  const isValidPhoneNumber = (phone: string): boolean => {
    const phoneRegex = /^\+?[1-9]\d{1,14}$/;
    return phoneRegex.test(phone.replace(/\D/g, ''));
  };

  const handleNext = async () => {
    if (validateForm()) {
      setIsSubmitting(true);
      try {
        await onNext(formData);
      } catch (error) {
        console.error('Error proceeding to next step:', error);
      } finally {
        setIsSubmitting(false);
      }
    }
  };

  const handlePrevious = () => {
    if (!isLoading && !isSubmitting) {
      onPrevious();
    }
  };

  const handleSkip = () => {
    if (onSkip && !isLoading && !isSubmitting) {
      onSkip();
    }
  };

  const canProceedToNext = canProceed && !isLoading && !isSubmitting && validateForm();

  return (
    <div className="max-w-4xl mx-auto">
      {/* Step Header */}
      <div className="mb-8 text-center">
        <div className="mb-4">
          <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-blue-100 text-blue-800">
            Step {step.step}
          </span>
        </div>
        
        <h2 className="text-3xl font-bold text-gray-900 mb-2">{step.title}</h2>
        
        {step.subtitle && (
          <p className="text-lg text-gray-600 max-w-2xl mx-auto">{step.subtitle}</p>
        )}
        
        {/* Category Badge */}
        <div className="mt-4">
          <span className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-medium ${
            step.category === 'critical' 
              ? 'bg-red-100 text-red-800' 
              : step.category === 'important'
              ? 'bg-yellow-100 text-yellow-800'
              : 'bg-green-100 text-green-800'
          }`}>
            {step.category === 'critical' && 'Required'}
            {step.category === 'important' && 'Recommended'}
            {step.category === 'enhanced' && 'Optional'}
          </span>
        </div>
      </div>

      {/* Form Content */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-8">
        <form className="space-y-6" onSubmit={(e) => { e.preventDefault(); handleNext(); }}>
          {/* Form Fields */}
          <div className="space-y-6">
            {step.fields.map((field) => (
              <FormField
                key={field.name}
                field={field}
                value={formData[field.name]}
                onChange={handleFieldChange}
                error={localErrors[field.name]}
                disabled={isLoading || isSubmitting}
              />
            ))}
          </div>

          {/* Validation Messages */}
          {((validation?.errors && validation.errors.length > 0) || (validation?.warnings && validation.warnings.length > 0)) && (
            <div className="mt-6">
              <FormValidation
                errors={validation?.errors || []}
                warnings={validation?.warnings || []}
              />
            </div>
          )}

          {/* Local Validation Errors */}
          {Object.keys(localErrors).length > 0 && (
            <div className="mt-6">
              <FormValidation
                errors={Object.entries(localErrors).map(([field, message]) => ({
                  field,
                  message,
                  code: 'VALIDATION_ERROR'
                }))}
              />
            </div>
          )}

          {/* Form Actions */}
          <div className="mt-8">
            <FormActions
              onNext={handleNext}
              onPrevious={handlePrevious}
              onSkip={onSkip ? handleSkip : undefined}
              isFirst={isFirst}
              isLast={isLast}
              isLoading={isLoading || isSubmitting}
              canProceed={canProceedToNext}
              showSkip={step.category !== 'critical' && !isLast}
              nextLabel={isLast ? 'Complete Setup' : 'Next'}
              previousLabel="Previous"
              skipLabel="Skip for now"
            />
          </div>
        </form>
      </div>

      {/* Step Information */}
      <div className="mt-6 text-center">
        <div className="text-sm text-gray-500">
          {step.isRequired ? (
            <p>This step is required to continue</p>
          ) : (
            <p>This step is optional - you can skip it for now</p>
          )}
        </div>
        
        {step.category === 'critical' && (
          <div className="mt-2 text-xs text-red-600">
            <p>Required fields are marked with an asterisk (*)</p>
          </div>
        )}
      </div>

      {/* Loading Overlay */}
      {(isLoading || isSubmitting) && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 flex items-center space-x-3">
            <svg className="animate-spin h-5 w-5 text-blue-600" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
            </svg>
            <span className="text-gray-700">
              {isSubmitting ? 'Saving...' : 'Loading...'}
            </span>
          </div>
        </div>
      )}
    </div>
  );
}; 