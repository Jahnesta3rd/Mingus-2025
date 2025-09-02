import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { OnboardingFlowService } from '../../services/onboarding-flow-service';
import { OnboardingStep } from '../../types/onboarding';

interface OnboardingNavigationProps {
  currentStep: string;
  onStepComplete?: (stepName: string) => void;
  showProgress?: boolean;
}

const OnboardingNavigation: React.FC<OnboardingNavigationProps> = ({
  currentStep,
  onStepComplete,
  showProgress = true
}) => {
  const [steps, setSteps] = useState<OnboardingStep[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

  useEffect(() => {
    const loadSteps = async () => {
      try {
        const stepsWithStatus = await OnboardingFlowService.getAllStepsWithStatus();
        setSteps(stepsWithStatus);
      } catch (err) {
        setError('Failed to load onboarding steps');
      } finally {
        setLoading(false);
      }
    };

    loadSteps();
  }, []);

  const handleStepClick = async (stepName: string) => {
    try {
      const success = await OnboardingFlowService.navigateToStep(stepName);
      if (!success) {
        setError('Cannot navigate to this step yet');
      }
    } catch (err) {
      setError('Navigation failed');
    }
  };

  const handleNextStep = async () => {
    try {
      const nextStep = await OnboardingFlowService.navigateToNextStep(currentStep);
      if (nextStep && onStepComplete) {
        onStepComplete(currentStep);
      }
    } catch (err) {
      setError('Failed to proceed to next step');
    }
  };

  const handleSkipStep = async () => {
    try {
      const nextStep = await OnboardingFlowService.navigateToNextStep(currentStep);
      if (nextStep) {
        // Mark current step as skipped
        await OnboardingFlowService.markStepCompleted(currentStep, { skipped: true });
        if (onStepComplete) {
          onStepComplete(currentStep);
        }
      }
    } catch (err) {
      setError('Failed to skip step');
    }
  };

  const getCurrentStepInfo = () => {
    return steps.find(step => step.name === currentStep);
  };

  const getNextStepInfo = () => {
    const currentIndex = steps.findIndex(step => step.name === currentStep);
    if (currentIndex >= 0 && currentIndex < steps.length - 1) {
      return steps[currentIndex + 1];
    }
    return null;
  };

  const canProceedToNext = () => {
    const currentStepInfo = getCurrentStepInfo();
    return currentStepInfo?.completed || currentStepInfo?.canSkip;
  };

  if (loading) {
    return (
      <div className="flex justify-center py-4">
        <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-600 text-sm">{error}</p>
        </div>
      )}

      {showProgress && (
        <div className="bg-white rounded-lg p-4 shadow-sm border border-gray-200">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-medium text-gray-700">Onboarding Progress</h3>
            <span className="text-sm text-gray-500">
              {steps.filter(s => s.completed).length} of {steps.length} steps
            </span>
          </div>
          
          <div className="flex space-x-2 mb-4">
            {steps.map((step, index) => (
              <button
                key={step.name}
                onClick={() => handleStepClick(step.name)}
                disabled={!step.completed && !step.isCurrent}
                className={`flex-1 h-2 rounded-full transition-colors ${
                  step.completed
                    ? 'bg-green-500'
                    : step.isCurrent
                    ? 'bg-blue-500'
                    : 'bg-gray-200'
                } ${step.completed || step.isCurrent ? 'cursor-pointer' : 'cursor-not-allowed'}`}
                title={`${step.displayName} - ${step.completed ? 'Completed' : step.isCurrent ? 'Current' : 'Not available'}`}
              />
            ))}
          </div>

          <div className="flex justify-between text-xs text-gray-500">
            <span>{getCurrentStepInfo()?.displayName}</span>
            {getNextStepInfo() && (
              <span>Next: {getNextStepInfo()?.displayName}</span>
            )}
          </div>
        </div>
      )}

      <div className="flex justify-between items-center">
        <button
          onClick={() => navigate('/dashboard')}
          className="px-4 py-2 text-gray-600 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
        >
          Back to Dashboard
        </button>

        <div className="flex space-x-3">
          {getCurrentStepInfo()?.canSkip && (
            <button
              onClick={handleSkipStep}
              className="px-4 py-2 text-gray-600 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
            >
              Skip
            </button>
          )}
          
          <button
            onClick={handleNextStep}
            disabled={!canProceedToNext()}
            className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {getNextStepInfo() ? `Continue to ${getNextStepInfo()?.displayName}` : 'Complete'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default OnboardingNavigation; 