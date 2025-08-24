// components/onboarding/OnboardingStepExample.tsx
import React, { useState, useEffect } from 'react';
import { OnboardingStep } from './OnboardingStep';
import { OnboardingService } from '../../services/onboardingService';
import { ONBOARDING_STEPS } from '../../config/onboarding';
import { UserProfile } from '../../types/user';

interface OnboardingStepExampleProps {
  initialData?: Partial<UserProfile>;
  onComplete?: (userData: Partial<UserProfile>) => void;
  onStepChange?: (step: number, data: Partial<UserProfile>) => void;
}

export const OnboardingStepExample: React.FC<OnboardingStepExampleProps> = ({
  initialData = {},
  onComplete,
  onStepChange
}) => {
  const [onboardingService] = useState(() => new OnboardingService(initialData));
  const [currentStep, setCurrentStep] = useState(1);
  const [userData, setUserData] = useState<Partial<UserProfile>>(initialData);
  const [isLoading, setIsLoading] = useState(false);
  const [validation, setValidation] = useState(onboardingService.validateCurrentStep());

  // Load saved progress on mount
  useEffect(() => {
    onboardingService.loadProgress();
    const progress = onboardingService.getProgress();
    setCurrentStep(progress.currentStep);
    setUserData(onboardingService.getUserData());
  }, []);

  // Update validation when data changes
  useEffect(() => {
    setValidation(onboardingService.validateCurrentStep());
  }, [userData, currentStep]);

  const handleNext = async (stepData: Record<string, any>) => {
    setIsLoading(true);
    
    try {
      // Update service with new data
      onboardingService.updateStepData(stepData);
      const updatedData = onboardingService.getUserData();
      setUserData(updatedData);

      // Check if onboarding is complete
      if (onboardingService.isOnboardingComplete()) {
        await handleOnboardingComplete(updatedData);
        return;
      }

      // Move to next step
      const moved = onboardingService.nextStep();
      if (moved) {
        const newStep = onboardingService.getProgress().currentStep;
        setCurrentStep(newStep);
        
        // Notify parent of step change
        onStepChange?.(newStep, updatedData);
      }

    } catch (error) {
      console.error('Error proceeding to next step:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handlePrevious = () => {
    const moved = onboardingService.previousStep();
    if (moved) {
      const newStep = onboardingService.getProgress().currentStep;
      setCurrentStep(newStep);
      
      // Notify parent of step change
      onStepChange?.(newStep, userData);
    }
  };

  const handleSkip = () => {
    const moved = onboardingService.nextStep();
    if (moved) {
      const newStep = onboardingService.getProgress().currentStep;
      setCurrentStep(newStep);
      
      // Notify parent of step change
      onStepChange?.(newStep, userData);
    }
  };

  const handleOnboardingComplete = async (finalData: Partial<UserProfile>) => {
    try {
      // Calculate final completion percentage
      const finalAnalytics = onboardingService.getProfileCompletionAnalytics();
      const completedData = {
        ...finalData,
        profileCompletionPercentage: finalAnalytics.completionPercentage,
        onboardingStep: ONBOARDING_STEPS.length
      };

      // Notify parent of completion
      onComplete?.(completedData);
      
      // Clear saved progress
      onboardingService.clearProgress();
      
    } catch (error) {
      console.error('Error completing onboarding:', error);
    }
  };

  const currentStepData = onboardingService.getCurrentStep();
  const progress = onboardingService.getProgress();
  const analytics = onboardingService.getProfileCompletionAnalytics();

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
      {/* Progress Header */}
      <div className="max-w-4xl mx-auto px-6 mb-8">
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex justify-between items-center mb-4">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Onboarding Progress</h1>
              <p className="text-gray-600">Step {currentStep} of {ONBOARDING_STEPS.length}</p>
            </div>
            <div className="text-right">
              <div className="text-2xl font-bold text-blue-600">
                {analytics.completionPercentage}%
              </div>
              <div className="text-sm text-gray-500">Complete</div>
            </div>
          </div>
          
          {/* Progress Bar */}
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div
              className="bg-blue-600 h-2 rounded-full transition-all duration-300"
              style={{ width: `${(currentStep / ONBOARDING_STEPS.length) * 100}%` }}
            />
          </div>
          
          {/* Profile Completion Bar */}
          <div className="mt-2">
            <div className="flex justify-between text-xs text-gray-500 mb-1">
              <span>Profile Completion</span>
              <span>{analytics.completedFields}/{analytics.totalFields} fields</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-1">
              <div
                className="bg-green-500 h-1 rounded-full transition-all duration-300"
                style={{ width: `${analytics.completionPercentage}%` }}
              />
            </div>
          </div>
        </div>
      </div>

      {/* Current Step */}
      <OnboardingStep
        step={currentStepData}
        data={userData}
        onNext={handleNext}
        onPrevious={handlePrevious}
        onSkip={handleSkip}
        isFirst={currentStep === 1}
        isLast={currentStep === ONBOARDING_STEPS.length}
        isLoading={isLoading}
        canProceed={validation.isValid}
        validation={validation}
      />

      {/* Analytics Summary */}
      <div className="max-w-4xl mx-auto px-6 mt-8">
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
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

      {/* Debug Information (Development Only) */}
      {process.env.NODE_ENV === 'development' && (
        <div className="max-w-4xl mx-auto px-6 mt-8">
          <div className="bg-gray-100 rounded-lg p-4">
            <h3 className="font-medium text-gray-900 mb-2">Debug Information</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
              <div>
                <strong>Current Step:</strong> {currentStep}
                <br />
                <strong>Completed Steps:</strong> {progress.completedSteps.join(', ')}
                <br />
                <strong>Profile Completion:</strong> {analytics.completionPercentage}%
              </div>
              <div>
                <strong>Missing Fields:</strong> {analytics.missingFields.length}
                <br />
                <strong>Validation Valid:</strong> {validation.isValid ? 'Yes' : 'No'}
                <br />
                <strong>Errors:</strong> {validation.errors.length}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}; 