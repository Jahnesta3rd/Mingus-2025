// components/onboarding/OnboardingFlow.tsx
import React, { useState, useEffect, useCallback } from 'react';
import { OnboardingStep } from './OnboardingStep';
import { FormProgress } from '../forms/FormProgress';
import { OnboardingService } from '../../services/onboardingService';
import { ONBOARDING_STEPS } from '../../config/onboarding';
import { UserProfile } from '../../types/user';

interface OnboardingFlowProps {
  onComplete: (userData: Partial<UserProfile>) => void;
  onStepChange?: (step: number, data: Partial<UserProfile>) => void;
  onSave?: (data: Partial<UserProfile>) => Promise<void>;
  initialData?: Partial<UserProfile>;
  autoSave?: boolean;
  showAnalytics?: boolean;
  allowSkip?: boolean;
  className?: string;
}

export const OnboardingFlow: React.FC<OnboardingFlowProps> = ({ 
  onComplete, 
  onStepChange,
  onSave,
  initialData = {},
  autoSave = true,
  showAnalytics = true,
  allowSkip = true,
  className = ''
}) => {
  const [onboardingService] = useState(() => new OnboardingService(initialData));
  const [currentStep, setCurrentStep] = useState(1);
  const [userData, setUserData] = useState<Partial<UserProfile>>(initialData);
  const [isLoading, setIsLoading] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [validation, setValidation] = useState(onboardingService.validateCurrentStep());
  const [lastSavedData, setLastSavedData] = useState<Partial<UserProfile>>(initialData);
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);

  // Load saved progress on mount
  useEffect(() => {
    onboardingService.loadProgress();
    const progress = onboardingService.getProgress();
    const savedData = onboardingService.getUserData();
    
    setCurrentStep(progress.currentStep);
    setUserData(savedData);
    setLastSavedData(savedData);
    setValidation(onboardingService.validateCurrentStep());
  }, []);

  // Auto-save functionality
  useEffect(() => {
    if (autoSave && hasUnsavedChanges && !isLoading) {
      const saveTimeout = setTimeout(() => {
        handleAutoSave();
      }, 2000); // Save after 2 seconds of inactivity

      return () => clearTimeout(saveTimeout);
    }
  }, [userData, autoSave, hasUnsavedChanges, isLoading]);

  // Update validation when data or step changes
  useEffect(() => {
    setValidation(onboardingService.validateCurrentStep());
  }, [userData, currentStep]);

  // Track unsaved changes
  useEffect(() => {
    const hasChanges = JSON.stringify(userData) !== JSON.stringify(lastSavedData);
    setHasUnsavedChanges(hasChanges);
  }, [userData, lastSavedData]);

  const handleAutoSave = useCallback(async () => {
    if (!onSave || !hasUnsavedChanges) return;

    setIsSaving(true);
    try {
      await onSave(userData);
      setLastSavedData(userData);
      setHasUnsavedChanges(false);
      onboardingService.saveProgress();
    } catch (error) {
      console.error('Auto-save failed:', error);
    } finally {
      setIsSaving(false);
    }
  }, [onSave, userData, hasUnsavedChanges]);

  const handleNext = async (stepData: Record<string, any>) => {
    setIsLoading(true);
    
    try {
      // Update service with new data
      onboardingService.updateStepData(stepData);
      const updatedData = onboardingService.getUserData();
      setUserData(updatedData);

      // Save progress if callback provided
      if (onSave) {
        await onSave(updatedData);
        setLastSavedData(updatedData);
        setHasUnsavedChanges(false);
      }

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
    if (isLoading) return;

    const moved = onboardingService.previousStep();
    if (moved) {
      const newStep = onboardingService.getProgress().currentStep;
      setCurrentStep(newStep);
      
      // Notify parent of step change
      onStepChange?.(newStep, userData);
    }
  };

  const handleSkip = () => {
    if (isLoading || !allowSkip) return;

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
      // Calculate final completion percentage and analytics
      const finalAnalytics = onboardingService.getProfileCompletionAnalytics();
      const completedData = {
        ...finalData,
        profileCompletionPercentage: finalAnalytics.completionPercentage,
        onboardingStep: ONBOARDING_STEPS.length
      };

      // Final save before completion
      if (onSave) {
        await onSave(completedData);
      }

      // Notify parent of completion
      onComplete(completedData);
      
      // Clear saved progress
      onboardingService.clearProgress();
      
    } catch (error) {
      console.error('Error completing onboarding:', error);
    }
  };

  const handleGoToStep = (stepNumber: number) => {
    if (isLoading) return;

    const success = onboardingService.goToStep(stepNumber);
    if (success) {
      setCurrentStep(stepNumber);
      onStepChange?.(stepNumber, userData);
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
    <div className={`min-h-screen bg-gray-50 py-12 ${className}`}>
      {/* Enhanced Progress Header */}
      <div className="max-w-4xl mx-auto px-6 mb-8">
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex justify-between items-center mb-4">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Complete Your Profile</h1>
              <p className="text-gray-600">Step {currentStep} of {ONBOARDING_STEPS.length}</p>
            </div>
            <div className="text-right">
              <div className="text-2xl font-bold text-blue-600">
                {analytics.completionPercentage}%
              </div>
              <div className="text-sm text-gray-500">Complete</div>
            </div>
          </div>
          
          {/* Enhanced Progress Bar */}
          <FormProgress
            currentStep={currentStep}
            totalSteps={ONBOARDING_STEPS.length}
            completedSteps={progress.completedSteps}
            onStepClick={handleGoToStep}
            showStepNumbers={true}
            showPercentage={true}
            className="mb-4"
          />
          
          {/* Profile Completion Bar */}
          <div className="mt-4">
            <div className="flex justify-between text-xs text-gray-500 mb-1">
              <span>Profile Completion</span>
              <span>{analytics.completedFields}/{analytics.totalFields} fields</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className="bg-green-500 h-2 rounded-full transition-all duration-300"
                style={{ width: `${analytics.completionPercentage}%` }}
              />
            </div>
          </div>

          {/* Auto-save indicator */}
          {autoSave && (
            <div className="mt-3 flex items-center justify-between text-xs">
              <div className="flex items-center space-x-2">
                {isSaving ? (
                  <>
                    <svg className="animate-spin h-3 w-3 text-blue-600" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                    </svg>
                    <span className="text-blue-600">Saving...</span>
                  </>
                ) : hasUnsavedChanges ? (
                  <>
                    <div className="w-2 h-2 bg-yellow-400 rounded-full"></div>
                    <span className="text-yellow-600">Unsaved changes</span>
                  </>
                ) : (
                  <>
                    <div className="w-2 h-2 bg-green-400 rounded-full"></div>
                    <span className="text-green-600">All changes saved</span>
                  </>
                )}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Current Step */}
      <OnboardingStep
        step={currentStepData}
        data={userData}
        onNext={handleNext}
        onPrevious={handlePrevious}
        onSkip={allowSkip ? handleSkip : undefined}
        isFirst={currentStep === 1}
        isLast={currentStep === ONBOARDING_STEPS.length}
        isLoading={isLoading}
        canProceed={validation.isValid}
        validation={validation}
      />

      {/* Analytics Summary */}
      {showAnalytics && (
        <div className="max-w-4xl mx-auto px-6 mt-8">
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Profile Completion Summary</h3>
            
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
              {Object.entries(analytics.categoryCompletions).map(([category, percentage]) => (
                <div key={category} className="text-center">
                  <div className="text-2xl font-bold text-blue-600">{percentage}%</div>
                  <div className="text-sm text-gray-600 capitalize">{category}</div>
                </div>
              ))}
            </div>
            
            {analytics.nextRecommendedFields.length > 0 && (
              <div className="p-4 bg-blue-50 rounded-lg">
                <p className="text-sm text-blue-800">
                  <strong>Next recommended:</strong> {analytics.nextRecommendedFields.join(', ')}
                </p>
              </div>
            )}

            {/* Missing Fields Summary */}
            {analytics.missingFields.length > 0 && (
              <div className="mt-4 p-4 bg-yellow-50 rounded-lg">
                <h4 className="text-sm font-medium text-yellow-800 mb-2">Missing Fields</h4>
                <div className="grid grid-cols-2 md:grid-cols-3 gap-2 text-xs">
                  {analytics.missingFields.slice(0, 6).map((field, index) => (
                    <div key={index} className="text-yellow-700">{field}</div>
                  ))}
                  {analytics.missingFields.length > 6 && (
                    <div className="text-yellow-700">+{analytics.missingFields.length - 6} more</div>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Quick Navigation */}
      <div className="max-w-4xl mx-auto px-6 mt-6">
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
          <h4 className="text-sm font-medium text-gray-900 mb-3">Quick Navigation</h4>
          <div className="flex flex-wrap gap-2">
            {ONBOARDING_STEPS.map((step, index) => (
              <button
                key={step.step}
                onClick={() => handleGoToStep(step.step)}
                disabled={isLoading}
                className={`px-3 py-1 text-xs rounded-full border transition-colors ${
                  step.step === currentStep
                    ? 'bg-blue-600 text-white border-blue-600'
                    : progress.completedSteps.includes(step.step)
                    ? 'bg-green-100 text-green-800 border-green-300 hover:bg-green-200'
                    : 'bg-gray-100 text-gray-600 border-gray-300 hover:bg-gray-200'
                } ${isLoading ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}`}
              >
                {step.step}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Debug Information (Development Only) */}
      {process.env.NODE_ENV === 'development' && (
        <div className="max-w-4xl mx-auto px-6 mt-6">
          <div className="bg-gray-100 rounded-lg p-4">
            <h3 className="font-medium text-gray-900 mb-2">Debug Information</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
              <div>
                <strong>Current Step:</strong> {currentStep}
                <br />
                <strong>Completed Steps:</strong> {progress.completedSteps.join(', ')}
                <br />
                <strong>Profile Completion:</strong> {analytics.completionPercentage}%
                <br />
                <strong>Has Unsaved Changes:</strong> {hasUnsavedChanges ? 'Yes' : 'No'}
              </div>
              <div>
                <strong>Missing Fields:</strong> {analytics.missingFields.length}
                <br />
                <strong>Validation Valid:</strong> {validation.isValid ? 'Yes' : 'No'}
                <strong>Errors:</strong> {validation.errors.length}
                <br />
                <strong>Auto-save:</strong> {autoSave ? 'Enabled' : 'Disabled'}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}; 