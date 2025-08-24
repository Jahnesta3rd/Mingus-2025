// components/forms/FormActions.tsx
import React from 'react';

interface FormActionsProps {
  onNext?: () => void;
  onPrevious?: () => void;
  onSkip?: () => void;
  onSave?: () => void;
  onCancel?: () => void;
  isFirst?: boolean;
  isLast?: boolean;
  isLoading?: boolean;
  canProceed?: boolean;
  showSkip?: boolean;
  showSave?: boolean;
  showCancel?: boolean;
  nextLabel?: string;
  previousLabel?: string;
  skipLabel?: string;
  saveLabel?: string;
  cancelLabel?: string;
  className?: string;
}

export const FormActions: React.FC<FormActionsProps> = ({
  onNext,
  onPrevious,
  onSkip,
  onSave,
  onCancel,
  isFirst = false,
  isLast = false,
  isLoading = false,
  canProceed = true,
  showSkip = false,
  showSave = false,
  showCancel = false,
  nextLabel = 'Next',
  previousLabel = 'Previous',
  skipLabel = 'Skip',
  saveLabel = 'Save',
  cancelLabel = 'Cancel',
  className = ''
}) => {
  const handleNext = () => {
    if (onNext && canProceed && !isLoading) {
      onNext();
    }
  };

  const handlePrevious = () => {
    if (onPrevious && !isLoading) {
      onPrevious();
    }
  };

  const handleSkip = () => {
    if (onSkip && !isLoading) {
      onSkip();
    }
  };

  const handleSave = () => {
    if (onSave && !isLoading) {
      onSave();
    }
  };

  const handleCancel = () => {
    if (onCancel && !isLoading) {
      onCancel();
    }
  };

  return (
    <div className={`flex justify-between items-center pt-6 border-t border-gray-200 ${className}`}>
      {/* Left side - Previous and Cancel */}
      <div className="flex space-x-3">
        {!isFirst && onPrevious && (
          <button
            type="button"
            onClick={handlePrevious}
            disabled={isLoading}
            className="px-6 py-3 border border-gray-300 text-gray-700 bg-white rounded-lg hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors duration-200"
          >
            {isLoading ? (
              <div className="flex items-center space-x-2">
                <svg className="animate-spin h-4 w-4 text-gray-500" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                </svg>
                <span>Loading...</span>
              </div>
            ) : (
              <>
                <svg className="w-4 h-4 mr-2 inline" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                </svg>
                {previousLabel}
              </>
            )}
          </button>
        )}

        {showCancel && onCancel && (
          <button
            type="button"
            onClick={handleCancel}
            disabled={isLoading}
            className="px-6 py-3 border border-gray-300 text-gray-700 bg-white rounded-lg hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-red-500 focus:border-red-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors duration-200"
          >
            {cancelLabel}
          </button>
        )}
      </div>

      {/* Right side - Skip, Save, and Next */}
      <div className="flex space-x-3">
        {showSkip && onSkip && !isLast && (
          <button
            type="button"
            onClick={handleSkip}
            disabled={isLoading}
            className="px-6 py-3 text-gray-600 bg-transparent hover:text-gray-800 focus:outline-none focus:ring-2 focus:ring-gray-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors duration-200"
          >
            {skipLabel}
          </button>
        )}

        {showSave && onSave && (
          <button
            type="button"
            onClick={handleSave}
            disabled={isLoading}
            className="px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-green-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors duration-200"
          >
            {isLoading ? (
              <div className="flex items-center space-x-2">
                <svg className="animate-spin h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                </svg>
                <span>Saving...</span>
              </div>
            ) : (
              <>
                <svg className="w-4 h-4 mr-2 inline" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
                {saveLabel}
              </>
            )}
          </button>
        )}

        {onNext && (
          <button
            type="button"
            onClick={handleNext}
            disabled={isLoading || !canProceed}
            className={`px-6 py-3 text-white rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors duration-200 ${
              canProceed && !isLoading
                ? 'bg-blue-600 hover:bg-blue-700'
                : 'bg-gray-400 cursor-not-allowed'
            }`}
          >
            {isLoading ? (
              <div className="flex items-center space-x-2">
                <svg className="animate-spin h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                </svg>
                <span>Loading...</span>
              </div>
            ) : (
              <>
                {isLast ? (
                  <>
                    <svg className="w-4 h-4 mr-2 inline" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                    Complete Setup
                  </>
                ) : (
                  <>
                    {nextLabel}
                    <svg className="w-4 h-4 ml-2 inline" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                    </svg>
                  </>
                )}
              </>
            )}
          </button>
        )}
      </div>
    </div>
  );
}; 