import React, { useEffect } from 'react';
import { useAICalculatorStore } from '../../store/aiCalculatorStore';
import { ProgressBar } from './ProgressBar';
import { JobInfoStep } from './steps/JobInfoStep';
import { DailyTasksStep } from './steps/DailyTasksStep';
import { WorkEnvironmentStep } from './steps/WorkEnvironmentStep';
import { SkillsConcernsStep } from './steps/SkillsConcernsStep';
import { ContactInfoStep } from './steps/ContactInfoStep';
import { AIResultsDisplay } from './AIResultsDisplay';

interface AICalculatorModalProps {
  isOpen: boolean;
  onClose: () => void;
  onComplete?: (results: any) => void;
}

export const AICalculatorModal: React.FC<AICalculatorModalProps> = ({
  isOpen,
  onClose,
  onComplete
}) => {
  const {
    currentStep,
    totalSteps,
    formData,
    isSubmitting,
    results,
    error,
    isModalOpen,
    openModal,
    closeModal,
    setCurrentStep,
    updateFormData,
    validateStep,
    submitForm,
    resetForm,
    clearError
  } = useAICalculatorStore();

  // Sync external isOpen prop with store
  useEffect(() => {
    if (isOpen && !isModalOpen) {
      openModal();
    } else if (!isOpen && isModalOpen) {
      closeModal();
    }
  }, [isOpen, isModalOpen, openModal, closeModal]);

  const handleClose = () => {
    closeModal();
    onClose();
  };

  const handleNext = () => {
    const errors = validateStep(currentStep);
    if (Object.keys(errors).length === 0) {
      if (currentStep === totalSteps) {
        submitForm();
      } else {
        setCurrentStep(currentStep + 1);
      }
    }
  };

  const handleBack = () => {
    if (currentStep > 1) {
      setCurrentStep(currentStep - 1);
    }
  };

  const handleUpdateFormData = (data: any) => {
    updateFormData(data);
    clearError();
  };

  const renderStep = () => {
    const stepProps = {
      formData,
      onUpdate: handleUpdateFormData,
      onNext: handleNext,
      onBack: handleBack,
      currentStep,
      totalSteps,
      errors: validateStep(currentStep)
    };

    switch (currentStep) {
      case 1:
        return <JobInfoStep {...stepProps} />;
      case 2:
        return <DailyTasksStep {...stepProps} />;
      case 3:
        return <WorkEnvironmentStep {...stepProps} />;
      case 4:
        return <SkillsConcernsStep {...stepProps} />;
      case 5:
        return <ContactInfoStep {...stepProps} />;
      case 6:
        return results ? (
          <AIResultsDisplay 
            results={results}
            onUpgrade={() => {
              // Handle upgrade logic
              console.log('Upgrade clicked');
            }}
            onShare={() => {
              // Handle share logic
              console.log('Share clicked');
            }}
            countdownMinutes={60}
          />
        ) : null;
      default:
        return null;
    }
  };

  if (!isModalOpen) return null;

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      {/* Backdrop */}
      <div 
        className="fixed inset-0 bg-black bg-opacity-50 transition-opacity"
        onClick={handleClose}
        aria-hidden="true"
      />

      {/* Modal */}
      <div className="flex min-h-full items-center justify-center p-4">
        <div className="relative w-full max-w-4xl bg-white rounded-2xl shadow-2xl overflow-hidden">
          {/* Header */}
          <div className="bg-gradient-to-r from-purple-600 to-purple-800 text-white p-6">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-2xl font-bold">
                  AI Job Impact Calculator
                </h2>
                <p className="text-purple-100 mt-1">
                  Discover how AI will affect your career in the next 5 years
                </p>
              </div>
              <button
                onClick={handleClose}
                className="text-white hover:text-purple-200 transition-colors p-2"
                aria-label="Close modal"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
            
            {/* Progress Bar */}
            {currentStep <= totalSteps && (
              <div className="mt-6">
                <ProgressBar 
                  currentStep={currentStep} 
                  totalSteps={totalSteps}
                  className="bg-purple-700"
                />
              </div>
            )}
          </div>

          {/* Content */}
          <div className="p-6 max-h-[70vh] overflow-y-auto">
            {/* Error Display */}
            {error && (
              <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg">
                <div className="flex items-center">
                  <svg className="w-5 h-5 text-red-400 mr-2" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                  </svg>
                  <span className="text-red-800 font-medium">{error}</span>
                </div>
              </div>
            )}

            {/* Loading State */}
            {isSubmitting && (
              <div className="flex items-center justify-center py-12">
                <div className="text-center">
                  <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600 mx-auto mb-4"></div>
                  <p className="text-gray-600 font-medium">Analyzing your job impact...</p>
                  <p className="text-gray-500 text-sm mt-2">This may take a few moments</p>
                </div>
              </div>
            )}

            {/* Step Content */}
            {!isSubmitting && renderStep()}
          </div>

          {/* Footer */}
          {currentStep <= totalSteps && !isSubmitting && (
            <div className="bg-gray-50 px-6 py-4 border-t border-gray-200">
              <div className="flex items-center justify-between">
                <div className="text-sm text-gray-500">
                  Step {currentStep} of {totalSteps}
                </div>
                <div className="flex space-x-3">
                  {currentStep > 1 && (
                    <button
                      onClick={handleBack}
                      className="px-4 py-2 text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
                    >
                      Back
                    </button>
                  )}
                  <button
                    onClick={handleNext}
                    disabled={Object.keys(validateStep(currentStep)).length > 0}
                    className="px-6 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                  >
                    {currentStep === totalSteps ? 'Get Results' : 'Next'}
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
