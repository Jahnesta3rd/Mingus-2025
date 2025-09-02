import React, { useEffect, useState, useCallback } from 'react';
import { OnboardingFlowService } from '../../services/OnboardingFlowService';
import { OnboardingProgress } from '../../types/onboarding';
import { useNetworkStatus } from '../../hooks/useNetworkStatus';
import { VerificationErrorDisplay } from './VerificationErrorDisplay';
import { getBackoffDelay } from '../utils/exponentialBackoff';

interface OnboardingProgressBarProps {
  userId: string;
  currentStep: string;
  showTimeEstimate?: boolean;
  showStepIndicators?: boolean;
}

export const OnboardingProgressBar: React.FC<OnboardingProgressBarProps> = ({
  userId,
  currentStep,
  showTimeEstimate = true,
  showStepIndicators = true
}) => {
  const [progress, setProgress] = useState<OnboardingProgress | null>(null);
  const [summary, setSummary] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const flowService = OnboardingFlowService.getInstance();
  const isOnline = useNetworkStatus();
  const [error, setError] = useState<VerificationError | null>(null);
  const [retryAttempt, setRetryAttempt] = useState(0);
  const [retryDelay, setRetryDelay] = useState(0);

  useEffect(() => {
    loadProgress();
  }, [userId, currentStep]);

  const loadProgress = async () => {
    try {
      setLoading(true);
      const progressData = await flowService.fetchProgress(userId);
      setProgress(progressData);
      setSummary(flowService.getProgressSummary(progressData));
    } catch (error) {
      console.error('Error loading progress:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleRetry = useCallback(() => {
    setRetryAttempt((prev) => prev + 1);
    setRetryDelay(getBackoffDelay(retryAttempt));
    // Retry logic here...
  }, [retryAttempt]);

  if (loading) {
    return (
      <div className="w-full max-w-4xl mx-auto px-4 py-6">
        <div className="animate-pulse">
          <div className="h-2 bg-gray-200 rounded-full mb-4"></div>
          <div className="flex justify-between">
            {[...Array(5)].map((_, i) => (
              <div key={i} className="w-8 h-8 bg-gray-200 rounded-full"></div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (!progress || !summary) {
    return null;
  }

  const steps = flowService.getAllSteps().filter(s => s.required);

  return (
    <div className="w-full max-w-4xl mx-auto px-4 py-6">
      {/* Progress Bar */}
      <div className="mb-4">
        <div className="flex justify-between items-center mb-2">
          <span className="text-base leading-relaxed font-medium text-gray-700">
            Step {summary.completedSteps + 1} of {summary.totalSteps}
          </span>
          <span className="text-base leading-relaxed font-medium text-gray-700">
            {progress.progressPercentage}% Complete
          </span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div
            className="bg-gradient-to-r from-blue-600 to-indigo-600 h-2 rounded-full transition-all duration-300"
            style={{ width: `${progress.progressPercentage}%` }}
          ></div>
        </div>
      </div>

      {/* Step Indicators */}
      {showStepIndicators && (
        <div className="flex justify-between items-center mb-4">
          {steps.map((step, index) => {
            const isCompleted = progress.completedSteps.includes(step.id);
            const isCurrent = step.id === currentStep;
            const isAccessible = flowService.canAccessStep(step.id, progress);

            return (
              <div key={step.id} className="flex flex-col items-center">
                <div className={`
                  w-8 h-8 rounded-full flex items-center justify-center text-base leading-relaxed font-medium
                  ${isCompleted ? 'bg-green-500 text-white' : 
                    isCurrent ? 'bg-blue-600 text-white' : 
                    isAccessible ? 'bg-gray-300 text-gray-600' : 'bg-gray-200 text-gray-400'}
                `}>
                  {isCompleted ? '✓' : index + 1}
                </div>
                <span className={`
                  text-base leading-relaxed mt-1 text-center max-w-16
                  ${isCurrent ? 'text-blue-600 font-medium' : 'text-gray-500'}
                `}>
                  {step.title.split(' ')[0]}
                </span>
              </div>
            );
          })}
        </div>
      )}

      {/* Time Estimate */}
      {showTimeEstimate && summary.estimatedTimeRemaining > 0 && (
        <div className="text-center">
          <span className="text-base leading-relaxed text-gray-600">
            About {summary.estimatedTimeRemaining} minutes remaining
          </span>
        </div>
      )}

      <VerificationErrorDisplay
        error={error}
        onRetry={handleRetry}
        onAlternative={() => setShowAlternativeModal(true)}
        isRetrying={isRetrying}
        retryDelay={retryDelay}
        isOffline={!isOnline}
      />
    </div>
  );
};

export default OnboardingProgressBar; 