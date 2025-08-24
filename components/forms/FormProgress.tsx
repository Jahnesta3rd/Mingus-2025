// components/forms/FormProgress.tsx
import React from 'react';

interface FormProgressProps {
  currentStep: number;
  totalSteps: number;
  stepTitles: string[];
  completedSteps?: number[];
  onStepClick?: (step: number) => void;
  showStepNumbers?: boolean;
  showStepTitles?: boolean;
  className?: string;
}

export const FormProgress: React.FC<FormProgressProps> = ({
  currentStep,
  totalSteps,
  stepTitles,
  completedSteps = [],
  onStepClick,
  showStepNumbers = true,
  showStepTitles = true,
  className = ''
}) => {
  const progressPercentage = (currentStep / totalSteps) * 100;

  const getStepStatus = (step: number) => {
    if (completedSteps.includes(step)) return 'completed';
    if (step === currentStep) return 'current';
    if (step < currentStep) return 'completed';
    return 'upcoming';
  };

  const getStepIcon = (step: number, status: string) => {
    switch (status) {
      case 'completed':
        return (
          <svg className="w-6 h-6 text-white" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
          </svg>
        );
      case 'current':
        return (
          <span className="w-6 h-6 text-sm font-medium text-blue-600 bg-white border-2 border-blue-600 rounded-full flex items-center justify-center">
            {step}
          </span>
        );
      default:
        return (
          <span className="w-6 h-6 text-sm font-medium text-gray-500 bg-white border-2 border-gray-300 rounded-full flex items-center justify-center">
            {step}
          </span>
        );
    }
  };

  const getStepClassName = (status: string) => {
    const baseClasses = 'flex items-center space-x-3 transition-all duration-200';
    
    switch (status) {
      case 'completed':
        return `${baseClasses} text-green-600 cursor-pointer hover:text-green-700`;
      case 'current':
        return `${baseClasses} text-blue-600 font-medium`;
      default:
        return `${baseClasses} text-gray-400 cursor-not-allowed`;
    }
  };

  return (
    <div className={`w-full ${className}`}>
      {/* Progress Bar */}
      <div className="mb-8">
        <div className="flex justify-between items-center mb-2">
          <span className="text-sm font-medium text-gray-600">
            Step {currentStep} of {totalSteps}
          </span>
          <span className="text-sm text-gray-600">
            {Math.round(progressPercentage)}% complete
          </span>
        </div>
        
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div
            className="bg-blue-600 h-2 rounded-full transition-all duration-300 ease-out"
            style={{ width: `${progressPercentage}%` }}
          />
        </div>
      </div>

      {/* Step Indicators */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {stepTitles.map((title, index) => {
          const stepNumber = index + 1;
          const status = getStepStatus(stepNumber);
          const isClickable = onStepClick && (status === 'completed' || stepNumber <= currentStep + 1);

          return (
            <div
              key={stepNumber}
              className={getStepClassName(status)}
              onClick={isClickable ? () => onStepClick(stepNumber) : undefined}
            >
              <div className="flex-shrink-0">
                {getStepIcon(stepNumber, status)}
              </div>
              
              <div className="min-w-0 flex-1">
                {showStepNumbers && (
                  <p className="text-xs font-medium text-gray-500">
                    Step {stepNumber}
                  </p>
                )}
                {showStepTitles && (
                  <p className="text-sm font-medium truncate">
                    {title}
                  </p>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}; 