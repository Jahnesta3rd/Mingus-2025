// components/onboarding/EnhancedOnboardingFlow.tsx
import React, { useState, useEffect } from 'react';
import { OnboardingStep } from './OnboardingStep';
import { OnboardingService } from '../../services/onboardingService';
import { UserProfile, OnboardingProgress, ProfileCompletionAnalytics } from '../../types/user';

interface EnhancedOnboardingFlowProps {
  onComplete: (userData: Partial<UserProfile>) => void;
  onProgressUpdate?: (progress: OnboardingProgress) => void;
  onAnalyticsUpdate?: (analytics: ProfileCompletionAnalytics) => void;
  initialData?: Partial<UserProfile>;
  allowSkip?: boolean;
  showProgressBar?: boolean;
  autoSave?: boolean;
}

export const EnhancedOnboardingFlow: React.FC<EnhancedOnboardingFlowProps> = ({
  onComplete,
  onProgressUpdate,
  onAnalyticsUpdate,
  initialData = {},
  allowSkip = false,
  showProgressBar = true,
  autoSave = true
}) => {
  const [onboardingService] = useState(() => new OnboardingService(initialData));
  const [currentStep, setCurrentStep] = useState<number>(1);
  const [userData, setUserData] = useState<Partial<UserProfile>>(initialData);
  const [progress, setProgress] = useState<OnboardingProgress>(onboardingService.getProgress());
  const [analytics, setAnalytics] = useState<ProfileCompletionAnalytics>(onboardingService.getProfileCompletionAnalytics());
  const [validation, setValidation] = useState(onboardingService.validateCurrentStep());
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Load saved progress on mount
  useEffect(() => {
    if (autoSave) {
      onboardingService.loadProgress();
      const savedProgress = onboardingService.getProgress();
      const savedData = onboardingService.getUserData();
      
      setCurrentStep(savedProgress.currentStep);
      setUserData(savedData);
      setProgress(savedProgress);
      setAnalytics(onboardingService.getProfileCompletionAnalytics());
    }
  }, [autoSave]);

  // Update progress and analytics when data changes
  useEffect(() => {
    const newProgress = onboardingService.getProgress();
    const newAnalytics = onboardingService.getProfileCompletionAnalytics();
    
    setProgress(newProgress);
    setAnalytics(newAnalytics);
    
    onProgressUpdate?.(newProgress);
    onAnalyticsUpdate?.(newAnalytics);
  }, [userData, currentStep, onProgressUpdate, onAnalyticsUpdate]);

  // Auto-save progress
  useEffect(() => {
    if (autoSave) {
      onboardingService.saveProgress();
    }
  }, [userData, currentStep, autoSave]);

  const handleStepComplete = async (stepData: Record<string, any>) => {
    setIsLoading(true);
    setError(null);

    try {
      // Update service with new data
      onboardingService.updateStepData(stepData);
      const updatedData = onboardingService.getUserData();
      setUserData(updatedData);

      // Validate current step
      const newValidation = onboardingService.validateCurrentStep();
      setValidation(newValidation);

      if (!newValidation.isValid) {
        setError('Please fix the errors before continuing');
        setIsLoading(false);
        return;
      }

      // Check if onboarding is complete
      if (onboardingService.isOnboardingComplete()) {
        await handleOnboardingComplete(updatedData);
        return;
      }

      // Move to next step
      const moved = onboardingService.nextStep();
      if (moved) {
        setCurrentStep(onboardingService.getProgress().currentStep);
        setValidation(onboardingService.validateCurrentStep());
      }

    } catch (err) {
      setError('An error occurred while saving your information');
      console.error('Onboarding step error:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleStepBack = () => {
    const moved = onboardingService.previousStep();
    if (moved) {
      setCurrentStep(onboardingService.getProgress().currentStep);
      setValidation(onboardingService.validateCurrentStep());
    }
  };

  const handleSkipStep = () => {
    if (!allowSkip) return;

    const moved = onboardingService.nextStep();
    if (moved) {
      setCurrentStep(onboardingService.getProgress().currentStep);
      setValidation(onboardingService.validateCurrentStep());
    }
  };

  const handleOnboardingComplete = async (finalData: Partial<UserProfile>) => {
    setIsLoading(true);
    setError(null);

    try {
      // Calculate final completion percentage
      const finalAnalytics = onboardingService.getProfileCompletionAnalytics();
      const completedData = {
        ...finalData,
        profileCompletionPercentage: finalAnalytics.completionPercentage,
        onboardingStep: onboardingService.getAllSteps().length
      };

      await onComplete(completedData);
    } catch (err) {
      setError('Failed to complete onboarding. Please try again.');
      console.error('Onboarding completion error:', err);
      setIsLoading(false);
    }
  };

  const handleJumpToStep = (stepNumber: number) => {
    const moved = onboardingService.goToStep(stepNumber);
    if (moved) {
      setCurrentStep(stepNumber);
      setValidation(onboardingService.validateCurrentStep());
    }
  };

  const currentStepData = onboardingService.getCurrentStep();
  const totalSteps = onboardingService.getAllSteps().length;
  const isFirstStep = currentStep === 1;
  const isLastStep = currentStep === totalSteps;
  const canProceed = validation.isValid && !isLoading;

  if (!currentStepData) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <h2 className="text-2xl font-bold text-gray-900 mb-4">Onboarding Error</h2>
          <p className="text-gray-600">Unable to load onboarding step. Please refresh the page.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-12">
      {/* Progress Bar */}
      {showProgressBar && (
        <div className="max-w-4xl mx-auto mb-8 px-6">
          <div className="flex justify-between items-center mb-4">
            <span className="text-sm font-medium text-gray-600">
              Step {currentStep} of {totalSteps}
            </span>
            <span className="text-sm text-gray-600">
              {progress.profileCompletionPercentage}% complete
            </span>
          </div>
          
          {/* Main Progress Bar */}
          <div className="w-full bg-gray-200 rounded-full h-3 mb-2">
            <div
              className="bg-blue-600 h-3 rounded-full transition-all duration-300"
              style={{ width: `${(currentStep / totalSteps) * 100}%` }}
            />
          </div>
          
          {/* Profile Completion Bar */}
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div
              className="bg-green-500 h-2 rounded-full transition-all duration-300"
              style={{ width: `${progress.profileCompletionPercentage}%` }}
            />
          </div>
          
          {/* Step Indicators */}
          <div className="flex justify-between mt-4">
            {onboardingService.getAllSteps().map((step, index) => (
              <button
                key={step.step}
                onClick={() => handleJumpToStep(step.step)}
                className={`flex flex-col items-center space-y-1 ${
                  step.step <= currentStep ? 'text-blue-600' : 'text-gray-400'
                }`}
                disabled={step.step > currentStep + 1}
              >
                <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${
                  step.step < currentStep ? 'bg-green-500 text-white' :
                  step.step === currentStep ? 'bg-blue-600 text-white' :
                  'bg-gray-200 text-gray-500'
                }`}>
                  {step.step < currentStep ? '✓' : step.step}
                </div>
                <span className="text-xs text-center max-w-16">{step.title}</span>
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Error Display */}
      {error && (
        <div className="max-w-4xl mx-auto mb-6 px-6">
          <div className="bg-red-50 border border-red-200 rounded-lg p-4">
            <div className="flex">
              <div className="flex-shrink-0">
                <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                </svg>
              </div>
              <div className="ml-3">
                <p className="text-sm text-red-800">{error}</p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Validation Errors */}
      {validation.errors.length > 0 && (
        <div className="max-w-4xl mx-auto mb-6 px-6">
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
            <div className="flex">
              <div className="flex-shrink-0">
                <svg className="h-5 w-5 text-yellow-400" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                </svg>
              </div>
              <div className="ml-3">
                <h3 className="text-sm font-medium text-yellow-800">
                  Please fix the following errors:
                </h3>
                <div className="mt-2 text-sm text-yellow-700">
                  <ul className="list-disc pl-5 space-y-1">
                    {validation.errors.map((error, index) => (
                      <li key={index}>{error.message}</li>
                    ))}
                  </ul>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Main Content */}
      <div className="max-w-4xl mx-auto px-6">
        <OnboardingStep
          step={currentStepData}
          data={userData}
          onNext={handleStepComplete}
          onPrevious={handleStepBack}
          onSkip={allowSkip ? handleSkipStep : undefined}
          isFirst={isFirstStep}
          isLast={isLastStep}
          isLoading={isLoading}
          canProceed={canProceed}
          validation={validation}
        />
      </div>

      {/* Analytics Summary (Optional) */}
      {analytics.completionPercentage > 0 && (
        <div className="max-w-4xl mx-auto mt-8 px-6">
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Profile Completion Summary</h3>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
              {Object.entries(analytics.categoryCompletions).map(([category, percentage]) => (
                <div key={category} className="text-center">
                  <div className="text-2xl font-bold text-blue-600">{percentage}%</div>
                  <div className="text-sm text-gray-600 capitalize">{category}</div>
                </div>
              ))}
            </div>
            {analytics.nextRecommendedFields.length > 0 && (
              <div className="mt-4 p-4 bg-blue-50 rounded-lg">
                <p className="text-sm text-blue-800">
                  <strong>Next recommended:</strong> {analytics.nextRecommendedFields.join(', ')}
                </p>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}; 