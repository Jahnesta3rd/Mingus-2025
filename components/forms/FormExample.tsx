// components/forms/FormExample.tsx
import React, { useState } from 'react';
import { FormField } from './FormField';
import { FormSection } from './FormSection';
import { FormProgress } from './FormProgress';
import { FormValidation } from './FormValidation';
import { FormActions } from './FormActions';
import { FormField as FormFieldType } from '../../types/user';

// Example form configuration
const EXAMPLE_FIELDS: FormFieldType[] = [
  {
    name: 'firstName',
    type: 'text',
    label: 'First Name',
    placeholder: 'Enter your first name',
    required: true,
    validation: {
      min: 2,
      max: 50,
      pattern: '^[a-zA-Z]+$',
      message: 'Please enter a valid first name (letters only)'
    }
  },
  {
    name: 'lastName',
    type: 'text',
    label: 'Last Name',
    placeholder: 'Enter your last name',
    required: true,
    validation: {
      min: 2,
      max: 50,
      pattern: '^[a-zA-Z]+$',
      message: 'Please enter a valid last name (letters only)'
    }
  },
  {
    name: 'email',
    type: 'email',
    label: 'Email Address',
    placeholder: 'your@email.com',
    required: true,
    validation: {
      pattern: '^[^\\s@]+@[^\\s@]+\\.[^\\s@]+$',
      message: 'Please enter a valid email address'
    }
  },
  {
    name: 'phoneNumber',
    type: 'tel',
    label: 'Phone Number',
    placeholder: '(555) 123-4567',
    required: false,
    validation: {
      pattern: '^[+]?[1-9][\\d]{0,15}$',
      message: 'Please enter a valid phone number'
    }
  },
  {
    name: 'monthlyIncome',
    type: 'currency',
    label: 'Monthly Income',
    placeholder: '$5,000',
    required: true,
    validation: {
      min: 0,
      max: 999999,
      message: 'Please enter a valid income amount'
    }
  },
  {
    name: 'incomeFrequency',
    type: 'select',
    label: 'Income Frequency',
    required: true,
    options: [
      { value: 'weekly', label: 'Weekly' },
      { value: 'bi-weekly', label: 'Bi-weekly' },
      { value: 'semi-monthly', label: 'Semi-monthly' },
      { value: 'monthly', label: 'Monthly' },
      { value: 'annually', label: 'Annually' }
    ]
  },
  {
    name: 'riskTolerance',
    type: 'radio',
    label: 'Investment Risk Tolerance',
    required: true,
    options: [
      { value: 'conservative', label: 'Conservative - I prefer low-risk, stable investments' },
      { value: 'moderate', label: 'Moderate - I want a balance of growth and stability' },
      { value: 'aggressive', label: 'Aggressive - I seek maximum growth potential' }
    ]
  },
  {
    name: 'stressLevel',
    type: 'slider',
    label: 'Current Stress Level',
    subtitle: 'On a scale of 1-10, how would you rate your current stress level?',
    required: false,
    validation: {
      min: 1,
      max: 10
    }
  },
  {
    name: 'gdprConsent',
    type: 'checkbox',
    label: 'GDPR Consent',
    subtitle: 'I consent to the processing of my personal data for the purposes described in the privacy policy',
    required: true
  }
];

const STEP_TITLES = [
  'Personal Information',
  'Financial Details',
  'Preferences & Consent'
];

export const FormExample: React.FC = () => {
  const [currentStep, setCurrentStep] = useState(1);
  const [formData, setFormData] = useState<Record<string, any>>({});
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [isLoading, setIsLoading] = useState(false);

  const totalSteps = 3;
  const completedSteps = currentStep > 1 ? Array.from({ length: currentStep - 1 }, (_, i) => i + 1) : [];

  const handleFieldChange = (name: string, value: any) => {
    setFormData(prev => ({ ...prev, [name]: value }));
    
    // Clear error when user starts typing
    if (errors[name]) {
      setErrors(prev => ({ ...prev, [name]: '' }));
    }
  };

  const validateCurrentStep = () => {
    const stepFields = getCurrentStepFields();
    const newErrors: Record<string, string> = {};

    stepFields.forEach(field => {
      const value = formData[field.name];
      
      if (field.required && (!value || value === '' || value === null || value === undefined)) {
        newErrors[field.name] = `${field.label} is required`;
        return;
      }

      if (field.validation && value) {
        const { min, max, pattern, message } = field.validation;
        
        if (min !== undefined && value < min) {
          newErrors[field.name] = message || `Minimum value is ${min}`;
        }
        
        if (max !== undefined && value > max) {
          newErrors[field.name] = message || `Maximum value is ${max}`;
        }
        
        if (pattern && typeof value === 'string') {
          const regex = new RegExp(pattern);
          if (!regex.test(value)) {
            newErrors[field.name] = message || 'Invalid format';
          }
        }
      }
    });

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const getCurrentStepFields = () => {
    switch (currentStep) {
      case 1:
        return EXAMPLE_FIELDS.slice(0, 4); // Personal info
      case 2:
        return EXAMPLE_FIELDS.slice(4, 7); // Financial details
      case 3:
        return EXAMPLE_FIELDS.slice(7); // Preferences & consent
      default:
        return [];
    }
  };

  const handleNext = () => {
    if (validateCurrentStep()) {
      if (currentStep < totalSteps) {
        setCurrentStep(currentStep + 1);
      } else {
        handleSubmit();
      }
    }
  };

  const handlePrevious = () => {
    if (currentStep > 1) {
      setCurrentStep(currentStep - 1);
    }
  };

  const handleSkip = () => {
    if (currentStep < totalSteps) {
      setCurrentStep(currentStep + 1);
    }
  };

  const handleSubmit = async () => {
    setIsLoading(true);
    
    try {
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      console.log('Form submitted:', formData);
      alert('Form submitted successfully!');
      
      // Reset form
      setFormData({});
      setCurrentStep(1);
      setErrors({});
    } catch (error) {
      console.error('Form submission failed:', error);
      alert('Form submission failed. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const currentFields = getCurrentStepFields();
  const canProceed = currentFields.every(field => {
    if (!field.required) return true;
    const value = formData[field.name];
    return value && value !== '' && value !== null && value !== undefined;
  });

  return (
    <div className="min-h-screen bg-gray-50 py-12">
      <div className="max-w-4xl mx-auto px-6">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            Example Form
          </h1>
          <p className="text-lg text-gray-600">
            This is an example of how to use the form components
          </p>
        </div>

        {/* Progress */}
        <div className="mb-8">
          <FormProgress
            currentStep={currentStep}
            totalSteps={totalSteps}
            stepTitles={STEP_TITLES}
            completedSteps={completedSteps}
            onStepClick={(step) => {
              if (step <= currentStep + 1) {
                setCurrentStep(step);
              }
            }}
          />
        </div>

        {/* Form Content */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-8">
          <FormSection
            title={STEP_TITLES[currentStep - 1]}
            subtitle={`Step ${currentStep} of ${totalSteps}`}
            fields={currentFields}
            data={formData}
            onChange={handleFieldChange}
            errors={errors}
            disabled={isLoading}
          />

          {/* Validation Messages */}
          <div className="mt-6">
            <FormValidation
              errors={Object.entries(errors).map(([field, message]) => ({
                field,
                message,
                code: 'VALIDATION_ERROR'
              }))}
            />
          </div>

          {/* Form Actions */}
          <div className="mt-8">
            <FormActions
              onNext={handleNext}
              onPrevious={handlePrevious}
              onSkip={handleSkip}
              isFirst={currentStep === 1}
              isLast={currentStep === totalSteps}
              isLoading={isLoading}
              canProceed={canProceed}
              showSkip={currentStep < totalSteps}
              nextLabel={currentStep === totalSteps ? 'Submit' : 'Next'}
            />
          </div>
        </div>

        {/* Debug Info */}
        {process.env.NODE_ENV === 'development' && (
          <div className="mt-8 p-4 bg-gray-100 rounded-lg">
            <h3 className="font-medium text-gray-900 mb-2">Debug Information</h3>
            <pre className="text-sm text-gray-600 overflow-auto">
              {JSON.stringify({ currentStep, formData, errors }, null, 2)}
            </pre>
          </div>
        )}
      </div>
    </div>
  );
}; 